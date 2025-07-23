async def get_bayley4_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate Bayley-4 assessment interpretation prompt for pediatric OT reports."""
    """Generate Bayley-4 assessment interpretation prompt for pediatric OT reports."""

    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    chronological_age = patient_info.get("chronological_age", {})

    bayley_data = report_data.get("bayley", {})
    cogintive_and_motor = bayley_data.get("cognitive_and_motor", {})

    cognitive_data = cogintive_and_motor.get("cognitive", [])
    receptive_comm_data = cogintive_and_motor.get("receptive_communication", [])
    expressive_comm_data = cogintive_and_motor.get("expressive_communication", [])
    fine_motor_data = cogintive_and_motor.get("fine_motor", [])
    gross_motor_data = cogintive_and_motor.get("gross_motor", [])

    print("$" * 30)
    print(cognitive_data)
    print("$" * 30)

    cognitive_data = "\n".join([f"- {x['item_description']}: {x['contextual_observation']}" for x in cognitive_data])
    receptive_comm_data = "\n".join([f"- {x['item_description']}: {x['contextual_observation']}" for x in receptive_comm_data])
    expressive_comm_data = "\n".join([f"- {x['item_description']}: {x['contextual_observation']}" for x in expressive_comm_data])
    fine_motor_data = "\n".join([f"- {x['item_description']}: {x['contextual_observation']}" for x in fine_motor_data])
    gross_motor_data = "\n".join([f"- {x['item_description']}: {x['contextual_observation']}" for x in gross_motor_data])

    domain_contexts = {
        "cognitive": {
            "description": "Assesses attention, memory, sensory-motor development, exploration and manipulation, object relatedness, concept formation, and problem-solving abilities.",
            "infant_tasks": "Visual tracking, habituation to stimuli, object permanence, cause-effect understanding, and early symbolic play.",
            "toddler_tasks": "Shape sorting, puzzle completion, block stacking, spatial memory, and basic concept categorization.",
            "example_interpretation": """
                In the cognitive domain, Child was able to complete structured problem-solving tasks with
                emerging accuracy and sustained attention. He completed a shape-sorting board with three
                shapes (square, circle, triangle) in 60 seconds and placed eight inset shapes accurately within 90
                seconds. He successfully placed nine blocks into a cup and inserted all six pegs onto a pegboard
                within 35 seconds. He also assembled two-piece puzzles, including a ball puzzle and an ice
                cream puzzle, demonstrating basic visual-spatial reasoning. While he imitates scribbling and
                combines functional objects appropriately (e.g., spoon in bowl), he is not yet spontaneously
                naming five or more objects or using symbolic play with substitute objects. Relational play
                remains limited to the use of one object with a caregiver, and attention to books or storytelling is
                brief. These observations are consistent with a Bayley-4 Cognitive scaled score of 2, placing him
                in the extremely low range with an age equivalent of 18 months.
            """
        },
        "receptive_communication": {
            "description": "Evaluates comprehension of verbal language and nonverbal cues, including gestures and contextual communication.",
            "infant_tasks": "Responding to name, recognizing voices, following gestures, and reacting to familiar people or words.",
            "toddler_tasks": "Following one-step commands, identifying objects/body parts, and understanding common language constructs.",
            "example_interpretation": """
                In the receptive language domain, Child consistently reacts to sounds and voice and
                demonstrates appropriate responses to simple verbal requests. However, he inconsistently
                responds when his name is called. He maintains attention for up to 30 consecutive seconds,
                indicating emerging auditory processing skills. These findings are aligned with a scaled score of
                1 and an age equivalent of 10 months, which is in the extremely low range for receptive
                communication.
            """
        },
        "expressive_communication": {
            "description": "Assesses verbal and non-verbal expressive skills such as sounds, gestures, word production, and early sentence use.",
            "infant_tasks": "Cooing, babbling, vocal imitation, and use of gestures like pointing or waving.",
            "toddler_tasks": "Using words, combining words, forming short phrases or sentences, and expressing wants/needs.",
            "example_interpretation": """
                In the expressive language domain, Child initiates play and demonstrates early social reciprocity
                by directing attention to objects, vocalizing moods, and laughing during social interactions. He
                occasionally produces single words or word approximations and uses gestures to communicate.
                However, expressive vocabulary remains limited, and consistent use of consonant-vowel
                combinations or spontaneous verbal output is infrequent. His Bayley-4 expressive
                communication scaled score is 1, with an age equivalent of 10 months, placing him in the
                extremely low range.
            """
        },
        "fine_motor": {
            "description": "Evaluates manual dexterity, visual-motor coordination, and small muscle precision in the hands and fingers.",
            "infant_tasks": "Grasping objects, transferring items, visual tracking, and early object manipulation.",
            "toddler_tasks": "Stacking, drawing, threading, pincer grasp development, and pre-writing skills.",
            "example_interpretation": r"""
                In the fine motor domain, Child presents with emerging foundational skills, but continues to
                demonstrate significant delays in bilateral coordination, grasp development, and motor planning.
                He is able to grasp a block using partial thumb opposition and has developed a refined pincer
                grasp, allowing him to manipulate small items and isolate his index finger to poke with intention.
                He demonstrates spontaneous scribbling using an immature grasp pattern—alternating between a
                brush grasp and a gross cylindrical grasp—indicating the early stages of tool use and pre-writing
                development. Child is able to turn pages in a board book and shows a clear hand dominance,
                favoring his right hand during most fine motor tasks.

                However, several age-appropriate childtones remain unmet. He is unable to stack blocks, string
                beads, or complete tasks that require refined bimanual coordination, such as holding and
                threading or using stabilizing and manipulating hands in tandem. These limitations suggest
                underdeveloped bilateral integration and insufficient distal control. Additionally, although he is
                willing to engage in table-top fine motor tasks, he frequently requires prompting to maintain
                engagement and complete tasks that demand sustained attention or multiple steps. These clinical
                observations are consistent with his Bayley-4 Fine Motor scaled score of 4, which corresponds to
                an age equivalent of 17 months and falls within the extremely low to low range of functioning
                with a 41% delay.
            """
        },
        "gross_motor": {
            "description": "Assesses large muscle development, postural control, balance, and body coordination in space.",
            "infant_tasks": "Head control, rolling, sitting, crawling, and early attempts at standing or walking.",
            "toddler_tasks": "Running, jumping, climbing, throwing, stair use, and coordinated movement sequences.",
            "example_interpretation": """
                In the gross motor domain, Child is ambulatory and able to walk independently. He demonstrates
                functional mobility by squatting without support, raising himself to stand, and walking up and
                down stairs with assistance, using both feet per step. He can attempt to throw a ball overhead and
                can jump with both feet together. He demonstrates emerging balance with support on both right
                and left foot. His gross motor scaled score of 5, with an age equivalent of 19 months, places him
                within the low average to mildly delayed range compared to same-age peers
            """
        }
    }

    if json_format:
        prompt = f"""
        Write a comprehensive Bayley-4 clinical interpretation for a pediatric OT report using the actual data below.

        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Unknown')}

        ACTUAL BAYLEY-4 VALID ANSWERS WITH ITEM DESCRIPTION:
        COGNITIVE DOMAIN: 
        {cognitive_data}
        
        RECEPTIVE COMMUNICATION DOMAIN: 
        {receptive_comm_data}
        
        EXPRESSIVE COMMUNICATION DOMAIN: 
        {expressive_comm_data}
        
        FINE MOTOR DOMAIN: 
        {fine_motor_data}
        
        GROSS MOTOR DOMAIN: 
        {gross_motor_data}

        DOMAIN CONTEXTS AND SCORING GUIDELINES:
        {domain_contexts}

        SCORE INTERPRETATION GUIDELINES:
        - Score 2: Well-established skills - Consistent, reliable performance meeting all criteria
        - Score 1: Emerging skills - Inconsistent or partial demonstration of the skill
        - Score 0: Skills not yet developed - No demonstration or unable to perform

        PERFORMANCE CLASSIFICATIONS:
        - Extremely Low: Scaled scores 1-3 (≤2nd percentile)
        - Borderline: Scaled scores 4-5 (3rd-8th percentile)
        - Low Average: Scaled scores 6-7 (9th-24th percentile)
        - Average: Scaled scores 8-12 (25th-74th percentile)
        - High Average: Scaled scores 13-14 (75th-90th percentile)
        - Superior: Scaled scores 15-19 (≥91st percentile)

        CLINICAL INTERPRETATION INSTRUCTIONS:

        **Core Principles for Interpretation:**
        - **Focus**: Adopt a diagnostic and assessment-based approach. Analyze behaviors such as attention span, task persistence, and response to name. Link these observations directly to standardized scores and developmental expectations.
        - **Tone**: Maintain a technical, specific, and objective tone grounded in psychometric evaluation.
        - **Integrate Quantitative Data**: Reference scaled scores and age equivalents to provide a clear, quantitative picture of the child's performance. Use formal diagnostic terms (e.g., "extremely low range," "borderline," "average") to classify scores.
        - **Deficit-Oriented Analysis**: Primarily describe developmental deficits and current limitations to inform diagnosis and treatment planning. While strengths can be noted, the emphasis is on identifying areas of need.

        1. **USE "item_description" (NOT "item_no")** when describing tasks.
        - ✅ Correct: "On the Eyes Follow Moving Person task..."
        - ❌ Incorrect: "On Item 1..."

        2. **EXPLAIN SCORE WITH MEANINGS** from contextual_observation of each domain assessment
        - Avoid just stating the number — interpret it clinically.

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
        - Compare performance to age expectations using provided scaled scores and age equivalents.
        - Identify domain-specific patterns (e.g., "emerging foundational skills but significant limitations in...")
        - Note discrepancies between subskills

        6. **FUNCTIONAL IMPLICATIONS**:
        - Connect specific deficits to daily activities (self-care, play, pre-academic skills)
        - Recommend intervention focus areas based on identified limitations.
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
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL COGNITIVE DATA. Use item_description and contextal observation, and describe developmental significance and functional implications.**"
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
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL RECEPTIVE COMMUNICATION DATA. Use item_description and contextal observation, and describe developmental significance and functional implications.**"
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
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL EXPRESSIVE COMMUNICATION DATA. Use item_description and contextal observation, and describe developmental significance and functional implications.**"
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
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL FINE MOTOR DATA. Use item_description and contextal observation, and describe developmental significance and functional implications.**"
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
                    "content": "**REPLACE WITH CLINICAL INTERPRETATION USING ACTUAL GROSS MOTOR DATA. Use item_description and contextal observation, and describe developmental significance and functional implications.**"
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
        - Integrate scaled scores and age equivalents, using diagnostic language like "extremely low range" or "borderline" to describe performance.
        - Focus primarily on deficits and current limitations.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report using the ACTUAL VALID ANSWERS provided below.
        
        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Not available')}
        
        ACTUAL BAYLEY-4 VALID ANSWERS DATA:
        Cognitive Domain: 
        {cognitive_data}
        
        Receptive Communication Domain: 
        {receptive_comm_data}
        
        Expressive Communication Domain: 
        {expressive_comm_data}
        
        Fine Motor Domain: 
        {fine_motor_data}
        
        Gross Motor Domain: 
        {gross_motor_data}
        
        DOMAIN CONTEXTS FOR DETAILED UNDERSTANDING:
        {domain_contexts}
        
        CRITICAL INSTRUCTIONS FOR ITEM ANALYSIS AND CLINICAL INTERPRETATION:

        **Core Principles for Interpretation:**
        - **Focus**: Adopt a diagnostic and assessment-based approach. Analyze behaviors such as attention span, task persistence, and response to name. Link these observations directly to standardized scores and developmental expectations.
        - **Tone**: Maintain a technical, specific, and objective tone grounded in psychometric evaluation.
        - **Integrate Quantitative Data**: Reference scaled scores and age equivalents to provide a clear, quantitative picture of the child's performance. Use formal diagnostic terms (e.g., "extremely low range," "borderline," "average") to classify scores.
        - **Deficit-Oriented Analysis**: Primarily describe developmental deficits and current limitations to inform diagnosis and treatment planning. While strengths can be noted, the emphasis is on identifying areas of need.
        
        1. **USE ITEM_DESCRIPTION, NOT ITEM_NO**: When referencing tasks, ALWAYS use the "item_description" field, not the "item_no".
        
        2. **ELABORATE ON SCORE MEANINGS**: For each item mentioned, explain what the specific score means clinically using the scoring_criteria provided.
        
        3. **DETAILED CLINICAL INTERPRETATION**: For each item, provide:
           - What the task measures (use item_description)
           - What score was achieved (valid_answer)
           - What that score means according to scoring_criteria
           - Clinical interpretation of developmental significance, linking to scaled scores and age equivalents.
           - Functional implications focusing on deficits.
        
        4. **PERFORMANCE PATTERN ANALYSIS**: Group items by performance level and explain what these patterns indicate about overall development. Analyze performance in relation to age expectations using quantitative data.
        
        5. **FUNCTIONAL IMPLICATIONS**: Connect specific item performance to real-world functional abilities and intervention needs, focusing on limitations.

        6. **REFERENCE**: Take refrence from the "example_interpretations" from each domain context for generation of context for each domain. The generated context should align the with it language, score and example.
        
        Format Requirements:
        - Start each domain with the header format: "Domain Name (Abbreviation)"
        - Use item_description when referencing tasks
        - Quote scoring criteria when explaining what scores mean
        - Provide clinical interpretation of developmental significance
        - Connect findings to functional implications
        - Use professional, clinical language grounded in psychometric evaluation.
        - Use formal diagnostic terms (e.g., "extremely low range," "borderline") to describe performance.
        
        EXAMPLE OF DETAILED CLINICAL ANALYSIS:
        "During fine motor assessment, {child_name}'s performance corresponded to an age equivalent of X months, placing him in the 'extremely low range' with a scaled score of Y. He demonstrated variable performance across developmental tasks. On the Eyes Follow Moving Person task, he achieved a score of 2, indicating his eyes can track a person through midline to both left and right sides according to the scoring criteria, suggesting age-appropriate visual-motor coordination. However, on the Brings Hand to Mouth task, he scored 1, meaning he 'attempts to place his hand in his mouth but does not have consistent success.' This emerging skill suggests delays in motor planning and execution for self-care activities. The overall pattern of scores indicates a significant deficit in fine motor skills, impacting his ability to engage in age-appropriate play and self-care."
        
        Write detailed clinical narrative covering all domains with specific item analysis using item_description and contextal observation, and functional implications using the actual valid answers data provided.
        """
        return prompt 