from datetime import datetime
import os
import json
from pathlib import Path
import re
import sys
import time
from traceback import format_exc
from typing import (
    Any,
    Dict,
    List,
    Literal,
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

from ...utils.aws.chomps import parse_chomps_json_response
from ...common.logging import logging
from config import config as server_config



# logging.basicConfig(
#     level=logging.INFO,
#     format="%(filename)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     filename=os.path.join(server_config.PROJECT_DIR, 'logs', __file__)
# )
logger = logging.getLogger(__name__)


class State(TypedDict):
    openai_client: Any
    pdf_path: str 
    aws: "AWSTextractOCRTableAnalyzer"
    full_response: Dict[str, Union[Dict, List]] = {}
    pages_as_bytes: list = []
    aws_raw_responses: list = []
    aws_merged_response: list = {}
    observation_data: dict = {}
    contextual_report: dict[str, list[str]]
    error: str
    status: Literal['success', 'error']
    max_retries: int = 3


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


def get_prompts(observations: str | dict, /):
    prompt = f"""
        You are an expert pediatric occupational therapist interpreting individual ChOMPS assessment items.

        Your task is to read the provided JSON data, which contains patient information and categorized observations. For each observation within `observationsByCategory`, you must add a new key-value pair: `"context": "<your_interpretation>"`.

        Generate a 1–3 sentence clinical interpretation for each observation based on its score. This interpretation should explain what the score says about the child's current skill level.

        Use the following scoring criteria for your interpretation:
        - 2 = YES: Skill is mastered and performed independently
        - 1 = SOMETIMES: Skill is emerging, inconsistent, or performed with difficulty
        - 0 = NOT YET: Skill is not yet developed or attempted

        ---

        🧠 INSTRUCTIONS:
        - Modify the JSON by adding the "context" field to each observation object.
        - The value of "context" should be your clinical interpretation.
        - Use clinical but accessible language.
        - Avoid repeating the item description verbatim in your interpretation.
        - Focus on the functional interpretation of the skill.
        - Reference observed difficulties or strengths based on the score.
        - Frame statements from a third-person professional point of view ("The child...").
        - **IMPORTANT**: Return the complete, modified JSON object. The structure must be identical to the input, with only the `context` key added to each observation.

        ---

        💡 EXAMPLE:

        Input Snippet:
        {{
            "observation": "13. use a filled spoon or fork to bring food to mouth",
            "response": "Yes",
            "score": 2
        }}

        Output Snippet with added context:
        {{
            "observation": "13. use a filled spoon or fork to bring food to mouth",
            "response": "Yes",
            "score": 2,
            "context": "The child consistently demonstrates the ability to self-feed using utensils, indicating age-appropriate fine motor coordination and independent feeding skills."
        }}
        
        ---

        IMPORTANT:
        - Only return a valid JSON object as the response. Do not include any other text, descriptions, or markdown formatting like ```json.
        - The output JSON structure MUST exactly match the input structure.
        
        >>> JSON CONTENT FOR INTERPRETATION
        {observations}
        <<<
        """
    return prompt


def clean_observation(state: State):
    """
    Clean sentence, remove number, dot and space
    from starting of the sentence.
    """
    def clean_sentence(text: str) -> str:
        cleaned_text = re.sub(r'^\d+\.\s+', '', text)
        return text
        

    try:    
        data = state['observation_data']
        observation_data = data["observationsByCategory"]
        
        for cat, observations in observation_data.items():
            cleaned_observations = []
            for ob in observations:
                text = clean_sentence(ob['observation'])
                print(text)
                ob['observation'] = text
                cleaned_observations.append(ob)
            observation_data[cat] = cleaned_observations
        
        data["observationsByCategory"] = observation_data
        state['observation_data'] = data

        logger.info("Saving clean observations data: outputs/aws_chomps_observation_data_cleaned.json")
        with open("outputs/aws_chomps_observation_data_cleaned.json", 'w+') as f:
            f.write(json.dumps(data, indent=4))
    
        return state

    except Exception as e:
        logger.info("Error on clean observations data: {}".format(str(e)))
        state['status']['error']
        state['error'] = "Error on clean observations data: {}".format(str(e))
        return state    

    


def merge_textract_json_response(state: State):
    """
    Merges multiple AWS Textract JSON response files into a single file.

    Args:
        file_paths (list): A list of paths to the JSON files to merge.
        output_file (str): The path to save the merged JSON file.
    """

    aws_raw_responses = state['aws_raw_responses']
    
    merged_data = aws_raw_responses[0]

    # Overwrite page count based on files merged
    merged_data["DocumentMetadata"]["Pages"] = len(aws_raw_responses)

    # Append blocks from remaining files
    for idx, file_path in enumerate(aws_raw_responses[1:], start=2):
        # with open(file_path, 'r') as f:
        #     data = json.load(f)
        data = aws_raw_responses[idx-1]
        for block in data.get('Blocks', []):
            block['Page'] = idx
        merged_data['Blocks'].extend(data.get('Blocks', []))

    # Save the merged data to the output file
    with open("outputs/aws_chomps_page_merged.json", 'w') as f:
        json.dump(merged_data, f, indent=4)
        
    print(f"Successfully merged responses into outputs/aws_chomps_page_merged.json")

    state['aws_merged_response'] = merged_data
    return state


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
        aws_raw_responses = state['aws_raw_responses']

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
                aws_raw_responses.append(response)

                with open(f"outputs/aws_chomps_page_{page_num}.json", 'w+') as f:
                    f.write(json.dumps(response, indent=4))

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
 
        state['full_response'] = full_response
        state['aws_raw_responses'] = aws_raw_responses
        logger.info(f"✅ Successfully analyzed document: {pdf_path}")
        return state
        
    except Exception as e:
        print(format_exc())
        logger.error(f"Error analyzing document {pdf_path}: {e}")
        state['error'] = f"Error analyzing document {pdf_path}: {e}"
        return state


def report_translation(state: State) -> State:
    """Translates observation scores to clinical context using an LLM."""
    logger.info("=== Starting report translation ===")
    MAX_RETRIES = state['max_retries']
    try:
        report_json = state['observation_data']
        llm = state['openai_client']
        logger.info(f"Report JSON length: {len(json.dumps(report_json))} characters")

        observation_category_data = report_json['observationsByCategory']
        for cat_name, observations in observation_category_data.items():

            logger.info("Sending translation prompt to LLM...")
            
            prompt = get_prompts(observations)

            translated_observation = None
            for attempt in range(MAX_RETRIES):

                
                logger.info(f"Sending translation prompt for category '{cat_name}', attempt {attempt + 1}/{MAX_RETRIES}")
                result = llm.invoke(prompt)
                
                logger.info("Received translation response from LLM")
                output = result.content.strip()
                
                print(output)
                
                # Clean up potential markdown
                if output.startswith("```json"):
                    output = output[7:]
                if output.endswith("```"):
                    output = output[:-3]
                output = output.strip()

                logger.info(f"Translation output length: {len(output)} characters")
                
                try:
                    logger.info("Attempting to parse translation output as JSON...")
                    translated_observation = json.loads(output)
                    logger.info("Successfully parsed translation output.")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in report translation: {str(e)}")
                    state['error'] = f"Failed to parse LLM response: {e}"
                    
                time.sleep(0.1)

            if translated_observation is not None:
                observation_category_data[cat_name] = translated_observation
            else:
                logger.error(f"Failed to get translated observations for '{cat_name}' after all retries.")

        report_json['observationsByCategory'] = observation_category_data
        state['translated_report'] = report_json
        return state

    except Exception as e:
        logger.error(f"Error in report translation: {str(e)}")
        state['error'] = f"An unexpected error occurred: {e}"
        return state


def get_context(state: State) -> State:
    """
    This function will get the context in categories.
    """
    try:
        logger.info("Collecting contextual data")
        data: dict = state['observation_data']
        observation_category_data: dict = data['observationsByCategory']
        contextual_report = {}

        for cat_name, observations in observation_category_data.items():
            contextual_observation = []
            for ob in observations:
                contextual_observation.append(ob['context'])
            contextual_report[cat_name] = contextual_observation
        
        state['contextual_report'] = contextual_report

        with open("outputs/aws_chomps_contextual_observations.json", 'w+') as f:
            f.write(json.dumps(contextual_report, indent=4))
        logger.info("Saved the contentual data to: outputs/aws_chomps_contextual_observations.json")
        state['status'] = "success"
        return state
    
    except Exception as e:
        logger.error(f"Error in Get contextual data: {str(e)}")
        state['error'] = f"An unexpected error occurred: {e}"
        return state



def build_graph():
    # GRAPH BUILDER
    graph_builder = StateGraph(state_schema=State)
    graph_builder.add_node("analyze_document", analyze_document)
    graph_builder.add_node("extract_pages_as_bytes", extract_pages_as_bytes)
    graph_builder.add_node("merge_textract_json_response", merge_textract_json_response)
    graph_builder.add_node("parse_chomps_json_response", parse_chomps_json_response)
    graph_builder.add_node("clean_observation", clean_observation)
    graph_builder.add_node("report_translation", report_translation)
    graph_builder.add_node("get_context", get_context)

    # FLOW
    graph_builder.add_edge(START, "extract_pages_as_bytes")
    graph_builder.add_edge("extract_pages_as_bytes", "analyze_document")
    graph_builder.add_edge("analyze_document", "merge_textract_json_response")
    graph_builder.add_edge("merge_textract_json_response", "parse_chomps_json_response")
    graph_builder.add_edge("parse_chomps_json_response", "clean_observation")
    graph_builder.add_edge('clean_observation', 'report_translation')
    graph_builder.add_edge("report_translation", "get_context")
    graph_builder.add_edge("get_context", END)
    
    return graph_builder.compile()


def create_initial_state():
    aws_client = AWSTextractOCRTableAnalyzer(
        aws_access_key_id=server_config.AMAZON_ACCESS_KEY_ID,
        aws_secret_access_key=server_config.AMAZON_SECRET_ACCESS_KEY,
        region_name=server_config.AMAZON_REGION
    )
    openai_client = init_chat_model("openai:gpt-4o")

    return State({
        'aws': aws_client.textract_client,
        'aws_merged_response': {},
        "aws_raw_responses": [],
        "contextual_report": {},
        "full_response": dict(),
        'max_retries': 3,
        "observation_data": {},
        "openai_client": openai_client,
        "pages_as_bytes": list(),
    })


def aws_chomps_data_extract_agent(pdf_path: str, /):
    
    graph = build_graph()

    state = create_initial_state()
    state['pdf_path'] = pdf_path

    final_state = graph.invoke(state)
    full_response = final_state['contextual_report']
    observation_data = final_state['observation_data']

    if final_state.get('status') == 'error':
        return {
            "status": final_state['status']
        }

    with open("outputs/aws_final_full_response.json", 'w+') as f:
        json.dump(full_response, f, indent=4)

    logger.info("Chomps data parsed successfully.`")

    return {
        "status": final_state['status'],
        "full_response": full_response,
        "observation_data": observation_data
    }


def main():
    pdf_path: str = "/home/lap-49/Documents/ot-report/assets/inputs/images/ChOMPS_image.pdf"
    final_state = aws_chomps_data_extract_agent(pdf_path)


if __name__ == "__main__":
    main()