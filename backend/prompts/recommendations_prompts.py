async def get_recommendations_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate recommendations prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
    
    # Extract assessment analysis for context
    assessment_analysis = report_data.get("assessment_analysis", {})
    
    if json_format:
        prompt = f"""
        Generate comprehensive OT recommendations for a pediatric report based on assessment findings.

        Patient: {child_name} (age: {age})
        Assessment Analysis: {assessment_analysis}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "bullet_points" for the recommendations list.
        - Generate 6-10 specific, actionable recommendations.

        Content Requirements:
        Create specific, actionable recommendations that address:
        - Direct occupational therapy services (frequency and duration)
        - Physical therapy services if indicated
        - Speech therapy services if needed
        - Early intervention services
        - Home program activities for families
        - Environmental modifications
        - Caregiver training and education
        - Equipment or adaptive tools
        - School/daycare accommodations
        - Follow-up assessments and monitoring

        Format each recommendation as a clear, actionable statement that families and providers can understand and implement.

        JSON response format:
        {{
            "clinical_recommendations": {{
                "type": "bullet_points",
                "content": [
                    "Occupational therapy services 2-3 times per week for 45-60 minute sessions to address fine motor delays and sensory processing needs",
                    "Speech therapy evaluation and services to support communication development and oral motor skills",
                    "Physical therapy consultation for gross motor development and mobility skills",
                    "Early intervention services coordination to ensure comprehensive developmental support",
                    "Home program activities focusing on fine motor skills, bilateral coordination, and pre-writing development",
                    "Environmental modifications including sensory tools and adaptive equipment as needed",
                    "Caregiver education on developmental activities and strategies for daily routines"
                ]
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Generate 6-10 professional therapy recommendations for a pediatric client based on comprehensive assessment findings.
        
        Patient: {child_name} (age: {age})
        Assessment findings: {assessment_analysis}
        
        Include:
        - Occupational Therapy (with specific frequency)
        - Physical Therapy (if indicated)
        - Speech Therapy (if needed)
        - Early intervention services
        - Home program recommendations
        - Environmental modifications
        - Caregiver education
        - Equipment needs
        - Follow-up assessments
        
        Use bullet point format, be specific and professional.
        """
        return prompt 