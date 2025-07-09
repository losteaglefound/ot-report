import json
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pdfplumber


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
    
    def get_domain_scoring_criteria(self, domain: str) -> Dict[str, str]:
        """
        Get the scoring criteria for a specific domain.
        
        Args:
            domain: The domain name
            
        Returns:
            Dictionary of scoring criteria for the domain
        """
        if domain == 'social_emotional':
            return self.domains_data['social_emotional'].get('scoring_criteria', {})
        elif domain in ['receptive_observations', 'expressive_observations', 'personal_observations', 'play_and_leisure_observations']:
            return self.domains_data['adaptive_behavior'].get('scoring_criteria', {})
        return {}
    
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
        if "/" in score:
            return False
            
        item = self.get_item_details(domain, observation_no)
        if not item:
            return False
        
        # Get the scoring criteria for the domain
        scoring_criteria = self.get_domain_scoring_criteria(domain)
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

def process_bayley_social_adaptive_assessment(pdf_path: str, json_path: str = "assets/inputs/baylay-4-social-and-adaptive-questioner.json") -> Dict:
    """
    Main function to process Bayley-4 social and adaptive behavior assessment PDF and return valid answers.
    
    Args:
        pdf_path: Path to the Bayley-4 PDF file
        json_path: Path to the questioner JSON file
        
    Returns:
        Dictionary with valid answers organized by domain with proper hierarchical structure
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Initialize the detector
    detector = BayleyDomainDetectorSocialAdaptive(json_path)
    
    # Dictionary to store valid answers with proper domain structure
    valid_answers_dict = {
        "social_emotional": {
            "scoring_criteria": detector.get_domain_scoring_criteria("social_emotional"),
            "observations": []
        },
        "adaptive_behavior": {
            "scoring_criteria": detector.get_domain_scoring_criteria("receptive_observations"),  # All adaptive subdomains use same criteria
            "subdomains": {
                "receptive": {
                    "observations": []
                },
                "expressive": {
                    "observations": []
                },
                "personal": {
                    "observations": []
                },
                "play_and_leisure": {
                    "observations": []
                }
            }
        }
    }
    
    # Mapping from detection domains to output structure
    domain_mapping = {
        "social_emotional": ("social_emotional", "observations"),
        "receptive_observations": ("adaptive_behavior", "subdomains", "receptive", "observations"),
        "expressive_observations": ("adaptive_behavior", "subdomains", "expressive", "observations"),
        "personal_observations": ("adaptive_behavior", "subdomains", "personal", "observations"),
        "play_and_leisure_observations": ("adaptive_behavior", "subdomains", "play_and_leisure", "observations")
    }
    
    try:
        with pdfplumber.open(pdf_path) as p:
            for page_num, page in enumerate(p.pages, 1):
                logger.info(f"Processing Bayley-4 social adaptive page {page_num}")
                
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
                    
                    result = detector.process_terminal_line(line)
                    
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
                            
                            next_result = detector.process_terminal_line(next_line)
                            
                            # Stop if new domain is found
                            if next_result['domain']:
                                break
                            
                            # Stop if no answers found (invalid domain content)
                            if not next_result['answers']:
                                break
                            
                            # Add answers from this line
                            all_answers.extend(next_result['answers'])
                            next_line_num += 1
                        
                        # Only process if we found answers
                        if all_answers:
                            # Get the target location in the output structure
                            target_path = domain_mapping.get(current_domain)
                            if target_path:
                                # Navigate to the target location
                                target_location = valid_answers_dict
                                for key in target_path[:-1]:  # All keys except the last one
                                    target_location = target_location[key]
                                
                                target_list = target_location[target_path[-1]]  # The observations list
                                
                                # Validate and add answers
                                for observation_no, score in all_answers:
                                    is_valid = detector.validate_score(current_domain, observation_no, score)
                                    observation_details = detector.get_item_details(current_domain, observation_no)
                                    
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
                                        
                                        target_list.append(valid_observation)
                                        logger.debug(f"Added valid answer: {current_domain} observation {observation_no}: {score}")
                        
                        # Skip to the line where we stopped
                        line_num = next_line_num - 1
                    
                    line_num += 1
                    
    except Exception as e:
        logger.error(f"Error processing Bayley-4 social adaptive PDF {pdf_path}: {e}")
        return {}
    
    # Log summary
    social_count = len(valid_answers_dict["social_emotional"]["observations"])
    adaptive_count = sum(len(subdomain["observations"]) for subdomain in valid_answers_dict["adaptive_behavior"]["subdomains"].values())
    total_observations = social_count + adaptive_count
    
    logger.info(f"Bayley-4 social adaptive processing complete:")
    logger.info(f"  - Social-Emotional: {social_count} valid observations")
    logger.info(f"  - Adaptive Behavior: {adaptive_count} valid observations")
    logger.info(f"  - Total: {total_observations} valid observations")
    
    return valid_answers_dict
