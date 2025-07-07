#!/usr/bin/env python3
"""
Simple usage script for OCR Agent

This script demonstrates how to use the SimpleOCRAgent to extract text from images.
"""

import asyncio
import sys
import os
from pathlib import Path

from sconfig import config

# # Add the backend directory to the path
# backend_path = Path(__file__).parent.parent / "backend"
# sys.path.insert(0, str(backend_path))

from backend.langgraph.ocr_agent import SimpleOCRAgent


async def main():
    """Main function to test OCR agent"""
    
    # Initialize the OCR agent
    print("🤖 Initializing OCR Agent...")
    agent = SimpleOCRAgent()
    
    # Test image path - you can change this to your image file
    test_image_path = input("Enter path to image file (or press Enter for default): ").strip()
    
    if not test_image_path:
        # Look for sample images in the project
        possible_images = [
            "Bayley-4-Social-Emotional-and-Adaptive-Behavior-Scales-Score-Report_70360653_1751082312974.pdf",
            "Bayley-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf",
            "OT_Evaluation_Report_20250628.pdf"
        ]
        
        # Find first available image
        for img_path in possible_images:
            if Path(img_path).exists():
                test_image_path = img_path
                break
        
        if not test_image_path:
            print("❌ No test image found. Please provide a valid image path.")
            return
    
    # Check if file exists
    if not Path(test_image_path).exists():
        print(f"❌ Image file not found: {test_image_path}")
        return
    
    print(f"📷 Processing image: {test_image_path}")
    
    # Extract text from image
    try:
        result = await agent.extract_text_from_image(test_image_path)
        
        # Display results
        print("\n" + "="*50)
        print("📝 OCR RESULTS")
        print("="*50)
        
        if result["success"]:
            print(f"✅ Success: Text extracted successfully")
            print(f"📄 Text length: {len(result['extracted_text'])} characters")
            print(f"\n📋 Extracted Text:\n{'-'*30}")
            print(result["extracted_text"])
        else:
            print(f"❌ Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 