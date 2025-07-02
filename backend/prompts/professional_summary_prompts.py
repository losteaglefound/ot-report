async def get_professional_summary_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate professional summary prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "The child")
    age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
    
    # Extract and analyze all assessment data
    extracted_data = report_data.get("extracted_data", {})
    bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
    bayley_social = extracted_data.get("bayley4_social", {})
    assessment_analysis = report_data.get("assessment_analysis", {})
    
    # Analyze overall performance pattern
    overall_analysis = _generate_overall_performance_analysis(bayley_cognitive, bayley_social)
    
    # Identify strengths and needs
    strengths = _identify_assessment_strengths(bayley_cognitive, bayley_social)
    needs = _identify_assessment_needs(bayley_cognitive, bayley_social)
    
    if json_format:
        prompt = f"""
        Write a comprehensive professional "Summary" section for a pediatric OT evaluation report.

        Patient: {child_name} (chronological age: {age})
        Overall Performance Analysis: {overall_analysis}
        Key Strengths: {strengths}
        Areas of Need: {needs}
        Assessment Analysis: {assessment_analysis}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "paragraph" for the narrative content.
        - Content should be 6-8 sentences comprehensive summary.

        Content Requirements:
        - Start with "{child_name} (chronological age: {age}) was assessed using multiple standardized pediatric assessment tools..."
        - Include specific delay percentages where applicable
        - Mention both areas of strength and areas requiring intervention
        - Discuss impact on functional performance and daily activities
        - Recommend multidisciplinary intervention approach
        - Include prognosis and benefit from services
        - Address family involvement and education needs
        - Mention regular monitoring and reassessment
        - Use professional clinical language typical of pediatric OT summaries

        Example elements to include:
        - "The comprehensive evaluation revealed both areas of strength and areas requiring targeted intervention support"
        - "Based on the assessment findings, occupational therapy services are recommended..."
        - "A collaborative, family-centered approach involving [services] will be beneficial..."
        - "Regular monitoring and reassessment will be important to track progress..."
        - "This assessment provides a foundation for developing an individualized intervention plan..."

        Focus on evidence-based conclusions and specific recommendations based on actual assessment findings.

        JSON response format:
        {{
            "professional_summary": {{
                "type": "paragraph",
                "content": "{child_name} (chronological age: {age}) was assessed using multiple standardized pediatric assessment tools to evaluate developmental functioning across cognitive, motor, sensory processing, and adaptive behavior domains. The comprehensive evaluation revealed both areas of emerging strength and areas requiring targeted intervention support. Based on the assessment findings, occupational therapy services are recommended to address identified areas of need and support optimal developmental progression. A collaborative, family-centered approach involving occupational therapy and related services will be beneficial to address the client's comprehensive developmental needs. Regular monitoring and reassessment will be important to track progress and adjust intervention strategies as needed to promote functional independence and developmental success."
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a comprehensive professional "Summary" section for {child_name} ({age}) based on assessment findings.
        
        Overall Performance Analysis: {overall_analysis}
        Key Strengths: {strengths}
        Areas of Need: {needs}
        
        Requirements:
        - Start with "{child_name} (chronological age: {age}) was assessed using multiple standardized pediatric assessment tools..."
        - Include specific delay percentages where applicable
        - Mention both areas of strength and areas requiring intervention
        - Discuss impact on functional performance and daily activities
        - Recommend multidisciplinary intervention approach
        - Include prognosis and benefit from services
        - Address family involvement and education needs
        - Mention regular monitoring and reassessment
        - Use professional clinical language typical of pediatric OT summaries
        - Write 6-8 sentences comprehensive summary
        
        Focus on evidence-based conclusions and specific recommendations based on actual assessment findings.
        """
        return prompt


def _generate_overall_performance_analysis(bayley_cognitive: dict, bayley_social: dict) -> str:
    """Generate overall performance analysis from assessment scores"""
    analysis_points = []
    
    # Analyze cognitive domain scores
    if bayley_cognitive.get("scaled_scores"):
        cog_scores = list(bayley_cognitive["scaled_scores"].values())
        avg_cog = sum(cog_scores) / len(cog_scores) if cog_scores else 0
        
        if avg_cog < 7:
            analysis_points.append("significant delays in cognitive-motor domains")
        elif avg_cog > 13:
            analysis_points.append("above-average cognitive-motor abilities")
        else:
            analysis_points.append("mixed cognitive-motor profile with areas of both strength and need")
    
    # Analyze social-emotional scores
    if bayley_social.get("scaled_scores"):
        social_scores = list(bayley_social["scaled_scores"].values())
        avg_social = sum(social_scores) / len(social_scores) if social_scores else 0
        
        if avg_social < 7:
            analysis_points.append("challenges in social-emotional and adaptive behavior development")
        elif avg_social > 13:
            analysis_points.append("strengths in social-emotional functioning")
        else:
            analysis_points.append("typical social-emotional development with some areas for growth")
    
    return "; ".join(analysis_points) if analysis_points else "comprehensive developmental evaluation across multiple domains"


def _identify_assessment_strengths(bayley_cognitive: dict, bayley_social: dict) -> str:
    """Identify strengths from assessment data"""
    strengths = []
    
    # Check for cognitive strengths
    if bayley_cognitive.get("scaled_scores"):
        for domain, score in bayley_cognitive["scaled_scores"].items():
            if score >= 10:
                strengths.append(f"{domain.lower()}")
    
    # Check for social-emotional strengths
    if bayley_social.get("scaled_scores"):
        for domain, score in bayley_social["scaled_scores"].items():
            if score >= 10:
                strengths.append(f"{domain.lower()}")
    
    return ", ".join(strengths[:3]) if strengths else "emerging developmental skills, social engagement, learning potential"


def _identify_assessment_needs(bayley_cognitive: dict, bayley_social: dict) -> str:
    """Identify areas of need from assessment data"""
    needs = []
    
    # Check for cognitive needs
    if bayley_cognitive.get("scaled_scores"):
        for domain, score in bayley_cognitive["scaled_scores"].items():
            if score < 8:
                needs.append(f"{domain.lower()}")
    
    # Check for social-emotional needs
    if bayley_social.get("scaled_scores"):
        for domain, score in bayley_social["scaled_scores"].items():
            if score < 8:
                needs.append(f"{domain.lower()}")
    
    return ", ".join(needs[:4]) if needs else "fine motor coordination, attention and focus, communication skills, behavioral regulation" 