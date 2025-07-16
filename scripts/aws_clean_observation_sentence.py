import json
import re


def clean_observation():
    """
    Clean sentence, remove number, dot and space
    from starting of the sentence.
    """
    def clean_sentence(text: str) -> str:
        cleaned_text = re.sub(r'^\d+\.\s+', '', text)
        return cleaned_text

    with open("outputs/aws_chomps_observation_data.json", 'r') as f:
        data = json.loads(f.read())

    observation_data = data["observationsByCategory"]
    
    for cat, observations in observation_data.items():
        cleaned_observations = []
        for ob in observations:
            text = clean_sentence(ob['observation'])
            print(text)
            ob['observation'] = text
            cleaned_observations.append(ob)
        observation_data[cat] = cleaned_observations
    
    data["observationsByCategory"] = observation_data

    with open("outputs/aws_chomps_observation_data_cleaned.json", 'w+') as f:
        f.write(json.dumps(data, indent=4))

if __name__ == "__main__":
    clean_observation()