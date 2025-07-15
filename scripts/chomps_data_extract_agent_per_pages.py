import json
import re
import os
import fitz  # PyMuPDF
from traceback import format_exc
from typing import Dict, Any
import logging

from dotenv import load_dotenv
from langgraph.graph import START, StateGraph, END
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chomps_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load API key from .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize the LLM
llm = init_chat_model(f"openai:gpt-4o")

# Shared state keys for the sensory agent
STATE_KEYS = ["pdf_path", "report_text", "parsed_json", "valid", "retry_count", "error_message"]

# Prompt template for sensory data extraction
extraction_prompt_template = ChatPromptTemplate.from_messages([
    (
        "system", 
        """You are a pediatric occupational therapist who specializes in feeding evaluations.
        You will be given raw observations, symptoms, and caregiver reports from a pediatric feeding assessment. Your task is to interpret this data and generate a clinical assessment report in the voice of a licensed OT.
        Your report must be written in a **clinical, observational, and analytical tone** as if it were being submitted for a medical record or parent consultation.
        """
    ),
    (
        "human", 
        """
        {prompt}

        📝 OUTPUT FORMAT:

        ```json
        {{
        "section_1_physical_exam": {{
            "body": "...",
            "head_and_neck": "...",
            "jaw": "...",
            "lips": "...",
            "tongue": "...",
            "cheek": "...",
            "palate": "..."
        }},
        "section_2_cranial_nerve_screening": {{
            "CN_I": "...",
            "CN_V": "...",
            "CN_VII": "...",
            "CN_IX": "...",
            "CN_X": "...",
            "CN_XI": "...",
            "CN_XII": "..."
        }},
        "section_3_chomps_summary": "...",
        "section_4_oral_motor_skills": "...",
        "section_5_pedieat_analysis": "..."
        }}
        """)
])



