import json
import re
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from typing import Dict, Any

from langgraph.graph import START, StateGraph, END
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate

# Load API key from .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize the LLM
llm = init_chat_model(f"openai:gpt-4o")

# Shared state keys for the CHOMPS agent
STATE_KEYS = ["pdf_path", "report_text", "parsed_json", "valid", "retry_count", "error_message"]

# Prompt template for CHOMPS data extraction
extraction_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are an expert speech-language pathologist and occupational therapist specializing in pediatric feeding and swallowing disorders. 
    You have extensive experience with the ChOMPS (Chicago Oral Motor and Feeding Scale) assessment tool.
    Extract information with clinical precision and maintain diagnostic accuracy. ALWAYS return valid JSON that can be parsed directly."""),
    ("human", """{prompt}

    IMPORTANT: Return ONLY valid JSON that can be parsed directly. Do not include any text before or after the JSON object.
    The JSON must follow this EXACT structure:
    
    {{
      "oral_motor_skills": {{
        "items": [
          {{ "item_no": "1", "item_description": "description of oral motor item", "score": 0 }},
          {{ "item_no": "2", "item_description": "description of oral motor item", "score": 1 }}
        ],
        "total_score": 0,
        "risk_level": "Low/Moderate/High"
      }},
      "oral_sensory_skills": {{
        "items": [
          {{ "item_no": "3", "item_description": "description of sensory item", "score": 0 }}
        ],
        "total_score": 0,
        "risk_level": "Low/Moderate/High"
      }},
      "feeding_behaviors": {{
        "items": [
          {{ "item_no": "4", "item_description": "description of feeding behavior", "score": 0 }}
        ],
        "total_score": 0,
        "risk_level": "Low/Moderate/High"
      }},
      "medical_history": {{
        "items": [
          {{ "item_no": "5", "item_description": "description of medical history item", "score": 0 }}
        ],
        "total_score": 0,
        "risk_level": "Low/Moderate/High"
      }},
      "nutritional_status": {{
        "items": [
          {{ "item_no": "6", "item_description": "description of nutritional item", "score": 0 }}
        ],
        "total_score": 0,
        "risk_level": "Low/Moderate/High"
      }},
      "feeding_history": {{
        "items": [
          {{ "item_no": "7", "item_description": "description of feeding history item", "score": 0 }}
        ],
        "total_score": 0,
        "risk_level": "Low/Moderate/High"
      }},
      "overall_assessment": {{
        "total_score": 0,
        "overall_risk_level": "Low/Moderate/High",
        "feeding_safety_concerns": [],
        "recommendations": []
      }}
    }}
    """)
])

def extract_text_from_pdf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract text from PDF file."""
    try:
        pdf_path = state.get("pdf_path", "")
        if not pdf_path or not os.path.exists(pdf_path):
            return {
                **state,
                "error_message": f"PDF file not found: {pdf_path}",
                "report_text": "",
                "valid": False
            }
        
        doc = fitz.open(pdf_path)
        full_text = "".join([page.get_text() for page in doc])
        doc.close()
        
        if not full_text.strip():
            return {
                **state,
                "error_message": "No text could be extracted from the PDF",
                "report_text": "",
                "valid": False
            }
        
        return {
            **state,
            "report_text": full_text,
            "error_message": "",
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        return {
            **state,
            "error_message": f"Error extracting text from PDF: {str(e)}",
            "report_text": "",
            "valid": False
        }

def parse_chomps_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Parse CHOMPS data using LLM."""
    try:
        report_text = state.get("report_text", "")

        if not report_text:
            return {
                **state,
                "error_message": "No report text available for parsing",
                "parsed_json": "",
                "valid": False
            }
        
        # Create the extraction prompt
        prompt = f"""
        Extract ChOMPS (Chicago Oral Motor and Feeding Scale) assessment data from this report.
        
        The ChOMPS assessment evaluates feeding and swallowing skills across multiple domains:
        1. Oral Motor Skills - jaw, lip, tongue movements and coordination
        2. Oral Sensory Skills - sensory processing and responses
        3. Feeding Behaviors - behavioral responses during feeding
        4. Medical History - relevant medical factors affecting feeding
        5. Nutritional Status - growth, weight gain, and nutritional concerns
        6. Feeding History - developmental feeding milestones and challenges
        
        Extract all scored items with their descriptions and scores. Calculate domain totals and risk levels.
        Risk levels are typically: Low (0-2), Moderate (3-5), High (6+) but may vary by domain.
        
        Look for patterns like:
        - Item numbers with descriptions and scores
        - Domain subtotals
        - Risk level classifications
        - Overall assessment scores
        - Safety concerns or recommendations
        
        --- BEGIN REPORT TEXT ---
        {report_text}
        --- END REPORT TEXT ---
        """
        
        # Generate response
        messages = extraction_prompt_template.format_messages(prompt=prompt)
        response = llm.invoke(messages)
        
        # Clean the response
        output = response.content.strip().replace("```json", "").replace("```", "")
        

        with open("outputs/chomps_output.json", 'w') as f:
            f.write(output)


        return {
            **state,
            "parsed_json": output,
            "retry_count": state.get("retry_count", 0)
        }
        
    except Exception as e:
        return {
            **state,
            "error_message": f"Error parsing CHOMPS data: {str(e)}",
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
        required_keys = ["oral_motor_skills", "oral_sensory_skills", "feeding_behaviors", "medical_history", "nutritional_status", "feeding_history", "overall_assessment"]
        if not all(key in parsed_data for key in required_keys):
            raise ValueError("Missing required keys in JSON structure")
        
        return {**state, "valid": True, "error_message": ""}
        
    except json.JSONDecodeError as e:
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
    
    # End if valid or too many retries
    if is_valid or retry_count >= 3:
        return END
    
    # If there's an error in text extraction, don't retry parsing
    if "PDF" in error_message or "text" in error_message:
        return END
    
    # Otherwise, retry parsing
    return "parse_chomps_data"

def check_text_extraction(state: Dict[str, Any]) -> str:
    """Check if text extraction was successful."""
    error_message = state.get("error_message", "")
    report_text = state.get("report_text", "")
    
    if error_message or not report_text:
        return END
    
    return "parse_chomps_data"

# Build the LangGraph
builder = StateGraph(state_schema=dict)  # Use simple dict for flexible state

# Add nodes
builder.add_node("extract_text", extract_text_from_pdf)
builder.add_node("parse_chomps_data", parse_chomps_data)
builder.add_node("validate_json", validate_json_response)

# Add edges
builder.add_edge(START, "extract_text")
builder.add_conditional_edges("extract_text", check_text_extraction)
builder.add_edge("parse_chomps_data", "validate_json")
builder.add_conditional_edges("validate_json", route_by_validation)

# Compile the graph
chomps_graph = builder.compile()

def extract_chomps_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract CHOMPS data from a PDF using the LangGraph agent.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: Extracted CHOMPS data or error information
    """
    try:
        final_state = chomps_graph.invoke({
            "pdf_path": pdf_path,
            "report_text": "",
            "parsed_json": "",
            "valid": False,
            "retry_count": 0,
            "error_message": ""
        })
        
        if final_state.get("error_message"):
            return {
                "success": False,
                "error": final_state.get("error_message"),
                "data": None
            }
        
        parsed_json = final_state.get("parsed_json", "")
        if parsed_json:
            try:
                data = json.loads(parsed_json)
                return {
                    "success": True,
                    "error": None,
                    "data": data
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse final JSON response",
                    "data": parsed_json  # Return raw response for debugging
                }
        
        return {
            "success": False,
            "error": "No data extracted",
            "data": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in CHOMPS data extraction: {str(e)}",
            "data": None
        }

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract CHOMPS data from PDF reports")
    parser.add_argument("--pdf", required=True, help="Path to the CHOMPS PDF report")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    args = parser.parse_args()
    
    # Extract CHOMPS data
    result = extract_chomps_data(args.pdf)
    
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