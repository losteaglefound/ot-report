async def get_pedieat_prompt(pedieat_analysis: str, json_format=False) -> str:
    if json_format:
        pedieat_prompt = f"""
        Write a detailed PediEAT assessment interpretation for a pediatric OT report.

        PediEAT Analysis: {pedieat_analysis}

        Output Requirements:
        - Return the output as a valid JSON object with multiple sections.
        - Use appropriate "type" for each section: "header", "paragraph", "table", or "bullet_points".
        - Create a comprehensive feeding assessment interpretation.

        Content Requirements:
        - Report domain-specific PediEAT scores and percentile rankings
        - Describe feeding physiology findings (oral motor, swallowing safety)
        - Address feeding processing abilities (texture acceptance, utensil use)
        - Include feeding behavior analysis (mealtime behaviors, food selectivity)
        - Provide selectivity assessment (food preferences, acceptance patterns)
        - Include safety considerations and aspiration risk
        - Provide specific clinical recommendations based on findings
        - Address texture modification needs and feeding progression
        - Include caregiver education and mealtime strategies
        - Use professional terminology related to pediatric feeding and dysphagia

        Connect assessment findings to the child's functional feeding abilities and nutritional adequacy.

        JSON response format:
        {{
            "pedieat_overview": {{
                "type": "header",
                "content": "PediEAT Assessment (Feeding Assessment)"
            }},
            "assessment_description": {{
                "type": "paragraph",
                "content": "The PediEAT assessment evaluates feeding and swallowing abilities across four key domains: Physiology, Processing, Behavior, and Selectivity. This comprehensive assessment provides insight into feeding safety, efficiency, and participation."
            }},
            "physiology_domain": {{
                "type": "paragraph",
                "content": "Physiology domain assessment revealed [specific findings regarding oral motor skills, swallowing safety, and physiological feeding functions]. These findings indicate [interpretation of feeding safety and risk factors]."
            }},
            "processing_domain": {{
                "type": "paragraph",
                "content": "Processing domain evaluation demonstrated [texture acceptance, sensory processing of foods, and adaptive feeding skills]. The child's ability to process various food textures and consistencies shows [specific findings and implications]."
            }},
            "behavior_domain": {{
                "type": "paragraph",
                "content": "Behavior domain analysis indicated [mealtime behaviors, attention during feeding, and behavioral responses to food]. These patterns suggest [behavioral implications for feeding intervention]."
            }},
            "selectivity_domain": {{
                "type": "paragraph",
                "content": "Selectivity assessment revealed [food preferences, acceptance patterns, and variety in diet]. The degree of food selectivity demonstrates [impact on nutritional adequacy and feeding development]."
            }},
            "feeding_recommendations": {{
                "type": "bullet_points",
                "content": [
                    "Feeding therapy services to address identified areas of need",
                    "Texture modifications and feeding progression strategies",
                    "Oral motor exercises and feeding skill development",
                    "Mealtime behavioral strategies and environmental modifications",
                    "Caregiver education on safe feeding practices",
                    "Nutritional monitoring and consultation as needed"
                ]
            }},
            "safety_considerations": {{
                "type": "paragraph",
                "content": "Based on the PediEAT findings, feeding safety considerations include [specific safety recommendations and monitoring needs]. Regular reassessment of feeding skills and safety is recommended to ensure optimal nutrition and prevent feeding-related complications."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return pedieat_prompt
    
    pedieat_prompt = f"""
    Write a detailed PediEAT assessment interpretation for a pediatric OT report.

    PediEAT Analysis: {pedieat_analysis}

    Requirements:
    - Report domain-specific scores and levels of concern
    - Describe feeding physiology findings (oral motor, swallowing safety)
    - Address feeding processing abilities (texture acceptance, utensil use)  
    - Include feeding behavior analysis (mealtime behaviors, food selectivity)
    - Include safety considerations and aspiration risk assessment
    - Provide specific clinical recommendations
    - Address texture modification needs and feeding progression
    - Include caregiver education and mealtime strategies
    - Use professional terminology related to pediatric feeding and dysphagia
    - Connect findings to functional feeding abilities and nutritional adequacy
    
    Focus on feeding safety, efficiency, and recommendations for intervention.
    """
    return pedieat_prompt