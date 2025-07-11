import sys
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Add the backend directory to Python path to import the pedieat agent
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .pedieat_data_extract_agent import extract_sensory_data

logger = logging.getLogger(__name__)


def extract_pedieat_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract PediEAT data from PDF file.
    
    Args:
        pdf_path: Path to the PediEAT PDF file
        
    Returns:
        dict: Extracted PediEAT data in JSON format
    """
    try:
        logger.info(f"🧠 Extracting PediEAT data from: {pdf_path}")
        
        # Use the existing pedieat data extraction agent
        result = extract_sensory_data(pdf_path)
        
        if result.get("success"):
            logger.info("✅ PediEAT data extracted successfully")
            return {
                "success": True,
                "pedieat_data": result.get("data", {}),
                "error": None
            }
        else:
            logger.error(f"❌ PediEAT extraction failed: {result.get('error')}")
            return {
                "success": False,
                "pedieat_data": None,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"❌ Error in PediEAT extraction: {str(e)}")
        return {
            "success": False,
            "pedieat_data": None,
            "error": str(e)
        } 