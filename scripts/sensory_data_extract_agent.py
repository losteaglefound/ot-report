import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Load API key from .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Define the state schema
class GraphState(TypedDict):
    pdf_path: str
    report_text: str
    parsed_json: str

# ---------------------- Step 1: Text Extraction Node ----------------------
def extract_text_node(state):
    pdf_path = state["pdf_path"]
    doc = fitz.open(pdf_path)
    full_text = "".join([page.get_text() for page in doc])
    doc.close()
    return {**state, "report_text": full_text}

# ---------------------- Step 2: LLM JSON Parsing Node ----------------------
EXTRACTION_PROMPT = """
You are an expert pediatric occupational therapist analyzing a Toddler Sensory Profile™ 2 Summary Report.

Extract the following information and return as VALID JSON with EXACT structure:

{{
  "scoring_criteria": {{
    "AA": 5, "F": 4, "H": 3, "O": 2, "AN": 1, "DNA": 0
  }},
  "processing": {{
    "GENERAL": {{ "items": [], "raw_score": null }},
    "AUDITORY": {{ "items": [], "raw_score": null }},
    "VISUAL": {{ "items": [], "raw_score": null }},
    "TOUCH": {{ "items": [], "raw_score": null }},
    "MOVEMENT": {{ "items": [], "raw_score": null }},
    "ORAL_SENSORY": {{ "items": [], "raw_score": null }}
  }},
  "quadrant_score_summary": {{
    "Seeking/Seeker": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "Avoiding/Avoider": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "Sensitivity/Sensor": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "Registration/Bystander": {{ "raw_score": null, "percentile_range": null, "classification": null }}
  }},
  "sensory_and_behavioral_section_score_summary": {{
    "GENERAL Processing": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "AUDITORY Processing": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "VISUAL Processing": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "TOUCH Processing": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "MOVEMENT Processing": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "ORAL SENSORY Processing": {{ "raw_score": null, "percentile_range": null, "classification": null }},
    "BEHAVIORAL responses associated with sensory processing": {{ "raw_score": null, "percentile_range": null, "classification": null }}
  }}
}}

Only return the JSON. Do not explain or comment.

--- BEGIN REPORT TEXT ---
{report_text}
--- END REPORT TEXT ---
"""

def parse_json_node(state):
    prompt = EXTRACTION_PROMPT.format(report_text=state["report_text"])
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    response = llm([HumanMessage(content=prompt)])
    return {**state, "parsed_json": response.content}


def build_graph():
    # Create the StateGraph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("parse_json", parse_json_node)

    # Set entry point
    workflow.set_entry_point("extract_text")
    
    # Add edges
    workflow.add_edge("extract_text", "parse_json")
    workflow.add_edge("parse_json", END)

    # Compile the graph
    return workflow.compile()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to the Sensory Profile PDF report")
    args = parser.parse_args()

    # Build and invoke the graph
    graph = build_graph()
    result = graph.invoke({"pdf_path": args.pdf})
    print(result["parsed_json"])

if __name__ == "__main__":
    main()
