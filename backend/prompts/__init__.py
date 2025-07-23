import json
import os
from typing import Literal, Dict, Any
import re

from backend.prompts.pedieat_prompts import (
    get_pedieat_prompt
)
from backend.prompts.chomps_prompts import (
    get_chomps_prompt
)
from config import config

from .background_prompts import get_background_prompt
from .bayley4_prompts import get_bayley4_prompt
from .bayley4_social_and_adaptive_prompts import get_bayley4_social_adaptive_prompt
from .caregiver_concerns_prompts import get_caregiver_concerns_prompt
from .clinical_observations_prompts import get_clinical_observations_prompt
from .ot_goals_prompts import get_ot_goals_prompt
from .professional_summary_prompts import get_professional_summary_prompt
from .recommendations_prompts import get_recommendations_prompt
from .sp2_prompts import get_sp2_prompt

PromptType = Literal[
    'chomps', 
    'pedieat', 
    'background', 
    'caregiver_concerns', 
    'clinical_observations', 
    'professional_summary', 
    'recommendations', 
    'ot_goals', 
    'bayley4'
]

PromptDict = {
    "background": get_background_prompt,
    "bayley4": get_bayley4_prompt,
    "bayley4-social-and-adaptive": get_bayley4_social_adaptive_prompt,
    "caregiver_concerns": get_caregiver_concerns_prompt,
    'chomps': get_chomps_prompt,
    "clinical_observations": get_clinical_observations_prompt,
    "ot_goals": get_ot_goals_prompt,
    'pedieat': get_pedieat_prompt,
    "professional_summary": get_professional_summary_prompt,
    "recommendations": get_recommendations_prompt,
    "sp2": get_sp2_prompt,
}


def remove_lang_tags(text: str) -> str:
    """Remove language tags and clean text from AI responses."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove backticks and language specifiers
    text = re.sub(r'```[\w]*\n?', '', text)
    text = re.sub(r'```', '', text)
    
    # Remove JSON code block markers
    text = re.sub(r'^json\s*', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = text.strip()
    
    return text


async def get_prompt(prompt_type: str, report_data: Dict[str, Any], json_format: bool = True, **kwargs) -> str:
    """
    Get the appropriate prompt for the given type.
    
    Args:
        prompt_type: Type of prompt to generate
        report_data: Report data dictionary
        json_format: Whether to return JSON format
        **kwargs: Additional arguments for specific prompts
    
    Returns:
        Formatted prompt string
    """
    
    # prompt_functions = {
    #     'bayley4': get_bayley4_prompt,
    #     "bayley4-social-and-adaptive": get_bayley4_social_adaptive_prompt,
    #     'background': get_background_prompt,
    #     'caregiver_concerns': get_caregiver_concerns_prompt,
    #     'chomps': get_chomps_prompt,
    #     'clinical_observations': get_clinical_observations_prompt,
    #     'ot_goals': get_ot_goals_prompt,
    #     'pedieat': get_pedieat_prompt,
    #     'professional_summary': get_professional_summary_prompt,
    #     'recommendations': get_recommendations_prompt,
    #     'sp2': get_sp2_prompt,
    # }
    
    if prompt_type not in PromptDict:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    prompt_function = PromptDict[prompt_type]
    
    # Handle special cases for prompts that need different parameters
    if prompt_type in ['chomps', 'pedieat']:
        # These prompts need analysis data passed as first parameter
        # analysis_data = kwargs.get('analysis_data', '')
        return await prompt_function(report_data, json_format=json_format)
    else:
        # Standard prompts that take report_data
        return await prompt_function(report_data, json_format=json_format)


async def save_response(data: str, /, *,file_name: PromptType, json_format: bool = False):
    """
    Save the response to a file. Data must be json parsed.
    Args:
        data: The data to save.
        file_name: The name of the file to save.
        json_format: Whether to save the prompt in JSON format.
    Returns:
        None
    """
    if json_format:
        file_name = os.path.join(config.get_ai_save_response_dir(), f"{file_name}_response.json")
        with open(file_name, 'w') as f:
            f.write(json.dumps(data, indent=4))
    else:
        file_name = os.path.join(config.get_ai_save_response_dir(), f"{file_name}_response.txt")
        with open(file_name, 'w') as f:
            f.write(json.dumps(data))


async def save_prompt(data: str, /, *, file_name: PromptType, json_format: bool = False):
    """
    Save the response to a file. Data must be json parsed.
    Args:
        data: The data to save.
        file_name: The name of the file to save.
        json_format: Whether to save the prompt in JSON format.
    Returns:
        None
    """
    file_name = os.path.join(config.get_ai_save_prompt_dir(), f"{file_name}_response.txt")
    with open(file_name, 'w') as f:
        f.write(data)


# Export all functions for direct use if needed
__all__ = [
    'get_prompt',
    'remove_lang_tags',
    'get_background_prompt',
    'get_caregiver_concerns_prompt', 
    'get_clinical_observations_prompt',
    'get_professional_summary_prompt',
    'get_recommendations_prompt',
    'get_ot_goals_prompt',
    'get_bayley4_prompt',
    "get_bayley4_social_adaptive_prompt",
    'get_sp2_prompt',
    'get_chomps_prompt',
    'get_pedieat_prompt',
]