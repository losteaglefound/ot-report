async def get_chomps_prompt(chomps_analysis: str, json_format=False) -> str:
    if json_format:
        prompt = f"""
        Write a detailed ChOMPS assessment interpretation for a pediatric OT report.

        ChOMPS Analysis: {chomps_analysis}

        Output Format:
        - Return the output as a valid JSON array of objects.
        - Each object must include:
        - "type": one of "header", "paragraph", "bullet_points", or "table"
        - "content": the content appropriate to the type

        Formatting Rules:
        - Use "header" for section titles
        - Use "paragraph" for narrative interpretations and clinical descriptions
        - Use "bullet_points" for recommendations, observations, or caregiver education lists
        - Use "table" for domain-specific scores, analysis results, or comparison data
        - Tables must be returned as JSON objects with:
            - "columns": list of column names
            - "rows": list of rows, each row as a list of values

        Content Requirements:
        - Report domain-specific ChOMPS scores and levels of concern
        - Describe feeding risks including bolus control, gagging, and food hoarding
        - Include safety considerations and aspiration risk assessment
        - Provide specific clinical recommendations based on findings
        - Address any needs for texture modifications
        - Include caregiver education guidance
        - Use professional terminology related to dysphagia and pediatric feeding
        - Connect assessment findings to the child's functional feeding abilities and participation

        Ensure the structure supports downstream formatting and interface display. Focus on feeding safety, efficiency, and evidence-based recommendations.

        JSON response format:
        {{
            "Physiology": {{
                "type": "header",
                "content": "Physiology"
            }},
            "Physiology Interpretation": {{
                "type": "header",
                "content": "Interpretation..."
            }},
        }}
        """
    
    prompt = f"""
    Write a detailed ChOMPS assessment interpretation for a pediatric OT report.
    
    ChOMPS Analysis: {chomps_analysis}
    
    Requirements:
    - Report domain-specific scores and levels of concern
    - Describe feeding risks including bolus control, gagging, and food hoarding
    - Include safety considerations and aspiration risk assessment
    - Provide specific clinical recommendations
    - Address texture modification needs
    - Include caregiver education recommendations
    - Use professional dysphagia terminology
    - Connect findings to functional feeding abilities
    
    Focus on feeding safety, efficiency, and recommendations for intervention.
    """
    return prompt