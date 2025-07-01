import json
import os
from typing import Literal

from backend.prompts.pedieat_prompts import (
    get_pedieat_prompt
)
from backend.prompts.chomps_prompts import (
    get_chomps_prompt
)
from config import config



PromptType = Literal['chomps', 'pedieat']

PromptDict = {

    'chomps': get_chomps_prompt,
    'pedieat': get_pedieat_prompt,
}


async def get_prompt(*, prompt_type: PromptType, data: str, json_format: bool = False) -> str:
    """
    Get the prompt for the given prompt type.
    """
    return await PromptDict[prompt_type](data, json_format)


async def save_response(data: str , /, *,file_name: PromptType, json_format: bool = False):
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
        prompt = await PromptDict[file_name](data, json_format)
        file_name = os.path.join(config.get_ai_save_response_dir(), f"{file_name}_response.json")
        with open(file_name, 'w') as f:
            f.write(json.dumps(data, indent=4))
    else:
        prompt = await PromptDict[file_name](data)
        file_name = os.path.join(config.get_ai_save_response_dir(), f"{file_name}_response.txt")
        with open(file_name, 'w') as f:
            f.write(prompt)


async def remove_lang_tags(data: str) -> str:
    """
    Remove the language tags from the data.
    Args:
        data: The data to remove the language tags from.
    Returns:
        The data with the language tags removed.
    """
    return data.replace("```json", "").replace("```", "")