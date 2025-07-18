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
        chomps_dict = True

    if json_format:
        pedieat_prompt = f"""
        You are a highly experienced occupational therapist with specialized training in pediatric feeding and oral-motor development. Based on the pedieat data provided below, generate a comprehensive, clinical report using professional terminology and a structured format. The tone should be clinical, objective, and precise, appropriate for inclusion in a multidisciplinary medical or therapy report. Provide interpretations and implications where relevant.
        """
        
        if pedieat:
            pedieat_prompt += f"\nPedieat data: \n{pedieat_formatted_data}\n"

        if chomps:
            pedieat_prompt += f"\nChomps data: \n{chomps_dict}\n"
        
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

        ----------------- Guide for Pediate Score Summary --------------
        Generate a clinically concise and professional summary paragraph describing a child's global feeding concerns, grounded in the results of the Pediatric Eating Assessment Tool (PediEAT). Use formal clinical language suitable for inclusion in a multidisciplinary report or evaluation summary. Tailor the paragraph based on specific input, such as the total PediEAT score, concern level, and any relevant subscale domains (e.g., physiological, behavioral, sensory, oral-motor).

        The paragraph should include the following components:
            Identification of the child by first name only (if provided).
            Overall concern level based on the total PediEAT score and how it compares to normative thresholds (e.g., “High Concern”).
            Mention of elevated subscale domains, reflecting whether concerns span multiple areas (physiological, behavioral, sensory, oral-motor).
            Clinical framing, indicating that the data reflects global feeding difficulty and supports need for further assessment/intervention.

        Style Guidelines:
            Use professional, objective tone.
            Write in past tense.
            Avoid speculation or caregiver quotes unless prompted.

        Summarize multiple areas of concern clearly in one paragraph.

        
        -------------------- Guide for generating Feeding observation --------------------
        Generate a detailed clinical paragraph summarizing feeding observations in a pediatric patient, particularly focused on oropharyngeal coordination, respiratory control, and labial function. Use a professional tone suitable for medical records or developmental feeding evaluations. Base the paragraph on observational data, and adapt the language depending on the child’s feeding method (e.g., bottle, breast), behaviors, and age.

        The paragraph should include:
            Breathing-feeding coordination issues, such as:
            Frequent pauses during feeding to catch breath
            Signs of respiratory fatigue (e.g., gulping, labored breathing, poor endurance)
            Immature oropharyngeal coordination or suck-swallow-breathe patterns

        Labial function/mobility, including:
            Lip seal issues (e.g., poor anterior lip seal, lip flaring vs. inversion)
            Upper/lower lip tucking or instability
            Impact on ability to maintain negative intraoral pressure

        Functional consequences of these issues, such as:
            Reduced efficiency
            Inconsistent latch
            Fatigue during oral feeding

        Style Guidelines:
            Use objective, clinical language
            Write in past tense
            Refer to the child by first name if provided
            Avoid caregiver impressions unless requested

        No need to reference interventions or treatment plans unless prompted

        
        ------------ Guide for  generating behavioural observations ------------------
        Generate a detailed clinical paragraph describing a pediatric patient’s behavioral responses during feeding, with a focus on distress behaviors, oral fatigue, and feeding endurance. The paragraph should reflect objective observations and provide clinical insight into how these behaviors may relate to broader feeding difficulties.

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
            }},
            "intraoral_inspection": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF INTRAORAL EXAMINATION FINDINGS. Include oral structures, tissue integrity, dental status, frenulum restrictions, and their impact on feeding function and oral-motor development.**"
            }},
            "pedieat_score_summary": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF PEDIEAT TOTAL SCORES AND DOMAIN-SPECIFIC RESULTS. Include overall concern level, elevated subscale domains, percentile rankings, clinical significance, and implications for feeding intervention.**"
            }},
            "feeding_and_swallowing_observations": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF FEEDING AND SWALLOWING OBSERVATIONS. Include oral-motor coordination, swallowing safety, feeding efficiency, behavioral responses, and specific observations during different textures and feeding methods.**"
            }},
            "clinical_recommendations": {{
                "type": "bullet_points",
                "content": [
                "**REPLACE WITH SPECIFIC CLINICAL RECOMMENDATIONS BASED ON ASSESSMENT FINDINGS. Include intervention strategies, therapy goals, environmental modifications, and referral recommendations.**"
                ]
            }},
            "safety_considerations": {{
                "type": "paragraph",
                "content": "**REPLACE WITH DETAILED INTERPRETATION OF FEEDING SAFETY CONSIDERATIONS. Include aspiration risk, texture modifications, positioning requirements, supervision needs, and emergency protocols.**"
            }}
            }}
        
        IMPORTANT: Replace all content marked with **REPLACE WITH...** with actual clinical interpretations based on the provided PediEAT and feeding assessment data. Do not output the placeholder instructions literally.
        
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