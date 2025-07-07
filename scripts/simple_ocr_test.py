#!/usr/bin/env python3
"""
Simple OCR Test Script

Basic usage example of SimpleOCRAgent
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
from sconfig import config

from backend.langgraph.ocr_agent import SimpleOCRAgent


async def test_ocr():
    """Simple OCR test"""
    
    # Initialize agent
    agent = SimpleOCRAgent()
    
    # Image path (change this to your image file)
    image_path = "/home/lap-49/Documents/ot-report/scripts/outputs/ocr_results/images/page_2_img_0.jpeg"
    
    # Extract text
    result = await agent.extract_text_from_image(image_path)
    
    # Print results
    if result["success"]:
        print("✅ Success!")
        print(f"Extracted text: {result['extracted_text']}")
    else:
        print(f"❌ Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_ocr()) 