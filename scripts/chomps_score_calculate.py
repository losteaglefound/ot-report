def parse_chomps_domain_scores_simple(report_data: dict) -> list:
    """
    Simplified version that returns only domain_name and total_score as requested.
    
    Args:
        chomps_data (dict): The CHOMPS observation data with domains and observations
        
    Returns:
        list: List of dictionaries with keys 'domain_name' and 'total_score'
    """
    domain_scores = []
    chomps_data = report_data['extracted_data']['chomps']
    
    for domain_name, observations in chomps_data.items():
        # Skip if not a list of observations
        if not isinstance(observations, list):
            continue
            
        # Calculate total score for this domain
        total_score = sum(
            observation.get('score', 0) 
            for observation in observations 
            if isinstance(observation, dict)
        )
        
        # Add domain score to results
        domain_scores.append({
            'domain_name': domain_name,
            'total_score': total_score
        })
    
    return domain_scores