def extract_text_from_pdf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract text from PDF file page by page."""
    logger.info("=== Starting PDF text extraction ===")
    try:
        pdf_path = state.get("pdf_path", "")
        page_number = state.get("page_number", 0)
        logger.info(f"PDF path: {pdf_path}, processing page: {page_number}")
        
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return {
                **state,
                "error_message": f"PDF file not found: {pdf_path}",
                "report_text": "",
                "valid": False
            }
        
        logger.info("Opening PDF document...")
        doc = fitz.open(pdf_path)
        
        # Check if page number is valid
        if page_number >= len(doc):
            logger.error(f"Page number {page_number} exceeds total pages {len(doc)}")
            doc.close()
            return {
                **state,
                "error_message": f"Page number {page_number} exceeds total pages {len(doc)}",
                "report_text": "",
                "valid": False
            }
        
        # Extract text from specific page
        page = doc[page_number]
        page_text = page.get_text()
        doc.close()
        
        text_length = len(page_text.strip())
        logger.info(f"Extracted text length from page {page_number}: {text_length} characters")
        
        if not page_text.strip():
            logger.warning(f"No text could be extracted from page {page_number}")
            return {
                **state,
                "report_text": "",
                "error_message": f"No text extracted from page {page_number}",
                "valid": False
            }
        
        logger.info(f"PDF text extraction completed successfully for page {page_number}")
        return {
            **state,
            "report_text": page_text,
            "error_message": "",
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in PDF text extraction: {str(e)}")
        logger.error(format_exc())
        return {
            **state,
            "error_message": f"Error extracting text from PDF: {str(e)}",
            "report_text": "",
            "valid": False
        }

def ai_convert_raw_data_to_json(state: Dict[str, any]) -> Dict[str, any]:
    logger.info("=== Starting raw data to JSON conversion ===")
    try:
        page_number = state.get("page_number", 0)
        output_file = f"outputs/chomps_raw_to_json_page_{page_number}.json"

        # Check if we already processed this page
        # if os.path.exists(output_file):
        #     logger.info(f"Loading existing raw_to_json response for page {page_number}")
        #     with open(output_file, 'r') as f:
        #         output = f.read()

        #     return {
        #         **state,
        #         "report_json": output,
        #         "raw_to_json_retry_count": 0,
        #         "previous_attempts": [],
        #         "retry_count": state.get("retry_count", 0)
        #     }

        report_text = state.get("report_text", "")
        retry_count = state.get("raw_to_json_retry_count", 0)
        
        logger.info(f"Report text length for page {page_number}: {len(report_text)} characters")
        logger.info(f"Current retry count: {retry_count}")

        if not report_text:
            logger.error(f"No report text available for parsing page {page_number}")
            return {
                **state,
                "error_message": f"No report text available for parsing page {page_number}",
                "parsed_json": "",
                "valid": False
            }
        
        logger.info(f"Creating extraction prompt for page {page_number}...")
        # Create the extraction prompt
        prompt = f"""
        You are an assistant that converts survey-based pediatric feeding assessment data into structured JSON format.

        You will be given a text containing numbered items from the Child Oral and Motor Proficiency Scale (ChOMPS), each with a description and a score.

        This is PAGE {page_number} of the PDF document.

        ---

        Your task is to extract:
        - The item number (e.g., "1")
        - The item description (e.g., "stand without holding on to anything")
        - The score (an integer: 2 = Yes, 1 = Sometimes, 0 = Not Yet)

        Then format each item as an object:
        {{ "item_no": "<ITEM_NO>", "item_description": "<ITEM_DESCRIPTION>", "score": <SCORE> }}

        Return the full list as a JSON array.

        ---

        💡 Example:

        Input text (shortened):
        1. stand without holding on to anything
        2. walk 10-20 steps by himself/herself
        Scores: 2, 1

        Expected output:
        [
        {{"item_no": "1", "item_description": "stand without holding on to anything", "score": 2}},
        {{"item_no": "2", "item_description": "walk 10-20 steps by himself/herself", "score": 1}}
        ]

        ---

        Now, using this format, extract all items and scores from the following input text from PAGE {page_number}:
        <<<
        {report_text}
        >>>
        """
        
        logger.info(f"Sending prompt to LLM for page {page_number}...")
        # Generate response
        response = llm.invoke(prompt)
        
        logger.info(f"Received response from LLM for page {page_number}")
        # Clean the response
        output = response.content.strip().replace("```json", "").replace("```", "")
        
        logger.info(f"Cleaned output length for page {page_number}: {len(output)} characters")
        logger.info(f"Output preview: {output[:200]}...")

        # Save with page number
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Saved raw JSON output to {output_file}")

        logger.info(f"Raw data to JSON conversion completed successfully for page {page_number}")
        return {
            **state,
            "report_json": output,
            "raw_to_json_retry_count": 0,
            "previous_attempts": [],
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in raw data to JSON conversion for page {page_number}: {str(e)}")
        logger.error(format_exc())
        return {
            **state,
            "error_message": f"Error parsing sensory data: {str(e)}",
            "parsed_json": "",
            "valid": False
        }
    
def report_translation(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("=== Starting report translation ===")
    try:
        page_number = state.get("page_number", 0)
        output_file = f"outputs/chomps_report_context_page_{page_number}.json"
        
        # Check if we already processed this page
        # if os.path.exists(output_file):
        #     with open(output_file, 'r') as f:
        #         output = f.read()

        #     output_json = json.loads(output)

        #     report_context_translation_list = []
        #     for d in output_json:
        #         report_context_translation_list.append(d['context'])

        #     logger.info(f"Report translation completed successfully for page {page_number}")
        #     return {
        #         **state,
        #         "report_context_translation_list": report_context_translation_list,
        #         "report_context_translation": output,
        #         "retry_count": state.get("retry_count", 0)
        #     }

        report_json = state['report_json']
        logger.info(f"Report JSON length for page {page_number}: {len(report_json)} characters")

        prompt = f"""
        You are an expert pediatric occupational therapist interpreting individual ChOMPS assessment items.

        Your task is to read each item and its score, and generate a 1–3 sentence clinical interpretation that explains what the score says about the child's current skill level.

        This is PAGE {page_number} of the PDF document.

        Use the following scoring criteria:
        - 2 = YES: Skill is mastered and performed independently
        - 1 = SOMETIMES: Skill is emerging, inconsistent, or performed with difficulty
        - 0 = NOT YET: Skill is not yet developed or attempted

        ---

        🧠 INSTRUCTIONS:
        - Use clinical but accessible language
        - Avoid repeating the item description verbatim
        - Focus on functional interpretation of the skill
        - Reference observed difficulties or strengths based on score
        - Frame statements from a third-person professional point of view ("The child...")

        ---

        💡 EXAMPLES:

        Input:
        {{ "item_no": "13", "item_description": "use a filled spoon or fork to bring food to mouth", "score": 2 }}

        Output:
        The child consistently demonstrates the ability to self-feed using utensils, indicating age-appropriate fine motor coordination and independent feeding skills.

        ---

        Input:
        {{ "item_no": "18", "item_description": "use upper teeth or lip to clean food from bottom lip", "score": 1 }}

        Output:
        The child shows emerging skill in lip and jaw coordination but may not yet consistently use appropriate oral patterns to clean food effectively from the lower lip.

        ---

        Now interpret the following item:

        {{ "item_no": "<ITEM_NO>", "item_description": "<ITEM_DESCRIPTION>", "score": <SCORE> }}

        
        IMPORTANT:
        - only return json response, no description.
        
        RESPONES FORMAT:
        [
            {{
                "item_no": "1", 
                "item_description": "stand without holding on to anything", 
                "score": 2,
                "context": "<INTERPRETATION OF ITEM 1 CONTEXT FROM SCORE>"
            }},
            {{
                "item_no": "2", 
                "item_description": "walk 10-20 steps by himself/herself", 
                "score": 1,
                "context": "<INTERPRETATION OF ITEM 2 CONTEXT FROM SCORE>"
            }}
        ]


        >>> JSON CONTENT FOR INTERPRETATION (PAGE {page_number})
        {report_json}
        <<<
        """

        logger.info(f"Sending translation prompt to LLM for page {page_number}...")
        result = llm.invoke(prompt)
        
        logger.info(f"Received translation response from LLM for page {page_number}")
        output = result.content.strip().replace("```json", "").replace('```', '')
        
        logger.info(f"Translation output length for page {page_number}: {len(output)} characters")

        # Save with page number
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Saved translation output to {output_file}")

        logger.info(f"Attempting to parse translation output as JSON for page {page_number}...")
        output_json = json.loads(output)
        logger.info(f"Successfully parsed translation output with {len(output_json)} items for page {page_number}")

        report_context_translation_list = []
        for d in output_json:
            report_context_translation_list.append(d['context'])

        logger.info(f"Report translation completed successfully for page {page_number}")
        return {
            **state,
            "report_context_translation_list": report_context_translation_list,
            "report_context_translation": output_json,
            "retry_count": state.get("retry_count", 0)
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in report translation for page {page_number}: {str(e)}")
        logger.error(format_exc())
        return {
            **state,
            "error_message": f"Error parsing sensory data: {str(e)}",
            "parsed_json": "",
            "valid": False
        }
        
    except Exception as e:
        logger.error(f"Error in report translation for page {page_number}: {str(e)}")
        logger.error(format_exc())
        return {
            **state,
            "error_message": f"Error parsing sensory data: {str(e)}",
            "parsed_json": "",
            "valid": False
        }

def divert_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("=== Passing through divert_node ===")
    return state


def parse_sensory_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Parse sensory data using LLM."""
    logger.info("=== Starting sensory data parsing ===")
    try:
        page_number = state.get("page_number", 0)
        report_text = state.get("report_text", "")
        logger.info(f"Report text length for page {page_number}: {len(report_text)} characters")
        
        # Save report text for this page
        page_text_file = f"outputs/chomps_agent_page_{page_number}.txt"
        with open(page_text_file, 'w') as f:
            f.write(report_text)
        logger.info(f"Saved report text to {page_text_file}")
        
        if not report_text:
            logger.error(f"No report text available for parsing page {page_number}")
            return {
                **state,
                "error_message": f"No report text available for parsing page {page_number}",
                "parsed_json": "",
                "valid": False
            }
        
        # Create the extraction prompt
        prompt = f"""
        🎯 TASK:
        Interpret and analyze the observations provided below from PAGE {page_number}. Then return a structured JSON report organized into five sections.

        Each section requires insight based on your OT expertise:
        1. **Physical Exam** – Analyze posture, orofacial tone, movement patterns
        2. **Cranial Nerve Screening** – Infer nerve-related findings from described behaviors
        3. **ChOMPS Summary & Analysis** – Synthesize the meaning of the child's ChOMPS outcomes
        4. **Oral-Motor Findings** – Identify compensations, weaknesses, and developmental gaps
        5. **PediEAT Analysis** – Identify feeding risks, sensory preferences, and safety issues

        --- BEGIN REPORT TEXT (PAGE {page_number}) ---
        {report_text}
        --- END REPORT TEXT ---
        """
        
        # Generate response
        messages = extraction_prompt_template.format_messages(prompt=prompt)
        response = llm.invoke(messages)
        
        # Clean the response
        output = response.content.strip().replace("```json", "").replace("```", "")

        # Save output for this page
        page_output_file = f"outputs/chomps_parsed_page_{page_number}.json"
        with open(page_output_file, 'w') as f:
            f.write(output)
        logger.info(f"Saved parsed output to {page_output_file}")

        logger.info(f"Sensory data output length for page {page_number}: {len(output)} characters")
        logger.info(f"Sensory data parsing completed successfully for page {page_number}")
        
        return {
            **state,
            "parsed_json": output,
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in sensory data parsing for page {page_number}: {str(e)}")
        logger.error(format_exc())
        return {
            **state,
            "error_message": f"Error parsing sensory data: {str(e)}",
            "parsed_json": "",
            "valid": False
        }

def validate_json_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate JSON response."""
    output = state.get("parsed_json", "")
    retry_count = state.get("retry_count", 0)
    
    if not output:
        return {
            **state,
            "valid": False,
            "error_message": "No output to validate",
            "retry_count": retry_count + 1
        }
    
    try:
        # Try to parse as JSON
        parsed_data = json.loads(output)
        
        # Validate required structure
        # required_keys = ["scoring_criteria", "processing", "quadrant_score_summary", "sensory_and_behavioral_section_score_summary"]
        # if not all(key in parsed_data for key in required_keys):
        #     raise ValueError("Missing required keys in JSON structure")
        
        return {**state, "valid": True, "error_message": ""}
        
    except json.JSONDecodeError as e:
        print(format_exc())
        print(f"JSON validation failed (attempt {retry_count + 1}): {e}")
        print(f"Response was: {output[:200]}...")
        
        # If we've tried too many times, accept the response as-is
        if retry_count >= 2:
            print("Max retries reached, accepting response")
            return {**state, "valid": True, "error_message": "Max retries reached"}
        
        # Try to fix common JSON issues
        fixed_output = _fix_common_json_issues(output)
        try:
            json.loads(fixed_output)
            print("Successfully fixed JSON issues")
            return {**state, "parsed_json": fixed_output, "valid": True, "error_message": ""}
        except:
            # Still invalid, mark for retry
            return {
                **state,
                "valid": False,
                "error_message": f"JSON validation failed: {str(e)}",
                "retry_count": retry_count + 1
            }
    
    except Exception as e:
        print(format_exc())
        return {
            **state,
            "valid": False,
            "error_message": f"Validation error: {str(e)}",
            "retry_count": retry_count + 1
        }

def _fix_common_json_issues(output: str) -> str:
    """Attempt to fix common JSON formatting issues."""
    # Remove any leading/trailing text that's not JSON
    output = output.strip()
    
    # Find JSON content between braces
    json_match = re.search(r'\{.*\}', output, re.DOTALL)
    if json_match:
        output = json_match.group(0)
    
    # Fix common issues
    output = output.replace("'", '"')  # Single to double quotes
    output = re.sub(r',\s*}', '}', output)  # Remove trailing commas
    output = re.sub(r',\s*]', ']', output)  # Remove trailing commas in arrays
    output = re.sub(r':\s*None', ': null', output)  # Replace None with null
    
    return output

def route_by_validation(state: Dict[str, Any]) -> str:
    """Route based on validation results."""
    is_valid = state.get("valid", False)
    retry_count = state.get("retry_count", 0)
    error_message = state.get("error_message", "")
    
    logger.info(f"=== Routing by validation: valid={is_valid}, retry_count={retry_count} ===")
    
    # End if valid or too many retries
    if is_valid or retry_count >= 3:
        logger.info("Ending - either valid or max retries reached")
        return END
    
    # If there's an error in text extraction, don't retry parsing
    if "PDF" in error_message or "text" in error_message:
        logger.info("Ending - PDF or text extraction error")
        return END
    
    # Otherwise, retry parsing
    logger.info("Retrying parse_sensory_data")
    return "parse_sensory_data"

def check_text_extraction(state: Dict[str, Any]) -> str:
    """Check if text extraction was successful."""
    error_message = state.get("error_message", "")
    report_text = state.get("report_text", "")
    
    logger.info(f"=== Checking text extraction: error={bool(error_message)}, text_length={len(report_text)} ===")
    
    if error_message or not report_text:
        logger.info("Text extraction failed - ending")
        return END
    
    logger.info("Text extraction successful - continuing to parse_sensory_data")
    return "parse_sensory_data"


def reflect(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logger.info("====== Starting reflect ======")
        page_number = state.get("page_number", 0)
        report_text = state['report_text']
        initial_json = state['report_json']
        reflect_retry_count = state.get("reflect", {}).get("retry_count", 1)
        reflect_outputs: list = state.get('reflect', {}).get("outputs", [])
        
        logger.info(f"Reflection retry {reflect_retry_count} for page {page_number}")

        logger.info(f"Building reflect prompt for page {page_number}")
        prompt = f"""
        You are a data extraction validator and corrector.
        Your job is to review a JSON object extracted from raw PDF text, reflect on the accuracy of the "Score" field, and correct any mistakes by comparing it to the raw source.
        Evaluate how confident you are in the analyze that the score in json structure is correct based on the raw text.

        This is PAGE {page_number} of the PDF document.

        Confidence criteria, range from 0.1 to 0.9. 

        ---

        RAW TEXT (from the PDF PAGE {page_number}):

        {report_text}

        ---

        INITIAL JSON (possibly inaccurate) for PAGE {page_number}:

        {initial_json}

        ---

        TASK:
        1. For each item in the JSON, locate its corresponding data in the raw text.
        2. Carefully verify that the "Score" field is accurate.
        3. If the score is incorrect, correct it using only evidence from the raw text.
        4. Return a new JSON dict with the verified list and not-verified list.
        6. Verified list should include item whose score verfied.
        7. Not-verfied should include those item whose Score you are not able to verify.
        5. Do not guess. If an item cannot be verified, mark its score as "UNKNOWN".
        6. Check and must return all the items from given json.

        Only return the corrected JSON.

        RESPONES FORMAT:
        {{
            "page": {page_number},
            "verified": [
                {{
                    "item_no": "1", 
                    "item_description": "stand without holding on to anything", 
                    "score": 2,
                    "context": "<INTERPRETATION OF ITEM 1 CONTEXT FROM SCORE>",
                    "confidence: <CONFIDENCE OF SCORING IS CORRECT>"
                }},
                {{
                    "item_no": "2", 
                    "item_description": "walk 10-20 steps by himself/herself", 
                    "score": 1,
                    "context": "<INTERPRETATION OF ITEM 2 CONTEXT FROM SCORE>",
                    "confidence: <CONFIDENCE OF SCORING IS CORRECT>"
                }}
            ],
            "not-verified": [
                {{
                    "item_no": "12", 
                    "item_description": "stand without holding on to anything", 
                    "score": UNKNOWN,
                    "context": "<INTERPRETATION OF ITEM 1 CONTEXT FROM SCORE>",
                    "confidence: <CONFIDENCE OF SCORING IS CORRECT>"
                }},
                {{
                    "item_no": "22", 
                    "item_description": "walk 10-20 steps by himself/herself", 
                    "score": UNKNOWN,
                    "context": "<INTERPRETATION OF ITEM 2 CONTEXT FROM SCORE>",
                    "confidence: <CONFIDENCE OF SCORING IS CORRECT>"
                }}
            ],

        }}
        ---
        """

        logger.info(f"Calling llm for reflection on page {page_number}")
        result = llm.invoke(prompt)
        output = result.content.strip().replace("```json", "").replace("```", "")

        output_file = f"outputs/chomps_reflect_page_{page_number}_retry_{reflect_retry_count}.json"
        logger.info(f"Writing reflection output to {output_file}")
        with open(output_file, 'w') as f:
            f.write(output)

        reflect_outputs.append(output)
        reflect = {
            "outputs": reflect_outputs,
            "retry_count": reflect_retry_count
        }

        return {
            **state,
            "reflect": reflect
        }

    except Exception as e:
        print(format_exc())
        return {
            **state,
            "valid": False,
        }
    
def reflect_validation(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        reflect_retry_count = state.get("reflect", {}).get("retry_count", 1)
        reflect_outputs: list = state['reflect']['outputs']
        reflect_output = reflect_outputs[-1]

        logger.info("Validating reflection")

        reflect_output_json = json.loads(reflect_output)
        if reflect_retry_count > 3:
            logger.info("Going to divert_node from reflection")
            return "divert_node"

        reflect_retry_count += 1
        state['reflect']['retry_count'] = reflect_retry_count

        logger.info("Redirecting to reflection")
        return "reflect"
        
    except Exception as e:
        print(format_exc())
        return {
            **state,
            "error": "Error at reflect validation node {}".format(str(e)),  # Fixed: changed "errror" to "error"
            "valid": False,
        }



# Build the LangGraph
builder = StateGraph(state_schema=dict)  # Use simple dict for flexible state

# Add nodes
builder.add_node("extract_text", extract_text_from_pdf)
builder.add_node("parse_sensory_data", parse_sensory_data)
builder.add_node("validate_json", validate_json_response)
builder.add_node("raw_to_json", ai_convert_raw_data_to_json)
builder.add_node("report_context", report_translation)
builder.add_node('divert_node', divert_node)
builder.add_node("reflect", reflect)
# builder.add_node("reflect_validation", reflect_validation)

# Add edges
builder.add_edge(START, "extract_text")
builder.add_edge("extract_text", "raw_to_json")
builder.add_edge("raw_to_json", "report_context")
builder.add_edge("report_context", "reflect")
builder.add_conditional_edges("reflect", reflect_validation)
builder.add_conditional_edges("divert_node", check_text_extraction)
builder.add_edge("parse_sensory_data", "validate_json")
builder.add_conditional_edges("validate_json", route_by_validation)

# Compile the graph
sensory_graph = builder.compile()

def get_pdf_page_count(pdf_path: str) -> int:
    """Get the total number of pages in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        logger.error(f"Error getting page count: {str(e)}")
        return 0

def process_single_page(pdf_path: str, page_number: int) -> Dict[str, Any]:
    """
    Process a single page of the PDF through the extraction pipeline.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: Page number to process (0-indexed)
        
    Returns:
        dict: Processing result for the page
    """
    logger.info(f"=== Processing page {page_number} ===")
    
    try:
        # Create initial state for this page
        initial_state = {
            "pdf_path": pdf_path,
            "page_number": page_number,
            "report_text": "",
            "parsed_json": "",
            "valid": False,
            "retry_count": 0,
            "error_message": ""
        }
        
        # Process through the pipeline
        final_state = sensory_graph.invoke(initial_state)
        
        logger.info(f"Page {page_number} processing completed")
        
        return {
            "page_number": page_number,
            "success": not bool(final_state.get("error_message")),
            "error": final_state.get("error_message"),
            "data": final_state
        }
        
    except Exception as e:
        logger.error(f"Error processing page {page_number}: {str(e)}")
        logger.error(format_exc())
        return {
            "page_number": page_number,
            "success": False,
            "error": f"Error processing page {page_number}: {str(e)}",
            "data": None
        }

def extract_sensory_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract sensory data from a PDF using the LangGraph agent, processing each page separately.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: Extracted sensory data or error information
    """
    logger.info("=== Starting sensory data extraction pipeline ===")
    logger.info(f"PDF path: {pdf_path}")
    
    try:
        # First, get the total number of pages
        total_pages = get_pdf_page_count(pdf_path)
        if total_pages == 0:
            return {
                "success": False,
                "error": "Could not read PDF or PDF has no pages",
                "data": None
            }
        
        logger.info(f"PDF has {total_pages} pages. Processing each page separately...")
        
        # Process each page
        all_results = []
        successful_pages = []
        failed_pages = []
        
        for page_num in range(total_pages):
            logger.info(f"Processing page {page_num + 1} of {total_pages}")
            
            result = process_single_page(pdf_path, page_num)
            all_results.append(result)
            
            if result["success"]:
                successful_pages.append(page_num)
                logger.info(f"Page {page_num} processed successfully")
            else:
                failed_pages.append(page_num)
                logger.warning(f"Page {page_num} failed: {result['error']}")
        
        # Save summary of all results
        summary = {
            "total_pages": total_pages,
            "successful_pages": successful_pages,
            "failed_pages": failed_pages,
            "results": all_results
        }
        
        summary_file = "outputs/chomps_processing_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"Saved processing summary to {summary_file}")
        
        if successful_pages:
            logger.info(f"Successfully processed {len(successful_pages)} out of {total_pages} pages")
            return {
                "success": True,
                "error": None,
                "data": summary
            }
        else:
            logger.error("No pages were processed successfully")
            return {
                "success": False,
                "error": "No pages were processed successfully",
                "data": summary
            }
        
    except Exception as e:
        logger.error(f"Error in sensory data extraction pipeline: {str(e)}")
        logger.error(format_exc())
        return {
            "success": False,
            "error": f"Error in sensory data extraction: {str(e)}",
            "data": None
        }

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Chomps data from PDF reports")
    parser.add_argument("--pdf", required=True, help="Path to the Chomps Profile PDF report")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    args = parser.parse_args()
    
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Extract sensory data
    result = extract_sensory_data(args.pdf)
    
    if result["success"]:
        # The data now contains a summary of all pages processed
        summary_data = result["data"]
        
        print(f"Processing completed!")
        print(f"Total pages: {summary_data['total_pages']}")
        print(f"Successfully processed pages: {summary_data['successful_pages']}")
        print(f"Failed pages: {summary_data['failed_pages']}")
        
        # Save summary to output file if specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            print(f"Processing summary saved to {args.output}")
        
        # Print information about generated files
        print("\nGenerated files:")
        print("- outputs/chomps_processing_summary.json (overall summary)")
        
        for page_num in summary_data['successful_pages']:
            print(f"- outputs/chomps_raw_to_json_page_{page_num}.json")
            print(f"- outputs/chomps_report_context_page_{page_num}.json")
            print(f"- outputs/chomps_reflect_page_{page_num}_retry_1.json")
        
    else:
        print(f"Error: {result['error']}")
        if result["data"]:
            # Even if failed, we might have partial results
            print("Partial results available in outputs/chomps_processing_summary.json")

if __name__ == "__main__":
    main()
