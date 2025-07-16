import json
import logging
import os
import re
import time
from typing import Any, Dict, List, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model as openai_init_chat_model
from langgraph.graph import END, StateGraph

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TranslationState(TypedDict):
    """Represents the state of our graph."""
    llm: ChatOpenAI
    original_data: Dict[str, Any]
    report_json_str: str
    final_output: Dict[str, Any]
    error_message: str


def init_chat_model(state: TranslationState) -> Dict[str, Any]:
    """Initialize the ChatOpenAI model."""
    logger.info("=== Initializing Chat Model ===")
    return {"llm": openai_init_chat_model("openai:gpt-4o")}
    # return {"llm": ChatOpenAI(model="gpt-4o", temperature=0.7)}


def prepare_data_for_translation(state: TranslationState) -> Dict[str, Any]:
    """Load data and prepare it for translation."""
    logger.info("=== Preparing Data for Translation ===")
    input_file = 'outputs/aws_chomps_observation_data_cleaned.json'
    
    with open(input_file, 'r') as f:
        data = json.load(f)

    report_json_str = json.dumps(data, indent=4)
    
    return {
        "original_data": data,
        "report_json_str": report_json_str,
    }


def report_translation(state: TranslationState) -> Dict[str, Any]:
    """Translates observation scores to clinical context using an LLM."""
    logger.info("=== Starting report translation ===")
    try:
        report_json = state['original_data']
        llm = state['llm']
        logger.info(f"Report JSON length: {len(state['report_json_str'])} characters")

        observation_category_data = report_json['observationsByCategory']
        for cat_name, observations in observation_category_data.items():

            prompt = f"""
            You are an expert pediatric occupational therapist interpreting individual ChOMPS assessment items.

            Your task is to read the provided JSON data, which contains patient information and categorized observations. For each observation within `observationsByCategory`, you must add a new key-value pair: `"context": "<your_interpretation>"`.

            Generate a 1–3 sentence clinical interpretation for each observation based on its score. This interpretation should explain what the score says about the child's current skill level.

            Use the following scoring criteria for your interpretation:
            - 2 = YES: Skill is mastered and performed independently
            - 1 = SOMETIMES: Skill is emerging, inconsistent, or performed with difficulty
            - 0 = NOT YET: Skill is not yet developed or attempted

            ---

            🧠 INSTRUCTIONS:
            - Modify the JSON by adding the "context" field to each observation object.
            - The value of "context" should be your clinical interpretation.
            - Use clinical but accessible language.
            - Avoid repeating the item description verbatim in your interpretation.
            - Focus on the functional interpretation of the skill.
            - Reference observed difficulties or strengths based on the score.
            - Frame statements from a third-person professional point of view ("The child...").
            - **IMPORTANT**: Return the complete, modified JSON object. The structure must be identical to the input, with only the `context` key added to each observation.

            ---

            💡 EXAMPLE:

            Input Snippet:
            {{
                "observation": "13. use a filled spoon or fork to bring food to mouth",
                "response": "Yes",
                "score": 2
            }}

            Output Snippet with added context:
            {{
                "observation": "13. use a filled spoon or fork to bring food to mouth",
                "response": "Yes",
                "score": 2,
                "context": "The child consistently demonstrates the ability to self-feed using utensils, indicating age-appropriate fine motor coordination and independent feeding skills."
            }}
            
            ---

            IMPORTANT:
            - Only return a valid JSON object as the response. Do not include any other text, descriptions, or markdown formatting like ```json.
            - The output JSON structure MUST exactly match the input structure.
            
            >>> JSON CONTENT FOR INTERPRETATION
            {observations}
            <<<
            """

            logger.info("Sending translation prompt to LLM...")
            result = llm.invoke(prompt)
            
            logger.info("Received translation response from LLM")
            output = result.content.strip()
            
            print(output)
            
            # Clean up potential markdown
            if output.startswith("```json"):
                output = output[7:]
            if output.endswith("```"):
                output = output[:-3]
            output = output.strip()

            logger.info(f"Translation output length: {len(output)} characters")
            
            try:
                logger.info("Attempting to parse translation output as JSON...")
                final_output = json.loads(output)
                logger.info("Successfully parsed translation output.")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in report translation: {str(e)}")
                return {"error_message": f"Failed to parse LLM response: {e}"}

            observation_category_data[cat_name] = final_output

            time.sleep(0.1)
        report_json['observationsByCategory'] = observation_category_data

        return {"final_output": report_json, "error_message": None}

    except Exception as e:
        logger.error(f"Error in report translation: {str(e)}")
        return {"error_message": f"An unexpected error occurred: {e}"}


def save_output(state: TranslationState):
    """Save the final output to a file."""
    logger.info("=== Saving Final Output ===")
    output_data = state['final_output']
    output_file = 'outputs/aws_chomps_observation_data_with_context.json'
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    logger.info(f"Successfully saved output to {output_file}")
    return {}


def handle_error(state: TranslationState) -> Dict[str, Any]:
    """Handles errors in the graph."""
    logger.error(f"An error occurred: {state['error_message']}")
    return {}


def should_continue(state: TranslationState):
    """Determines whether to continue or handle an error."""
    if state.get("error_message"):
        logger.warning("Error detected, routing to error handler.")
        return "error"
    logger.info("No errors detected, continuing.")
    return "continue"


def main():
    """Main function to run the translation graph."""
    workflow = StateGraph(TranslationState)

    workflow.add_node("init_model", init_chat_model)
    workflow.add_node("prepare_data", prepare_data_for_translation)
    workflow.add_node("translate", report_translation)
    workflow.add_node("save", save_output)
    workflow.add_node("error_handler", handle_error)

    workflow.set_entry_point("init_model")
    workflow.add_edge("init_model", "prepare_data")
    workflow.add_edge("prepare_data", "translate")
    
    workflow.add_conditional_edges(
        "translate",
        should_continue,
        {
            "continue": "save",
            "error": "error_handler",
        },
    )
    workflow.add_edge("save", END)
    workflow.add_edge("error_handler", END)

    app = workflow.compile()

    # Run the graph
    logger.info("Starting translation process...")
    # No initial inputs needed for this self-contained script
    for output in app.stream({}):
        for key, value in output.items():
            logger.info(f"Finished node '{key}'")
    logger.info("Translation process finished.")


if __name__ == "__main__":
    main()
