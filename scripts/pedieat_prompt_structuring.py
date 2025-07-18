import json

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

    # prompt_parts.extend([
    #     "\n\n---",
    #     "\nEND ASSESSMENT DATA",
    #     "\n\nOutput Requirements:",
    #     "Based on the data provided, please generate a clinical report that includes:",
    #     "1.  Overall Summary: A brief, high-level overview of the child's feeding profile.",
    #     "2.  Detailed Analysis by Domain: For each domain, summarize the findings by integrating the 'Areas of Concern' with the 'Observed Strengths' to provide a balanced view.",
    #     "3.  Key Clinical Concerns: Explicitly list the most severe and high-risk symptoms identified from the data.",
    #     "4.  Recommendations: Suggest next steps, potential referrals (e.g., ENT, SLP, OT), and possible interventions."
    # ])

    return "\n".join(prompt_parts)

# --- Example Usage ---
# Paste your JSON data as a multi-line string
# json_data_string = """
# {
#     "physiologic_symtoms": {
#         "asc_scoring": {
#             "observations": [
#                 {"description": "gets watery eyes when eating", "score": "2", "score_string": "Sometimes"},
#                 {"description": "gets red color around eyes or face when eating", "score": "0", "score_string": "Never"},
#                 {"description": "coughs during or after eating", "score": "2", "score_string": "Sometimes"},
#                 {"description": "sounds gurgly or like they need to cough or clear their throat during or after 4. eating", "score": "1", "score_string": "Almost Never"},
#                 {"description": "sounds different during or after a meal (for example, voice becomes hoarse, 5. high-pitched, or quiet)", "score": "0", "score_string": "Never"},
#                 {"description": "chokes or coughs on water or other thin liquids", "score": "2", "score_string": "Sometimes"},
#                 {"description": "moves head down toward chest when swallowing", "score": "2", "score_string": "Sometimes"},
#                 {"description": "has food or liquid come out of nose when eating", "score": "4", "score_string": "Almost Always"},
#                 {"description": "gets pale or blue color around his/her lips during meals", "score": "0", "score_string": "Never"},
#                 {"description": "breathes faster or harder when eating", "score": "1", "score_string": "Almost Never"},
#                 {"description": "needs to take a break during the meal to rest or catch their breath", "score": "5", "score_string": "Always"},
#                 {"description": "gets tired from eating and is not able to finish", "score": "1", "score_string": "Almost Never"},
#                 {"description": "sweats/gets clammy during meals", "score": "1", "score_string": "Almost Never"},
#                 {"description": "tilts head back while eating", "score": "1", "score_string": "Almost Never"},
#                 {"description": "burps more than usual while eating", "score": "1", "score_string": "Almost Never"},
#                 {"description": "throws up during mealtime", "score": "0", "score_string": "Never"},
#                 {"description": "throws up between meals (from 30 minutes after the last meal until the next 17. meal)", "score": "1", "score_string": "Almost Never"},
#                 {"description": "arches back during or after meals", "score": "2", "score_string": "Sometimes"},
#                 {"description": "gags when it is time to eat (for example, when they see food or when placed in 19. high chair)", "score": "0", "score_string": "Never"},
#                 {"description": "gags with smooth foods like pudding", "score": "0", "score_string": "Never"},
#                 {"description": "gags with textured food like coarse oatmeal", "score": "1", "score_string": "Almost Never"},
#                 {"description": "gags, coughs, or vomits when brushing teeth (if your child does not have teeth, 22. select Never. If your child will not allow you to brush his/her teeth, select Always)", "score": "0", "score_string": "Never"},
#                 {"description": "gets a bloated tummy after eating", "score": "1", "score_string": "Almost Never"},
#                 {"description": "turns red in face, may cry with stooling", "score": "0", "score_string": "Never"},
#                 {"description": "has gas", "score": "0", "score_string": "Never"},
#                 {"description": "drools when eating", "score": "3", "score_string": "Often"},
#                 {"description": "has a hard time eating due to stuffy nose", "score": "5", "score_string": "Always"}
#             ],
#             "score": "36"
#         },
#         "desc_scoring": {
#             "observations": [],
#             "score": "0"
#         }
#     },
#     "problematic_mealtime_bahaviors": {
#         "asc_scoring": {
#             "observations": [
#                 {"description": "avoids eating by playing or talking", "score": "0", "score_string": "Never"},
#                 {"description": "has to be told to start eating", "score": "0", "score_string": "Never"},
#                 {"description": "has to be reminded to keep eating", "score": "3", "score_string": "Often"},
#                 {"description": "won't eat at meals, but wants food later", "score": "0", "score_string": "Never"},
#                 {"description": "stops eating after a few bites", "score": "0", "score_string": "Never"},
#                 {"description": "refuses to eat", "score": "0", "score_string": "Never"},
#                 {"description": "shows more stress during meals than during non-meal times (whines, cries, 34. gets angry, tantrums)", "score": "0", "score_string": "Never"},
#                 {"description": "insists on food being offered in a certain way (such as, how food is on the plate 36. or what dish or spoon is used, or where they sit)", "score": "3", "score_string": "Often"},
#                 {"description": "insists on being fed by the same person(s)", "score": "0", "score_string": "Never"},
#                 {"description": "becomes upset by the smell of food", "score": "0", "score_string": "Never"},
#                 {"description": "throws food or pushes food away", "score": "3", "score_string": "Often"},
#                 {"description": "prefers to drink instead of eat", "score": "1", "score_string": "Almost Never"},
#                 {"description": "prefers crunchy foods", "score": "0", "score_string": "Never"},
#                 {"description": "eats better when entertained", "score": "2", "score_string": "Sometimes"},
#                 {"description": "takes more than 30 minutes to eat", "score": "2", "score_string": "Sometimes"},
#                 {"description": "needs mealtime to be calm", "score": "2", "score_string": "Sometimes"}
#             ],
#             "score": "16"
#         },
#         "desc_scoring": {
#             "observations": [],
#             "score": "0"
#         }
#     }
# }
# """

# Load the JSON data from the string into a Python dictionary
with open("outputs/aws_pedieat_extract.json", 'r') as f:
    json_data_string = f.read()
pediaeat_data = json.loads(json_data_string)

# Generate the structured prompt
structured_prompt = format_pediaeat_prompt(pediaeat_data)

# Print the result
print(structured_prompt)
