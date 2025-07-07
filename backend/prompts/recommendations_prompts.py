async def get_recommendations_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate recommendations prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
    
    # Extract assessment analysis for context
    assessment_analysis = report_data.get("assessment_analysis", {})
    
    if json_format:
        prompt = f"""
        Generate specific OT recommendations for a pediatric report based on assessment findings.

        Patient: {child_name} (age: {age})
        Assessment Analysis: {assessment_analysis}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "bullet_points" for the recommendations list.
        - Generate exactly 4 specific recommendations only.

        Content Requirements:
        Create exactly these 4 specific recommendations:
        1. Physical Therapy
        2. Speech Therapy
        3. Infant Stim
        4. Occupational Therapy 2x/week

        Format each recommendation as a clear, actionable statement based on the assessment findings.

        JSON response format:
        {{
            "clinical_recommendations": {{
                "type": "bullet_points",
                "content": [
                    "Physical Therapy",
                    "Speech Therapy", 
                    "Infant Stim",
                    "Occupational Therapy 2x/week"
                ]
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure with exactly these 4 recommendations.
        """
        return prompt
    
    else:
        prompt = f"""
        Generate exactly 4 specific therapy recommendations for a pediatric client based on comprehensive assessment findings.
        
        Patient: {child_name} (age: {age})
        Assessment findings: {assessment_analysis}
        
        Include exactly these 4 recommendations only:
        - Physical Therapy
        - Speech Therapy
        - Infant Stim
        - Occupational Therapy 2x/week
        
        Use bullet point format, be specific and professional.
        """
        return prompt 