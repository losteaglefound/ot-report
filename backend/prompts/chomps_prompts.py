async def get_chomps_prompt(chomps_analysis: str, json_format=False) -> str:
    if json_format:
        prompt = f"""
        Write a detailed ChOMPS assessment interpretation for a pediatric OT report.

        ChOMPS Analysis: {chomps_analysis}

        Output Requirements:
        - Return the output as a valid JSON object with multiple sections.
        - Use appropriate "type" for each section: "header", "paragraph", "table", or "bullet_points".
        - Create a comprehensive feeding assessment interpretation.

        Content Requirements:
        - Report domain-specific ChOMPS scores and levels of concern
        - Describe feeding risks including bolus control, gagging, and food hoarding
        - Include safety considerations and aspiration risk assessment
        - Provide specific clinical recommendations based on findings
        - Address any needs for texture modifications
        - Include caregiver education guidance
        - Use professional terminology related to dysphagia and pediatric feeding
        - Connect assessment findings to the child's functional feeding abilities and participation

        Ensure the structure supports downstream formatting and interface display. 
        Focus on feeding safety, efficiency, and evidence-based recommendations.

        JSON response format:
        {{
            "chomps_overview": {{
                "type": "header",
                "content": "ChOMPS Assessment (Feeding Evaluation)"
            }},
            "assessment_description": {{
                "type": "paragraph",
                "content": "The ChOMPS assessment evaluates feeding and swallowing function across multiple domains to identify feeding difficulties and safety concerns. This assessment provides critical information for developing feeding intervention strategies."
            }},
            "domain_analysis": {{
                "type": "paragraph",
                "content": "Analysis of ChOMPS domains revealed [specific findings regarding feeding safety, efficiency, and functional abilities]. The assessment identified [level of concern] in [specific domains] that require intervention attention."
            }},
            "feeding_safety": {{
                "type": "paragraph",
                "content": "Feeding safety assessment indicated [safety concerns or absence of concerns]. Specific considerations include [bolus control, aspiration risk, choking episodes, gagging patterns]. These findings suggest [safety recommendations and monitoring needs]."
            }},
            "feeding_efficiency": {{
                "type": "paragraph",
                "content": "Feeding efficiency evaluation demonstrated [timing, coordination, and overall feeding competence]. The child's ability to manage various textures and feeding demands shows [specific efficiency patterns and implications]."
            }},
            "clinical_recommendations": {{
                "type": "bullet_points",
                "content": [
                    "Feeding therapy services to address identified safety and efficiency concerns",
                    "Texture modification recommendations based on swallowing abilities",
                    "Environmental modifications to support optimal feeding performance",
                    "Caregiver education on feeding techniques and safety precautions",
                    "Monitoring protocols for feeding progression and safety",
                    "Coordination with speech-language pathology for comprehensive feeding support"
                ]
            }},
            "intervention_priorities": {{
                "type": "paragraph",
                "content": "Based on ChOMPS findings, intervention priorities focus on [specific priorities based on assessment results]. Regular reassessment will be important to monitor feeding development and adjust intervention strategies as needed."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
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