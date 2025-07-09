import json
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pdfplumber


from sconfig import config as sconfig
from config import config as bconfig


class BayleyDomainDetectorSocialAdaptive:
    def __init__(self, json_path: str):
        """Initialize the domain detector with the Bayley-4 social and adaptive behavior record form JSON."""
        self.json_path = Path(json_path)
        self.domains_data = self._load_domains_data()
        self.domain_patterns = self._create_domain_patterns()
        
    def _load_domains_data(self) -> Dict:
        """Load the Bayley-4 social and adaptive behavior record form JSON data."""
        with open(self.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    def _create_domain_patterns(self) -> Dict[str, List[str]]:
        """Create regex patterns to identify each domain."""
        return {
            'social_emotional': [
                r'social[\s\-]?emotional',
                r'social[\s\-]?emotion',
                r'social\s+development',
                r'emotional\s+development',
                r'emotional\s+regulation',
                r'social\s+skills',
                r'emotional\s+skills',
                r'social\s+interaction',
                r'emotional\s+responses'
            ],
            'receptive_observations': [
                r'receptive\s+communication',
                r'receptive\s+language',
                r'understanding\s+communication',
                r'listening\s+skills',
                r'comprehension\s+skills',
                r'receptive',
                r'adaptive.*receptive'
            ],
            'expressive_observations': [
                r'expressive\s+communication',
                r'expressive\s+language',
                r'verbal\s+expression',
                r'communication\s+expression',
                r'speaking\s+skills',
                r'expressive',
                r'adaptive.*expressive'
            ],
            'personal_observations': [
                r'personal\s+daily\s+living',
                r'personal\s+care',
                r'self[\s\-]?care',
                r'personal\s+skills',
                r'daily\s+living\s+skills',
                r'personal\s+independence',
                r'personal',
                r'daily\s+living.*personal'
            ],
            'play_and_leisure_observations': [
                r'play\s+and\s+leisure',
                r'play\s+skills',
                r'leisure\s+skills',
                r'recreational\s+activities',
                r'play\s+activities',
                r'leisure\s+activities',
                r'play.*leisure',
                r'socialization.*play.*leisure'
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
        Parse answers from a line in the format "observation_no: score" or "observation_no: /".
        
        Args:
            line: The line of text containing answers
            
        Returns:
            List of tuples (observation_no, score) where score is the value or '/' for unanswered
        """
        answers = []
        
        # Pattern to match "number: value" or "number: /"
        pattern = r'(\d+):\s*([0-9/]+|\s*/\s*)'
        matches = re.findall(pattern, line)
        
        for observation_no, score in matches:
            # Clean up the score (remove extra spaces)
            score = score.strip()
            answers.append((observation_no, score))
        
        return answers
    
    def get_domain_items(self, domain: str) -> List[Dict]:
        """
        Get all items for a specific domain.
        
        Args:
            domain: The domain name
            
        Returns:
            List of items for the domain
        """
        if domain == 'social_emotional':
            return self.domains_data['social_emotional'].get('social_emotional_observations', [])
        elif domain in ['receptive_observations', 'expressive_observations', 'personal_observations', 'play_and_leisure_observations']:
            return self.domains_data['adaptive_behavior'].get(domain, [])
        return []
    
    def get_item_details(self, domain: str, observation_no: str) -> Optional[Dict]:
        """
        Get details for a specific observation in a domain.
        
        Args:
            domain: The domain name
            observation_no: The observation number
            
        Returns:
            Observation details if found, None otherwise
        """
        items = self.get_domain_items(domain)
        for item in items:
            if item.get('observation_no') == observation_no:
                return item
        return None
    
    def validate_score(self, domain: str, observation_no: str, score: str) -> bool:
        """
        Validate if a score is valid for a specific observation.
        
        Args:
            domain: The domain name
            observation_no: The observation number
            score: The score to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Explicitly reject any score containing "/"
        # if "/" in score:
        #     return False
        item = self.get_item_details(domain, observation_no)
        if not item:
            return False
        
        # Get the scoring criteria for the domain
        if domain == 'social_emotional':
            scoring_criteria = self.domains_data['social_emotional'].get('scoring_criteria', {})
        elif domain in ['receptive_observations', 'expressive_observations', 'personal_observations', 'play_and_leisure_observations']:
            scoring_criteria = self.domains_data['adaptive_behavior'].get('scoring_criteria', {})
        else:
            return False
            
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
            for observation_no, score in answers:
                is_valid = self.validate_score(domain, observation_no, score)
                result['validation_results'].append({
                    'observation_no': observation_no,
                    'score': score,
                    'is_valid': is_valid,
                    'observation_details': self.get_item_details(domain, observation_no)
                })
        
        return result

def main():
    """Example usage of the BayleyDomainDetectorSocialAdaptive."""
    # Initialize the detector
    detector = BayleyDomainDetectorSocialAdaptive("assets/inputs/baylay-4-social-and-adaptive-questioner.json")
    file_path = sconfig.PROJECT_DIR / "assets/inputs/Bayley-4-Social-Emotional-and-Adaptive-Behavior-Scales-Score-Report_70360653_1751082312974.pdf"

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
                                for observation_no, score in all_answers:
                                    is_valid = detector.validate_score(current_domain, observation_no, score)
                                    observation_details = detector.get_item_details(current_domain, observation_no)
                                    
                                    validation_results.append({
                                        'observation_no': observation_no,
                                        'score': score,
                                        'is_valid': is_valid,
                                        'observation_details': observation_details
                                    })
                                    
                                    # Add to valid_answers_dict if valid
                                    if is_valid and observation_details:
                                        # Create a copy of the original observation structure
                                        valid_observation = {
                                            "observation_no": observation_details["observation_no"],
                                            "description": observation_details["description"],
                                            "valid_answer": score
                                        }
                                        
                                        # Add optional fields if they exist
                                        if "scoring_tip" in observation_details:
                                            valid_observation["scoring_tip"] = observation_details["scoring_tip"]
                                        if "scoring_criteria" in observation_details:
                                            valid_observation["scoring_criteria"] = observation_details["scoring_criteria"]
                                        
                                        valid_answers_dict[current_domain].append(valid_observation)
                                
                                if validation_results:
                                    print("Validation Results:")
                                    for validation in validation_results:
                                        status = "✓" if validation['is_valid'] else "✗"
                                        print(f"  {status} Observation {validation['observation_no']}: {validation['score']}")
                                        if validation['observation_details']:
                                            print(f"    Description: {validation['observation_details']['description']}")
                            
                            # Skip to the line where we stopped
                            line_num = next_line_num - 1
                    
                    line_num += 1
            else:
                print(f"No text found on page {page_num}")
    
    # Save the valid answers dictionary to a JSON file
    if valid_answers_dict:
        output_file = sconfig.PROJECT_DIR / "assets/outputs/bayley-4-social-adaptive-valid-answers.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(valid_answers_dict, f, indent=4, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("VALID ANSWERS SUMMARY")
        print(f"{'='*60}")
        
        total_valid_observations = 0
        for domain, observations in valid_answers_dict.items():
            print(f"\n🎯 {domain.replace('_', ' ').title()}: {len(observations)} valid observations")
            total_valid_observations += len(observations)
            
            # Show first few observations as preview
            for i, observation in enumerate(observations[:3]):
                print(f"   {observation['observation_no']}: {observation['description'][:50]}... → {observation['valid_answer']}")
            
            if len(observations) > 3:
                print(f"   ... and {len(observations) - 3} more observations")
        
        print(f"\nTotal valid observations across all domains: {total_valid_observations}")
        print(f"📁 Valid answers saved to: {output_file}")
        
        # Show sample structure
        print(f"\n{'='*60}")
        print("SAMPLE JSON STRUCTURE")
        print(f"{'='*60}")
        
        sample_domain = list(valid_answers_dict.keys())[0]
        sample_observation = valid_answers_dict[sample_domain][0]
        print(f"Sample from {sample_domain}:")
        print(json.dumps({sample_domain: [sample_observation]}, indent=2))
    else:
        print("\nNo valid answers found!")

if __name__ == "__main__":
    main() 