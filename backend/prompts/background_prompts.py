async def get_background_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate background narrative prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    patient_name = patient_info.get('name', 'the client')
    age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
    
    # Extract assessment context
    extracted_data = report_data.get("extracted_data", {})
    bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
    bayley_social = extracted_data.get("bayley4_social", {})
    
    assessment_context = ""
    if bayley_cognitive.get("raw_scores") or bayley_social.get("raw_scores"):
        assessment_context = f"""
        Assessment Context:
        - Bayley-4 Cognitive/Language/Motor assessment completed
        - Bayley-4 Social-Emotional/Adaptive Behavior assessment completed
        - Patient age: {age}
        - Comprehensive developmental evaluation across multiple domains
        """
    
    if json_format:
        prompt = f"""
        Write a professional "Reason for referral and background information" section for a pediatric OT evaluation report.

        Patient: {patient_name} (age: {age})
        {assessment_context}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "paragraph" for the narrative content.
        - Content should be 2-3 sentences maximum.

        Content Requirements:
        - Start with "A developmental evaluation was recommended by the Regional Center..."
        - Explain the purpose: determine current level of performance and guide service frequency recommendations for early intervention
        - Keep it concise but professional
        - Use clinical terminology appropriate for a pediatric OT evaluation
        - Match the tone and format of professional OT reports

        JSON response format:
        {{
            "background_narrative": {{
                "type": "paragraph",
                "content": "A developmental evaluation was recommended by the Regional Center to determine {patient_name}'s current level of performance and to guide service frequency recommendations for early intervention..."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a professional "Reason for referral and background information" section for a pediatric OT evaluation report. 
        
        Patient: {patient_name} (age: {age})
        {assessment_context}
        
        Requirements:
        - Start with "A developmental evaluation was recommended by the Regional Center..."
        - Explain the purpose: determine current level of performance and guide service frequency recommendations for early intervention
        - Keep it concise but professional
        - Use clinical terminology appropriate for a pediatric OT evaluation
        - Match the tone and format of professional OT reports
        
        Write 2-3 sentences maximum, similar to this style: "A developmental evaluation was recommended by the Regional Center to determine [patient name]'s current level of performance and to guide service frequency recommendations for early intervention."
        """
        return prompt 