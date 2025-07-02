import os
from pathlib import Path
import sys


BASE_DIR = Path(__name__).resolve().parent.parent
sys.path.append(BASE_DIR.__str__())


try:
    from backend.common.logging import logging
    from backend.langgraph.graph import ChatBot
except Exception as e:
    raise RuntimeError("Unable to import library backend") from e


logger = logging.getLogger(__name__)
logging.FileHandler(os.path.join())