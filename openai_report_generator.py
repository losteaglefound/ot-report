from datetime import datetime
from dateutil import parser
import io
import json
import logging
import os
import re
from traceback import format_exc
from typing import Dict, Any, List, Optional

# Import configuration
from config import config
from config import get_openai_api_key, get_openai_model, is_openai_enabled

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging for this module (after imports)
logger = logging.getLogger(__name__)

if OPENAI_AVAILABLE:
    logger.info("✅ OpenAI library imported successfully")
else:
    logger.warning("⚠️ OpenAI library not available - install with: pip install openai")

from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph, 
    PageBreak,
    SimpleDocTemplate, 
    Spacer, 
    Table, 
    TableStyle, 
    ListFlowable,
    ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors


from backend.prompts import save_response, remove_lang_tags, get_prompt
from backend.utils.response import format_data_for_pdf
from backend.langgraph import graph_invoke


class OpenAIEnhancedReportGenerator:
    """Professional OT Report Generator using OpenAI for clinical narratives"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🧠 Initializing OpenAI Enhanced Report Generator...")
        self.config = config
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.logger.info("✅ ReportLab styles configured")
        
        # Initialize OpenAI based on configuration
        self.openai_client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client using configuration system"""
        self.logger.info("🔑 Initializing OpenAI client...")
        
        if not OPENAI_AVAILABLE:
            self.logger.error("❌ OpenAI library not available")
            return
        
        if not is_openai_enabled():
            self.logger.warning("⚠️ OpenAI not configured in .env file")
            self.logger.info("💡 Professional narratives will use enhanced fallback templates")
            return
        
        api_key = get_openai_api_key()
        model = get_openai_model()
        
        try:
            # Initialize OpenAI client with configuration
            self.logger.info(f"🔧 Creating OpenAI client with model: {model}")
            
            # Try different initialization methods for compatibility
            try:
                # Modern OpenAI library (v1.0+)
                self.openai_client = openai.OpenAI(
                    api_key=api_key,
                    timeout=30.0
                )
                self.logger.info("✅ OpenAI client initialized with modern API")
            except TypeError as e:
                self.logger.warning(f"⚠️ Modern OpenAI init failed: {e}")
                # Fallback for older versions
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.logger.info("✅ OpenAI client initialized with basic config")
                except Exception as fallback_error:
                    self.logger.error(f"❌ Both initialization methods failed: {fallback_error}")
                    self.openai_client = None
                    return
            
            # Test API connection with configured model
            try:
                self.logger.info("🧪 Testing OpenAI API connection...")
                test_response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                self.logger.info(f"✅ OpenAI API connection test successful with model: {model}")
            except Exception as test_error:
                self.logger.error(f"❌ OpenAI API test failed: {test_error}")
                self.logger.warning("⚠️ Will use enhanced fallback text generation")
                # Don't set client to None here, as we might still be able to use it
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def _calculate_chronological_age(self, dob_str: str, encounter_date_str: str) -> Dict[str, Any]:
        """Calculate detailed chronological age from DOB and encounter date"""
        try:
            # Parse dates
            dob = parser.parse(dob_str)
            encounter_date = parser.parse(encounter_date_str)
            
            # Calculate age difference
            age_delta = encounter_date - dob
            total_days = age_delta.days
            
            # Calculate years, months, days
            years = total_days // 365
            remaining_days = total_days % 365
            months = remaining_days // 30
            days = remaining_days % 30
            
            # Total months for calculation purposes
            total_months = (years * 12) + months
            
            return {
                "years": years,
                "months": months,
                "days": days,
                "total_days": total_days,
                "total_months": total_months,
                "formatted": f"{years} years, {months} months" if years > 0 else f"{total_months} months"
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Could not calculate chronological age: {e}")
            return {
                "years": 0,
                "months": 0,
                "days": 0,
                "total_days": 0,
                "total_months": 0,
                "formatted": "Age calculation unavailable"
            }
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles with enhanced professional formatting"""
        # Header style for main title - Enhanced with better typography
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f4788'),  # Professional blue
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            borderWidth=2,
            borderColor=colors.HexColor('#1f4788'),
            borderPadding=8,
            leftIndent=0,
            rightIndent=0
        ))
        
        # Clinic info style - Enhanced readability
        self.styles.add(ParagraphStyle(
            name='ClinicInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#444444'),
            spaceAfter=6,
            spaceBefore=2,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=14
        ))
        
        # Section header style - Enhanced with better visual hierarchy
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#1f4788'),
            borderPadding=6,
            backColor=colors.HexColor('#f8f9fa'),
            leftIndent=8,
            rightIndent=8
        ))
        
        # Domain header style - Enhanced subsection headers
        self.styles.add(ParagraphStyle(
            name='DomainHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leftIndent=4,
            underlineWidth=1,
            underlineColor=colors.HexColor('#2c5282')
        ))
        
        # Clinical body text - Enhanced for better readability
        self.styles.add(ParagraphStyle(
            name='ClinicalBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            spaceBefore=4,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            fontName='Helvetica',
            leading=14,
            firstLineIndent=0
        ))
        
        # Bullet point style - Enhanced with better indentation
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            spaceBefore=3,
            leftIndent=24,
            bulletIndent=12,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=14
        ))
        
        # Assessment results style - New for score presentations
        self.styles.add(ParagraphStyle(
            name='AssessmentResults',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=8,
            spaceBefore=4,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=12,
            leftIndent=12,
            rightIndent=12,
            backColor=colors.HexColor('#f7fafc'),
            borderWidth=0.5,
            borderColor=colors.HexColor('#e2e8f0'),
            borderPadding=8
        ))
        
        # Key findings style - For highlighting important information
        self.styles.add(ParagraphStyle(
            name='KeyFindings',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2b6cb0'),
            spaceAfter=8,
            spaceBefore=8,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=14,
            leftIndent=16,
            rightIndent=16,
            backColor=colors.HexColor('#ebf8ff'),
            borderWidth=1,
            borderColor=colors.HexColor('#2b6cb0'),
            borderPadding=8
        ))
        
        # Recommendations style - For highlighting recommendations
        self.styles.add(ParagraphStyle(
            name='RecommendationItem',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2d5016'),
            spaceAfter=6,
            spaceBefore=3,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=14,
            leftIndent=20,
            rightIndent=8,
            backColor=colors.HexColor('#f0fff4'),
            borderWidth=0.5,
            borderColor=colors.HexColor('#68d391'),
            borderPadding=6
        ))
        
        # Footer style - For signature and contact information
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            spaceAfter=4,
            spaceBefore=2,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=11
        ))
        
        # Table header style for score tables
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            spaceAfter=4,
            spaceBefore=4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=12
        ))
        
        # Table cell style for score tables
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=3,
            spaceBefore=3,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=12
        ))
    
    async def generate_comprehensive_report(self, report_data: Dict[str, Any], session_id: str) -> str:
        """Generate comprehensive professional OT report using OpenAI enhancement"""
        self.logger.info(f"📝 Starting comprehensive report generation for session: {session_id}")
        
        # Save report data for potential regeneration
        report_data_path = os.path.join("outputs", f"report_data_{session_id}.json")
        try:
            with open(report_data_path, 'w') as f:
                json.dump(report_data, f)
            self.logger.info(f"💾 Saved report data for regeneration: {report_data_path}")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save report data: {e}")
        
        # Enhanced data extraction and processing
        enhanced_data = await self._enhance_report_data(report_data)
        
        patient_name = enhanced_data.get("patient_info", {}).get("name", "Unknown")
        self.logger.info(f"👤 Patient: {patient_name}")
        
        output_path = os.path.join("outputs", f"professional_ot_report_{session_id}.pdf")
        self.logger.info(f"📁 Output path: {output_path}")
        
        try:
            # Create the PDF document with enhanced settings
            self.logger.info("📄 Creating PDF document with professional formatting...")
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                topMargin=0.85*inch,      # Slightly larger top margin for header spacing
                bottomMargin=0.85*inch,   # Larger bottom margin for footer/signature
                leftMargin=0.9*inch,      # Increased left margin for better readability
                rightMargin=0.9*inch,     # Increased right margin for better readability
                title="FMRC Health Group - OT Evaluation Report",
                author="Fushia Crooms, MOT, OTR/L",
                subject="Occupational Therapy Developmental Evaluation",
                creator="FMRC Health Group Report Generator",
                keywords="occupational therapy, developmental evaluation, pediatric assessment"
            )
            
            page_width, page_width = doc.pagesize

            img_path = self.config.get_header_image_path()
            with PILImage.open(img_path) as img:
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
                scaled_height = page_width * aspect_ratio

            # Create Platypus Image with scaled dimensions
            header_image = Image(img_path, width=page_width, height=scaled_height)

            # Build the report content
            story = []
            story.extend([header_image, Spacer(1, 12)])
            
            # Header section (clinic branding and patient info)
            self.logger.info("📋 Generating header section...")
            story.extend(self._create_professional_header(enhanced_data["patient_info"]))
            
            # Main report sections
            self.logger.info("📝 Generating background section...")
            story.extend(await self._create_background_section(enhanced_data))
            
            self.logger.info("👥 Generating caregiver concerns...")
            story.extend(await self._create_caregiver_concerns(enhanced_data))
            
            self.logger.info("👁️ Generating clinical observations...")
            story.extend(await self._create_clinical_observations(enhanced_data))
            
            self.logger.info("🔧 Adding assessment tools description...")
            story.extend(self._create_assessment_tools_description())
            
            self.logger.info("📊 Generating detailed assessment results...")
            story.extend(await self._create_detailed_assessment_results(enhanced_data))
            
            self.logger.info("💡 Generating recommendations...")
            story.extend(await self._create_recommendations_section(enhanced_data))
            
            self.logger.info("📋 Generating professional summary...")
            story.extend(await self._create_professional_summary(enhanced_data))
            
            self.logger.info("🎯 Generating OT goals...")
            story.extend(await self._create_ot_goals_section(enhanced_data))
            
            self.logger.info("✍️ Adding signature block...")
            story.extend(self._create_signature_block())
            
            # Build the PDF
            self.logger.info("🔨 Building final PDF document...")
            doc.build(story)
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
                self.logger.info(f"✅ Report generated successfully: {file_size:.2f} MB")
            else:
                raise Exception("PDF file was not created")
            
            return output_path
            
        except Exception as e:
            print(format_exc())
            self.logger.error(f"❌ Report generation failed: {e}")
            raise

    async def generate_google_docs_report(self, report_data: Dict[str, Any], session_id: str) -> str:
        """Generate comprehensive professional OT report in Google Docs format using OpenAI enhancement"""
        self.logger.info(f"📝 Starting AI-enhanced Google Docs report generation for session: {session_id}")
        
        # Enhanced data extraction and processing (same as PDF generation)
        enhanced_data = await self._enhance_report_data(report_data)
        
        patient_name = enhanced_data.get("patient_info", {}).get("name", "Unknown")
        self.logger.info(f"👤 Patient: {patient_name}")
        
        try:
            # Import Google Docs integration
            from google_docs_integration import GoogleDocsReportGenerator
            
            # Initialize Google Docs generator
            self.logger.info("📄 Initializing Google Docs integration...")
            google_docs_generator = GoogleDocsReportGenerator()
            
            if not google_docs_generator.service:
                raise Exception("Google Docs service not available")
            
            # Prepare enhanced report data for Google Docs format
            self.logger.info("🧠 Preparing AI-enhanced content for Google Docs...")
            docs_enhanced_data = await self._prepare_google_docs_content(enhanced_data)
            
            # Create the Google Doc using enhanced content
            self.logger.info("📝 Creating professional Google Docs report...")
            doc_url = await self._create_enhanced_google_doc(google_docs_generator, docs_enhanced_data, session_id)
            
            self.logger.info(f"✅ AI-enhanced Google Docs report created successfully: {doc_url}")
            return doc_url
            
        except Exception as e:
            self.logger.error(f"❌ Google Docs report generation failed: {e}")
            raise

    async def _prepare_google_docs_content(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare enhanced content specifically formatted for Google Docs"""
        self.logger.info("🔧 Preparing content for Google Docs format...")
        
        # Start with enhanced data
        docs_data = enhanced_data.copy()
        
        # Generate Google Docs specific narratives (more conversational, less clinical)
        self.logger.info("📝 Generating Google Docs optimized narratives...")
        docs_narratives = await self._generate_google_docs_narratives(enhanced_data)
        docs_data["docs_narratives"] = docs_narratives
        
        # Format assessment results for Google Docs tables
        docs_data["formatted_assessments"] = await self._format_assessments_for_docs(enhanced_data)
        
        # Generate enhanced recommendations formatted for Google Docs
        docs_data["enhanced_recommendations"] = await self._generate_enhanced_recommendations_for_docs(enhanced_data)
        
        # Generate enhanced goals formatted for Google Docs
        docs_data["enhanced_goals"] = await self._generate_enhanced_goals_for_docs(enhanced_data)
        
        return docs_data

    async def _generate_google_docs_narratives(self, enhanced_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate narratives optimized for Google Docs format (more accessible, less clinical)"""
        patient_info = enhanced_data.get("patient_info", {})
        assessment_analysis = enhanced_data.get("assessment_analysis", {})
        
        narratives = {}
        
        # Background narrative for Google Docs
        background_prompt = f"""
        Create a comprehensive background section for a Google Docs OT report that is professional yet accessible to families.
        
        Patient: {patient_info.get('name', 'Child')}
        Age: {patient_info.get('chronological_age', {}).get('formatted', 'Unknown')}
        Date of Birth: {patient_info.get('date_of_birth', 'Unknown')}
        Parent/Guardian: {patient_info.get('parent_guardian', 'Unknown')}
        
        Write in a professional but family-friendly tone that explains:
        - Reason for referral and evaluation
        - Child's developmental history context
        - Assessment purpose and goals
        - Family involvement in the process
        
        Keep the language clear and avoid excessive clinical jargon. This should be understandable to parents while maintaining professional standards.
        """
        
        narratives["background"] = await self._generate_with_openai(background_prompt, max_tokens=400)
        
        # Clinical observations narrative for Google Docs
        observations_prompt = f"""
        Create a clinical observations section for a Google Docs OT report.
        
        Patient: {patient_info.get('name', 'Child')}
        Age: {patient_info.get('chronological_age', {}).get('formatted', 'Unknown')}
        
        Based on typical pediatric OT observations, write about:
        - Child's engagement and cooperation during assessment
        - Social interaction patterns
        - Attention and focus abilities
        - Physical presentation and motor skills
        - Communication and behavioral observations
        
        Write in a balanced tone that highlights both strengths and areas of concern. Make it family-friendly while maintaining clinical accuracy.
        """
        
        narratives["clinical_observations"] = await self._generate_with_openai(observations_prompt, max_tokens=400)
        
        # Professional summary for Google Docs
        summary_prompt = f"""
        Create a professional summary for a Google Docs OT report that synthesizes assessment findings.
        
        Patient: {patient_info.get('name', 'Child')}
        Age: {patient_info.get('chronological_age', {}).get('formatted', 'Unknown')}
        
        Assessment data indicates:
        - Bayley-4 results show developmental patterns
        - Multiple assessment tools were administered
        - Comprehensive evaluation completed
        
        Write a summary that:
        - Synthesizes key findings across all assessments
        - Identifies the child's strengths and abilities
        - Addresses areas requiring intervention
        - Provides overall developmental picture
        - Sets context for recommendations
        
        Use professional language that is accessible to families and other team members.
        """
        
        narratives["professional_summary"] = await self._generate_with_openai(summary_prompt, max_tokens=500)
        
        return narratives

    async def _format_assessments_for_docs(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format assessment results specifically for Google Docs tables and formatting"""
        self.logger.info("📊 Formatting assessments for Google Docs...")
        
        formatted = {}
        assessment_analysis = enhanced_data.get("assessment_analysis", {})
        
        # Format Bayley-4 results
        if "bayley4" in assessment_analysis:
            formatted["bayley4"] = await self._format_bayley4_for_docs(assessment_analysis["bayley4"])
        
        # Format SP2 results
        if "sp2" in assessment_analysis:
            formatted["sp2"] = await self._format_sp2_for_docs(assessment_analysis["sp2"])
        
        # Format ChOMPS results
        if "chomps" in assessment_analysis:
            formatted["chomps"] = await self._format_chomps_for_docs(assessment_analysis["chomps"])
        
        # Format PediEAT results
        if "pedieat" in assessment_analysis:
            formatted["pedieat"] = await self._format_pedieat_for_docs(assessment_analysis["pedieat"])
        
        return formatted

    async def _format_bayley4_for_docs(self, bayley_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format Bayley-4 results for Google Docs presentation"""
        formatted = {
            "domains": [],
            "summary": ""
        }
        
        # Process cognitive analysis
        if "cognitive_analysis" in bayley_analysis:
            for domain, analysis in bayley_analysis["cognitive_analysis"].items():
                if isinstance(analysis, dict):
                    formatted["domains"].append({
                        "domain": domain,
                        "range": analysis.get("range_class", "Unknown"),
                        "percentile": analysis.get("percentile_range", "Unknown"),
                        "description": analysis.get("clinical_desc", "Assessment completed")
                    })
        
        # Process social-emotional analysis
        if "social_emotional_analysis" in bayley_analysis:
            for domain, analysis in bayley_analysis["social_emotional_analysis"].items():
                if isinstance(analysis, dict):
                    formatted["domains"].append({
                        "domain": domain,
                        "range": analysis.get("range_class", "Unknown"),
                        "percentile": analysis.get("percentile_range", "Unknown"),
                        "description": analysis.get("clinical_desc", "Assessment completed")
                    })
        
        return formatted

    async def _format_sp2_for_docs(self, sp2_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format SP2 results for Google Docs presentation"""
        return {
            "quadrants": sp2_analysis.get("quadrant_scores", {}),
            "interpretations": sp2_analysis.get("interpretations", {}),
            "implications": sp2_analysis.get("real_world_implications", [])
        }

    async def _format_chomps_for_docs(self, chomps_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format ChOMPS results for Google Docs presentation"""
        return {
            "concerns": chomps_analysis.get("concern_levels", {}),
            "risks": chomps_analysis.get("feeding_risks", []),
            "recommendations": chomps_analysis.get("recommendations", [])
        }

    async def _format_pedieat_for_docs(self, pedieat_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format PediEAT results for Google Docs presentation"""
        return {
            "domains": pedieat_analysis.get("domain_scores", {}),
            "interpretations": pedieat_analysis.get("interpretations", {}),
            "safety_concerns": pedieat_analysis.get("safety_concerns", [])
        }

    async def _generate_enhanced_recommendations_for_docs(self, enhanced_data: Dict[str, Any]) -> List[str]:
        """Generate enhanced recommendations formatted for Google Docs"""
        recommendations_prompt = f"""
        Generate comprehensive OT recommendations for a Google Docs report based on assessment findings.
        
        Patient: {enhanced_data.get('patient_info', {}).get('name', 'Child')}
        Age: {enhanced_data.get('patient_info', {}).get('chronological_age', {}).get('formatted', 'Unknown')}
        
        Create 8-12 specific, actionable recommendations that address:
        - Direct occupational therapy services
        - Home program activities
        - Environmental modifications
        - Caregiver training and education
        - Equipment or adaptive tools
        - School/daycare accommodations
        - Follow-up assessments
        - Community resources
        
        Format each recommendation as a clear, actionable statement that families can understand and implement.
        """
        
        recommendations_text = await self._generate_with_openai(recommendations_prompt, max_tokens=600)
        
        # Convert to list format
        recommendations = [rec.strip() for rec in recommendations_text.split('\n') if rec.strip() and not rec.strip().startswith('#')]
        
        return recommendations[:12]  # Limit to 12 recommendations

    async def _generate_enhanced_goals_for_docs(self, enhanced_data: Dict[str, Any]) -> List[str]:
        """Generate enhanced OT goals formatted for Google Docs"""
        goals_prompt = f"""
        Generate specific, measurable OT goals for a Google Docs report.
        
        Patient: {enhanced_data.get('patient_info', {}).get('name', 'Child')}
        Age: {enhanced_data.get('patient_info', {}).get('chronological_age', {}).get('formatted', 'Unknown')}
        
        Create 6-8 SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound) that address:
        - Fine motor development
        - Gross motor skills
        - Sensory processing
        - Self-care/adaptive skills
        - Social participation
        - Cognitive-motor integration
        
        Format each goal with:
        - Clear measurable criteria
        - Realistic timeframes
        - Age-appropriate expectations
        - Family-friendly language
        
        Example format: "By [timeframe], [child] will [specific action] with [level of assistance] in [context] as measured by [criteria]."
        """
        
        goals_text = await self._generate_with_openai(goals_prompt, max_tokens=600)
        
        # Convert to list format
        goals = [goal.strip() for goal in goals_text.split('\n') if goal.strip() and not goal.strip().startswith('#')]
        
        return goals[:8]  # Limit to 8 goals

    async def _create_enhanced_google_doc(self, google_docs_generator, enhanced_data: Dict[str, Any], session_id: str) -> str:
        """Create Google Doc using the enhanced data and AI-generated content"""
        self.logger.info("📝 Creating enhanced Google Doc with AI-generated content...")
        
        # Create the document structure with enhanced content
        doc_title = f"OT Evaluation Report - {enhanced_data.get('patient_info', {}).get('name', 'Patient')} - {datetime.now().strftime('%Y-%m-%d')}"
        
        try:
            # Create a new document
            doc = google_docs_generator.service.documents().create(body={'title': doc_title}).execute()
            doc_id = doc.get('documentId')
            self.logger.info(f"📄 Created Google Doc with ID: {doc_id}")
            
            # Build enhanced content requests
            requests = await self._build_enhanced_docs_requests(enhanced_data)
            
            # Apply all formatting and content in batches
            self.logger.info("🎨 Applying enhanced formatting and content...")
            batch_size = 50  # Google Docs API limit
            for i in range(0, len(requests), batch_size):
                batch = requests[i:i + batch_size]
                google_docs_generator.service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': batch}
                ).execute()
            
            # Make document shareable
            doc_url = google_docs_generator._make_document_shareable(doc_id)
            
            self.logger.info(f"✅ Enhanced Google Docs report created: {doc_url}")
            return doc_url
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create enhanced Google Doc: {e}")
            # Fallback to basic Google Docs generation
            self.logger.info("🔄 Falling back to basic Google Docs generation...")
            return await google_docs_generator.create_report(enhanced_data, session_id)

    async def _build_enhanced_docs_requests(self, enhanced_data: Dict[str, Any]) -> List[Dict]:
        """Build Google Docs API requests for enhanced content"""
        requests = []
        current_index = 1
        
        patient_info = enhanced_data.get("patient_info", {})
        docs_narratives = enhanced_data.get("docs_narratives", {})
        
        # Document title and header
        title_text = f"PEDIATRIC OCCUPATIONAL THERAPY EVALUATION\n\n"
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': title_text
            }
        })
        current_index += len(title_text)
        
        # Format title
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': 1, 'endIndex': current_index - 2},
                'textStyle': {
                    'bold': True,
                    'fontSize': {'magnitude': 16, 'unit': 'PT'},
                    'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                },
                'fields': 'bold,fontSize,foregroundColor'
            }
        })
        
        # Center title
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': 1, 'endIndex': current_index - 2},
                'paragraphStyle': {'alignment': 'CENTER'},
                'fields': 'alignment'
            }
        })
        
        # Patient information section
        patient_section = f"Patient Name: {patient_info.get('name', 'Unknown')}\n"
        patient_section += f"Date of Birth: {patient_info.get('date_of_birth', 'Unknown')}\n"
        patient_section += f"Chronological Age: {patient_info.get('chronological_age', {}).get('formatted', 'Unknown')}\n"
        patient_section += f"Parent/Guardian: {patient_info.get('parent_guardian', 'Unknown')}\n"
        patient_section += f"Evaluation Date: {patient_info.get('encounter_date', 'Unknown')}\n"
        patient_section += f"Report Date: {patient_info.get('report_date', datetime.now().strftime('%Y-%m-%d'))}\n\n"
        
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': patient_section
            }
        })
        current_index += len(patient_section)
        
        # Background section
        if docs_narratives.get("background"):
            background_header = "BACKGROUND AND REASON FOR REFERRAL\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': background_header
                }
            })
            current_index += len(background_header)
            
            # Format header
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index - len(background_header), 'endIndex': current_index - 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                    },
                    'fields': 'bold,fontSize,foregroundColor'
                }
            })
            
            background_content = docs_narratives["background"] + "\n\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': background_content
                }
            })
            current_index += len(background_content)
        
        # Assessment Results section
        assessment_header = "ASSESSMENT RESULTS\n"
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': assessment_header
            }
        })
        current_index += len(assessment_header)
        
        # Format assessment header
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': current_index - len(assessment_header), 'endIndex': current_index - 1},
                'textStyle': {
                    'bold': True,
                    'fontSize': {'magnitude': 14, 'unit': 'PT'},
                    'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                },
                'fields': 'bold,fontSize,foregroundColor'
            }
        })
        
        # Add assessment content
        formatted_assessments = enhanced_data.get("formatted_assessments", {})
        if formatted_assessments.get("bayley4"):
            bayley_content = "Bayley Scales of Infant and Toddler Development (4th Edition):\n"
            for domain_info in formatted_assessments["bayley4"].get("domains", []):
                bayley_content += f"• {domain_info['domain']}: {domain_info['range']} ({domain_info['percentile']}) - {domain_info['description']}\n"
            bayley_content += "\n"
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': bayley_content
                }
            })
            current_index += len(bayley_content)
        
        # Clinical Observations
        if docs_narratives.get("clinical_observations"):
            observations_header = "CLINICAL OBSERVATIONS\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': observations_header
                }
            })
            current_index += len(observations_header)
            
            # Format header
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index - len(observations_header), 'endIndex': current_index - 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                    },
                    'fields': 'bold,fontSize,foregroundColor'
                }
            })
            
            observations_content = docs_narratives["clinical_observations"] + "\n\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': observations_content
                }
            })
            current_index += len(observations_content)
        
        # Recommendations
        enhanced_recommendations = enhanced_data.get("enhanced_recommendations", [])
        if enhanced_recommendations:
            recommendations_header = "RECOMMENDATIONS\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': recommendations_header
                }
            })
            current_index += len(recommendations_header)
            
            # Format header
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index - len(recommendations_header), 'endIndex': current_index - 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                    },
                    'fields': 'bold,fontSize,foregroundColor'
                }
            })
            
            recommendations_content = ""
            for i, rec in enumerate(enhanced_recommendations, 1):
                recommendations_content += f"{i}. {rec}\n"
            recommendations_content += "\n"
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': recommendations_content
                }
            })
            current_index += len(recommendations_content)
        
        # Professional Summary
        if docs_narratives.get("professional_summary"):
            summary_header = "PROFESSIONAL SUMMARY\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': summary_header
                }
            })
            current_index += len(summary_header)
            
            # Format header
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index - len(summary_header), 'endIndex': current_index - 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                    },
                    'fields': 'bold,fontSize,foregroundColor'
                }
            })
            
            summary_content = docs_narratives["professional_summary"] + "\n\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': summary_content
                }
            })
            current_index += len(summary_content)
        
        # Treatment Goals
        enhanced_goals = enhanced_data.get("enhanced_goals", [])
        if enhanced_goals:
            goals_header = "TREATMENT GOALS\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': goals_header
                }
            })
            current_index += len(goals_header)
            
            # Format header
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index - len(goals_header), 'endIndex': current_index - 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 14, 'unit': 'PT'},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.12, 'green': 0.28, 'blue': 0.53}}}
                    },
                    'fields': 'bold,fontSize,foregroundColor'
                }
            })
            
            goals_content = ""
            for i, goal in enumerate(enhanced_goals, 1):
                goals_content += f"{i}. {goal}\n"
            goals_content += "\n"
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': goals_content
                }
            })
            current_index += len(goals_content)
        
        # Signature block
        signature_text = "Report prepared by:\n"
        signature_text += "Fushia Crooms, MOT, OTR/L\n"
        signature_text += "Occupational Therapist\n"
        signature_text += "FMRC Health Group\n"
        signature_text += f"Date: {datetime.now().strftime('%B %d, %Y')}\n"
        
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': signature_text
            }
        })
        
        return requests
    
    async def _enhance_report_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance report data with detailed analysis and calculations"""
        enhanced_data = report_data.copy()
        
        # Enhanced patient info with chronological age calculation
        patient_info = enhanced_data.get("patient_info", {})
        if patient_info.get("date_of_birth") and patient_info.get("encounter_date"):
            chron_age = self._calculate_chronological_age(
                patient_info["date_of_birth"], 
                patient_info["encounter_date"]
            )
            patient_info["chronological_age"] = chron_age
        
        # Enhanced clinical notes extraction
        enhanced_data["clinical_notes"] = await self._extract_clinical_notes(report_data)
        
        # Enhanced assessment analysis
        enhanced_data["assessment_analysis"] = await self._detailed_assessment_analysis(report_data)
        
        # Generate ALL narratives in single OpenAI call to save tokens
        enhanced_data["consolidated_narratives"] = await self._generate_consolidated_report_narratives(enhanced_data)
        
        return enhanced_data
    
    async def _extract_clinical_notes(self, report_data: Dict[str, Any]) -> List[str]:
        """Extract and format clinical notes in bullet-point format"""
        extracted_data = report_data.get("extracted_data", {})
        clinical_notes = []
        
        # Extract from various sources
        if "clinical_notes" in extracted_data:
            notes_text = extracted_data["clinical_notes"]
            if isinstance(notes_text, str):
                # Convert to bullet points using AI
                notes_prompt = f"""
                Convert the following clinical notes into clear, professional bullet points for a pediatric OT report:
                
                {notes_text}
                
                Format as bullet points covering:
                - Behavioral observations
                - Physical presentations
                - Interaction patterns
                - Performance observations
                - Caregiver reports
                
                Use concise, clinical language appropriate for OT documentation.
                """
                notes_response = await self._generate_with_openai(notes_prompt, max_tokens=400)
                clinical_notes = [note.strip() for note in notes_response.split("•") if note.strip()]
        
        # Add fallback notes if none extracted
        if not clinical_notes:
            clinical_notes = [
                "Child was alert and responsive during assessment session",
                "Demonstrated age-appropriate attention and engagement",
                "Caregiver present and provided developmental history",
                "Assessment completed in structured clinical environment"
            ]
        
        return clinical_notes
    
    async def _detailed_assessment_analysis(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed analysis of all assessment tools"""
        extracted_data = report_data.get("extracted_data", {})
        analysis = {}
        
        # Bayley-4 detailed analysis
        analysis["bayley4"] = await self._analyze_bayley4_detailed(extracted_data)
        
        # SP2 analysis
        analysis["sp2"] = await self._analyze_sp2_detailed(extracted_data)
        
        # ChOMPS analysis  
        analysis["chomps"] = await self._analyze_chomps_detailed(extracted_data)
        
        # PediEAT analysis
        analysis["pedieat"] = await self._analyze_pedieat_detailed(extracted_data)
        
        return analysis
    
    async def _analyze_bayley4_detailed(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed Bayley-4 analysis with rich clinical interpretation"""
        bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        bayley_social = extracted_data.get("bayley4_social", {})
        
        analysis = {
            "cognitive_analysis": {},
            "social_emotional_analysis": {},
            "motor_analysis": {},
            "language_analysis": {}
        }
        
        # Detailed cognitive analysis
        if bayley_cognitive.get("scaled_scores"):
            for domain, score in bayley_cognitive["scaled_scores"].items():
                interpretation = self._get_bayley_score_interpretation(domain, score)
                analysis["cognitive_analysis"][domain] = interpretation
        
        # Detailed social-emotional analysis
        if bayley_social.get("scaled_scores"):
            for domain, score in bayley_social["scaled_scores"].items():
                interpretation = self._get_bayley_score_interpretation(domain, score)
                analysis["social_emotional_analysis"][domain] = interpretation
        
        return analysis
    
    def _get_bayley_score_interpretation(self, domain: str, scaled_score: int) -> Dict[str, Any]:
        """Get detailed interpretation for Bayley scaled scores"""
        # Score ranges and interpretations
        if scaled_score >= 13:
            range_class = "Above Average"
            percentile_range = "84th percentile and above"
            clinical_desc = "significantly above expected developmental level"
        elif scaled_score >= 8:
            range_class = "Average"  
            percentile_range = "25th-75th percentile"
            clinical_desc = "within expected developmental range"
        elif scaled_score >= 4:
            range_class = "Below Average"
            percentile_range = "9th-24th percentile" 
            clinical_desc = "below expected developmental level"
        else:
            range_class = "Extremely Low"
            percentile_range = "2nd percentile and below"
            clinical_desc = "significantly below expected developmental level"
        
        # Domain-specific functional implications
        functional_implications = self._get_domain_functional_implications(domain, range_class)
        
        return {
            "scaled_score": scaled_score,
            "range_classification": range_class,
            "percentile_range": percentile_range,
            "clinical_description": clinical_desc,
            "functional_implications": functional_implications
        }
    
    def _get_domain_functional_implications(self, domain: str, range_class: str) -> str:
        """Get domain-specific functional implications"""
        implications = {
            "Cognitive": {
                "Above Average": "demonstrates advanced problem-solving, memory, and learning abilities with strong visual processing skills",
                "Average": "shows age-appropriate cognitive processing, problem-solving, and learning capacity",
                "Below Average": "experiences mild challenges in problem-solving and cognitive processing that may impact learning",
                "Extremely Low": "demonstrates significant cognitive delays requiring intensive intervention support"
            },
            "Receptive Communication": {
                "Above Average": "exceptional language comprehension with advanced understanding of instructions and vocabulary",
                "Average": "age-appropriate understanding of spoken language and ability to follow instructions",
                "Below Average": "mild difficulties understanding spoken language and following complex instructions",
                "Extremely Low": "significant language comprehension delays affecting daily communication and learning"
            },
            "Expressive Communication": {
                "Above Average": "advanced verbal expression with rich vocabulary and complex sentence formation",
                "Average": "age-appropriate verbal expression and communication skills",
                "Below Average": "limited verbal expression that may impact social communication",
                "Extremely Low": "severe expressive language delays requiring intensive speech therapy intervention"
            },
            "Fine Motor": {
                "Above Average": "exceptional hand-eye coordination and manipulation skills beyond age expectations",
                "Average": "age-appropriate fine motor control and manipulation abilities",
                "Below Average": "mild fine motor delays that may impact self-care and pre-academic skills",
                "Extremely Low": "significant fine motor delays affecting daily living skills and academic readiness"
            },
            "Gross Motor": {
                "Above Average": "advanced gross motor coordination, balance, and movement skills",
                "Average": "age-appropriate gross motor development and movement patterns",
                "Below Average": "mild gross motor delays that may impact mobility and play participation",
                "Extremely Low": "significant gross motor delays requiring intensive physical therapy intervention"
            }
        }
        
        return implications.get(domain, {}).get(range_class, f"requires further assessment in {domain} domain")
    
    async def _analyze_sp2_detailed(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed SP2 analysis with real-world implications"""
        sp2_data = extracted_data.get("sp2", {})
        
        analysis = {
            "seeking_analysis": "",
            "avoiding_analysis": "",
            "sensitivity_analysis": "",
            "registration_analysis": "",
            "real_world_implications": []
        }
        
        if sp2_data:
            # Analyze each quadrant with real-world implications
            seeking_score = sp2_data.get("seeking", 0)
            analysis["seeking_analysis"] = self._interpret_sp2_seeking(seeking_score)
            
            avoiding_score = sp2_data.get("avoiding", 0)
            analysis["avoiding_analysis"] = self._interpret_sp2_avoiding(avoiding_score)
            
            sensitivity_score = sp2_data.get("sensitivity", 0)
            analysis["sensitivity_analysis"] = self._interpret_sp2_sensitivity(sensitivity_score)
            
            registration_score = sp2_data.get("registration", 0)
            analysis["registration_analysis"] = self._interpret_sp2_registration(registration_score)
            
            # Real-world implications
            analysis["real_world_implications"] = self._get_sp2_real_world_implications(
                seeking_score, avoiding_score, sensitivity_score, registration_score
            )
        
        return analysis
    
    def _interpret_sp2_seeking(self, score: int) -> str:
        """Interpret SP2 seeking score with clinical implications"""
        if score > 60:
            return "High sensory seeking behaviors - actively seeks intense sensory input, may appear restless or constantly moving"
        elif score > 40:
            return "Typical sensory seeking - appropriate interest in sensory experiences"
        else:
            return "Low sensory seeking - limited interest in sensory exploration, may appear withdrawn from sensory experiences"
    
    def _interpret_sp2_avoiding(self, score: int) -> str:
        """Interpret SP2 avoiding score with clinical implications"""
        if score > 60:
            return "High sensory avoiding - actively avoids sensory input, may be overwhelmed by everyday sensations"
        elif score > 40:
            return "Typical sensory avoiding - appropriate behavioral responses to overwhelming sensory input"
        else:
            return "Low sensory avoiding - tolerates most sensory experiences well"
    
    def _interpret_sp2_sensitivity(self, score: int) -> str:
        """Interpret SP2 sensitivity score with clinical implications"""
        if score > 60:
            return "High sensory sensitivity - notices sensory input others miss, easily distracted by background stimuli"
        elif score > 40:
            return "Typical sensory sensitivity - notices sensory input at expected levels"
        else:
            return "Low sensory sensitivity - may miss subtle sensory cues in environment"
    
    def _interpret_sp2_registration(self, score: int) -> str:
        """Interpret SP2 registration score with clinical implications"""
        if score > 60:
            return "High registration challenges - misses important sensory information, appears unaware of sensory input"
        elif score > 40:
            return "Typical sensory registration - notices relevant sensory information appropriately"
        else:
            return "Good sensory registration - consistently notices and responds to sensory input"
    
    def _get_sp2_real_world_implications(self, seeking: int, avoiding: int, sensitivity: int, registration: int) -> List[str]:
        """Get real-world implications for SP2 scores"""
        implications = []
        
        # Grooming implications
        if avoiding > 60 or sensitivity > 60:
            implications.append("Grooming: May resist hairbrushing, teeth brushing, or face washing due to sensory defensiveness")
        if registration > 60:
            implications.append("Grooming: May not notice when face or hands are dirty, requiring extra prompting for hygiene")
        
        # Play implications
        if seeking > 60:
            implications.append("Play: Seeks intense physical play, may play roughly with toys and peers")
        if avoiding > 60:
            implications.append("Play: May avoid messy play activities, prefers predictable sensory experiences")
        
        # Feeding implications
        if sensitivity > 60:
            implications.append("Feeding: May be highly selective about food textures, temperatures, or tastes")
        if registration > 60:
            implications.append("Feeding: May not notice food around mouth, poor awareness of hunger/fullness cues")
        
        return implications
    
    async def _analyze_chomps_detailed(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed ChOMPS analysis with feeding risk assessment"""
        chomps_data = extracted_data.get("chomps", {})
        
        analysis = {
            "domain_scores": {},
            "concern_levels": {},
            "feeding_risks": [],
            "clinical_recommendations": []
        }
        
        if chomps_data:
            # Analyze each domain
            domains = ["oral_motor", "oral_sensory", "behavioral", "pharyngeal", "esophageal"]
            
            for domain in domains:
                if domain in chomps_data:
                    score = chomps_data[domain]
                    analysis["domain_scores"][domain] = score
                    analysis["concern_levels"][domain] = self._get_chomps_concern_level(score)
            
            # Assess feeding risks
            analysis["feeding_risks"] = self._assess_chomps_feeding_risks(chomps_data)
            
            # Clinical recommendations
            analysis["clinical_recommendations"] = self._get_chomps_recommendations(chomps_data)
        
        return analysis
    
    def _get_chomps_concern_level(self, score: int) -> str:
        """Get ChOMPS concern level based on score"""
        if score >= 7:
            return "High concern - significant feeding difficulties requiring immediate intervention"
        elif score >= 4:
            return "Moderate concern - feeding challenges that warrant monitoring and intervention"
        elif score >= 2:
            return "Mild concern - minor feeding difficulties that may benefit from strategies"
        else:
            return "No concern - typical feeding behaviors for age"
    
    def _assess_chomps_feeding_risks(self, chomps_data: Dict) -> List[str]:
        """Assess specific feeding risks from ChOMPS data"""
        risks = []
        
        # Bolus control risks
        if chomps_data.get("oral_motor", 0) >= 4:
            risks.append("Bolus control: Difficulty managing food bolus, risk of pocketing or spillage")
        
        # Gagging risks
        if chomps_data.get("oral_sensory", 0) >= 4:
            risks.append("Gagging: Heightened gag response to textures, limiting food variety and intake")
        
        # Food hoarding risks
        if chomps_data.get("behavioral", 0) >= 4:
            risks.append("Food hoarding: Behavioral feeding patterns including food refusal or hoarding behaviors")
        
        # Swallowing safety
        if chomps_data.get("pharyngeal", 0) >= 4:
            risks.append("Swallowing safety: Potential aspiration risk requiring modified textures and positioning")
        
        return risks
    
    def _get_chomps_recommendations(self, chomps_data: Dict) -> List[str]:
        """Get clinical recommendations based on ChOMPS findings"""
        recommendations = []
        
        if any(score >= 4 for score in chomps_data.values()):
            recommendations.append("Feeding therapy with licensed speech-language pathologist")
            recommendations.append("Modified food textures and positioning strategies")
            recommendations.append("Caregiver education on safe feeding practices")
        
        if chomps_data.get("pharyngeal", 0) >= 6:
            recommendations.append("Video fluoroscopic swallow study (VFSS) evaluation")
        
        return recommendations
    
    async def _analyze_pedieat_detailed(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed PediEAT analysis with symptom interpretation"""
        pedieat_data = extracted_data.get("pedieat", {})
        
        analysis = {
            "physiology_analysis": "",
            "processing_analysis": "",
            "mealtime_behavior_analysis": "",
            "selectivity_analysis": "",
            "safety_concerns": [],
            "endurance_concerns": []
        }
        
        if pedieat_data:
            # Analyze each domain
            physiology_score = pedieat_data.get("physiology", 0)
            analysis["physiology_analysis"] = self._interpret_pedieat_physiology(physiology_score)
            
            processing_score = pedieat_data.get("processing", 0)
            analysis["processing_analysis"] = self._interpret_pedieat_processing(processing_score)
            
            behavior_score = pedieat_data.get("mealtime_behavior", 0)
            analysis["mealtime_behavior_analysis"] = self._interpret_pedieat_behavior(behavior_score)
            
            selectivity_score = pedieat_data.get("selectivity", 0)
            analysis["selectivity_analysis"] = self._interpret_pedieat_selectivity(selectivity_score)
            
            # Safety and endurance concerns
            analysis["safety_concerns"] = self._assess_pedieat_safety(pedieat_data)
            analysis["endurance_concerns"] = self._assess_pedieat_endurance(pedieat_data)
        
        return analysis
    
    def _interpret_pedieat_physiology(self, score: int) -> str:
        """Interpret PediEAT physiology domain"""
        if score > 14:
            return "Elevated physiological symptoms - significant concerns with growth, medical complexity, or physical function during meals"
        elif score > 7:
            return "Moderate physiological symptoms - some concerns with physical aspects of eating and growth"
        else:
            return "Typical physiological function - no significant concerns with physical eating processes"
    
    def _interpret_pedieat_processing(self, score: int) -> str:
        """Interpret PediEAT processing domain"""
        if score > 14:
            return "Elevated processing symptoms - significant sensory processing challenges affecting eating and mealtime participation"
        elif score > 7:
            return "Moderate processing symptoms - some sensory processing differences impacting food acceptance"
        else:
            return "Typical sensory processing - appropriate sensory responses during eating"
    
    def _interpret_pedieat_behavior(self, score: int) -> str:
        """Interpret PediEAT mealtime behavior domain"""
        if score > 14:
            return "Elevated behavioral symptoms - significant challenging behaviors during mealtimes affecting family dynamics"
        elif score > 7:
            return "Moderate behavioral symptoms - some challenging mealtime behaviors requiring strategies"
        else:
            return "Typical mealtime behaviors - appropriate social engagement and cooperation during meals"
    
    def _interpret_pedieat_selectivity(self, score: int) -> str:
        """Interpret PediEAT selectivity domain"""
        if score > 14:
            return "Elevated selectivity symptoms - severe food selectivity limiting nutritional intake and food variety"
        elif score > 7:
            return "Moderate selectivity symptoms - some food preferences and limitations affecting meal planning"
        else:
            return "Typical food selectivity - age-appropriate food preferences and acceptance"
    
    def _assess_pedieat_safety(self, pedieat_data: Dict) -> List[str]:
        """Assess safety concerns from PediEAT data"""
        concerns = []
        
        if pedieat_data.get("physiology", 0) > 12:
            concerns.append("Nutritional safety: Risk of inadequate caloric or nutrient intake")
            concerns.append("Growth concerns: May require nutritional monitoring and intervention")
        
        if pedieat_data.get("mealtime_behavior", 0) > 12:
            concerns.append("Mealtime safety: Behavioral challenges may impact safe food consumption")
        
        return concerns
    
    def _assess_pedieat_endurance(self, pedieat_data: Dict) -> List[str]:
        """Assess endurance concerns from PediEAT data"""
        concerns = []
        
        if pedieat_data.get("physiology", 0) > 10:
            concerns.append("Feeding endurance: May fatigue quickly during meals, requiring shorter feeding sessions")
            concerns.append("Energy conservation: Strategies needed to optimize energy during eating")
        
        return concerns
    
    async def _create_detailed_assessment_results(self, report_data: Dict[str, Any]) -> List:
        """Create comprehensive assessment results section with detailed interpretations"""
        elements = []
        
        # Main title
        header = Paragraph("Assessment Results and Clinical Interpretation", 
                          self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 8))
        
        # Get assessment analysis
        assessment_analysis = report_data.get("assessment_analysis", {})
        
        # Bayley-4 detailed results
        if assessment_analysis.get("bayley4"):
            elements.extend(await self._create_bayley4_detailed_section(report_data))
        
        # SP2 detailed results
        if assessment_analysis.get("sp2"):
            elements.extend(await self._create_sp2_detailed_section(report_data))
        
        # ChOMPS detailed results
        if assessment_analysis.get("chomps"):
            elements.extend(await self._create_chomps_detailed_section(report_data))
        
        # PediEAT detailed results  
        if assessment_analysis.get("pedieat"):
            elements.extend(await self._create_pedieat_detailed_section(report_data))
        
        return elements
    
    async def _create_bayley4_detailed_section(self, report_data: Dict[str, Any]) -> List:
        """Create detailed Bayley-4 section with comprehensive interpretation and professional score table"""
        elements = []
        
        # # Bayley-4 header with enhanced styling
        # header = Paragraph("Bayley Scales of Infant and Toddler Development - Fourth Edition (Bayley-4)", 
        #                   self.styles['DomainHeader'])
        # elements.append(header)
        # elements.append(Spacer(1, 8))
        
        # # Get extracted Bayley data
        # extracted_data = report_data.get("extracted_data", {})
        # bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        # bayley_social = extracted_data.get("bayley4_social", {})
        
        # # Create professional scores table if we have data
        # if bayley_cognitive.get("raw_scores") or bayley_social.get("raw_scores"):
            
        #     # Scores table header
        #     score_header = Paragraph("Assessment Scores Summary", self.styles['KeyFindings'])
        #     elements.append(score_header)
        #     elements.append(Spacer(1, 6))
            
        #     # Build comprehensive scores table
        #     score_data = [
        #         # Table headers with enhanced styling
        #         [Paragraph("Domain", self.styles['TableHeader']),
        #          Paragraph("Raw Score", self.styles['TableHeader']),
        #          Paragraph("Scaled Score", self.styles['TableHeader']),
        #          Paragraph("Percentile", self.styles['TableHeader']),
        #          Paragraph("Age Equivalent", self.styles['TableHeader']),
        #          Paragraph("Classification", self.styles['TableHeader'])]
        #     ]
            
        #     # Add cognitive/language/motor scores if available
        #     if bayley_cognitive.get("raw_scores"):
        #         cog_scores = bayley_cognitive["raw_scores"]
        #         for domain, scores in cog_scores.items():
        #             if isinstance(scores, dict) and scores.get("scaled_score"):
        #                 classification = self._get_score_classification(scores.get("scaled_score", 0))
        #                 percentile = self._score_to_percentile(scores.get("scaled_score", 0))
                        
        #                 score_data.append([
        #                     Paragraph(f"<b>{domain.title()}</b>", self.styles['TableCell']),
        #                     Paragraph(str(scores.get("raw_score", "N/A")), self.styles['TableCell']),
        #                     Paragraph(str(scores.get("scaled_score", "N/A")), self.styles['TableCell']),
        #                     Paragraph(f"{percentile}%", self.styles['TableCell']),
        #                     Paragraph(scores.get("age_equivalent", "N/A"), self.styles['TableCell']),
        #                     Paragraph(classification, self.styles['TableCell'])
        #                 ])
            
        #     # Add social-emotional/adaptive scores if available
        #     if bayley_social.get("raw_scores"):
        #         social_scores = bayley_social["raw_scores"]
        #         for domain, scores in social_scores.items():
        #             if isinstance(scores, dict) and scores.get("scaled_score"):
        #                 classification = self._get_score_classification(scores.get("scaled_score", 0))
        #                 percentile = self._score_to_percentile(scores.get("scaled_score", 0))
                        
        #                 score_data.append([
        #                     Paragraph(f"<b>{domain.replace('_', ' ').title()}</b>", self.styles['TableCell']),
        #                     Paragraph(str(scores.get("raw_score", "N/A")), self.styles['TableCell']),
        #                     Paragraph(str(scores.get("scaled_score", "N/A")), self.styles['TableCell']),
        #                     Paragraph(f"{percentile}%", self.styles['TableCell']),
        #                     Paragraph(scores.get("age_equivalent", "N/A"), self.styles['TableCell']),
        #                     Paragraph(classification, self.styles['TableCell'])
        #                 ])
            
        #     # Create the scores table with professional styling
        #     scores_table = Table(score_data, 
        #                        colWidths=[1.4*inch, 0.8*inch, 0.9*inch, 0.8*inch, 1.0*inch, 1.5*inch])
            
        #     # Enhanced table styling
        #     scores_table.setStyle(TableStyle([
        #         # Header row styling
        #         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        #         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        #         ('FONTSIZE', (0, 0), (-1, 0), 10),
        #         ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
        #         # Data rows styling
        #         ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        #         ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
        #         ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        #         ('FONTSIZE', (0, 1), (-1, -1), 9),
        #         ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center all except domain names
        #         ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Left align domain names
                
        #         # Borders and grid
        #         ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e0')),
        #         ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1f4788')),
                
        #         # Padding
        #         ('TOPPADDING', (0, 0), (-1, -1), 6),
        #         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        #         ('LEFTPADDING', (0, 0), (-1, -1), 8),
        #         ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                
        #         # Alternating row colors for better readability
        #         ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                
        #         # Highlight low scores in red
        #         ('TEXTCOLOR', (2, 1), (2, -1), colors.HexColor('#e53e3e')),  # Scaled scores
        #     ]))
            
        #     elements.append(scores_table)
        #     elements.append(Spacer(1, 16))
        
        # # Patient info for age comparison
        # patient_info = report_data.get("patient_info", {})
        # chronological_age = patient_info.get("chronological_age", {})
        
        # # Assessment analysis data
        # bayley_analysis = report_data.get("assessment_analysis", {}).get("bayley4", {})
        
        # Generate comprehensive Bayley interpretation
        prompt = await get_prompt(prompt_type="bayley4", report_data=report_data, json_format=True)

        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="bayley4", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="bayley4", json_format=True)
            self.logger.error(f"❌ SP2 response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)
        
        return elements
    
    def _get_score_classification(self, scaled_score: int) -> str:
        """Get classification for scaled scores"""
        if scaled_score >= 16:
            return "Above Average"
        elif scaled_score >= 8:
            return "Average"
        elif scaled_score >= 4:
            return "Below Average"
        else:
            return "Extremely Low"
    
    def _score_to_percentile(self, scaled_score: int) -> int:
        """Convert scaled score to approximate percentile"""
        # Simplified conversion - in real implementation you'd use norm tables
        if scaled_score >= 16:
            return 85
        elif scaled_score >= 13:
            return 75
        elif scaled_score >= 8:
            return 50
        elif scaled_score >= 4:
            return 25
        else:
            return 5
    
    async def _create_sp2_detailed_section(self, report_data: Dict[str, Any]) -> List:
        """Create detailed SP2 section with real-world implications"""
        elements = []
        
        # SP2 header
        header = Paragraph("Sensory Profile 2 (SP2)", self.styles['DomainHeader'])
        elements.append(header)
        elements.append(Spacer(1, 6))
        
        # SP2 analysis data
        sp2_analysis = report_data.get("assessment_analysis", {}).get("sp2", {})
        
        # Generate SP2 interpretation
        sp2_prompt = f"""
        Write a detailed Sensory Profile 2 (SP2) interpretation for a pediatric OT report.
        
        SP2 Analysis: {sp2_analysis}
        
        Requirements:
        - Explain Seeking, Avoiding, Sensitivity, and Registration scores
        - Include specific score interpretations and quadrant analysis
        - Provide real-world implications for grooming, play, and feeding
        - Describe sensory processing patterns and their impact
        - Include recommendations for sensory strategies
        - Use professional sensory integration terminology
        - Connect findings to functional performance in daily activities
        
        Focus on how sensory processing affects daily living skills and participation.
        """
        
        # sp2_narrative = await self._generate_with_openai(sp2_prompt, max_tokens=600)
        
        # narrative_para = Paragraph(sp2_narrative, self.styles['ClinicalBody'])
        # elements.append(narrative_para)
        # elements.append(Spacer(1, 12))

        prompt = await get_prompt(prompt_type="sp2", report_data=report_data, json_format=True)

        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="sp2", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="sp2", json_format=True)
            self.logger.error(f"❌ SP2 response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)
        
        return elements
    
    async def _create_chomps_detailed_section(self, report_data: Dict[str, Any]) -> List:
        """Create detailed ChOMPS section with feeding risk assessment"""
        print("Extracting chomps details")
        elements = []
        
        # ChOMPS header
        header = Paragraph("Chicago Oral Motor and Swallowing Scale (ChOMPS)", 
                          self.styles['DomainHeader'])
        elements.append(header)
        elements.append(Spacer(1, 6))
        
        # ChOMPS analysis data
        chomps_analysis = report_data.get("assessment_analysis", {}).get("chomps", {})
        
        # Generate ChOMPS interpretation
        chomps_prompt = await get_prompt(prompt_type="chomps", report_data=chomps_analysis, json_format=True)
        print("########### PROMPT ##########", chomps_prompt)
        chomps_narrative = await self._generate_with_openai(chomps_prompt, max_tokens=2000)
        chomps_narrative = remove_lang_tags(chomps_narrative)
        try:
            chomps_narrative = json.loads(chomps_narrative)
            await save_response(chomps_narrative, file_name="chomps", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(chomps_narrative, file_name="chomps", json_format=True)
            self.logger.error(f"❌ ChOMPS response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(chomps_narrative)
        elements.extend(body)
        
        # narrative_para = Paragraph(chomps_narrative, self.styles['ClinicalBody'])
        # elements.append(narrative_para)
        # elements.append(Spacer(1, 12))
        
        return elements
    
    async def _create_pedieat_detailed_section(self, report_data: Dict[str, Any]) -> List:
        """Create detailed PediEAT section with symptom interpretation"""
        elements = []
        
        # PediEAT header
        header = Paragraph("Pediatric Eating Assessment Tool (PediEAT)", 
                          self.styles['DomainHeader'])
        elements.append(header)
        elements.append(Spacer(1, 6))
        
        # PediEAT analysis data
        pedieat_analysis = report_data.get("assessment_analysis", {}).get("pedieat", {})
        
        pedieat_prompt = await get_prompt(prompt_type="pedieat", report_data=pedieat_analysis, json_format=True)

        # def parse_pedieat_report(text):
        #     """
        #     Parses the OpenAI PediEAT response into a list of (section_title, content) tuples.
        #     """
        #     pattern = r"\*\*(.+?):\*\*"
        #     matches = list(re.finditer(pattern, text))

        #     sections = []
        #     for i, match in enumerate(matches):
        #         title = match.group(1).strip()
        #         start = match.end()
        #         end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        #         content = text[start:end].strip().replace('\n', ' ')
        #         sections.append((title, content))
        #     return sections

        # def create_story(parsed_sections):
        #     styles = getSampleStyleSheet()
        #     s = []
        #     for title, content in parsed_sections:
        #         if 'SectionTitle' not in styles:
        #             style = styles.add(ParagraphStyle(
        #                 name='SectionTitle',
        #                 fontSize=14,
        #                 leading=16,
        #                 spaceAfter=10,
        #                 spaceBefore=12,
        #                 fontName='Helvetica-Bold'
        #             ))
        #             s.append(style)
        #         else:
        #             s.append(Paragraph(title, styles['SectionTitle']))
                
        #         if 'Content' not in styles:
        #             style = styles.add(ParagraphStyle(
        #                 name='Content',
        #                 fontSize=11,
        #                 leading=14,
        #                 alignment=TA_LEFT
        #             ))
        #             s.append(style)
        #         else:
        #             s.append(Paragraph(content, styles['Content']))
        #         s.append(Spacer(1, 12))
        #     return s
        
        # pedieat_narrative = await self._generate_with_openai(pedieat_prompt, max_tokens=600)
        
        # # narrative_para = Paragraph(pedieat_narrative, self.styles['ClinicalBody'])
        # # elements.append(narrative_para)

        # parsed_sections = parse_pedieat_report(pedieat_narrative)
        # story = create_story(parsed_sections)
        # elements.extend(story)
        # elements.append(Spacer(1, 12))

        pedieat_response = await self._generate_with_openai(pedieat_prompt, max_tokens=1000)
        pedieat_response = remove_lang_tags(pedieat_response)
        try:
            pedieat_response = json.loads(pedieat_response)
            await save_response(pedieat_response, file_name="pedieat", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(pedieat_response, file_name="pedieat", json_format=True)
            self.logger.error(f"❌ PediEAT response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(pedieat_response)
        elements.extend(body)
        
        return elements
    
    async def _create_recommendations_section(self, report_data: Dict[str, Any]) -> List:
        """Create comprehensive recommendations section with enhanced formatting"""
        elements = []
        
        # Enhanced recommendations header
        header = Paragraph("Clinical Recommendations", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 10))
        
        # Generate recommendations using OpenAI or fallback
        recommendations = await self._generate_recommendations(report_data)
        
        # Handle new JSON response format
        if isinstance(recommendations, dict) and "clinical_recommendations" in recommendations:
            rec_section = recommendations["clinical_recommendations"]
            if isinstance(rec_section, dict) and "content" in rec_section and isinstance(rec_section["content"], list):
                recommendations = rec_section["content"]
            else:
                recommendations = []
        
        if recommendations:
            # Introduction paragraph
            intro_text = ("Based on the comprehensive assessment findings and observed functional limitations, "
                         "the following evidence-based recommendations are provided to support optimal "
                         "developmental progress and functional independence:")
            
            intro_para = Paragraph(intro_text, self.styles['ClinicalBody'])
            elements.append(intro_para)
            elements.append(Spacer(1, 12))
            
            # Priority recommendations header
            priority_header = Paragraph("Priority Intervention Areas", self.styles['KeyFindings'])
            elements.append(priority_header)
            elements.append(Spacer(1, 8))
            
            # Process and format each recommendation with enhanced styling
            for i, recommendation in enumerate(recommendations[:3], 1):  # Top 3 as priority
                if isinstance(recommendation, str):
                    clean_rec = recommendation.strip().lstrip('•-').strip()
                    if not clean_rec.endswith('.'):
                        clean_rec += '.'
                    formatted_rec = f"<b>{i}.</b> {clean_rec}"
                    rec_para = Paragraph(formatted_rec, self.styles['RecommendationItem'])
                    elements.append(rec_para)
                    elements.append(Spacer(1, 6))
                else:
                    # If it's already a flowable (e.g., ListFlowable), just add it
                    elements.append(recommendation)
                    elements.append(Spacer(1, 6))
            
            # Additional recommendations if available
            if len(recommendations) > 3:
                additional_header = Paragraph("Additional Considerations", self.styles['DomainHeader'])
                elements.append(additional_header)
                elements.append(Spacer(1, 8))
                
                for i, recommendation in enumerate(recommendations[3:], 4):
                    if isinstance(recommendation, str):
                        clean_rec = recommendation.strip().lstrip('•-').strip()
                        if not clean_rec.endswith('.'):
                            clean_rec += '.'
                        formatted_rec = f"<b>{i}.</b> {clean_rec}"
                        rec_para = Paragraph(formatted_rec, self.styles['ClinicalBody'])
                        elements.append(rec_para)
                        elements.append(Spacer(1, 4))
                    else:
                        elements.append(recommendation)
                        elements.append(Spacer(1, 4))
            
            # Service frequency recommendation with highlighting
            elements.append(Spacer(1, 12))
            frequency_header = Paragraph("Recommended Service Frequency", self.styles['KeyFindings'])
            elements.append(frequency_header)
            elements.append(Spacer(1, 6))
            
            frequency_text = ("Based on assessment findings and identified areas of need, occupational therapy "
                            "services are recommended at a frequency of 2-3 times per week for 45-60 minute "
                            "sessions to address developmental delays and functional limitations identified in "
                            "this evaluation.")
            
            frequency_para = Paragraph(frequency_text, self.styles['RecommendationItem'])
            elements.append(frequency_para)
            
        else:
            # Fallback if no recommendations generated
            fallback_text = ("Comprehensive recommendations will be developed based on ongoing assessment "
                           "findings and family priorities. A detailed intervention plan will be provided "
                           "following further clinical observation and family consultation.")
            
            fallback_para = Paragraph(fallback_text, self.styles['ClinicalBody'])
            elements.append(fallback_para)
        
        elements.append(Spacer(1, 16))
        return elements
    
    async def _create_ot_goals_section(self, report_data: Dict[str, Any]) -> List:
        """Create OT goals section with proper report elements"""
        elements = []
        
        # Section header
        header = Paragraph("Occupational Therapy Goals", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 8))
        
        # Generate goals using helper method
        goals = await self._generate_ot_goals(report_data)
        
        # Add each goal as a paragraph
        # for i, goal in enumerate(goals, 1):
        #     goal_text = f"{i}. {goal}"
        #     goal_para = Paragraph(goal_text, self.styles['ClinicalBody'])
        #     elements.append(goal_para)
        #     elements.append(Spacer(1, 6))
        
        # elements.append(Spacer(1, 12))
        elements.extend(goals)
        
        return elements
    
    async def _generate_ot_goals(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate specific, measurable OT goals"""
        # patient_info = report_data.get("patient_info", {})
        # child_name = patient_info.get("name", "the child")
        
        # prompt = f"""Generate 4 specific, measurable occupational therapy goals for {child_name} following SMART goal format. Include:
        # - Timeline (within 6 months)
        # - Specific activity/skill
        # - Measurable criteria (4 out of 5 opportunities)
        # - Assistance level
        # - Focus areas: fine motor, visual-motor, bilateral coordination, pre-writing
        
        # Format each goal as a complete sentence with specific metrics."""
        
        # goals_text = await self._generate_with_openai(prompt, max_tokens=400)
        
        # # Parse goals or use defaults
        # if "Within" in goals_text:
        #     goals = [goal.strip() for goal in goals_text.split('\n') if goal.strip() and ('Within' in goal or goal[0].isdigit())]
        # else:
        #     goals = [
        #         "Within six months, the child will stack 5 one-inch blocks independently in 4 out of 5 opportunities with no more than 2 prompts, to improve visual-motor coordination and hand stability.",
        #         "Within six months, the child will string 2–3 large beads onto a string in 4 out of 5 opportunities with no more than moderate assistance, demonstrating bilateral hand use and midline crossing.",
        #         "Within six months, the child will use a pincer grasp (thumb and index finger) to pick up and release small objects in 4 out of 5 opportunities with no more than 2 prompts.",
        #         "Within six months, the child will spontaneously scribble on paper using a crayon or marker in 4 out of 5 opportunities with no more than moderate prompts, to promote pre-writing and fine motor development."
        #     ]
        
        # return goals[:4]  # Limit to 4 goals
        elements = []
        prompt = await get_prompt(prompt_type="ot_goals", report_data=report_data, json_format=True)
        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="ot_goals", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="ot_goals", json_format=True)
            self.logger.error(f"❌ ot_goals response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)
        return elements
    
    def _create_professional_header(self, patient_info: Dict[str, Any]) -> List:
        """Create professional header with FMRC logo and clinic info, matching Sabrina OT Report style"""
        elements = []
        # Centered FMRC logo
        logo_path = self.config.get_header_image_path()
        if os.path.exists(logo_path):
            logo_img = Image(logo_path, width=2.2*inch, height=2.2*inch)
            logo_img.hAlign = 'CENTER'
            elements.append(logo_img)
            elements.append(Spacer(1, 12))
        # Centered clinic info
        clinic_lines = [
            '<b>FMRC Health Group</b>',
            '<b>Occupational Therapy Developmental Evaluation</b>',
            '<b>Vendor #PW8583</b>',
            '1626 Centinela Ave, Suite 108, Inglewood CA 90302',
            'www.fmrchealth.com'
        ]
        for line in clinic_lines:
            elements.append(Paragraph(line, ParagraphStyle(
                name='ClinicHeader', fontName='Helvetica-Bold', fontSize=12, alignment=TA_CENTER, spaceAfter=2, spaceBefore=2)))
        elements.append(Spacer(1, 12))
        # Patient info table (bordered, bold labels)
        patient_data = [
            [Paragraph('<b>Name:</b>', self.styles['Normal']), patient_info.get('name', ''),
             Paragraph('<b>Date of Birth:</b>', self.styles['Normal']), patient_info.get('date_of_birth', '')],
            [Paragraph('<b>Parent/Guardian:</b>', self.styles['Normal']), patient_info.get('parent_guardian', ''),
             Paragraph('<b>Chronological Age:</b>', self.styles['Normal']), patient_info.get('chronological_age', {}).get('formatted', '')],
            [Paragraph('<b>UCI#</b>', self.styles['Normal']), patient_info.get('uci_number', ''),
             Paragraph('<b>Service Coordinator:</b>', self.styles['Normal']), patient_info.get('service_coordinator', '')],
            [Paragraph('<b>Sex:</b>', self.styles['Normal']), patient_info.get('sex', ''),
             Paragraph('<b>Primary Language:</b>', self.styles['Normal']), patient_info.get('language', '')],
            [Paragraph('<b>Examiner:</b>', self.styles['Normal']), 'Fushia Crooms, MOT, OTR/L',
             Paragraph('<b>Date of Report:</b>', self.styles['Normal']), patient_info.get('report_date', '')],
            ['', '', Paragraph('<b>Date of Encounter:</b>', self.styles['Normal']), patient_info.get('encounter_date', '')]
        ]
        patient_table = Table(patient_data, colWidths=[1.5*inch, 2.1*inch, 1.5*inch, 2.1*inch])
        patient_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(patient_table)
        elements.append(Spacer(1, 18))
        return elements

    def _section_header(self, text: str) -> Paragraph:
        """Return a full-width orange section header with bold black text"""
        return Paragraph(
            f'<b>{text}</b>',
            ParagraphStyle(
                name='OrangeSectionHeader',
                fontName='Helvetica-Bold',
                fontSize=13,
                alignment=TA_LEFT,
                textColor=colors.black,
                backColor=colors.HexColor('#F9A825'),
                spaceBefore=12,
                spaceAfter=8,
                leftIndent=0,
                rightIndent=0,
                borderPadding=4,
                leading=16
            )
        )

    # Example usage in section methods:
    # elements.append(self._section_header('Reason for referral and background information'))
    # elements.append(Paragraph(..., ...))

    # For score tables, use blue header row
    def _styled_score_table(self, data, colWidths=None):
        table = Table(data, colWidths=colWidths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('ALIGN', (0,1), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7fafc')]),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        return table

    # Add small logo and page number to every page
    def _add_page_decor(self, canvas, doc):
        # Small logo at top right
        logo_path = self.config.get_header_image_path()
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, doc.pagesize[0] - 1.2*inch, doc.pagesize[1] - 1.1*inch, width=0.8*inch, height=0.8*inch, mask='auto')
        # Page number at bottom right
        page_num = canvas.getPageNumber()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#333333'))
        canvas.drawRightString(doc.pagesize[0] - 0.7*inch, 0.65*inch, f"{page_num}")

    async def _create_background_section(self, report_data: Dict[str, Any]) -> List:
        elements = []
        elements.append(self._section_header('Reason for referral and background information'))
        body = await self._generate_background_narrative(report_data)
        elements.extend(body)
        elements.append(Spacer(1, 12))
        return elements

    async def _create_caregiver_concerns(self, report_data: Dict[str, Any]) -> List:
        elements = []
        elements.append(self._section_header('Caregiver Concerns'))
        body = await self._generate_caregiver_concerns_narrative(report_data)
        elements.extend(body)
        elements.append(Spacer(1, 12))
        return elements

    async def _create_clinical_observations(self, report_data: Dict[str, Any]) -> List:
        elements = []
        elements.append(self._section_header('Observation'))
        body = await self._generate_clinical_observations_narrative(report_data)
        elements.extend(body)
        elements.append(Spacer(1, 12))
        return elements

    def _create_assessment_tools_description(self) -> List:
        elements = []
        elements.append(self._section_header('Assessment Tools'))
        tools_text = ("Bayley Scales of Infant and Toddler Development - Fourth Edition (BSID-4), parent "
                      "report and clinical observation were used as assessment tools for this report.")
        tools_para = Paragraph(tools_text, self.styles['ClinicalBody'])
        elements.append(tools_para)
        elements.append(Spacer(1, 8))
        bayley_header = Paragraph(
            "<b>Bayley Scales of Infant and Toddler Development - Fourth Edition (BSID-4)</b>",
            self.styles['DomainHeader']
        )
        elements.append(bayley_header)
        intro = Paragraph(
            "The Bayley-4 is a norm-referenced assessment for children from birth to 42 months, providing standardized scores in the following developmental domains:",
            self.styles['ClinicalBody']
        )
        elements.append(intro)
        elements.append(Spacer(1, 6))
        bayley_domains = [
            ListItem(Paragraph("<b>1. Cognitive Scale:</b> Assesses problem-solving skills, memory, attention, and concept formation.", self.styles['ClinicalBody'])),
            ListItem(Paragraph("<b>2. Language Scale:</b>", self.styles['ClinicalBody'])),
            ListItem(Paragraph("Receptive Language: Evaluates the child's understanding of words, gestures, and simple instructions.", self.styles['BulletPoint']), leftIndent=36),
            ListItem(Paragraph("Expressive Language: Measures verbal communication, including babbling, single words, and early sentence formation.", self.styles['BulletPoint']), leftIndent=36),
            ListItem(Paragraph("<b>3. Motor Scale:</b>", self.styles['ClinicalBody'])),
            ListItem(Paragraph("Fine Motor: Examines grasping, manipulation of objects, hand-eye coordination, and early writing skills.", self.styles['BulletPoint']), leftIndent=36),
            ListItem(Paragraph("Gross Motor: Evaluates posture, crawling, standing, balance, and walking patterns.", self.styles['BulletPoint']), leftIndent=36),
            ListItem(Paragraph("<b>4. Social-Emotional Scale:</b> Measures the child's ability to interact with others, regulate emotions, and respond to social cues.", self.styles['ClinicalBody'])),
            ListItem(Paragraph("<b>5. Adaptive Behavior Scale:</b> Assesses daily functional tasks, including self-care skills such as feeding, dressing, and toileting.", self.styles['ClinicalBody']))
        ]
        elements.append(ListFlowable(
            bayley_domains,
            bulletType='bullet',
            start='circle',
            leftIndent=18
        ))
        elements.append(Spacer(1, 15))
        return elements
    
    async def _generate_background_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate professional background narrative using actual assessment data"""
        patient_info = report_data.get("patient_info", {})
        patient_name = patient_info.get('name', 'the client')
        age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
        
        # Extract actual assessment data for context
        extracted_data = report_data.get("extracted_data", {})
        bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        bayley_social = extracted_data.get("bayley4_social", {})
        
        self.logger.info(f"📝 Generating background narrative for {patient_name}")
        
        # Create detailed prompt with assessment context
        assessment_context = ""
        if bayley_cognitive.get("raw_scores") or bayley_social.get("raw_scores"):
            assessment_context = f"""
            Assessment Context:
            - Bayley-4 Cognitive/Language/Motor assessment completed
            - Bayley-4 Social-Emotional/Adaptive Behavior assessment completed
            - Patient age: {age}
            - Comprehensive developmental evaluation across multiple domains
            """
        
        # prompt = f"""
        # Write a professional "Reason for referral and background information" section for a pediatric OT evaluation report. 
        
        # Patient: {patient_name} (age: {age})
        
        # {assessment_context}
        
        # Requirements:
        # - Start with "A developmental evaluation was recommended by the Regional Center..."
        # - Explain the purpose: determine current level of performance and guide service frequency recommendations for early intervention
        # - Keep it concise but professional
        # - Use clinical terminology appropriate for a pediatric OT evaluation
        # - Match the tone and format of professional OT reports
        
        # Write 2-3 sentences maximum, similar to this style: "A developmental evaluation was recommended by the Regional Center to determine [patient name]'s current level of performance and to guide service frequency recommendations for early intervention."
        # """
        
        # return await self._generate_with_openai(prompt, max_tokens=150)
        elements = []
        prompt = await get_prompt(prompt_type="background", report_data=report_data, json_format=True)
        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="background", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="background", json_format=True)
            self.logger.error(f"❌ SP2 response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)

        return elements
    
    
    async def _generate_caregiver_concerns_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate detailed caregiver concerns narrative using assessment data"""
        patient_info = report_data.get("patient_info", {})
        parent_name = patient_info.get("parent_guardian", "The caregiver")
        child_name = patient_info.get("name", "the child")
        age = patient_info.get('chronological_age', {}).get('formatted', 'unknown age')
        
        # Extract actual assessment findings for context
        extracted_data = report_data.get("extracted_data", {})
        bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        bayley_social = extracted_data.get("bayley4_social", {})
        
        # Determine areas of concern based on scores
        concerns_context = self._analyze_assessment_concerns(bayley_cognitive, bayley_social)
        
        self.logger.info(f"👥 Generating caregiver concerns for {child_name}")
        
        prompt = f"""
        Write a detailed "Caregiver Concerns" section for a pediatric OT evaluation report.
        
        Details:
        - Child: {child_name} (age: {age})
        - Parent/Guardian: {parent_name}
        
        Assessment findings suggest concerns in: {concerns_context}
        
        Requirements:
        - Start with "{parent_name} expressed concerns regarding {child_name}'s overall development"
        - Include specific, realistic concerns that parents typically report:
          * Attention and focus during activities
          * Fine motor skill development
          * Speech and language development 
          * Behavioral regulation and transitions
          * Social interaction with peers
          * Developmental milestones
        - Use specific examples like "difficulty with transitions", "becomes upset when preferred items removed"
        - Make it personal and realistic to what parents actually say
        - Include both broad developmental concerns and specific behavioral observations
        - Write in professional clinical language but reflecting parental perspective
        - 3-4 sentences, detailed and specific
        
        Example style: "Ms. [Parent] expressed broad concerns regarding her daughter's overall development. She noted that [child] becomes easily upset when the iPad is removed, indicating difficulty with transitions and emotional regulation. Ms. [Parent] also reported challenges with [child]'s ability to attend to fine motor tasks and maintain focus during structured activities. Of primary concern is [child]'s speech and language development, which Ms. [Parent] described as significantly delayed compared to same-age peers."
        """
        
        # return await self._generate_with_openai(prompt, max_tokens=400)
        elements = []
        prompt = await get_prompt(prompt_type="caregiver_concerns", report_data=report_data, json_format=True)
        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="caregiver_concerns", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="caregiver_concerns", json_format=True)
            self.logger.error(f"❌ SP2 response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)

        return elements
    
    async def _generate_clinical_observations_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate detailed clinical observations using assessment data"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "The child")
        
        # Extract actual assessment data for specific observations
        extracted_data = report_data.get("extracted_data", {})
        bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        bayley_social = extracted_data.get("bayley4_social", {})
        clinical_notes = extracted_data.get("clinical_notes", {})
        
        # Analyze scores to determine performance patterns
        performance_analysis = self._analyze_performance_patterns(bayley_cognitive, bayley_social)
        
        # Include any extracted clinical observations
        observations = clinical_notes.get("converted_narratives", [])
        
        self.logger.info(f"👁️ Generating clinical observations for {child_name}")
        
        # prompt = f"""
        # Write a detailed "Observation" section for a pediatric OT evaluation report.
        
        # Patient: {child_name}
        # Performance analysis: {performance_analysis} 
        
        # Specific clinical observations from assessment: {'; '.join(observations[:3]) if observations else 'Standard pediatric assessment observations'}
        
        # Requirements:
        # - Start with "{child_name} participated in an in-clinic evaluation with [his/her] mother present"
        # - Include detailed clinical observations:
        #   * Affect and general presentation (cheerful, cooperative, etc.)
        #   * Muscle tone and range of motion assessment
        #   * Attention span and distractibility levels
        #   * Engagement patterns and task participation
        #   * Response to structured vs. self-directed activities
        #   * Fine motor coordination and visual-motor skills
        #   * Need for cues, redirection, and assistance levels
        #   * Specific behavioral observations during testing
        #   * Impact on standardized testing validity
        
        # - Use professional clinical terminology
        # - Include specific details like "required hand-over-hand assistance", "maximal verbal/visual cues"
        # - Mention testing modifications needed
        # - Write 6-8 sentences with rich clinical detail
        # - Match the professional tone of clinical evaluation reports
        
        # Example elements to include: muscle tone assessment, attention span observations, task engagement, assistance levels needed, behavioral responses, testing conditions impact.
        # """
        
        # return await self._generate_with_openai(prompt, max_tokens=600)
        elements = []
        prompt = await get_prompt(prompt_type="clinical_observations", report_data=report_data, json_format=True)
        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="clinical_observations", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="clinical_observations", json_format=True)
            self.logger.error(f"❌ clinical_observations response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)

        return elements
    
    def _analyze_assessment_concerns(self, bayley_cognitive: Dict, bayley_social: Dict) -> str:
        """Analyze assessment data to identify areas of concern"""
        concerns = []
        
        # Analyze cognitive scores
        if bayley_cognitive.get("scaled_scores"):
            cognitive_scores = bayley_cognitive["scaled_scores"]
            for domain, score in cognitive_scores.items():
                if score < 7:  # Below average range
                    concerns.append(f"{domain.lower()} development")
        
        # Analyze social-emotional scores  
        if bayley_social.get("scaled_scores"):
            social_scores = bayley_social["scaled_scores"]
            for domain, score in social_scores.items():
                if score < 7:
                    concerns.append(f"{domain.lower()} skills")
        
        # Default concerns if no scores available
        if not concerns:
            concerns = ["fine motor development", "attention and focus", "speech and language development", "behavioral regulation"]
        
        return ", ".join(concerns[:4])  # Limit to top 4 concerns
    
    def _analyze_performance_patterns(self, bayley_cognitive: Dict, bayley_social: Dict) -> str:
        """Analyze performance patterns from assessment scores"""
        patterns = []
        
        # Analyze cognitive performance
        if bayley_cognitive.get("scaled_scores"):
            cog_scores = list(bayley_cognitive["scaled_scores"].values())
            avg_score = sum(cog_scores) / len(cog_scores) if cog_scores else 0
            
            if avg_score < 7:
                patterns.append("below average cognitive-motor performance")
            elif avg_score > 13:
                patterns.append("above average cognitive-motor abilities")
            else:
                patterns.append("mixed cognitive-motor profile")
        
        # Analyze social-emotional performance
        if bayley_social.get("scaled_scores"):
            social_scores = list(bayley_social["scaled_scores"].values())
            avg_score = sum(social_scores) / len(social_scores) if social_scores else 0
            
            if avg_score < 7:
                patterns.append("challenges in social-emotional development")
            elif avg_score > 13:
                patterns.append("strengths in social-emotional areas")
            else:
                patterns.append("typical social-emotional functioning")
        
        return "; ".join(patterns) if patterns else "varied performance across developmental domains"
    
    async def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate evidence-based recommendations"""
        prompt = """Generate 4-6 professional therapy recommendations for a pediatric client based on comprehensive assessment findings. Include:
        - Physical Therapy
        - Speech Therapy  
        - Occupational Therapy with frequency
        - Early intervention services
        Use bullet point format, be specific and professional."""
        
        # recommendations_text = await self._generate_with_openai(prompt, max_tokens=300)
        
        # # Parse into list or use default
        # if "•" in recommendations_text:
        #     recommendations = [rec.strip() for rec in recommendations_text.split("•") if rec.strip()]
        # else:
        #     recommendations = [
        #         "Physical Therapy",
        #         "Speech Therapy",
        #         "Infant Stim",
        #         "Occupational Therapy 2x/week"
        #     ]
        
        # return recommendations
        elements = []
        prompt = await get_prompt(prompt_type="recommendations", report_data=report_data, json_format=True)
        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="recommendations", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="recommendations", json_format=True)
            self.logger.error(f"❌ recommendations response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)

        return elements
    
    async def _create_professional_summary(self, report_data: Dict[str, Any]) -> List:
        """Create comprehensive professional summary section"""
        elements = []
        
        header = Paragraph("Summary:", self.styles['SectionHeader'])
        elements.append(header)
        
        # Generate comprehensive summary using enhanced method
        summary_text = await self._generate_professional_summary(report_data)
        
        # summary_para = Paragraph(summary_text, self.styles['ClinicalBody'])
        # elements.append(summary_para)
        # elements.append(Spacer(1, 15))
        elements.extend(summary_text)
        
        return elements
    
    def _create_signature_block(self) -> List:
        """Create professional signature block with enhanced formatting"""
        elements = []
        
        # Add extra space before signature
        elements.append(Spacer(1, 24))
        
        # Professional signature section with border
        elements.append(PageBreak())  # Start signature on new page if needed
        
        # Signature header
        sig_header = Paragraph("Report Prepared By", self.styles['SectionHeader'])
        elements.append(sig_header)
        elements.append(Spacer(1, 12))
        
        # Create signature table with professional layout
        sig_data = [
            # Signature line
            ["Signature: ___________________________________", "Date: _______________"],
            ["", ""],
            # Professional credentials
            ["Fushia Crooms, MOT, OTR/L", ""],
            ["Occupational Therapist", ""],
            ["License #: OTR/L12345", ""]
        ]
        
        sig_table = Table(sig_data, colWidths=[4.5*inch, 2*inch])
        sig_table.setStyle(TableStyle([
            # General styling
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Signature line styling
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            
            # Professional name and credentials
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (0, 2), 12),
            ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor('#1f4788')),
            
            # Title and license
            ('TEXTCOLOR', (0, 3), (0, 4), colors.HexColor('#4a5568')),
            ('FONTSIZE', (0, 3), (0, 4), 10),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(sig_table)
        elements.append(Spacer(1, 20))
        
        # Contact information section
        contact_header = Paragraph("Contact Information", self.styles['DomainHeader'])
        elements.append(contact_header)
        elements.append(Spacer(1, 8))
        
        # Professional contact information table
        contact_data = [
            ["Organization:", "FMRC Health Group"],
            ["Address:", "1626 Centinela Ave, Suite 108"],
            ["", "Inglewood, CA 90302"],
            ["Phone:", "(555) 123-4567"],
            ["Email:", "fcrooms@fmrchealth.com"],
            ["Website:", "www.fmrchealth.com"]
        ]
        
        contact_table = Table(contact_data, colWidths=[1.2*inch, 4*inch])
        contact_table.setStyle(TableStyle([
            # Background and borders
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            
            # Text styling
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
            
            # Alignment
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(contact_table)
        elements.append(Spacer(1, 16))
        
        # Footer disclaimer
        disclaimer = Paragraph(
            "<i>This report contains confidential medical information and is intended solely for the use of "
            "the identified patient and authorized personnel. Distribution or reproduction without written "
            "consent is prohibited.</i>",
            self.styles['Footer']
        )
        elements.append(disclaimer)
        
        return elements
    
    async def _generate_professional_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate comprehensive professional summary"""
        # patient_info = report_data.get("patient_info", {})
        # child_name = patient_info.get("name", "The child")
        # age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
        
        # Extract and analyze all assessment data
        # extracted_data = report_data.get("extracted_data", {})
        # bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        # bayley_social = extracted_data.get("bayley4_social", {})
        
        # Analyze overall performance pattern
        # overall_analysis = self._generate_overall_performance_analysis(bayley_cognitive, bayley_social)
        
        # Identify strengths and needs
        # strengths = self._identify_assessment_strengths(bayley_cognitive, bayley_social)
        # needs = self._identify_assessment_needs(bayley_cognitive, bayley_social)
        
        # prompt = f"""
        # Write a comprehensive professional "Summary" section for {child_name} ({age}) based on Bayley-4 assessment findings.
        
        # Overall Performance Analysis: {overall_analysis}
        
        # Key Strengths: {strengths}
        # Areas of Need: {needs}
        
        # Requirements:
        # - Start with "{child_name} (chronological age: {age}) was assessed using multiple standardized pediatric assessment tools..."
        # - Include specific delay percentages where applicable
        # - Mention both areas of strength and areas requiring intervention
        # - Discuss impact on functional performance and daily activities
        # - Recommend multidisciplinary intervention approach
        # - Include prognosis and benefit from services
        # - Address family involvement and education needs
        # - Mention regular monitoring and reassessment
        # - Use professional clinical language typical of pediatric OT summaries
        # - Write 6-8 sentences comprehensive summary
        
        # Example elements:
        # - "The comprehensive evaluation revealed both areas of strength and areas requiring targeted intervention support"
        # - "Based on the assessment findings, occupational therapy services are recommended..."
        # - "A collaborative, family-centered approach involving [services] will be beneficial..."
        # - "Regular monitoring and reassessment will be important to track progress..."
        # - "This assessment provides a foundation for developing an individualized intervention plan..."
        
        # Focus on evidence-based conclusions and specific recommendations based on actual assessment findings.
        # """
        
        # return await self._generate_with_openai(prompt, max_tokens=600)

        elements = []
        prompt = await get_prompt(prompt_type="professional_summary", report_data=report_data, json_format=True)
        response = await self._generate_with_openai(prompt, max_tokens=1000)
        response = remove_lang_tags(response)
        try:
            response = json.loads(response)
            await save_response(response, file_name="professional_summary", json_format=True)
        except json.JSONDecodeError as e:
            print(format_exc())
            await save_response(response, file_name="professional_summary", json_format=True)
            self.logger.error(f"❌ professional_summary response parsing failed: {e}")
            raise
        body = await format_data_for_pdf(response)
        elements.extend(body)
        return elements
    
    def _generate_overall_performance_analysis(self, bayley_cognitive: Dict, bayley_social: Dict) -> str:
        """Generate overall performance analysis from assessment scores"""
        analysis_points = []
        
        # Analyze cognitive domain scores
        if bayley_cognitive.get("scaled_scores"):
            cog_scores = list(bayley_cognitive["scaled_scores"].values())
            avg_cog = sum(cog_scores) / len(cog_scores) if cog_scores else 0
            
            if avg_cog < 7:
                analysis_points.append("significant delays in cognitive-motor domains")
            elif avg_cog > 13:
                analysis_points.append("above-average cognitive-motor abilities")
            else:
                analysis_points.append("mixed cognitive-motor profile with areas of both strength and need")
        
        # Analyze social-emotional scores
        if bayley_social.get("scaled_scores"):
            social_scores = list(bayley_social["scaled_scores"].values())
            avg_social = sum(social_scores) / len(social_scores) if social_scores else 0
            
            if avg_social < 7:
                analysis_points.append("challenges in social-emotional and adaptive behavior development")
            elif avg_social > 13:
                analysis_points.append("strengths in social-emotional functioning")
            else:
                analysis_points.append("typical social-emotional development with some areas for growth")
        
        return "; ".join(analysis_points) if analysis_points else "comprehensive developmental evaluation across multiple domains"
    
    def _identify_assessment_strengths(self, bayley_cognitive: Dict, bayley_social: Dict) -> str:
        """Identify strengths from assessment data"""
        strengths = []
        
        # Check for cognitive strengths
        if bayley_cognitive.get("scaled_scores"):
            for domain, score in bayley_cognitive["scaled_scores"].items():
                if score >= 10:
                    strengths.append(f"{domain.lower()}")
        
        # Check for social-emotional strengths
        if bayley_social.get("scaled_scores"):
            for domain, score in bayley_social["scaled_scores"].items():
                if score >= 10:
                    strengths.append(f"{domain.lower()}")
        
        return ", ".join(strengths[:3]) if strengths else "emerging developmental skills, social engagement, learning potential"
    
    def _identify_assessment_needs(self, bayley_cognitive: Dict, bayley_social: Dict) -> str:
        """Identify areas of need from assessment data"""
        needs = []
        
        # Check for cognitive needs
        if bayley_cognitive.get("scaled_scores"):
            for domain, score in bayley_cognitive["scaled_scores"].items():
                if score < 8:
                    needs.append(f"{domain.lower()}")
        
        # Check for social-emotional needs
        if bayley_social.get("scaled_scores"):
            for domain, score in bayley_social["scaled_scores"].items():
                if score < 8:
                    needs.append(f"{domain.lower()}")
        
        return ", ".join(needs[:4]) if needs else "fine motor coordination, attention and focus, communication skills, behavioral regulation"
    
    async def _generate_with_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using OpenAI with clinical context"""
        self.logger.info(f"🤖 Generating text with OpenAI (max_tokens: {max_tokens})")
        
        if not self.openai_client:
            self.logger.warning("⚠️ OpenAI client not available, using fallback")
            return await self._generate_fallback_text(prompt)
        
        # Get configured model
        model = get_openai_model()
        
        try:
            self.logger.info(f"📡 Sending request to OpenAI API with model: {model}...")
            # response = self.openai_client.chat.completions.create(
            #     model=model,
            #     messages=[
            #         {
            #             "role": "system",
            #             "content": "You are a professional pediatric occupational therapist writing clinical evaluation reports. Use sophisticated clinical terminology, evidence-based interpretations, and maintain a professional, objective tone. Base your responses on standard pediatric developmental assessments and best practices in occupational therapy."
            #         },
            #         {
            #             "role": "user",
            #             "content": prompt
            #         }
            #     ],
            #     max_tokens=max_tokens,
            #     temperature=0.3
            # )
            
            # generated_text = response.choices[0].message.content.strip()
            generated_text = graph_invoke(prompt)
            self.logger.info(f"✅ OpenAI generation successful ({len(generated_text)} characters)")
            print("############ ", generated_text)
            return generated_text
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI generation failed: {e}")
            self.logger.info("🔄 Falling back to enhanced template text")
            return await self._generate_fallback_text(prompt)
    
    async def _generate_consolidated_report_narratives(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate ALL report narratives in a single OpenAI call to save tokens"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "the child")
        age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
        parent_name = patient_info.get("parent_guardian", "The caregiver")
        
        # Extract assessment context
        extracted_data = report_data.get("extracted_data", {})
        assessment_analysis = report_data.get("assessment_analysis", {})
        
        consolidated_prompt = f"""
        Generate ALL sections for a pediatric OT evaluation report for {child_name} (age: {age}). 
        
        Patient Info: {child_name}, age {age}, caregiver: {parent_name}
        Assessment Data: {assessment_analysis}
        
        Generate these EXACT sections with clear section markers:
        
        [BACKGROUND]
        Write 2-3 sentences: "A developmental evaluation was recommended by the Regional Center to determine {child_name}'s current level of performance..."
        
        [CAREGIVER_CONCERNS]  
        Write 3-4 sentences about {parent_name}'s concerns regarding {child_name}'s development, attention, fine motor skills, transitions, etc.
        
        [OBSERVATIONS]
        Write 6-8 sentences about {child_name}'s participation in evaluation, muscle tone, attention span, task engagement, assistance needed.
        
        [SUMMARY]
        Write comprehensive 6-8 sentence summary covering assessment findings, strengths, needs, intervention recommendations.
        
        [RECOMMENDATIONS]
        List 4-6 therapy recommendations (PT, ST, OT frequency, early intervention).
        
        [GOALS]
        List 4 specific SMART OT goals with timelines, measurable criteria, assistance levels.
        
        Use professional clinical language. Keep each section focused and concise.
        """
        
        try:
            # Single consolidated OpenAI call instead of 11 separate calls
            consolidated_response = await self._generate_with_openai(consolidated_prompt, max_tokens=2000)
            
            # Parse the response into sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in consolidated_response.split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    # Save previous section
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    # Start new section
                    current_section = line[1:-1].lower()
                    current_content = []
                elif line and current_section:
                    current_content.append(line)
            
            # Save last section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Provide fallbacks for missing sections
            fallback_sections = {
                'background': f"A developmental evaluation was recommended by the Regional Center to determine {child_name}'s current level of performance and to guide service frequency recommendations for early intervention.",
                'caregiver_concerns': f"{parent_name} expressed concerns regarding {child_name}'s overall development, including attention span, fine motor skills, and behavioral regulation during transitions.",
                'observations': f"{child_name} participated in an in-clinic evaluation with cooperative affect but variable attention span. Muscle tone appeared typical with tasks requiring verbal cues and hand-over-hand assistance.",
                'summary': f"{child_name} (chronological age: {age}) was assessed using standardized pediatric assessment tools. The evaluation revealed areas requiring targeted intervention support through occupational therapy services.",
                'recommendations': "• Physical Therapy\n• Speech Therapy\n• Occupational Therapy 2x/week\n• Early intervention services",
                'goals': "1. Within six months, the child will stack 5 blocks independently in 4/5 opportunities with minimal prompts.\n2. Within six months, the child will string 3 beads with moderate assistance in 4/5 opportunities.\n3. Within six months, the child will use pincer grasp for small objects in 4/5 opportunities.\n4. Within six months, the child will scribble on paper spontaneously in 4/5 opportunities."
            }
            
            # Ensure all sections are present
            for section, fallback in fallback_sections.items():
                if section not in sections or not sections[section]:
                    sections[section] = fallback
            
            self.logger.info(f"✅ Generated {len(sections)} report sections in single OpenAI call")
            return sections
            
        except Exception as e:
            self.logger.error(f"❌ Consolidated generation failed: {e}")
            # Return all fallbacks
            return {
                'background': f"A developmental evaluation was recommended by the Regional Center to determine {child_name}'s current level of performance and to guide service frequency recommendations for early intervention.",
                'caregiver_concerns': f"{parent_name} expressed concerns regarding {child_name}'s overall development, including attention span, fine motor skills, and behavioral regulation during transitions.",
                'observations': f"{child_name} participated in an in-clinic evaluation with cooperative affect but variable attention span. Muscle tone appeared typical with tasks requiring verbal cues and hand-over-hand assistance.",
                'summary': f"{child_name} (chronological age: {age}) was assessed using standardized pediatric assessment tools. The evaluation revealed areas requiring targeted intervention support through occupational therapy services.",
                'recommendations': "• Physical Therapy\n• Speech Therapy\n• Occupational Therapy 2x/week\n• Early intervention services",
                'goals': "1. Within six months, the child will stack 5 blocks independently in 4/5 opportunities with minimal prompts.\n2. Within six months, the child will string 3 beads with moderate assistance in 4/5 opportunities.\n3. Within six months, the child will use pincer grasp for small objects in 4/5 opportunities.\n4. Within six months, the child will scribble on paper spontaneously in 4/5 opportunities."
            }
    
    async def _generate_fallback_text(self, prompt: str) -> str:
        """Generate enhanced fallback text when OpenAI is not available"""
        self.logger.info("📝 Using enhanced fallback text generation")
        
        # Extract key context from the prompt to generate better fallback text
        if "background" in prompt.lower():
            # Extract patient name and age from prompt
            patient_name = "the client"
            if "Patient:" in prompt:
                try:
                    patient_name = prompt.split("Patient:")[1].split("(")[0].strip()
                except:
                    pass
            
            fallback_text = f"A developmental evaluation was recommended by the Regional Center to determine {patient_name}'s current level of performance and to guide service frequency recommendations for early intervention."
            
        elif "caregiver concerns" in prompt.lower():
            # Extract patient and parent information
            patient_name = "the child"
            parent_name = "The caregiver"
            
            if "Child:" in prompt:
                try:
                    patient_name = prompt.split("Child:")[1].split("\n")[0].strip()
                except:
                    pass
            
            if "Parent/Guardian:" in prompt:
                try:
                    parent_name = prompt.split("Parent/Guardian:")[1].split("\n")[0].strip()
                except:
                    pass
            
            # Enhanced caregiver concerns with specific details
            fallback_text = f"{parent_name} expressed broad concerns regarding {patient_name}'s overall development. She noted challenges with attention span and focus during structured activities, indicating difficulty with sustained engagement. {parent_name} also reported concerns about fine motor skill development and {patient_name}'s ability to manipulate small objects. Of particular concern is {patient_name}'s communication development and behavioral regulation during transitions between activities."
            
        elif "observation" in prompt.lower():
            # Enhanced clinical observations
            patient_name = "The child"
            if "Patient:" in prompt:
                try:
                    patient_name = prompt.split("Patient:")[1].split("\n")[0].strip()
                except:
                    pass
            
            fallback_text = f"{patient_name} participated in an in-clinic evaluation with the caregiver present. {patient_name} presented with a cooperative affect initially but demonstrated variable attention span throughout the assessment. Muscle tone appeared typical for chronological age, with adequate range of motion observed. However, participation was impacted by distractibility and need for frequent redirection. During structured tasks, {patient_name} required verbal and visual cues to maintain engagement. Fine motor coordination showed areas for development, with tasks requiring hand-over-hand assistance for completion. These factors impacted standardized testing and required modifications to maintain participation."
            
        elif any(domain in prompt.lower() for domain in ["cognitive", "receptive", "expressive", "fine motor", "gross motor", "social-emotional"]):
            # Domain-specific enhanced text
            domain_name = "this domain"
            for domain in ["Cognitive", "Receptive Communication", "Expressive Communication", "Fine Motor", "Gross Motor", "Social-Emotional"]:
                if domain.lower() in prompt.lower():
                    domain_name = domain
                    break
            
            patient_name = "The child"
            if "Patient:" in prompt:
                try:
                    patient_name = prompt.split("Patient:")[1].split("\n")[0].strip()
                except:
                    pass
            
            # Extract any score information from the prompt
            score_info = ""
            if "Scaled Score:" in prompt:
                try:
                    score_info = "Assessment scores and clinical observations indicate areas for targeted intervention. "
                except:
                    pass
            
            fallback_text = f"{patient_name} demonstrated variable performance in {domain_name} during assessment. {score_info}Clinical observations revealed both emerging skills and areas requiring support. During testing activities, {patient_name} showed intermittent engagement with tasks requiring sustained attention and effort. Performance patterns suggest the need for structured intervention to support skill development in this domain. These findings indicate that {patient_name} would benefit from targeted therapeutic intervention."
            
        elif "summary" in prompt.lower():
            # Enhanced comprehensive summary
            patient_name = "The child"
            age = "unknown age"
            
            if "Patient:" in prompt:
                try:
                    patient_name = prompt.split("Patient:")[1].split("(")[0].strip()
                    age = prompt.split("(")[1].split(")")[0].strip()
                except:
                    pass
            
            fallback_text = f"{patient_name} (chronological age: {age}) was assessed using multiple standardized pediatric assessment tools to evaluate developmental functioning across cognitive, motor, sensory processing, and adaptive behavior domains. The comprehensive evaluation revealed both areas of emerging strength and areas requiring targeted intervention support. Based on the assessment findings, occupational therapy services are recommended to address identified areas of need and support optimal developmental progression. A collaborative, family-centered approach involving occupational therapy and related services will be beneficial to address the client's comprehensive developmental needs. Regular monitoring and reassessment will be important to track progress and adjust intervention strategies as needed."
            
        elif "goals" in prompt.lower():
            # Enhanced OT goals
            patient_name = "the child"
            if "Patient:" in prompt:
                try:
                    patient_name = prompt.split("Patient:")[1].split("\n")[0].strip()
                except:
                    pass
            
            goals = [
                f"Within six months, {patient_name} will stack 4-5 one-inch blocks independently in 4 out of 5 opportunities with minimal verbal prompts, to improve visual-motor coordination and hand stability for age-appropriate play skills.",
                f"Within six months, {patient_name} will string 2-3 large beads onto a shoelace in 4 out of 5 opportunities with moderate assistance, demonstrating bilateral hand coordination and crossing midline.",
                f"Within six months, {patient_name} will use a pincer grasp to pick up and place small objects (cheerios, blocks) in 4 out of 5 opportunities with minimal cues, improving fine motor precision for functional tasks.",
                f"Within six months, {patient_name} will spontaneously scribble on paper using an age-appropriate grasp in 4 out of 5 opportunities with minimal prompts, promoting pre-writing skill development and creative expression."
            ]
            fallback_text = "\n".join([f"{i+1}. {goal}" for i, goal in enumerate(goals)])
            
        else:
            # Generic enhanced fallback
            fallback_text = "Based on comprehensive standardized assessment findings, the client demonstrates a mixed profile of developmental strengths and areas requiring targeted intervention support. Clinical observations and assessment results indicate the need for structured therapeutic intervention to promote optimal developmental outcomes."
        
        self.logger.info(f"✅ Enhanced fallback text generated ({len(fallback_text)} characters)")
        return fallback_text 
    
    async def _get_consolidated_narrative(self, report_data: Dict[str, Any], section_key: str) -> str:
        """Get pre-generated narrative from consolidated narratives to avoid additional OpenAI calls"""
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        
        if section_key in consolidated_narratives and consolidated_narratives[section_key]:
            return consolidated_narratives[section_key]
        
        # Fallback if not found
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "the child")
        parent_name = patient_info.get("parent_guardian", "The caregiver")
        age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
        
        fallbacks = {
            'background': f"A developmental evaluation was recommended by the Regional Center to determine {child_name}'s current level of performance and to guide service frequency recommendations for early intervention.",
            'caregiver_concerns': f"{parent_name} expressed concerns regarding {child_name}'s overall development, including attention span, fine motor skills, and behavioral regulation during transitions.",
            'observations': f"{child_name} participated in an in-clinic evaluation with cooperative affect but variable attention span. Muscle tone appeared typical with tasks requiring verbal cues and hand-over-hand assistance.",
            'summary': f"{child_name} (chronological age: {age}) was assessed using standardized pediatric assessment tools. The evaluation revealed areas requiring targeted intervention support through occupational therapy services.",
        }
        
        return fallbacks.get(section_key, f"Clinical assessment completed for {child_name}.")
    
    # OPTIMIZED METHODS - Use consolidated narratives instead of individual OpenAI calls
    async def _generate_background_narrative_optimized(self, report_data: Dict[str, Any]) -> str:
        """Use consolidated narrative instead of individual OpenAI call"""
        return await self._get_consolidated_narrative(report_data, 'background')
    
    async def _generate_caregiver_concerns_narrative_optimized(self, report_data: Dict[str, Any]) -> str:
        """Use consolidated narrative instead of individual OpenAI call"""
        return await self._get_consolidated_narrative(report_data, 'caregiver_concerns')
    
    async def _generate_clinical_observations_narrative_optimized(self, report_data: Dict[str, Any]) -> str:
        """Use consolidated narrative instead of individual OpenAI call"""
        return await self._get_consolidated_narrative(report_data, 'observations')
    
    async def _generate_professional_summary_optimized(self, report_data: Dict[str, Any]) -> str:
        """Use consolidated narrative instead of individual OpenAI call"""
        return await self._get_consolidated_narrative(report_data, 'summary')
    
    async def _generate_recommendations_optimized(self, report_data: Dict[str, Any]) -> List[str]:
        """Use consolidated narrative instead of individual OpenAI call"""
        recommendations_text = await self._get_consolidated_narrative(report_data, 'recommendations')
        
        # Parse into list
        if "•" in recommendations_text:
            recommendations = [rec.strip() for rec in recommendations_text.split("•") if rec.strip()]
        elif "\n" in recommendations_text:
            recommendations = [rec.strip() for rec in recommendations_text.split("\n") if rec.strip()]
        else:
            recommendations = [
                "Physical Therapy",
                "Speech Therapy", 
                "Occupational Therapy 2x/week",
                "Early intervention services"
            ]
        
        return recommendations
    
    async def _generate_ot_goals_optimized(self, report_data: Dict[str, Any]) -> List[str]:
        """Use consolidated narrative instead of individual OpenAI call"""
        goals_text = await self._get_consolidated_narrative(report_data, 'goals')
        
        # Parse goals
        if "Within" in goals_text:
            goals = [goal.strip() for goal in goals_text.split('\n') if goal.strip() and ('Within' in goal or goal[0].isdigit())]
        else:
            goals = [
                "Within six months, the child will stack 5 blocks independently in 4/5 opportunities with minimal prompts.",
                "Within six months, the child will string 3 beads with moderate assistance in 4/5 opportunities.",
                "Within six months, the child will use pincer grasp for small objects in 4/5 opportunities.",
                "Within six months, the child will scribble on paper spontaneously in 4/5 opportunities."
            ]
        
        return goals[:4]