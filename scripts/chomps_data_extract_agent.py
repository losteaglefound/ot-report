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
    """Extract text from PDF file."""
    logger.info("=== Starting PDF text extraction ===")
    try:
        pdf_path = state.get("pdf_path", "")
        logger.info(f"PDF path: {pdf_path}")
        
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
        full_text = "".join([page.get_text() for page in doc])
        doc.close()
        
        text_length = len(full_text.strip())
        logger.info(f"Extracted text length: {text_length} characters")
        
        if not full_text.strip():
            logger.error("No text could be extracted from the PDF")
            return {
                **state,
                "error_message": "No text could be extracted from the PDF",
                "report_text": "",
                "valid": False
            }
        
        logger.info("PDF text extraction completed successfully")
        return {
            **state,
            "report_text": full_text,
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

def ai_convert_raw_data_to_json(state: Dict[str, Any]) -> Dict[str, any]:
    logger.info("=== Starting raw data to JSON conversion ===")
    try:

        # if os.path.exists("outputs/chomps_raw_to_json.json"):
        #     logger.info("Loading existing raw_to_json response")
        #     with open("outputs/chomps_raw_to_json.json", 'r') as f:
        #         output = f.read()

        #     return {
        #         **state,
        #         "report_json": output,
        #         "raw_to_json_retry_count": 0,  # Initialize retry count
        #         "previous_attempts": [],  # Initialize attempt history
        #         "retry_count": state.get("retry_count", 0)
        #     }

        report_text = state.get("report_text", "")
        retry_count = state.get("raw_to_json_retry_count", 0)
        
        logger.info(f"Report text length: {len(report_text)} characters")
        logger.info(f"Current retry count: {retry_count}")

        if not report_text:
            logger.error("No report text available for parsing")
            return {
                **state,
                "error_message": "No report text available for parsing",
                "parsed_json": "",
                "valid": False
            }
        
        logger.info("Creating extraction prompt...")
        # Create the extraction prompt
        prompt = f"""
        You are an assistant that converts survey-based pediatric feeding assessment data into structured JSON format.

        You will be given a text containing numbered items from the Child Oral and Motor Proficiency Scale (ChOMPS), each with a description and a score.

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

        Now, using this format, extract all items and scores from the following input text:
        <<<
        {report_text}
        >>>
        """
        
        logger.info("Sending prompt to LLM...")
        # Generate response
        response = llm.invoke(prompt)
        
        logger.info("Received response from LLM")
        # Clean the response
        output = response.content.strip().replace("```json", "").replace("```", "")
        
        logger.info(f"Cleaned output length: {len(output)} characters")
        logger.info(f"Output preview: {output[:200]}...")

        with open("outputs/chomps_raw_to_json.json", 'w') as f:
            f.write(output)
        logger.info("Saved raw JSON output to file")

        logger.info("Raw data to JSON conversion completed successfully")
        return {
            **state,
            "report_json": output,
            "raw_to_json_retry_count": 0,  # Initialize retry count
            "previous_attempts": [],  # Initialize attempt history
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in raw data to JSON conversion: {str(e)}")
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
        # if os.path.exists("outputs/chomps_report_context.json"):
        #     with open("outputs/chomps_report_context.json", 'r') as f:
        #         output = f.read()

        #     output_json = json.loads(output)

        #     report_context_translation_list = []
        #     for d in output_json:
        #         report_context_translation_list.append(d['context'])

        #     logger.info("Report translation completed successfully")
        #     return {
        #         **state,
        #         "report_context_translation_list": report_context_translation_list,
        #         "report_context_translation": output,
        #         "retry_count": state.get("retry_count", 0)
        #     }

        report_json = state['report_json']
        logger.info(f"Report JSON length: {len(report_json)} characters")

        prompt = f"""
        You are an expert pediatric occupational therapist interpreting individual ChOMPS assessment items.

        Your task is to read each item and its score, and generate a 1–3 sentence clinical interpretation that explains what the score says about the child's current skill level.

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


        >>> JSON CONTENT FOR INTERPRETATION
        {report_json}
        <<<
        """

        logger.info("Sending translation prompt to LLM...")
        result = llm.invoke(prompt)
        
        logger.info("Received translation response from LLM")
        output = result.content.strip().replace("```json", "").replace('```', '')
        
        logger.info(f"Translation output length: {len(output)} characters")

        with open("outputs/chomps_report_context.json", 'w') as f:
            f.write(output)
        logger.info("Saved translation output to file")

        logger.info("Attempting to parse translation output as JSON...")
        output = json.loads(output)
        logger.info(f"Successfully parsed translation output with {len(output)} items")

        report_context_translation_list = []
        for d in output:
            report_context_translation_list.append(d['context'])

        logger.info("Report translation completed successfully")
        return {
            **state,
            "report_context_translation_list": report_context_translation_list,
            "report_context_translation": output,
            "retry_count": state.get("retry_count", 0)
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in report translation: {str(e)}")
        logger.error(format_exc())
        return {
            **state,
            "error_message": f"Error parsing sensory data: {str(e)}",
            "parsed_json": "",
            "valid": False
        }
        
    except Exception as e:
        logger.error(f"Error in report translation: {str(e)}")
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
        report_text = state.get("report_text", "")
        logger.info(f"Report text length: {len(report_text)} characters")
        
        

        print(2)


        print(2)
        with open("outputs/chomps_agent.txt", 'w') as f:
            f.write(report_text)
        logger.info("Saved report text to outputs/chomps_agent.txt")
        
        

        print(3)


        print(3)
        if not report_text:
            logger.error("No report text available for parsing")
            return {
                **state,
                "error_message": "No report text available for parsing",
                "parsed_json": "",
                "valid": False
            }
        

        # Create the extraction prompt
        prompt = f"""
        🎯 TASK:
        Interpret and analyze the observations provided below. Then return a structured JSON report organized into five sections.

        Each section requires insight based on your OT expertise:
        1. **Physical Exam** – Analyze posture, orofacial tone, movement patterns
        2. **Cranial Nerve Screening** – Infer nerve-related findings from described behaviors
        3. **ChOMPS Summary & Analysis** – Synthesize the meaning of the child's ChOMPS outcomes
        4. **Oral-Motor Findings** – Identify compensations, weaknesses, and developmental gaps
        5. **PediEAT Analysis** – Identify feeding risks, sensory preferences, and safety issues

        --- BEGIN REPORT TEXT ---
        {report_text}
        --- END REPORT TEXT ---
        """
        

        # Generate response
        messages = extraction_prompt_template.format_messages(prompt=prompt)
        response = llm.invoke(messages)
        

        # Clean the response
        output = response.content.strip().replace("```json", "").replace("```", "")

        # with open("outputs/pedieat.json", 'w') as f:
        #     f.write(output)

        logger.info(f"Sensory data output length: {len(output)} characters")
        logger.info("Sensory data parsing completed successfully")
        
        return {
            **state,
            "parsed_json": output,
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error in sensory data parsing: {str(e)}")
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
        report_text = state['report_text']
        initial_json = state['report_json']
        reflect_retry_count = state.get("reflect", {}).get("retry_count", 1)
        reflect_outputs: list = state.get('reflect', {}).get("outputs", [])
        
        logger.info("Reflection retry {}".format(reflect_retry_count))

        logger.info("Building reflect prompt")
        prompt = f"""
        You are a data extraction validator and corrector.
        Your job is to review a JSON object extracted from raw PDF text, reflect on the accuracy of the "Score" field, and correct any mistakes by comparing it to the raw source.
        Evaluate how confident you are in the analyze that the score in json structure is correct based on the raw text.

        Confidence criteria, range from 0.1 to 0.9. 

        ---

        RAW TEXT (from the PDF):

        {report_text}

        ---

        INITIAL JSON (possibly inaccurate):

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

        logger.info("Calling llm for reflection")
        result = llm.invoke(prompt)
        output = result.content.strip().replace("```json", "").replace("```", "")

        logger.info(f"Writting reflection output to outputs/chomps_reflect_{reflect_retry_count}.json")
        with open(f"outputs/chomps_reflect_{reflect_retry_count}.json", 'w') as f:
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

def extract_sensory_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract sensory data from a PDF using the LangGraph agent.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: Extracted sensory data or error information
    """
    logger.info("=== Starting sensory data extraction pipeline ===")
    logger.info(f"PDF path: {pdf_path}")
    
    try:
        final_state = sensory_graph.invoke({
            "pdf_path": pdf_path,
            "report_text": "",
            "parsed_json": "",
            "valid": False,
            "retry_count": 0,
            "error_message": ""
        })
        
        logger.info("Pipeline execution completed")
        logger.info(f"Final state keys: {list(final_state.keys())}")
        
        if final_state.get("error_message"):
            logger.error(f"Pipeline ended with error: {final_state.get('error_message')}")
            return {
                "success": False,
                "error": final_state.get("error_message"),
                "data": None
            }
        
        parsed_json = final_state.get("parsed_json", "")
        if parsed_json:
            try:
                data = json.loads(parsed_json)
                logger.info("Successfully parsed final JSON response")
                return {
                    "success": True,
                    "error": None,
                    "data": data
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse final JSON response")
                logger.error(format_exc())
                return {
                    "success": False,
                    "error": "Failed to parse final JSON response",
                    "data": parsed_json  # Return raw response for debugging
                }
        
        logger.warning("No data extracted from pipeline")
        return {
            "success": False,
            "error": "No data extracted",
            "data": None
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
    
    parser = argparse.ArgumentParser(description="Extract sensory data from PDF reports")
    parser.add_argument("--pdf", required=True, help="Path to the Sensory Profile PDF report")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    args = parser.parse_args()
    
    # Extract sensory data
    result = extract_sensory_data(args.pdf)
    
    if result["success"]:
        output_data = json.dumps(result["data"], indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_data)
            print(f"Successfully extracted data and saved to {args.output}")
        else:
            print(output_data)
    else:
        print(f"Error: {result['error']}")
        if result["data"]:
            print(f"Raw response: {result['data']}")

if __name__ == "__main__":
    main()
