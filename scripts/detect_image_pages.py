import asyncio
import base64
from datetime import datetime, timedelta
import io
import json
import logging
import os
import sys
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
import pdfplumber
from PIL import Image
import PyPDF2

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

sys.path.append(PROJECT_DIR.__str__())
print(sys.path)

from backend.common.logging import logging
from langgraph_ocr_agent import LangGraphOCRAgent

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
    logger.info("✅ pdfplumber library imported successfully")
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("⚠️ pdfplumber not available - install with: pip install pdfplumber")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
    logger.info("✅ PyPDF2 library imported successfully")
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("⚠️ PyPDF2 not available - install with: pip install PyPDF2")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    logger.info("✅ PyMuPDF library imported successfully")
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("⚠️ PyMuPDF not available - install with: pip install PyMuPDF")


class EnhancedPDFProcessor:
    """Enhanced PDF processor for multiple pediatric assessment types"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("📄 Initializing Enhanced PDF Processor...")
        
        if not PDFPLUMBER_AVAILABLE and not PYPDF2_AVAILABLE:
            self.logger.error("❌ No PDF processing libraries available")
            raise ImportError("Either pdfplumber or PyPDF2 must be installed")
        
        self.logger.info(f"📚 Available PDF libraries: pdfplumber={PDFPLUMBER_AVAILABLE}, PyPDF2={PYPDF2_AVAILABLE}")
        
        # Initialize extraction patterns
        self._setup_extraction_patterns()
        
        # Initialize LangGraph OCR agent
        self.ocr_agent = LangGraphOCRAgent()
        
        self.logger.info("✅ PDF extraction patterns configured")
        self.logger.info("🤖 LangGraph OCR Agent initialized")
    
    def _setup_extraction_patterns(self):
        """Setup regex patterns for data extraction"""
        self.logger.info("🔧 Setting up extraction patterns...")
        
        # Score patterns
        self.score_patterns = {
            'scaled_score': r'Scaled Score[:\s]+(\d+)',
            'composite_score': r'Composite Score[:\s]+(\d+)',
            'percentile': r'Percentile[:\s]+(\d+)',
            'age_equivalent': r'Age Equivalent[:\s]+(\d+:\d+)',
            'standard_score': r'Standard Score[:\s]+(\d+)'
        }
        
        # Assessment-specific patterns
        self.assessment_patterns = {
            'bayley4': {
                'cognitive': r'Cognitive.*?(\d+)',
                'language': r'Language.*?(\d+)',
                'motor': r'Motor.*?(\d+)',
                'social_emotional': r'Social.*?Emotional.*?(\d+)',
                'adaptive': r'Adaptive.*?(\d+)'
            },
            'sp2': {
                'seeking': r'Seeking.*?(\d+)',
                'avoiding': r'Avoiding.*?(\d+)',
                'sensitivity': r'Sensitivity.*?(\d+)',
                'registration': r'Registration.*?(\d+)'
            }
        }
        
        self.logger.info(f"✅ Configured {len(self.score_patterns)} score patterns")
        self.logger.info(f"✅ Configured {len(self.assessment_patterns)} assessment patterns")
    
    def calculate_chronological_age(self, date_of_birth: datetime, encounter_date: datetime) -> Dict[str, Any]:
        """Calculate chronological age in years, months, and days"""
        age_delta = encounter_date - date_of_birth
        
        # Calculate years
        years = age_delta.days // 365
        remaining_days = age_delta.days % 365
        
        # Calculate months (approximate)
        months = remaining_days // 30
        days = remaining_days % 30
        
        # Total months for assessment calculations
        total_months = (years * 12) + months
        
        return {
            "years": years,
            "months": months,
            "days": days,
            "total_months": total_months,
            "formatted": f"{years} years, {months} months, {days} days"
        }
    
    async def process_multiple_assessments(self, uploaded_files: Dict[str, str]) -> Dict[str, Any]:
        """Process multiple assessment PDFs and extract data from each"""
        self.logger.info(f"🔄 Starting processing of {len(uploaded_files)} assessment files")
        
        extracted_data = {}
        
        for assessment_type, file_path in uploaded_files.items():
            self.logger.info(f"📋 Processing {assessment_type}: {os.path.basename(file_path)}")
            
            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    self.logger.error(f"❌ File not found: {file_path}")
                    continue
                
                # Get file size for logging
                file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                self.logger.info(f"📁 File size: {file_size:.2f} MB")
                
                # Extract text from PDF
                text_content = await self.extract_text_from_pdf(file_path)
                
                if not text_content:
                    self.logger.warning(f"⚠️ No text extracted from {assessment_type}")
                    continue
                
                self.logger.info(f"📝 Extracted {len(text_content)} characters from {assessment_type}")
                
                # Process based on assessment type
                if assessment_type in ['bayley4_cognitive', 'bayley4_social']:
                    data = await self._extract_bayley4_data(text_content, assessment_type)
                elif assessment_type == 'sp2':
                    data = await self._extract_sp2_data(text_content)
                elif assessment_type == 'chomps':
                    data = await self._extract_chomps_data(text_content)
                elif assessment_type == 'pedieat':
                    data = await self._extract_pedieat_data(text_content)
                elif assessment_type == 'facesheet':
                    data = await self._extract_facesheet_data(text_content)
                elif assessment_type == 'clinical_notes':
                    data = await self._extract_clinical_notes(text_content)
                else:
                    self.logger.warning(f"⚠️ Unknown assessment type: {assessment_type}")
                    data = {"raw_text": text_content}
                
                if data:
                    extracted_data[assessment_type] = data
                    self.logger.info(f"✅ Successfully processed {assessment_type}")
                else:
                    self.logger.warning(f"⚠️ No structured data extracted from {assessment_type}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing {assessment_type}: {e}")
                continue
        
        self.logger.info(f"🎉 Completed processing: {len(extracted_data)}/{len(uploaded_files)} files successful")
        return extracted_data
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using available libraries"""
        self.logger.info(f"📖 Extracting text from: {os.path.basename(file_path)}")
        
        text_content = ""
        
        # Try pdfplumber first
        if PDFPLUMBER_AVAILABLE:
            try:
                self.logger.info("🔧 Using pdfplumber for text extraction")
                text_content = await self._extract_with_pdfplumber(file_path)
                if text_content:
                    self.logger.info(f"✅ pdfplumber extraction successful ({len(text_content)} characters)")
                    return text_content
            except Exception as e:
                self.logger.warning(f"⚠️ pdfplumber extraction failed: {e}")
        
        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                self.logger.info("🔧 Using PyPDF2 for text extraction")
                text_content = await self._extract_with_pypdf2(file_path)
                if text_content:
                    self.logger.info(f"✅ PyPDF2 extraction successful ({len(text_content)} characters)")
                    return text_content
            except Exception as e:
                self.logger.warning(f"⚠️ PyPDF2 extraction failed: {e}")
        
        self.logger.error(f"❌ Failed to extract text from {file_path}")
        return ""
    
    async def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber"""
        text_content = ""
        page_count = 0
        
        try:
            with pdfplumber.open(file_path) as pdf:
                self.logger.info(f"📄 PDF has {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                            page_count += 1
                        else:
                            self.logger.warning(f"⚠️ No text on page {page_num}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error extracting page {page_num}: {e}")
                
                self.logger.info(f"✅ Extracted text from {page_count}/{len(pdf.pages)} pages")
                
        except Exception as e:
            self.logger.error(f"❌ pdfplumber extraction error: {e}")
            raise
        
        return text_content
    
    async def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2"""
        text_content = ""
        page_count = 0
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                self.logger.info(f"📄 PDF has {total_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                            page_count += 1
                        else:
                            self.logger.warning(f"⚠️ No text on page {page_num}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error extracting page {page_num}: {e}")
                
                self.logger.info(f"✅ Extracted text from {page_count}/{total_pages} pages")
                
        except Exception as e:
            self.logger.error(f"❌ PyPDF2 extraction error: {e}")
            raise
        
        return text_content
    
    async def _extract_facesheet_data(self, text_content: str) -> Dict[str, Any]:
        """Extract patient demographics and basic information from facesheet"""
        
        data = {
            "report_type": "facesheet",
            "patient_info": {},
            "insurance_info": {},
            "contact_info": {},
            "referral_info": {}
        }
        
        # Extract patient demographics
        patterns = {
            "name": [r"Name[:\s]+([^\n\r]+)", r"Patient[:\s]+([^\n\r]+)", r"Child[:\s]+([^\n\r]+)"],
            "dob": [r"(?:Date of Birth|DOB|Born)[:\s]+([^\n\r]+)"],
            "age": [r"Age[:\s]+([^\n\r]+)"],
            "sex": [r"(?:Sex|Gender)[:\s]+([^\n\r]+)"],
            "language": [r"Language[:\s]+([^\n\r]+)"],
            "uci_number": [r"(?:UCI|ID|Medical Record)[:\s#]*([^\n\r]+)"],
            "parent_guardian": [r"(?:Parent|Guardian|Mother|Father)[:\s]+([^\n\r]+)"],
            "address": [r"Address[:\s]+([^\n\r]+(?:\n[^\n\r]+)*)"],
            "phone": [r"(?:Phone|Tel|Telephone)[:\s]+([^\n\r]+)"],
            "insurance": [r"Insurance[:\s]+([^\n\r]+)"]
        }
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data["patient_info"][field] = match.group(1).strip()
                    break
        
        return data
    
    async def _extract_bayley4_data(self, text_content: str, assessment_type: str) -> Dict[str, Any]:
        """Extract Bayley-4 assessment data with enhanced pattern recognition"""
        self.logger.info(f"🔍 Extracting Bayley-4 data from {assessment_type}")
        
        data = {
            "report_type": assessment_type,
            "patient_info": {},
            "raw_scores": {},
            "scaled_scores": {},
            "composite_scores": {},
            "percentiles": {},
            "age_equivalents": {},
            "interpretations": {},
            "clinical_observations": [],
            "strengths": [],
            "needs": [],
            "recommendations": []
        }
        
        # Extract patient information first
        patient_patterns = {
            "name": [r"Name:\s*([^\n\r]+)", r"Examinee.*?Name:\s*([^\n\r]+)"],
            "birth_date": [r"Birth Date:\s*([^\n\r]+)", r"Date of Birth:\s*([^\n\r]+)"],
            "test_date": [r"Test Date:\s*([^\n\r]+)"],
            "test_age": [r"Test Age.*?(\d+:\d+)", r"Chronological Age.*?(\d+ Months)"],
            "examiner": [r"Examiner Name:\s*([^\n\r]+)"],
            "gender": [r"Gender:\s*([^\n\r]+)"]
        }
        
        for field, patterns in patient_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data["patient_info"][field] = match.group(1).strip()
                    self.logger.info(f"✅ Extracted {field}: {match.group(1).strip()}")
                    break
        
        if "cognitive" in assessment_type:
            # Extract cognitive, language, and motor domains
            domains = {
                "Cognitive": ["CG", "Cognitive"],
                "Receptive Communication": ["RC", "Receptive"],
                "Expressive Communication": ["EC", "Expressive"],
                "Fine Motor": ["FM", "Fine Motor"],
                "Gross Motor": ["GM", "Gross Motor"]
            }
            
            composite_domains = {
                "Cognitive Composite": ["Cognitive"],
                "Language Composite": ["Language"],
                "Motor Composite": ["Motor"]
            }
            
        else:  # social-emotional
            domains = {
                "Social-Emotional": ["SE", "Social-Emotional"],
                "Self-Control": ["Self-Control"],
                "Compliance": ["Compliance"],
                "Communication": ["Communication"],
                "Community Use": ["Community"],
                "Functional Pre-Academics": ["Pre-Academics"],
                "Home Living": ["Home Living"],
                "Health and Safety": ["Health"],
                "Leisure": ["Leisure"],
                "Self-Care": ["Self-Care"],
                "Self-Direction": ["Self-Direction"],
                "Social": ["Social"],
                "Motor": ["Motor"]
            }
            
            composite_domains = {
                "Social-Emotional Composite": ["Social-Emotional"],
                "Adaptive Behavior Composite": ["Adaptive"]
            }
        
        # Enhanced score extraction patterns
        score_table_patterns = [
            # Look for score tables with specific format
            r"(\w+(?:\s+\w+)*)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+:\d+)",  # Domain Raw Scaled Percentile Age
            r"(\w+(?:\s+\w+)*)\s+(\d+)\s+(\d+)\s+(\d+)",  # Domain Raw Scaled Percentile
            # Look for individual score lines
            r"(\w+(?:\s+\w+)*)[:\s]+.*?(\d+)[^\d]*(\d+)[^\d]*(\d+)",
        ]
        
        # Extract scores using multiple patterns
        self.logger.info("🔍 Searching for score patterns...")
        scores_found = 0
        
        for domain_name, aliases in domains.items():
            for alias in aliases:
                # Try different score extraction patterns
                patterns = [
                    rf"{alias}[:\s]+.*?Raw Score[:\s]*(\d+).*?Scaled Score[:\s]*(\d+)",
                    rf"{alias}[:\s]+.*?(\d+)[^\d]+(\d+)[^\d]+(\d+)",
                    rf"({alias})\s+(\d+)\s+(\d+)\s+(\d+)"
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, text_content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        if len(match.groups()) >= 3:
                            try:
                                raw_score = int(match.group(2)) if match.group(2).isdigit() else None
                                scaled_score = int(match.group(3)) if match.group(3).isdigit() else None
                                percentile = int(match.group(4)) if len(match.groups()) > 3 and match.group(4) and match.group(4).isdigit() else None
                                
                                if raw_score:
                                    data["raw_scores"][domain_name] = raw_score
                                    scores_found += 1
                                    self.logger.info(f"✅ {domain_name} Raw Score: {raw_score}")
                                
                                if scaled_score:
                                    data["scaled_scores"][domain_name] = scaled_score
                                    self.logger.info(f"✅ {domain_name} Scaled Score: {scaled_score}")
                                
                                if percentile:
                                    data["percentiles"][domain_name] = percentile
                                    self.logger.info(f"✅ {domain_name} Percentile: {percentile}")
                                
                                break
                            except (ValueError, IndexError) as e:
                                self.logger.warning(f"⚠️ Error parsing scores for {domain_name}: {e}")
        
        # Extract composite scores
        for composite, aliases in composite_domains.items():
            for alias in aliases:
                patterns = [
                    rf"{alias}\s+Composite[:\s]*(\d+)",
                    rf"{alias}[:\s]+.*?(\d+)",
                    rf"Composite.*?{alias}.*?(\d+)"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        try:
                            score = int(match.group(1))
                            data["composite_scores"][composite] = score
                            data["interpretations"][composite] = self._interpret_composite_score(score)
                            self.logger.info(f"✅ {composite}: {score}")
                            break
                        except (ValueError, IndexError):
                            continue
        
        # If no scores found, try alternative extraction methods
        if scores_found == 0:
            self.logger.warning("⚠️ No scores found with standard patterns, trying alternative extraction...")
            data = await self._extract_bayley4_alternative(text_content, assessment_type)
        
        self.logger.info(f"📊 Total scores extracted: {scores_found}")
        self.logger.info(f"📋 Raw scores: {len(data['raw_scores'])}")
        self.logger.info(f"📋 Scaled scores: {len(data['scaled_scores'])}")
        self.logger.info(f"📋 Composite scores: {len(data['composite_scores'])}")
        
        return data
    
    async def _extract_bayley4_alternative(self, text_content: str, assessment_type: str) -> Dict[str, Any]:
        """Alternative Bayley-4 extraction method for complex layouts"""
        self.logger.info("🔄 Using alternative Bayley-4 extraction method...")
        
        data = {
            "report_type": assessment_type,
            "raw_scores": {},
            "scaled_scores": {},
            "composite_scores": {},
            "percentiles": {},
            "age_equivalents": {},
            "interpretations": {},
            "clinical_observations": [],
            "patient_info": {}
        }
        
        # Extract all numbers in sequence and try to map them to domains
        lines = text_content.split('\n')
        score_lines = []
        
        for line in lines:
            # Look for lines that might contain scores
            if re.search(r'\d+\s+\d+\s+\d+', line):
                score_lines.append(line.strip())
        
        self.logger.info(f"🔍 Found {len(score_lines)} potential score lines")
        
        # Try to extract specific score table data
        table_pattern = r'(\w+(?:\s+\w+)*)\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+:\d+))?'
        
        for line in score_lines:
            match = re.match(table_pattern, line)
            if match:
                domain = match.group(1)
                raw_score = int(match.group(2))
                scaled_score = int(match.group(3))
                percentile = int(match.group(4))
                age_equiv = match.group(5) if match.group(5) else None
                
                data["raw_scores"][domain] = raw_score
                data["scaled_scores"][domain] = scaled_score
                data["percentiles"][domain] = percentile
                if age_equiv:
                    data["age_equivalents"][domain] = age_equiv
                
                self.logger.info(f"✅ Alternative extraction - {domain}: {raw_score}/{scaled_score}/{percentile}")
        
        return data
    
    async def _extract_sp2_data(self, text_content: str) -> Dict[str, Any]:
        """Extract Sensory Profile 2 data"""
        
        data = {
            "report_type": "sp2",
            "quadrant_scores": {},
            "sensory_processing": {},
            "behavioral_responses": {},
            "interpretations": {},
            "clinical_implications": []
        }
        
        # Extract SP2 quadrant scores
        quadrants = ["Seeking", "Avoiding", "Sensitivity", "Registration"]
        
        for quadrant in quadrants:
            # Look for raw scores and classifications
            score_pattern = rf"{quadrant}.*?(\d+).*?(Much (?:More|Less) Than Most|More Than Most|Less Than Most|Typical Performance)"
            match = re.search(score_pattern, text_content, re.IGNORECASE | re.DOTALL)
            if match:
                data["quadrant_scores"][quadrant] = {
                    "raw_score": int(match.group(1)),
                    "classification": match.group(2),
                    "interpretation": self._interpret_sp2_score(quadrant, match.group(2))
                }
        
        # Extract behavioral implications
        data["clinical_implications"] = self._extract_sp2_implications(text_content)
        
        return data
    
    async def _extract_chomps_data(self, text_content: str) -> Dict[str, Any]:
        """Extract ChOMPS feeding assessment data"""
        
        data = {
            "report_type": "chomps",
            "domain_scores": {},
            "risk_levels": {},
            "feeding_concerns": [],
            "safety_issues": [],
            "recommendations": []
        }
        
        # ChOMPS domains
        domains = [
            "Sensory", "Motor", "Behavioral", "Medical", 
            "Nutritional", "Feeding History"
        ]
        
        for domain in domains:
            # Extract domain scores and risk levels
            domain_pattern = rf"{domain}.*?Score[:\s]*(\d+).*?Risk[:\s]*(Low|Moderate|High)"
            match = re.search(domain_pattern, text_content, re.IGNORECASE | re.DOTALL)
            if match:
                score = int(match.group(1))
                risk = match.group(2)
                data["domain_scores"][domain] = score
                data["risk_levels"][domain] = risk
        
        # Extract feeding concerns
        data["feeding_concerns"] = self._extract_feeding_concerns(text_content)
        data["safety_issues"] = self._extract_safety_concerns(text_content)
        
        return data
    
    async def _extract_pedieat_data(self, text_content: str) -> Dict[str, Any]:
        """Extract PediEAT assessment data"""
        
        data = {
            "report_type": "pedieat",
            "domain_scores": {},
            "symptom_levels": {},
            "feeding_behaviors": [],
            "safety_concerns": [],
            "endurance_issues": []
        }
        
        # PediEAT domains
        domains = [
            "Physiology", "Processing", "Mealtime Behavior", "Selectivity"
        ]
        
        for domain in domains:
            # Extract T-scores and symptom levels
            score_pattern = rf"{domain}.*?T-Score[:\s]*(\d+)"
            level_pattern = rf"{domain}.*?(?:Elevated|Typical|Atypical)"
            
            score_match = re.search(score_pattern, text_content, re.IGNORECASE)
            level_match = re.search(level_pattern, text_content, re.IGNORECASE)
            
            if score_match:
                data["domain_scores"][domain] = int(score_match.group(1))
            if level_match:
                data["symptom_levels"][domain] = level_match.group(0)
        
        return data
    
    async def _extract_clinical_notes(self, text_content: str) -> Dict[str, Any]:
        """Extract and process clinical observations and notes"""
        
        data = {
            "report_type": "clinical_notes",
            "raw_observations": [],
            "narrative_observations": [],
            "bullet_points": [],
            "converted_narratives": []
        }
        
        # Extract bullet points
        bullet_points = self._extract_bullet_points(text_content)
        data["bullet_points"] = bullet_points
        
        # Convert bullet points to narrative
        data["converted_narratives"] = [
            self._convert_bullet_to_narrative(bullet) for bullet in bullet_points
        ]
        
        # Extract structured observations
        data["raw_observations"] = self._extract_structured_observations(text_content)
        
        return data
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet point observations from text"""
        bullet_patterns = [
            r"[-•*]\s+([^.\n]+\.?)",
            r"^\s*-\s+(.+)$",
            r"^\s*•\s+(.+)$",
            r"^\s*\*\s+(.+)$"
        ]
        
        bullet_points = []
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            bullet_points.extend([match.strip() for match in matches])
        
        return bullet_points
    
    def _convert_bullet_to_narrative(self, bullet_point: str) -> str:
        """Convert bullet point observations to professional narrative format"""
        
        # Common bullet-to-narrative conversions
        conversions = {
            r"overstuffed mouth": "overstuffed his/her mouth",
            r"gagged several times": "gagged in response to large bolus sizes",
            r"used both hands": "used both hands during self-feeding, demonstrating",
            r"limited oral control": "but showed limited oral motor control",
            r"refused": "demonstrated refusal behaviors when presented with",
            r"required (\w+) assistance": r"required \1 level of assistance",
            r"appeared (\w+)": r"appeared \1 throughout the session"
        }
        
        narrative = bullet_point.lower()
        
        # Apply conversions
        for pattern, replacement in conversions.items():
            narrative = re.sub(pattern, replacement, narrative, flags=re.IGNORECASE)
        
        # Ensure proper sentence structure
        if not narrative.endswith('.'):
            narrative += '.'
        
        # Capitalize first letter
        narrative = narrative[0].upper() + narrative[1:] if narrative else ""
        
        return f"Child {narrative}"
    
    def _interpret_composite_score(self, score: int) -> Dict[str, str]:
        """Interpret Bayley-4 composite scores"""
        if score >= 130:
            classification = "Very Superior"
            range_desc = "Well above average"
        elif score >= 120:
            classification = "Superior"
            range_desc = "Above average"
        elif score >= 110:
            classification = "High Average"
            range_desc = "Slightly above average"
        elif score >= 90:
            classification = "Average"
            range_desc = "Within normal limits"
        elif score >= 80:
            classification = "Low Average"
            range_desc = "Slightly below average"
        elif score >= 70:
            classification = "Below Average"
            range_desc = "Below average, may indicate delay"
        else:
            classification = "Extremely Low"
            range_desc = "Significantly below average, indicates significant delay"
        
        percentile = self._score_to_percentile(score)
        
        return {
            "classification": classification,
            "range_description": range_desc,
            "percentile": percentile,
            "clinical_significance": self._get_clinical_significance(score)
        }
    
    def _interpret_sp2_score(self, quadrant: str, classification: str) -> str:
        """Interpret SP2 quadrant scores"""
        interpretations = {
            "Seeking": {
                "Much More Than Most": "Significantly increased sensory seeking behaviors affecting daily functioning",
                "More Than Most": "Elevated sensory seeking that may impact activities",
                "Typical Performance": "Age-appropriate sensory seeking behaviors",
                "Less Than Most": "Reduced sensory seeking, may appear passive",
                "Much Less Than Most": "Significantly reduced sensory seeking affecting engagement"
            },
            "Avoiding": {
                "Much More Than Most": "Significant sensory avoidance impacting participation",
                "More Than Most": "Elevated avoidance behaviors affecting activities",
                "Typical Performance": "Age-appropriate sensory tolerance",
                "Less Than Most": "Reduced avoidance, may seek out intense sensations",
                "Much Less Than Most": "Minimal avoidance behaviors, may have safety concerns"
            }
            # Add other quadrants as needed
        }
        
        return interpretations.get(quadrant, {}).get(classification, "Interpretation needed")
    
    def _score_to_percentile(self, standard_score: int) -> int:
        """Convert standard score to percentile"""
        if standard_score >= 130:
            return 98
        elif standard_score >= 120:
            return 91
        elif standard_score >= 110:
            return 75
        elif standard_score >= 100:
            return 50
        elif standard_score >= 90:
            return 25
        elif standard_score >= 80:
            return 9
        elif standard_score >= 70:
            return 2
        else:
            return 1
    
    def _get_clinical_significance(self, score: int) -> str:
        """Get clinical significance of score"""
        if score < 70:
            return "Significant delay requiring intervention"
        elif score < 85:
            return "Mild delay, monitor and consider support"
        elif score >= 90:
            return "Within normal limits"
        else:
            return "Borderline, continue monitoring"
    
    # Additional helper methods for extracting specific content sections
    def _extract_clinical_observations(self, text: str) -> List[str]:
        """Extract clinical observations from text"""
        observations = []
        
        # Pattern for observation sections
        obs_patterns = [
            r"Clinical Observations?[:\s]*([^\.]+\.[^\.]*\.)",
            r"Behavior[:\s]*([^\.]+\.[^\.]*\.)",
            r"Observed[:\s]*([^\.]+\.)"
        ]
        
        for pattern in obs_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            observations.extend([obs.strip() for obs in matches])
        
        return observations
    
    def _extract_strengths(self, text: str) -> List[str]:
        """Extract strengths from report"""
        return self._extract_section_content(text, ["Strengths?", "Areas? of Strength"])
    
    def _extract_needs(self, text: str) -> List[str]:
        """Extract areas of need from report"""
        return self._extract_section_content(text, ["Areas? of (?:Need|Concern)", "Weaknesses?", "Challenges?"])
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from report"""
        return self._extract_section_content(text, ["Recommendations?", "Suggest", "Recommend"])
    
    def _extract_section_content(self, text: str, section_headers: List[str]) -> List[str]:
        """Generic method to extract content from specific sections"""
        content = []
        
        for header in section_headers:
            pattern = rf"{header}[:\s]*([^\.]+\.[^\.]*\.)"
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            content.extend([match.strip() for match in matches])
        
        return content
    
    def _extract_sp2_implications(self, text: str) -> List[str]:
        """Extract clinical implications from SP2"""
        implications = []
        
        # Look for implication sections
        impl_patterns = [
            r"Implications?[:\s]*([^\.]+\.)",
            r"Impact on[:\s]*([^\.]+\.)",
            r"Affects?[:\s]*([^\.]+\.)"
        ]
        
        for pattern in impl_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            implications.extend([impl.strip() for impl in matches])
        
        return implications
    
    def _extract_feeding_concerns(self, text: str) -> List[str]:
        """Extract feeding concerns from ChOMPS"""
        concerns = []
        
        concern_keywords = [
            "choking", "gagging", "aspiration", "coughing", 
            "difficulty swallowing", "oral motor", "texture"
        ]
        
        for keyword in concern_keywords:
            pattern = rf"([^\.]*{keyword}[^\.]*\.)"
            matches = re.findall(pattern, text, re.IGNORECASE)
            concerns.extend([concern.strip() for concern in matches])
        
        return concerns
    
    def _extract_safety_concerns(self, text: str) -> List[str]:
        """Extract safety concerns from assessments"""
        safety_concerns = []
        
        safety_keywords = [
            "aspiration risk", "choking risk", "unsafe", "danger",
            "requires supervision", "modified consistency"
        ]
        
        for keyword in safety_keywords:
            pattern = rf"([^\.]*{keyword}[^\.]*\.)"
            matches = re.findall(pattern, text, re.IGNORECASE)
            safety_concerns.extend([concern.strip() for concern in matches])
        
        return safety_concerns
    
    def _extract_structured_observations(self, text: str) -> List[Dict[str, str]]:
        """Extract structured clinical observations"""
        observations = []
        
        # Pattern for structured observations
        obs_pattern = r"(\w+(?:\s+\w+)*)[:\s]*([^\.]+\.)"
        matches = re.findall(obs_pattern, text)
        
        for category, observation in matches:
            if len(observation.split()) > 3:  # Filter out short/irrelevant matches
                observations.append({
                    "category": category.strip(),
                    "observation": observation.strip()
                })
        
        return observations


    async def analyze_pdf_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF structure including images and page sizes"""
        self.logger.info(f"🔍 Analyzing PDF structure: {os.path.basename(file_path)}")
        
        analysis = {
            "file_path": file_path,
            "has_images": False,
            "has_a4_pages": False,
            "total_pages": 0,
            "images_found": 0,
            "a4_pages_count": 0,
            "page_sizes": [],
            "image_details": [],
            "non_a4_pages": []
        }
        
        try:
            # Use PyMuPDF for comprehensive analysis
            if PYMUPDF_AVAILABLE:
                analysis.update(await self._analyze_with_pymupdf(file_path))
            else:
                # Fallback to pdfplumber for basic page size detection
                analysis.update(await self._analyze_with_pdfplumber(file_path))
            
            # Summary
            analysis["has_images"] = analysis["images_found"] > 0
            analysis["has_a4_pages"] = analysis["a4_pages_count"] > 0
            
            self.logger.info(f"📊 Analysis complete: {analysis['images_found']} images, {analysis['a4_pages_count']}/{analysis['total_pages']} A4 pages")
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing PDF structure: {e}")
            analysis["error"] = str(e)
        
        return analysis

    async def _analyze_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF using PyMuPDF (most comprehensive)"""
        analysis = {
            "total_pages": 0,
            "images_found": 0,
            "a4_pages_count": 0,
            "page_sizes": [],
            "image_details": [],
            "non_a4_pages": []
        }
        
        # A4 dimensions in points (72 points per inch)
        A4_WIDTH = 595.276  # 8.27 inches
        A4_HEIGHT = 841.890  # 11.69 inches
        TOLERANCE = 10  # tolerance for A4 detection
        
        try:
            doc = fitz.open(file_path)
            analysis["total_pages"] = len(doc)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get page dimensions
                rect = page.rect
                width, height = rect.width, rect.height
                
                # Check if page is A4 (portrait or landscape)
                is_a4_portrait = (
                    abs(width - A4_WIDTH) <= TOLERANCE and 
                    abs(height - A4_HEIGHT) <= TOLERANCE
                )
                is_a4_landscape = (
                    abs(width - A4_HEIGHT) <= TOLERANCE and 
                    abs(height - A4_WIDTH) <= TOLERANCE
                )
                
                page_info = {
                    "page_number": page_num + 1,
                    "width": width,
                    "height": height,
                    "is_a4": is_a4_portrait or is_a4_landscape,
                    "orientation": "portrait" if is_a4_portrait else ("landscape" if is_a4_landscape else "custom")
                }
                
                analysis["page_sizes"].append(page_info)
                
                if page_info["is_a4"]:
                    analysis["a4_pages_count"] += 1
                else:
                    analysis["non_a4_pages"].append(page_info)
                
                # Detect images on this page
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image details
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Get image dimensions
                        img_pil = Image.open(io.BytesIO(image_bytes))
                        img_width, img_height = img_pil.size
                        
                        image_detail = {
                            "page_number": page_num + 1,
                            "image_index": img_index + 1,
                            "width": img_width,
                            "height": img_height,
                            "format": image_ext.upper(),
                            "size_bytes": len(image_bytes),
                            "xref": xref
                        }
                        
                        analysis["image_details"].append(image_detail)
                        analysis["images_found"] += 1
                        
                        self.logger.info(f"🖼️ Found image on page {page_num + 1}: {img_width}x{img_height} {image_ext.upper()}")
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error processing image {img_index + 1} on page {page_num + 1}: {e}")
            
            doc.close()
            
        except Exception as e:
            self.logger.error(f"❌ PyMuPDF analysis failed: {e}")
            raise
        
        return analysis

    async def _analyze_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF using pdfplumber (fallback for page sizes only)"""
        analysis = {
            "total_pages": 0,
            "images_found": 0,
            "a4_pages_count": 0,
            "page_sizes": [],
            "image_details": [],
            "non_a4_pages": []
        }
        
        # A4 dimensions in points
        A4_WIDTH = 595.276
        A4_HEIGHT = 841.890
        TOLERANCE = 10
        
        try:
            with pdfplumber.open(file_path) as pdf:
                analysis["total_pages"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    width = page.width
                    height = page.height
                    
                    # Check if page is A4
                    is_a4_portrait = (
                        abs(width - A4_WIDTH) <= TOLERANCE and 
                        abs(height - A4_HEIGHT) <= TOLERANCE
                    )
                    is_a4_landscape = (
                        abs(width - A4_HEIGHT) <= TOLERANCE and 
                        abs(height - A4_WIDTH) <= TOLERANCE
                    )
                    
                    page_info = {
                        "page_number": page_num + 1,
                        "width": width,
                        "height": height,
                        "is_a4": is_a4_portrait or is_a4_landscape,
                        "orientation": "portrait" if is_a4_portrait else ("landscape" if is_a4_landscape else "custom")
                    }
                    
                    analysis["page_sizes"].append(page_info)
                    
                    if page_info["is_a4"]:
                        analysis["a4_pages_count"] += 1
                    else:
                        analysis["non_a4_pages"].append(page_info)
                    
                    # Basic image detection using pdfplumber
                    try:
                        images = page.images
                        if images:
                            analysis["images_found"] += len(images)
                            for img_index, img in enumerate(images):
                                image_detail = {
                                    "page_number": page_num + 1,
                                    "image_index": img_index + 1,
                                    "width": img.get('width', 'unknown'),
                                    "height": img.get('height', 'unknown'),
                                    "format": "unknown",
                                    "size_bytes": "unknown",
                                    "detected_by": "pdfplumber"
                                }
                                analysis["image_details"].append(image_detail)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error detecting images on page {page_num + 1}: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ pdfplumber analysis failed: {e}")
            raise
        
        return analysis

    async def check_pdf_has_images(self, file_path: str) -> bool:
        """Quick check if PDF contains images"""
        self.logger.info(f"🔍 Quick image check: {os.path.basename(file_path)}")
        
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    if page.get_images():
                        doc.close()
                        self.logger.info("✅ Images found in PDF")
                        return True
                doc.close()
                self.logger.info("❌ No images found in PDF")
                return False
            else:
                # Fallback to pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        if page.images:
                            self.logger.info("✅ Images found in PDF")
                            return True
                    self.logger.info("❌ No images found in PDF")
                    return False
        except Exception as e:
            self.logger.error(f"❌ Error checking for images: {e}")
            return False

    async def check_pdf_has_a4_pages(self, file_path: str) -> bool:
        """Quick check if PDF has A4 pages"""
        self.logger.info(f"📏 Quick A4 check: {os.path.basename(file_path)}")
        
        # A4 dimensions in points
        A4_WIDTH = 595.276
        A4_HEIGHT = 841.890
        TOLERANCE = 10
        
        try:
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        width, height = page.width, page.height
                        
                        is_a4_portrait = (
                            abs(width - A4_WIDTH) <= TOLERANCE and 
                            abs(height - A4_HEIGHT) <= TOLERANCE
                        )
                        is_a4_landscape = (
                            abs(width - A4_HEIGHT) <= TOLERANCE and 
                            abs(height - A4_WIDTH) <= TOLERANCE
                        )
                        
                        if is_a4_portrait or is_a4_landscape:
                            self.logger.info("✅ A4 pages found in PDF")
                            return True
                    
                    self.logger.info("❌ No A4 pages found in PDF")
                    return False
            else:
                self.logger.warning("⚠️ Cannot check A4 pages without pdfplumber")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error checking for A4 pages: {e}")
            return False

    async def get_pdf_summary(self, file_path: str) -> Dict[str, Any]:
        """Get a complete summary of PDF characteristics"""
        self.logger.info(f"📋 Getting PDF summary: {os.path.basename(file_path)}")
        
        # Get full analysis
        analysis = await self.analyze_pdf_structure(file_path)
        
        # Create summary
        summary = {
            "filename": os.path.basename(file_path),
            "total_pages": analysis["total_pages"],
            "has_images": analysis["has_images"],
            "images_count": analysis["images_found"],
            "has_a4_pages": analysis["has_a4_pages"],
            "a4_pages_count": analysis["a4_pages_count"],
            "a4_percentage": (analysis["a4_pages_count"] / analysis["total_pages"] * 100) if analysis["total_pages"] > 0 else 0,
            "page_formats": self._summarize_page_formats(analysis["page_sizes"]),
            "image_formats": self._summarize_image_formats(analysis["image_details"]),
            "recommendations": self._generate_recommendations(analysis)
        }
        
        self.logger.info(f"📊 PDF Summary: {summary['images_count']} images, {summary['a4_percentage']:.1f}% A4 pages")
        
        return summary

    def _summarize_page_formats(self, page_sizes: List[Dict]) -> Dict[str, int]:
        """Summarize page format distribution"""
        formats = {}
        for page in page_sizes:
            if page["is_a4"]:
                orientation = page["orientation"]
                key = f"A4_{orientation}"
            else:
                key = f"Custom_{int(page['width'])}x{int(page['height'])}"
            
            formats[key] = formats.get(key, 0) + 1
        
        return formats

    def _summarize_image_formats(self, image_details: List[Dict]) -> Dict[str, int]:
        """Summarize image format distribution"""
        formats = {}
        for img in image_details:
            format_key = img.get("format", "unknown")
            formats[format_key] = formats.get(format_key, 0) + 1
        
        return formats

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on PDF analysis"""
        recommendations = []
        
        if analysis["has_images"]:
            recommendations.append(f"📸 PDF contains {analysis['images_found']} images - consider image processing for better text extraction")
        
        if not analysis["has_a4_pages"]:
            recommendations.append("📏 PDF does not use A4 format - check if this affects processing")
        elif analysis["a4_pages_count"] < analysis["total_pages"]:
            recommendations.append(f"📏 Mixed page sizes detected - {analysis['a4_pages_count']}/{analysis['total_pages']} pages are A4")
        
        if analysis["total_pages"] > 20:
            recommendations.append("📄 Large PDF detected - consider pagination for better performance")
        
        return recommendations

    async def extract_text_from_images_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """Extract text from images in PDF using LangGraph OCR agent"""
        self.logger.info(f"🖼️ Extracting text from images in: {os.path.basename(file_path)}")
        
        extracted_data = {
            "total_images": 0,
            "processed_images": 0,
            "extracted_texts": [],
            "processing_errors": [],
            "metadata": {}
        }
        
        try:
            if not PYMUPDF_AVAILABLE:
                self.logger.error("❌ PyMuPDF required for image extraction")
                extracted_data["processing_errors"].append("PyMuPDF not available")
                return extracted_data
            
            import fitz  # PyMuPDF
            
            # Open PDF
            doc = fitz.open(file_path)
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                extracted_data["total_images"] += len(image_list)
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image data
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        self.logger.info(f"📸 Processing image {img_index + 1} on page {page_num + 1}")
                        
                        # Use LangGraph OCR agent to extract text
                        ocr_result = await self.ocr_agent.process_image(
                            image_data=image_bytes,
                            document_type="medical_assessment",
                            page_number=page_num + 1,
                            image_index=img_index + 1
                        )
                        
                        # Store results
                        image_result = {
                            "page_number": page_num + 1,
                            "image_index": img_index + 1,
                            "extracted_text": ocr_result.get("extracted_text", ""),
                            "confidence_level": ocr_result.get("confidence_level", "medium"),
                            "context_info": ocr_result.get("context_info", ""),
                            "quality_score": ocr_result.get("quality_score", 0),
                            "enhanced": ocr_result.get("enhanced", False),
                            "processing_errors": ocr_result.get("processing_errors", [])
                        }
                        
                        extracted_data["extracted_texts"].append(image_result)
                        
                        if ocr_result.get("extracted_text"):
                            extracted_data["processed_images"] += 1
                            self.logger.info(f"✅ Successfully extracted {len(ocr_result['extracted_text'])} characters")
                        else:
                            self.logger.warning(f"⚠️ No text extracted from image {img_index + 1}")
                        
                    except Exception as e:
                        error_msg = f"Error processing image {img_index + 1} on page {page_num + 1}: {str(e)}"
                        extracted_data["processing_errors"].append(error_msg)
                        self.logger.error(f"❌ {error_msg}")
            
            doc.close()
            
            # Summary
            extracted_data["metadata"] = {
                "total_pages": len(doc),
                "success_rate": (extracted_data["processed_images"] / extracted_data["total_images"]) * 100 if extracted_data["total_images"] > 0 else 0,
                "total_text_length": sum(len(result["extracted_text"]) for result in extracted_data["extracted_texts"]),
                "average_quality_score": sum(result["quality_score"] for result in extracted_data["extracted_texts"]) / len(extracted_data["extracted_texts"]) if extracted_data["extracted_texts"] else 0
            }
            
            self.logger.info(f"🎉 OCR processing completed:")
            self.logger.info(f"   📊 {extracted_data['processed_images']}/{extracted_data['total_images']} images processed")
            self.logger.info(f"   📝 {extracted_data['metadata']['total_text_length']} total characters extracted")
            self.logger.info(f"   📈 {extracted_data['metadata']['success_rate']:.1f}% success rate")
            
        except Exception as e:
            error_msg = f"OCR extraction failed: {str(e)}"
            extracted_data["processing_errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
        
        return extracted_data

    async def process_pdf_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """Process PDF combining regular text extraction with OCR for images"""
        self.logger.info(f"🔄 Processing PDF with OCR: {os.path.basename(file_path)}")
        
        combined_data = {
            "file_path": file_path,
            "text_extraction": {},
            "image_extraction": {},
            "combined_text": "",
            "processing_summary": {}
        }
        
        try:
            # First extract regular text
            text_content = await self.extract_text_from_pdf(file_path)
            combined_data["text_extraction"] = {
                "text": text_content,
                "length": len(text_content)
            }
            
            # Then extract text from images
            if await self.check_pdf_has_images(file_path):
                self.logger.info("📸 PDF contains images, running OCR...")
                image_data = await self.extract_text_from_images_with_ocr(file_path)
                combined_data["image_extraction"] = image_data
                
                # Combine all extracted texts
                all_texts = [text_content] if text_content else []
                for img_result in image_data.get("extracted_texts", []):
                    if img_result.get("extracted_text"):
                        all_texts.append(f"\n--- Image {img_result['image_index']} (Page {img_result['page_number']}) ---\n{img_result['extracted_text']}")
                
                combined_data["combined_text"] = "\n".join(all_texts)
            else:
                self.logger.info("📄 No images found, using text extraction only")
                combined_data["combined_text"] = text_content
            
            # Create processing summary
            combined_data["processing_summary"] = {
                "total_text_length": len(combined_data["combined_text"]),
                "regular_text_length": len(text_content),
                "ocr_text_length": len(combined_data["combined_text"]) - len(text_content),
                "images_processed": combined_data["image_extraction"].get("processed_images", 0),
                "images_total": combined_data["image_extraction"].get("total_images", 0),
                "has_images": "image_extraction" in combined_data and combined_data["image_extraction"].get("total_images", 0) > 0,
                "processing_errors": combined_data["image_extraction"].get("processing_errors", [])
            }
            
            self.logger.info(f"✅ Combined processing completed: {combined_data['processing_summary']['total_text_length']} total characters")
            
        except Exception as e:
            error_msg = f"Combined PDF processing failed: {str(e)}"
            combined_data["processing_summary"] = {"error": error_msg}
            self.logger.error(f"❌ {error_msg}")
        
        return combined_data


async def main():
    # Quick checks
    processor = EnhancedPDFProcessor()

    # Check if PDF has images
    input_path = os.path.join(PROJECT_DIR, "assets", 'inputs', "images", "Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf")
    if not os.path.exists(input_path):
        raise RuntimeError("File does not exists: {}".format(input_path))
    
    # Test the new OCR functionality
    print("\n=== Testing OCR Functionality ===")
    combined_results = await processor.process_pdf_with_ocr(input_path)
    
    print(f"\nProcessing Summary:")
    summary = combined_results.get("processing_summary", {})
    print(f"  Total text length: {summary.get('total_text_length', 0)}")
    print(f"  Regular text length: {summary.get('regular_text_length', 0)}")
    print(f"  OCR text length: {summary.get('ocr_text_length', 0)}")
    print(f"  Images processed: {summary.get('images_processed', 0)}/{summary.get('images_total', 0)}")
    print(f"  Has images: {summary.get('has_images', False)}")
    
    if summary.get('processing_errors'):
        print(f"  Errors: {len(summary['processing_errors'])}")
        for error in summary['processing_errors'][:3]:  # Show first 3 errors
            print(f"    - {error}")
    
    # Show combined text preview
    combined_text = combined_results.get("combined_text", "")
    if combined_text:
        print(f"\nCombined text preview (first 500 chars):")
        print(combined_text[:500] + "..." if len(combined_text) > 500 else combined_text)
    
    print("\n=== Testing Basic Analysis ===")
    has_images = await processor.check_pdf_has_images(input_path)
    print(f"Has images: {has_images}")

    # Get complete analysis
    analysis = await processor.analyze_pdf_structure(input_path)
    print(f"Total pages: {analysis['total_pages']}")
    print(f"Images found: {analysis['images_found']}")
    print(f"A4 pages: {analysis['a4_pages_count']}")

    # Get summary with recommendations
    summary = await processor.get_pdf_summary(input_path)
    print("\nRecommendations:")
    for rec in summary['recommendations']:
        print(f"  - {rec}")
    print()

if __name__ == "__main__":
    asyncio.run(main())