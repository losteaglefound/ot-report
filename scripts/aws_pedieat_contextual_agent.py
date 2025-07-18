#!/usr/bin/env python3
"""
AWS Pedi-EAT Contextual Interpretation Agent

This script takes the extracted Pedi-EAT observations JSON and adds contextual
clinical interpretations using OpenAI GPT-4o through LangGraph.

The agent analyzes each observation and provides clinical context based on:
- The observation description
- The scoring mechanism (asc_scoring vs desc_scoring)
- The score value and string representation
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, List, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor

# Load environment variables
assert load_dotenv()


# ==============================================================================
# SECTION 1: Data Types and Schemas
# ==============================================================================

class ObservationWithContext(TypedDict):
    description: str
    score: str
    score_string: str
    contextual_information: str

class ScoringDataWithContext(TypedDict):
    observations: List[ObservationWithContext]
    score: str

class ObservationCategoryWithContext(TypedDict):
    asc_scoring: ScoringDataWithContext
    desc_scoring: ScoringDataWithContext

class GraphState(TypedDict):
    """State of the LangGraph workflow"""
    input_data: Dict[str, Any]
    current_category: str
    current_scoring_type: str
    current_observation: Dict[str, Any]
    processed_data: Dict[str, Any]
    error: str


# ==============================================================================
# SECTION 2: Clinical Context Generator
# ==============================================================================

class ClinicalContextGenerator:
    """Generates clinical contextual interpretations for Pedi-EAT observations"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize the clinical context generator with OpenAI model"""
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,  # Lower temperature for more consistent clinical interpretations
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'contextual_agent.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_contextual_interpretation(
        self,
        observation: Dict[str, Any],
        category: str,
        scoring_type: str
    ) -> str:
        """Generate clinical contextual interpretation for an observation"""
        
        # Determine scoring mechanism explanation
        scoring_explanation = (
            "Higher scores indicate greater frequency/severity of concerning behaviors"
            if scoring_type == "asc_scoring"
            else "Higher scores indicate higher concern regarding child growth and development"
        )
        
        # Create the prompt for clinical interpretation
        prompt = f"""
As a pediatric feeding specialist, provide a brief clinical interpretation for the following observation:

Observation: "{observation['description']}"
Score: {observation['score']} out of 5 ({observation['score_string']})
Category: {category.replace('_', ' ').title()}
Scoring Type: {scoring_type.replace('_', ' ').title()}

Scoring Context: {scoring_explanation}

Please provide a concise clinical interpretation (2-3 sentences) that:
1. Explains what this score means clinically
2. Indicates the level of concern or positive functioning
3. Uses professional, clinical language appropriate for healthcare documentation

Response should be direct and clinical, without introductory phrases.
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            self.logger.error(f"Error generating context for observation: {e}")
            return f"Clinical interpretation unavailable due to processing error."


# ==============================================================================
# SECTION 3: LangGraph Workflow
# ==============================================================================

def create_contextual_graph() -> StateGraph:
    """Create the LangGraph workflow for adding contextual interpretations"""
    
    # Initialize the context generator
    context_generator = ClinicalContextGenerator()
    
    def initialize_processing(state: GraphState) -> GraphState:
        """Initialize the processing workflow"""
        logging.info("🔄 Initializing contextual interpretation workflow")
        
        # Create a deep copy of the input data for processing
        processed_data = json.loads(json.dumps(state["input_data"]))
        
        return {
            **state,
            "processed_data": processed_data,
            "error": ""
        }
    
    def process_observations(state: GraphState) -> GraphState:
        """Process all observations and add contextual interpretations"""
        logging.info("🧠 Generating contextual interpretations for all observations")
        
        processed_data = state["processed_data"]
        
        try:
            # Process each category
            for category_name, category_data in processed_data.items():
                logging.info(f"📋 Processing category: {category_name}")
                
                # Process both scoring types
                for scoring_type in ["asc_scoring", "desc_scoring"]:
                    observations = category_data[scoring_type]["observations"]
                    
                    logging.info(f"🔍 Processing {len(observations)} observations for {scoring_type}")
                    
                    # Add contextual information to each observation
                    for observation in observations:
                        context = context_generator.generate_contextual_interpretation(
                            observation, category_name, scoring_type
                        )
                        observation["contextual_information"] = context
                        
                        logging.info(f"✅ Added context for: {observation['description'][:50]}...")
            
            return {
                **state,
                "processed_data": processed_data
            }
            
        except Exception as e:
            logging.error(f"Error processing observations: {e}")
            return {
                **state,
                "error": str(e)
            }
    
    def finalize_processing(state: GraphState) -> GraphState:
        """Finalize the processing and prepare output"""
        logging.info("🎯 Finalizing contextual interpretation workflow")
        
        if state.get("error"):
            logging.error(f"Workflow completed with error: {state['error']}")
        else:
            logging.info("✅ Contextual interpretation workflow completed successfully")
        
        return state
    
    # Create the workflow graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_processing)
    workflow.add_node("process_observations", process_observations)
    workflow.add_node("finalize", finalize_processing)
    
    # Define the workflow edges
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "process_observations")
    workflow.add_edge("process_observations", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


# ==============================================================================
# SECTION 4: Main Execution
# ==============================================================================

def load_pedieat_data(file_path: str) -> Dict[str, Any]:
    """Load the Pedi-EAT observation data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logging.info(f"📄 Successfully loaded data from: {file_path}")
        return data
    except Exception as e:
        logging.error(f"Error loading data from {file_path}: {e}")
        raise


def save_contextual_data(data: Dict[str, Any], output_path: str):
    """Save the processed data with contextual interpretations"""
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"💾 Successfully saved contextual data to: {output_path}")
    except Exception as e:
        logging.error(f"Error saving data to {output_path}: {e}")
        raise


def main():
    """Main function to run the contextual interpretation agent"""
    parser = argparse.ArgumentParser(
        description='Add contextual clinical interpretations to Pedi-EAT observations'
    )
    parser.add_argument(
        '--input-file',
        default='outputs/aws_pedieat_extract.json',
        help='Path to the input JSON file with extracted observations'
    )
    parser.add_argument(
        '--output-file',
        default='outputs/aws_pedieat_contextual.json',
        help='Path to save the output with contextual interpretations'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    # Verify OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)
    
    try:
        # Load the input data
        input_data = load_pedieat_data(args.input_file)
        
        # Create and run the contextual interpretation workflow
        workflow = create_contextual_graph()
        
        # Execute the workflow
        logging.info("🚀 Starting contextual interpretation workflow")
        result = workflow.invoke({
            "input_data": input_data,
            "current_category": "",
            "current_scoring_type": "",
            "current_observation": {},
            "processed_data": {},
            "error": ""
        })
        
        # Check for errors
        if result.get("error"):
            print(f"❌ Workflow failed with error: {result['error']}")
            sys.exit(1)
        
        # Save the results
        save_contextual_data(result["processed_data"], args.output_file)
        
        print(f"🎉 Contextual interpretation complete!")
        print(f"📄 Input file: {args.input_file}")
        print(f"💾 Output file: {args.output_file}")
        
        # Print summary statistics
        total_observations = 0
        for category_data in result["processed_data"].values():
            for scoring_data in category_data.values():
                total_observations += len(scoring_data["observations"])
        
        print(f"🧠 Added contextual interpretations to {total_observations} observations")
        
    except Exception as e:
        logging.exception("An error occurred during contextual interpretation")
        print(f"❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 