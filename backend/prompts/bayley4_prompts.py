async def get_bayley4_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate Bayley-4 assessment interpretation prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "The child")
    chronological_age = patient_info.get("chronological_age", {})
    
    # Get extracted Bayley data
    extracted_data = report_data.get("extracted_data", {})
    bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
    bayley_social = extracted_data.get("bayley4_social", {})
    
    # Assessment analysis data
    bayley_analysis = report_data.get("assessment_analysis", {}).get("bayley4", {})
    
    if json_format:
        prompt = f"""
        Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report.

        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Unknown')}
        Bayley-4 Cognitive Data: {bayley_cognitive}
        Bayley-4 Social-Emotional Data: {bayley_social}
        Assessment Analysis: {bayley_analysis}

        Output Requirements:
        - Return the output as a valid JSON object with multiple sections.
        - Use appropriate "type" for each section: "header", "paragraph", "table", or "bullet_points".
        - Create a comprehensive interpretation covering all tested domains.

        Content Requirements:
        - Include specific scaled scores, age equivalents, and percentile rankings
        - Calculate and report percentage delays where applicable
        - Compare performance to chronological age expectations
        - Include range classifications (extremely low, below average, average, above average)
        - Link findings to observed functional limitations
        - Describe specific tasks and child's performance
        - Use professional clinical language
        - Provide detailed interpretation for each domain tested
        - Include implications for intervention planning

        JSON response format:
        {{
            "bayley4_overview": {{
                "type": "header",
                "content": "Bayley Scales of Infant and Toddler Development - Fourth Edition (Bayley-4)"
            }},
            "assessment_summary": {{
                "type": "paragraph",
                "content": "The Bayley-4 assessment was administered to evaluate {child_name}'s developmental functioning across cognitive, language, motor, social-emotional, and adaptive behavior domains. The assessment provides standardized scores that allow comparison to same-age peers and identification of areas of strength and need."
            }},
            "cognitive_domain": {{
                "type": "paragraph",
                "content": "In the Cognitive domain, {child_name} achieved a scaled score that falls within the [range] range (percentile), indicating [interpretation]. Performance in this domain reflects the child's ability to problem-solve, explore the environment, and demonstrate early learning skills."
            }},
            "language_domains": {{
                "type": "paragraph",
                "content": "Language assessment revealed [receptive communication findings] and [expressive communication findings]. These results indicate the child's current level of language comprehension and verbal expression compared to developmental expectations."
            }},
            "motor_domains": {{
                "type": "paragraph",
                "content": "Motor evaluation demonstrated [fine motor findings] and [gross motor findings]. These scores reflect the child's ability to coordinate movements and manipulate objects in the environment."
            }},
            "social_emotional_adaptive": {{
                "type": "paragraph",
                "content": "Social-emotional and adaptive behavior assessment indicated [findings]. These domains reflect the child's ability to interact with others, regulate emotions, and demonstrate age-appropriate self-care skills."
            }},
            "clinical_implications": {{
                "type": "bullet_points",
                "content": [
                    "Areas of strength identified for building intervention strategies",
                    "Specific domains requiring targeted intervention support",
                    "Functional implications for daily activities and participation",
                    "Recommendations for family and intervention team"
                ]
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report.
        
        Patient chronological age: {chronological_age.get('formatted', 'Not available')}
        Assessment Analysis: {bayley_analysis}
        
        Requirements:
        - Include specific scaled scores, age equivalents, and percentile rankings
        - Calculate and report percentage delays where applicable
        - Compare performance to chronological age expectations
        - Include range classifications (extremely low, below average, average, above average)
        - Link findings to observed functional limitations
        - Describe specific tasks and child's performance
        - Use professional clinical language
        - Provide detailed interpretation for each domain tested
        - Include implications for intervention planning
        
        Write as detailed clinical narrative covering all tested domains with specific scores and interpretations.
        """
        return prompt 