import sys
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Add the backend directory to Python path to import the chomps agent
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .chomps_data_extract_agent import extract_chomps_data

logger = logging.getLogger(__name__)


def extract_chomps_data_wrapper(pdf_path: str) -> Dict[str, Any]:
    """
    Extract CHOMPS data from PDF file.
    
    Args:
        pdf_path: Path to the CHOMPS PDF file
        
    Returns:
        dict: Extracted CHOMPS data in JSON format
    """
    try:
        logger.info(f"🧠 Extracting CHOMPS data from: {pdf_path}")
        
        # Use the existing CHOMPS data extraction agent
        result = extract_chomps_data(pdf_path)
        
        if result.get("success"):
            logger.info("✅ CHOMPS data extracted successfully")
            return {
                "success": True,
                "chomps_data": result.get("data", {}),
                "error": None
            }
        else:
            logger.error(f"❌ CHOMPS extraction failed: {result.get('error')}")
            return {
                "success": False,
                "chomps_data": None,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"❌ Error in CHOMPS extraction: {str(e)}")
        return {
            "success": False,
            "chomps_data": None,
            "error": str(e)
        } 