from datetime import datetime
import os
import json
import logging
from pathlib import Path
import sys
import time
from traceback import format_exc
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypedDict,
    Union
)

import boto3
import fitz
from langchain.chat_models import init_chat_model
from langgraph.graph import (
    END, 
    START,
    StateGraph
)

from aws_respnose_parser import parse_chomps_json
from backend.common.logging import logging
from sconfig import config as script_config
from config import config as server_config



logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(server_config.PROJECT_DIR, 'logs', __file__)
)
logger = logging.getLogger(__name__)



class State(TypedDict):
    openai_client: Any
    pdf_path: str 
    aws: "AWSTextractOCRTableAnalyzer"
    full_response: Dict[str, Union[Dict, List]] = {}
    pages_as_bytes: list = []
    error: str 


class AWSTextractOCRTableAnalyzer:
    """
    A class to analyze PDF documents page by page and extract table data using AWS Textract analyze_document API
    """
    
    def __init__(self, 
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = 'us-east-1'
    ):
        """
        Initialize the Textract OCR analyzer
        
        Args:
            aws_access_key_id: AWS access key ID (optional, can use env vars)
            aws_secret_access_key: AWS secret access key (optional, can use env vars)
            region_name: AWS region name
            output_dir: Directory to store output files
        """
        region_name = region_name
        
        
        # Initialize Textract client
        try:
            session_kwargs = {'region_name': region_name}
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                })
            
            self.textract_client = boto3.client('textract', **session_kwargs)
            logger.info(f"Initialized Textract client for region: {region_name}")
        except Exception as e:
            print(format_exc())
            logger.error(f"Failed to initialize Textract client: {e}")
            raise
    

def extract_pages_as_bytes(state: State) -> State:
    """
    Extract all pages from PDF as bytes
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of page bytes
    """
    try:
        pdf_path = state['pdf_path']

        logger.info(f"📄 Extracting pages from PDF: {pdf_path}")
        
        # Open PDF document
        doc = fitz.open(pdf_path)
        page_bytes_list = []
        
        for page_num in range(len(doc)):
            logger.info(f"🔄 Processing page {page_num + 1}/{len(doc)}")
            
            # Get page
            page = doc[page_num]
            
            # Convert page to image (PNG format)
            pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
            img_data = pix.tobytes("png")
            
            page_bytes_list.append(img_data)
        
        doc.close()
        logger.info(f"✅ Successfully extracted {len(page_bytes_list)} pages as bytes")
        state['pages_as_bytes'] = page_bytes_list
        return state
        
    except Exception as e:
        print(format_exc())
        logger.error(f"Failed to extract pages from PDF: {e}")
        state['error'] = f"Failed to extract pages from PDF {pdf_path}: {e}"
        return state


def analyze_document(state: State) -> State:
    """
    Analyze a PDF document to extract tables using analyze_document API
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing all page analysis results
    """
    try:
        pdf_path = state['pdf_path']
        textract_client = state['aws']
        page_bytes_list = state['pages_as_bytes']
        full_response = state['full_response']

        logger.info(f"🔍 Starting OCR table analysis of document: {pdf_path}")
        
        # Extract pages as bytes
        # page_bytes_list = extract_pages_as_bytes(pdf_path)
        
        # Analyze each page
        # all_responses = []
        
        for page_num, page_bytes in enumerate(page_bytes_list):
            logger.info(f"📊 Analyzing page {page_num + 1}/{len(page_bytes_list)}")
            
            try:
                # Call Textract analyze_document for this page
                response = textract_client.analyze_document(
                    Document={'Bytes': page_bytes},
                    FeatureTypes=['TABLES', 'FORMS']
                )

                with open(f"outputs/aws_chomps_page_{page_num}.json", 'w+') as f:
                    f.write(json.dumps(response, indent=4))

                json_data = parse_chomps_json(response)
                if json_data.get('patientInfo', {}).get("name", ""):
                    full_response['patientInfo'] = json_data['patientInfo']
                if check1 := json_data.get("observations", []):
                    if check2 := full_response.get("observations", []):
                        full_response['observations'].extend(json_data['observations'])
                    else:
                        full_response['observations'] = json_data['observations']
                
                # Process the response
                # processed_response = process_textract_response(response, page_num + 1)
                # all_responses.append(processed_response)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(format_exc())
                logger.error(f"Failed to analyze page {page_num + 1}: {e}")
                # Continue with next page
                error_response = {
                    'page_number': page_num + 1,
                    'error': str(e),
                    'tables': [],
                    'extracted_text': [],
                    'raw_response': None
                }
                # all_responses.append(error_response)
        
        # Create final result
        # final_result = {
        #     'pages': all_responses,
        #     'metadata': {
        #         'source_file': pdf_path,
        #         'analysis_timestamp': datetime.now().isoformat(),
        #         'total_pages': len(page_bytes_list),
        #         'successful_pages': len([r for r in all_responses if 'error' not in r]),
        #         'failed_pages': len([r for r in all_responses if 'error' in r]),
        #         'aws_region': region_name,
        #         'analysis_method': 'analyze_document'
        #     }
        # }

        state['full_response'] = full_response
        logger.info(f"✅ Successfully analyzed document: {pdf_path}")
        return state
        
    except Exception as e:
        print(format_exc())
        logger.error(f"Error analyzing document {pdf_path}: {e}")
        state['error'] = f"Error analyzing document {pdf_path}: {e}"
        return state
    


# def report_translation(state: Dict[str, Any]) -> Dict[str, Any]:
#     logger.info("=== Starting report translation ===")
#     try:
#         report_json = state['report_json']
#         logger.info(f"Report JSON length: {len(report_json)} characters")

