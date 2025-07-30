#!/usr/bin/env python3
"""
AWS SP2 Complete Processor
Unified script that:
1. Extracts data from PDF pages using AWS Textract analyze_document API
2. Merges individual page responses
3. Extracts SP2 data in report format
"""

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
import time
from traceback import format_exc
from typing import Dict, List, Optional, Any, TypedDict, cast, Union
import glob
import tempfile
import re

import boto3
from dotenv import load_dotenv
import fitz  # PyMuPDF
from trp import Document

assert load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# SP2 Type definitions for report format
class SP2Item(TypedDict):
    item_no: str
    item_description: str
    score: int


class SP2ProcessingSection(TypedDict):
    items: List[SP2Item]
    raw_score: int


class SP2Processing(TypedDict):
    GENERAL: SP2ProcessingSection
    AUDITORY: SP2ProcessingSection
    VISUAL: SP2ProcessingSection
    TOUCH: SP2ProcessingSection
    MOVEMENT: SP2ProcessingSection
    ORAL_SENSORY: SP2ProcessingSection


class SP2ScoreInfo(TypedDict):
    raw_score: int
    percentile_range: str
    classification: str


class SP2ReportFormat(TypedDict):
    scoring_criteria: Dict[str, int]
    processing: SP2Processing
    quadrant_score_summary: Dict[str, SP2ScoreInfo]
    sensory_and_behavioral_section_score_summary: Dict[str, SP2ScoreInfo]


# Constants for SP2 scoring
SP2_RESPONSE_WEIGHTS = {
    "AA": 5,  # Almost Always
    "F": 4,   # Frequently
    "H": 3,   # Half the time
    "O": 2,   # Occasionally
    "AN": 1,  # Almost Never
    "DNA": 0  # Does Not Apply
}


