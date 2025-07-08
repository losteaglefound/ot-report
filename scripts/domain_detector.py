import json
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pdfplumber


from sconfig import config as sconfig
from config import config as bconfig


class BayleyDomainDetector:
    def __init__(self, json_path: str):
        """Initialize the domain detector with the Bayley-4 record form JSON."""
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
        """
        Detect which domain a line belongs to.
        
        Args:
            line: The line of text to analyze
            
        Returns:
            The domain name if detected, None otherwise
        """
        line_lower = line.lower().strip()
        
        for domain, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return domain
        
        return None
    
    def parse_answers(self, line: str) -> List[Tuple[str, str]]:
        """
        Parse answers from a line in the format "item_no: score" or "item_no: /".
        
        Args:
            line: The line of text containing answers
            
        Returns:
            List of tuples (item_no, score) where score is the value or '/' for unanswered
        """
        answers = []
        
        # Pattern to match "number: value" or "number: /"
        pattern = r'(\d+):\s*([0-9/]+|\s*/\s*)'
        matches = re.findall(pattern, line)
        
        for item_no, score in matches:
            # Clean up the score (remove extra spaces)
            score = score.strip()
            answers.append((item_no, score))
        
        return answers
    
    def get_domain_items(self, domain: str) -> List[Dict]:
        """
        Get all items for a specific domain.
        
        Args:
            domain: The domain name
            
        Returns:
            List of items for the domain
        """
        if domain in self.domains_data:
            return self.domains_data[domain]
        return []
    
    def get_item_details(self, domain: str, item_no: str) -> Optional[Dict]:
        """
        Get details for a specific item in a domain.
        
        Args:
            domain: The domain name
            item_no: The item number
            
        Returns:
            Item details if found, None otherwise
        """
        items = self.get_domain_items(domain)
        for item in items:
            if item.get('item_no') == item_no:
                return item
        return None
    
    def validate_score(self, domain: str, item_no: str, score: str) -> bool:
        """
        Validate if a score is valid for a specific item.
        
        Args:
            domain: The domain name
            item_no: The item number
            score: The score to validate
            
        Returns:
            True if valid, False otherwise
        """
        if score == '/':
            return True  # Unanswered is always valid
        
        item = self.get_item_details(domain, item_no)
        if not item:
            return False
        
        scoring_criteria = item.get('scoring_criteria', {})
        return score in scoring_criteria.keys()
    
    def process_terminal_line(self, line: str) -> Dict:
        """
        Process a terminal line to detect domain and extract answers.
        
        Args:
            line: The terminal line to process
            
        Returns:
            Dictionary containing domain, answers, and validation results
        """
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

def main():
    """Example usage of the BayleyDomainDetector."""
    # Initialize the detector
    detector = BayleyDomainDetector('assets/inputs/bayley-4-record-form.json')
    file_path = sconfig.PROJECT_DIR / "assets/inputs/Bayley-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"

    # Example terminal lines
    # test_lines = [
    #     "Cognitive Domain:"
    #     " 1: 2, 5: 1, 10: /, 15: 0",
    #     "Receptive Communication: 3: 1, 7: 2, 12: /",
    #     "Expressive communication results: 2: 0, 8: 2, 14: /",
    #     "Fine motor skills: 4: 1, 9: /, 16: 2",
    #     "Gross motor assessment: 6: 2, 11: 0, 18: /"
    # ]
    
    # Process each line
    # for line in test_lines:
    with pdfplumber.open(file_path) as p:
        for page_num, page in enumerate(p.pages, 1):
            print(f"\n{'='*60}")
            print(f"PROCESSING PAGE {page_num}")
            print(f"{'='*60}")
            
            # Extract text and split into lines
            text = page.extract_text()
            if text:
                lines = text.splitlines()  # Split by newlines
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()  # Remove leading/trailing whitespace
                    if line:  # Skip empty lines
                        result = detector.process_terminal_line(line)
                        
                        # Only print if we found a domain or answers
                        if result['domain'] or result['answers']:
                            print(f"\nLine {line_num}: {result['line']}")
                            
                            if result['domain']:
                                print(f"Domain: {result['domain'].replace('_', ' ').title()}")
                            
                            if result['answers']:
                                print(f"Answers: {result['answers']}")
                                
                                if result['validation_results']:
                                    print("Validation Results:")
                                    for validation in result['validation_results']:
                                        status = "✓" if validation['is_valid'] else "✗"
                                        print(f"  {status} Item {validation['item_no']}: {validation['score']}")
                                        if validation['item_details']:
                                            print(f"    Description: {validation['item_details']['item_description']}")
            else:
                print(f"No text found on page {page_num}")
if __name__ == "__main__":
    main()