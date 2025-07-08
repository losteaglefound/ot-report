"""
Advanced PDF Detector

This module provides advanced detection capabilities to determine whether a PDF
is text-based or image-based with high accuracy.
"""

from dataclasses import dataclass
from enum import Enum
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF

from ..common.logging import logging


class PDFType(Enum):
    """PDF type enumeration"""
    TEXT_BASED = "text_based"
    IMAGE_BASED = "image_based"
    MIXED = "mixed"
    EMPTY = "empty"
    UNKNOWN = "unknown"


@dataclass
class PDFAnalysisResult:
    """Result of PDF analysis"""
    pdf_type: PDFType
    confidence: float
    total_pages: int
    text_pages: int
    image_pages: int
    mixed_pages: int
    empty_pages: int
    text_character_count: int
    image_count: int
    text_to_image_ratio: float
    has_extractable_text: bool
    has_embedded_images: bool
    has_vector_graphics: bool
    average_text_density: float
    image_coverage_percentage: float
    font_count: int
    details: Dict[str, any]


class AdvancedPDFDetector:
    """Advanced PDF detector for determining PDF content type"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Detection thresholds
        self.TEXT_DENSITY_THRESHOLD = 0.1  # Characters per square unit
        self.IMAGE_COVERAGE_THRESHOLD = 0.7  # 70% image coverage
        self.TEXT_LENGTH_THRESHOLD = 50  # Minimum characters for text detection
        self.CONFIDENCE_THRESHOLD = 0.8
        
    def detect_pdf_type(self, pdf_path: Union[str, Path]) -> PDFAnalysisResult:
        """
        Detect whether a PDF is text-based or image-based
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDFAnalysisResult with detection results
        """
        self.logger.info(f"🔍 Analyzing PDF: {pdf_path}")
        
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return self._create_error_result("PDF file not found")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(str(pdf_path))
            
            if doc.page_count == 0:
                return self._create_result(PDFType.EMPTY, 1.0, 0, {})
            
            # Analyze all pages
            analysis_data = self._analyze_all_pages(doc)
            
            # Determine PDF type based on analysis
            pdf_type, confidence = self._determine_pdf_type(analysis_data)
            
            # Create detailed result
            result = self._create_detailed_result(pdf_type, confidence, analysis_data)
            
            doc.close()
            
            self.logger.info(f"✅ PDF analysis complete: {pdf_type.value} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ PDF analysis failed: {str(e)}")
            return self._create_error_result(str(e))
    
    def _analyze_all_pages(self, doc: fitz.Document) -> Dict[str, any]:
        """Analyze all pages in the PDF"""
        
        analysis_data = {
            "total_pages": doc.page_count,
            "pages": [],
            "text_pages": 0,
            "image_pages": 0,
            "mixed_pages": 0,
            "empty_pages": 0,
            "total_text_chars": 0,
            "total_images": 0,
            "total_text_area": 0,
            "total_image_area": 0,
            "total_page_area": 0,
            "fonts": set(),
            "has_vector_graphics": False
        }
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_analysis = self._analyze_page(page, page_num)
            analysis_data["pages"].append(page_analysis)
            
            # Aggregate data
            if page_analysis["type"] == "text":
                analysis_data["text_pages"] += 1
            elif page_analysis["type"] == "image":
                analysis_data["image_pages"] += 1
            elif page_analysis["type"] == "mixed":
                analysis_data["mixed_pages"] += 1
            else:
                analysis_data["empty_pages"] += 1
            
            analysis_data["total_text_chars"] += page_analysis["text_chars"]
            analysis_data["total_images"] += page_analysis["image_count"]
            analysis_data["total_text_area"] += page_analysis["text_area"]
            analysis_data["total_image_area"] += page_analysis["image_area"]
            analysis_data["total_page_area"] += page_analysis["page_area"]
            analysis_data["fonts"].update(page_analysis["fonts"])
            
            if page_analysis["has_vector_graphics"]:
                analysis_data["has_vector_graphics"] = True
        
        return analysis_data
    
    def _analyze_page(self, page: fitz.Page, page_num: int) -> Dict[str, any]:
        """Analyze a single page"""
        
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height
        
        # Extract text
        text = page.get_text()
        text_chars = len(text.strip())
        
        # Get text blocks for area calculation
        text_blocks = page.get_text("dict")
        text_area = self._calculate_text_area(text_blocks)
        
        # Get images
        images = page.get_images(full=True)
        image_count = len(images)
        image_area = self._calculate_image_area(page, images)
        
        # Check for vector graphics
        has_vector_graphics = self._has_vector_graphics(page)
        
        # Extract fonts
        fonts = self._extract_fonts(text_blocks)
        
        # Calculate text density
        text_density = text_chars / page_area if page_area > 0 else 0
        
        # Determine page type
        page_type = self._determine_page_type(
            text_chars, image_count, text_area, image_area, page_area
        )
        
        return {
            "page_num": page_num,
            "type": page_type,
            "text_chars": text_chars,
            "image_count": image_count,
            "text_area": text_area,
            "image_area": image_area,
            "page_area": page_area,
            "text_density": text_density,
            "image_coverage": image_area / page_area if page_area > 0 else 0,
            "has_vector_graphics": has_vector_graphics,
            "fonts": fonts,
            "text_sample": text[:100] if text else ""
        }
    
    def _calculate_text_area(self, text_blocks: Dict) -> float:
        """Calculate total area covered by text"""
        total_area = 0
        
        try:
            for block in text_blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    bbox = block.get("bbox", [0, 0, 0, 0])
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    total_area += width * height
        except Exception as e:
            self.logger.warning(f"Error calculating text area: {e}")
        
        return total_area
    
    def _calculate_image_area(self, page: fitz.Page, images: List) -> float:
        """Calculate total area covered by images"""
        total_area = 0
        
        try:
            for img_index, img in enumerate(images):
                # Get image rectangle
                img_rects = page.get_image_rects(img[0])
                for rect in img_rects:
                    total_area += rect.width * rect.height
        except Exception as e:
            self.logger.warning(f"Error calculating image area: {e}")
        
        return total_area
    
    def _has_vector_graphics(self, page: fitz.Page) -> bool:
        """Check if page has vector graphics"""
        try:
            # Check for drawings/paths
            drawings = page.get_drawings()
            return len(drawings) > 0
        except Exception:
            return False
    
    def _extract_fonts(self, text_blocks: Dict) -> set:
        """Extract font names from text blocks"""
        fonts = set()
        
        try:
            for block in text_blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            font_name = span.get("font", "")
                            if font_name:
                                fonts.add(font_name)
        except Exception as e:
            self.logger.warning(f"Error extracting fonts: {e}")
        
        return fonts
    
    def _determine_page_type(self, text_chars: int, image_count: int, 
                           text_area: float, image_area: float, page_area: float) -> str:
        """Determine the type of a single page"""
        
        # Empty page
        if text_chars < 5 and image_count == 0:
            return "empty"
        
        # Calculate coverage ratios
        text_coverage = text_area / page_area if page_area > 0 else 0
        image_coverage = image_area / page_area if page_area > 0 else 0
        
        # Text-based page
        if (text_chars >= self.TEXT_LENGTH_THRESHOLD and 
            text_coverage > 0.1 and 
            image_coverage < 0.3):
            return "text"
        
        # Image-based page
        if (image_coverage > self.IMAGE_COVERAGE_THRESHOLD or 
            (image_count > 0 and text_chars < self.TEXT_LENGTH_THRESHOLD)):
            return "image"
        
        # Mixed page
        if text_chars >= self.TEXT_LENGTH_THRESHOLD and image_count > 0:
            return "mixed"
        
        # Default to image if has images, text if has text
        if image_count > 0:
            return "image"
        elif text_chars > 0:
            return "text"
        
        return "empty"
    
    def _determine_pdf_type(self, analysis_data: Dict) -> Tuple[PDFType, float]:
        """Determine overall PDF type and confidence"""
        
        total_pages = analysis_data["total_pages"]
        text_pages = analysis_data["text_pages"]
        image_pages = analysis_data["image_pages"]
        mixed_pages = analysis_data["mixed_pages"]
        empty_pages = analysis_data["empty_pages"]
        
        # Calculate ratios
        text_ratio = text_pages / total_pages if total_pages > 0 else 0
        image_ratio = image_pages / total_pages if total_pages > 0 else 0
        mixed_ratio = mixed_pages / total_pages if total_pages > 0 else 0
        
        # Calculate text/image content ratio
        total_chars = analysis_data["total_text_chars"]
        total_images = analysis_data["total_images"]
        
        # Determine type based on dominant content
        if text_ratio >= 0.8:
            return PDFType.TEXT_BASED, min(0.95, 0.5 + text_ratio * 0.5)
        elif image_ratio >= 0.8:
            return PDFType.IMAGE_BASED, min(0.95, 0.5 + image_ratio * 0.5)
        elif mixed_ratio >= 0.6:
            return PDFType.MIXED, min(0.9, 0.5 + mixed_ratio * 0.4)
        elif total_chars >= 1000 and total_images == 0:
            return PDFType.TEXT_BASED, 0.85
        elif total_images > 0 and total_chars < 100:
            return PDFType.IMAGE_BASED, 0.85
        elif empty_pages == total_pages:
            return PDFType.EMPTY, 0.95
        else:
            # Use additional heuristics
            if total_chars > total_images * 100:
                return PDFType.TEXT_BASED, 0.7
            elif total_images > 0:
                return PDFType.IMAGE_BASED, 0.7
            else:
                return PDFType.UNKNOWN, 0.5
    
    def _create_detailed_result(self, pdf_type: PDFType, confidence: float, 
                              analysis_data: Dict) -> PDFAnalysisResult:
        """Create detailed analysis result"""
        
        total_area = analysis_data["total_page_area"]
        text_area = analysis_data["total_text_area"]
        image_area = analysis_data["total_image_area"]
        
        return PDFAnalysisResult(
            pdf_type=pdf_type,
            confidence=confidence,
            total_pages=analysis_data["total_pages"],
            text_pages=analysis_data["text_pages"],
            image_pages=analysis_data["image_pages"],
            mixed_pages=analysis_data["mixed_pages"],
            empty_pages=analysis_data["empty_pages"],
            text_character_count=analysis_data["total_text_chars"],
            image_count=analysis_data["total_images"],
            text_to_image_ratio=analysis_data["total_text_chars"] / max(1, analysis_data["total_images"]),
            has_extractable_text=analysis_data["total_text_chars"] > 0,
            has_embedded_images=analysis_data["total_images"] > 0,
            has_vector_graphics=analysis_data["has_vector_graphics"],
            average_text_density=analysis_data["total_text_chars"] / max(1, total_area),
            image_coverage_percentage=(image_area / max(1, total_area)) * 100,
            font_count=len(analysis_data["fonts"]),
            details={
                "fonts": list(analysis_data["fonts"]),
                "pages": analysis_data["pages"],
                "text_area": text_area,
                "image_area": image_area,
                "total_area": total_area
            }
        )
    
    def _create_result(self, pdf_type: PDFType, confidence: float, 
                      total_pages: int, details: Dict) -> PDFAnalysisResult:
        """Create basic result"""
        return PDFAnalysisResult(
            pdf_type=pdf_type,
            confidence=confidence,
            total_pages=total_pages,
            text_pages=0,
            image_pages=0,
            mixed_pages=0,
            empty_pages=0,
            text_character_count=0,
            image_count=0,
            text_to_image_ratio=0,
            has_extractable_text=False,
            has_embedded_images=False,
            has_vector_graphics=False,
            average_text_density=0,
            image_coverage_percentage=0,
            font_count=0,
            details=details
        )
    
    def _create_error_result(self, error_message: str) -> PDFAnalysisResult:
        """Create error result"""
        return PDFAnalysisResult(
            pdf_type=PDFType.UNKNOWN,
            confidence=0.0,
            total_pages=0,
            text_pages=0,
            image_pages=0,
            mixed_pages=0,
            empty_pages=0,
            text_character_count=0,
            image_count=0,
            text_to_image_ratio=0,
            has_extractable_text=False,
            has_embedded_images=False,
            has_vector_graphics=False,
            average_text_density=0,
            image_coverage_percentage=0,
            font_count=0,
            details={"error": error_message}
        )


# Export main classes
__all__ = ["AdvancedPDFDetector", "PDFType", "PDFAnalysisResult"] 