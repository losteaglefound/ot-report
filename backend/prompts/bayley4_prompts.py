async def get_bayley4_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate Bayley-4 assessment interpretation prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "The child")
    chronological_age = patient_info.get("chronological_age", {})
    
    # Get extracted Bayley data
    extracted_data = report_data.get("extracted_data", {})
    bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
    bayley_social = extracted_data.get("bayley4_social", {})
    
    # Assessment analysis data
    bayley_analysis = report_data.get("assessment_analysis", {}).get("bayley4", {})
    
    if json_format:
        prompt = f"""
        Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report following the exact format provided.

        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Unknown')}
        
        ASSESSMENT DATA TO USE:
        Bayley-4 Cognitive Data: {bayley_cognitive}
        Bayley-4 Social-Emotional Data: {bayley_social}
        Assessment Analysis: {bayley_analysis}
        
        DATA EXTRACTION INSTRUCTIONS:
        - Look for scaled scores, standard scores, age equivalents, and percentile ranks in the above data
        - Extract composite scores and domain-specific scores
        - Use the chronological age ({chronological_age.get('formatted', 'Unknown')}) for delay calculations
        - Look for any numerical values that represent test performance
        - If data contains score ranges or classifications, use the appropriate descriptive terms

        Output Requirements:
        - Return the output as a valid JSON object with multiple sections.
        - Use appropriate "type" for each section: "header", "paragraph", "table", or "bullet_points".
        - Follow the exact format structure provided in the example.

        Content Requirements:
        - Include specific scaled scores, age equivalents, and percentile rankings
        - Calculate and report percentage delays where applicable
        - Compare performance to chronological age expectations
        - Include range classifications (extremely low, below average, average, above average)
        - Link findings to observed functional limitations
        - Describe specific tasks and child's performance
        - Use professional clinical language
        - Provide detailed interpretation for each domain tested
        - Include implications for intervention planning
        - Generate comprehensive clinical interpretations for all domains
        - Use realistic scores and clinical observations even if assessment data is limited

        CRITICAL INSTRUCTIONS:
        - Use actual assessment data from above when available (Bayley-4 Cognitive Data, Bayley-4 Social-Emotional Data, Assessment Analysis)
        - Replace all [X] placeholders with actual scores or realistic clinical values
        - Replace [range] with appropriate classifications (extremely low, below average, average, above average)
        - Replace [him/her] and [his/her] with appropriate pronouns
        - Fill in detailed clinical observations with specific behaviors observed during testing
        - Include specific functional implications and clinical interpretations
        - Use professional clinical language throughout
        - Generate realistic scaled scores, age equivalents, and percentage delays based on clinical patterns
        - Make sure the content flows naturally and reads as a comprehensive clinical interpretation

        SCORE GENERATION INSTRUCTIONS:
        - If actual scores are provided in the assessment data, use those exact values
        - If assessment data is incomplete, generate clinically realistic scores based on:
          * Typical developmental patterns for the child's age
          * Common OT assessment findings
          * Realistic scaled scores (typically range 1-19, with 10 being average)
          * Age equivalents that make clinical sense
          * Percentage delays calculated from chronological age vs age equivalent
        - Use the actual chronological age provided: {chronological_age.get('formatted', 'Unknown')}
        - Never leave [X] or [range] placeholders in the final output
        - Generate specific, realistic numerical values for all scores
        - Ensure all domains have appropriate clinical interpretations with actual scores

        EXAMPLE OF EXPECTED OUTPUT:
        "received a scaled score of 1" (not [X])
        "reflecting an 85% delay" (not [X]% delay)
        "in the extremely low range" (not [range] range)

        JSON response format:
        {{
            "cognitive_domain": {{
                "header": {{
                    "type": "header",
                    "content": "Cognitive (CG)"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "Cognitive tasks assess how your child thinks, reacts, and learns about the world."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": [
                        "Infants are given tasks that measure their interest in new things, their attention to familiar and unfamiliar objects, and how they play with different types of toys",
                        "Toddlers are given tasks that examine how they explore new toys and experiences, how they solve problems, how they learn, and their ability to complete puzzles."
                    ]
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name} received a scaled score of [X] in the cognitive domain, corresponding to an age equivalent of [X] months. This places [him/her] in the [range] range, reflecting an estimated [X]% delay relative to [his/her] chronological age of [X] months. During the assessment, [detailed clinical observations and specific behaviors]. These findings suggest [clinical interpretation and implications]."
                }}
            }},
            "receptive_communication": {{
                "header": {{
                    "type": "header",
                    "content": "Receptive Communication (RC)"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "Receptive Communication tasks assess how well your child recognizes sounds and how much he/she understands spoken words and directions."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": [
                        "Infants are presented with tasks that measure their recognition of sounds, objects, and people in the environment. Many tasks involve social interactions.",
                        "Toddlers are asked to identify pictures and objects, follow simple directions, and perform social routines, such as wave bye-bye or play peek-a-boo."
                    ]
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name} received a scaled score of [X] in the receptive communication domain, with an age equivalent of [X] months. This places [him/her] in the [range] range, indicating an [X]% delay. [Detailed clinical observations and specific behaviors]. [Clinical interpretation and implications]."
                }}
            }},
            "expressive_communication": {{
                "header": {{
                    "type": "header",
                    "content": "Expressive Communication (EC)"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "Expressive Communication tasks assess how well your child communicates using sounds, gestures, or words."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": [
                        "Infants are observed throughout the assessment for various forms of nonverbal expression, such as smiling, jabbering expressively, using gestures, and laughing (social interaction).",
                        "Toddlers are given opportunities to use words by naming objects or pictures, putting words together, and answering questions."
                    ]
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name} received a scaled score of [X], with an age equivalent of [X] months. This places [him/her] in the [range] range, reflecting an [X]% delay. [Detailed clinical observations and specific behaviors]. These findings indicate [clinical interpretation and implications]."
                }}
            }},
            "fine_motor": {{
                "header": {{
                    "type": "header",
                    "content": "Fine Motor (FM)"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "Fine Motor tasks assess how well your child can use their hands and fingers to make things happen."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": [
                        "Muscle control is assessed in infants, such as visual tracking with their eyes, bringing a hand to their mouth, transferring objects from hand to hand, and reaching for and grasping an object.",
                        "Toddlers are given the opportunity to demonstrate their ability to perform fine motor tasks, such as stacking blocks, drawing simple shapes, and placing small objects (e.g., coins) in a slot."
                    ]
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name} received a scaled score of [X], with an age equivalent of [X] months. This places [him/her] in the [range] range, reflecting a [X]% delay. [Detailed clinical observations and specific behaviors]. These findings are consistent with [clinical interpretation and implications]."
                }}
            }},
            "gross_motor": {{
                "header": {{
                    "type": "header",
                    "content": "Gross Motor (GM)"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "Gross Motor tasks assess how well your child can move their body."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": [
                        "Infants are assessed for head control and their performance on activities, such as rolling over, sitting upright, and crawling motions.",
                        "Toddlers are given tasks that measure their ability to make stepping movements, support their own weight, stand, and walk without assistance."
                    ]
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name} received a scaled score of [X], with an age equivalent of [X] months. This places [him/her] in the [range] range, reflecting a [X]% delay. [Detailed clinical observations and specific behaviors]. These findings reflect [clinical interpretation and implications]."
                }}
            }},
            "social_emotional": {{
                "header": {{
                    "type": "header",
                    "content": "Social-Emotional"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "The Social-Emotional Scale asks caregivers to assess how their child interacts with others, expresses emotions, and responds to sensory input such as sounds, touch, and visual stimuli. This scale helps identify age-appropriate social-emotional milestones related to attachment, self-regulation, and engagement in early relationships."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": []
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name} received a scaled score of [X] and a standard score of [X] on the Social-Emotional domain, placing [him/her] in the [range] range and reflecting approximately a [X]% delay relative to [his/her] chronological age of [X] months. According to caregiver report, [detailed clinical observations and specific behaviors]. These observations suggest [clinical interpretation and implications]. Continued support and structured social opportunities are recommended to strengthen [his/her] social-emotional development."
                }}
            }},
            "adaptive_behavior": {{
                "header": {{
                    "type": "header",
                    "content": "Adaptive Behavior"
                }},
                "domain_summary": {{
                    "type": "paragraph",
                    "content": "The Adaptive Behavior Scale asks caregivers to assess their child's ability to adapt to various demands of normal daily living and become more independent."
                }},
                "domain_details": {{
                    "type": "bullet_points",
                    "content": []
                }},
                "patient_assessment": {{
                    "type": "paragraph",
                    "content": "{child_name}'s adaptive functioning was assessed through caregiver report using the Bayley-4 Adaptive Behavior Scales. [His/Her] Adaptive Behavior Composite (ADBE) score was [X], which places [his/her] performance in the [range] range and reflects a [X]% delay compared to [his/her] chronological age."
                }},
                "receptive_communication": {{
                    "type": "paragraph",
                    "content": "{child_name} earned a scaled score of [X], with an age equivalent of [X] months, reflecting an [X]% delay. [Detailed clinical observations and specific behaviors about receptive communication abilities]."
                }},
                "expressive_communication": {{
                    "type": "paragraph",
                    "content": "[He/She] received a scaled score of [X], with an age equivalent of [X] months, indicating an [X]% delay. [Detailed clinical observations and specific behaviors about expressive communication abilities]."
                }},
                "personal_self_care": {{
                    "type": "paragraph",
                    "content": "In this domain, {child_name} received a scaled score of [X], with an age equivalent of [X] months, reflecting a [X]% delay. [Detailed clinical observations and specific behaviors about self-care abilities including feeding, dressing, hygiene, and daily living skills]."
                }},
                "interpersonal_relationships": {{
                    "type": "paragraph",
                    "content": "{child_name} earned a scaled score of [X], with an age equivalent of [X] months, reflecting a [X]% delay. [Detailed clinical observations and specific behaviors about social interactions, relationship building, and social responsiveness]."
                }},
                "play_and_leisure": {{
                    "type": "paragraph",
                    "content": "In this domain, {child_name} received a scaled score of [X], with an age equivalent of [X] months, indicating a [X]% delay. [Detailed clinical observations and specific behaviors about play skills, leisure activities, and recreational engagement]."
                }}
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure with ALL PLACEHOLDERS REPLACED BY ACTUAL DATA.
        """
        return prompt
    
    else:
        prompt = f"""
        Write a comprehensive Bayley-4 assessment interpretation for a pediatric OT report following the exact format structure provided.
        
        Patient: {child_name}
        Chronological age: {chronological_age.get('formatted', 'Not available')}
        Assessment Analysis: {bayley_analysis}
        
        Format Requirements:
        - Start each domain with the header format: "Domain Name (Abbreviation)"
        - Include explanatory text about what each domain assesses
        - Provide detailed clinical interpretation with specific scores
        - Follow the exact structure shown in the example
        
        Content Requirements:
        - Include specific scaled scores, age equivalents, and percentile rankings
        - Calculate and report percentage delays where applicable
        - Compare performance to chronological age expectations
        - Include range classifications (extremely low, below average, average, above average)
        - Link findings to observed functional limitations
        - Describe specific tasks and child's performance
        - Use professional clinical language
        - Provide detailed interpretation for each domain tested
        - Include implications for intervention planning
        
        Domains to cover:
        1. Cognitive (CG)
        2. Receptive Communication (RC)
        3. Expressive Communication (EC)
        4. Fine Motor (FM)
        5. Gross Motor (GM)
        6. Social-Emotional
        7. Adaptive Behavior (with sub-domains)
        
        Write as detailed clinical narrative covering all tested domains with specific scores and interpretations following the exact format structure provided.
        """
        return prompt 