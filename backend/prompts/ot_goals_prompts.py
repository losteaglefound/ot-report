async def get_ot_goals_prompt(report_data: dict, json_format: bool = False) -> str:
    """Generate OT goals prompt for pediatric OT reports."""
    
    patient_info = report_data.get("patient_info", {})
    child_name = patient_info.get("name", "the child")
    age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
    
    # Extract assessment analysis for context
    assessment_analysis = report_data.get("assessment_analysis", {})
    
    if json_format:
        prompt = f"""
        Generate specific, measurable OT goals for a pediatric report.

        Patient: {child_name} (age: {age})
        Assessment Analysis: {assessment_analysis}

        Output Requirements:
        - Return the output as a valid JSON object.
        - Use "type": "bullet_points" for the goals list.
        - Generate 6-8 SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound).

        Content Requirements:
        Create SMART goals that address:
        - Fine motor development and dexterity
        - Gross motor skills and coordination
        - Visual-motor integration
        - Bilateral coordination and crossing midline
        - Self-care and adaptive skills
        - Sensory processing and regulation
        - Pre-writing and tool use skills
        - Social participation and play skills

        Goal Format Requirements:
        - Include specific timeframes (within 3-6 months)
        - Specify measurable criteria (4 out of 5 opportunities, 80% accuracy, etc.)
        - Define assistance levels (independent, minimal assistance, moderate cues)
        - Include functional context (during play, at home, in classroom)
        - Use age-appropriate expectations

        Example format: "Within [timeframe], [child] will [specific action] with [level of assistance] in [context] as measured by [criteria]."

        JSON response format:
        {{
            "ot_goals": {{
                "type": "bullet_points",
                "content": [
                    "Within six months, {child_name} will stack 5 one-inch blocks independently in 4 out of 5 opportunities with no more than 2 verbal prompts, to improve visual-motor coordination and hand stability for age-appropriate play skills.",
                    "Within six months, {child_name} will string 3-4 large beads onto a string in 4 out of 5 opportunities with moderate assistance, demonstrating bilateral hand use and midline crossing during fine motor activities.",
                    "Within six months, {child_name} will use a tripod or quadrupod grasp to hold a crayon and make controlled marks on paper in 4 out of 5 opportunities with minimal prompts, promoting pre-writing skill development.",
                    "Within six months, {child_name} will complete a 4-piece puzzle independently in 4 out of 5 opportunities, demonstrating improved visual-perceptual skills and problem-solving abilities.",
                    "Within six months, {child_name} will transition between activities with no more than 1 verbal prompt in 4 out of 5 opportunities, improving behavioral regulation and attention skills.",
                    "Within six months, {child_name} will demonstrate age-appropriate self-feeding skills using utensils with minimal assistance in 4 out of 5 meal opportunities."
                ]
            }}
        }}

        Ensure the response is valid JSON and follows this exact structure.
        """
        return prompt
    
    else:
        prompt = f"""
        Generate 6-8 specific, measurable OT goals for {child_name} following SMART goal format.
        
        Assessment context: {assessment_analysis}
        
        Include:
        - Timeline (within 3-6 months)
        - Specific activity/skill
        - Measurable criteria (4 out of 5 opportunities)
        - Assistance level
        - Focus areas: fine motor, visual-motor, bilateral coordination, pre-writing, self-care
        
        Format each goal as a complete sentence with specific metrics.
        """
        return prompt 