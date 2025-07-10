import sys
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Add the scripts directory to Python path to import the sensory agent
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from .sensory_data_extract_agent import extract_sensory_data

logger = logging.getLogger(__name__)


def extract_sp2_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract SP2 sensory data from PDF file.
    
    Args:
        pdf_path: Path to the SP2 PDF file
        
    Returns:
        dict: Extracted SP2 data in JSON format
    """
    try:
        logger.info(f"🧠 Extracting SP2 data from: {pdf_path}")
        
        # Use the existing sensory data extraction agent
        result = extract_sensory_data(pdf_path)
        
        if result.get("success"):
            logger.info("✅ SP2 data extracted successfully")
            return {
                "success": True,
                "sp2_data": result.get("data", {}),
                "error": None
            }
        else:
            logger.error(f"❌ SP2 extraction failed: {result.get('error')}")
            return {
                "success": False,
                "sp2_data": None,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"❌ Error in SP2 extraction: {str(e)}")
        return {
            "success": False,
            "sp2_data": None,
            "error": str(e)
        } 