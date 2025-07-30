
import csv
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
import time
from traceback import format_exc
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict
)


import boto3
import fitz
from langgraph.graph import (
    END,
    START,
    StateGraph
)
from langgraph.graph.state import CompiledStateGraph
from trp import Document

from sconfig import config as script_config
from config import config as server_config
from backend.common.logging import logging



logger = logging.getLogger(__file__)
OUTPUT_DIR = server_config.PROJECT_DIR.joinpath("outputs")


class AWSState(TypedDict, total=False):
    textract_client: Any
    extracted_pages: list[dict] | None
    merged_response: dict | None
    document: Document | None

class State(TypedDict):
    aws: AWSState | None
    sp2_data: dict | None
    message: str | None
    pages_as_bytes: list[bytes] | None
    pdf_path: str | None
    status: Literal["success", 'error'] | None



def initialize_aws_textract_client(state: State):
    """
    Initialize the Textract OCR analyzer
    
    Args:
        state: The state object containing configuration
        
    Returns:
        Updated state with textract client
    """
    try:
        session_kwargs = {
            'region_name': server_config.AMAZON_REGION,
            'aws_access_key_id': server_config.AMAZON_ACCESS_KEY_ID,
            'aws_secret_access_key': server_config.AMAZON_SECRET_ACCESS_KEY
        }
        
        textract_client = boto3.client('textract', **session_kwargs)
        if not state.get('aws'):
            state['aws'] = {}
        state['aws']['textract_client'] = textract_client
        state['status'] = 'success'
        state['message'] = "Textract client created successfully"
        logger.info(f"Initialized Textract client for region: {server_config.AMAZON_REGION}")
        return state
    except Exception as e:
        logger.error(f"Failed to initialize Textract client: {e}")
        state['status'] = 'error'
        state['message'] = f"Failed to initialize Textract client: {e}"
        return state
        

def extract_pages_as_bytes(state: State) -> List[bytes]:
    """
    Extract all pages from PDF as bytes
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of page bytes
    """
    try:
        pdf_path: str = state['pdf_path']
        if not pdf_path or not Path(pdf_path).exists():
            raise RuntimeError(f"Sensory profile pdf path not found: {pdf_path}")

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
        state['status'] = 'success'
        state['message'] = "Extract sp2 page images from pdf"
        state['pages_as_bytes'] = page_bytes_list
        return state

    except Exception as e:
        logger.error(f"Failed to extract pages from PDF: {e}")
        state['status'] = 'error'
        state['message'] = f"Failed to extract pages from PDF: {e}"
        return state
        

def analyze_document(state: State) -> State:
    """
    Analyze a PDF document to extract tables using analyze_document API
    
    Args:
        state: The state object containing the document to analyze
        
    Returns:
        Updated state with analysis results
    """
    try:
        pdf_path = state['pdf_path']
        page_bytes_list = state['pages_as_bytes']
        analyzer = state['aws']['textract_client']
        
        if not page_bytes_list:
            raise ValueError("No pages to analyze")
            
        # Analyze each page
        all_responses = []
        
        for page_num, page_bytes in enumerate(page_bytes_list):
            logger.info(f"📊 Analyzing page {page_num + 1}/{len(page_bytes_list)}")
            
            try:
                # Call Textract analyze_document for this page
                response = analyzer.analyze_document(
                    Document={'Bytes': page_bytes},
                    FeatureTypes=['TABLES', 'FORMS']
                )

                output_path = OUTPUT_DIR / f"aws_sp2_page_{page_num}.json"
                with open(output_path, 'w') as f:
                    json.dump(response, f, indent=4)

                all_responses.append(response)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to analyze page {page_num + 1}: {e}")
                # Continue with next page
        
        if not all_responses:
            raise ValueError("No successful page analyses")
            
        logger.info(f"✅ Successfully analyzed document: {pdf_path}")
        state['aws']['extracted_pages'] = all_responses
        state['status'] = 'success'
        state['message'] = f"✅ Successfully analyzed document: {pdf_path}"
        return state
        
    except Exception as e:
        logger.error(f"Error analyzing document {state['pdf_path']}: {e}")
        state['status'] = 'error'
        state['message'] = f"Error analyzing document: {e}"
        return state


