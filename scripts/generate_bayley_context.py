import json
import argparse
import os
from typing import TypedDict, List, Tuple
import openai
from dotenv import load_dotenv
import logging

from langgraph.graph import StateGraph, END


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- OpenAI Client Initialization ---
# Load environment variables from .env file, if it exists.
load_dotenv()
# Get the OpenAI API key from environment variables.
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    client = openai.OpenAI(api_key=api_key)
else:
    print("Warning: OPENAI_API_KEY not found in environment variables. AI-based context generation will be skipped.")


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        report_data: The full report data loaded from the input JSON.
        input_file: Path to the input JSON file.
        output_file: Path to the destination for the enriched JSON file.
        subdomains_to_process: A list of subdomain keys to process.
        current_subdomain_index: The index of the subdomain currently being processed.
    """
    report_data: dict
    input_file: str
    output_file: str
    subdomains_to_process: List[str]
    current_subdomain_index: int

def get_patient_info(state: GraphState) -> Tuple[str, Tuple[str, str, str]]:
    """Extracts patient's name and pronouns from the report data."""
    patient_info = state["report_data"].get("patient_info", {})
    name = patient_info.get("name", "The child")
    sex = patient_info.get("sex", "They").lower()
    
    if sex == "male":
        pronouns = ("he", "his", "him")
    elif sex == "female":
        pronouns = ("she", "her", "her")
    else:
        pronouns = ("they", "their", "them")
        
    return name, pronouns

