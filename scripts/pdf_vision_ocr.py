import os
import json
import base64
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io
from openai import AsyncOpenAI
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFVisionOCR:
    """PDF OCR processor using OpenAI's Vision model"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.supported_image_formats = ['jpeg', 'jpg', 'png']
        self.output_dir = Path('outputs/ocr_results')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def process_pdf(self, pdf_path: str, save_images: bool = False) -> Dict[str, Any]:
        """Process a PDF file and extract text using OpenAI Vision"""
        logger.info(f"Processing PDF: {pdf_path}")
        
        results = {
            "file_info": {
                "filename": os.path.basename(pdf_path),
                "processed_at": datetime.now().isoformat(),
            },
            "metadata": {},
            "pages": [],
            "summary": {},
        }
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Extract metadata
            results["metadata"] = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
            }
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_data = await self._process_page(page, page_num + 1, save_images)
                results["pages"].append(page_data)
            
            # Generate summary
            results["summary"] = {
                "total_pages": len(doc),
                "pages_with_images": sum(1 for p in results["pages"] if p["images"]),
                "total_images": sum(len(p["images"]) for p in results["pages"]),
                "total_text_blocks": sum(len(p["text_blocks"]) for p in results["pages"]),
            }
            
            # Save results
            output_path = self._get_output_path(pdf_path)
            self._save_results(results, output_path)
            
            doc.close()
            return results
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
    
    async def _process_page(self, page: fitz.Page, page_num: int, save_images: bool) -> Dict[str, Any]:
        """Process a single PDF page"""
        page_data = {
            "page_number": page_num,
            "size": {"width": page.rect.width, "height": page.rect.height},
            "images": [],
            "text_blocks": [],
            "tables": [],
        }
        
        # Extract images
        image_list = page.get_images(full=True)
        
        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                if base_image["ext"].lower() not in self.supported_image_formats:
                    continue
                
                image_bytes = base_image["image"]

                image_path = self._save_image_base64(image_bytes, page_num, img_idx, "txt")
                
                # Process image with Vision API
                vision_result = await self._process_image_with_vision(
                    image_bytes,
                    f"Please read and extract all the text from this image, including small or faint characters."
                )
                
                image_data = {
                    "image_index": img_idx + 1,
                    "format": base_image["ext"],
                    "size": {"width": base_image["width"], "height": base_image["height"]},
                    "extracted_text": vision_result
                    # "extracted_text": vision_result.get("text", ""),
                    # "confidence": vision_result.get("confidence", 0),
                    # "detected_elements": vision_result.get("detected_elements", []),
                }
                
                # Save image if requested
                if save_images:
                    image_path = self._save_image(image_bytes, page_num, img_idx, base_image["ext"])
                    image_data["saved_path"] = str(image_path)
                
                page_data["images"].append(image_data)
                
                # Add extracted text blocks
                # if vision_result.get("text"):
                #     page_data["text_blocks"].append({
                #         "source": "image",
                #         "image_index": img_idx + 1,
                #         "text": vision_result["text"],
                #         "confidence": vision_result.get("confidence", 0),
                #     })
                if vision_result:
                    page_data['text_blocks'].append({
                        "text": vision_result
                    })
                
                # Add detected tables
                # if vision_result.get("tables"):
                #     page_data["tables"].extend(vision_result["tables"])
                
            except Exception as e:
                logger.warning(f"Error processing image {img_idx + 1} on page {page_num}: {e}")
        
        return page_data
    
    async def _process_image_with_vision(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """Process an image using OpenAI Vision API"""
        try:
            # Convert image bytes to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare messages for Vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # Call Vision API
            response = await self.client.chat.completions.create(
                # model="gpt-4-vision-preview",
                model = "gpt-4-turbo-2024-04-09",
                messages=messages,
                max_tokens=1000,
                temperature=0.8
            )
            
            response_content = response.choices[0].message.content
            # print(f"\n{response_content}\n")

            # Process response
            # result = self._parse_vision_response(response_content)
            # return result
            return response_content
            
        except Exception as e:
            logger.error(f"Error calling Vision API: {e}")
            return {"error": str(e)}
    
    
    def _parse_vision_response(self, response: str) -> Dict[str, Any]:
        """Parse the Vision API response into structured data"""
        result = {
            "text": "",
            "confidence": "medium",
            "detected_elements": [],
            "tables": []
        }
        
        try:
            # Split response into sections
            sections = response.split('\n\n')
            
            for section in sections:
                if section.lower().startswith('text:'):
                    result["text"] = section[5:].strip()
                elif section.lower().startswith('table:'):
                    # Parse table data
                    table_data = self._parse_table_data(section[6:].strip())
                    if table_data:
                        result["tables"].append(table_data)
                elif section.lower().startswith('elements:'):
                    result["detected_elements"] = [
                        elem.strip() for elem in section[9:].strip().split(',')
                    ]
                elif section.lower().startswith('confidence:'):
                    confidence = section[11:].strip().lower()
                    if 'high' in confidence:
                        result["confidence"] = "high"
                    elif 'low' in confidence:
                        result["confidence"] = "low"
            
        except Exception as e:
            logger.warning(f"Error parsing Vision response: {e}")
        
        return result
    
    def _parse_table_data(self, table_text: str) -> Dict[str, Any]:
        """Parse table data from text"""
        try:
            rows = [row.strip().split('|') for row in table_text.split('\n')]
            if not rows:
                return None
            
            return {
                "headers": [cell.strip() for cell in rows[0]],
                "data": [[cell.strip() for cell in row] for row in rows[1:]]
            }
        except Exception:
            return None
    
    def _get_output_path(self, pdf_path: str) -> Path:
        """Generate output path for results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(pdf_path).stem
        return self.output_dir / f"{base_name}_ocr_{timestamp}.json"
    
    def _save_image(self, image_bytes: bytes, page_num: int, img_idx: int, ext: str) -> Path:
        """Save extracted image"""
        images_dir = self.output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        image_path = images_dir / f"page_{page_num}_img_{img_idx}.{ext}"
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        return image_path

    def _save_image_base64(self, image_bytes: bytes, page_num: int, img_idx: int, ext: str) -> Path:
        """Save extracted image"""
        images_dir = self.output_dir / "texts"
        images_dir.mkdir(exist_ok=True)

        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        image_path = images_dir / f"page_{page_num}_img_{img_idx}.{ext}"
        with open(image_path, 'wt') as f:
            f.write(base64_image)
        
        return image_path
    
    def _save_results(self, results: Dict[str, Any], output_path: Path):
        """Save results to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to: {output_path}")

async def process_pdf_batch(api_key: str, pdf_files: List[str], save_images: bool = False) -> List[Dict[str, Any]]:
    """Process multiple PDF files"""
    processor = PDFVisionOCR(api_key)
    results = []
    
    for pdf_file in pdf_files:
        try:
            result = await processor.process_pdf(pdf_file, save_images)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
            results.append({
                "file": pdf_file,
                "error": str(e)
            })
    
    return results 