import os
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from pdf_vision_ocr import PDFVisionOCR, process_pdf_batch

from sconfig import config
from backend.common.logging import logging

# Configure logging
logger = logging.getLogger(__name__)



async def test_single_pdf():
    """Test processing a single PDF file"""
    # Get OpenAI API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize processor
    processor = PDFVisionOCR(api_key)
    
    # Test PDF path - replace with your test PDF
    file = config.get_input_file_pdf_image_file()
    test_pdf = str(file)
    
    if not os.path.exists(test_pdf):
        raise FileNotFoundError(f"Test PDF not found: {test_pdf}")
    
    try:
        # Process PDF with image saving enabled
        results = await processor.process_pdf(test_pdf, save_images=True)
        
        # Print summary
        print("\n=== PDF Processing Results ===")
        print(f"File: {results['file_info']['filename']}")
        print(f"Total Pages: {results['summary']['total_pages']}")
        print(f"Pages with Images: {results['summary']['pages_with_images']}")
        print(f"Total Images: {results['summary']['total_images']}")
        print(f"Total Text Blocks: {results['summary']['total_text_blocks']}")
        
        # Check output directory
        output_dir = Path('outputs/ocr_results')
        print(f"\nOutput files saved in: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        raise

async def test_batch_processing():
    """Test processing multiple PDF files"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Test PDF directory - replace with your test PDFs directory
    test_pdfs_dir = "path/to/your/test_pdfs"
    
    if not os.path.exists(test_pdfs_dir):
        raise FileNotFoundError(f"Test PDFs directory not found: {test_pdfs_dir}")
    
    # Get all PDF files
    pdf_files = [
        str(f) for f in Path(test_pdfs_dir).glob("*.pdf")
    ]
    
    if not pdf_files:
        raise ValueError(f"No PDF files found in {test_pdfs_dir}")
    
    try:
        # Process batch of PDFs
        results = await process_pdf_batch(api_key, pdf_files, save_images=True)
        
        # Print summary for each PDF
        print("\n=== Batch Processing Results ===")
        for result in results:
            if "error" in result:
                print(f"\nError processing {result['file']}: {result['error']}")
            else:
                print(f"\nFile: {result['file_info']['filename']}")
                print(f"Total Pages: {result['summary']['total_pages']}")
                print(f"Total Images: {result['summary']['total_images']}")
                print(f"Total Text Blocks: {result['summary']['total_text_blocks']}")
        
    except Exception as e:
        logger.error(f"Error in batch test: {e}")
        raise

def main():
    """Main test function"""
    # Create test directories if they don't exist
    Path('outputs/ocr_results').mkdir(parents=True, exist_ok=True)
    Path('outputs/ocr_results/images').mkdir(parents=True, exist_ok=True)
    
    # Run tests
    asyncio.run(test_single_pdf())
    print("\nSingle PDF test completed!")
    
    # asyncio.run(test_batch_processing())
    # print("\nBatch processing test completed!")

if __name__ == "__main__":
    main() 