def generate_bulk_observations(patient_name: str, pronouns: Tuple[str, str, str], items: List[dict], subdomain_name: str) -> dict:
    """Generates detailed observations for a list of items in a single API call."""
    if not client:
        logging.warning("OpenAI client not initialized. Skipping AI-based context generation.")
        return {}

    subject_pronoun, possessive_pronoun, object_pronoun = pronouns

    # Prepare a condensed list of items for the prompt
    items_for_prompt = [
        {
            "item_no": item.get("item_no"),
            "item_description": item.get("item_description"),
            "valid_answer": item.get("valid_answer"),
            "scoring_criteria": item.get("scoring_criteria"),
        }
        for item in items
    ]

    prompt = f"""
    You are an expert pediatric occupational therapist analyzing a Bayley-4 assessment for a child named {patient_name}.

    **Child's Name:** {patient_name}
    **Child's Pronouns:** {subject_pronoun}/{possessive_pronoun}/{object_pronoun}
    **Assessment Subdomain:** {subdomain_name.replace('_', ' ').title()}

    **Assessment Items:**
    {json.dumps(items_for_prompt, indent=2)}

    **Your Task:**
    For EACH item in the list above, write a detailed, narrative observation about {patient_name}'s performance.
    - Interpret each score in the context of its scoring criteria.
    - Describe the likely behaviors {patient_name} exhibited to achieve this score.
    - Frame each observation in a professional, clinical tone, suitable for a formal report.

    **Output Format:**
    Return your response as a single, valid JSON array of objects. Each object must have "item_no" and "contextual_observation" keys.
    Example:
    {{
        "observations": [
            {{
                "item_no": "1",
                "contextual_observation": "The detailed narrative for item 1."
            }},
            {{
                "item_no": "2",
                "contextual_observation": "The detailed narrative for item 2."
            }}
        ]
    }}
    Ensure every item from the input list has a corresponding entry in your JSON response.
    """

    try:
        logging.info(f"Generating bulk observations for subdomain: '{subdomain_name}'...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert pediatric occupational therapist outputting JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        # The response content is a JSON string, which needs to be parsed.
        # It is expected to be a dictionary, potentially with a key containing the list.
        # Let's find the key that holds the array of observations.
        response_content = response.choices[0].message.content
        response_content = response_content.replace("```json", "").replace("```", "")
        response_data = json.loads(response_content)
        
        print("Response data: ", response_data)
        
        observations_list = []
        for key, value in response_data.items():
            if isinstance(value, list):
                observations_list = value
                break
        
        if not observations_list:
            logging.error(f"Could not find an array of observations in the JSON response for subdomain '{subdomain_name}'.")
            return {}

        logging.info(f"Successfully generated bulk observations for subdomain: '{subdomain_name}'.")
        
        # Convert list of observations to a dictionary mapping item_no to observation
        return {str(obs.get("item_no")): obs.get("contextual_observation") for obs in observations_list}

    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from OpenAI response for subdomain '{subdomain_name}'.")
        return {}
    except Exception as e:
        logging.error(f"Error calling OpenAI API for subdomain '{subdomain_name}': {e}")
        return {}

def load_data(state: GraphState) -> GraphState:
    """Loads the report data from the input JSON file."""
    logging.info(f"Loading data from {state['input_file']}...")
    try:
        with open(state['input_file'], 'r') as f:
            data = json.load(f)
        state["report_data"] = data
        logging.info("Data loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: Input file not found at {state['input_file']}")
        return
    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from {state['input_file']}")
        return
    return state

def process_subdomain(state: GraphState) -> GraphState:
    """Processes one subdomain, adding contextual observations and removing scoring criteria."""
    subdomain_index = state["current_subdomain_index"]
    subdomain = state["subdomains_to_process"][subdomain_index]
    logging.info(f"Processing subdomain: {subdomain}...")

    patient_name, pronouns = get_patient_info(state)
    
    try:
        subdomain_data = state["report_data"]["bayley"]["cognitive_and_motor"][subdomain]
        if isinstance(subdomain_data, list) and subdomain_data:
            observations_map = generate_bulk_observations(patient_name, pronouns, subdomain_data, subdomain)

            if observations_map:
                for item in subdomain_data:
                    item_no = str(item.get("item_no"))
                    if item_no in observations_map:
                        item["contextual_observation"] = observations_map[item_no]
                    else:
                        item["contextual_observation"] = f"Observation for item {item_no} was not returned in the bulk response."
                        logging.warning(f"Missing observation for item {item_no} in subdomain {subdomain}.")
                    
                    if "scoring_criteria" in item:
                        del item["scoring_criteria"]
                    if "caregiver_question" in item:
                        del item["caregiver_question"]
                    if "completion_metrics" in item:
                        del item["completion_metrics"]
            else:
                logging.error(f"Bulk observation generation failed for {subdomain}. No observations were added.")

    except KeyError:
        logging.warning(f"Warning: Subdomain '{subdomain}' not found in the expected data structure.")

    logging.info(f"Finished processing {subdomain}.")
    state["current_subdomain_index"] += 1
    return state

def save_data(state: GraphState) -> GraphState:
    """Saves the enriched cognitive and motor data to the output JSON file."""
    output_file = state['output_file']
    logging.info(f"Saving enriched Bayley cognitive and motor data to {output_file}...")
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    data_to_save = state["report_data"].get("bayley", {}).get("cognitive_and_motor", {})


        
    with open(output_file, 'w') as f:
        json.dump(data_to_save, f, indent=4)
    logging.info(f"Data saved successfully to {output_file}.")
    return state

def should_continue(state: GraphState) -> str:
    """Determines whether to continue processing subdomains or to finish."""
    if state["current_subdomain_index"] < len(state["subdomains_to_process"]):
        return "continue"
    else:
        return "end"


def main():
    """Main function to set up and run the LangGraph workflow."""
    parser = argparse.ArgumentParser(description="Generate detailed contextual observations for Bayley-4 data using an OpenAI agent.")
    parser.add_argument("input_file", help="Path to the input JSON file.")
    parser.add_argument("output_file", help="Path for the output JSON file.")
    args = parser.parse_args()

    if not client:
        logging.error("Exiting: OpenAI client could not be initialized. Please ensure OPENAI_API_KEY is set.")
        return

    workflow = StateGraph(GraphState)
    workflow.add_node("load_data", load_data)
    workflow.add_node("process_subdomain", process_subdomain)
    workflow.add_node("save_data", save_data)
    
    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "process_subdomain")
    workflow.add_conditional_edges(
        "process_subdomain",
        should_continue,
        {"continue": "process_subdomain", "end": "save_data"}
    )
    workflow.add_edge("save_data", END)

    app = workflow.compile()
    subdomains = ["cognitive", "receptive_communication", "expressive_communication", "fine_motor", "gross_motor"]
    
    initial_state = {
        "input_file": args.input_file,
        "output_file": args.output_file,
        "report_data": {},
        "subdomains_to_process": subdomains,
        "current_subdomain_index": 0,
    }

    final_state = app.invoke(initial_state)
    cognitive_and_motor = final_state["report_data"].get("bayley", {}).get("cognitive_and_motor", {})
    return cognitive_and_motor


def main():
    """Main function to set up and run the LangGraph workflow."""
    parser = argparse.ArgumentParser(description="Generate detailed contextual observations for Bayley-4 data using an OpenAI agent.")
    parser.add_argument("input_file", help="Path to the input JSON file.")
    parser.add_argument("output_file", help="Path for the output JSON file.")
    args = parser.parse_args()

    if not client:
        logging.error("Exiting: OpenAI client could not be initialized. Please ensure OPENAI_API_KEY is set.")
        return

    workflow = StateGraph(GraphState)
    workflow.add_node("load_data", load_data)
    workflow.add_node("process_subdomain", process_subdomain)
    workflow.add_node("save_data", save_data)
    
    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "process_subdomain")
    workflow.add_conditional_edges(
        "process_subdomain",
        should_continue,
        {"continue": "process_subdomain", "end": "save_data"}
    )
    workflow.add_edge("save_data", END)

    app = workflow.compile()
    subdomains = ["cognitive", "receptive_communication", "expressive_communication", "fine_motor", "gross_motor"]
    
    initial_state = {
        "input_file": args.input_file,
        "output_file": args.output_file,
        "report_data": {},
        "subdomains_to_process": subdomains,
        "current_subdomain_index": 0,
    }

    app.invoke(initial_state)

if __name__ == "__main__":
    main() 