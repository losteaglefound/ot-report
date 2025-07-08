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
        # Remove the special case for '/' - only scoring_criteria keys are valid
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

    # Dictionary to store valid answers in the same structure as original JSON
    valid_answers_dict = {}

    with pdfplumber.open(file_path) as p:
        for page_num, page in enumerate(p.pages, 1):
            print(f"\n{'='*60}")
            print(f"PROCESSING PAGE {page_num}")
            print(f"{'='*60}")
            
            # Extract text and split into lines
            text = page.extract_text()
            if text:
                lines = text.splitlines()  # Split by newlines
                
                line_num = 0
                while line_num < len(lines):
                    line = lines[line_num].strip()  # Remove leading/trailing whitespace
                    if line:  # Skip empty lines
                        result = detector.process_terminal_line(line)
                        
                        # Check if domain is detected
                        if result['domain']:
                            current_domain = result['domain']
                            all_answers = []
                            all_lines = [f"Line {line_num + 1}: {line}"]
                            
                            # Add answers from current line if any
                            if result['answers']:
                                all_answers.extend(result['answers'])
                            
                            # Continue collecting answers from subsequent lines
                            next_line_num = line_num + 1
                            while next_line_num < len(lines):
                                next_line = lines[next_line_num].strip()
                                if next_line:
                                    next_result = detector.process_terminal_line(next_line)
                                    
                                    # Stop if new domain is found
                                    if next_result['domain']:
                                        break
                                    
                                    # Stop if no answers found (invalid domain content)
                                    if not next_result['answers']:
                                        break
                                    
                                    # Add answers from this line
                                    all_answers.extend(next_result['answers'])
                                    all_lines.append(f"Line {next_line_num + 1}: {next_line}")
                                    
                                next_line_num += 1
                            
                            # Only process if we found answers
                            if all_answers:
                                print(f"\nDomain: {current_domain.replace('_', ' ').title()}")
                                for line_info in all_lines:
                                    print(line_info)
                                print(f"All Answers: {all_answers}")
                                
                                # Initialize domain in valid_answers_dict if not exists
                                if current_domain not in valid_answers_dict:
                                    valid_answers_dict[current_domain] = []
                                
                                # Create validation results for all answers
                                validation_results = []
                                for item_no, score in all_answers:
                                    is_valid = detector.validate_score(current_domain, item_no, score)
                                    item_details = detector.get_item_details(current_domain, item_no)
                                    
                                    validation_results.append({
                                        'item_no': item_no,
                                        'score': score,
                                        'is_valid': is_valid,
                                        'item_details': item_details
                                    })
                                    
                                    # Add to valid_answers_dict if valid
                                    if is_valid and item_details:
                                        # Create a copy of the original item structure
                                        valid_item = {
                                            "item_no": item_details["item_no"],
                                            "item_description": item_details["item_description"],
                                            "valid_answer": score
                                        }
                                        
                                        # Add optional fields if they exist
                                        if "material" in item_details:
                                            valid_item["material"] = item_details["material"]
                                        if "scoring_criteria" in item_details:
                                            valid_item["scoring_criteria"] = item_details["scoring_criteria"]
                                        if "time_limit" in item_details:
                                            valid_item["time_limit"] = item_details["time_limit"]
                                        if "time_limits" in item_details:
                                            valid_item["time_limits"] = item_details["time_limits"]
                                        if "caregiver_question" in item_details:
                                            valid_item["caregiver_question"] = item_details["caregiver_question"]
                                        if "trial_items" in item_details:
                                            valid_item["trial_items"] = item_details["trial_items"]
                                        if "trial_structure" in item_details:
                                            valid_item["trial_structure"] = item_details["trial_structure"]
                                        if "completion_metrics" in item_details:
                                            valid_item["completion_metrics"] = item_details["completion_metrics"]
                                        if "note" in item_details:
                                            valid_item["note"] = item_details["note"]
                                        
                                        valid_answers_dict[current_domain].append(valid_item)
                                
                                if validation_results:
                                    print("Validation Results:")
                                    for validation in validation_results:
                                        status = "✓" if validation['is_valid'] else "✗"
                                        print(f"  {status} Item {validation['item_no']}: {validation['score']}")
                                        if validation['item_details']:
                                            print(f"    Description: {validation['item_details']['item_description']}")
                            
                            # Skip to the line where we stopped
                            line_num = next_line_num - 1
                    
                    line_num += 1
            else:
                print(f"No text found on page {page_num}")
    
    # Save the valid answers dictionary to a JSON file
    if valid_answers_dict:
        output_file = sconfig.PROJECT_DIR / "assets/outputs/bayley-4-valid-answers.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(valid_answers_dict, f, indent=4, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("VALID ANSWERS SUMMARY")
        print(f"{'='*60}")
        
        total_valid_items = 0
        for domain, items in valid_answers_dict.items():
            print(f"\n🎯 {domain.replace('_', ' ').title()}: {len(items)} valid items")
            total_valid_items += len(items)
            
            # Show first few items as preview
            for i, item in enumerate(items[:3]):
                print(f"   {item['item_no']}: {item['item_description']} → {item['valid_answer']}")
            
            if len(items) > 3:
                print(f"   ... and {len(items) - 3} more items")
        
        print(f"\nTotal valid items across all domains: {total_valid_items}")
        print(f"📁 Valid answers saved to: {output_file}")
        
        # Show sample structure
        print(f"\n{'='*60}")
        print("SAMPLE JSON STRUCTURE")
        print(f"{'='*60}")
        
        sample_domain = list(valid_answers_dict.keys())[0]
        sample_item = valid_answers_dict[sample_domain][0]
        print(f"Sample from {sample_domain}:")
        print(json.dumps({sample_domain: [sample_item]}, indent=2))
    else:
        print("\nNo valid answers found!")

if __name__ == "__main__":
    main()