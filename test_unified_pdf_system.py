#!/usr/bin/env python3
"""
Comprehensive test script for the unified PDF processing system.

This script demonstrates:
1. PDF type detection (text-based vs image-based)
2. Intelligent PDF processing using the appropriate method
3. OCR processing for image-based PDFs using LangGraph agent
4. Unified processing flow for different PDF types
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔄 Starting imports...")
from backend.utils import PDFDetector, UnifiedPDFProcessor
print("✅ Imports completed successfully")


class PDFProcessingTester:
    """Test class for the unified PDF processing system"""
    
    def __init__(self):
        print("🔧 Initializing PDFProcessingTester...")
        self.detector = PDFDetector()
        print("✅ PDFDetector initialized")
        self.processor = UnifiedPDFProcessor()
        print("✅ UnifiedPDFProcessor initialized")
        
    async def test_pdf_detection(self, pdf_path: str) -> Dict[str, Any]:
        """Test PDF detection functionality"""
        print(f"🔍 Starting PDF detection for: {os.path.basename(pdf_path)}")
        logger.info(f"🔍 Testing PDF detection for: {os.path.basename(pdf_path)}")
        
        try:
            # Full detection
            print("🔍 Running full detection...")
            detection_result = await self.detector.detect_pdf_type(pdf_path)
            print("✅ Full detection completed")
            
            # Quick check
            print("⚡ Running quick check...")
            quick_result = await self.detector.quick_check(pdf_path)
            print("✅ Quick check completed")
            
            return {
                "file_path": pdf_path,
                "detection_result": detection_result,
                "quick_result": quick_result
            }
            
        except Exception as e:
            print(f"❌ Detection failed: {e}")
            logger.error(f"❌ Detection failed: {e}")
            return {"error": str(e)}
    
    async def test_pdf_processing(self, pdf_path: str, force_ocr: bool = False) -> Dict[str, Any]:
        """Test PDF processing functionality"""
        print(f"📄 Starting PDF processing for: {os.path.basename(pdf_path)}")
        logger.info(f"📄 Testing PDF processing for: {os.path.basename(pdf_path)}")
        
        try:
            # Process the PDF
            print("🔧 Running PDF processing...")
            result = await self.processor.process_pdf(
                pdf_path, 
                force_ocr=force_ocr,
                document_type="medical_assessment"
            )
            print("✅ PDF processing completed")
            
            return result
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            logger.error(f"❌ Processing failed: {e}")
            return {"error": str(e)}
    
    def print_detection_results(self, results: Dict[str, Any]):
        """Print detection results in a formatted way"""
        print("\n" + "="*80)
        print("PDF DETECTION RESULTS")
        print("="*80)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        detection = results.get("detection_result", {})
        quick = results.get("quick_result", {})
        
        print(f"📄 File: {os.path.basename(results['file_path'])}")
        print(f"🔍 PDF Type: {detection.get('pdf_type', 'unknown')}")
        print(f"📊 Confidence: {detection.get('confidence', 0):.2f}")
        
        # Analysis summary
        analysis = detection.get("analysis", {})
        if analysis:
            text_analysis = analysis.get("text_analysis", {})
            image_analysis = analysis.get("image_analysis", {})
            
            print(f"📝 Text Analysis:")
            print(f"   - Total characters: {text_analysis.get('total_chars', 0)}")
            print(f"   - Avg chars per page: {text_analysis.get('avg_chars_per_page', 0):.0f}")
            print(f"   - Pages with text: {text_analysis.get('pages_with_text', 0)}")
            print(f"   - Total pages: {analysis.get('total_pages', 0)}")
            
            print(f"🖼️ Image Analysis:")
            print(f"   - Total images: {image_analysis.get('total_images', 0)}")
            print(f"   - Significant images: {image_analysis.get('significant_images', 0)}")
            print(f"   - Large images: {image_analysis.get('large_images', 0)}")
            print(f"   - Pages with images: {image_analysis.get('pages_with_images', 0)}")
        
        # Recommendation
        recommendation = detection.get("recommendation", {})
        if recommendation:
            print(f"💡 Recommendation:")
            print(f"   - Primary method: {recommendation.get('primary_method', 'unknown')}")
            print(f"   - Expected quality: {recommendation.get('expected_quality', 'unknown')}")
            print(f"   - Processing time: {recommendation.get('processing_time', 'unknown')}")
        
        # Quick check
        print(f"⚡ Quick Check:")
        print(f"   - Has images: {quick.get('has_images', False)}")
        print(f"   - Has extractable text: {quick.get('has_extractable_text', False)}")
        print(f"   - Quick type: {quick.get('quick_type', 'unknown')}")
        print(f"   - Total pages: {quick.get('total_pages', 0)}")
    
    def print_processing_results(self, results: Dict[str, Any]):
        """Print processing results in a formatted way"""
        print("\n" + "="*80)
        print("PDF PROCESSING RESULTS")
        print("="*80)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        print(f"📄 File: {results.get('file_name', 'unknown')}")
        print(f"🔍 Detected Type: {results.get('pdf_type', 'unknown')}")
        print(f"📊 Detection Confidence: {results.get('detection_confidence', 0):.2f}")
        print(f"🔧 Processing Method: {results.get('processing_method', 'unknown')}")
        print(f"⏱️ Processing Time: {results.get('processing_time_seconds', 0):.2f}s")
        print(f"✅ Processing Complete: {results.get('processing_complete', False)}")
        
        # Text extraction results
        extracted_text = results.get("extracted_text", "")
        print(f"📝 Extracted Text:")
        print(f"   - Total characters: {len(extracted_text)}")
        print(f"   - Has content: {'Yes' if extracted_text.strip() else 'No'}")
        
        # Quality score
        quality_score = results.get("quality_score", 0)
        print(f"📊 Quality Score: {quality_score:.2f}")
        
        # Processing errors
        errors = results.get("processing_errors", [])
        if errors:
            print(f"⚠️ Processing Errors ({len(errors)}):")
            for i, error in enumerate(errors[:5]):  # Show first 5 errors
                print(f"   {i+1}. {error}")
        
        # Processing details
        details = results.get("processing_details", {})
        if details:
            print(f"🔧 Processing Details:")
            for key, value in details.items():
                print(f"   - {key}: {value}")
        
        # Preview of extracted text
        if extracted_text:
            preview = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
            print(f"👁️ Text Preview:")
            print(f"   {preview}")
        
        print("-" * 80)


async def main():
    """Main test function"""
    print("🚀 Starting main function...")
    logger.info("🚀 Starting comprehensive PDF processing tests...")
    
    # Initialize tester
    print("🔧 Initializing tester...")
    tester = PDFProcessingTester()
    print("✅ Tester initialized")
    
    # Test files as specified by user
    test_files = {
        "image_pdf": "assets/inputs/images/Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf",
        "text_pdf": "Bayley-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"
    }
    
    # Verify files exist
    print("🔍 Verifying test files exist...")
    existing_files = {}
    for file_type, file_path in test_files.items():
        if os.path.exists(file_path):
            existing_files[file_type] = file_path
            logger.info(f"✅ Found {file_type}: {os.path.basename(file_path)}")
        else:
            logger.warning(f"⚠️ Missing {file_type}: {file_path}")
    
    if not existing_files:
        logger.error("❌ No test files found!")
        return
    
    print(f"\n🎯 Testing with {len(existing_files)} files:")
    for file_type, file_path in existing_files.items():
        print(f"   - {file_type}: {os.path.basename(file_path)}")
    
    # Test 1: PDF Detection for both files
    print("\n" + "="*80)
    print("🔍 TESTING PDF DETECTION")
    print("="*80)
    
    detection_results = {}
    for file_type, file_path in existing_files.items():
        print(f"\n📋 Testing {file_type.upper()}:")
        print(f"📄 Starting detection for: {file_path}")
        detection_results[file_type] = await tester.test_pdf_detection(file_path)
        print(f"✅ Detection completed for: {file_type}")
        tester.print_detection_results(detection_results[file_type])
    
    # Test 2: PDF Processing for both files
    print("\n" + "="*80)
    print("📄 TESTING PDF PROCESSING")
    print("="*80)
    
    processing_results = {}
    for file_type, file_path in existing_files.items():
        print(f"\n📋 Processing {file_type.upper()}:")
        print(f"📄 Starting processing for: {file_path}")
        processing_results[file_type] = await tester.test_pdf_processing(file_path)
        print(f"✅ Processing completed for: {file_type}")
        tester.print_processing_results(processing_results[file_type])
    
    # Test 3: Force OCR on text-based PDF to compare
    if "text_pdf" in existing_files:
        print("\n" + "="*80)
        print("🔧 TESTING FORCE OCR ON TEXT-BASED PDF")
        print("="*80)
        
        print(f"\n📋 Force OCR on TEXT PDF:")
        print(f"📄 Starting force OCR for: {existing_files['text_pdf']}")
        force_ocr_result = await tester.test_pdf_processing(existing_files["text_pdf"], force_ocr=True)
        print(f"✅ Force OCR completed")
        tester.print_processing_results(force_ocr_result)
    
    # Test 4: Processing Statistics
    print("\n" + "="*80)
    print("📊 PROCESSING STATISTICS")
    print("="*80)
    
    print("🔍 Getting processing stats...")
    stats = tester.processor.get_processing_stats()
    print(f"📈 Processing Summary:")
    print(f"   - Total processed: {stats['total_processed']}")
    print(f"   - Text-based count: {stats['text_based_count']}")
    print(f"   - Image-based count: {stats['image_based_count']}")
    print(f"   - Mixed count: {stats['mixed_count']}")
    print(f"   - Successful extractions: {stats['successful_extractions']}")
    print(f"   - Failed extractions: {stats['failed_extractions']}")
    print(f"   - Success rate: {stats['success_rate']:.1f}%")
    
    print("✅ All tests completed!")
    logger.info("✅ All tests completed!")


if __name__ == "__main__":
    print("🎬 Script starting...")
    asyncio.run(main())
    print("�� Script finished!") 