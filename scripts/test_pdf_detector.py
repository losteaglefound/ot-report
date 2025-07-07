#!/usr/bin/env python3
"""
Test script for Advanced PDF Detector

Simple demonstration of the PDF detector functionality
"""

import sys
from pathlib import Path

from sconfig import config

from backend.utils.pdf_detector import AdvancedPDFDetector, PDFType


def test_pdf_detector():
    """Test the PDF detector with sample files"""
    
    print("🔍 Testing Advanced PDF Detector")
    print("=" * 50)
    
    # Initialize detector
    detector = AdvancedPDFDetector()
    
    # Test files (you can change these paths)
    test_files = [
        config.PROJECT_DIR / "assets/inputs/Bayley-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf",
        config.PROJECT_DIR / "assets/inputs/images/Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"
    ]
    
    for pdf_path in test_files:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"❌ File not found: {pdf_path}")
            continue
        
        print(f"\n📄 Analyzing: {pdf_path.name}")
        print("-" * 40)
        
        # Detect PDF type
        result = detector.detect_pdf_type(pdf_path)
        
        # Display results
        print(f"🎯 Type: {result.pdf_type.value}")
        print(f"🔐 Confidence: {result.confidence:.2f}")
        print(f"📊 Total Pages: {result.total_pages}")
        print(f"📝 Text Pages: {result.text_pages}")
        print(f"🖼️ Image Pages: {result.image_pages}")
        print(f"🔤 Text Characters: {result.text_character_count}")
        print(f"🖼️ Images: {result.image_count}")
        print(f"📊 Text Density: {result.average_text_density:.4f}")
        print(f"🎨 Image Coverage: {result.image_coverage_percentage:.1f}%")
        print(f"🔤 Fonts: {result.font_count}")
        print(f"✅ Has Text: {result.has_extractable_text}")
        print(f"🖼️ Has Images: {result.has_embedded_images}")
        print(f"🎨 Has Vector Graphics: {result.has_vector_graphics}")
        
        # Show page breakdown
        if result.details and "pages" in result.details:
            page_types = {}
            for page in result.details["pages"]:
                page_type = page["type"]
                page_types[page_type] = page_types.get(page_type, 0) + 1
            
            print(f"📋 Page Breakdown: {page_types}")


def test_single_pdf():
    """Test with a single PDF file"""
    
    # Get PDF path from user
    pdf_path = input("Enter PDF path: ").strip()
    
    if not pdf_path:
        print("❌ No path provided")
        return
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"\n🔍 Analyzing: {pdf_path.name}")
    print("=" * 50)
    
    # Initialize detector and analyze
    detector = AdvancedPDFDetector()
    result = detector.detect_pdf_type(pdf_path)
    
    # Display comprehensive results
    print(f"📄 PDF Type: {result.pdf_type.value.upper()}")
    print(f"🎯 Confidence: {result.confidence:.2f}")
    print(f"📊 Analysis:")
    print(f"  - Total Pages: {result.total_pages}")
    print(f"  - Text Pages: {result.text_pages}")
    print(f"  - Image Pages: {result.image_pages}")
    print(f"  - Mixed Pages: {result.mixed_pages}")
    print(f"  - Empty Pages: {result.empty_pages}")
    print(f"  - Total Characters: {result.text_character_count}")
    print(f"  - Total Images: {result.image_count}")
    print(f"  - Text/Image Ratio: {result.text_to_image_ratio:.2f}")
    print(f"  - Text Density: {result.average_text_density:.4f}")
    print(f"  - Image Coverage: {result.image_coverage_percentage:.1f}%")
    print(f"  - Font Count: {result.font_count}")
    
    # Show decision factors
    print(f"\n🧠 Decision Factors:")
    print(f"  - Has Extractable Text: {result.has_extractable_text}")
    print(f"  - Has Embedded Images: {result.has_embedded_images}")
    print(f"  - Has Vector Graphics: {result.has_vector_graphics}")
    
    # Show recommendation
    if result.pdf_type == PDFType.TEXT_BASED:
        print("\n💡 Recommendation: Use text extraction methods")
    elif result.pdf_type == PDFType.IMAGE_BASED:
        print("\n💡 Recommendation: Use OCR for text extraction")
    elif result.pdf_type == PDFType.MIXED:
        print("\n💡 Recommendation: Use hybrid approach (text extraction + OCR)")
    else:
        print(f"\n💡 Recommendation: Handle as {result.pdf_type.value}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided file
        pdf_path = sys.argv[1]
        detector = AdvancedPDFDetector()
        result = detector.detect_pdf_type(pdf_path)
        print(f"PDF Type: {result.pdf_type.value}")
        print(f"Confidence: {result.confidence:.2f}")
    else:
        # Interactive mode
        print("Choose test mode:")
        print("1. Test with sample files")
        print("2. Test with single PDF")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            test_pdf_detector()
        elif choice == "2":
            test_single_pdf()
        else:
            print("Invalid choice") 