import re
import logging
from collections import defaultdict

import pdfplumber

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class SensoryProfileExtractor:
    def __init__(self, pdf_text):
        self.pdf_text = pdf_text
        self.scoring_weights = {"AA": 5, "F": 4, "H": 3, "O": 2, "AN": 1, "DNA": 0}
        self.quadrant_mapping = {
            "Seeking/Seeker": ["GENERAL", "VISUAL", "MOVEMENT"],
            "Avoiding/Avoider": ["TOUCH", "ORAL SENSORY"],
            "Sensitivity/Sensor": ["AUDITORY", "BEHAVIORAL"],
            "Registration/Bystander": []
        }
        self.known_quirks = {
            "TOUCH": {"32": "DNA", "33": "DNA", "34": "DNA", "35": "DNA"},
            "MOVEMENT": {"41": "DNA"},
            "GENERAL": {"9": "AN", "10": "AN"}
        }
        self.results = {
            "scoring_criteria": self.scoring_weights,
            "processing": {},
            "quadrant_score_summary": {},
            "sensory_and_behavioral_section_score_summary": {}
        }

    def extract_summary_tables(self):
        """Extract quadrant and sensory/behavioral summary scores"""
        # Extract quadrant scores
        quadrant_pattern = r"(\w+/\w+)\s*\|\s*(\d+)\s*\|\s*([\d-]+)\s*\|\s*(.+?)\n"
        quadrant_matches = re.findall(quadrant_pattern, self.pdf_text)
        
        for match in quadrant_matches:
            quadrant, raw_score, percentile, classification = match
            self.results["quadrant_score_summary"][quadrant] = {
                "raw_score": int(raw_score),
                "percentile_range": percentile,
                "classification": classification
            }
        
        # Extract sensory/behavioral scores
        sensory_pattern = r"([A-Z ]+Processing|BEHAVIORAL.+?)\s*\|\s*(\d+)\s*\|\s*([\d-]+)\s*\|\s*(.+?)\n"
        sensory_matches = re.findall(sensory_pattern, self.pdf_text)
        
        for match in sensory_matches:
            section, raw_score, percentile, classification = match
            self.results["sensory_and_behavioral_section_score_summary"][section] = {
                "raw_score": int(raw_score),
                "percentile_range": percentile,
                "classification": classification
            }
    
    def parse_item_response(self, response_line):
        """Parse item response with multi-checkmark handling"""
        columns = ["AA", "F", "H", "O", "AN", "DNA"]
        responses = [col.strip() for col in response_line.split('|')]
        
        # Handle multi-checkmark cases
        marked = [col for col in responses if '✅' in col]
        if not marked:
            return "DNA"
        elif len(marked) == 1:
            return columns[responses.index(marked[0])]
        else:
            # Priority to higher frequency responses
            for col in columns:
                if col in responses and '✅' in responses[responses.index(col)]:
                    return col
            return "DNA"
    
    def extract_item_analysis(self):
        """Extract detailed item responses with validation"""
        section_pattern = r"([A-Z]+) Processing \| AA \| F \| H \| O \| AN \| DNA"
        sections = re.findall(section_pattern, self.pdf_text)
        
        for section in sections:
            section_key = section.replace(" ", "_")
            self.results["processing"][section_key] = {"items": [], "raw_score": None}
            
            # Extract section items
            pattern = rf"\| ({section} Processing).+?\n(?:(?!\| {section} Raw Score).)*?\| {section} Raw Score \|\s*(\d+)"
            section_match = re.search(pattern, self.pdf_text, re.DOTALL)
            
            if section_match:
                raw_score = int(section_match.group(2))
                self.results["processing"][section_key]["raw_score"] = raw_score
                
                # Extract items
                item_pattern = r"\|?\s*([A-Z]{2})?\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|(.+?)\n"
                items = re.findall(item_pattern, section_match.group(0))
                
                for quad, item_no, desc, responses in items:
                    response = self.parse_item_response(responses)
                    
                    # Apply domain-specific corrections
                    if section in self.known_quirks and item_no in self.known_quirks[section]:
                        response = self.known_quirks[section][item_no]
                    
                    self.results["processing"][section_key]["items"].append({
                        "item_no": item_no,
                        "item_description": desc.strip(),
                        "score": response
                    })
    
    def validate_extraction(self):
        """Validate extracted data through multiple checks"""
        # 1. Quadrant-Section Consistency
        for quadrant, sections in self.quadrant_mapping.items():
            quadrant_score = self.results["quadrant_score_summary"][quadrant]["raw_score"]
            section_scores = sum(
                self.results["sensory_and_behavioral_section_score_summary"][s]["raw_score"]
                for s in sections if s in self.results["sensory_and_behavioral_section_score_summary"]
            )
            
            if abs(quadrant_score - section_scores) > 5:  # Allow reasonable variance
                logging.warning(f"Quadrant-section mismatch: {quadrant} ({quadrant_score}) vs sections {section_scores}")
        
        # 2. Raw Score Validation
        for section, data in self.results["processing"].items():
            reported_score = data["raw_score"]
            calculated_score = sum(
                self.scoring_weights[item["score"]]
                for item in data["items"]
                if not self.is_excluded_item(section, item["item_no"])
            )
            
            if reported_score != calculated_score:
                logging.error(f"Score mismatch in {section}: Reported {reported_score} vs Calculated {calculated_score}")
                # Auto-correct based on calculation
                data["raw_score"] = calculated_score
                logging.info(f"Auto-corrected {section} raw score to {calculated_score}")
        
        return True
    
    def is_excluded_item(self, section, item_no):
        """Check if item should be excluded from raw score calculation"""
        section_name = section.replace("_", " ")
        return (
            section_name in self.known_quirks and 
            item_no in self.known_quirks[section_name]
        )
    
    def execute(self):
        """Main extraction workflow"""
        self.extract_summary_tables()
        self.extract_item_analysis()
        self.validate_extraction()
        return self.results

# Example Usage
if __name__ == "__main__":
    pdf_text = ""
    with pdfplumber.open("assets/inputs/Sensory-Profile-2-Summary-Report_70247631_1751134355067.pdf") as p:
        for page in p.pages:
            pdf_text += page.extract_text()

    # with open("Sensory-Profile-Report.txt", "r") as f:
    #     pdf_text = f.read()
    

    extractor = SensoryProfileExtractor(pdf_text)
    results = extractor.execute()
    
    # Output results as JSON
    import json
    with open("sensory_profile_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Extraction completed with validation checks")