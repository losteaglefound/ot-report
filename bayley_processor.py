"""
Bayley-4 Assessment PDF Processor
Handles domain detection and valid answer extraction from Bayley-4 assessment PDFs.
"""

import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


class BayleyProcessor:
    def __init__(self, json_path: str):
        """Initialize the Bayley-4 processor with the record form JSON."""
        self.json_path = Path(json_path)
        self.domains_data = self._load_domains_data()
        self.domain_patterns = self._create_domain_patterns()
        
    def _load_domains_data(self) -> Dict:
        """Load the Bayley-4 record form JSON data."""
        with open(self.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    def _create_domain_patterns(self) -> Dict[str, List[str]]:
        """Create regex patterns to identify each domain."""
        return {
            'cognitive': [
                r'cognitive',
                r'cognition',
                r'thinking',
                r'problem[\s\-]?solving',
                r'memory',
                r'attention'
            ],
            'receptive_communication': [
                r'receptive\s+communication',
                r'receptive\s+language',
                r'understanding',
                r'comprehension',
                r'listening'
            ],
            'expressive_communication': [
                r'expressive\s+communication',
                r'expressive\s+language',
                r'speaking',
                r'verbal\s+expression',
                r'communication'
            ],
            'fine_motor': [
                r'fine\s+motor',
                r'fine[\s\-]?motor',
                r'small\s+muscle',
                r'hand\s+skills',
                r'finger\s+skills'
            ],
            'gross_motor': [
                r'gross\s+motor',
                r'gross[\s\-]?motor',
                r'large\s+muscle',
                r'body\s+movement',
                r'physical\s+movement'
            ]
        }
    
    def detect_domain(self, line: str) -> Optional[str]:
        """Detect which domain a line belongs to."""
        line_lower = line.lower().strip()
        
        for domain, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return domain
        
        return None
    
    def parse_answers(self, line: str) -> List[Tuple[str, str]]:
        """Parse answers from a line in the format 'item_no: score'."""
        answers = []
        pattern = r'(\d+):\s*([0-9/]+|\s*/\s*)'
        matches = re.findall(pattern, line)
        
        for item_no, score in matches:
            score = score.strip()
            answers.append((item_no, score))
        
        return answers
    
    def get_item_details(self, domain: str, item_no: str) -> Optional[Dict]:
        """Get details for a specific item in a domain."""
        if domain not in self.domains_data:
            return None
            
        items = self.domains_data[domain]
        for item in items:
            if item.get('item_no') == item_no:
                return item
        return None
    
    def validate_score(self, domain: str, item_no: str, score: str) -> bool:
        """Validate if a score is valid for a specific item (only scoring_criteria keys)."""
        item = self.get_item_details(domain, item_no)
        if not item:
            return False
        
        scoring_criteria = item.get('scoring_criteria', {})
        return score in scoring_criteria.keys()
    
    def process_line(self, line: str) -> Dict:
        """Process a single line to detect domain and extract answers."""
        result = {
            'line': line,
            'domain': None,
            'answers': [],
            'validation_results': []
        }
        
        # Detect domain
        domain = self.detect_domain(line)
        result['domain'] = domain
        
        # Parse answers
        answers = self.parse_answers(line)
        result['answers'] = answers
        
        # Validate answers if domain is detected
        if domain:
            for item_no, score in answers:
                is_valid = self.validate_score(domain, item_no, score)
                result['validation_results'].append({
                    'item_no': item_no,
                    'score': score,
                    'is_valid': is_valid,
                    'item_details': self.get_item_details(domain, item_no)
                })
        
        return result
    
    def create_valid_item(self, item_details: Dict, valid_answer: str) -> Dict:
        """Create a valid item dictionary with the same structure as original JSON."""
        valid_item = {
            "item_no": item_details["item_no"],
            "item_description": item_details["item_description"],
            "valid_answer": valid_answer
        }
        
        # Add optional fields if they exist
        optional_fields = [
            "material", "scoring_criteria", "time_limit", "time_limits",
            "caregiver_question", "trial_items", "trial_structure",
            "completion_metrics", "note"
        ]
        
        for field in optional_fields:
            if field in item_details:
                valid_item[field] = item_details[field]
        
        return valid_item
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Process a Bayley-4 PDF file and extract valid answers.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with valid answers organized by domain
        """
        valid_answers_dict = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"Processing Bayley-4 page {page_num}")
                    
                    # Extract text and split into lines
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.splitlines()
                    line_num = 0
                    
                    while line_num < len(lines):
                        line = lines[line_num].strip()
                        if not line:
                            line_num += 1
                            continue
                        
                        result = self.process_line(line)
                        
                        # Check if domain is detected
                        if result['domain']:
                            current_domain = result['domain']
                            all_answers = []
                            
                            # Add answers from current line if any
                            if result['answers']:
                                all_answers.extend(result['answers'])
                            
                            # Continue collecting answers from subsequent lines
                            next_line_num = line_num + 1
                            while next_line_num < len(lines):
                                next_line = lines[next_line_num].strip()
                                if not next_line:
                                    next_line_num += 1
                                    continue
                                
                                next_result = self.process_line(next_line)
                                
                                # Stop if new domain is found
                                if next_result['domain']:
                                    break
                                
                                # Stop if no answers found (invalid domain content)
                                if not next_result['answers']:
                                    break
                                
                                # Add answers from this line
                                all_answers.extend(next_result['answers'])
                                next_line_num += 1
                            
                            # Process valid answers
                            if all_answers:
                                # Initialize domain in valid_answers_dict if not exists
                                if current_domain not in valid_answers_dict:
                                    valid_answers_dict[current_domain] = []
                                
                                # Validate and add answers
                                for item_no, score in all_answers:
                                    is_valid = self.validate_score(current_domain, item_no, score)
                                    item_details = self.get_item_details(current_domain, item_no)
                                    
                                    if is_valid and item_details:
                                        valid_item = self.create_valid_item(item_details, score)
                                        valid_answers_dict[current_domain].append(valid_item)
                                        logger.debug(f"Added valid answer: {current_domain} item {item_no}: {score}")
                            
                            # Skip to the line where we stopped
                            line_num = next_line_num - 1
                        
                        line_num += 1
                        
        except Exception as e:
            logger.error(f"Error processing Bayley-4 PDF {pdf_path}: {e}")
            return {}
        
        # Log summary
        total_items = sum(len(items) for items in valid_answers_dict.values())
        logger.info(f"Bayley-4 processing complete: {total_items} valid items across {len(valid_answers_dict)} domains")
        
        return valid_answers_dict


def process_bayley_assessment(pdf_path: str, json_path: str = "assets/inputs/bayley-4-record-form.json") -> Dict:
    """
    Main function to process Bayley-4 assessment PDF and return valid answers.
    
    Args:
        pdf_path: Path to the Bayley-4 PDF file
        json_path: Path to the record form JSON file
        
    Returns:
        Dictionary with valid answers organized by domain
    """
    processor = BayleyProcessor(json_path)
    return processor.process_pdf(pdf_path) 