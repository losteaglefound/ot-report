#!/usr/bin/env python3
"""
AWS Pedi-EAT Data Extraction Agent

This script orchestrates a multi-step process to extract structured data from a PDF.
The flow is as follows:
1.  Takes a PDF file as input.
2.  Converts each page of the PDF into an image.
3.  Sends each page image to AWS Textract to get a raw analysis response.
4.  Merges the list of raw responses for each page into a single, consolidated JSON object.
5.  Parses the merged JSON using the trp library.
6.  Extracts observations, categorizes them, and calculates scores.
7.  Outputs the final, structured JSON data to the console.
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import TypedDict, cast, Any, List, Dict, Optional

import boto3
import fitz  # PyMuPDF
from dotenv import load_dotenv
from trp import Document

# Load environment variables from .env file
assert load_dotenv()


# ==============================================================================
# SECTION 1: AWS Textract Document Analyzer
# (Logic from aws_pedieat_textract_document_analyzer.py)
# ==============================================================================

class AWSTextractOCRAnalyzer:
    """
    A class to analyze PDF documents page by page using AWS Textract.
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = 'us-east-1',
    ):
        """Initialize the Textract OCR analyzer."""
        self.region_name = region_name
        self.setup_logging()

        try:
            session_kwargs = {'region_name': region_name}
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                })

            self.textract_client = boto3.client('textract', **session_kwargs)
            self.logger.info(f"Initialized Textract client for region: {region_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Textract client: {e}")
            raise

    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'aws_pedieat_extract_agent.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _extract_pages_as_bytes(self, pdf_path: str) -> List[bytes]:
        """Extract all pages from a PDF as image bytes."""
        try:
            self.logger.info(f"📄 Extracting pages from PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            page_bytes_list = []
            for page_num in range(len(doc)):
                self.logger.info(f"🔄 Processing page {page_num + 1}/{len(doc)}")
                page = doc[page_num]
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                page_bytes_list.append(img_data)
            doc.close()
            self.logger.info(f"✅ Successfully extracted {len(page_bytes_list)} pages as bytes")
            return page_bytes_list
        except Exception as e:
            self.logger.error(f"Failed to extract pages from PDF: {e}")
            raise

    def get_raw_page_responses(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Analyze a PDF to get a list of raw Textract responses for each page."""
        self.logger.info(f"🔍 Starting OCR analysis of document: {pdf_path}")
        page_bytes_list = self._extract_pages_as_bytes(pdf_path)
        all_responses = []

        for page_num, page_bytes in enumerate(page_bytes_list):
            self.logger.info(f"📊 Analyzing page {page_num + 1}/{len(page_bytes_list)} with Textract")
            try:
                response = self.textract_client.analyze_document(
                    Document={'Bytes': page_bytes},
                    FeatureTypes=['TABLES', 'FORMS']
                )
                all_responses.append(response)
            except Exception as e:
                self.logger.error(f"Failed to analyze page {page_num + 1}: {e}")
                # Add an empty response to maintain page count if a page fails
                all_responses.append({
                    "DocumentMetadata": {"Pages": 1},
                    "Blocks": [],
                    "Page": page_num + 1,
                    "Error": str(e)
                })
        
        self.logger.info(f"✅ Successfully received responses for {len(all_responses)} pages.")
        return all_responses


# ==============================================================================
# SECTION 2: Response Merger
# (Logic from aws_pedieat_merge_response.py)
# ==============================================================================

def merge_textract_responses(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merges multiple AWS Textract JSON responses into a single object."""
    if not responses:
        raise ValueError("Response list cannot be empty.")

    # Use a deep copy of the first response as the base
    merged_data = json.loads(json.dumps(responses[0]))
    merged_data["DocumentMetadata"]["Pages"] = len(responses)

    # Append blocks from the remaining files
    for idx, data in enumerate(responses[1:], start=2):
        for block in data.get('Blocks', []):
            block['Page'] = idx
        merged_data['Blocks'].extend(data.get('Blocks', []))
    
    print(f"Successfully merged {len(responses)} responses in memory.")
    return merged_data


# ==============================================================================
# SECTION 3: Data Extractor
# (Logic from aws_pedieat_data_extract.py)
# ==============================================================================

# --- Data Schemas and Types ---
class Observation(TypedDict):
    description: str
    score: str

class ScoringData(TypedDict):
    observations: list[Observation]
    score: str

class ObservationCategory(TypedDict):
    asc_scoring: ScoringData
    desc_scoring: ScoringData

PediateObservations = dict[str, ObservationCategory]


# --- Functional Helpers ---
def get_selected(text: str) -> str | None:
    matches = re.findall(r'\b[A-Z]+\b', text)
    return matches[0] if matches else None

def clean_sentence(text: str) -> str:
    return re.sub(r'^\d+\.\s+', '', text).strip()

def extract_observation_score(row: dict[str, str], scores: dict[str, str]) -> list[str] | None:
    observation = row.get('Observations')
    if not observation:
        return None
    for key, value in row.items():
        if key in scores and "SELECTED" in value and "NOT_SELECTED" not in value:
            if get_selected(value) == "SELECTED":
                return [observation, scores[key]]
    return None

def categorize_observation(
    observation_score: list[str],
    categories: dict[str, list[str]],
    reverse_scoring_questions: list[str]
) -> tuple[str, str, dict[str, str]] | None:
    ob_sentence = clean_sentence(observation_score[0])
    ob_score = observation_score[1]
    for category, questions in categories.items():
        if ob_sentence in questions:
            scoring_type = 'desc_scoring' if ob_sentence in reverse_scoring_questions else 'asc_scoring'
            return category, scoring_type, {'description': ob_sentence, "score": ob_score}
    return None

# --- Main Data Processing Function ---
def process_document_to_pediate_observations(doc: Document) -> PediateObservations:
    """Processes a trp.Document object to extract and structure Pedi-EAT data."""
    columns = ['Observations', 'Never', 'Almost Never', "Sometimes", 'Often', 'Almost Always', 'Always', "Score"]
    scores = {
        "Never": "0", "Almost Never": "1", "Sometimes": "2",
        "Often": "3", "Almost Always": "4", "Always": "5"
    }

    csv_data = [
        {col: cell.text for col, cell in zip(columns, row.cells)}
        for page in doc.pages for table in page.tables for row in table.rows
    ]

    observation_scores = [
        score for row in csv_data
        if (score := extract_observation_score(row, scores)) is not None
    ]
    
    pediate_observations: PediateObservations = {
        category: {
            "asc_scoring": {"observations": [], "score": ""},
            "desc_scoring": {"observations": [], "score": ""}
        } for category in OBSERVATION_CATEGORIES
    }

    for ob_score in observation_scores:
        result = categorize_observation(ob_score, OBSERVATION_CATEGORIES, REVERSE_SCORING_QUESTION)
        if result:
            category, scoring_type, observation_data = result
            cast(ScoringData, pediate_observations[category][scoring_type])['observations'].append(observation_data)

    for category_data in pediate_observations.values():
        for scoring_type in ['asc_scoring', 'desc_scoring']:
            scoring_dict = cast(ScoringData, category_data[scoring_type])
            observations = scoring_dict['observations']
            total_score = sum(int(obs['score']) for obs in observations)
            scoring_dict['score'] = str(total_score)
            
    return pediate_observations

# --- Constants ---
REVERSE_SCORING_QUESTION = [
    "likes to eat", "eats a variety of foods (fruits, vegetables, proteins, etc.)",
    "is willing to stay seated during mealtime", "opens their mouth when food is offered",
    "is willing to touch food with their hands", "will eat mixed texture foods",
    "will eat food warmer than room temperature",
    "is willing to feed self (if younger in age, holds cup, feeds self crackers)",
    "keeps food in mouth when eating (food means non-liquids)",
    "keeps liquids in mouth when drinking", "keeps their tongue inside mouth during eating",
    "acts hungry before meals", "will eat foods that need to be chewed",
    "will eat textured food like coarse oatmeal", "will eat frozen food, like ice cream",
    "chews their food enough", "moves food in their mouth when chewing without help"
]
PHYSIOLOGIC_SYMTOMS = [
    "gets watery eyes when eating", "gets red color around eyes or face when eating",
    "coughs during or after eating",
    "sounds gurgly or like they need to cough or clear their throat during or after 4. eating",
    "sounds different during or after a meal (for example, voice becomes hoarse, 5. high-pitched, or quiet)",
    "chokes or coughs on water or other thin liquids", "moves head down toward chest when swallowing",
    "has food or liquid come out of nose when eating", "gets pale or blue color around his/her lips during meals",
    "breathes faster or harder when eating", "needs to take a break during the meal to rest or catch their breath",
    "gets tired from eating and is not able to finish", "sweats/gets clammy during meals",
    "tilts head back while eating", "burps more than usual while eating", "throws up during mealtime",
    "throws up between meals (from 30 minutes after the last meal until the next 17. meal)",
    "arches back during or after meals",
    "gags when it is time to eat (for example, when they see food or when placed in 19. high chair)",
    "gags with smooth foods like pudding", "gags with textured food like coarse oatmeal",
    "gags, coughs, or vomits when brushing teeth (if your child does not have teeth, 22. select Never. If your child will not allow you to brush his/her teeth, select Always)",
    "gets a bloated tummy after eating", "turns red in face, may cry with stooling", "has gas",
    "drools when eating", "has a hard time eating due to stuffy nose"
]
PROBLEMATIC_MEALTIME_BEHAVIORS = [
    "avoids eating by playing or talking", "has to be told to start eating",
    "has to be reminded to keep eating", "won't eat at meals, but wants food later",
    "stops eating after a few bites", "refuses to eat",
    "shows more stress during meals than during non-meal times (whines, cries, 34. gets angry, tantrums)",
    "insists on food being offered in a certain way (such as, how food is on the plate 36. or what dish or spoon is used, or where they sit)",
    "insists on being fed by the same person(s)", "becomes upset by the smell of food",
    "throws food or pushes food away", "prefers to drink instead of eat", "prefers crunchy foods",
    "eats better when entertained", "takes more than 30 minutes to eat", "needs mealtime to be calm",
    "wants the same food for more than two weeks in a row", "likes to eat",
    "eats a variety of foods (fruits, vegetables, proteins, etc.)",
    "is willing to stay seated during mealtime", "opens their mouth when food is offered",
    "is willing to touch food with their hands"
]
SELECTIVE_RESTRICTIVE_EATING = [
    "will eat mixed texture foods", "will eat food warmer than room temperature",
    "is willing to feed self (if younger in age, holds cup, feeds self crackers)",
    "keeps food in mouth when eating (food means non-liquids)",
    "keeps liquids in mouth when drinking", "keeps their tongue inside mouth during eating",
    "acts hungry before meals", "will eat foods that need to be chewed",
    "will eat textured food like coarse oatmeal", "will eat frozen food, like ice cream",
    "chews their food enough", "moves food in their mouth when chewing without help",
    "sniffs food or objects", "spits food out", "eats too fast"
]
ORAL_PROCESSING = [
    "stores food in their cheek or roof of mouth", "gets food stuck in their cheek or roof of mouth",
    "prefers smooth foods like yogurt", "puts too much food in mouth at one time",
    "puts fingers in mouth to move food", "prefers strong flavors",
    "bites down on the spoon or fork and does not release it easily",
    "grinds teeth when awake (if your child does not have teeth, please select 73. Never.",
    "chews on toys, clothes, or other objects", "has to be reminded to chew food",
    "sucks on food to soften or moisten it, rather than chewing it",
    "chews food but doesn't swallow it", "chews a bite of food for a long time (~30 seconds or longer)",
]

OBSERVATION_CATEGORIES = {
    "physiologic_symtoms": PHYSIOLOGIC_SYMTOMS,
    "problematic_mealtime_bahaviors": PROBLEMATIC_MEALTIME_BEHAVIORS,
    "selective_restrictive_eating": SELECTIVE_RESTRICTIVE_EATING,
    "oral_processing": ORAL_PROCESSING,
}


# ==============================================================================
# SECTION 4: Main Execution
# ==============================================================================

def main():
    """Main function to run the data extraction and processing pipeline."""
    parser = argparse.ArgumentParser(description='Analyze a Pedi-EAT PDF document using AWS Textract.')
    parser.add_argument('pdf_path', help='Path to the PDF file to analyze')
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file '{args.pdf_path}' not found.")
        sys.exit(1)

    try:
        # Step 1: Initialize the analyzer
        analyzer = AWSTextractOCRAnalyzer(
            aws_access_key_id=os.getenv("AMAZON_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AMAZON_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AMAZON_REGION", "us-east-1"),
        )

        # Step 2: Get raw Textract responses for each page
        raw_responses = analyzer.get_raw_page_responses(args.pdf_path)

        # Step 3: Merge the responses into a single object
        merged_response = merge_textract_responses(raw_responses)
        
        # Optional: Save the merged response for debugging
        # with open('outputs/aws_pedieat_page_merged_from_agent.json', 'w') as f:
        #     json.dump(merged_response, f, indent=4)

        # Step 4: Use the extractor to process the merged data
        doc = Document(merged_response)
        final_structured_data = process_document_to_pediate_observations(doc)

        # Step 5: Output the final result
        print("\n🎉 Analysis complete! Final structured JSON output:\n")
        print(json.dumps(final_structured_data, indent=4))

    except Exception as e:
        logging.exception("An error occurred during the extraction pipeline.")
        print(f"❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()