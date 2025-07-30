import json

async def get_bayley4_social_adaptive_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate Bayley-4 assessment interpretation prompt for Social-Emotional and Adaptive Behavior domains."""

    with open("outputs/test_baley_social_and_adaptive_response.json", 'w') as f:
        f.write(json.dumps(report_data, indent=4))
    print("\n Bayley4 social and adaptive prompt: outputs/test_baley_social_and_adaptive_response.json\n")

    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    chronological_age = patient_info.get("chronological_age", {}).get("formatted", "Unknown")

    bayley_data = report_data.get("bayley", {})
    social_and_adaptive = bayley_data.get("social_and_adaptive", {})
    social_emotional_data = social_and_adaptive.get("social_emotional", {}).get("observations", [])
    adaptive_behavior_data = social_and_adaptive.get("adaptive_behavior", {})

    adaptive_receptive_data = adaptive_behavior_data.get('subdomains', {}).get("receptive", {}).get('observations', [])
    adaptive_expressive_data = adaptive_behavior_data.get('subdomains', {}).get("expressive", {}).get('observations', [])
    adaptive_personal_data = adaptive_behavior_data.get('subdomains', {}).get("personal", {}).get('observations', [])
    adaptive_play_data = adaptive_behavior_data.get('subdomains', {}).get("play_and_leisure", {}).get('observations', [])

    social_emotional_data = [f"- {x['contextual_observation']}" for x in social_emotional_data]
    adaptive_receptive_data = [f"- {x['contextual_observation']}" for x in adaptive_receptive_data]
    adaptive_expressive_data = [f"- {x['contextual_observation']}" for x in adaptive_expressive_data]
    adaptive_personal_data = [f"- {x['contextual_observation']}" for x in adaptive_personal_data]
    adaptive_play_data = [f"- {x['contextual_observation']}" for x in adaptive_play_data]
    

    social_emotional_context = (
        "The Social-Emotional Scale asks caregivers to assess how their child interacts with others, expresses emotions,"
        " and responds to sensory input such as sounds, touch, and visual stimuli. This scale helps identify age-appropriate"
        " social-emotional milestones related to attachment, self-regulation, and engagement in early relationships."
    )

    adaptive_behavior_context = (
        "The Adaptive Behavior Scale asks caregivers to assess their child's ability to adapt to various demands of normal"
        " daily living and become more independent."
    )

    if json_format:
        prompt = f"""
        Write a comprehensive Bayley-4 interpretation for Social-Emotional and Adaptive Behavior domains using the data below.

        Patient: {child_name}
        Chronological Age: {chronological_age}


        ACTUAL BAYLEY-4 VALID ANSWERS INTERPRETATIONS:
        Social-Emotional Domain: 
        {social_emotional_data}
        
        Adaptive Behavior Domain: 
            Receptive behaviour
                {adaptive_receptive_data}

            Expressive behaviour
                {adaptive_expressive_data}

            Personal
                {adaptive_personal_data}

            Play and Liesure
                {adaptive_play_data}

        CLINICAL INTERPRETATION INSTRUCTIONS:

        1. Use "observation_description" (not "observation_no") when describing tasks.
        2. Interpret each score based on its associated "scoring_criteria".
        3. Provide clinical meaning, behavioral significance, and functional implications.
        4. Group tasks by performance level:
           - Score 2: Skills consistently demonstrated
           - Score 1: Emerging or inconsistently demonstrated skills
           - Score 0: Skills not yet observed
        5. Identify developmental patterns and compare to age expectations.
        6. Link observed behaviors to home and community functioning.
        7. In adaptive behaviour response create patient_assessment paragraph for each subdomain
            - Receptive Communication
            - Expressive Communication
            - Personal 
            - Interpersonal Relationships
            - Play and Leisure

        RESPONSE FORMAT (DO NOT CHANGE):

        {{
            "social_emotional": {{
                "header": {{"type": "header", "content": "Social-Emotional (SE)"}},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "{social_emotional_context}"
                }},
                "domain_details": {{
                    "type": "paragraph",
                    "content": "This domain includes social referencing, affective expression, empathy, and emotional regulation skills. Items assess responses to familiar caregivers, attention to faces, and emotional reciprocity."
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL SOCIAL-EMOTIONAL DATA. Use item_description, quote scoring_criteria, and describe functional and emotional significance.**"
                }}
            }},
            "adaptive_behavior": {{
                "header": {{"type": "header", "content": "Adaptive Behavior (AB)"}},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "{adaptive_behavior_context}"
                }},
                "domain_details": {{
                    "type": "paragraph",
                    "content": "This domain includes skills like self-care routines, personal responsibility, communication, following safety rules, and basic daily living abilities across environments."
                }},
                "patient_assessment_receptive_communication": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL ADAPTIVE BEHAVIOR DATA FOR RECEPTIVE COMMUNICATION SUBDOMAIN. Use item_description, quote scoring_criteria, and explain functional independence, communication patterns, and adaptive developmental levels.**"
                }},
                "patient_assessment_expressive_communication": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL ADAPTIVE BEHAVIOR DATA FOR EXPRESSIVE COMMUNICATION SUBDOMAIN. Use item_description, quote scoring_criteria, and explain functional independence, communication patterns, and adaptive developmental levels.**"
                }},
                "patient_assessment_personal": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL ADAPTIVE BEHAVIOR DATA FOR PERSONAL SUBDOMAIN. Use item_description, quote scoring_criteria, and explain functional independence, communication patterns, and adaptive developmental levels.**"
                }},
                "patient_assessment_interpersonal_relation": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL ADAPTIVE BEHAVIOR DATA FOR INTERPERSONAL RELATIONSHIPS SUBDOMAIN. Use item_description, quote scoring_criteria, and explain functional independence, communication patterns, and adaptive developmental levels.**"
                }},
                "patient_assessment_play_and_leisure": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL ADAPTIVE BEHAVIOR DATA FOR PLAY AND LEISURE SUBDOMAIN. Use item_description, quote scoring_criteria, and explain functional independence, communication patterns, and adaptive developmental levels.**"
                }}
            }}
        }}

        MANDATORY REQUIREMENTS:
        - Always use item_description when describing performance
        - Quote exact scoring_criteria for interpretation
        - No bullet points — narrative format only
        - Highlight specific functional challenges or strengths in social and adaptive settings
        - Maintain clinical tone appropriate for pediatric OT documentation
        """
        return prompt.strip()

    prompt = f"""
    Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report using the ACTUAL VALID ANSWERS provided below.

    Patient: {child_name}
    Chronological Age: {chronological_age}

    ACTUAL BAYLEY-4 VALID ANSWERS INTERPRETATIONS:
    Social-Emotional Domain: 
    {social_emotional_data}
    
    Adaptive Behavior Domain: 
        Receptive behaviour
            {adaptive_receptive_data}

        Expressive behaviour
            {adaptive_expressive_data}

        Personal
            {adaptive_personal_data}

        Play and Liesure
            {adaptive_play_data}

    INSTRUCTIONS FOR CLINICAL INTERPRETATION:

    - Use "item_description" when referencing items.
    - Interpret score meanings using the "scoring_criteria" provided.
    - Group performance into well-developed, emerging, and absent skill levels.
    - Describe what the child does well, what is developing, and what is not yet present.
    - Connect observations to real-life behaviors and daily functioning.
    - Avoid bullet points; use narrative paragraph format.
    - Maintain a professional and objective clinical tone throughout.

    DOMAIN CONTEXTS:

    Social-Emotional (SE): {social_emotional_context}
    Adaptive Behavior (AB): {adaptive_behavior_context}

    EXAMPLE:

    "In the Social-Emotional domain, {child_name} demonstrated several foundational skills. On the Looks at Caregiver’s Face task, a score of 2 was achieved, indicating consistent eye contact and social engagement, which is developmentally appropriate for the child's age. In contrast, the Turns Toward Name task received a score of 1, suggesting emerging awareness of auditory social cues. These patterns indicate growing social responsiveness but possible delays in joint attention behaviors. The child’s performance suggests appropriate attachment development but would benefit from targeted social engagement strategies at home."

    Now write a detailed interpretation for each domain using the actual data provided.
    """
    return prompt.strip()
