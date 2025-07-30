import csv
import json
import re
from typing import Literal, TypedDict, cast, Optional, Dict, List, Any, Union

from trp.trp2_analyzeid import TAnalyzeIdDocument, TAnalyzeIdDocumentSchema
from trp import Document



# Type definitions for report format
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


class SP2QuadrantScoreSummary(TypedDict):
    pass  # Will be dynamically populated


class SP2SensoryBehavioralScoreSummary(TypedDict):
    pass  # Will be dynamically populated


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

SP2_RESPONSE_LABELS = {
    "AA": "Almost Always (90% or more of the time)",
    "F": "Frequently (75% of the time)",
    "H": "Half the Time (50% of the time)",
    "O": "Occasionally (25% of the time)",
    "AN": "Almost Never (10% or less of the time)",
    "DNA": "Does Not Apply"
}


def extract_number_from_text(text: str) -> Optional[int]:
    """Extract the first number found in text."""
    if not text:
        return None
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else None


def clean_description(text: str) -> str:
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


def parse_sp2_csv_to_report_format(csv_file_path: str) -> SP2ReportFormat:
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
                    description = clean_description(description)
            
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
    
    # Parse quadrant and section score summaries
    for line in lines:
        line = line.strip()
        parts = line.split(',')
        
        # Parse quadrant scores
        if "Seeking/Seeker" in line and len(parts) >= 4:
            raw_score = extract_number_from_text(parts[1]) or 0
            percentile = parts[2].strip() if len(parts) > 2 else ""
            classification = parts[3].strip() if len(parts) > 3 else ""
            quadrant_scores["Seeking/Seeker"] = SP2ScoreInfo(
                raw_score=raw_score,
                percentile_range=percentile,
                classification=classification
            )
        
        elif "Avoiding/Avoider" in line and len(parts) >= 4:
            raw_score = extract_number_from_text(parts[1]) or 0
            percentile = parts[2].strip() if len(parts) > 2 else ""
            classification = parts[3].strip() if len(parts) > 3 else ""
            quadrant_scores["Avoiding/Avoider"] = SP2ScoreInfo(
                raw_score=raw_score,
                percentile_range=percentile,
                classification=classification
            )
        
        elif "Sensitivity/Sensor" in line and len(parts) >= 4:
            raw_score = extract_number_from_text(parts[1]) or 0
            percentile = parts[2].strip() if len(parts) > 2 else ""
            classification = parts[3].strip() if len(parts) > 3 else ""
            quadrant_scores["Sensitivity/Sensor"] = SP2ScoreInfo(
                raw_score=raw_score,
                percentile_range=percentile,
                classification=classification
            )
        
        elif ("Registration/ Bystander" in line or "Registration/Bystander" in line) and len(parts) >= 4:
            raw_score = extract_number_from_text(parts[1]) or 0
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
                    raw_score = extract_number_from_text(parts[1])
                
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
        processing=SP2Processing(
            GENERAL=SP2ProcessingSection(
                items=processing_data["GENERAL"]["items"],
                raw_score=processing_data["GENERAL"]["raw_score"]
            ),
            AUDITORY=SP2ProcessingSection(
                items=processing_data["AUDITORY"]["items"],
                raw_score=processing_data["AUDITORY"]["raw_score"]
            ),
            VISUAL=SP2ProcessingSection(
                items=processing_data["VISUAL"]["items"],
                raw_score=processing_data["VISUAL"]["raw_score"]
            ),
            TOUCH=SP2ProcessingSection(
                items=processing_data["TOUCH"]["items"],
                raw_score=processing_data["TOUCH"]["raw_score"]
            ),
            MOVEMENT=SP2ProcessingSection(
                items=processing_data["MOVEMENT"]["items"],
                raw_score=processing_data["MOVEMENT"]["raw_score"]
            ),
            ORAL_SENSORY=SP2ProcessingSection(
                items=processing_data["ORAL_SENSORY"]["items"],
                raw_score=processing_data["ORAL_SENSORY"]["raw_score"]
            )
        ),
        quadrant_score_summary=quadrant_scores,
        sensory_and_behavioral_section_score_summary=sensory_behavioral_scores
    )
    
    return report


def process_document_to_sp2_report_format(doc: Document) -> SP2ReportFormat:
    """Process Amazon Textract document to SP2 report format."""
    
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
    
    # Convert to CSV-like format and use the parser
    import tempfile
    import os
    
    temp_csv_content = []
    for row in csv_data:
        temp_csv_content.append(','.join(row))
    
    # Write to temporary file and parse
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('\n'.join(temp_csv_content))
        temp_file_path = f.name
    
    try:
        report = parse_sp2_csv_to_report_format(temp_file_path)
    finally:
        os.unlink(temp_file_path)
    
    return report


def main():
    """Main function to run the SP2 data extraction in report format."""
    
    # Option 1: Process from Amazon Textract JSON
    textract_filename = '/home/lap-49/Documents/ot-report/outputs/aws_sp2_page_merged.json'
    
    # Option 2: Process from CSV file
    csv_filename = '/home/lap-49/Documents/ot-report/notebook/output.csv'
    
    try:
        print("Processing SP2 data from CSV file to report format...")
        sp2_report = parse_sp2_csv_to_report_format(csv_filename)
        
        # Output the result in the exact format requested
        print("\n=== SP2 Report Format Output ===")
        print(json.dumps({"sp2": sp2_report}, indent=4, default=str))
        
        # Print summary
        print(f"\n=== SP2 Report Summary ===")
        total_items = sum(len(section["items"]) for section in sp2_report["processing"].values())
        print(f"Total items extracted: {total_items}")
        
        print(f"\nItems by section:")
        for section_name, section_data in sp2_report["processing"].items():
            print(f"  {section_name}: {len(section_data['items'])} items (Raw Score: {section_data['raw_score']})")
        
        print(f"\nQuadrant Scores:")
        for quadrant_name, scores in sp2_report["quadrant_score_summary"].items():
            print(f"  {quadrant_name}: Raw Score = {scores['raw_score']}, Classification = {scores['classification']}")
        
        print(f"\nSensory & Behavioral Section Scores:")
        for section_name, scores in sp2_report["sensory_and_behavioral_section_score_summary"].items():
            print(f"  {section_name}: Raw Score = {scores['raw_score']}, Classification = {scores['classification']}")
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error processing SP2 data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 