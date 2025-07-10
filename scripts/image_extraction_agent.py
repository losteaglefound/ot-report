import base64
import json
from io import BytesIO
import os
from traceback import format_exc
from typing import List, Dict

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, START
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage

# OpenAI client
from openai import OpenAI

# PDF to Image conversion
from pdf2image import convert_from_bytes # Requires 'pip install pdf2image Pillow' and Poppler utilities


from dotenv import load_dotenv

assert load_dotenv()

# Initialize OpenAI Client (it will pick up OPENAI_API_KEY from environment variables)
client = OpenAI()

# --- 1. Define Helper Functions for Core Logic ---

def encode_image(image_bytes_io: BytesIO) -> str:
    """Encodes a BytesIO image object to a base64 string."""
    # Move to the beginning of the BytesIO object before reading
    image_bytes_io.seek(0)
    return base64.b64encode(image_bytes_io.getvalue()).decode('utf-8')

def convert_pdf_page_to_image_func(pdf_bytes: bytes, page_number: int = 1, dpi: int = 300) -> BytesIO:
    """
    Converts a specific page of a PDF (given as bytes) into an image (BytesIO).
    Requires Poppler utilities to be installed and accessible in system PATH.
    """
    print(f"Attempting to convert PDF page {page_number} to image with DPI {dpi}...")
    try:
        # convert_from_bytes handles the PDF to image conversion
        images = convert_from_bytes(pdf_bytes, first_page=page_number, last_page=page_number, dpi=dpi)
        if not images:
            raise ValueError(f"No image was generated for page {page_number}. Check PDF content or page number.")

        img_byte_arr = BytesIO()
        # Save the PIL Image object to a BytesIO object as PNG format
        images[0].save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0) # Rewind to the beginning for subsequent reads
        print(f"Successfully converted page {page_number} to image (BytesIO object).")
        return img_byte_arr
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
        print("Please ensure Poppler utilities are correctly installed and added to your system's PATH.")
        raise # Re-raise the exception to propagate error in LangGraph

def extract_table_with_vision_func(base64_image: str) -> str:
    """
    Sends the base64 encoded image to OpenAI Vision for table extraction.
    Returns the extracted text (expected to be a JSON string) from the model.
    """
    print("Sending image to OpenAI Vision API for table extraction...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # gpt-4o is recommended for its strong vision capabilities and JSON mode
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            "Extract the 'SCORE PROFILE' table data from this image. "
                            "Provide the output as a JSON array of objects. "
                            "Each object should represent a row with the following keys: "
                            "'Quadrant', 'Much less than others', 'Less than others', "
                            "'Just like the majority of others', 'More than others', "
                            "'Much more than others', and 'Description'."
                            "Ensure the 'Description' field captures the full text for that row. "
                            "If a numerical range is empty, use an empty string for that key."
                        )},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}" # Specify PNG format
                            },
                        },
                    ],
                }
            ],
            max_tokens=4000, # Sufficient tokens for a detailed JSON output
            response_format={"type": "json_object"} # Instruct the model to return JSON
        )
        # The content from the Vision API will be a string, which we expect to be JSON
        extracted_content = response.choices[0].message.content
        print("Successfully received response from OpenAI Vision API.")
        return extracted_content
    except Exception as e:
        print(f"Error calling OpenAI Vision API: {e}")
        print("Please ensure your OPENAI_API_KEY is correctly set and you have network connectivity.")
        raise # Re-raise the exception

# --- 2. Define LangGraph Tools ---

# Tool for PDF to Image conversion
# This tool takes raw PDF bytes and the target page number
pdf_to_image_tool = Tool(
    name="convert_pdf_page_to_image",
    description="Converts a specified page of PDF bytes into an image (BytesIO object).",
    func=convert_pdf_page_to_image_func,
    # Define expected arguments for LangGraph's tool calling
    args_schema={"pdf_bytes": bytes, "page_number": int, "dpi": int}
)

# Tool for OpenAI Vision extraction
# This tool takes a base64 encoded image string
vision_extraction_tool = Tool(
    name="extract_table_with_vision",
    description="Uses OpenAI Vision to extract structured data (JSON string) from a base64 encoded image.",
    func=extract_table_with_vision_func,
    # Define expected arguments for LangGraph's tool calling
    args_schema={"base64_image": str}
)

# --- 3. Define LangGraph State and Nodes ---

class AgentState:
    """Represents the state of our LangGraph agent workflow."""
    pdf_raw_content: bytes = None # Stores the actual binary content of the PDF file
    image_data: BytesIO = None    # Stores the BytesIO object of the converted image
    base64_image: str = None      # Stores the base64 encoded string of the image for Vision API
    extracted_json: List[Dict] = [] # Stores the parsed JSON data from the Vision API
    error: str = None             # Stores any error messages encountered during the workflow

