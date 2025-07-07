#!/usr/bin/env python3
"""
Debug script for OCR Agent to identify specific issues
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from backend.langgraph.ocr_agent import LangGraphOCRAgent
import fitz  # PyMuPDF

async def test_ocr_agent():
    """Test OCR agent with a single image"""
    
    # Test with the image-based PDF
    pdf_path = "assets/inputs/images/Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"Test file not found: {pdf_path}")
        return
    
    try:
        # Initialize OCR agent
        logger.info("🤖 Initializing OCR Agent...")
        ocr_agent = LangGraphOCRAgent()
        
        # Extract first page as image
        logger.info("🖼️ Extracting first page as image...")
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # First page
        
        # Convert page to image
        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        image_bytes = pix.tobytes("jpeg")
        
        logger.info(f"📄 Image extracted: {len(image_bytes)} bytes")
        
        doc.close()
        
        # Test OCR processing
        logger.info("🚀 Starting OCR processing...")
        
        result = await ocr_agent.process_image(
            image_data=image_bytes,
            document_type="medical_assessment",
            page_number=1
        )
        
        # Display results
        logger.info("📊 OCR Results:")
        logger.info(f"  Processing complete: {result.get('processing_complete', False)}")
        logger.info(f"  Quality score: {result.get('quality_score', 0)}")
        logger.info(f"  Confidence: {result.get('confidence_level', 'unknown')}")
        logger.info(f"  Text length: {len(result.get('extracted_text', ''))}")
        logger.info(f"  Errors: {len(result.get('processing_errors', []))}")
        
        if result.get('processing_errors'):
            logger.error("❌ Processing errors:")
            for error in result.get('processing_errors', []):
                logger.error(f"  - {error}")
        
        extracted_text = result.get('extracted_text', '')
        if extracted_text:
            preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
            logger.info(f"📝 Extracted text preview:\n{preview}")
        else:
            logger.warning("⚠️ No text extracted")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ocr_agent()) 