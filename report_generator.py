import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Configure logging for this module (after imports)
logger = logging.getLogger(__name__)

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

class OTReportGenerator:
    """Basic OT Report Generator using templates"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("📄 Initializing Basic OT Report Generator...")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.logger.info("✅ ReportLab styles configured")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.logger.info("🎨 Setting up custom styles...")
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='BasicReportHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='BasicSectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='BasicBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        self.logger.info("✅ Custom styles configured")
    
    async def generate_report(self, report_data: Dict[str, Any], session_id: str) -> str:
        """Generate basic OT report PDF"""
        patient_name = report_data.get("patient_info", {}).get("name", "Unknown")
        self.logger.info(f"📝 Starting basic report generation for {patient_name} (session: {session_id})")
        
        output_path = os.path.join("outputs", f"ot_report_{session_id}.pdf")
        self.logger.info(f"📁 Output path: {output_path}")
        
        try:
            # Create PDF document
            self.logger.info("📄 Creating PDF document...")
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                topMargin=1*inch,
                bottomMargin=1*inch,
                leftMargin=1*inch,
                rightMargin=1*inch
            )
            
            # Build content
            story = []
            
            # Header
            self.logger.info("📋 Adding header...")
            story.extend(self._create_header(report_data))
            
            # Patient information
            self.logger.info("👤 Adding patient information...")
            story.extend(self._create_patient_section(report_data))
            
            # Assessment results
            self.logger.info("📊 Adding assessment results...")
            story.extend(self._create_assessment_section(report_data))
            
            # Recommendations
            self.logger.info("💡 Adding recommendations...")
            story.extend(self._create_recommendations_section(report_data))
            
            # Build PDF
            self.logger.info("🔨 Building PDF document...")
            doc.build(story)
            
            # Verify file creation
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
                self.logger.info(f"✅ Basic report generated successfully: {file_size:.2f} MB")
            else:
                raise Exception("PDF file was not created")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate basic report: {e}")
            raise

    def _create_header(self, patient_info: Dict[str, Any]) -> list:
        """Create report header"""
        elements = []
        
        # Title
        title = Paragraph("OCCUPATIONAL THERAPY EVALUATION REPORT", self.styles['BasicReportHeader'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Patient information table
        patient_data = [
            ["Client Name:", patient_info.get("name", "")],
            ["Age:", patient_info.get("age", "")],
            ["Date of Assessment:", patient_info.get("assessment_date", "")],
            ["Date of Report:", patient_info.get("report_date", "")]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_patient_section(self, report_data: Dict[str, Any]) -> list:
        """Create patient information section"""
        elements = []
        
        # Section header
        header = Paragraph("BACKGROUND INFORMATION", self.styles['BasicSectionHeader'])
        elements.append(header)
        
        # Background text
        background_text = f"""
        This occupational therapy evaluation was conducted to assess {report_data['patient_info'].get('name', 'the client')}'s 
        developmental skills and functional abilities. The assessment was based on standardized testing using the Bayley Scales 
        of Infant and Toddler Development, Fourth Edition (Bayley-4), which includes cognitive, language, motor, 
        social-emotional, and adaptive behavior scales.
        
        The Bayley-4 is a comprehensive developmental assessment tool designed to evaluate the developmental functioning 
        of infants and toddlers from 16 days to 42 months of age. The assessment provides valuable information about 
        the child's current developmental status and helps identify areas of strength and need for intervention planning.
        """
        
        background_para = Paragraph(background_text, self.styles['BasicBodyText'])
        elements.append(background_para)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_assessment_section(self, report_data: Dict[str, Any]) -> list:
        """Create assessment results section"""
        elements = []
        
        # Section header
        header = Paragraph("ASSESSMENT RESULTS", self.styles['BasicSectionHeader'])
        elements.append(header)
        
        # Cognitive and Motor Results
        if "cognitive_motor_data" in report_data:
            elements.extend(self._create_cognitive_motor_results(report_data["cognitive_motor_data"]))
        
        # Social-Emotional and Adaptive Behavior Results
        if "social_emotional_data" in report_data:
            elements.extend(self._create_social_emotional_results(report_data["social_emotional_data"]))
        
        return elements
    
    def _create_cognitive_motor_results(self, cognitive_data: Dict[str, Any]) -> list:
        """Create cognitive and motor assessment results"""
        elements = []
        
        # Cognitive Results Subheader
        subheader = Paragraph("Cognitive and Motor Development", self.styles['BasicSectionHeader'])
        elements.append(subheader)
        
        # Create results table
        results_data = [["Domain", "Raw Score", "Scaled Score", "Percentile", "Age Equivalent"]]
        
        # Add cognitive scores
        domains = ["Cognitive", "Visual Reception", "Fine Motor", "Receptive Communication", "Expressive Communication", "Gross Motor"]
        
        for domain in domains:
            raw_score = cognitive_data.get("raw_scores", {}).get(domain, "N/A")
            scaled_score = cognitive_data.get("scaled_scores", {}).get(domain, "N/A")
            percentile = cognitive_data.get("percentiles", {}).get(domain, "N/A")
            age_equiv = cognitive_data.get("age_equivalents", {}).get(domain, "N/A")
            
            results_data.append([domain, raw_score, scaled_score, percentile, age_equiv])
        
        results_table = Table(results_data, colWidths=[2.2*inch, 1*inch, 1*inch, 1*inch, 1.3*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(results_table)
        elements.append(Spacer(1, 15))
        
        # Composite Scores
        if cognitive_data.get("composite_scores"):
            composite_header = Paragraph("Composite Scores", self.styles['Heading3'])
            elements.append(composite_header)
            
            composite_data = [["Composite", "Standard Score", "Percentile", "Classification"]]
            
            for composite, score in cognitive_data["composite_scores"].items():
                classification = self._get_score_classification(int(score) if score.isdigit() else 0)
                percentile = self._standard_to_percentile(int(score) if score.isdigit() else 0)
                composite_data.append([composite, score, str(percentile), classification])
            
            composite_table = Table(composite_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            composite_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(composite_table)
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_social_emotional_results(self, social_data: Dict[str, Any]) -> list:
        """Create social-emotional and adaptive behavior results"""
        elements = []
        
        # Social-Emotional Results Subheader
        subheader = Paragraph("Social-Emotional and Adaptive Behavior", self.styles['BasicSectionHeader'])
        elements.append(subheader)
        
        # Adaptive Behavior domains
        adaptive_domains = [
            "Communication", "Community Use", "Functional Pre-Academics", 
            "Home Living", "Health and Safety", "Leisure", "Self-Care", 
            "Self-Direction", "Social", "Motor"
        ]
        
        if social_data.get("raw_scores"):
            adaptive_data = [["Domain", "Raw Score", "Scaled Score", "Percentile"]]
            
            for domain in adaptive_domains:
                raw_score = social_data.get("raw_scores", {}).get(domain, "N/A")
                scaled_score = social_data.get("scaled_scores", {}).get(domain, "N/A")
                percentile = social_data.get("percentiles", {}).get(domain, "N/A")
                
                adaptive_data.append([domain, raw_score, scaled_score, percentile])
            
            adaptive_table = Table(adaptive_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
            adaptive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(adaptive_table)
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_recommendations_section(self, report_data: Dict[str, Any]) -> list:
        """Create recommendations section"""
        elements = []
        
        # Section header
        header = Paragraph("RECOMMENDATIONS", self.styles['BasicSectionHeader'])
        elements.append(header)
        
        # Combine recommendations from both reports
        all_recommendations = []
        if "cognitive_motor_data" in report_data:
            all_recommendations.extend(report_data["cognitive_motor_data"].get("recommendations", []))
        if "social_emotional_data" in report_data:
            all_recommendations.extend(report_data["social_emotional_data"].get("recommendations", []))
        
        if not all_recommendations:
            all_recommendations = [
                "Individual occupational therapy services to address fine motor and sensory processing needs",
                "Physical therapy consultation for gross motor development and postural control",
                "Speech-language therapy for communication and language development",
                "Structured play activities to promote social-emotional development",
                "Parent training and education for home-based intervention strategies",
                "Environmental modifications to support development and safety",
                "Regular reassessment to monitor progress and adjust intervention plans"
            ]
        
        for i, recommendation in enumerate(all_recommendations, 1):
            rec_para = Paragraph(f"{i}. {recommendation}", self.styles['BasicBodyText'])
            elements.append(rec_para)
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _get_score_classification(self, standard_score: int) -> str:
        """Get classification based on standard score"""
        if standard_score >= 130:
            return "Very Superior"
        elif standard_score >= 120:
            return "Superior"
        elif standard_score >= 110:
            return "High Average"
        elif standard_score >= 90:
            return "Average"
        elif standard_score >= 80:
            return "Low Average"
        elif standard_score >= 70:
            return "Below Average"
        else:
            return "Well Below Average"
    
    def _standard_to_percentile(self, standard_score: int) -> int:
        """Convert standard score to approximate percentile"""
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