class AWSSP2CompleteProcessor:
    """
    Complete SP2 processing pipeline from PDF to structured report data
    """
    
    def __init__(self, 
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
            region_name: str = 'us-east-1',
            output_dir: str = 'outputs'
        ):
        """
        Initialize the complete SP2 processor
        
        Args:
            aws_access_key_id: AWS access key ID (optional, can use env vars)
            aws_secret_access_key: AWS secret access key (optional, can use env vars)
            region_name: AWS region name
            output_dir: Directory to store output files
        """
        self.region_name = region_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize Textract client
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
        """Setup logging configuration"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'sp2_complete_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_pages_as_bytes(self, pdf_path: str) -> List[bytes]:
        """
        Extract all pages from PDF as bytes
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of page bytes
        """
        try:
            self.logger.info(f"📄 Extracting pages from PDF: {pdf_path}")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            page_bytes_list = []
            
            for page_num in range(len(doc)):
                self.logger.info(f"🔄 Processing page {page_num + 1}/{len(doc)}")
                
                # Get page
                page = doc[page_num]
                
                # Convert page to image (PNG format)
                pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
                img_data = pix.tobytes("png")
                
                page_bytes_list.append(img_data)
            
            doc.close()
            self.logger.info(f"✅ Successfully extracted {len(page_bytes_list)} pages as bytes")
            return page_bytes_list
            
        except Exception as e:
            self.logger.error(f"Failed to extract pages from PDF: {e}")
            raise

    def analyze_document_pages(self, pdf_path: str, output_prefix: str = "aws_sp2_page") -> List[str]:
        """
        Analyze PDF document page by page and save individual responses
        
        Args:
            pdf_path: Path to the PDF file
            output_prefix: Prefix for output files
            
        Returns:
            List of paths to saved page response files
        """
        try:
            self.logger.info(f"🔍 Starting page-by-page analysis of: {pdf_path}")
            
            # Extract pages as bytes
            page_bytes_list = self.extract_pages_as_bytes(pdf_path)
            
            # Analyze each page and save responses
            page_files = []
            
            for page_num, page_bytes in enumerate(page_bytes_list):
                self.logger.info(f"📊 Analyzing page {page_num + 1}/{len(page_bytes_list)}")
                
                try:
                    # Call Textract analyze_document for this page
                    response = self.textract_client.analyze_document(
                        Document={'Bytes': page_bytes},
                        FeatureTypes=['TABLES', 'FORMS']
                    )
                    
                    # Save individual page response
                    page_file = self.output_dir / f"{output_prefix}_{page_num}.json"
                    with open(page_file, 'w') as f:
                        json.dump(response, f, indent=4)
                    
                    page_files.append(str(page_file))
                    self.logger.info(f"✅ Saved page {page_num + 1} response to: {page_file}")
                    
                    # Add small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to analyze page {page_num + 1}: {e}")
                    # Continue with next page
                    continue
            
            self.logger.info(f"✅ Successfully analyzed {len(page_files)} pages")
            return page_files
            
        except Exception as e:
            self.logger.error(f"Error analyzing document pages: {e}")
            raise

    def merge_textract_responses(self, page_files: List[str], output_file: str) -> str:
        """
        Merge multiple AWS Textract JSON response files into a single file
        
        Args:
            page_files: List of paths to individual page JSON files
            output_file: Path to save the merged JSON file
            
        Returns:
            Path to merged file
        """
        try:
            self.logger.info(f"🔄 Merging {len(page_files)} page responses...")
            
            if not page_files:
                raise ValueError("No page files to merge")

            # Use the first file as the base for the merged data
            with open(page_files[0], 'r') as f:
                merged_data = json.load(f)

            # Update page count based on files merged
            merged_data["DocumentMetadata"]["Pages"] = len(page_files)

            # Append blocks from remaining files
            for idx, file_path in enumerate(page_files[1:], start=2):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for block in data.get('Blocks', []):
                        block['Page'] = idx
                    merged_data['Blocks'].extend(data.get('Blocks', []))

            # Save the merged data
            merged_path = self.output_dir / output_file
            with open(merged_path, 'w') as f:
                json.dump(merged_data, f, indent=4)
                
            self.logger.info(f"✅ Successfully merged {len(page_files)} files into {merged_path}")
            return str(merged_path)
            
        except Exception as e:
            self.logger.error(f"Error merging responses: {e}")
            raise

    def extract_number_from_text(self, text: str) -> Optional[int]:
        """Extract the first number found in text."""
        if not text:
            return None
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else None

    def clean_description(self, text: str) -> str:
        """Clean and format item descriptions."""
        if not text:
            return ""
        
        # Remove quotes and extra formatting
        cleaned = text.replace('"', '').replace("'", '')
        # Remove leading numbers and dots
        cleaned = re.sub(r'^\d+\.?\s*', '', cleaned)
        # Remove asterisks
        cleaned = re.sub(r'\*', '', cleaned)
        # Clean up extra spaces and newlines
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Handle truncated descriptions - if it ends with "for example" add closing parenthesis
        if cleaned.endswith('for example'):
            cleaned += ')'
        elif cleaned.endswith('(for example'):
            cleaned += ')'
        
        # Remove trailing periods only if description seems cut off
        if cleaned.endswith(' .'):
            cleaned = cleaned[:-2].strip()
        
        # Ensure first letter is lowercase unless it's a proper noun
        if cleaned and len(cleaned) > 1:
            if not cleaned[0].isupper() or (cleaned[0].isupper() and cleaned[1].islower()):
                cleaned = cleaned[0].lower() + cleaned[1:]
        
        return cleaned

    def validate_sp2_extraction(self, sp2_report: SP2ReportFormat, csv_file_path: str) -> Dict[str, Any]:
        """
        Validate the extracted SP2 data and provide debugging information
        
        Args:
            sp2_report: The extracted SP2 report
            csv_file_path: Path to the original CSV file for comparison
            
        Returns:
            Dictionary with validation results and debug information
        """
        validation_results = {
            "total_items_extracted": 0,
            "items_by_section": {},
            "score_validation": {},
            "potential_issues": []
        }
        
        # Count items by section
        for section_name, section_data in sp2_report["processing"].items():
            item_count = len(section_data["items"])
            validation_results["items_by_section"][section_name] = item_count
            validation_results["total_items_extracted"] += item_count
            
            # Validate raw scores vs calculated scores
            calculated_score = sum(item["score"] for item in section_data["items"])
            raw_score = section_data["raw_score"]
            
            validation_results["score_validation"][section_name] = {
                "raw_score": raw_score,
                "calculated_score": calculated_score,
                "matches": raw_score == calculated_score
            }
            
            if raw_score != calculated_score:
                validation_results["potential_issues"].append(
                    f"{section_name}: Raw score ({raw_score}) doesn't match calculated score ({calculated_score})"
                )
        
        # Check for common issues
        if validation_results["total_items_extracted"] < 20:
            validation_results["potential_issues"].append(
                f"Low item count ({validation_results['total_items_extracted']}) - expected ~54 items for complete SP2"
            )
        
        # Check for missing scores
        for section_name, section_data in sp2_report["processing"].items():
            zero_score_items = [item for item in section_data["items"] if item["score"] == 0]
            if zero_score_items:
                validation_results["potential_issues"].append(
                    f"{section_name}: {len(zero_score_items)} items have score=0, may indicate parsing issues"
                )
        
        # Log validation results
        self.logger.info(f"📊 SP2 Validation Results:")
        self.logger.info(f"  Total items extracted: {validation_results['total_items_extracted']}")
        for section, count in validation_results["items_by_section"].items():
            score_info = validation_results["score_validation"][section]
            match_status = "✅" if score_info["matches"] else "❌"
            self.logger.info(f"  {section}: {count} items, scores {match_status}")
        
        if validation_results["potential_issues"]:
            self.logger.warning("⚠️  Potential issues found:")
            for issue in validation_results["potential_issues"]:
                self.logger.warning(f"    • {issue}")
        else:
            self.logger.info("✅ No validation issues found")
        
        return validation_results

    def parse_sp2_from_textract_document(self, doc: Document) -> SP2ReportFormat:
        """
        Parse SP2 data from Textract Document object and return in report format
        
        Args:
            doc: TRP Document object
            
        Returns:
            SP2 data in report format
        """
        try:
            self.logger.info("📊 Extracting SP2 data from Textract document...")
            
            # Extract all text content from the document
            csv_data = []
            
            for page in doc.pages:
                # Extract from tables
                for table in page.tables:
                    for row in table.rows:
                        row_data = []
                        for cell in row.cells:
                            row_data.append(cell.text)
                        csv_data.append(row_data)
                
                # Extract from form fields
                if hasattr(page, 'form') and page.form:
                    for field in page.form.fields:
                        if field.key and field.value:
                            csv_data.append([field.key.text, field.value.text])
            
            # Convert to CSV-like format and parse
            temp_csv_content = []
            for row in csv_data:
                temp_csv_content.append(','.join(row))
            
            # Use temporary file for parsing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write('\n'.join(temp_csv_content))
                temp_file_path = f.name
            
            try:
                sp2_report = self.parse_sp2_csv_to_report_format(temp_file_path)
                
                # Validate the extraction
                validation_results = self.validate_sp2_extraction(sp2_report, temp_file_path)
                
            finally:
                os.unlink(temp_file_path)
            
            return sp2_report
            
        except Exception as e:
            self.logger.error(f"Error parsing SP2 from Textract document: {e}")
            raise

    def parse_sp2_csv_to_report_format(self, csv_file_path: str) -> SP2ReportFormat:
        """Parse SP2 CSV and return in report format."""
        
        # Initialize data structures
        processing_data = {
            "GENERAL": {"items": [], "raw_score": 0},
            "AUDITORY": {"items": [], "raw_score": 0},
            "VISUAL": {"items": [], "raw_score": 0},
            "TOUCH": {"items": [], "raw_score": 0},
            "MOVEMENT": {"items": [], "raw_score": 0},
            "ORAL_SENSORY": {"items": [], "raw_score": 0},
            "BEHAVIORAL": {"items": [], "raw_score": 0}
        }
        
        quadrant_scores = {}
        sensory_behavioral_scores = {}
        current_section = ""
        seen_items = set()  # To avoid duplicates
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Parse the CSV data
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            parts = [part.strip() for part in line.split(',')]
            
            # Detect section headers - improved logic
            if "Processing" in line or "BEHAVIORAL" in line:
                if any(keyword in line for keyword in ["GENERAL", "AUDITORY", "VISUAL", "TOUCH", "MOVEMENT", "ORAL", "BEHAVIORAL"]):
                    if "GENERAL Processing" in line:
                        current_section = "GENERAL"
                    elif "AUDITORY Processing" in line:
                        current_section = "AUDITORY"
                    elif "VISUAL Processing" in line:
                        current_section = "VISUAL"
                    elif "TOUCH Processing" in line:
                        current_section = "TOUCH"
                    elif "MOVEMENT Processing" in line:
                        current_section = "MOVEMENT"
                    elif "ORAL SENSORY Processing" in line:
                        current_section = "ORAL_SENSORY"
                    elif "BEHAVIORAL" in line and "Processing" not in line:
                        # Handle "BEHAVIORAL Responses" or similar headers
                        current_section = "BEHAVIORAL"
                    
                    self.logger.debug(f"Section changed to: {current_section}")
            
            # Also detect section changes based on Raw Score lines
            if "Raw Score" in line:
                if "GENERAL Raw Score" in line:
                    current_section = "GENERAL"
                elif "AUDITORY Raw Score" in line:
                    current_section = "AUDITORY"
                elif "VISUAL Raw Score" in line:
                    current_section = "VISUAL"
                elif "TOUCH Raw Score" in line:
                    current_section = "TOUCH"
                elif "MOVEMENT Raw Score" in line:
                    current_section = "MOVEMENT"
                elif "ORAL SENSORY Raw Score" in line:
                    current_section = "ORAL_SENSORY"
                elif "BEHAVIORAL Raw Score" in line:
                    current_section = "BEHAVIORAL"
            
            # Extract raw scores for sections - improved logic
            if "Raw Score" in line and current_section and current_section in processing_data:
                # Look for the score in the line - try multiple patterns
                for part in parts:
                    if re.match(r'^\d+$', part.strip()):
                        score = int(part.strip())
                        processing_data[current_section]["raw_score"] = score
                        break
                # Also check if the score is in a different position
                score_match = re.search(r'Raw Score[,\s]*(\d+)', line)
                if score_match:
                    processing_data[current_section]["raw_score"] = int(score_match.group(1))
            
            # Parse item lines - improved logic with flexible column count
            if len(parts) >= 8:  # More flexible: accept 8+ columns instead of requiring 9
                # Extract item number - be more flexible
                item_number = None
                if len(parts) > 1:
                    # Try multiple ways to extract item number
                    num_match = re.search(r'(\d+)', parts[1])
                    if num_match:
                        item_number = num_match.group(1)
                    else:
                        # Check if item number is in the quadrant column
                        num_match = re.search(r'(\d+)', parts[0])
                        if num_match:
                            item_number = num_match.group(1)
                
                # Extract description - handle multi-part descriptions
                description = ""
                if len(parts) > 2:
                    # Join description parts that might be split across columns
                    desc_parts = []
                    for j in range(2, min(len(parts), 8)):  # Don't go beyond response columns
                        part = parts[j].strip()
                        if part and not any(word in part for word in ["SELECTED", "NOT_SELECTED", "AA", "F", "H", "O", "AN", "DNA"]):
                            # Skip numeric-only parts that might be scores
                            if not re.match(r'^\d+$', part):
                                desc_parts.append(part)
                    
                    if desc_parts:
                        description = " ".join(desc_parts)
                        description = self.clean_description(description)
                
                # Find selected response and calculate score - improved logic
                response = None
                score = 0
                
                # Define the response mapping based on column positions
                # Columns are: Quadrant, Item#, Description, AA, F, H, O, AN, DNA
                response_columns = ["AA", "F", "H", "O", "AN", "DNA"]
                
                # Look for SELECTED responses in the appropriate columns (positions 3-8)
                selected_found = False
                for i, response_type in enumerate(response_columns):
                    col_index = 3 + i  # AA=3, F=4, H=5, O=6, AN=7, DNA=8
                    
                    if col_index < len(parts):
                        cell_content = parts[col_index].strip().upper()
                        # Check for various forms of "SELECTED"
                        if ("SELECTED" in cell_content and "NOT_SELECTED" not in cell_content) or cell_content == "SELECTED":
                            response = response_type
                            score = SP2_RESPONSE_WEIGHTS[response_type]
                            selected_found = True
                            break
                
                # Fallback: if no SELECTED found, look for direct response indicators
                if not selected_found:
                    for i, part in enumerate(parts[3:min(len(parts), 9)], start=3):  # Flexible end range
                        part_clean = part.strip().upper()
                        if part_clean in SP2_RESPONSE_WEIGHTS:
                            response = part_clean
                            score = SP2_RESPONSE_WEIGHTS[part_clean]
                            break
                
                # Additional validation for meaningful items
                if item_number and description and response and current_section in processing_data:
                    # Enhanced filtering for summary/descriptive lines
                    should_skip = False
                    description_lower = description.lower()
                    
                    # Skip obvious summary lines
                    if (description_lower.startswith("my child") or 
                        description_lower.startswith("item response") or
                        description_lower.startswith("quadrant") or
                        len(description) <= 5 or
                        description.isdigit()):
                        should_skip = True
                    
                    # Skip lines that contain the child's name or are summary descriptions
                    elif ("sabrina" in description_lower or
                          "responds much more" in description_lower or
                          "is much more likely" in description_lower or
                          "detects many more" in description_lower or
                          "notices sensory cues" in description_lower or
                          "exhibits behaviors" in description_lower):
                        should_skip = True
                    
                    # Skip item number "0" which are typically summary lines
                    elif item_number == "0":
                        should_skip = True
                    
                    # Skip descriptions that look like score ranges (multiple numbers)
                    elif re.search(r'\d+\s+\d+\s+\d+', description):
                        should_skip = True
                    
                    if not should_skip:
                        # Create unique identifier to avoid duplicates
                        item_key = (item_number, description, current_section)
                        
                        if item_key not in seen_items:
                            item = SP2Item(
                                item_no=item_number,
                                item_description=description,
                                score=score
                            )
                            processing_data[current_section]["items"].append(item)
                            seen_items.add(item_key)
                            
                            # Debug logging for successful items
                            self.logger.debug(f"Added item {item_number} ({response}={score}): {description[:30]}...")
                    else:
                        # Debug log skipped items
                        self.logger.debug(f"Skipped summary line: Item {item_number}: {description[:50]}...")
                
                # Debug logging for problematic cases (only for rows with item numbers)
                elif item_number and description and not response and current_section:
                    self.logger.warning(f"No response found for item {item_number} in {current_section}: {description[:50]}...")
                    self.logger.debug(f"Line parts: {parts[:10]}")  # Only show first 10 parts
        
        # Parse quadrant and section score summaries
        for line in lines:
            line = line.strip()
            parts = line.split(',')
            
            # Parse quadrant scores
            if "Seeking/Seeker" in line and len(parts) >= 4:
                raw_score = self.extract_number_from_text(parts[1]) or 0
                percentile = parts[2].strip() if len(parts) > 2 else ""
                classification = parts[3].strip() if len(parts) > 3 else ""
                quadrant_scores["Seeking/Seeker"] = SP2ScoreInfo(
                    raw_score=raw_score,
                    percentile_range=percentile,
                    classification=classification
                )
            
            elif "Avoiding/Avoider" in line and len(parts) >= 4:
                raw_score = self.extract_number_from_text(parts[1]) or 0
                percentile = parts[2].strip() if len(parts) > 2 else ""
                classification = parts[3].strip() if len(parts) > 3 else ""
                quadrant_scores["Avoiding/Avoider"] = SP2ScoreInfo(
                    raw_score=raw_score,
                    percentile_range=percentile,
                    classification=classification
                )
            
            elif "Sensitivity/Sensor" in line and len(parts) >= 4:
                raw_score = self.extract_number_from_text(parts[1]) or 0
                percentile = parts[2].strip() if len(parts) > 2 else ""
                classification = parts[3].strip() if len(parts) > 3 else ""
                quadrant_scores["Sensitivity/Sensor"] = SP2ScoreInfo(
                    raw_score=raw_score,
                    percentile_range=percentile,
                    classification=classification
                )
            
            elif ("Registration/ Bystander" in line or "Registration/Bystander" in line) and len(parts) >= 4:
                raw_score = self.extract_number_from_text(parts[1]) or 0
                percentile = parts[2].strip() if len(parts) > 2 else ""
                classification = parts[3].strip() if len(parts) > 3 else ""
                quadrant_scores["Registration/Bystander"] = SP2ScoreInfo(
                    raw_score=raw_score,
                    percentile_range=percentile,
                    classification=classification
                )
        
        # Extract sensory and behavioral section scores from the summary table - improved parsing
        for line in lines:
            line = line.strip()
            parts = line.split(',')
            
            # Look for section score summary lines
            section_patterns = [
                ("GENERAL Processing", "GENERAL Processing"),
                ("AUDITORY Processing", "AUDITORY Processing"),
                ("VISUAL Processing", "VISUAL Processing"),
                ("TOUCH Processing", "TOUCH Processing"),
                ("MOVEMENT Processing", "MOVEMENT Processing"),
                ("ORAL SENSORY Processing", "ORAL SENSORY Processing"),
                ("BEHAVIORAL responses", "BEHAVIORAL responses associated with sensory processing")
            ]
            
            for pattern, key in section_patterns:
                if pattern in line and len(parts) >= 4:
                    # Try to extract from different positions
                    raw_score = None
                    percentile = ""
                    classification = ""
                    
                    # Pattern 1: score in position 1
                    if len(parts) > 1:
                        raw_score = self.extract_number_from_text(parts[1])
                    
                    # Pattern 2: Look for percentile ranges
                    for part in parts:
                        if re.search(r'\d+-\d+', part):
                            percentile = part.strip()
                        elif any(cls in part for cls in ["Much More Than Others", "More Than Others", "Just like the Majority of Others", "Less than others", "Much less than others"]):
                            classification = part.strip()
                    
                    # If we found data, store it
                    if raw_score is not None or percentile or classification:
                        # Fall back to processing data raw score if not found in summary
                        if raw_score is None:
                            section_map = {
                                "GENERAL Processing": "GENERAL",
                                "AUDITORY Processing": "AUDITORY", 
                                "VISUAL Processing": "VISUAL",
                                "TOUCH Processing": "TOUCH",
                                "MOVEMENT Processing": "MOVEMENT",
                                "ORAL SENSORY Processing": "ORAL_SENSORY"
                            }
                            if pattern in section_map:
                                raw_score = processing_data[section_map[pattern]]["raw_score"]
                        
                        sensory_behavioral_scores[key] = SP2ScoreInfo(
                            raw_score=raw_score or 0,
                            percentile_range=percentile,
                            classification=classification
                        )
        
        # Calculate raw scores from items if not found in CSV
        for section_name, section_data in processing_data.items():
            if section_data["raw_score"] == 0 and section_data["items"]:
                calculated_score = sum(item["score"] for item in section_data["items"])
                section_data["raw_score"] = calculated_score
        
        # If we don't have summary scores, create them from processing data
        if not sensory_behavioral_scores:
            for section_name, section_data in processing_data.items():
                if section_data["raw_score"] > 0:
                    display_name = f"{section_name.replace('_', ' ')} Processing"
                    sensory_behavioral_scores[display_name] = SP2ScoreInfo(
                        raw_score=section_data["raw_score"],
                        percentile_range="",
                        classification=""
                    )
        
        # Ensure we have entries for all expected sections
        expected_sections = [
            "GENERAL Processing",
            "AUDITORY Processing", 
            "VISUAL Processing",
            "TOUCH Processing",
            "MOVEMENT Processing",
            "ORAL SENSORY Processing"
        ]
        
        for section in expected_sections:
            if section not in sensory_behavioral_scores:
                section_key = section.replace(" Processing", "").replace(" ", "_")
                if section_key in processing_data:
                    sensory_behavioral_scores[section] = SP2ScoreInfo(
                        raw_score=processing_data[section_key]["raw_score"],
                        percentile_range="",
                        classification=""
                    )
        
        # Create the final report format (exclude BEHAVIORAL from main processing sections)
        report = SP2ReportFormat(
            scoring_criteria={
                "AA": 5,
                "F": 4,
                "H": 3,
                "O": 2,
                "AN": 1,
                "DNA": 0
            },
            processing={
                "GENERAL": processing_data["GENERAL"],
                "AUDITORY": processing_data["AUDITORY"],
                "VISUAL": processing_data["VISUAL"],
                "TOUCH": processing_data["TOUCH"],
                "MOVEMENT": processing_data["MOVEMENT"],
                "ORAL_SENSORY": processing_data["ORAL_SENSORY"]
            },
            quadrant_score_summary=quadrant_scores,
            sensory_and_behavioral_section_score_summary=sensory_behavioral_scores
        )
        
        # Log BEHAVIORAL items separately for debugging
        if processing_data["BEHAVIORAL"]["items"]:
            self.logger.info(f"BEHAVIORAL section has {len(processing_data['BEHAVIORAL']['items'])} items (handled separately)")
        
        return report

    def process_sp2_pdf_complete(self, pdf_path: str, output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete SP2 processing pipeline from PDF to structured report data
        
        Args:
            pdf_path: Path to the SP2 PDF file
            output_filename: Optional custom filename for outputs
            
        Returns:
            Dictionary containing SP2 report data and processing metadata
        """
        try:
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                source_name = Path(pdf_path).stem
                output_filename = f"sp2_complete_{source_name}_{timestamp}"
            
            self.logger.info(f"🚀 Starting complete SP2 processing for: {pdf_path}")
            
            # Step 1: Analyze document pages
            self.logger.info("📄 Step 1: Analyzing PDF pages with AWS Textract...")
            page_files = self.analyze_document_pages(pdf_path, f"{output_filename}_page")
            
            if not page_files:
                raise ValueError("No pages were successfully analyzed")
            
            # Step 2: Merge responses
            self.logger.info("🔄 Step 2: Merging page responses...")
            merged_file = f"{output_filename}_merged.json"
            merged_path = self.merge_textract_responses(page_files, merged_file)
            
            # Step 3: Extract SP2 data
            self.logger.info("📊 Step 3: Extracting SP2 data in report format...")
            with open(merged_path, 'r') as f:
                textract_data = json.load(f)
            
            doc = Document(textract_data)
            sp2_report = self.parse_sp2_from_textract_document(doc)
            
            # Step 4: Save final results
            self.logger.info("💾 Step 4: Saving final SP2 report...")
            final_output = {"sp2": sp2_report}
            
            # Save SP2 report
            sp2_output_path = self.output_dir / f"{output_filename}_sp2_report.json"
            with open(sp2_output_path, 'w') as f:
                json.dump(final_output, f, indent=4)
            
            # Create processing metadata
            processing_metadata = {
                "source_pdf": pdf_path,
                "processing_timestamp": datetime.now().isoformat(),
                "pages_processed": len(page_files),
                "page_files": page_files,
                "merged_file": merged_path,
                "sp2_report_file": str(sp2_output_path),
                "total_items_extracted": sum(len(section["items"]) for section in sp2_report["processing"].values()),
                "sections_with_data": [section for section, data in sp2_report["processing"].items() if data["items"]],
                "quadrant_scores_available": len(sp2_report["quadrant_score_summary"]) > 0,
                "sensory_scores_available": len(sp2_report["sensory_and_behavioral_section_score_summary"]) > 0
            }
            
            # Save processing metadata
            metadata_path = self.output_dir / f"{output_filename}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(processing_metadata, f, indent=4)
            
            self.logger.info(f"✅ Complete SP2 processing finished successfully!")
            self.logger.info(f"📊 SP2 Report: {sp2_output_path}")
            self.logger.info(f"📋 Metadata: {metadata_path}")
            self.logger.info(f"📄 Total items extracted: {processing_metadata['total_items_extracted']}")
            
            # Return complete results
            return {
                "sp2_report": final_output,
                "metadata": processing_metadata,
                "files": {
                    "sp2_report": str(sp2_output_path),
                    "metadata": str(metadata_path),
                    "merged_textract": merged_path,
                    "page_files": page_files
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Complete SP2 processing failed: {e}")
            raise


def main():
    """Main function to run the complete SP2 processing script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete SP2 Processing: PDF → AWS Textract → Merge → SP2 Report')
    parser.add_argument(
        'pdf_path', 
        help='Path to the SP2 PDF file to process',
    )
    parser.add_argument(
        '--output-dir', 
        default='outputs', 
        help='Output directory for all results',
    )
    parser.add_argument(
        '--output-filename', 
        help='Custom output filename prefix (without extension)',
    )
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file '{args.pdf_path}' not found.")
        sys.exit(1)
    
    try:
        # Initialize processor
        processor = AWSSP2CompleteProcessor(
            aws_access_key_id=os.getenv("AMAZON_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AMAZON_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AMAZON_REGION", "us-east-1"),
            output_dir=args.output_dir
        )
        
        # Run complete processing
        print(f"🚀 Starting complete SP2 processing pipeline...")
        print(f"📄 Input PDF: {args.pdf_path}")
        print(f"📁 Output Directory: {args.output_dir}")
        
        results = processor.process_sp2_pdf_complete(args.pdf_path, args.output_filename)
        
        print(f"\n🎉 SP2 Processing Complete!")
        print(f"📊 SP2 Report saved to: {results['files']['sp2_report']}")
        print(f"📋 Processing metadata: {results['files']['metadata']}")
        
        # Print summary
        metadata = results['metadata']
        print(f"\n📈 Summary:")
        print(f"  📄 Pages processed: {metadata['pages_processed']}")
        print(f"  📝 Total items extracted: {metadata['total_items_extracted']}")
        print(f"  📊 Sections with data: {', '.join(metadata['sections_with_data'])}")
        print(f"  🎯 Quadrant scores: {'✅' if metadata['quadrant_scores_available'] else '❌'}")
        print(f"  📈 Sensory scores: {'✅' if metadata['sensory_scores_available'] else '❌'}")
        
        # Show sample of SP2 data
        sp2_data = results['sp2_report']['sp2']
        print(f"\n📋 Sample Items:")
        item_count = 0
        for section_name, section_data in sp2_data['processing'].items():
            if section_data['items'] and item_count < 3:
                for item in section_data['items'][:2]:
                    print(f"  • {section_name}: Item {item['item_no']} - {item['item_description'][:50]}...")
                    item_count += 1
                    if item_count >= 3:
                        break
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        print("🔧 Please check:")
        print("  - AWS credentials are configured correctly")
        print("  - You have sufficient Textract permissions")
        print("  - PDF file is a valid SP2 assessment")
        print("  - PyMuPDF is installed (pip install PyMuPDF)")
        sys.exit(1)


if __name__ == "__main__":
    main() 