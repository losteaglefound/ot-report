

def format_pediaeat_prompt(data: dict) -> str:
    """
    Generates a structured clinical prompt from PediEAT assessment JSON data.

    This function processes the JSON data, separating observations into "Areas of
    Concern" (asc_scoring) and "Observed Strengths" (desc_scoring), and formats
    them into a clear, structured prompt for an AI clinical expert.

    Args:
        data: A dictionary containing the PediEAT assessment data, matching
              the structure of the provided JSON.

    Returns:
        A string containing the fully formatted prompt.
    """
    prompt_parts = [
        # "Role: You are a clinical expert in pediatric feeding disorders, specializing in interpreting assessment data.",
        # "\nTask: Analyze the following data from a PediEAT assessment. The data is categorized into domains (e.g., Physiologic Symptoms). Within each domain, observations are split into two scoring types: `asc_scoring` and `desc_scoring`. Your goal is to synthesize this information into a comprehensive clinical summary.",
        "\nScoring Interpretation (Crucial):",
        "`asc_scoring` (Areas of Concern): These are problematic symptoms. A higher score (1-5) indicates a HIGHER level of concern and greater frequency of the problem. A score of 0 means the problem is absent.",
        "`desc_scoring` (Observed Strengths): These are positive, functional behaviors. The scoring is inverted. A higher score (1-5) indicates a LOWER level of concern (i.e., the child performs the skill well). A lower score indicates a higher concern because the strength is absent.",
        "\n---",
        "\nPEDIEAT ASSESSMENT DATA"
    ]

    # Process each main domain (e.g., physiologic_symtoms)
    for domain_key, domain_value in data.items():
        # Format domain name for display (e.g., "physiologic_symtoms" -> "Physiologic Symtoms")
        domain_name = domain_key.replace('_', ' ').title()
        prompt_parts.append(f"\n\nDomain: {domain_name}")

        # Process asc_scoring (Areas of Concern)
        if 'asc_scoring' in domain_value and domain_value['asc_scoring']['observations']:
            asc_scoring_data = domain_value['asc_scoring']
            prompt_parts.append("\n\n1. Areas of Concern (`asc_scoring`)")
            prompt_parts.append("*(For this section, a higher score = higher concern)*")
            
            # Filter for observations with a score > 0
            concern_observations = [obs for obs in asc_scoring_data['observations'] if int(obs['score']) > 0]
            
            if concern_observations:
                for obs in concern_observations:
                    prompt_parts.append(f"{obs['description']}:* Score {obs['score']}/5 ({obs['score_string']})")
            else:
                prompt_parts.append("* No concerns noted in this area.")

            prompt_parts.append(f"Total Concern Score (`asc_scoring`): {asc_scoring_data['score']}")

        # Process desc_scoring (Observed Strengths)
        if 'desc_scoring' in domain_value and domain_value['desc_scoring']['observations']:
            desc_scoring_data = domain_value['desc_scoring']
            prompt_parts.append("\n\n2. Observed Strengths (`desc_scoring`)")
            prompt_parts.append("*(For this section, a higher score = lower concern)*")

            if desc_scoring_data['observations']:
                 for obs in desc_scoring_data['observations']:
                    prompt_parts.append(f"{obs['description']}:* Score {obs['score']}/5 ({obs['score_string']})")
            else:
                prompt_parts.append("* No specific strengths noted in this area.")
            
            prompt_parts.append(f"Total Strength Score (`desc_scoring`): {desc_scoring_data['score']}")


    return "\n".join(prompt_parts)