#         prompt = f"""
#         You are an expert pediatric occupational therapist interpreting individual ChOMPS assessment items.

#         Your task is to read each item and its score, and generate a 1–3 sentence clinical interpretation that explains what the score says about the child's current skill level.

#         Use the following scoring criteria:
#         - 2 = YES: Skill is mastered and performed independently
#         - 1 = SOMETIMES: Skill is emerging, inconsistent, or performed with difficulty
#         - 0 = NOT YET: Skill is not yet developed or attempted

#         ---

#         🧠 INSTRUCTIONS:
#         - Use clinical but accessible language
#         - Avoid repeating the item description verbatim
#         - Focus on functional interpretation of the skill
#         - Reference observed difficulties or strengths based on score
#         - Frame statements from a third-person professional point of view ("The child...")

#         ---

#         💡 EXAMPLES:

#         Input:
#         {{ "item_no": "13", "item_description": "use a filled spoon or fork to bring food to mouth", "score": 2 }}

#         Output:
#         The child consistently demonstrates the ability to self-feed using utensils, indicating age-appropriate fine motor coordination and independent feeding skills.

#         ---

#         Input:
#         {{ "item_no": "18", "item_description": "use upper teeth or lip to clean food from bottom lip", "score": 1 }}

#         Output:
#         The child shows emerging skill in lip and jaw coordination but may not yet consistently use appropriate oral patterns to clean food effectively from the lower lip.

#         ---

#         Now interpret the following item:

#         {{ "item_no": "<ITEM_NO>", "item_description": "<ITEM_DESCRIPTION>", "score": <SCORE> }}

        
#         IMPORTANT:
#         - only return json response, no description.
        
#         RESPONES FORMAT:
#         [
#             {{
#                 "item_no": "1", 
#                 "item_description": "stand without holding on to anything", 
#                 "score": 2,
#                 "context": "<INTERPRETATION OF ITEM 1 CONTEXT FROM SCORE>"
#             }},
#             {{
#                 "item_no": "2", 
#                 "item_description": "walk 10-20 steps by himself/herself", 
#                 "score": 1,
#                 "context": "<INTERPRETATION OF ITEM 2 CONTEXT FROM SCORE>"
#             }}
#         ]


#         >>> JSON CONTENT FOR INTERPRETATION
#         {report_json}
#         <<<
#         """
#         llm = state[]

#         logger.info("Sending translation prompt to LLM...")
#         result = llm.invoke(prompt)
        
#         logger.info("Received translation response from LLM")
#         output = result.content.strip().replace("```json", "").replace('```', '')
        
#         logger.info(f"Translation output length: {len(output)} characters")

#         with open("outputs/chomps_report_context.json", 'w') as f:
#             f.write(output)
#         logger.info("Saved translation output to file")

#         logger.info("Attempting to parse translation output as JSON...")
#         output = json.loads(output)
#         logger.info(f"Successfully parsed translation output with {len(output)} items")

#         report_context_translation_list = []
#         for d in output:
#             report_context_translation_list.append(d['context'])

#         logger.info("Report translation completed successfully")
#         return {
#             **state,
#             "report_context_translation_list": report_context_translation_list,
#             "report_context_translation": output,
#             "retry_count": state.get("retry_count", 0)
#         }
    
#     except json.JSONDecodeError as e:
#         logger.error(f"JSON decode error in report translation: {str(e)}")
#         logger.error(format_exc())
#         return {
#             **state,
#             "error_message": f"Error parsing sensory data: {str(e)}",
#             "parsed_json": "",
#             "valid": False
#         }
        
#     except Exception as e:
#         logger.error(f"Error in report translation: {str(e)}")
#         logger.error(format_exc())
#         return {
#             **state,
#             "error_message": f"Error parsing sensory data: {str(e)}",
#             "parsed_json": "",
#             "valid": False
#         }




def build_graph():
    # GRAPH BUILDER
    graph_builder = StateGraph(state_schema=State)
    graph_builder.add_node("analyze_document", analyze_document)
    graph_builder.add_node("extract_pages_as_bytes", extract_pages_as_bytes)

    # FLOW
    graph_builder.add_edge(START, "extract_pages_as_bytes")
    graph_builder.add_edge("extract_pages_as_bytes", "analyze_document")
    graph_builder.add_edge("analyze_document", END)
    
    return graph_builder.compile()

def create_initial_state():
    aws_client = AWSTextractOCRTableAnalyzer(
        aws_access_key_id=server_config.AMAZON_ACCESS_KEY_ID,
        aws_secret_access_key=server_config.AMAZON_SECRET_ACCESS_KEY,
        region_name=server_config.AMAZON_REGION
    )

    return State({
        'aws': aws_client.textract_client,
        "full_response": dict(),
        "pages_as_bytes": list(),
        "openai_client": server_config.openai
    })


def aws_chomps_data_extract_agent(pdf_path: str, /):
    
    graph = build_graph()
    openai_client = init_chat_model("openai:gpt-4o")

    state = create_initial_state()
    state['pdf_path'] = pdf_path

    final_state = graph.invoke(state)
    full_response = state['full_response']

    with open("outputs/aws_final_full_response.json", 'w+') as f:
        json.dump(full_response, f, indent=4)

    logger.info("Chomps data parsed successfully.`")

def main():
    pdf_path: str = "/home/lap-49/Documents/ot-report/assets/inputs/images/ChOMPS_image.pdf"
    final_state = aws_chomps_data_extract_agent(pdf_path)


if __name__ == "__main__":
    main()