"""
SP2 Report Extractor
Clean module for extracting SP2 data in report format
"""

import json

from trp import Document

from sconfig import config as script_config
from aws_sp2_data_extract_report_format import parse_sp2_csv_to_report_format, process_document_to_sp2_report_format




def extract_sp2_report_from_csv(csv_file_path: str) -> dict:
    """
    Extract SP2 data from CSV file and return in report format.
    
    Args:
        csv_file_path: Path to the SP2 CSV file
        
    Returns:
        dict: SP2 data in report format with structure:
            {
                "sp2": {
                    "scoring_criteria": {...},
                    "processing": {...},
                    "quadrant_score_summary": {...},
                    "sensory_and_behavioral_section_score_summary": {...}
                }
            }
    """
    sp2_report = parse_sp2_csv_to_report_format(csv_file_path)
    return {"sp2": sp2_report}


def extract_sp2_report_from_textract(textract_json_path: str) -> dict:
    """
    Extract SP2 data from Amazon Textract JSON and return in report format.
    
    Args:
        textract_json_path: Path to the Amazon Textract JSON file
        
    Returns:
        dict: SP2 data in report format
    """
    with open(textract_json_path, 'r') as f:
        textract_data = json.load(f)
    
    doc = Document(textract_data)
    sp2_report = process_document_to_sp2_report_format(doc)
    return {"sp2": sp2_report}


def extract_sp2_report_from_textract_document(doc: Document) -> dict:
    """
    Extract SP2 data from Amazon Textract Document object and return in report format.
    
    Args:
        doc: TRP Document object
        
    Returns:
        dict: SP2 data in report format
    """
    sp2_report = process_document_to_sp2_report_format(doc)
    return {"sp2": sp2_report}


# Example usage
if __name__ == "__main__":
    # Extract from CSV file
    csv_file = '/home/lap-49/Documents/ot-report/notebook/output.csv'
    result = extract_sp2_report_from_csv(csv_file)
    
    # Print just the SP2 section
    print(json.dumps(result, indent=2)) 