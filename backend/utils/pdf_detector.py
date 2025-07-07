import logging
import os
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

from PIL import Image


class PDFDetector:
    """Advanced PDF detection utility to determine if PDF is text-based or image-based"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🔍 Initializing PDF Detector...")
        
        # A4 dimensions in points (72 points per inch)
        self.A4_WIDTH = 595.276  # 8.27 inches
        self.A4_HEIGHT = 841.890  # 11.69 inches
        self.TOLERANCE = 10  # tolerance for A4 detection
        
        # Thresholds for detection
        self.TEXT_DENSITY_THRESHOLD = 50  # characters per page minimum for text-based
        self.IMAGE_COVERAGE_THRESHOLD = 0.3  # 30% of page covered by images
        self.MIN_IMAGE_SIZE = 1000  # minimum image size in bytes
        
        self.logger.info("✅ PDF Detector initialized successfully")
    
    async def detect_pdf_type(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive PDF type detection
        
        Returns:
            Dict containing:
            - pdf_type: 'text_based', 'image_based', or 'mixed'
            - confidence: 0.0 to 1.0
            - analysis: detailed analysis results
            - recommendation: processing recommendation
        """
        self.logger.info(f"🔍 Detecting PDF type: {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Get comprehensive analysis
        analysis = await self._analyze_pdf_comprehensive(file_path)
        
        # Determine PDF type based on analysis
        pdf_type, confidence = self._determine_pdf_type(analysis)
        
        result = {
            "pdf_type": pdf_type,
            "confidence": confidence,
            "file_path": file_path,
            "analysis": analysis,
            "recommendation": self._get_processing_recommendation(pdf_type, analysis),
            "detected_at": "now"
        }
        
        self.logger.info(f"✅ Detection complete: {pdf_type} (confidence: {confidence:.2f})")
        return result
    
    async def _analyze_pdf_comprehensive(self, file_path: str) -> Dict[str, Any]:
        """Comprehensive PDF analysis using multiple detection methods"""
        analysis = {
            "total_pages": 0,
            "text_analysis": {
                "total_chars": 0,
                "avg_chars_per_page": 0,
                "extractable_text_ratio": 0,
                "pages_with_text": 0
            },
            "image_analysis": {
                "total_images": 0,
                "significant_images": 0,
                "image_coverage_ratio": 0,
                "pages_with_images": 0,
                "large_images": 0
            },
            "structure_analysis": {
                "has_a4_pages": False,
                "mixed_page_sizes": False,
                "non_standard_layout": False
            },
            "quality_metrics": {
                "text_extraction_success": 0,
                "image_detection_success": 0,
                "overall_quality": 0
            }
        }
        
        try:
            # Use PyMuPDF for most comprehensive analysis
            if PYMUPDF_AVAILABLE:
                analysis.update(await self._analyze_with_pymupdf(file_path))
            # Fallback to pdfplumber
            elif PDFPLUMBER_AVAILABLE:
                analysis.update(await self._analyze_with_pdfplumber(file_path))
            # Final fallback to PyPDF2
            elif PYPDF2_AVAILABLE:
                analysis.update(await self._analyze_with_pypdf2(file_path))
            else:
                raise RuntimeError("No PDF processing library available")
            
            # Calculate derived metrics
            self._calculate_derived_metrics(analysis)
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive analysis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    async def _analyze_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF using PyMuPDF (most comprehensive)"""
        analysis = {
            "total_pages": 0,
            "text_analysis": {"total_chars": 0, "pages_with_text": 0},
            "image_analysis": {"total_images": 0, "significant_images": 0, "pages_with_images": 0, "large_images": 0},
            "structure_analysis": {"has_a4_pages": False, "mixed_page_sizes": False},
            "page_details": []
        }
        
        try:
            doc = fitz.open(file_path)
            analysis["total_pages"] = len(doc)
            
            page_sizes = set()
            pages_with_text = 0
            pages_with_images = 0
            total_chars = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_detail = {
                    "page_number": page_num + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "text_chars": 0,
                    "image_count": 0,
                    "large_image_count": 0
                }
                
                # Analyze text
                text_content = page.get_text()
                if text_content and text_content.strip():
                    char_count = len(text_content.strip())
                    page_detail["text_chars"] = char_count
                    total_chars += char_count
                    if char_count > self.TEXT_DENSITY_THRESHOLD:
                        pages_with_text += 1
                
                # Analyze images
                image_list = page.get_images(full=True)
                page_detail["image_count"] = len(image_list)
                
                if image_list:
                    pages_with_images += 1
                    for img in image_list:
                        try:
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Check if image is significant
                            if len(image_bytes) > self.MIN_IMAGE_SIZE:
                                analysis["image_analysis"]["significant_images"] += 1
                                
                                # Check image dimensions
                                img_pil = Image.open(io.BytesIO(image_bytes))
                                img_width, img_height = img_pil.size
                                
                                # Consider large images (> 25% of page area)
                                page_area = page.rect.width * page.rect.height
                                img_area = img_width * img_height
                                if img_area > (page_area * 0.25):
                                    page_detail["large_image_count"] += 1
                                    analysis["image_analysis"]["large_images"] += 1
                        
                        except Exception as e:
                            self.logger.warning(f"⚠️ Error analyzing image on page {page_num + 1}: {e}")
                
                # Track page sizes
                page_sizes.add((round(page.rect.width), round(page.rect.height)))
                
                # Check if A4
                is_a4 = self._is_a4_page(page.rect.width, page.rect.height)
                page_detail["is_a4"] = is_a4
                
                analysis["page_details"].append(page_detail)
            
            # Update analysis
            analysis["text_analysis"]["total_chars"] = total_chars
            analysis["text_analysis"]["pages_with_text"] = pages_with_text
            analysis["image_analysis"]["total_images"] = sum(p["image_count"] for p in analysis["page_details"])
            analysis["image_analysis"]["pages_with_images"] = pages_with_images
            analysis["structure_analysis"]["has_a4_pages"] = any(p["is_a4"] for p in analysis["page_details"])
            analysis["structure_analysis"]["mixed_page_sizes"] = len(page_sizes) > 1
            
            doc.close()
            
        except Exception as e:
            self.logger.error(f"❌ PyMuPDF analysis failed: {e}")
            raise
        
        return analysis
    
    async def _analyze_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF using pdfplumber (fallback)"""
        analysis = {
            "total_pages": 0,
            "text_analysis": {"total_chars": 0, "pages_with_text": 0},
            "image_analysis": {"total_images": 0, "significant_images": 0, "pages_with_images": 0, "large_images": 0},
            "structure_analysis": {"has_a4_pages": False, "mixed_page_sizes": False},
            "page_details": []
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                analysis["total_pages"] = len(pdf.pages)
                
                page_sizes = set()
                pages_with_text = 0
                pages_with_images = 0
                total_chars = 0
                
                for page_num, page in enumerate(pdf.pages):
                    page_detail = {
                        "page_number": page_num + 1,
                        "width": page.width,
                        "height": page.height,
                        "text_chars": 0,
                        "image_count": 0,
                        "large_image_count": 0
                    }
                    
                    # Analyze text
                    text_content = page.extract_text()
                    if text_content and text_content.strip():
                        char_count = len(text_content.strip())
                        page_detail["text_chars"] = char_count
                        total_chars += char_count
                        if char_count > self.TEXT_DENSITY_THRESHOLD:
                            pages_with_text += 1
                    
                    # Analyze images (basic with pdfplumber)
                    try:
                        images = page.images
                        if images:
                            page_detail["image_count"] = len(images)
                            pages_with_images += 1
                            # Assume all detected images are significant (pdfplumber limitation)
                            analysis["image_analysis"]["significant_images"] += len(images)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error detecting images on page {page_num + 1}: {e}")
                    
                    # Track page sizes
                    page_sizes.add((round(page.width), round(page.height)))
                    
                    # Check if A4
                    is_a4 = self._is_a4_page(page.width, page.height)
                    page_detail["is_a4"] = is_a4
                    
                    analysis["page_details"].append(page_detail)
                
                # Update analysis
                analysis["text_analysis"]["total_chars"] = total_chars
                analysis["text_analysis"]["pages_with_text"] = pages_with_text
                analysis["image_analysis"]["total_images"] = sum(p["image_count"] for p in analysis["page_details"])
                analysis["image_analysis"]["pages_with_images"] = pages_with_images
                analysis["structure_analysis"]["has_a4_pages"] = any(p["is_a4"] for p in analysis["page_details"])
                analysis["structure_analysis"]["mixed_page_sizes"] = len(page_sizes) > 1
                
        except Exception as e:
            self.logger.error(f"❌ pdfplumber analysis failed: {e}")
            raise
        
        return analysis
    
    async def _analyze_with_pypdf2(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF using PyPDF2 (basic fallback)"""
        analysis = {
            "total_pages": 0,
            "text_analysis": {"total_chars": 0, "pages_with_text": 0},
            "image_analysis": {"total_images": 0, "significant_images": 0, "pages_with_images": 0, "large_images": 0},
            "structure_analysis": {"has_a4_pages": False, "mixed_page_sizes": False},
            "page_details": []
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                analysis["total_pages"] = len(pdf_reader.pages)
                
                pages_with_text = 0
                total_chars = 0
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_detail = {
                        "page_number": page_num + 1,
                        "width": 0,  # PyPDF2 doesn't easily provide dimensions
                        "height": 0,
                        "text_chars": 0,
                        "image_count": 0,  # PyPDF2 has limited image detection
                        "large_image_count": 0
                    }
                    
                    # Analyze text
                    text_content = page.extract_text()
                    if text_content and text_content.strip():
                        char_count = len(text_content.strip())
                        page_detail["text_chars"] = char_count
                        total_chars += char_count
                        if char_count > self.TEXT_DENSITY_THRESHOLD:
                            pages_with_text += 1
                    
                    analysis["page_details"].append(page_detail)
                
                # Update analysis
                analysis["text_analysis"]["total_chars"] = total_chars
                analysis["text_analysis"]["pages_with_text"] = pages_with_text
                
        except Exception as e:
            self.logger.error(f"❌ PyPDF2 analysis failed: {e}")
            raise
        
        return analysis
    
    def _is_a4_page(self, width: float, height: float) -> bool:
        """Check if page dimensions match A4 (portrait or landscape)"""
        is_a4_portrait = (
            abs(width - self.A4_WIDTH) <= self.TOLERANCE and 
            abs(height - self.A4_HEIGHT) <= self.TOLERANCE
        )
        is_a4_landscape = (
            abs(width - self.A4_HEIGHT) <= self.TOLERANCE and 
            abs(height - self.A4_WIDTH) <= self.TOLERANCE
        )
        return is_a4_portrait or is_a4_landscape
    
    def _calculate_derived_metrics(self, analysis: Dict[str, Any]) -> None:
        """Calculate derived metrics from analysis"""
        total_pages = analysis["total_pages"]
        
        if total_pages > 0:
            # Text metrics
            analysis["text_analysis"]["avg_chars_per_page"] = analysis["text_analysis"]["total_chars"] / total_pages
            analysis["text_analysis"]["extractable_text_ratio"] = analysis["text_analysis"]["pages_with_text"] / total_pages
            
            # Image metrics
            analysis["image_analysis"]["image_coverage_ratio"] = analysis["image_analysis"]["pages_with_images"] / total_pages
            
            # Quality metrics
            analysis["quality_metrics"]["text_extraction_success"] = min(1.0, analysis["text_analysis"]["total_chars"] / (total_pages * 100))
            analysis["quality_metrics"]["image_detection_success"] = 1.0 if analysis["image_analysis"]["total_images"] > 0 else 0.0
            analysis["quality_metrics"]["overall_quality"] = (
                analysis["quality_metrics"]["text_extraction_success"] + 
                analysis["quality_metrics"]["image_detection_success"]
            ) / 2
    
    def _determine_pdf_type(self, analysis: Dict[str, Any]) -> tuple[str, float]:
        """Determine PDF type based on analysis with confidence score"""
        
        # Extract key metrics
        avg_chars_per_page = analysis["text_analysis"]["avg_chars_per_page"]
        extractable_text_ratio = analysis["text_analysis"]["extractable_text_ratio"]
        image_coverage_ratio = analysis["image_analysis"]["image_coverage_ratio"]
        significant_images = analysis["image_analysis"]["significant_images"]
        large_images = analysis["image_analysis"]["large_images"]
        total_pages = analysis["total_pages"]
        
        # Decision logic with confidence scoring
        confidence_factors = []
        
        # Factor 1: Text density analysis
        if avg_chars_per_page > 500:  # High text density
            text_score = 1.0
            confidence_factors.append(("high_text_density", 0.9))
        elif avg_chars_per_page > 200:  # Medium text density
            text_score = 0.7
            confidence_factors.append(("medium_text_density", 0.7))
        elif avg_chars_per_page > 50:  # Low text density
            text_score = 0.3
            confidence_factors.append(("low_text_density", 0.5))
        else:  # Very low text density
            text_score = 0.0
            confidence_factors.append(("very_low_text_density", 0.8))
        
        # Factor 2: Image analysis
        if significant_images > (total_pages * 0.5):  # Many significant images
            image_score = 1.0
            confidence_factors.append(("many_images", 0.9))
        elif significant_images > 0:  # Some images
            image_score = 0.5
            confidence_factors.append(("some_images", 0.7))
        else:  # No images
            image_score = 0.0
            confidence_factors.append(("no_images", 0.9))
        
        # Factor 3: Large image analysis
        if large_images > (total_pages * 0.3):  # Many large images
            large_image_score = 1.0
            confidence_factors.append(("many_large_images", 0.9))
        elif large_images > 0:  # Some large images
            large_image_score = 0.5
            confidence_factors.append(("some_large_images", 0.7))
        else:  # No large images
            large_image_score = 0.0
            confidence_factors.append(("no_large_images", 0.8))
        
        # Factor 4: Text extraction success ratio
        if extractable_text_ratio > 0.8:  # High text extraction success
            extraction_score = 1.0
            confidence_factors.append(("high_extraction_success", 0.9))
        elif extractable_text_ratio > 0.5:  # Medium text extraction success
            extraction_score = 0.7
            confidence_factors.append(("medium_extraction_success", 0.7))
        elif extractable_text_ratio > 0.2:  # Low text extraction success
            extraction_score = 0.3
            confidence_factors.append(("low_extraction_success", 0.6))
        else:  # Very low text extraction success
            extraction_score = 0.0
            confidence_factors.append(("very_low_extraction_success", 0.8))
        
        # Decision matrix
        text_weight = (text_score + extraction_score) / 2
        image_weight = (image_score + large_image_score) / 2
        
        # Determine type
        if text_weight > 0.7 and image_weight < 0.3:
            pdf_type = "text_based"
            base_confidence = 0.8
        elif image_weight > 0.6 and text_weight < 0.4:
            pdf_type = "image_based"
            base_confidence = 0.8
        elif text_weight > 0.4 and image_weight > 0.4:
            pdf_type = "mixed"
            base_confidence = 0.7
        elif text_weight < 0.3 and image_weight < 0.3:
            # Uncertain case - lean towards image_based for safety
            pdf_type = "image_based"
            base_confidence = 0.5
        else:
            # Default case
            if text_weight > image_weight:
                pdf_type = "text_based"
                base_confidence = 0.6
            else:
                pdf_type = "image_based"
                base_confidence = 0.6
        
        # Adjust confidence based on factors
        confidence_adjustment = sum(cf[1] for cf in confidence_factors) / len(confidence_factors)
        final_confidence = (base_confidence + confidence_adjustment) / 2
        
        # Cap confidence at 1.0
        final_confidence = min(1.0, final_confidence)
        
        return pdf_type, final_confidence
    
    def _get_processing_recommendation(self, pdf_type: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get processing recommendation based on PDF type and analysis"""
        
        if pdf_type == "text_based":
            return {
                "primary_method": "text_extraction",
                "fallback_method": "ocr_if_needed",
                "expected_quality": "high",
                "processing_time": "fast",
                "notes": "Standard text extraction should work well"
            }
        
        elif pdf_type == "image_based":
            return {
                "primary_method": "ocr_vision",
                "fallback_method": "text_extraction_attempt",
                "expected_quality": "medium_to_high",
                "processing_time": "slow",
                "notes": "Use OCR with vision model for best results"
            }
        
        else:  # mixed
            return {
                "primary_method": "hybrid_approach",
                "fallback_method": "ocr_vision",
                "expected_quality": "medium",
                "processing_time": "medium",
                "notes": "Combine text extraction with OCR for images"
            }
    
    async def quick_check(self, file_path: str) -> Dict[str, Any]:
        """Quick check for PDF type (faster, less comprehensive)"""
        self.logger.info(f"⚡ Quick PDF check: {os.path.basename(file_path)}")
        
        result = {
            "has_images": False,
            "has_extractable_text": False,
            "total_pages": 0,
            "quick_type": "unknown"
        }
        
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                result["total_pages"] = len(doc)
                
                # Check first few pages for images and text
                pages_to_check = min(3, len(doc))
                has_images = False
                has_text = False
                
                for page_num in range(pages_to_check):
                    page = doc.load_page(page_num)
                    
                    # Quick image check
                    if page.get_images():
                        has_images = True
                    
                    # Quick text check
                    text = page.get_text()
                    if text and len(text.strip()) > 50:
                        has_text = True
                
                result["has_images"] = has_images
                result["has_extractable_text"] = has_text
                
                # Quick type determination
                if has_text and not has_images:
                    result["quick_type"] = "text_based"
                elif has_images and not has_text:
                    result["quick_type"] = "image_based"
                elif has_text and has_images:
                    result["quick_type"] = "mixed"
                else:
                    result["quick_type"] = "unknown"
                
                doc.close()
                
        except Exception as e:
            self.logger.error(f"❌ Quick check failed: {e}")
            result["error"] = str(e)
        
        return result 