

from langgraph.graph import START, StateGraph, END
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
import json
import re

from backend.prompts import remove_lang_tags

# Shared state keys
STATE_KEYS = ["prompt", "output", "valid"]

# Initialize the LLM
llm = init_chat_model(f"openai:gpt-4o")

# Prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a professional pediatric occupational therapist writing clinical evaluation reports. Use sophisticated clinical terminology, evidence-based interpretations, and maintain a professional, objective tone. Base your responses on standard pediatric developmental assessments and best practices in occupational therapy."),
    ("user", "{prompt}")
])

# LLM invocation node
def generate_response(state):
    prompt = state["prompt"]
    messages = prompt_template.format_messages(prompt=prompt)
    response = llm(messages)
    return {
        "prompt": prompt,
        "output": response.content,
        "valid": None  # to be set by validation node
    }

# Validation node
def validate_json(state):
    output = state["output"]
    print("######## validate_json #############", output)
    if output.startswith("```"):
        output = output.replace("```json", "").replace("```", "")
    try:
        parsed = json.loads(output)
        # Optional: strict schema validation
        if "summary" in parsed and isinstance(parsed["keywords"], list):
            return {**state, "valid": True}
    except json.JSONDecodeError:
        pass
    return {**state, "valid": False}

# Router to determine next step
def route_by_validation(state):
    return "generate_response" if state["valid"] else END

# Build the LangGraph
builder = StateGraph(state_schema=dict)  # Use simple dict for flexible state
builder.add_node("generate_response", generate_response)
builder.add_node("validate_json", validate_json)

builder.add_edge(START, "generate_response")
builder.add_edge("generate_response", "validate_json")
builder.add_conditional_edges("validate_json", route_by_validation)

graph = builder.compile()

def graph_invoke(prompt: str):
    final_state = graph.invoke({"prompt": prompt})
    return final_state

