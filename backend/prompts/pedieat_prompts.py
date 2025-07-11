async def get_pedieat_prompt(pedieat_analysis: str, json_format=False) -> str:
    if json_format:
        pedieat_prompt = f"""
        You are a highly experienced occupational therapist with specialized training in pediatric feeding and oral-motor development. Based on the pedieat data provided below, generate a comprehensive, clinical report using professional terminology and a structured format. The tone should be clinical, objective, and precise, appropriate for inclusion in a multidisciplinary medical or therapy report. Provide interpretations and implications where relevant.
        PediEAT Analysis: {pedieat_analysis}

        
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
            "pedieat_overview": {{
                "type": "header",
                "content": "PediEAT Assessment (Feeding Evaluation Report)"
            }},
            "physical_examination_header": {{
                "type": "physical_examination_header",
                "content": "Physical Examination"
            }},
            "physical_examination": {{
                "type": "paragraph",
                "content": {{
                "body": "replace the content with detailed interpretation from the given data",
                "head_and_neck": "replace the content with detailed interpretation from the given data",
                "face": "replace the content with detailed interpretation from the given data",
                "jaw": "replace the content with detailed interpretation from the given data",
                "lips": "replace the content with detailed interpretation from the given data",
                "tongue": "replace the content with detailed interpretation from the given data",
                "cheeks": "replace the content with detailed interpretation from the given data",
                "palate": "replace the content with detailed interpretation from the given data"
                }}
            }},
            "cranial_nerve_screening_header": {{
                "type": "cranial_nerve_screening_header",
                "content": "Cranial Nerve Screening"
            }},
            "cranial_nerve_screening": {{
                "type": "paragraph",
                "content": {{
                "CN I (Olfactory)": "replace the content with detailed interpretation from the given data",
                "CN V (Trigeminal)": "replace the content with detailed interpretation from the given data",
                "CN VII (Facial)": "replace the content with detailed interpretation from the given data",
                "CN IX (Glossopharyngeal)": "replace the content with detailed interpretation from the given data",
                "CN X (Vagus):": "replace the content with detailed interpretation from the given data",
                "CN XI (Accessory)": "replace the content with detailed interpretation from the given data",
                "CN XII (Hypoglossal)": "replace the content with detailed interpretation from the given data"
                }}
            }},
            "intraoral_inspection": {{
                "type": "paragraph",
                "content": "replace the content with detailed interpretation from the given data"
            }},
            "pedieat_score_summary": {{
                "type": "paragraph",
                "content": "replace the content with detailed interpretation from the given data"
            }},
            "feeding_and_swallowing_observations": {{
                "type": "paragraph",
                "content": "replace the content with detailed interpretation from the given data"
            }},
            "clinical_recommendations": {{
                "type": "bullet_points",
                "content": [
                "replace the content with detailed interpretation from the given data"
                ]
            }},
            "safety_considerations": {{
                "type": "paragraph",
                "content": "replace the content with detailed interpretation from the given data"
            }}
            }}
        Ensure the response is valid JSON and all required sections are populated with clinical-level detail.
        """
        return pedieat_prompt
    
    pedieat_prompt = f"""
    Write a detailed PediEAT assessment interpretation for a pediatric OT report.

    PediEAT Analysis: {pedieat_analysis}

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