def merge_textract_json_files(state: State):
    """
    Merges multiple AWS Textract JSON response files into a single file.

    Args:
        state: The state object containing the responses to merge
    Returns:
        Updated state with merged response
    """
    responses = state['aws']['extracted_pages']
    if not responses:
        state['status'] = 'error'
        state['message'] = "No responses to merge"
        return state

    merged_data = responses[0]

    # Overwrite page count based on files merged
    merged_data["DocumentMetadata"]["Pages"] = len(responses)

    # Append blocks from remaining files
    for idx, data in enumerate(responses[1:], start=2):
        for block in data.get('Blocks', []):
            block['Page'] = idx
        merged_data['Blocks'].extend(data.get('Blocks', []))
        
    logger.info(f"Successfully merged {len(responses)} responses")
    state['status'] = 'success'
    state['message'] = f"Successfully merged {len(responses)} responses"
    state['aws']['merged_response'] = merged_data
    state['aws']['document'] = Document(merged_data)
    return state


def extract_behavioral_items(state: State) -> State:
    """
    Extract behavioral items and organize them by sensory domain with classification and examples.
    
    Returns:
        Updated state with `sp2_data` formatted as:
        {
            "Seeking": {
                "classification": None,
                "examples": [...]
            },
            ...
        }
    """
    try:
        document = state['aws'].get('document')
        if not document:
            raise ValueError("No document available for extraction")

        # Initialize domain structure
        domain_map = {
            "SK": "Seeking",
            "AV": "Avoiding",
            "SN": "Sensitivity",
            "ET": "Touch",
            "VO": "Visual"
        }

        extracted = defaultdict(lambda: {"classification": None, "examples": []})

        for page in document.pages:
            for table in page.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    if not cells or len(cells) < 3:
                        continue

                    code = cells[0]
                    text = cells[2].strip('"').rstrip("* ")

                    # Skip if not a sensory domain item
                    if code not in domain_map:
                        continue

                    # Check for any SELECTED value in the response columns
                    if any("SELECTED" in cell for cell in cells[3:]):
                        domain = domain_map[code]
                        extracted[domain]["examples"].append(text)

        # Inject into state
        state["sp2_data"] = dict(extracted)
        state["status"] = "success"
        state["message"] = "Successfully extracted behavioral items with domain structure"
        return state

    except Exception as e:
        logger.error(f"Error extracting behavioral items: {e}")
        state["status"] = "error"
        state["message"] = f"Error extracting behavioral items: {e}"
        return state
    

def create_initial_state(pdf_path: str) -> State:
    """Create initial state for the graph execution"""
    return {
        "aws": {},
        "message": None,
        "pages_as_bytes": None,
        "pdf_path": pdf_path,
        "sp2_data": None,
        "status": None
    }


def build_graph():
    
    graph_builder = StateGraph(state_schema=State)

    # Build graph
    graph_builder.add_node("initialize_aws_textract_client", initialize_aws_textract_client)
    graph_builder.add_node("extract_pages_as_bytes", extract_pages_as_bytes)
    graph_builder.add_node("analyze_document", analyze_document)
    graph_builder.add_node("merge_textract_json_files", merge_textract_json_files)
    graph_builder.add_node("extract_behavioral_items", extract_behavioral_items)

    graph_builder.set_entry_point("initialize_aws_textract_client")

    # Add edges
    graph_builder.add_edge("initialize_aws_textract_client", "extract_pages_as_bytes")
    graph_builder.add_edge("extract_pages_as_bytes", "analyze_document")
    graph_builder.add_edge("analyze_document", "merge_textract_json_files")
    graph_builder.add_edge("merge_textract_json_files", "extract_behavioral_items")
    graph_builder.add_edge("extract_behavioral_items", END)

    graph = graph_builder.compile()
    return graph


def extract_sp2_data(pdf_path: str) -> dict:
    """
    Extract sensory profile data from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extraction results and status
    """
    try:
        initial_state = create_initial_state(pdf_path=pdf_path)
        graph: CompiledStateGraph = build_graph()
        final_state: State = graph.invoke(initial_state)
        
        if final_state['status'] == 'error':
            return {
                "status": "error",
                "message": final_state['message'],
                "data": None
            }
            
        return {
            "status": "success",
            "message": final_state['message'],
            "data": final_state.get('sp2_data')
        }
        
    except Exception as e:
        logger.error(f"Error in sensory profile data extraction: {e}")
        return {
            "status": "error",
            "message": f"Error in sensory profile data extraction: {e}",
            "data": None
        }
    

def main():
    FILENAME = '/home/lap-49/Documents/ot-report/assets/inputs/images/Sensory-image-Profile-2-Summary-Report_70247631_1751134355067.pdf'
    print(extract_sp2_data(FILENAME))

if __name__ == "__main__":
    main()