def convert_pdf_page_node(state: AgentState):
    """
    LangGraph node responsible for converting a specific PDF page to an image.
    It calls the `pdf_to_image_tool`.
    """
    print("\n--- LangGraph Node: convert_pdf_page_node ---")
    if not state.pdf_raw_content:
        print("Error: PDF raw content is missing from state.")
        return {"error": "PDF raw content is missing."}

    # The 'SCORE PROFILE' table is typically found on page 4 of the provided PDF report.
    target_page = 4
    try:
        # Execute the PDF to image conversion tool
        image_bytes_io = pdf_to_image_tool.run({
            "pdf_bytes": state.pdf_raw_content,
            "page_number": target_page,
            "dpi": 300 # High DPI (dots per inch) for better OCR accuracy
        })
        # Update the state with the generated image data and its base64 representation
        return {"image_data": image_bytes_io, "base64_image": encode_image(image_bytes_io)}
    except Exception as e:
        # Capture and return any errors during conversion
        return {"error": f"PDF to image conversion failed in node: {e}"}

def extract_table_data_node(state: AgentState):
    """
    LangGraph node responsible for sending the image to OpenAI Vision for table extraction.
    It calls the `vision_extraction_tool`.
    """
    print("\n--- LangGraph Node: extract_table_data_node ---")
    if not state.base64_image:
        print("Error: Base64 image data is missing for vision extraction.")
        return {"error": "Base64 image data is missing for vision extraction."}

    try:
        # Execute the Vision API extraction tool
        raw_json_str = vision_extraction_tool.run({"base64_image": state.base64_image})
        # Attempt to parse the string output from Vision API into a Python list of dictionaries
        extracted_data = json.loads(raw_json_str)
        print("Successfully extracted and parsed JSON data from OpenAI Vision.")
        return {"extracted_json": extracted_data}
    except json.JSONDecodeError as e:
        # Handle cases where the Vision API's output is not valid JSON
        print(f"JSON decoding error from Vision API output: {e}. Raw output starts: {raw_json_str[:200]}...")
        return {"error": f"Failed to parse JSON from Vision API: {e}. Raw output starts: {raw_json_str[:200]}..."}
    except Exception as e:
        # Handle any other exceptions during Vision API call or processing
        return {"error": f"Vision API extraction failed in node: {e}"}

# --- 4. Build LangGraph Workflow ---

# Create a new StateGraph with our defined AgentState
workflow = StateGraph(AgentState)

# Add nodes to the workflow, mapping them to our Python functions
workflow.add_node("convert_pdf_page", convert_pdf_page_node)
workflow.add_node("extract_table_data", extract_table_data_node)

# Define the sequence of operations (edges)
# Start the workflow by converting the PDF page
workflow.add_edge(START, "convert_pdf_page")
# After converting the PDF page, proceed to extract table data using Vision API
workflow.add_edge("convert_pdf_page", "extract_table_data")

# Compile the workflow into an executable application
app = workflow.compile()

# --- 5. Execution Block ---

if __name__ == "__main__":
    # --- IMPORTANT: Configure your PDF file path here ---
    # Make sure this path points to the actual PDF file on your system.
    # For example: pdf_file_path = "/Users/youruser/Documents/Sensory-Profile-2-Summary-Report_70247631_1751134355067.pdf"
    pdf_file_path = "assets/inputs/Sensory-Profile-2-Summary-Report_70247631_1751134355067.pdf" # Assumes PDF is in the same directory

    if not os.path.exists(pdf_file_path):
        print(f"Error: The PDF file was not found at '{pdf_file_path}'.")
        print("Please ensure the file exists and the 'pdf_file_path' variable is set correctly.")
    else:
        try:
            # Read the actual binary content of the PDF file
            with open(pdf_file_path, "rb") as f:
                pdf_bytes_content = f.read()

            print(f"Loaded PDF file: {pdf_file_path} (size: {len(pdf_bytes_content)} bytes)")

            # Initialize the agent's state with the PDF content
            initial_agent_state = AgentState.pdf_raw_content=pdf_bytes_content

            # Invoke the LangGraph workflow
            print("\n--- Invoking LangGraph workflow ---")
            final_state = app.invoke(initial_agent_state)

            # Check for errors or success
            if final_state.error:
                print("\n--- Workflow finished with errors ---")
                print(f"Error details: {final_state.error}")
            else:
                print("\n--- Workflow completed successfully ---")
                print("\nExtracted Score Profile Table Data:")
                # Pretty print the extracted JSON data
                print(json.dumps(final_state.extracted_json, indent=2))

        except FileNotFoundError:
            print(f"Runtime Error: PDF file not found at '{pdf_file_path}'. Please verify the path.")
        except Exception as e:
            print(f"An unexpected error occurred during workflow execution: {e}")
            print("Please check your environment setup (Poppler, OpenAI API Key) and PDF file integrity.")
            