async def get_sp2_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate SP2 assessment interpretation prompt for pediatric OT reports."""
    
    # Get extracted SP2 data from sensory agent
    extracted_sp2_data = report_data.get("extracted_data", {}).get("sp2", {})
    
    # Also get SP2 analysis data if available for backwards compatibility
    sp2_analysis = report_data.get("assessment_analysis", {}).get("sp2", {})
    
    if json_format:
        prompt = f"""
        Write a detailed Sensory Profile 2 (SP2) interpretation for a pediatric occupational therapy report.

        Use the provided extracted SP2 data to generate clinically relevant interpretation paragraphs in the following order. Each paragraph should reflect the complexity, tone, and detail of a formal pediatric OT report. Use clear, professional sensory integration terminology, and link sensory behaviors to functional impact.

        Extracted SP2 Data: {extracted_sp2_data}
        SP2 Analysis: {sp2_analysis}

        📄 Output Format:
        Return your response as a valid JSON object with this exact structure:
        {{
            "sensory_overview_summary": {{
                "type": "paragraph",
                "content": "**REPLACE WITH PARAGRAPH 1: Overall summary of child’s sensory profile. Highlight high/low responses, their quadrant context, and global effects on calmness, play, routines. Use data from all categories. If there is both under-responsiveness (e.g., low seeking/visual) and over-responsiveness (e.g., high sensitivity/avoidance), describe it as a "complex sensory profile.""
            }},
            "touch_processing_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH PARAGRAPH 2: Focus on low sensory seeking and reduced visual engagement. Mention examples (e.g., shiny/spinning objects, TV screens) and impact on play, learning, and attention. If Seeking is low, explicitly mention the quadrant score range (e.g., "Less Than Others") and describe how low sensory seeking affects exploration, engagement, and attention in early play."
            }},
            "oral_sensory_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH PARAGRAPH 3: Focus on high avoidance and tactile sensitivity. Include examples (e.g., clothing, grooming, messy textures) and how these affect bathing, dressing, and play. If oral or tactile avoidance is high, include examples of grooming resistance, food selectivity, and physical defensiveness. Mention quadrant score classification (e.g., “Much More Than Others”). Describe how these behaviors interfere with self-care routines and messy or sensory-rich play."
            }},
            "auditory_processing_domain": {{
                "type": "paragraph",
                "content": "**REPLACE WITH PARAGRAPH 4: Describe how auditory, movement, and oral sensory responses may fall in the typical range, but the child shows elevated sensitivity to routine change. Include behavioral manifestations such as tantrums, clinginess, and difficulty calming. If scoring indicates (e.g., 'Much More Than Others'), mention it. Connect this dysregulation to transitions and difficulty adapting to new settings, and root it in the broader pattern of sensitivity and avoidance.**"
            }},
            "visual_and_movement_processing": {{
                "type": "paragraph",
                "content": "**REPLACE WITH PARAGRAPH 5: Provide a summary of the sensory profile, clearly identifying both under-responsiveness (e.g., low seeking/visual engagement) and over-responsiveness (e.g., tactile, auditory, sensitivity). Use quadrant terms when possible. Explain how these mixed patterns may impact self-regulation, transitions, family routines, social participation, and play. End with 1–2 general, actionable recommendations such as routine-based interventions, environmental strategies, or sensory diets to support participation and emotional regulation.**"
            }},
            "summary": {{
                "type": "paragraph",
                "content": "**Duplicate of paragraph 5 or expanded summary across domains. Optional."
            }}
        }}

        🔎 Interpretation Guidelines:
        - Use extracted sensory examples (e.g., Seeking, Avoiding, Sensitivity) to support each paragraph.
        - Identify quadrant patterns (e.g., low Seeking, high Avoiding).
        - Include at least 2–4 behavior examples per paragraph when relevant.
        - Emphasize functional implications: grooming, feeding, transitions, play, attention.
        - Avoid generic language. Be specific and aligned with clinical standards.

        IMPORTANT:
        - Replace all **REPLACE WITH...** sections with final text.
        - Maintain valid JSON format and section order.
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