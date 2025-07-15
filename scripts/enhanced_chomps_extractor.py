import json
import re
import os
import fitz  # PyMuPDF
import pdfplumber
import base64
from io import BytesIO
from PIL import Image
from traceback import format_exc
from typing import Dict, Any, List, Optional
import logging

from dotenv import load_dotenv
from langgraph.graph import START, StateGraph, END
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_chomps_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load API key from .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize the LLM
llm = init_chat_model("openai:gpt-4o")

class EnhancedChOMPSExtractor:
    """Enhanced ChOMPS extractor that handles fillable PDFs, images, and multiple formats"""
    
    def __init__(self):
        self.logger = logger
        
    def extract_pdf_form_fields(self, pdf_path: str) -> Dict[str, Any]:
        """Extract form field data from fillable PDF"""
        self.logger.info("🔍 Extracting form fields from PDF...")
        
        form_data = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get form widgets (fillable fields) - convert generator to list
                widgets = list(page.widgets())  # Convert generator to list
                if widgets:
                    self.logger.info(f"📝 Found {len(widgets)} form fields on page {page_num + 1}")
                    
                    for widget in widgets:
                        field_name = widget.field_name
                        field_value = widget.field_value
                        field_type = widget.field_type
                        
                        # Log all fields for debugging, even empty ones
                        self.logger.info(f"🔍 Field '{field_name}' (type: {field_type}): '{field_value}'")
                        
                        # Include all fields, even if empty, for debugging
                        form_data[field_name] = {
                            "value": field_value,
                            "type": field_type,
                            "page": page_num + 1
                        }
                else:
                    self.logger.info(f"📄 No form fields found on page {page_num + 1}")
            
            doc.close()
            
            if form_data:
                self.logger.info(f"🎉 Successfully extracted {len(form_data)} form fields")
                return {"success": True, "form_fields": form_data, "method": "form_fields"}
            else:
                self.logger.warning("⚠️ No form fields found in the PDF")
                return {"success": False, "form_fields": {}, "method": "form_fields"}
                
        except Exception as e:
            self.logger.error(f"❌ Form field extraction failed: {e}")
            return {"success": False, "error": str(e), "method": "form_fields"}
    
    def extract_with_pdfplumber_enhanced(self, pdf_path: str) -> Dict[str, Any]:
        """Enhanced extraction using pdfplumber with table and text analysis"""
        self.logger.info("🔧 Using pdfplumber for enhanced extraction...")
        
        try:
            extracted_data = {
                "text": "",
                "tables": [],
                "checkboxes": [],
                "form_elements": []
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        extracted_data["text"] += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table and len(table) > 1:  # Valid table
                            extracted_data["tables"].append({
                                "page": page_num + 1,
                                "table_index": table_idx,
                                "data": table
                            })
                            self.logger.info(f"📊 Found table on page {page_num + 1}")
                    
                    # Look for checkbox patterns
                    checkboxes = self._find_checkbox_patterns(page_text or "")
                    if checkboxes:
                        extracted_data["checkboxes"].extend([
                            {"page": page_num + 1, **checkbox} 
                            for checkbox in checkboxes
                        ])
                    
                    # Extract form-like elements
                    form_elements = self._extract_form_elements(page_text or "")
                    if form_elements:
                        extracted_data["form_elements"].extend([
                            {"page": page_num + 1, **element} 
                            for element in form_elements
                        ])
            
            if extracted_data["text"] or extracted_data["tables"] or extracted_data["form_elements"]:
                self.logger.info("✅ pdfplumber extraction successful")
                return {"success": True, "data": extracted_data, "method": "pdfplumber_enhanced"}
            else:
                return {"success": False, "error": "No content extracted", "method": "pdfplumber_enhanced"}
                
        except Exception as e:
            self.logger.error(f"❌ pdfplumber extraction failed: {e}")
            return {"success": False, "error": str(e), "method": "pdfplumber_enhanced"}
    
    def _find_checkbox_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Find checkbox-like patterns in text"""
        checkboxes = []
        
        # Common checkbox patterns
        patterns = [
            r'☐\s*([^☐☑]+?)(?=☐|☑|$)',  # Empty checkbox
            r'☑\s*([^☐☑]+?)(?=☐|☑|$)',  # Checked checkbox
            r'\[\s*\]\s*([^\[\]]+?)(?=\[|$)',  # [ ] checkbox
            r'\[x\]\s*([^\[\]]+?)(?=\[|$)',  # [x] checkbox
            r'\[X\]\s*([^\[\]]+?)(?=\[|$)',  # [X] checkbox
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                checkboxes.append({
                    "type": "checkbox",
                    "text": match.strip(),
                    "checked": "☑" in pattern or "[x]" in pattern.lower()
                })
        
        return checkboxes
    
    def _extract_form_elements(self, text: str) -> List[Dict[str, Any]]:
        """Extract form-like elements from text"""
        elements = []
        
        # Look for numbered items with potential scores
        item_patterns = [
            r'(\d+)\.\s*([^:\n]+?)[:：]\s*([^\n]+)',  # "1. Item: Value"
            r'(\d+)\.\s*([^:\n]+)\s*[-–—]\s*([^\n]+)',  # "1. Item - Value"
            r'(\d+)\.\s*([^\n]+?)\s*\(?([012]|Yes|No|Sometimes|Not Yet)\)?',  # "1. Item (Score)"
        ]
        
        for pattern in item_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match) >= 3:
                    elements.append({
                        "item_number": match[0],
                        "description": match[1].strip(),
                        "value": match[2].strip(),
                        "type": "numbered_item"
                    })
        
        return elements
    
    def convert_pdf_to_images_and_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """Convert PDF pages to images and perform OCR"""
        self.logger.info("🖼️ Converting PDF to images for OCR...")
        
        try:
            doc = fitz.open(pdf_path)
            ocr_results = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                img = Image.open(BytesIO(img_data))
                
                # Encode for OpenAI Vision
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # Use OpenAI Vision for OCR
                ocr_text = self._perform_openai_ocr(img_base64, page_num + 1)
                
                if ocr_text:
                    ocr_results.append({
                        "page": page_num + 1,
                        "text": ocr_text,
                        "method": "openai_vision"
                    })
                    self.logger.info(f"✅ OCR completed for page {page_num + 1}")
            
            doc.close()
            
            if ocr_results:
                return {"success": True, "ocr_results": ocr_results, "method": "pdf_to_image_ocr"}
            else:
                return {"success": False, "error": "No OCR text extracted", "method": "pdf_to_image_ocr"}
                
        except Exception as e:
            self.logger.error(f"❌ PDF to image OCR failed: {e}")
            return {"success": False, "error": str(e), "method": "pdf_to_image_ocr"}
    
    def _perform_openai_ocr(self, image_base64: str, page_number: int) -> str:
        """Perform OCR using OpenAI Vision API"""
        try:
            prompt = f"""
            This is page {page_number} of a ChOMPS (Chicago Oral Motor and Feeding Scale) assessment form.
            
            Please extract ALL text content from this image, including:
            1. All form field labels and their values
            2. Any checked or unchecked boxes with their associated text
            3. Any handwritten or typed entries
            4. Score values (typically 0, 1, or 2)
            5. Item numbers and descriptions
            
            Format the output as clear, structured text that preserves the relationships between items and their scores.
            """
            
            response = llm.invoke([
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}",
                        "detail": "high"
                    }
                }
            ])
            
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI OCR failed for page {page_number}: {e}")
            return ""
    
    def extract_all_methods(self, pdf_path: str) -> Dict[str, Any]:
        """Try all extraction methods and return the best result"""
        self.logger.info("🚀 Starting comprehensive ChOMPS extraction...")
        
        results = {
            "pdf_path": pdf_path,
            "extraction_attempts": [],
            "best_result": None,
            "success": False
        }
        
        # Method 1: Form field extraction
        self.logger.info("Method 1: Form field extraction")
        form_result = self.extract_pdf_form_fields(pdf_path)
        results["extraction_attempts"].append(form_result)
        
        if form_result.get("success") and form_result.get("form_fields"):
            results["best_result"] = form_result
            results["success"] = True
            self.logger.info("✅ Form field extraction successful - using as primary method")
        
        # Method 2: Enhanced pdfplumber
        if not results["success"]:
            self.logger.info("Method 2: Enhanced pdfplumber extraction")
            pdfplumber_result = self.extract_with_pdfplumber_enhanced(pdf_path)
            results["extraction_attempts"].append(pdfplumber_result)
            
            if pdfplumber_result.get("success"):
                results["best_result"] = pdfplumber_result
                results["success"] = True
                self.logger.info("✅ pdfplumber extraction successful")
        
        # Method 3: OCR fallback
        if not results["success"]:
            self.logger.info("Method 3: PDF to image OCR")
            ocr_result = self.convert_pdf_to_images_and_ocr(pdf_path)
            results["extraction_attempts"].append(ocr_result)
            
            if ocr_result.get("success"):
                results["best_result"] = ocr_result
                results["success"] = True
                self.logger.info("✅ OCR extraction successful")
        
        # Save detailed results
        output_file = f"outputs/chomps_extraction_detailed_{os.path.basename(pdf_path)}.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"💾 Detailed results saved to {output_file}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save results: {e}")
        
        if results["success"]:
            self.logger.info("🎉 ChOMPS extraction completed successfully!")
        else:
            self.logger.error("❌ All extraction methods failed")
        
        return results
    
    def parse_extracted_data_to_chomps_structure(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse extracted data into ChOMPS structure"""
        if not extraction_result.get("success"):
            return {"success": False, "error": "No valid extraction data"}
        
        best_result = extraction_result.get("best_result", {})
        method = best_result.get("method", "unknown")
        
        self.logger.info(f"📊 Parsing data from method: {method}")
        
        try:
            if method == "form_fields":
                return self._parse_form_fields(best_result.get("form_fields", {}))
            elif method == "pdfplumber_enhanced":
                return self._parse_pdfplumber_data(best_result.get("data", {}))
            elif method == "pdf_to_image_ocr":
                return self._parse_ocr_data(best_result.get("ocr_results", []))
            else:
                return {"success": False, "error": f"Unknown parsing method: {method}"}
                
        except Exception as e:
            self.logger.error(f"❌ Data parsing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_form_fields(self, form_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse form field data into ChOMPS structure"""
        chomps_data = {
            "patient_info": {},
            "assessment_items": [],
            "domain_scores": {},
            "overall_score": 0,
            "extraction_method": "form_fields"
        }
        
        for field_name, field_info in form_fields.items():
            value = field_info.get("value", "")
            
            # Parse patient information
            if any(keyword in field_name.lower() for keyword in ["name", "patient", "child"]):
                chomps_data["patient_info"]["name"] = value
            elif "date" in field_name.lower():
                chomps_data["patient_info"]["date"] = value
            elif "age" in field_name.lower():
                chomps_data["patient_info"]["age"] = value
            
            # Parse assessment items (look for numbered items or score fields)
            elif re.match(r'item[\s_]*(\d+)', field_name.lower()):
                item_match = re.match(r'item[\s_]*(\d+)', field_name.lower())
                if item_match:
                    item_no = item_match.group(1)
                    chomps_data["assessment_items"].append({
                        "item_no": item_no,
                        "field_name": field_name,
                        "value": value
                    })
        
        self.logger.info(f"✅ Parsed {len(chomps_data['assessment_items'])} assessment items from form fields")
        return {"success": True, "data": chomps_data}
    
    def _parse_pdfplumber_data(self, pdfplumber_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse pdfplumber extracted data"""
        chomps_data = {
            "text_content": pdfplumber_data.get("text", ""),
            "tables": pdfplumber_data.get("tables", []),
            "form_elements": pdfplumber_data.get("form_elements", []),
            "checkboxes": pdfplumber_data.get("checkboxes", []),
            "extraction_method": "pdfplumber_enhanced"
        }
        
        # Use LLM to structure the data
        structured_data = self._llm_structure_chomps_data(chomps_data)
        return {"success": True, "data": structured_data}
    
    def _parse_ocr_data(self, ocr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse OCR extracted data"""
        combined_text = "\n".join([result.get("text", "") for result in ocr_results])
        
        chomps_data = {
            "combined_ocr_text": combined_text,
            "page_results": ocr_results,
            "extraction_method": "ocr"
        }
        
        # Use LLM to structure the data
        structured_data = self._llm_structure_chomps_data(chomps_data)
        return {"success": True, "data": structured_data}
    
    def _llm_structure_chomps_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to structure the raw extracted data into ChOMPS format"""
        
        # Combine all text content
        text_content = ""
        if "text_content" in raw_data:
            text_content += raw_data["text_content"]
        if "combined_ocr_text" in raw_data:
            text_content += raw_data["combined_ocr_text"]
        
        # Add structured elements
        if raw_data.get("form_elements"):
            text_content += "\n\nForm Elements:\n"
            for element in raw_data["form_elements"]:
                text_content += f"Item {element.get('item_number', 'N/A')}: {element.get('description', '')} = {element.get('value', '')}\n"
        
        if raw_data.get("checkboxes"):
            text_content += "\n\nCheckboxes:\n"
            for checkbox in raw_data["checkboxes"]:
                checked = "✓" if checkbox.get("checked") else "○"
                text_content += f"{checked} {checkbox.get('text', '')}\n"
        
        prompt = f"""
        Extract ChOMPS (Chicago Oral Motor and Feeding Scale) assessment data from the following content.
        
        The ChOMPS assessment evaluates feeding and swallowing skills across these domains:
        1. Oral Motor Skills - jaw, lip, tongue movements and coordination
        2. Oral Sensory Skills - sensory processing and responses  
        3. Feeding Behaviors - behavioral responses during feeding
        4. Medical History - relevant medical factors affecting feeding
        5. Nutritional Status - growth, weight gain, and nutritional concerns
        6. Feeding History - developmental feeding milestones and challenges
        
        Extract all scored items with their descriptions and scores.
        Scores are typically: 0 = Not Yet, 1 = Sometimes, 2 = Yes
        
        Return valid JSON in this structure:
        {{
          "patient_info": {{
            "name": "...",
            "date": "...",
            "age": "..."
          }},
          "oral_motor_skills": {{
            "items": [
              {{"item_no": "1", "description": "...", "score": 0}}
            ],
            "total_score": 0,
            "risk_level": "Low/Moderate/High"
          }},
          "oral_sensory_skills": {{
            "items": [...],
            "total_score": 0,
            "risk_level": "Low/Moderate/High"
          }},
          "feeding_behaviors": {{
            "items": [...],
            "total_score": 0,
            "risk_level": "Low/Moderate/High"
          }},
          "medical_history": {{
            "items": [...],
            "total_score": 0,
            "risk_level": "Low/Moderate/High"
          }},
          "nutritional_status": {{
            "items": [...],
            "total_score": 0,
            "risk_level": "Low/Moderate/High"
          }},
          "feeding_history": {{
            "items": [...],
            "total_score": 0,
            "risk_level": "Low/Moderate/High"
          }},
          "overall_assessment": {{
            "total_score": 0,
            "overall_risk_level": "Low/Moderate/High",
            "feeding_safety_concerns": [],
            "recommendations": []
          }}
        }}
        
        Content to analyze:
        {text_content}
        """
        
        try:
            response = llm.invoke(prompt)
            output = response.content.strip().replace("```json", "").replace("```", "")
            
            # Save the LLM output
            with open("outputs/chomps_llm_structured.json", 'w') as f:
                f.write(output)
            
            return json.loads(output)
            
        except Exception as e:
            self.logger.error(f"❌ LLM structuring failed: {e}")
            return {"error": f"LLM structuring failed: {e}"}


def extract_chomps_data_enhanced(pdf_path: str) -> Dict[str, Any]:
    """Main function to extract ChOMPS data using enhanced methods"""
    extractor = EnhancedChOMPSExtractor()
    
    # Extract data using all methods
    extraction_result = extractor.extract_all_methods(pdf_path)
    
    if not extraction_result.get("success"):
        return {
            "success": False,
            "error": "All extraction methods failed",
            "details": extraction_result
        }
    
    # Parse and structure the data
    structured_result = extractor.parse_extracted_data_to_chomps_structure(extraction_result)
    
    if structured_result.get("success"):
        return {
            "success": True,
            "data": structured_result.get("data"),
            "extraction_method": extraction_result.get("best_result", {}).get("method"),
            "extraction_details": extraction_result
        }
    else:
        return {
            "success": False,
            "error": structured_result.get("error"),
            "extraction_details": extraction_result
        }


if __name__ == "__main__":
    # Test with your ChOMPS file
    pdf_path = "assets/inputs/ChOMPS_fillable.pdf"
    
    print("🚀 Starting enhanced ChOMPS extraction...")
    result = extract_chomps_data_enhanced(pdf_path)
    
    if result.get("success"):
        print("✅ Extraction successful!")
        print(f"Method used: {result.get('extraction_method')}")
        
        # Save final result
        with open("outputs/chomps_final_result.json", 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print("💾 Final result saved to outputs/chomps_final_result.json")
    else:
        print("❌ Extraction failed:")
        print(result.get("error"))
        
        # Save error details for debugging
        with open("outputs/chomps_error_details.json", 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print("💾 Error details saved to outputs/chomps_error_details.json") 