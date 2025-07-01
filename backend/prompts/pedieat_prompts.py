async def get_pedieat_prompt(pedieat_analysis: str, json_format=False) -> str:
    if json_format:
        pedieat_prompt = f"""
        Write a detailed PediEAT assessment interpretation for a pediatric OT report.

        PediEAT Analysis: {pedieat_analysis}

        Output Requirements:
        - Format the output as a valid JSON object.
        - Each section must include a "type" key specifying the content type: "header", "paragraph", or "bullet_points".
        - Use "header" for section titles, "paragraph" for narrative text, and "bullet_points" for concise lists.
        - Maintain a logical order of interpretation: Physiology, Processing, Mealtime Behavior, Selectivity, Safety & Endurance, Family Dynamics, Nutritional Risk, Growth/Development, Recommendations.
        - Use professional feeding assessment terminology.
        - Connect findings to functional mealtime participation.

        # Content Requirements:
        # - Interpret elevated symptoms in the domains: Physiology, Processing, Mealtime Behavior, and Selectivity.
        # - Identify safety and endurance concerns during meals.
        # - Describe impact on family mealtime dynamics.
        # - Include nutritional risk assessment.
        # - Provide intervention recommendations.
        # - Address growth and development concerns.
        # - Focus on comprehensive feeding assessment and family-centered intervention planning.

        JSON response format:
        {{
            "Physiology": {{
                "type": "header",
                "content": "Physiology"
            }},
            "Physiology Interpretation": {{
                "type": "paragraph",
                "content": "The PediEAT assessment did not indicate any elevated symptoms in the domain of physiology. This suggests that the child does not exhibit significant physiological challenges such as dysphagia, oral-motor dysfunction, or other related issues that would impede the mechanical aspects of feeding. The absence of physiological concerns supports functional oral intake without apparent physical barriers."
            }},
        }}
        """
        return pedieat_prompt
    
    pedieat_prompt = f"""
    Write a detailed PediEAT assessment interpretation for a pediatric OT report.
    
    PediEAT Analysis: {pedieat_analysis}
    
    Requirements:
    - Interpret elevated symptoms in Physiology, Processing, Mealtime Behavior, and Selectivity domains
    - Identify safety and endurance concerns during meals
    - Describe impact on family mealtime dynamics
    - Include nutritional risk assessment
    - Provide intervention recommendations
    - Address growth and development concerns
    - Use professional feeding assessment terminology
    - Connect findings to functional mealtime participation
    
    Focus on comprehensive feeding assessment and family-centered intervention planning.
    """
    return pedieat_prompt