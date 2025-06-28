import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

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

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

class OpenAIEnhancedReportGenerator:
    """Professional OT Report Generator using OpenAI for clinical narratives"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🧠 Initializing OpenAI Enhanced Report Generator...")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.logger.info("✅ ReportLab styles configured")
        
        # Initialize OpenAI
        self.openai_client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        self.logger.info("🔑 Initializing OpenAI client...")
        
        if not OPENAI_AVAILABLE:
            self.logger.error("❌ OpenAI library not available")
            return
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.warning("⚠️ OPENAI_API_KEY environment variable not set")
            self.logger.info("💡 Professional narratives will use fallback templates")
            return
        
        try:
            # Initialize OpenAI client with basic configuration
            self.logger.info("🔧 Creating OpenAI client...")
            
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
            
            # Test API connection with a simple call
            try:
                self.logger.info("🧪 Testing OpenAI API connection...")
                test_response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                self.logger.info("✅ OpenAI API connection test successful")
            except Exception as test_error:
                self.logger.error(f"❌ OpenAI API test failed: {test_error}")
                self.logger.warning("⚠️ Will use fallback text generation")
                # Don't set client to None here, as we might still be able to use it
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles matching the sample report"""
        # Header style for main title
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Clinic info style
        self.styles.add(ParagraphStyle(
            name='ClinicInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Domain header style
        self.styles.add(ParagraphStyle(
            name='DomainHeader',
            parent=self.styles['Heading3'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=8,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Clinical body text
        self.styles.add(ParagraphStyle(
            name='ClinicalBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=2,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            fontName='Helvetica'
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=4,
            spaceBefore=2,
            leftIndent=20,
            bulletIndent=10,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
    
    async def generate_comprehensive_report(self, report_data: Dict[str, Any], session_id: str) -> str:
        """Generate comprehensive professional OT report using OpenAI enhancement"""
        self.logger.info(f"📝 Starting comprehensive report generation for session: {session_id}")
        
        patient_name = report_data.get("patient_info", {}).get("name", "Unknown")
        self.logger.info(f"👤 Patient: {patient_name}")
        
        output_path = os.path.join("outputs", f"professional_ot_report_{session_id}.pdf")
        self.logger.info(f"📁 Output path: {output_path}")
        
        try:
            # Create the PDF document
            self.logger.info("📄 Creating PDF document...")
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
                leftMargin=1*inch,
                rightMargin=1*inch
            )
            
            # Build the report content
            story = []
            
            # Header section (clinic branding and patient info)
            self.logger.info("📋 Generating header section...")
            story.extend(self._create_professional_header(report_data["patient_info"]))
            
            # Main report sections
            self.logger.info("📝 Generating background section...")
            story.extend(await self._create_background_section(report_data))
            
            self.logger.info("👥 Generating caregiver concerns...")
            story.extend(await self._create_caregiver_concerns(report_data))
            
            self.logger.info("👁️ Generating clinical observations...")
            story.extend(await self._create_clinical_observations(report_data))
            
            self.logger.info("🔧 Adding assessment tools description...")
            story.extend(self._create_assessment_tools_description())
            
            self.logger.info("📊 Generating Bayley results...")
            story.extend(await self._create_bayley_results(report_data))
            
            self.logger.info("💡 Generating recommendations...")
            story.extend(await self._create_recommendations_section(report_data))
            
            self.logger.info("📋 Generating professional summary...")
            story.extend(await self._create_professional_summary(report_data))
            
            self.logger.info("🎯 Generating OT goals...")
            story.extend(await self._create_ot_goals(report_data))
            
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
            self.logger.error(f"❌ Failed to generate comprehensive report: {e}")
            raise
    
    def _create_professional_header(self, patient_info: Dict[str, Any]) -> List:
        """Create professional header matching sample format"""
        elements = []
        
        # FMRC Health Group header
        title = Paragraph("FMRC Health Group", self.styles['ReportTitle'])
        elements.append(title)
        
        subtitle = Paragraph("Occupational Therapy Developmental Evaluation", self.styles['ClinicInfo'])
        elements.append(subtitle)
        
        vendor = Paragraph("Vendor #PW8583", self.styles['ClinicInfo'])
        elements.append(vendor)
        
        address = Paragraph("1626 Centinela Ave, Suite 108, Inglewood CA 90302", self.styles['ClinicInfo'])
        elements.append(address)
        
        website = Paragraph("www.fmrchealth.com", self.styles['ClinicInfo'])
        elements.append(website)
        
        elements.append(Spacer(1, 20))
        
        # Patient information table
        patient_data = [
            ["Name:", patient_info.get("name", ""), "Date of Birth:", patient_info.get("date_of_birth", "")],
            ["Parent/Guardian:", patient_info.get("parent_guardian", ""), "Chronological Age:", patient_info.get("chronological_age", {}).get("formatted", "")],
            ["UCI#:", patient_info.get("uci_number", ""), "Service Coordinator:", ""],
            ["Sex:", patient_info.get("sex", ""), "Primary Language:", patient_info.get("language", "")],
            ["Examiner:", "Fushia Crooms, MOT, OTR/L", "Date of Report:", patient_info.get("report_date", "")],
            ["", "", "Date of Encounter:", patient_info.get("encounter_date", "")]
        ]
        
        patient_table = Table(patient_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    async def _create_background_section(self, report_data: Dict[str, Any]) -> List:
        """Create background information section with OpenAI enhancement"""
        elements = []
        
        header = Paragraph("Reason for referral and background information", self.styles['SectionHeader'])
        elements.append(header)
        
        # Use OpenAI to generate professional background narrative
        background_text = await self._generate_background_narrative(report_data)
        
        background_para = Paragraph(background_text, self.styles['ClinicalBody'])
        elements.append(background_para)
        elements.append(Spacer(1, 12))
        
        return elements
    
    async def _create_caregiver_concerns(self, report_data: Dict[str, Any]) -> List:
        """Create caregiver concerns section with OpenAI enhancement"""
        elements = []
        
        header = Paragraph("Caregiver Concerns", self.styles['SectionHeader'])
        elements.append(header)
        
        # Generate professional caregiver concerns narrative
        concerns_text = await self._generate_caregiver_concerns_narrative(report_data)
        
        concerns_para = Paragraph(concerns_text, self.styles['ClinicalBody'])
        elements.append(concerns_para)
        elements.append(Spacer(1, 12))
        
        return elements
    
    async def _create_clinical_observations(self, report_data: Dict[str, Any]) -> List:
        """Create clinical observations section with OpenAI enhancement"""
        elements = []
        
        header = Paragraph("Observation", self.styles['SectionHeader'])
        elements.append(header)
        
        # Generate professional clinical observations
        observations_text = await self._generate_clinical_observations_narrative(report_data)
        
        observations_para = Paragraph(observations_text, self.styles['ClinicalBody'])
        elements.append(observations_para)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_assessment_tools_description(self) -> List:
        """Create assessment tools description section"""
        elements = []
        
        header = Paragraph("Assessment Tools", self.styles['SectionHeader'])
        elements.append(header)
        
        tools_text = ("Bayley Scales of Infant and Toddler Development - Fourth Edition (BSID-4), parent "
                     "report and clinical observation were used as assessment tools for this report.")
        
        tools_para = Paragraph(tools_text, self.styles['ClinicalBody'])
        elements.append(tools_para)
        elements.append(Spacer(1, 8))
        
        # Bayley-4 description
        bayley_header = Paragraph("Bayley Scales of Infant and Toddler Development - Fourth Edition (BSID-4)", 
                                 self.styles['SectionHeader'])
        elements.append(bayley_header)
        
        bayley_description = """The Bayley Scales of Infant and Toddler Development - Fourth Edition (BSID-4) is a norm-referenced assessment used to evaluate early developmental skills in children from birth to 42 months. It provides standardized scores in the following developmental domains:

1. Cognitive Scale: Assesses problem-solving skills, memory, attention, and concept formation.

2. Language Scale:
• Receptive Language: Evaluates the child's understanding of words, gestures, and simple instructions.
• Expressive Language: Measures verbal communication, including babbling, single words, and early sentence formation.

3. Motor Scale:
• Fine Motor: Examines grasping, manipulation of objects, hand-eye coordination, and early writing skills.
• Gross Motor: Evaluates posture, crawling, standing, balance, and walking patterns.

4. Social-Emotional Scale: Measures the child's ability to interact with others, regulate emotions, and respond to social cues.

5. Adaptive Behavior Scale: Assesses daily functional tasks, including self-care skills such as feeding, dressing, and toileting."""
        
        bayley_para = Paragraph(bayley_description, self.styles['ClinicalBody'])
        elements.append(bayley_para)
        elements.append(Spacer(1, 15))
        
        return elements
    
    async def _create_bayley_results(self, report_data: Dict[str, Any]) -> List:
        """Create detailed Bayley-4 results sections with OpenAI enhancement"""
        elements = []
        
        # Extract assessment data
        extracted_data = report_data.get("extracted_data", {})
        
        # Main title
        header = Paragraph("Bayley Scales of Infant and Toddler Development - Fourth Edition (BSID-4)", 
                          self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 8))
        
        # Create detailed sections for each domain
        domains = [
            ("Cognitive (CG)", "cognitive"),
            ("Receptive Communication (RC)", "receptive_communication"),
            ("Expressive Communication (EC)", "expressive_communication"),
            ("Fine Motor (FM)", "fine_motor"),
            ("Gross Motor (GM)", "gross_motor"),
            ("Social-Emotional", "social_emotional"),
            ("Adaptive Behavior", "adaptive_behavior")
        ]
        
        for domain_name, domain_key in domains:
            elements.extend(await self._create_domain_section(domain_name, domain_key, report_data))
        
        return elements
    
    async def _create_domain_section(self, domain_name: str, domain_key: str, report_data: Dict[str, Any]) -> List:
        """Create individual domain section with OpenAI-generated narrative"""
        elements = []
        
        # Domain header
        header = Paragraph(domain_name, self.styles['DomainHeader'])
        elements.append(header)
        
        # Domain description (based on sample report)
        domain_descriptions = {
            "cognitive": "Cognitive tasks assess how your child thinks, reacts, and learns about the world.\n• Infants are given tasks that measure their interest in new things, their attention to familiar and unfamiliar objects, and how they play with different types of toys\n• Toddlers are given tasks that examine how they explore new toys and experiences, how they solve problems, how they learn, and their ability to complete puzzles.",
            "receptive_communication": "Receptive Communication tasks assess how well your child recognizes sounds and how much he/she understands spoken words and directions.\n• Infants are presented with tasks that measure their recognition of sounds, objects, and people in the environment. Many tasks involve social interactions.\n• Toddlers are asked to identify pictures and objects, follow simple directions, and perform social routines, such as wave bye-bye or play peek-a-boo.",
            "expressive_communication": "Expressive Communication tasks assess how well your child communicates using sounds, gestures, or words.\n• Infants are observed throughout the assessment for various forms of nonverbal expression, such as smiling, jabbering expressively, using gestures, and laughing (social interaction).\n• Toddlers are given opportunities to use words by naming objects or pictures, putting words together, and answering questions.",
            "fine_motor": "Fine Motor tasks assess how well your child can use their hands and fingers to make things happen.\n• Muscle control is assessed in infants, such as visual tracking with their eyes, bringing a hand to their mouth, transferring objects from hand to hand, and reaching for and grasping an object.\n• Toddlers are given the opportunity to demonstrate their ability to perform fine motor tasks, such as stacking blocks, drawing simple shapes, and placing small objects (e.g., coins) in a slot.",
            "gross_motor": "Gross Motor tasks assess how well your child can move their body.\n• Infants are assessed for head control and their performance on activities, such as rolling over, sitting upright, and crawling motions.\n• Toddlers are given tasks that measure their ability to make stepping movements, support their own weight, stand, and walk without assistance.",
            "social_emotional": "The Social-Emotional Scale asks caregivers to assess how their child interacts with others, expresses emotions, and responds to sensory input such as sounds, touch, and visual stimuli. This scale helps identify age-appropriate social-emotional milestones related to attachment, self-regulation, and engagement in early relationships.",
            "adaptive_behavior": "The Adaptive Behavior Scale asks caregivers to assess their child's ability to adapt to various demands of normal daily living and become more independent."
        }
        
        if domain_key in domain_descriptions:
            desc_para = Paragraph(domain_descriptions[domain_key], self.styles['ClinicalBody'])
            elements.append(desc_para)
            elements.append(Spacer(1, 8))
        
        # Generate professional narrative for this domain
        domain_narrative = await self._generate_domain_narrative(domain_name, domain_key, report_data)
        
        narrative_para = Paragraph(domain_narrative, self.styles['ClinicalBody'])
        elements.append(narrative_para)
        elements.append(Spacer(1, 12))
        
        return elements
    
    async def _create_recommendations_section(self, report_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        elements = []
        
        header = Paragraph("Recommendations:", self.styles['SectionHeader'])
        elements.append(header)
        
        # Generate recommendations based on assessment data
        recommendations = await self._generate_recommendations(report_data)
        
        for rec in recommendations:
            bullet_para = Paragraph(f"• {rec}", self.styles['BulletPoint'])
            elements.append(bullet_para)
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    async def _create_professional_summary(self, report_data: Dict[str, Any]) -> List:
        """Create comprehensive professional summary"""
        elements = []
        
        header = Paragraph("Summary:", self.styles['SectionHeader'])
        elements.append(header)
        
        # Generate comprehensive summary using OpenAI
        summary_text = await self._generate_professional_summary(report_data)
        
        summary_para = Paragraph(summary_text, self.styles['ClinicalBody'])
        elements.append(summary_para)
        elements.append(Spacer(1, 15))
        
        return elements
    
    async def _create_ot_goals(self, report_data: Dict[str, Any]) -> List:
        """Create specific OT goals section"""
        elements = []
        
        header = Paragraph("OT Goals:", self.styles['SectionHeader'])
        elements.append(header)
        
        # Generate specific, measurable OT goals
        goals = await self._generate_ot_goals(report_data)
        
        for i, goal in enumerate(goals, 1):
            goal_para = Paragraph(f"{i}. {goal}", self.styles['ClinicalBody'])
            elements.append(goal_para)
            elements.append(Spacer(1, 6))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_signature_block(self) -> List:
        """Create signature block"""
        elements = []
        
        disclaimer = Paragraph("The final determination and the need for services will be made by the Regional Center Eligibility Team after review and analysis of this report.", 
                              self.styles['ClinicalBody'])
        elements.append(disclaimer)
        elements.append(Spacer(1, 20))
        
        signature_lines = [
            "Fushia Crooms, MOT, OTR/L",
            "Occupational Therapist",
            "Pediatric Feeding Therapist",
            "Email: fushia@fmrchealth.com",
            "Phone #: 323-229-6025 Ext. 1"
        ]
        
        for line in signature_lines:
            sig_para = Paragraph(line, self.styles['ClinicalBody'])
            elements.append(sig_para)
        
        return elements
    
    # OpenAI narrative generation methods
    async def _generate_with_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using OpenAI with clinical context"""
        self.logger.info(f"🤖 Generating text with OpenAI (max_tokens: {max_tokens})")
        
        if not self.openai_client:
            self.logger.warning("⚠️ OpenAI client not available, using fallback")
            return await self._generate_fallback_text(prompt)
        
        try:
            self.logger.info("📡 Sending request to OpenAI API...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional pediatric occupational therapist writing clinical evaluation reports. Use sophisticated clinical terminology, evidence-based interpretations, and maintain a professional, objective tone. Base your responses on standard pediatric developmental assessments and best practices in occupational therapy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            generated_text = response.choices[0].message.content.strip()
            self.logger.info(f"✅ OpenAI generation successful ({len(generated_text)} characters)")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI generation failed: {e}")
            self.logger.info("🔄 Falling back to template text")
            return await self._generate_fallback_text(prompt)
    
    async def _generate_fallback_text(self, prompt: str) -> str:
        """Generate fallback text when OpenAI is not available"""
        self.logger.info("📝 Using fallback text generation")
        
        # Simple template-based generation based on prompt content
        if "background" in prompt.lower():
            fallback_text = "A developmental evaluation was recommended by the Regional Center to determine the client's current level of performance and to guide service frequency recommendations for early intervention."
        elif "concerns" in prompt.lower():
            fallback_text = "The caregiver expressed concerns regarding the child's overall development, including challenges with attention, engagement, and developmental milestones across multiple domains."
        elif "observation" in prompt.lower():
            fallback_text = "The child participated in an in-clinic evaluation with the caregiver present. The assessment revealed varying levels of engagement and cooperation across different developmental domains."
        else:
            fallback_text = "Based on standardized assessment findings, the child demonstrates a mixed profile of developmental strengths and areas requiring targeted intervention support."
        
        self.logger.info(f"✅ Fallback text generated ({len(fallback_text)} characters)")
        return fallback_text
    
    async def _generate_background_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate professional background narrative"""
        patient_info = report_data.get("patient_info", {})
        patient_name = patient_info.get('name', 'the client')
        age = patient_info.get('chronological_age', {}).get('formatted', 'unknown')
        
        self.logger.info(f"📝 Generating background narrative for {patient_name}")
        
        prompt = f"""Write a professional background section for a pediatric OT evaluation report for {patient_name}, age {age}. The evaluation was recommended by the Regional Center. Keep it concise and professional, similar to standard pediatric OT reports."""
        
        return await self._generate_with_openai(prompt, max_tokens=200)
    
    async def _generate_caregiver_concerns_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate caregiver concerns narrative"""
        patient_info = report_data.get("patient_info", {})
        parent_name = patient_info.get("parent_guardian", "The caregiver")
        child_name = patient_info.get("name", "the child")
        
        self.logger.info(f"👥 Generating caregiver concerns for {child_name}")
        
        prompt = f"""Write a professional caregiver concerns section for a pediatric OT report. {parent_name} expressed concerns about {child_name}'s development. Include typical parental concerns about attention, fine motor skills, speech/language development, and behavioral regulation. Use clinical language appropriate for a professional evaluation report."""
        
        return await self._generate_with_openai(prompt, max_tokens=300)
    
    async def _generate_clinical_observations_narrative(self, report_data: Dict[str, Any]) -> str:
        """Generate clinical observations narrative"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "The child")
        
        self.logger.info(f"👁️ Generating clinical observations for {child_name}")
        
        # Include any extracted clinical notes
        clinical_notes = report_data.get("extracted_data", {}).get("clinical_notes", {})
        observations = clinical_notes.get("converted_narratives", [])
        
        prompt = f"""Write a detailed clinical observation section for {child_name} during a pediatric OT evaluation. Include observations about affect, muscle tone, engagement, attention span, cooperation with testing, and any behavioral observations. Mention how these factors impacted standardized testing. Use professional clinical language typical of pediatric OT evaluations."""
        
        if observations:
            prompt += f" Include these specific observations: {'; '.join(observations[:3])}"
            self.logger.info(f"📋 Including {len(observations)} clinical observations")
        
        return await self._generate_with_openai(prompt, max_tokens=400)
    
    async def _generate_domain_narrative(self, domain_name: str, domain_key: str, report_data: Dict[str, Any]) -> str:
        """Generate detailed domain-specific narrative"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "The child")
        age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
        
        self.logger.info(f"📊 Generating {domain_name} narrative for {child_name}")
        
        # Extract relevant assessment data
        extracted_data = report_data.get("extracted_data", {})
        domain_data = self._extract_domain_data(domain_key, extracted_data)
        
        if domain_data:
            self.logger.info(f"📋 Found assessment data for {domain_name}: {len(str(domain_data))} characters")
        else:
            self.logger.warning(f"⚠️ No assessment data found for {domain_name}")
        
        prompt = f"""Write a detailed {domain_name} section for {child_name} ({age}) in a pediatric OT evaluation report. Include:
        - Scaled score and age equivalent if available
        - Performance description during testing
        - Specific observations and behaviors
        - Clinical interpretation of findings
        - Percentage delay calculation
        - Professional clinical terminology
        
        Assessment data: {json.dumps(domain_data, indent=2)}
        
        Follow the format of professional pediatric OT reports with detailed clinical observations and interpretations."""
        
        return await self._generate_with_openai(prompt, max_tokens=600)
    
    def _extract_domain_data(self, domain_key: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant data for specific domain"""
        domain_data = {}
        
        # Look for Bayley-4 data
        bayley_cognitive = extracted_data.get("bayley4_cognitive", {})
        bayley_social = extracted_data.get("bayley4_social", {})
        
        # Map domain keys to assessment data
        if domain_key == "cognitive":
            domain_data = {
                "scaled_scores": bayley_cognitive.get("scaled_scores", {}),
                "composite_scores": bayley_cognitive.get("composite_scores", {}),
                "age_equivalents": bayley_cognitive.get("age_equivalents", {}),
                "interpretations": bayley_cognitive.get("interpretations", {})
            }
        elif domain_key in ["receptive_communication", "expressive_communication"]:
            domain_data = {
                "scaled_scores": bayley_cognitive.get("scaled_scores", {}),
                "age_equivalents": bayley_cognitive.get("age_equivalents", {})
            }
        elif domain_key in ["fine_motor", "gross_motor"]:
            domain_data = {
                "scaled_scores": bayley_cognitive.get("scaled_scores", {}),
                "age_equivalents": bayley_cognitive.get("age_equivalents", {})
            }
        elif domain_key == "social_emotional":
            domain_data = {
                "scaled_scores": bayley_social.get("scaled_scores", {}),
                "composite_scores": bayley_social.get("composite_scores", {}),
                "interpretations": bayley_social.get("interpretations", {})
            }
        
        return domain_data
    
    async def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate evidence-based recommendations"""
        prompt = """Generate 4-6 professional therapy recommendations for a pediatric client based on comprehensive assessment findings. Include:
        - Physical Therapy
        - Speech Therapy  
        - Occupational Therapy with frequency
        - Early intervention services
        Use bullet point format, be specific and professional."""
        
        recommendations_text = await self._generate_with_openai(prompt, max_tokens=300)
        
        # Parse into list or use default
        if "•" in recommendations_text:
            recommendations = [rec.strip() for rec in recommendations_text.split("•") if rec.strip()]
        else:
            recommendations = [
                "Physical Therapy",
                "Speech Therapy",
                "Infant Stim",
                "Occupational Therapy 2x/week"
            ]
        
        return recommendations
    
    async def _generate_professional_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate comprehensive professional summary"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "The child")
        age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
        
        prompt = f"""Write a comprehensive professional summary for {child_name} ({age}) based on Bayley-4 assessment findings. Include:
        - Overall developmental profile with specific delay percentages
        - Areas of relative strength and significant delay
        - Impact on functional performance
        - Need for multidisciplinary intervention
        - Prognosis and benefit from services
        
        Use professional clinical language typical of pediatric OT evaluation summaries."""
        
        return await self._generate_with_openai(prompt, max_tokens=500)
    
    async def _generate_ot_goals(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate specific, measurable OT goals"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "the child")
        
        prompt = f"""Generate 4 specific, measurable occupational therapy goals for {child_name} following SMART goal format. Include:
        - Timeline (within 6 months)
        - Specific activity/skill
        - Measurable criteria (4 out of 5 opportunities)
        - Assistance level
        - Focus areas: fine motor, visual-motor, bilateral coordination, pre-writing
        
        Format each goal as a complete sentence with specific metrics."""
        
        goals_text = await self._generate_with_openai(prompt, max_tokens=400)
        
        # Parse goals or use defaults
        if "Within" in goals_text:
            goals = [goal.strip() for goal in goals_text.split('\n') if goal.strip() and ('Within' in goal or goal[0].isdigit())]
        else:
            goals = [
                "Within six months, the child will stack 5 one-inch blocks independently in 4 out of 5 opportunities with no more than 2 prompts, to improve visual-motor coordination and hand stability.",
                "Within six months, the child will string 2–3 large beads onto a string in 4 out of 5 opportunities with no more than moderate assistance, demonstrating bilateral hand use and midline crossing.",
                "Within six months, the child will use a pincer grasp (thumb and index finger) to pick up and release small objects in 4 out of 5 opportunities with no more than 2 prompts.",
                "Within six months, the child will spontaneously scribble on paper using a crayon or marker in 4 out of 5 opportunities with no more than moderate prompts, to promote pre-writing and fine motor development."
            ]
        
        return goals[:4]  # Limit to 4 goals 