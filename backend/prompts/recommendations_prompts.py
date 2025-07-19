async def get_recommendations_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate recommendations prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
    
    # Extract assessment analysis for context
    assessment_analysis = report_data.get("assessment_analysis", {})
    
    if json_format:
        prompt = f"""
        Generate specific OT recommendations for a pediatric report based on assessment findings.

        Patient: {child_name} (age: {age})
        Assessment Analysis: {assessment_analysis}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "bullet_points" for the recommendations list.
        - Generate minimum 2 specific recommendations for each assessment test based on the assessment findings.

        Instructions:
        STEP 1: FIRST, identify which assessments actually contain meaningful data:
        - Check each assessment in the assessment_analysis
        - Skip assessments with empty dictionaries {{}}, empty arrays [], or empty strings ""
        - Only proceed with assessments that have actual analysis content
        - Example: If bayley4 has {{"cognitive_analysis": {{}}, "motor_analysis": {{}}}} - this is EMPTY data, skip it
        - Example: If sp2 has {{"seeking_analysis": "Low sensory seeking...", "avoiding_analysis": "Low sensory avoiding..."}} - this has REAL data, use it

        STEP 2: For ONLY the assessments with real data, analyze to identify PRIMARY AREAS OF CONCERN:
        - Developmental delays or deficits
        - Motor skill challenges (fine motor, gross motor)
        - Sensory processing issues
        - Cognitive or learning difficulties
        - Speech/language concerns
        - Social-emotional challenges
        - Adaptive behavior needs
        - Any other significant findings

        STEP 3: Generate 2 targeted recommendations for EACH assessment that has real data. Each recommendation must:
        1. Clearly state which area of concern it addresses
        2. Specify the recommended intervention/therapy type
        3. Include appropriate frequency (e.g., 2x/week, daily, monthly)
        4. Be specific to the child's identified needs and developmental level
        5. Be actionable and measurable
        6. ONLY generate recommendations for assessments with actual data content

        STEP 4: Ensure each recommendation follows this format:
        "[Assessment Name]: [Intervention Type] [Frequency] to address [Specific Area of Concern] - [Brief rationale based on assessment findings]"

        CRITICAL DATA CHECK EXAMPLES:
        
        ❌ SKIP THESE (Empty Data):
        - "bayley4": {{"cognitive_analysis": {{}}, "motor_analysis": {{}}}} 
        - "chomps": {{"domain_scores": {{}}, "feeding_risks": []}}
        - "pedieat": {{"physiology_analysis": "", "safety_concerns": []}}

        ✅ USE THESE (Real Data):
        - "sp2": {{"seeking_analysis": "Low sensory seeking - limited interest...", "avoiding_analysis": "Low sensory avoiding..."}}
        - "bayley4": {{"cognitive_analysis": {{"score": 85, "interpretation": "Below average"}}, "motor_analysis": {{"delays": "Significant delays observed"}}}}

        Multiple Example Formats for assessments WITH data:

        Example 1 - SP2 with Real Data:
        "SP2: Sensory Integration Therapy 1x/week to address low sensory seeking - Child shows limited interest in sensory exploration and may appear withdrawn from sensory experiences"
        "SP2: Environmental modifications daily to address sensory processing - Implement sensory-rich activities to encourage exploration while respecting low sensitivity patterns"

        JSON response format:
        {{
            "clinical_recommendations": {{
                "type": "bullet_points",
                "content": [
                    "Assessment with data: First recommendation targeting specific area of concern",
                    "Assessment with data: Second recommendation targeting specific area of concern"
                ]
            }}
        }}

        CRITICAL: 
        1. DO NOT generate recommendations for assessments with empty data structures
        2. ONLY include assessments that have meaningful analysis content
        3. If no assessments have real data, return empty content array
        4. Each recommendation must reference specific findings from the actual data present
        """
        return prompt
    
    else:
        prompt = f"""
        Generate minimum 2 specific therapy recommendations for each assessment test that contains actual data.
        
        Patient: {child_name} (age: {age})
        Assessment findings: {assessment_analysis}
        
        Instructions:
        STEP 1: FIRST, identify which assessments actually contain meaningful data:
        - Examine each assessment in the assessment_analysis carefully
        - Skip assessments with empty dictionaries {{}}, empty arrays [], or empty strings ""
        - Only proceed with assessments that have actual analysis content with real findings
        - Example: If bayley4 shows {{"cognitive_analysis": {{}}, "motor_analysis": {{}}}} - this is EMPTY, skip it
        - Example: If sp2 shows {{"seeking_analysis": "Low sensory seeking...", "avoiding_analysis": "Low sensory avoiding..."}} - this has REAL data, use it

        STEP 2: For ONLY assessments with real data, identify PRIMARY AREAS OF CONCERN:
        - Developmental delays or deficits in any domain
        - Motor skill challenges (fine motor, gross motor, visual motor)
        - Sensory processing difficulties
        - Cognitive or learning challenges
        - Speech/language concerns
        - Social-emotional difficulties
        - Adaptive behavior needs
        - Self-care skill deficits
        - Any other significant findings or red flags

        STEP 3: Generate 2 targeted recommendations for EACH assessment that has meaningful data. Each recommendation must:
        1. Clearly identify which area of concern it targets
        2. Specify the recommended intervention/therapy type
        3. Include appropriate frequency and duration
        4. Be tailored to the child's specific needs and developmental level
        5. Include a brief rationale based on assessment findings
        6. ONLY generate recommendations for assessments with actual data content

        STEP 4: Format each recommendation as:
        "[Assessment Name]: [Intervention Type] [Frequency] to address [Specific Area of Concern] - [Brief rationale from assessment]"

        CRITICAL DATA CHECK EXAMPLES:

        ❌ SKIP THESE (Empty/No Real Data):
        - bayley4 with empty analysis dictionaries
        - chomps with empty domain_scores and empty feeding_risks arrays
        - pedieat with empty string analyses and empty concern arrays

        ✅ GENERATE RECOMMENDATIONS FOR THESE (Real Data Present):
        - sp2 with actual seeking_analysis, avoiding_analysis text content
        - Any assessment with populated scores, interpretations, or analysis content

        Example Recommendations for SP2 (if it has real data):
        - "SP2: Sensory Integration Therapy 1x/week to address low sensory seeking - Assessment indicates limited interest in sensory exploration and withdrawal from sensory experiences"
        - "SP2: Daily sensory-rich activities to address sensory registration - Implement structured sensory play to support consistent sensory input awareness"

        Use bullet point format. 

        CRITICAL RULES:
        1. DO NOT generate recommendations for assessments with empty data structures
        2. ONLY create recommendations for assessments that contain meaningful analysis content
        3. If an assessment has empty dictionaries, arrays, or strings - SKIP IT COMPLETELY
        4. Each recommendation must cite specific findings from actual data present
        5. If no assessments have real data, state "No meaningful assessment data available for recommendations"
        """
        return prompt 