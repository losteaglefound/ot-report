import PyPDF2
import pdfplumber
import re
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
import asyncio
import os
import json

# Configure logging for this module (after imports)
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
        self.logger.info("✅ PDF extraction patterns configured")
    
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
    
    async def _extract_facesheet_data(self, pdf_path: str) -> Dict[str, Any]:
        """Extract patient demographics and basic information from facesheet"""
        text = await self._extract_text_from_pdf(pdf_path)
        
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
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data["patient_info"][field] = match.group(1).strip()
                    break
        
        return data
    
    async def _extract_bayley4_data(self, pdf_path: str, assessment_type: str) -> Dict[str, Any]:
        """Extract Bayley-4 assessment data with enhanced interpretation"""
        text = await self._extract_text_from_pdf(pdf_path)
        
        data = {
            "report_type": assessment_type,
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
        
        if "cognitive" in assessment_type:
            # Extract cognitive, language, and motor data
            domains = [
                "Cognitive", "Visual Reception", "Fine Motor", 
                "Receptive Communication", "Expressive Communication", "Gross Motor"
            ]
            
            composite_domains = [
                "Cognitive Composite", "Language Composite", "Motor Composite"
            ]
            
        else:  # social-emotional
            # Extract social-emotional and adaptive behavior data
            domains = [
                "Social-Emotional", "Self-Control", "Compliance",
                "Communication", "Community Use", "Functional Pre-Academics",
                "Home Living", "Health and Safety", "Leisure", 
                "Self-Care", "Self-Direction", "Social", "Motor"
            ]
            
            composite_domains = [
                "Social-Emotional Composite", "Adaptive Behavior Composite"
            ]
        
        # Extract scores for each domain
        for domain in domains:
            # Raw scores
            raw_pattern = rf"{re.escape(domain)}.*?Raw Score[:\s]*(\d+)"
            raw_match = re.search(raw_pattern, text, re.IGNORECASE)
            if raw_match:
                data["raw_scores"][domain] = int(raw_match.group(1))
            
            # Scaled scores
            scaled_pattern = rf"{re.escape(domain)}.*?Scaled Score[:\s]*(\d+)"
            scaled_match = re.search(scaled_pattern, text, re.IGNORECASE)
            if scaled_match:
                data["scaled_scores"][domain] = int(scaled_match.group(1))
            
            # Age equivalents
            age_pattern = rf"{re.escape(domain)}.*?Age Equivalent[:\s]*(\d+;\d+|\d+\s*years?\s*\d*\s*months?)"
            age_match = re.search(age_pattern, text, re.IGNORECASE)
            if age_match:
                data["age_equivalents"][domain] = age_match.group(1)
        
        # Extract composite scores
        for composite in composite_domains:
            composite_pattern = rf"{re.escape(composite)}[:\s]*(\d+)"
            composite_match = re.search(composite_pattern, text, re.IGNORECASE)
            if composite_match:
                score = int(composite_match.group(1))
                data["composite_scores"][composite] = score
                data["interpretations"][composite] = self._interpret_composite_score(score)
        
        # Extract clinical observations
        data["clinical_observations"] = self._extract_clinical_observations(text)
        data["strengths"] = self._extract_strengths(text)
        data["needs"] = self._extract_needs(text)
        data["recommendations"] = self._extract_recommendations(text)
        
        return data
    
    async def _extract_sp2_data(self, pdf_path: str) -> Dict[str, Any]:
        """Extract Sensory Profile 2 data"""
        text = await self._extract_text_from_pdf(pdf_path)
        
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
            match = re.search(score_pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                data["quadrant_scores"][quadrant] = {
                    "raw_score": int(match.group(1)),
                    "classification": match.group(2),
                    "interpretation": self._interpret_sp2_score(quadrant, match.group(2))
                }
        
        # Extract behavioral implications
        data["clinical_implications"] = self._extract_sp2_implications(text)
        
        return data
    
    async def _extract_chomps_data(self, pdf_path: str) -> Dict[str, Any]:
        """Extract ChOMPS feeding assessment data"""
        text = await self._extract_text_from_pdf(pdf_path)
        
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
            match = re.search(domain_pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                score = int(match.group(1))
                risk = match.group(2)
                data["domain_scores"][domain] = score
                data["risk_levels"][domain] = risk
        
        # Extract feeding concerns
        data["feeding_concerns"] = self._extract_feeding_concerns(text)
        data["safety_issues"] = self._extract_safety_concerns(text)
        
        return data
    
    async def _extract_pedieat_data(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PediEAT assessment data"""
        text = await self._extract_text_from_pdf(pdf_path)
        
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
            
            score_match = re.search(score_pattern, text, re.IGNORECASE)
            level_match = re.search(level_pattern, text, re.IGNORECASE)
            
            if score_match:
                data["domain_scores"][domain] = int(score_match.group(1))
            if level_match:
                data["symptom_levels"][domain] = level_match.group(0)
        
        return data
    
    async def _extract_clinical_notes(self, pdf_path: str) -> Dict[str, Any]:
        """Extract and process clinical observations and notes"""
        text = await self._extract_text_from_pdf(pdf_path)
        
        data = {
            "report_type": "clinical_notes",
            "raw_observations": [],
            "narrative_observations": [],
            "bullet_points": [],
            "converted_narratives": []
        }
        
        # Extract bullet points
        bullet_points = self._extract_bullet_points(text)
        data["bullet_points"] = bullet_points
        
        # Convert bullet points to narrative
        data["converted_narratives"] = [
            self._convert_bullet_to_narrative(bullet) for bullet in bullet_points
        ]
        
        # Extract structured observations
        data["raw_observations"] = self._extract_structured_observations(text)
        
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

# Legacy compatibility - keep the original class name as alias
PDFProcessor = EnhancedPDFProcessor 