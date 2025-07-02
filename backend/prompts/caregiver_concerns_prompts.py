async def get_caregiver_concerns_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate caregiver concerns narrative prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    parent_name = patient_info.get("parent_guardian", "The caregiver")
    child_name = patient_info.get("name", "the child")
    age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
    
    # Extract actual assessment findings for context
    extracted_data = report_data.get("extracted_data", {})
    bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
    bayley_social = extracted_data.get("bayley4_social", {})
    
    # Determine areas of concern based on scores
    concerns_context = _analyze_assessment_concerns(bayley_cognitive, bayley_social)
    
    if json_format:
        prompt = f"""
        Write a detailed "Caregiver Concerns" section for a pediatric OT evaluation report.

        Details:
        - Child: {child_name} (age: {age})
        - Parent/Guardian: {parent_name}
        - Assessment findings suggest concerns in: {concerns_context}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "paragraph" for the narrative content.
        - Content should be 3-4 sentences, detailed and specific.

        Content Requirements:
        - Start with "{parent_name} expressed concerns regarding {child_name}'s overall development"
        - Include specific, realistic concerns that parents typically report:
          * Attention and focus during activities
          * Fine motor skill development
          * Speech and language development 
          * Behavioral regulation and transitions
          * Social interaction with peers
          * Developmental milestones
        - Use specific examples like "difficulty with transitions", "becomes upset when preferred items removed"
        - Make it personal and realistic to what parents actually say
        - Include both broad developmental concerns and specific behavioral observations
        - Write in professional clinical language but reflecting parental perspective

        JSON response format:
        {{
            "caregiver_concerns": {{
                "type": "paragraph",
                "content": "{parent_name} expressed broad concerns regarding {child_name}'s overall development. She noted that {child_name} becomes easily upset when the iPad is removed, indicating difficulty with transitions and emotional regulation. {parent_name} also reported challenges with {child_name}'s ability to attend to fine motor tasks and maintain focus during structured activities. Of primary concern is {child_name}'s speech and language development, which {parent_name} described as significantly delayed compared to same-age peers."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a detailed "Caregiver Concerns" section for a pediatric OT evaluation report.
        
        Details:
        - Child: {child_name} (age: {age})
        - Parent/Guardian: {parent_name}
        
        Assessment findings suggest concerns in: {concerns_context}
        
        Requirements:
        - Start with "{parent_name} expressed concerns regarding {child_name}'s overall development"
        - Include specific, realistic concerns that parents typically report:
          * Attention and focus during activities
          * Fine motor skill development
          * Speech and language development 
          * Behavioral regulation and transitions
          * Social interaction with peers
          * Developmental milestones
        - Use specific examples like "difficulty with transitions", "becomes upset when preferred items removed"
        - Make it personal and realistic to what parents actually say
        - Include both broad developmental concerns and specific behavioral observations
        - Write in professional clinical language but reflecting parental perspective
        - 3-4 sentences, detailed and specific
        
        Example style: "Ms. [Parent] expressed broad concerns regarding her daughter's overall development. She noted that [child] becomes easily upset when the iPad is removed, indicating difficulty with transitions and emotional regulation. Ms. [Parent] also reported challenges with [child]'s ability to attend to fine motor tasks and maintain focus during structured activities. Of primary concern is [child]'s speech and language development, which Ms. [Parent] described as significantly delayed compared to same-age peers."
        """
        return prompt


def _analyze_assessment_concerns(bayley_cognitive: dict, bayley_social: dict) -> str:
    """Analyze assessment data to identify areas of concern"""
    concerns = []
    
    # Analyze cognitive scores
    if bayley_cognitive.get("scaled_scores"):
        cognitive_scores = bayley_cognitive["scaled_scores"]
        for domain, score in cognitive_scores.items():
            if score < 7:  # Below average range
                concerns.append(f"{domain.lower()} development")
    
    # Analyze social-emotional scores  
    if bayley_social.get("scaled_scores"):
        social_scores = bayley_social["scaled_scores"]
        for domain, score in social_scores.items():
            if score < 7:
                concerns.append(f"{domain.lower()} skills")
    
    # Default concerns if no scores available
    if not concerns:
        concerns = ["fine motor development", "attention and focus", "speech and language development", "behavioral regulation"]
    
    return ", ".join(concerns[:4])  # Limit to top 4 concerns 