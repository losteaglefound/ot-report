import json
import os
from typing import Literal

from config import config

async def save_json_data(data: dict | str, filename: str, extension: Literal['txt', 'json', 'csv'] = "json") -> None:
    output_dir = os.path.join(config.PROJECT_DIR, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, filename) + f".{extension}"

    with open(filename, 'w+') as f:
        if isinstance(data, str):
            f.write(data)
        if isinstance(data, dict) or isinstance(data, list):
            json.dump(data, f, indent=4)