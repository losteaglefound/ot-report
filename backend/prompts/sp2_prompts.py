async def get_sp2_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate SP2 assessment interpretation prompt for pediatric OT reports."""
    
    # Get extracted SP2 data from sensory agent
    extracted_sp2_data = report_data.get("extracted_data", {}).get("sp2", {})
    
    # Also get SP2 analysis data if available for backwards compatibility
    sp2_analysis = report_data.get("assessment_analysis", {}).get("sp2", {})
    
    if json_format:
        prompt = f"""
        Write a detailed Sensory Profile 2 (SP2) interpretation for a pediatric OT report.

        Extracted SP2 Data: {extracted_sp2_data}
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
            "sensory_overview": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILS INTERPRETATION OF WHOLE SENSORY ASSESSMENT.**"
            }},
            "touch_processing_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF TOUCH PROCESSING SCORES AND RESULTS. Include specific score values, percentile ranges, clinical significance, and functional implications for daily activities.**"
            }},
            "oral_sensory_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF ORAL SENSORY SCORES AND RESULTS. Include specific score values, percentile ranges, clinical significance, and impact on feeding and oral motor skills.**"
            }},
            "auditory_processing_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF AUDITORY PROCESSING SCORES AND RESULTS. Include specific score values, percentile ranges, clinical significance, and impact on attention and environmental response.**"
            }},
            "visual_and_movement_processing": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF VISUAL AND MOVEMENT PROCESSING SCORES AND RESULTS. Include specific score values, percentile ranges, clinical significance, and impact on motor planning and spatial awareness.**"
            }},
            "behavioural_response_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF BEHAVIOURAL RESPONSE SCORES AND RESULTS. Include specific score values, percentile ranges, clinical significance, and impact on self-regulation and adaptive behavior.**"
            }},
            "summary": {{
                "type": "paragraph",
                "content": "**REPLACE WITH COMPREHENSIVE SUMMARY OF ALL SP2 FINDINGS. Include overall sensory processing patterns, key areas of concern, functional implications, and recommendations for intervention strategies.**"
            }}
        }}

        IMPORTANT: Replace all content marked with **REPLACE WITH...** with actual clinical interpretations based on the provided SP2 data. Do not output the placeholder instructions literally.

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a detailed Sensory Profile 2 (SP2) interpretation for a pediatric OT report.
        
        Extracted SP2 Data: {extracted_sp2_data}
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