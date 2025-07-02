async def get_clinical_observations_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate clinical observations narrative prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "The child")
    
    # Extract actual assessment data for specific observations
    extracted_data = report_data.get("extracted_data", {})
    bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
    bayley_social = extracted_data.get("bayley4_social", {})
    clinical_notes = extracted_data.get("clinical_notes", {})
    
    # Analyze scores to determine performance patterns
    performance_analysis = _analyze_performance_patterns(bayley_cognitive, bayley_social)
    
    # Include any extracted clinical observations
    observations = clinical_notes.get("converted_narratives", [])
    
    if json_format:
        prompt = f"""
        Write a detailed "Observation" section for a pediatric OT evaluation report.

        Patient: {child_name}
        Performance analysis: {performance_analysis}
        Specific clinical observations from assessment: {'; '.join(observations[:3]) if observations else 'Standard pediatric assessment observations'}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "paragraph" for the narrative content.
        - Content should be 6-8 sentences with rich clinical detail.

        Content Requirements:
        - Start with "{child_name} participated in an in-clinic evaluation with [his/her] mother present"
        - Include detailed clinical observations:
          * Affect and general presentation (cheerful, cooperative, etc.)
          * Muscle tone and range of motion assessment
          * Attention span and distractibility levels
          * Engagement patterns and task participation
          * Response to structured vs. self-directed activities
          * Fine motor coordination and visual-motor skills
          * Need for cues, redirection, and assistance levels
          * Specific behavioral observations during testing
          * Impact on standardized testing validity
        - Use professional clinical terminology
        - Include specific details like "required hand-over-hand assistance", "maximal verbal/visual cues"
        - Mention testing modifications needed
        - Match the professional tone of clinical evaluation reports

        JSON response format:
        {{
            "clinical_observations": {{
                "type": "paragraph",
                "content": "{child_name} participated in an in-clinic evaluation with the caregiver present. {child_name} presented with a cooperative affect initially but demonstrated variable attention span throughout the assessment. Muscle tone appeared typical for chronological age, with adequate range of motion observed. However, participation was impacted by distractibility and need for frequent redirection. During structured tasks, {child_name} required verbal and visual cues to maintain engagement. Fine motor coordination showed areas for development, with tasks requiring hand-over-hand assistance for completion. These factors impacted standardized testing and required modifications to maintain participation."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a detailed "Observation" section for a pediatric OT evaluation report.
        
        Patient: {child_name}
        Performance analysis: {performance_analysis}
        
        Specific clinical observations from assessment: {'; '.join(observations[:3]) if observations else 'Standard pediatric assessment observations'}
        
        Requirements:
        - Start with "{child_name} participated in an in-clinic evaluation with [his/her] mother present"
        - Include detailed clinical observations:
          * Affect and general presentation (cheerful, cooperative, etc.)
          * Muscle tone and range of motion assessment
          * Attention span and distractibility levels
          * Engagement patterns and task participation
          * Response to structured vs. self-directed activities
          * Fine motor coordination and visual-motor skills
          * Need for cues, redirection, and assistance levels
          * Specific behavioral observations during testing
          * Impact on standardized testing validity
        
        - Use professional clinical terminology
        - Include specific details like "required hand-over-hand assistance", "maximal verbal/visual cues"
        - Mention testing modifications needed
        - Write 6-8 sentences with rich clinical detail
        - Match the professional tone of clinical evaluation reports
        
        Example elements to include: muscle tone assessment, attention span observations, task engagement, assistance levels needed, behavioral responses, testing conditions impact.
        """
        return prompt


def _analyze_performance_patterns(bayley_cognitive: dict, bayley_social: dict) -> str:
    """Analyze performance patterns from assessment scores"""
    patterns = []
    
    # Analyze cognitive performance
    if bayley_cognitive.get("scaled_scores"):
        cog_scores = list(bayley_cognitive["scaled_scores"].values())
        avg_score = sum(cog_scores) / len(cog_scores) if cog_scores else 0
        
        if avg_score < 7:
            patterns.append("below average cognitive-motor performance")
        elif avg_score > 13:
            patterns.append("above average cognitive-motor abilities")
        else:
            patterns.append("mixed cognitive-motor profile")
    
    # Analyze social-emotional performance
    if bayley_social.get("scaled_scores"):
        social_scores = list(bayley_social["scaled_scores"].values())
        avg_score = sum(social_scores) / len(social_scores) if social_scores else 0
        
        if avg_score < 7:
            patterns.append("challenges in social-emotional development")
        elif avg_score > 13:
            patterns.append("strengths in social-emotional areas")
        else:
            patterns.append("typical social-emotional functioning")
    
    return "; ".join(patterns) if patterns else "varied performance across developmental domains" 