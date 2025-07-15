import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

sys.path.append(str(BASE_DIR))
sys.path.append(str(PROJECT_DIR))