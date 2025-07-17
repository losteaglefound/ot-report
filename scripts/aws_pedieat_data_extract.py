
import csv
import json
import re
from typing import Literal, TypedDict, cast


from trp.trp2_analyzeid import TAnalyzeIdDocument, TAnalyzeIdDocumentSchema
from trp import Document


# Functional approach: Data extraction and processing functions
def get_selected(text: str) -> str | None:
    matches = re.findall(r'\b[A-Z]+\b', text)
    return matches[0] if matches else None


def clean_sentence(text: str) -> str:
    return re.sub(r'^\d+\.\s+', '', text).strip()


def extract_observation_score(row: dict[str, str], scores: dict[str, str]) -> list[str] | None:
    observation = row.get('Observations')
    if not observation:
        return None

    for key, value in row.items():
        if key in scores and "SELECTED" in value and "NOT_SELECTED" not in value:
            if get_selected(value) == "SELECTED":
                return [observation, scores[key]]
    return None


def categorize_observation(
    observation_score: list[str],
    categories: dict[str, list[str]],
    reverse_scoring_questions: list[str]
) -> tuple[str, str, dict[str, str]] | None:
    
    ob_sentence = clean_sentence(observation_score[0])
    ob_score = observation_score[1]

    for category, questions in categories.items():
        if ob_sentence in questions:
            scoring_type = 'desc_scoring' if ob_sentence in reverse_scoring_questions else 'asc_scoring'
            return category, scoring_type, {'description': ob_sentence, "score": ob_score}
    return None


# Data Schemas and Types
class Observation(TypedDict):
    description: str
    score: str

class ScoringData(TypedDict):
    observations: list[Observation]
    score: str

class ObservationCategory(TypedDict):
    asc_scoring: ScoringData
    desc_scoring: ScoringData

PediateObservations = dict[str, ObservationCategory]


# Main data processing function
def process_document_to_pediate_observations(doc: Document) -> PediateObservations:
    columns = ['Observations', 'Never', 'Almost Never', "Sometimes", 'Often', 'Almost Always', 'Always', "Score"]
    scores = {
        "Never": "0", "Almost Never": "1", "Sometimes": "2",
        "Often": "3", "Almost Always": "4", "Always": "5"
    }
    scores_reverse = {
        "Never": "5",
        "Almost Never": "4",
        "Sometimes": "3",
        "Often": "2",
        "Almost Always": "1",
        "Always": "0"
    }

    # Data is extracted and transformed through a series of pure functions
    csv_data = [
        {col: cell.text for col, cell in zip(columns, row.cells)}
        for page in doc.pages
        for table in page.tables
        for row in table.rows
    ]

    observation_scores = [
        score for row in csv_data
        if (score := extract_observation_score(row, scores)) is not None
    ]
    
    # Initialize the data structure
    pediate_observations: PediateObservations = {
        category: {
            "asc_scoring": {"observations": [], "score": ""},
            "desc_scoring": {"observations": [], "score": ""}
        } for category in OBSERVATION_CATEGORIES
    }

    # Categorize observations
    for ob_score in observation_scores:
        result = categorize_observation(ob_score, OBSERVATION_CATEGORIES, REVERSE_SCORING_QUESTION)
        if result:
            category, scoring_type, observation_data = result
            # We cast here to satisfy the type checker, as we are building the structure
            cast(ScoringData, pediate_observations[category][scoring_type])['observations'].append(observation_data)

    # Calculate final scores
    for category_data in pediate_observations.values():
        for scoring_type in ['asc_scoring', 'desc_scoring']:
            scoring_dict = cast(ScoringData, category_data[scoring_type])
            observations = scoring_dict['observations']
            total_score = sum(int(obs['score']) for obs in observations)
            scoring_dict['score'] = str(total_score)
            
    return pediate_observations


# Constants (moved here for clarity)
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

OBSERVATION_CATEGORIES = {
    "physiologic_symtoms": PHYSIOLOGIC_SYMTOMS,
    "problematic_mealtime_bahaviors": PROBLEMATIC_MEALTIME_BEHAVIORS,
    "selective_restrictive_eating": SELECTIVE_RESTRICTIVE_EATING,
    "oral_processing": ORAL_PROCESSING,
}


def main():
    """Main function to run the data extraction and processing."""
    filename = '/home/lap-49/Documents/ot-report/outputs/aws_pedieat_page_merged.json'
    try:
        with open(filename, 'r') as f:
            raw_data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return

    json_response = json.loads(raw_data)
    doc = Document(json_response)
    
    # Get the final structured data
    pediate_observations = process_document_to_pediate_observations(doc)

    # Output the result
    print(json.dumps(pediate_observations, indent=4))


if __name__ == "__main__":
    main()











