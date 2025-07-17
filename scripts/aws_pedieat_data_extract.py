
import csv
import json
import re
from typing import Literal


from trp.trp2_analyzeid import TAnalyzeIdDocument, TAnalyzeIdDocumentSchema
from trp import Document


filename = '/home/lap-49/Documents/ot-report/outputs/aws_pedieat_page_merged.json'
raw_data = ""

with open(filename, 'r') as f:
    raw_data = f.read()


json_response = json.loads(raw_data)


doc = Document(json_response)


columns = ['Observations', 'Never', 'Almost Never', "Sometimes", 'Often', 'Almost Always', 'Always', "Score"]

csv_dict: dict = {}
csv_data = []

with open('output.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for page in doc.pages:
        for table in page.tables:
            for row in table.rows:
                d = {col: cell.text for col, cell in zip(columns, row.cells)}
                csv_data.append(d)
                writer.writerow(csv_data)


scores = {
    "Never": "0",
    "Almost Never": "1",
    "Sometimes": "2",
    "Often": "3",
    "Almost Always": "4",
    "Always": "5"
}
scores_reverse = {
    "Never": "5",
    "Almost Never": "4",
    "Sometimes": "3",
    "Often": "2",
    "Almost Always": "1",
    "Always": "0"
}


def get_selected(text):
    matches = re.findall(r'\b[A-Z]+\b', text)
    return matches[0]


csv_data


# t_doc = TAnalyzeIdDocument().load(json.loads(raw_data))
observation_scores = []

for d in csv_data:
    l = []
    for k, v in d.items():
        if v == '': break
        if k == 'Score': continue
        if k == 'Observations':
            l.append(v)
        if "SELECTED" in d[k] and 'NOT_SELECTED' not in d[k]:
            if get_selected(v) == "SELECTED":
                l.append(scores[k])
    if l and not len(l) == 1:
        observation_scores.append(l)


observation_scores





observation_schema = Literal["physiologic_symtoms", "problematic_mealtime_bahaviors", "selective_restrictive_eating", "oral_processing"]
score_schema = Literal['asc_scoring', 'desc_scoring']
observations_keys_schema = Literal['observations', 'total_score']
observation_schema = Literal['description', 'score']

pediate_observations_schema = dict[observation_schema, dict[score_schema, dict[observations_keys_schema, str | list[dict[observation_schema]]]]]

pediate_observations: pediate_observations_schema = {
    "physiologic_symtoms": {
        "asc_scoring": {
            "observations": [],
            "score": ""
        },
        "desc_scoring": {
            "observations": [],
            "score": ""
        }
    },
    "problematic_mealtime_bahaviors": {
        "asc_scoring": {
            "observations": [],
            "score": ""
        },
        "desc_scoring": {
            "observations": [],
            "score": ""
        }
    },
    "selective_restrictive_eating": {
        "asc_scoring": {
            "observations": [],
            "score": ""
        },
        "desc_scoring": {
            "observations": [],
            "score": ""
        }
    },
    "oral_processing": {
        "asc_scoring": {
            "observations": [],
            "score": ""
        },
        "desc_scoring": {
            "observations": [],
            "score": ""
        }
    }
}


for x in observation_scores:
    print(" ----> ".join(x[::-1]))


def clean_sentence(text: str) -> str:
    cleaned_text = re.sub(r'^\d+\.\s+', '', text)
    return cleaned_text


for o in observation_scores:
    print(o[0])


REVERSE_SCORING_QUESTION = [
    "likes to eat",
    "eats a variety of foods (fruits, vegetables, proteins, etc.)",
    "is willing to stay seated during mealtime",
    "opens their mouth when food is offered",
    "is willing to touch food with their hands",
    "will eat mixed texture foods",
    "will eat food warmer than room temperature",
    "is willing to feed self (if younger in age, holds cup, feeds self crackers)",
    "keeps food in mouth when eating (food means non-liquids)",
    "keeps liquids in mouth when drinking",
    "keeps their tongue inside mouth during eating",
    "acts hungry before meals",
    "will eat foods that need to be chewed",
    "will eat textured food like coarse oatmeal",
    "will eat frozen food, like ice cream",
    "chews their food enough",
    "moves food in their mouth when chewing without help"
]
PHYSIOLOGIC_SYMTOMS = [
    "gets watery eyes when eating",
    "gets red color around eyes or face when eating",
    "coughs during or after eating",
    "sounds gurgly or like they need to cough or clear their throat during or after 4. eating",
    "sounds different during or after a meal (for example, voice becomes hoarse, 5. high-pitched, or quiet)",
    "chokes or coughs on water or other thin liquids",
    "moves head down toward chest when swallowing",
    "has food or liquid come out of nose when eating",
    "gets pale or blue color around his/her lips during meals",
    "breathes faster or harder when eating",
    "needs to take a break during the meal to rest or catch their breath",
    "gets tired from eating and is not able to finish",
    "sweats/gets clammy during meals",
    "tilts head back while eating",
    "burps more than usual while eating",
    "throws up during mealtime",
    "throws up between meals (from 30 minutes after the last meal until the next 17. meal)",
    "arches back during or after meals",
    "gags when it is time to eat (for example, when they see food or when placed in 19. high chair)",
    "gags with smooth foods like pudding",
    "gags with textured food like coarse oatmeal",
    "gags, coughs, or vomits when brushing teeth (if your child does not have teeth, 22. select Never. If your child will not allow you to brush his/her teeth, select Always)",
    "gets a bloated tummy after eating",
    "turns red in face, may cry with stooling",
    "has gas",
    "drools when eating",
    "has a hard time eating due to stuffy nose"
]
PROBLEMATIC_MEALTIME_BEHAVIORS = [
    "avoids eating by playing or talking",
    "has to be told to start eating",
    "has to be reminded to keep eating",
    "won't eat at meals, but wants food later",
    "stops eating after a few bites",
    "refuses to eat",
    "shows more stress during meals than during non-meal times (whines, cries, 34. gets angry, tantrums)",
    "insists on food being offered in a certain way (such as, how food is on the plate 36. or what dish or spoon is used, or where they sit)",
    "insists on being fed by the same person(s)",
    "becomes upset by the smell of food",
    "throws food or pushes food away",
    "prefers to drink instead of eat",
    "prefers crunchy foods",
    "eats better when entertained",
    "takes more than 30 minutes to eat",
    "needs mealtime to be calm",
    "wants the same food for more than two weeks in a row",
    "likes to eat",
    "eats a variety of foods (fruits, vegetables, proteins, etc.)",
    "is willing to stay seated during mealtime",
    "opens their mouth when food is offered",
    "is willing to touch food with their hands"
]
SELECTIVE_RESTRICTIVE_EATING = [
    "will eat mixed texture foods",
    "will eat food warmer than room temperature",
    "is willing to feed self (if younger in age, holds cup, feeds self crackers)",
    "keeps food in mouth when eating (food means non-liquids)",
    "keeps liquids in mouth when drinking",
    "keeps their tongue inside mouth during eating",
    "acts hungry before meals",
    "will eat foods that need to be chewed",
    "will eat textured food like coarse oatmeal",
    "will eat frozen food, like ice cream",
    "chews their food enough",
    "moves food in their mouth when chewing without help",
    "sniffs food or objects",
    "spits food out",
    "eats too fast"
]
ORAL_PROCESSING = [
    "stores food in their cheek or roof of mouth",
    "gets food stuck in their cheek or roof of mouth",
    "prefers smooth foods like yogurt",
    "puts too much food in mouth at one time",
    "puts fingers in mouth to move food",
    "prefers strong flavors",
    "bites down on the spoon or fork and does not release it easily",
    "grinds teeth when awake (if your child does not have teeth, please select 73. Never.",
    "chews on toys, clothes, or other objects",
    "has to be reminded to chew food",
    "sucks on food to soften or moisten it, rather than chewing it",
    "chews food but doesn't swallow it",
    "chews a bite of food for a long time (~30 seconds or longer)",
]


def create_json_structure():
    for ob in observation_scores:
        if len(ob) == 2:
            ob_sentence, ob_score = ob[0], ob[1]
            ob_sentence = clean_sentence(ob_sentence).strip()
            if ob_sentence in PROBLEMATIC_MEALTIME_BEHAVIORS:
                if ob_sentence in REVERSE_SCORING_QUESTION:
                    pediate_observations['problematic_mealtime_bahaviors']['desc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
                else:
                    pediate_observations['problematic_mealtime_bahaviors']['asc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
            if ob_sentence in PHYSIOLOGIC_SYMTOMS:
                if ob_sentence in REVERSE_SCORING_QUESTION:
                    pediate_observations['physiologic_symtoms']['desc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
                else:
                    pediate_observations['physiologic_symtoms']['asc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
            if ob_sentence in ORAL_PROCESSING:
                if ob_sentence in REVERSE_SCORING_QUESTION:
                    pediate_observations['oral_processing']['desc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
                else:
                    pediate_observations['oral_processing']['asc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
            if ob_sentence in SELECTIVE_RESTRICTIVE_EATING:
                if ob_sentence in REVERSE_SCORING_QUESTION:
                    pediate_observations['selective_restrictive_eating']['desc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})
                else:
                    pediate_observations['selective_restrictive_eating']['asc_scoring']['observations'].append({'description': ob_sentence, "score": ob_score})

def calculate_total_scores():
    for category_data in pediate_observations.values():
        for scoring_type in ['asc_scoring', 'desc_scoring']:
            observations = category_data[scoring_type]['observations']
            total_score = sum(int(obs['score']) for obs in observations)
            category_data[scoring_type]['score'] = str(total_score)
    


create_json_structure()
calculate_total_scores()

print(f"\n\n {pediate_observations}, {type(pediate_observations)}")

print(json.dumps(pediate_observations, indent=4))











