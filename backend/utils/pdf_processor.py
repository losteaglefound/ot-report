import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import io

# PDF processing imports
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from .pdf_detector import PDFDetector
from ..langgraph.ocr_agent import LangGraphOCRAgent


class UnifiedPDFProcessor:
    """
    Unified PDF processor that intelligently handles both text-based and image-based PDFs
    using detection logic and appropriate processing methods.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🚀 Initializing Unified PDF Processor...")
        
        # Initialize components
        self.pdf_detector = PDFDetector()
        self.ocr_agent = LangGraphOCRAgent(openai_api_key=openai_api_key)
        
        # Processing statistics
        self.processing_stats = {
            "total_processed": 0,
            "text_based_count": 0,
            "image_based_count": 0,
            "mixed_count": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
        
        self.logger.info("✅ Unified PDF Processor initialized successfully")
    
    async def process_pdf(self, file_path: str, force_ocr: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Process a PDF file intelligently based on its type
        
        Args:
            file_path: Path to the PDF file
            force_ocr: Force OCR processing even for text-based PDFs
            **kwargs: Additional metadata for processing
            
        Returns:
            Dict containing extracted text and processing information
        """
        self.logger.info(f"📄 Processing PDF: {os.path.basename(file_path)}")
        
        start_time = datetime.now()
        
        result = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "processing_started": start_time.isoformat(),
            "processing_method": "unknown",
            "pdf_type": "unknown",
            "detection_confidence": 0.0,
            "extracted_text": "",
            "metadata": kwargs,
            "processing_errors": [],
            "processing_complete": False,
            "processing_time_seconds": 0
        }
        
        try:
            # Step 1: Detect PDF type
            self.logger.info("🔍 Step 1: Detecting PDF type...")
            
            if force_ocr:
                self.logger.info("🔧 Force OCR mode enabled - skipping detection")
                detection_result = {
                    "pdf_type": "image_based",
                    "confidence": 1.0,
                    "recommendation": {
                        "primary_method": "ocr_vision",
                        "notes": "Forced OCR processing"
                    }
                }
            else:
                detection_result = await self.pdf_detector.detect_pdf_type(file_path)
            
            result["pdf_type"] = detection_result["pdf_type"]
            result["detection_confidence"] = detection_result["confidence"]
            result["detection_analysis"] = detection_result.get("analysis", {})
            result["processing_recommendation"] = detection_result.get("recommendation", {})
            
            # Step 2: Process based on detection
            self.logger.info(f"📊 Step 2: Processing as {result['pdf_type']} PDF...")
            
            if result["pdf_type"] == "text_based" and not force_ocr:
                # Use standard text extraction
                processing_result = await self._process_text_based_pdf(file_path, **kwargs)
                result["processing_method"] = "text_extraction"
                
            elif result["pdf_type"] == "image_based" or force_ocr:
                # Use OCR with vision
                processing_result = await self._process_image_based_pdf(file_path, **kwargs)
                result["processing_method"] = "ocr_vision"
                
            else:  # mixed
                # Use hybrid approach
                processing_result = await self._process_mixed_pdf(file_path, **kwargs)
                result["processing_method"] = "hybrid"
            
            # Step 3: Merge results
            result.update(processing_result)
            result["processing_complete"] = True
            
            # Update statistics
            self.processing_stats["total_processed"] += 1
            if result["pdf_type"] == "text_based":
                self.processing_stats["text_based_count"] += 1
            elif result["pdf_type"] == "image_based":
                self.processing_stats["image_based_count"] += 1
            else:
                self.processing_stats["mixed_count"] += 1
            
            if result["extracted_text"]:
                self.processing_stats["successful_extractions"] += 1
            else:
                self.processing_stats["failed_extractions"] += 1
            
            # Calculate processing time
            end_time = datetime.now()
            result["processing_completed"] = end_time.isoformat()
            result["processing_time_seconds"] = (end_time - start_time).total_seconds()
            
            self.logger.info(f"✅ PDF processing completed successfully")
            self.logger.info(f"   📄 Type: {result['pdf_type']} (confidence: {result['detection_confidence']:.2f})")
            self.logger.info(f"   🔧 Method: {result['processing_method']}")
            self.logger.info(f"   📝 Extracted: {len(result['extracted_text'])} characters")
            self.logger.info(f"   ⏱️ Time: {result['processing_time_seconds']:.2f}s")
            
        except Exception as e:
            error_msg = f"PDF processing failed: {str(e)}"
            result["processing_errors"].append(error_msg)
            result["processing_complete"] = False
            self.logger.error(f"❌ {error_msg}")
            
            # Update error statistics
            self.processing_stats["failed_extractions"] += 1
        
        return result
    
    async def _process_text_based_pdf(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Process text-based PDF using standard text extraction"""
        self.logger.info("📝 Processing text-based PDF...")
        
        result = {
            "extracted_text": "",
            "extraction_method": "text_extraction",
            "quality_score": 0.0,
            "processing_details": {},
            "processing_errors": []
        }
        
        try:
            # Try multiple extraction methods
            text_content = ""
            
            # Method 1: pdfplumber (preferred for text-based)
            if PDFPLUMBER_AVAILABLE:
                try:
                    self.logger.info("🔧 Using pdfplumber for text extraction...")
                    text_content = await self._extract_with_pdfplumber(file_path)
                    if text_content:
                        result["extraction_method"] = "pdfplumber"
                        self.logger.info(f"✅ pdfplumber extraction successful: {len(text_content)} characters")
                except Exception as e:
                    self.logger.warning(f"⚠️ pdfplumber extraction failed: {e}")
            
            # Method 2: PyPDF2 (fallback)
            if not text_content and PYPDF2_AVAILABLE:
                try:
                    self.logger.info("🔧 Using PyPDF2 for text extraction...")
                    text_content = await self._extract_with_pypdf2(file_path)
                    if text_content:
                        result["extraction_method"] = "pypdf2"
                        self.logger.info(f"✅ PyPDF2 extraction successful: {len(text_content)} characters")
                except Exception as e:
                    self.logger.warning(f"⚠️ PyPDF2 extraction failed: {e}")
            
            # Method 3: PyMuPDF (final fallback)
            if not text_content and PYMUPDF_AVAILABLE:
                try:
                    self.logger.info("🔧 Using PyMuPDF for text extraction...")
                    text_content = await self._extract_with_pymupdf(file_path)
                    if text_content:
                        result["extraction_method"] = "pymupdf"
                        self.logger.info(f"✅ PyMuPDF extraction successful: {len(text_content)} characters")
                except Exception as e:
                    self.logger.warning(f"⚠️ PyMuPDF extraction failed: {e}")
            
            result["extracted_text"] = text_content
            
            # Calculate quality score
            if text_content:
                result["quality_score"] = min(1.0, len(text_content) / 1000)  # Normalize to 1000 chars
            
            # Processing details
            result["processing_details"] = {
                "total_characters": len(text_content),
                "has_content": bool(text_content.strip()),
                "extraction_successful": bool(text_content)
            }
            
            if not text_content:
                result["processing_errors"].append("No text could be extracted from PDF")
            
        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            result["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return result
    
    async def _process_image_based_pdf(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Process image-based PDF using OCR with vision"""
        self.logger.info("🖼️ Processing image-based PDF with OCR...")
        
        result = {
            "extracted_text": "",
            "extraction_method": "ocr_vision",
            "quality_score": 0.0,
            "processing_details": {},
            "processing_errors": []
        }
        
        try:
            # Extract images from PDF and process with OCR
            extracted_data = await self._extract_images_and_ocr(file_path, **kwargs)
            
            # Combine all extracted texts
            combined_text = ""
            total_quality = 0.0
            successful_extractions = 0
            
            for page_data in extracted_data.get("pages", []):
                page_text = page_data.get("extracted_text", "")
                if page_text:
                    combined_text += f"\n--- Page {page_data.get('page_number', 'unknown')} ---\n{page_text}\n"
                    total_quality += page_data.get("quality_score", 0.0)
                    successful_extractions += 1
            
            result["extracted_text"] = combined_text.strip()
            
            # Calculate average quality score
            if successful_extractions > 0:
                result["quality_score"] = total_quality / successful_extractions
            
            # Processing details
            result["processing_details"] = {
                "total_pages": extracted_data.get("total_pages", 0),
                "pages_with_images": extracted_data.get("pages_with_images", 0),
                "successful_extractions": successful_extractions,
                "total_characters": len(combined_text),
                "average_quality_score": result["quality_score"]
            }
            
            # Collect any processing errors
            result["processing_errors"] = extracted_data.get("processing_errors", [])
            
        except Exception as e:
            error_msg = f"OCR processing failed: {str(e)}"
            result["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return result
    
    async def _process_mixed_pdf(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Process mixed PDF using hybrid approach"""
        self.logger.info("🔀 Processing mixed PDF with hybrid approach...")
        
        result = {
            "extracted_text": "",
            "extraction_method": "hybrid",
            "quality_score": 0.0,
            "processing_details": {},
            "processing_errors": []
        }
        
        try:
            # Step 1: Extract regular text
            text_result = await self._process_text_based_pdf(file_path, **kwargs)
            regular_text = text_result.get("extracted_text", "")
            
            # Step 2: Extract text from images
            ocr_result = await self._process_image_based_pdf(file_path, **kwargs)
            ocr_text = ocr_result.get("extracted_text", "")
            
            # Step 3: Combine results
            combined_text = ""
            
            if regular_text:
                combined_text += "=== EXTRACTED TEXT ===\n" + regular_text + "\n\n"
            
            if ocr_text:
                combined_text += "=== OCR EXTRACTED TEXT ===\n" + ocr_text + "\n\n"
            
            result["extracted_text"] = combined_text.strip()
            
            # Calculate combined quality score
            text_quality = text_result.get("quality_score", 0.0)
            ocr_quality = ocr_result.get("quality_score", 0.0)
            result["quality_score"] = (text_quality + ocr_quality) / 2
            
            # Processing details
            result["processing_details"] = {
                "regular_text_length": len(regular_text),
                "ocr_text_length": len(ocr_text),
                "combined_text_length": len(combined_text),
                "text_extraction_quality": text_quality,
                "ocr_extraction_quality": ocr_quality,
                "combined_quality": result["quality_score"]
            }
            
            # Combine errors
            result["processing_errors"] = text_result.get("processing_errors", []) + ocr_result.get("processing_errors", [])
            
        except Exception as e:
            error_msg = f"Hybrid processing failed: {str(e)}"
            result["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return result
    
    async def _extract_images_and_ocr(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract images from PDF and process with OCR"""
        self.logger.info("🖼️ Extracting images from PDF for OCR...")
        
        extracted_data = {
            "total_pages": 0,
            "pages_with_images": 0,
            "pages": [],
            "processing_errors": []
        }
        
        try:
            if not PYMUPDF_AVAILABLE:
                raise RuntimeError("PyMuPDF required for image extraction")
            
            doc = fitz.open(file_path)
            extracted_data["total_pages"] = len(doc)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_data = {
                    "page_number": page_num + 1,
                    "extracted_text": "",
                    "quality_score": 0.0,
                    "processing_errors": []
                }
                
                # Get images from page
                image_list = page.get_images(full=True)
                
                if image_list:
                    extracted_data["pages_with_images"] += 1
                    
                    # Process each image with OCR
                    page_texts = []
                    page_qualities = []
                    
                    for img_idx, img in enumerate(image_list):
                        try:
                            # Extract image data
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Process with OCR agent
                            ocr_result = await self.ocr_agent.process_image(
                                image_data=image_bytes,
                                document_type=kwargs.get("document_type", "medical_assessment"),
                                page_number=page_num + 1,
                                image_index=img_idx + 1
                            )
                            
                            # Extract results
                            extracted_text = ocr_result.get("extracted_text", "")
                            quality_score = ocr_result.get("quality_score", 0.0)
                            
                            if extracted_text:
                                page_texts.append(extracted_text)
                                page_qualities.append(quality_score)
                            
                            # Collect any errors
                            page_data["processing_errors"].extend(ocr_result.get("processing_errors", []))
                            
                        except Exception as e:
                            error_msg = f"Error processing image {img_idx + 1} on page {page_num + 1}: {str(e)}"
                            page_data["processing_errors"].append(error_msg)
                            self.logger.warning(f"⚠️ {error_msg}")
                    
                    # Combine page results
                    if page_texts:
                        page_data["extracted_text"] = "\n".join(page_texts)
                        page_data["quality_score"] = sum(page_qualities) / len(page_qualities)
                    
                extracted_data["pages"].append(page_data)
            
            doc.close()
            
        except Exception as e:
            error_msg = f"Image extraction and OCR failed: {str(e)}"
            extracted_data["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return extracted_data
    
    async def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber"""
        text_content = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        
        return text_content.strip()
    
    async def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2"""
        text_content = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        
        return text_content.strip()
    
    async def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF"""
        text_content = ""
        
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text:
                text_content += page_text + "\n"
        
        doc.close()
        return text_content.strip()
    
    async def batch_process_pdfs(self, file_paths: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Process multiple PDFs in batch"""
        self.logger.info(f"📄 Starting batch processing of {len(file_paths)} PDFs...")
        
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.process_pdf(file_path, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"❌ Failed to process {file_path}: {e}")
                results.append({
                    "file_path": file_path,
                    "processing_complete": False,
                    "processing_errors": [str(e)]
                })
        
        self.logger.info(f"✅ Batch processing completed: {len(results)} PDFs processed")
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.processing_stats,
            "success_rate": (
                self.processing_stats["successful_extractions"] / 
                max(1, self.processing_stats["total_processed"])
            ) * 100
        }
    
    async def quick_pdf_check(self, file_path: str) -> Dict[str, Any]:
        """Quick check of PDF type without full processing"""
        return await self.pdf_detector.quick_check(file_path)


# Export the processor
__all__ = ["UnifiedPDFProcessor"] 