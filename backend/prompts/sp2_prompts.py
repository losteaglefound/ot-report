async def get_sp2_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate SP2 assessment interpretation prompt for pediatric OT reports."""
    
    # SP2 analysis data
    sp2_analysis = report_data.get("assessment_analysis", {}).get("sp2", {})
    
    if json_format:
        prompt = f"""
        Write a detailed Sensory Profile 2 (SP2) interpretation for a pediatric OT report.

        SP2 Analysis: {sp2_analysis}

        Output Requirements:
        - Return the output as a valid JSON object with multiple sections.
        - Use appropriate "type" for each section: "header", "paragraph", "table", or "bullet_points".
        - Create a comprehensive sensory processing interpretation.

        Content Requirements:
        - Explain Seeking, Avoiding, Sensitivity, and Registration scores
        - Include specific score interpretations and quadrant analysis
        - Provide real-world implications for grooming, play, and feeding
        - Describe sensory processing patterns and their impact
        - Include recommendations for sensory strategies
        - Use professional sensory integration terminology
        - Connect findings to functional performance in daily activities

        Focus on how sensory processing affects daily living skills and participation.

        JSON response format:
        {{
            "sp2_overview": {{
                "type": "header",
                "content": "Sensory Profile 2 (SP2) Assessment"
            }},
            "assessment_description": {{
                "type": "paragraph",
                "content": "The Sensory Profile 2 is a standardized assessment that evaluates sensory processing patterns and their impact on daily functioning. The assessment examines four sensory processing quadrants: Seeking, Avoiding, Sensitivity, and Registration."
            }},
            "quadrant_analysis": {{
                "type": "table",
                "content": {{
                    "columns": ["Sensory Quadrant", "Score Range", "Interpretation", "Functional Impact"],
                    "rows": [
                        ["Seeking", "Score range", "Interpretation", "Impact on daily activities"],
                        ["Avoiding", "Score range", "Interpretation", "Impact on daily activities"],
                        ["Sensitivity", "Score range", "Interpretation", "Impact on daily activities"],
                        ["Registration", "Score range", "Interpretation", "Impact on daily activities"]
                    ]
                }}
            }},
            "real_world_implications": {{
                "type": "bullet_points",
                "content": [
                    "Grooming: Impact on self-care activities and hygiene routines",
                    "Play: Effects on toy selection, play preferences, and peer interaction",
                    "Feeding: Influence on food acceptance, mealtime behavior, and nutrition",
                    "Daily Routines: Impact on transitions, sleep, and activity participation"
                ]
            }},
            "sensory_strategies": {{
                "type": "bullet_points",
                "content": [
                    "Environmental modifications to support optimal sensory processing",
                    "Sensory diet activities for regulation and organization",
                    "Specific sensory tools and equipment recommendations",
                    "Caregiver education for implementing sensory strategies"
                ]
            }},
            "intervention_recommendations": {{
                "type": "paragraph",
                "content": "Based on the SP2 findings, occupational therapy intervention should focus on sensory integration principles and environmental modifications to support optimal sensory processing and functional participation in daily activities."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a detailed Sensory Profile 2 (SP2) interpretation for a pediatric OT report.
        
        SP2 Analysis: {sp2_analysis}
        
        Requirements:
        - Explain Seeking, Avoiding, Sensitivity, and Registration scores
        - Include specific score interpretations and quadrant analysis
        - Provide real-world implications for grooming, play, and feeding
        - Describe sensory processing patterns and their impact
        - Include recommendations for sensory strategies
        - Use professional sensory integration terminology
        - Connect findings to functional performance in daily activities
        
        Focus on how sensory processing affects daily living skills and participation.
        """
        return prompt 