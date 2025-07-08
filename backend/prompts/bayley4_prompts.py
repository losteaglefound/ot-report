async def get_bayley4_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate Bayley-4 assessment interpretation prompt for pediatric OT reports."""
    """Generate Bayley-4 assessment interpretation prompt for pediatric OT reports."""

    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    chronological_age = patient_info.get("chronological_age", {})

    bayley_data = report_data.get("bayley", {})

    cognitive_data = bayley_data.get("cognitive", [])
    receptive_comm_data = bayley_data.get("receptive_communication", [])
    expressive_comm_data = bayley_data.get("expressive_communication", [])
    fine_motor_data = bayley_data.get("fine_motor", [])
    gross_motor_data = bayley_data.get("gross_motor", [])

    domain_contexts = {
        "cognitive": {
            "description": "Assesses attention, memory, sensory-motor development, exploration and manipulation, object relatedness, concept formation, and problem-solving abilities.",
            "infant_tasks": "Visual tracking, habituation to stimuli, object permanence, cause-effect understanding, and early symbolic play.",
            "toddler_tasks": "Shape sorting, puzzle completion, block stacking, spatial memory, and basic concept categorization."
        },
        "receptive_communication": {
            "description": "Evaluates comprehension of verbal language and nonverbal cues, including gestures and contextual communication.",
            "infant_tasks": "Responding to name, recognizing voices, following gestures, and reacting to familiar people or words.",
            "toddler_tasks": "Following one-step commands, identifying objects/body parts, and understanding common language constructs."
        },
        "expressive_communication": {
            "description": "Assesses verbal and non-verbal expressive skills such as sounds, gestures, word production, and early sentence use.",
            "infant_tasks": "Cooing, babbling, vocal imitation, and use of gestures like pointing or waving.",
            "toddler_tasks": "Using words, combining words, forming short phrases or sentences, and expressing wants/needs."
        },
        "fine_motor": {
            "description": "Evaluates manual dexterity, visual-motor coordination, and small muscle precision in the hands and fingers.",
            "infant_tasks": "Grasping objects, transferring items, visual tracking, and early object manipulation.",
            "toddler_tasks": "Stacking, drawing, threading, pincer grasp development, and pre-writing skills."
        },
        "gross_motor": {
            "description": "Assesses large muscle development, postural control, balance, and body coordination in space.",
            "infant_tasks": "Head control, rolling, sitting, crawling, and early attempts at standing or walking.",
            "toddler_tasks": "Running, jumping, climbing, throwing, stair use, and coordinated movement sequences."
        }
    }

    if json_format:
        prompt = f"""
        Write a comprehensive Bayley-4 clinical interpretation for a pediatric OT report using the actual data below.

        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Unknown')}

        ACTUAL BAYLEY-4 VALID ANSWERS:
        Cognitive Domain: {cognitive_data}
        Receptive Communication Domain: {receptive_comm_data}
        Expressive Communication Domain: {expressive_comm_data}
        Fine Motor Domain: {fine_motor_data}
        Gross Motor Domain: {gross_motor_data}

        DOMAIN CONTEXTS:
        {domain_contexts}

        CLINICAL INTERPRETATION INSTRUCTIONS:

        1. **USE "item_description" (NOT "item_no")** when describing tasks.
        - ✅ Correct: "On the Eyes Follow Moving Person task..."
        - ❌ Incorrect: "On Item 1..."

        2. **EXPLAIN SCORE MEANINGS** using the "scoring_criteria" for each task.
        - Avoid just stating the number — interpret it clinically.
        - Use quoted criteria to explain what the score reflects developmentally.

        3. **ENHANCED ITEM ANALYSIS**:
        - Describe specific grasp patterns (digital pronate, pincer, etc.)
        - Quantify performance (number of blocks stacked, pegs placed, time taken)
        - Note bilateral coordination challenges explicitly
        - Identify visual-motor integration capabilities
        - Specify precision and control limitations
        - Highlight multi-step task difficulties

        4. **GROUP TASKS BY PERFORMANCE LEVEL**:
        - Score 2 → Well-established skills: Describe proficiency and functional implications
        - Score 1 → Emerging skills: Quantify partial success and developmental gaps
        - Score 0 → Skills not yet developed: Explain clinical significance of absence

        5. **DEVELOPMENTAL PATTERN ANALYSIS**:
        - Compare performance to age expectations
        - Identify domain-specific patterns (e.g., "emerging foundational skills but significant limitations in...")
        - Note discrepancies between subskills

        6. **FUNCTIONAL IMPLICATIONS**:
        - Connect specific deficits to daily activities (self-care, play, pre-academic skills)
        - Recommend intervention focus areas
        - Describe impact on independence

        RESPONSE FORMAT (DO NOT CHANGE):

        {{
            "cognitive_domain": {{
                "header": {{"type": "header", "content": "Cognitive (CG)"}},
                "domain_summary": {{"type": "paragraph", "content": "{domain_contexts['cognitive']['description']}"}},
                "domain_details": {{"type": "bullet_points", "content": [
                    "Infant tasks include: {domain_contexts['cognitive']['infant_tasks']}.",
                    "Toddler tasks include: {domain_contexts['cognitive']['toddler_tasks']}."
                ]}},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL COGNITIVE DATA. Use item_description, quote scoring_criteria, and describe developmental significance and functional implications.**"
                }}
            }},
            "receptive_communication": {{
                "header": {{"type": "header", "content": "Receptive Communication (RC)"}},
                "domain_summary": {{"type": "paragraph", "content": "{domain_contexts['receptive_communication']['description']}"}},
                "domain_details": {{"type": "bullet_points", "content": [
                    "Infant tasks include: {domain_contexts['receptive_communication']['infant_tasks']}.",
                    "Toddler tasks include: {domain_contexts['receptive_communication']['toddler_tasks']}."
                ]}},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL RECEPTIVE COMMUNICATION DATA. Use item_description, quote scoring_criteria, and describe developmental significance and functional implications.**"
                }}
            }},
            "expressive_communication": {{
                "header": {{"type": "header", "content": "Expressive Communication (EC)"}},
                "domain_summary": {{"type": "paragraph", "content": "{domain_contexts['expressive_communication']['description']}"}},
                "domain_details": {{"type": "bullet_points", "content": [
                    "Infant tasks include: {domain_contexts['expressive_communication']['infant_tasks']}.",
                    "Toddler tasks include: {domain_contexts['expressive_communication']['toddler_tasks']}."
                ]}},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL EXPRESSIVE COMMUNICATION DATA. Use item_description, quote scoring_criteria, and describe developmental significance and functional implications.**"
                }}
            }},
            "fine_motor": {{
                "header": {{"type": "header", "content": "Fine Motor (FM)"}},
                "domain_summary": {{"type": "paragraph", "content": "{domain_contexts['fine_motor']['description']}"}},
                "domain_details": {{"type": "bullet_points", "content": [
                    "Infant tasks include: {domain_contexts['fine_motor']['infant_tasks']}.",
                    "Toddler tasks include: {domain_contexts['fine_motor']['toddler_tasks']}."
                ]}},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL FINE MOTOR DATA. Use item_description, quote scoring_criteria, and describe developmental significance and functional implications.**"
                }}
            }},
            "gross_motor": {{
                "header": {{"type": "header", "content": "Gross Motor (GM)"}},
                "domain_summary": {{"type": "paragraph", "content": "{domain_contexts['gross_motor']['description']}"}},
                "domain_details": {{"type": "bullet_points", "content": [
                    "Infant tasks include: {domain_contexts['gross_motor']['infant_tasks']}.",
                    "Toddler tasks include: {domain_contexts['gross_motor']['toddler_tasks']}."
                ]}},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL GROSS MOTOR DATA. Use item_description, quote scoring_criteria, and describe developmental significance and functional implications.**"
                }}
            }}
        }}

        MANDATORY REQUIREMENTS:
        - Use item_description only (never item_no)
        - Quote exact scoring_criteria for interpretation
        - Include specific grasp patterns and quantitative performance data
        - Describe bilateral coordination and motor planning capabilities
        - Analyze visual-motor integration explicitly
        - Use clinical terminology: "digital pronate grasp", "bilateral coordination", "visual-motor integration"
        - Maintain professional clinical tone throughout
        """
        return prompt
    
    else:
        prompt = f"""
        Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report using the ACTUAL VALID ANSWERS provided below.
        
        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Not available')}
        
        ACTUAL BAYLEY-4 VALID ANSWERS DATA:
        Cognitive Domain: {cognitive_data}
        Receptive Communication Domain: {receptive_comm_data}
        Expressive Communication Domain: {expressive_comm_data}
        Fine Motor Domain: {fine_motor_data}
        Gross Motor Domain: {gross_motor_data}
        
        DOMAIN CONTEXTS FOR DETAILED UNDERSTANDING:
        {domain_contexts}
        
        CRITICAL INSTRUCTIONS FOR ITEM ANALYSIS AND CLINICAL INTERPRETATION:
        
        1. **USE ITEM_DESCRIPTION, NOT ITEM_NO**: When referencing tasks, ALWAYS use the "item_description" field, not the "item_no".
        
        2. **ELABORATE ON SCORE MEANINGS**: For each item mentioned, explain what the specific score means clinically using the scoring_criteria provided.
        
        3. **DETAILED CLINICAL INTERPRETATION**: For each item, provide:
           - What the task measures (use item_description)
           - What score was achieved (valid_answer)
           - What that score means according to scoring_criteria
           - Clinical interpretation of developmental significance
           - Functional implications
        
        4. **PERFORMANCE PATTERN ANALYSIS**: Group items by performance level and explain what these patterns indicate about overall development.
        
        5. **FUNCTIONAL IMPLICATIONS**: Connect specific item performance to real-world functional abilities and intervention needs.
        
        Format Requirements:
        - Start each domain with the header format: "Domain Name (Abbreviation)"
        - Use item_description when referencing tasks
        - Quote scoring criteria when explaining what scores mean
        - Provide clinical interpretation of developmental significance
        - Connect findings to functional implications
        - Use professional, clinical language
        
        EXAMPLE OF DETAILED CLINICAL ANALYSIS:
        "During fine motor assessment, {child_name} demonstrated variable performance across developmental tasks. On the Eyes Follow Moving Person task, he achieved a score of 2, indicating his eyes can track a person through midline to both left and right sides according to the scoring criteria, suggesting intact visual-motor coordination and oculomotor control. However, on the Brings Hand to Mouth task, he scored 1, meaning he attempts to place his hand in his mouth but does not have consistent success. This suggests emerging self-directed movement patterns but indicates delays in motor planning and execution for self-care activities. The pattern of scores suggests..."
        
        Write detailed clinical narrative covering all domains with specific item analysis using item_description, score interpretation using scoring_criteria, and functional implications using the actual valid answers data provided.
        """
        return prompt 