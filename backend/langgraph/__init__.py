from langgraph.graph import START, StateGraph, END
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
import json
import re

from backend.prompts import remove_lang_tags

# Shared state keys
STATE_KEYS = ["prompt", "output", "valid", "json_required", "retry_count"]

# Initialize the LLM
llm = init_chat_model(f"openai:gpt-4o")

# Prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a professional pediatric occupational therapist writing clinical evaluation reports. Use sophisticated clinical terminology, evidence-based interpretations, and maintain a professional, objective tone. Base your responses on standard pediatric developmental assessments and best practices in occupational therapy. When JSON format is requested, ALWAYS return valid JSON that can be parsed directly."),
    ("human", "{prompt}")
])

def generate_response(state):
    """Generate response using the language model."""
    try:
        prompt = state.get("prompt", "")
        
        # Check if JSON format is required
        json_required = "json" in prompt.lower() and ("json response format" in prompt.lower() or "return the output as a valid json" in prompt.lower())
        
        # Add JSON enforcement if needed
        if json_required:
            prompt += "\n\nIMPORTANT: Return ONLY valid JSON that can be parsed directly. Do not include any text before or after the JSON object."
        
        # Generate response
        messages = prompt_template.format_messages(prompt=prompt)
        response = llm.invoke(messages)
        
        # Clean the response
        output = response.content.strip()
        output = remove_lang_tags(output)
        
        return {
            **state,
            "output": output,
            "json_required": json_required,
            "retry_count": state.get("retry_count", 0)
        }
    except Exception as e:
        print(f"Error in generate_response: {e}")
        return {
            **state,
            "output": f"Error generating response: {str(e)}",
            "json_required": False,
            "retry_count": state.get("retry_count", 0)
        }

def validate_json(state):
    """Validate JSON response if required."""
    output = state.get("output", "")
    json_required = state.get("json_required", False)
    retry_count = state.get("retry_count", 0)
    
    if not json_required:
        # Non-JSON prompts are always valid
        return {**state, "valid": True}
    
    try:
        # Try to parse as JSON
        json.loads(output)
        return {**state, "valid": True}
    except json.JSONDecodeError as e:
        print(f"JSON validation failed (attempt {retry_count + 1}): {e}")
        print(f"Response was: {output[:200]}...")
        
        # If we've tried too many times, accept the response as-is
        if retry_count >= 2:
            print("Max retries reached, accepting response")
            return {**state, "valid": True}
        
        # Try to fix common JSON issues
        fixed_output = _fix_common_json_issues(output)
        try:
            json.loads(fixed_output)
            print("Successfully fixed JSON issues")
            return {**state, "output": fixed_output, "valid": True}
        except:
            # Still invalid, mark for retry
            return {**state, "valid": False, "retry_count": retry_count + 1}

def _fix_common_json_issues(output: str) -> str:
    """Attempt to fix common JSON formatting issues."""
    # Remove any leading/trailing text that's not JSON
    output = output.strip()
    
    # Find JSON content between braces
    json_match = re.search(r'\{.*\}', output, re.DOTALL)
    if json_match:
        output = json_match.group(0)
    
    # Fix common issues
    output = output.replace("'", '"')  # Single to double quotes
    output = re.sub(r',\s*}', '}', output)  # Remove trailing commas
    output = re.sub(r',\s*]', ']', output)  # Remove trailing commas in arrays
    
    return output

def route_by_validation(state):
    """Route based on validation results."""
    is_valid = state.get("valid", False)
    retry_count = state.get("retry_count", 0)
    json_required = state.get("json_required", False)
    
    # Always end if:
    # 1. Response is valid
    # 2. Too many retries
    # 3. JSON not required
    if is_valid or retry_count >= 3 or not json_required:
        return END
    
    # Otherwise, retry generation
    return "generate_response"

# Build the LangGraph
builder = StateGraph(state_schema=dict)  # Use simple dict for flexible state
builder.add_node("generate_response", generate_response)
builder.add_node("validate_json", validate_json)

builder.add_edge(START, "generate_response")
builder.add_edge("generate_response", "validate_json")
builder.add_conditional_edges("validate_json", route_by_validation)

# Compile the graph
graph = builder.compile()

def graph_invoke(prompt: str):
    """
    Invoke the langraph agent with the given prompt.
    
    Args:
        prompt: The prompt to send to the agent
        
    Returns:
        str: The generated response
    """
    try:
        final_state = graph.invoke(
            {
                "prompt": prompt, 
                "retry_count": 0,
                "json_required": False,
                "valid": False,
                "output": ""
            }
        )
        
        return final_state.get("output", "")
        
    except Exception as e:
        print(f"Error in graph_invoke: {e}")
        return f"Error generating response: {str(e)}"

