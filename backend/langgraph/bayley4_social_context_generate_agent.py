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
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    client = openai.OpenAI(api_key=api_key)
else:
    print("Warning: OPENAI_API_KEY not found in environment variables. AI-based context generation will be skipped.")


class GraphState(TypedDict):
    """Represents the state of our graph."""
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
    
    pronouns = ("they", "their", "them")
    if sex == "male":
        pronouns = ("he", "his", "him")
    elif sex == "female":
        pronouns = ("she", "her", "her")
        
    return name, pronouns

def generate_bulk_observations(patient_name: str, pronouns: Tuple[str, str, str], items: List[dict], subdomain_name: str) -> dict:
    """Generates detailed observations for a list of items in a single API call."""
    if not client:
        logging.warning("OpenAI client not initialized. Skipping AI-based context generation.")
        return {}

    subject_pronoun, possessive_pronoun, object_pronoun = pronouns

    items_for_prompt = [
        {
            "observation_no": item.get("observation_no"),
            "description": item.get("description"),
            "valid_answer": item.get("valid_answer"),
            "scoring_criteria": item.get("scoring_criteria"),
        }
        for item in items
    ]

    prompt = f"""
    You are an expert pediatric occupational therapist analyzing a Bayley-4 Social and Adaptive assessment for {patient_name}.

    **Child's Name:** {patient_name}
    **Child's Pronouns:** {subject_pronoun}/{possessive_pronoun}/{object_pronoun}
    **Assessment Subdomain:** {subdomain_name.replace('_', ' ').title()}

    **Assessment Items:**
    {json.dumps(items_for_prompt, indent=2)}

    **Your Task:**
    For EACH item in the list, write a detailed, narrative observation about {patient_name}'s performance.
    - Interpret each score using its scoring criteria.
    - Describe the likely behaviors {patient_name} exhibited.
    - Frame observations in a professional, clinical tone.

    **Output Format:**
    Return a single JSON object with one key: "observations". The value must be an array of objects, each with "observation_no" and "contextual_observation" keys.
    Example:
    {{
        "observations": [
          {{
            "observation_no": "1",
            "contextual_observation": "The detailed narrative for item 1."
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
        
        response_content = response.choices[0].message.content.replace("```json", "").replace("```", "")
        response_data = json.loads(response_content)
        
        observations_list = response_data.get("observations", [])
        
        if not observations_list:
            logging.error(f"Could not find an array of observations in the JSON response for subdomain '{subdomain_name}'.")
            return {}

        logging.info(f"Successfully generated bulk observations for subdomain: '{subdomain_name}'.")
        return {str(obs.get("observation_no")): obs.get("contextual_observation") for obs in observations_list}

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
        # with open(state['input_file'], 'r') as f:
            # state["report_data"] = json.load(f)
        data = state['input_file']
        state['report_data'] = data
        logging.info("Data loaded successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading data from {state['input_file']}: {e}")
        return
    return state

def process_subdomain(state: GraphState) -> GraphState:
    """Processes one subdomain, adding contextual observations and removing unwanted fields."""
    subdomain_index = state["current_subdomain_index"]
    subdomain_name = state["subdomains_to_process"][subdomain_index]
    logging.info(f"Processing subdomain: {subdomain_name}...")

    patient_name, pronouns = get_patient_info(state)
    
    try:
        subdomain_data = None
        if subdomain_name == "social_emotional":
            subdomain_data = state["report_data"]["bayley"]["social_and_adaptive"]["social_emotional"]["observations"]
        else:
            subdomain_data = state["report_data"]["bayley"]["social_and_adaptive"]["adaptive_behavior"]["subdomains"][subdomain_name]["observations"]
        
        if isinstance(subdomain_data, list) and subdomain_data:
            observations_map = generate_bulk_observations(patient_name, pronouns, subdomain_data, subdomain_name)

            if observations_map:
                for item in subdomain_data:
                    obs_no = str(item.get("observation_no"))
                    item["contextual_observation"] = observations_map.get(obs_no, f"Observation for item {obs_no} not returned.")
                    
                    for key in ["scoring_criteria", "scoring_tip", "caregiver_question", "completion_metrics"]:
                        if key in item:
                            del item[key]
            else:
                logging.error(f"Bulk observation generation failed for {subdomain_name}. No observations added.")

    except KeyError as e:
        logging.warning(f"Data path not found for subdomain '{subdomain_name}': {e}")

    logging.info(f"Finished processing {subdomain_name}.")
    state["current_subdomain_index"] += 1
    return state

def save_data(state: GraphState) -> GraphState:
    """Saves the enriched social and adaptive data to the output JSON file."""
    output_file = state['output_file']
    # logging.info(f"Saving enriched Bayley social and adaptive data to {output_file}...")
    # output_dir = os.path.dirname(output_file)
    # if output_dir:
    #     os.makedirs(output_dir, exist_ok=True)
    
    data_to_save = state["report_data"].get("bayley", {}).get("social_and_adaptive", {})
        
    # with open(output_file, 'w') as f:
    #     json.dump(data_to_save, f, indent=4)
    logging.info(f"Data saved successfully to {output_file}.")
    return state

def should_continue(state: GraphState) -> str:
    """Determines whether to continue processing subdomains or to finish."""
    return "end" if state["current_subdomain_index"] >= len(state["subdomains_to_process"]) else "continue"


def social_adaptive_context_agent(report_data):
    """Main function to set up and run the LangGraph workflow."""
    parser = argparse.ArgumentParser(description="Generate detailed contextual observations for Bayley-4 Social and Adaptive data.")
    # parser.add_argument("input_file", help="Path to the input JSON file.")
    # parser.add_argument("output_file", help="Path for the output JSON file.")
    # args = parser.parse_args()

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
    subdomains = ["social_emotional", "receptive", "expressive", "personal", "play_and_leisure"]
    
    initial_state = {
        "input_file": report_data,
        "output_file": "",
        "report_data": {},
        "subdomains_to_process": subdomains,
        "current_subdomain_index": 0,
    }

    final_state = app.invoke(initial_state)
    return  final_state["report_data"].get("bayley", {}).get("social_and_adaptive", {})


def main():
    """Main function to set up and run the LangGraph workflow."""
    parser = argparse.ArgumentParser(description="Generate detailed contextual observations for Bayley-4 Social and Adaptive data.")
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
    subdomains = ["social_emotional", "receptive", "expressive", "personal", "play_and_leisure"]
    
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