import json

from ..utils.pedieat import format_pediaeat_prompt

async def get_pedieat_prompt(extracted_data: dict, json_format=False) -> str:

    pedieat_dict = extracted_data.get('pedieat', {})
    chomps_dict = extracted_data.get('chomps', {})

    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(pedieat_dict)
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(chomps_dict)
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")



    pedieat_formatted_data = format_pediaeat_prompt(pedieat_dict)

    pedieat = False
    if pedieat_dict:
        pedieat = True

    chomps = False
    if chomps_dict:
        chomps = True

    print(f"\nPedieat: {pedieat}, Chomps: {chomps}\n")

    if json_format:
        pedieat_prompt = f"""
        You are a highly experienced occupational therapist with specialized training in pediatric feeding and oral-motor development. Based on the data provided below, generate a comprehensive, clinical report using professional terminology and a structured format. The tone should be clinical, objective, and precise, appropriate for inclusion in a multidisciplinary medical or therapy report. Provide interpretations and implications where relevant.
        """
        
        if pedieat:
            pedieat_prompt += f"\nPediEAT data: \n{pedieat_formatted_data}\n"

        if chomps:
            pedieat_prompt += f"\nChOMPS data: \n{chomps_dict}\n"
        
        pedieat_prompt += """
        
        --------- Guides for Intraoral Inspection --------
        Generate a clinically detailed and anatomically accurate intraoral inspection report for a pediatric patient. The report should be based on the context provided (including patient age, presenting concerns, and findings). Use formal medical language appropriate for clinical documentation. Address relevant anatomical, functional, and diagnostic components, adapting the content based on the specific oral structure examined (e.g., labial frenulum, lingual frenulum, buccal tie).

        The report should include the following sections and considerations:
        Anatomical Findings:
            Identify the specific oral structure examined (e.g., upper labial frenulum, lingual frenulum, buccal mucosa).
            Describe the insertion point (e.g., alveolar ridge, gingival margin, floor of mouth).
            Detail tissue tension/tethering, visibility, elasticity, and presence of blanching on retraction.
            Note any limitations in elevation or lateral movement of the lips or tongue.

        Functional Implications:
            Explain how anatomical findings may impact oral motor function.
            Include effects on feeding (e.g., latch, suction, milk transfer, spillage), speech development, or oral rest posture.
            Mention compensatory behaviors (e.g., jaw thrusting, increased effort during sucking, tongue cupping).

        Diagnostic Impression:
            If applicable, include suspected classification (e.g., Kotlow Class II lingual restriction) based on visual screening.
            If insufficient for full classification, indicate need for further functional assessment.

        Recommendations:
            Suggest referral to relevant specialists (e.g., pediatric dentist, ENT, IBCLC, speech-language pathologist).
            Recommend further evaluation if oral tethering is suspected to impact feeding, speech, or oral development.

        Style Guidelines:
            Use past tense and objective clinical tone.
            Avoid caregiver or patient-reported data unless prompted.

        ---------------------------------------------------------------

        ----------------- Guide for Assessment Overview Paragraph --------------"""
        
        # Add conditional instructions based on available data
        if pedieat and chomps:
            pedieat_prompt += """
        Generate a comprehensive introductory paragraph that establishes the assessment approach using both ChOMPS and PediEAT tools. The paragraph should:
            - Identify that the child's feeding abilities were assessed using both the Child Oral and Motor Proficiency Scale (ChOMPS) and the Pediatric Eating Assessment Tool (PediEAT)
            - Mention completion by caregiver and inclusion of clinical observations during feeding assessment
            - Present overall summary of significant concerns related to oral-motor coordination and feeding performance
            - State how these concerns interfere with age-appropriate mealtime routines and feeding independence
            - Use professional clinical language appropriate for multidisciplinary reports
            """
        elif pedieat:
            pedieat_prompt += """
        Generate an introductory paragraph focusing on PediEAT assessment. The paragraph should:
            - Identify that the child's feeding abilities were assessed using the Pediatric Eating Assessment Tool (PediEAT)
            - Mention completion by caregiver and inclusion of clinical observations during feeding assessment
            - Present overall summary of concerns related to feeding performance
            - State how these concerns interfere with age-appropriate mealtime routines
            - Use professional clinical language appropriate for multidisciplinary reports
            """
        elif chomps:
            pedieat_prompt += """
        Generate an introductory paragraph focusing on ChOMPS assessment. The paragraph should:
            - Identify that the child's feeding abilities were assessed using the Child Oral and Motor Proficiency Scale (ChOMPS)
            - Mention completion by caregiver and inclusion of clinical observations during feeding assessment
            - Present overall summary of concerns related to oral-motor coordination and feeding performance
            - State how these concerns interfere with age-appropriate mealtime routines and feeding independence
            - Use professional clinical language appropriate for multidisciplinary reports
            """

        pedieat_prompt += """

        ----------------- Guide for ChOMPS Assessment Paragraph --------------"""
        
        if chomps:
            pedieat_prompt += """
        Generate a detailed clinical paragraph analyzing ChOMPS results. The paragraph should include:
            - Statement that ChOMPS results indicate concerns across relevant domains (complex movement patterns, basic movement patterns, oral-motor coordination, fundamental oral-motor skills)
            - Analysis of self-feeding abilities, noting hand-to-mouth skills while identifying inefficiencies due to oral control limitations
            - Detailed description of chewing patterns (vertical vs. rotary movement, jaw stability, tongue lateralization)
            - Observations of audible behaviors, food retention patterns, and compensatory strategies
            - Assessment of lip closure consistency and coordination
            - Description of bolus formation abilities and intraoral awareness
            - Clinical interpretation linking findings to developmental delays in volitional oral-motor control
            - Discussion of implications for texture progression and feeding independence
            - Use professional terminology related to oral-motor development and feeding skills
            """
        else:
            pedieat_prompt += """
        Note: ChOMPS data not provided - this section will not be included in the assessment paragraph.
            """

        pedieat_prompt += """

        ----------------- Guide for PediEAT Assessment Paragraph --------------"""
        
        if pedieat:
            pedieat_prompt += """
        Generate a detailed clinical paragraph analyzing PediEAT results. The paragraph should include:
            - Statement that PediEAT findings support presence of feeding dysfunction with total score and concern level
            - Analysis of elevated domain scores (physiologic symptoms, oral processing, selective/restrictive eating, problematic mealtime behaviors)
            - Detailed description of physiologic symptoms including vomiting, food retention, swallow responses
            - Assessment of oral processing difficulties including tongue movement, chewing coordination, food manipulation
            - Analysis of selective/restrictive eating patterns, texture preferences, and refusal behaviors
            - Discussion of mealtime fatigue and aspiration risk factors
            - Differentiation between motor-based vs. behavioral origins of feeding difficulties
            - Clinical interpretation highlighting need for skilled intervention targeting oral-motor development, swallowing safety, and dietary expansion
            - Use professional terminology related to pediatric dysphagia and feeding disorders
            """
        else:
            pedieat_prompt += """
        Note: PediEAT data not provided - this section will not be included in the assessment paragraph.
            """

        pedieat_prompt += """

        ------------ Guide for  generating behavioural observations ------------------
        Generate a detailed clinical paragraph describing a pediatric patient's behavioral responses during feeding, with a focus on distress behaviors, oral fatigue, and feeding endurance. The paragraph should reflect objective observations and provide clinical insight into how these behaviors may relate to broader feeding difficulties.

        Include the following elements:
            Behavioral indicators of distress, such as:
                Food refusal, reduced intake
                Irritability, crying, pulling away
                Inconsistent acceptance of feeding routines
                Escalating stress during the meal

        Duration and tolerance:
            Note if the child stops feeding after a short period or few bites/sips
            Signs of poor feeding endurance or oral fatigue

        Potential contributing factors, such as:
            Oral discomfort
            Inefficient oral-motor skills
            Negative past feeding experiences

        Functional impact:
            How behaviors may be reinforcing a negative association with feeding
            Effects on intake, nutrition, and feeding progress

        Style Guidelines:
            Use formal, clinical language
            Write in past tense
            Refer to the child by first name if provided
            Do not quote caregivers unless instructed
            Compose a single paragraph

        ------------------------------------------------------------

        If no significant findings are noted, include that in professional terms.
        
        JSON response format:
        {{
            "physical_examination_header": {{
                "type": "physical_examination_header",
                "content": "Physical Examination"
            }},
            "physical_examination": {{
                "type": "physical_examination_paragraph",
                "content": {{
                "Body": "**REPLACE WITH DETAILED INTERPRETATION OF BODY POSITIONING AND GENERAL PHYSICAL FINDINGS. Include postural observations, muscle tone, overall physical presentation, and their impact on feeding function.**",
                "Head & Neck": "**REPLACE WITH DETAILED INTERPRETATION OF HEAD AND NECK STRUCTURE AND FUNCTION. Include head control, neck stability, positioning during feeding, and any structural abnormalities that affect feeding.**",
                "Face": "**REPLACE WITH DETAILED INTERPRETATION OF FACIAL STRUCTURE AND SYMMETRY. Include facial muscle tone, symmetry, expressions, and any dysmorphic features that impact oral-motor function.**",
                "Jaw": "**REPLACE WITH DETAILED INTERPRETATION OF JAW STRUCTURE AND FUNCTION. Include jaw stability, range of motion, strength, grading patterns, and their impact on chewing and biting.**",
                "Lips": "**REPLACE WITH DETAILED INTERPRETATION OF LIP STRUCTURE AND FUNCTION. Include lip seal, mobility, strength, coordination, and their impact on feeding efficiency and liquid containment.**",
                "Tongue": "**REPLACE WITH DETAILED INTERPRETATION OF TONGUE STRUCTURE AND FUNCTION. Include tongue mobility, strength, coordination, lateralization, elevation, and their impact on bolus manipulation and swallowing.**",
                "Cheeks": "**REPLACE WITH DETAILED INTERPRETATION OF CHEEK STRUCTURE AND FUNCTION. Include cheek tone, buccal tension, coordination with tongue movements, and their role in bolus containment.**",
                "Palate": "**REPLACE WITH DETAILED INTERPRETATION OF PALATE STRUCTURE AND FUNCTION. Include hard and soft palate integrity, height, width, and their impact on suction and swallowing safety.**"
                }}
            }},
            "cranial_nerve_screening_header": {{
                "type": "cranial_nerve_screening_header",
                "content": "Cranial Nerve Screening"
            }},
            "cranial_nerve_screening": {{
                "type": "cranial_nerve_screening_paragraph",
                "content": {{
                "CN I (Olfactory)": "**REPLACE WITH DETAILED INTERPRETATION OF OLFACTORY NERVE FUNCTION. Include smell recognition, appetite stimulation, and their impact on feeding motivation and safety.**",
                "CN V (Trigeminal)": "**REPLACE WITH DETAILED INTERPRETATION OF TRIGEMINAL NERVE FUNCTION. Include sensation, jaw strength, bite reflex, and their impact on chewing and protective reflexes.**",
                "CN VII (Facial)": "**REPLACE WITH DETAILED INTERPRETATION OF FACIAL NERVE FUNCTION. Include facial expressions, lip seal, cheek function, and their impact on feeding efficiency and oral containment.**",
                "CN IX (Glossopharyngeal)": "**REPLACE WITH DETAILED INTERPRETATION OF GLOSSOPHARYNGEAL NERVE FUNCTION. Include taste sensation, gag reflex, and their impact on swallowing safety and food acceptance.**",
                "CN X (Vagus):": "**REPLACE WITH DETAILED INTERPRETATION OF VAGUS NERVE FUNCTION. Include swallowing coordination, voice quality, cough reflex, and their impact on airway protection and feeding safety.**",
                "CN XI (Accessory)": "**REPLACE WITH DETAILED INTERPRETATION OF ACCESSORY NERVE FUNCTION. Include neck and shoulder muscle function, head positioning, and their impact on feeding posture and stability.**",
                "CN XII (Hypoglossal)": "**REPLACE WITH DETAILED INTERPRETATION OF HYPOGLOSSAL NERVE FUNCTION. Include tongue movement, strength, coordination, and their impact on bolus manipulation and swallowing initiation.**"
                }}
            }},"""
        
        # Add conditional assessment paragraphs based on available data
        if pedieat and chomps:
            pedieat_prompt += """
            "assessment_overview": {{
                "type": "paragraph",
                "content": "**REPLACE WITH COMPREHENSIVE ASSESSMENT OVERVIEW. Include introduction to both ChOMPS and PediEAT assessments, completion by caregiver, clinical observations, overall concerns about oral-motor coordination and feeding performance, and interference with age-appropriate mealtime routines.**"
            }},
            "chomps_assessment": {{
                "type": "paragraph", 
                "content": "**REPLACE WITH DETAILED CHOMPS ASSESSMENT ANALYSIS. Include concerns across all four domains, self-feeding abilities and inefficiencies, chewing patterns, tongue lateralization, food retention, compensatory strategies, lip closure, and implications for feeding development.**"
            }},
            "pedieat_assessment": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED PEDIEAT ASSESSMENT ANALYSIS. Include total score and concern level, elevated domain scores, physiologic symptoms, oral processing difficulties, selective eating patterns, mealtime behaviors, motor vs behavioral origins, and intervention needs.**"
            }},"""
        elif pedieat:
            pedieat_prompt += """
            "assessment_overview": {{
                "type": "paragraph",
                "content": "**REPLACE WITH PEDIEAT ASSESSMENT OVERVIEW. Include introduction to PediEAT assessment, completion by caregiver, clinical observations, overall concerns about feeding performance, and interference with mealtime routines.**"
            }},
            "pedieat_assessment": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED PEDIEAT ASSESSMENT ANALYSIS. Include total score and concern level, elevated domain scores, physiologic symptoms, oral processing difficulties, selective eating patterns, mealtime behaviors, motor vs behavioral origins, and intervention needs.**"
            }},"""
        elif chomps:
            pedieat_prompt += """
            "assessment_overview": {{
                "type": "paragraph",
                "content": "**REPLACE WITH CHOMPS ASSESSMENT OVERVIEW. Include introduction to ChOMPS assessment, completion by caregiver, clinical observations, overall concerns about oral-motor coordination and feeding performance, and interference with age-appropriate mealtime routines.**"
            }},
            "chomps_assessment": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED CHOMPS ASSESSMENT ANALYSIS. Include concerns across all four domains, self-feeding abilities and inefficiencies, chewing patterns, tongue lateralization, food retention, compensatory strategies, lip closure, and implications for feeding development.**"
            }},"""

        # pedieat_prompt += """
        #     "intraoral_inspection": {{
        #         "type": "paragraph",
        #         "content": "**REPLACE WITH DETAILED INTERPRETATION OF INTRAORAL EXAMINATION FINDINGS. Include oral structures, tissue integrity, dental status, frenulum restrictions, and their impact on feeding function and oral-motor development.**"
        #     }},
        #     "feeding_and_swallowing_observations": {{
        #         "type": "paragraph",
        #         "content": "**REPLACE WITH DETAILED INTERPRETATION OF FEEDING AND SWALLOWING OBSERVATIONS. Include oral-motor coordination, swallowing safety, feeding efficiency, behavioral responses, and specific observations during different textures and feeding methods.**"
        #     }},
        #     "clinical_recommendations": {{
        #         "type": "bullet_points",
        #         "content": [
        #         "**REPLACE WITH SPECIFIC CLINICAL RECOMMENDATIONS BASED ON ASSESSMENT FINDINGS. Include intervention strategies, therapy goals, environmental modifications, and referral recommendations.**"
        #         ]
        #     }},
        #     "safety_considerations": {{
        #         "type": "paragraph",
        #         "content": "**REPLACE WITH DETAILED INTERPRETATION OF FEEDING SAFETY CONSIDERATIONS. Include aspiration risk, texture modifications, positioning requirements, supervision needs, and emergency protocols.**"
        #     }}
        #     }}
        # """

        pedieat_prompt += """
        IMPORTANT: Replace all content marked with **REPLACE WITH...** with actual clinical interpretations based on the provided assessment data. Do not output the placeholder instructions literally.
        
        Ensure the response is valid JSON and all required sections are populated with clinical-level detail.
        """

        with open("outputs/pedieat_formatted_prompt.txt", 'w+') as f:
            f.write(pedieat_prompt)


        return pedieat_prompt
    
    pedieat_prompt = f"""
    Write a detailed PediEAT assessment interpretation for a pediatric OT report.

    PediEAT Analysis: {pedieat_dict}

    Requirements:
    - Report domain-specific scores and levels of concern
    - Describe feeding physiology findings (oral motor, swallowing safety)
    - Address feeding processing abilities (texture acceptance, utensil use)  
    - Include feeding behavior analysis (mealtime behaviors, food selectivity)
    - Include safety considerations and aspiration risk assessment
    - Provide specific clinical recommendations
    - Address texture modification needs and feeding progression
    - Include caregiver education and mealtime strategies
    - Use professional terminology related to pediatric feeding and dysphagia
    - Connect findings to functional feeding abilities and nutritional adequacy
    
    Focus on feeding safety, efficiency, and recommendations for intervention.
    """
    return pedieat_prompt