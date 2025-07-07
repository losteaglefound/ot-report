from reportlab.platypus import Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm ,inch


async def format_data_for_pdf(data: dict) -> list:
    """
    Converts structured JSON data into a list of ReportLab flowables.
    
    Args:
        data (dict): Parsed JSON with keys and content types ('header', 'paragraph', 'bullet_points').

    Returns:
        list: A list of flowables (Paragraphs, Spacers, ListFlowable) ready for PDF generation.
    """
    styles = getSampleStyleSheet()
    elements = []

    # Custom header style
    # header_style = ParagraphStyle(
    #     name='SectionHeader',
    #     parent=styles['Heading2'],
    #     fontSize=12,
    #     fontName="TimesNewRoman-Bold",
    #     leading=18,
    #     spaceAfter=6,
    #     spaceBefore=12,
    #     underlineWidth=1,
    # )
    header_style = ParagraphStyle(
        name="SectionHeader",
        fontSize=11,
        leading=14,
        fontName="TimesNewRoman-Bold",
        underlineWidth=1
    )
    body_style = ParagraphStyle(
        name='BodyText',
        parent=styles['Normal'],
        fontSize=11,
        fontName="TimesNewRoman",
        leading=14,
        spaceAfter=6,
        spaceBefore=12,
        underlineWidth=1,
    )

    for key, value in data.items():
        content_type = value.get("type")
        content = value.get("content", "")

        if content_type == "header":
            elements.append(Paragraph(f"<u>{content}</u>", header_style))
            elements.append(Spacer(1, 0.2 * inch))

        elif content_type == "paragraph":
            elements.append(Paragraph(content, body_style))
            elements.append(Spacer(1, 0.15 * inch))

        elif content_type == "bullet_points":
            if content:
                bullet_items = [
                    ListItem(
                        Paragraph(
                            point, ParagraphStyle(
                                name="bullet_point",
                                fontName="TimesNewRoman",
                                fontSize=11,
                                leading=13,
                                
                            )
                        )
                    ) for point in content
                ]
                elements.append(ListFlowable(bullet_items, bulletType='bullet'))
                elements.append(Spacer(1, 0.15 * inch))

    return elements


async def format_bayley_data_for_pdf(data: dict) -> list:
    """
    Converts Bayley-4 structured JSON data into a list of ReportLab flowables.
    Handles the nested structure with header, domain_summary, domain_details, and patient_assessment.
    
    Args:
        data (dict): Parsed Bayley-4 JSON with nested structure for each domain.

    Returns:
        list: A list of flowables (Paragraphs, Spacers, ListFlowable) ready for PDF generation.
    """
    styles = getSampleStyleSheet()
    elements = []

    # Custom styles for Bayley-4 formatting
    domain_header_style = ParagraphStyle(
        name="BayleyDomainHeader",
        fontSize=12 ,
        leading=14,
        fontName="TimesNewRoman-Bold",
        underlineWidth=1,
        spaceAfter=8,
        spaceBefore=16,
    )
    
    domain_summary_style = ParagraphStyle(
        name="BayleyDomainSummary",
        fontSize=11,
        leading=14,
        fontName="TimesNewRoman-Bold",
        spaceAfter=6,
        spaceBefore=6,
    )
    
    bullet_style = ParagraphStyle(
        name="BayleyBulletStyle",
        fontSize=11,
        leading=14,
        fontName="TimesNewRoman",
        leftIndent=20,
        spaceAfter=3,
    )
    
    patient_assessment_style = ParagraphStyle(
        name="BayleyPatientAssessment",
        fontSize=11,
        leading=14,
        fontName="TimesNewRoman",
        spaceAfter=12,
        spaceBefore=0,
        firstLineIndent=0,
    )

    # Style for adaptive behavior sub-domain headers
    adaptive_subdomain_style = ParagraphStyle(
        name="BayleyAdaptiveSubdomain",
        fontSize=11,
        leading=14,
        fontName="TimesNewRoman",
        spaceAfter=0,
        spaceBefore=8,
        firstLineIndent=0,
    )

    # Process each domain
    for domain_key, domain_data in data.items():
        if not isinstance(domain_data, dict):
            continue
            
        # Add domain header
        if "header" in domain_data:
            header_content = domain_data["header"].get("content", "")
            if header_content:
                elements.append(Paragraph(f"<u>{header_content}</u>", domain_header_style))
        
        # Add domain summary
        if "domain_summary" in domain_data:
            summary_content = domain_data["domain_summary"].get("content", "")
            if summary_content:
                elements.append(Paragraph(summary_content, domain_summary_style))
        
        # Add domain details (bullet points)
        if "domain_details" in domain_data:
            details_content = domain_data["domain_details"].get("content", [])
            if details_content and isinstance(details_content, list):
                for bullet_point in details_content:
                    if bullet_point.strip():  # Only add non-empty bullet points
                        elements.append(Paragraph(f"• {bullet_point}", bullet_style))
                elements.append(Spacer(1, 0.1 * inch))
        
        # Add patient assessment - special handling for adaptive behavior
        if "patient_assessment" in domain_data:
            assessment_content = domain_data["patient_assessment"].get("content", "")
            if assessment_content:
                if domain_key == "adaptive_behavior":
                    # Handle adaptive behavior with separate sub-domain keys
                    # Add the main assessment content
                    assessment_content = assessment_content.replace('\\n', '\n')
                    elements.append(Paragraph(assessment_content, patient_assessment_style))
                    
                    # Process individual sub-domains
                    subdomain_keys = [
                        ("receptive_communication", "Receptive Communication:"),
                        ("expressive_communication", "Expressive Communication:"),
                        ("personal_self_care", "Personal (Self-Care):"),
                        ("interpersonal_relationships", "Interpersonal Relationships:"),
                        ("play_and_leisure", "Play and Leisure:")
                    ]
                    
                    for subdomain_key, header_text in subdomain_keys:
                        if subdomain_key in domain_data:
                            subdomain_content = domain_data[subdomain_key].get("content", "")
                            if subdomain_content:
                                # Add the sub-domain header
                                elements.append(Paragraph(header_text, adaptive_subdomain_style))
                                # elements.append(Paragraph(header, patient_assessment_style))
                                # Add the content
                                content = subdomain_content.replace('\\n', '\n')
                                elements.append(Paragraph(content, patient_assessment_style))
                else:
                    # Regular patient assessment for other domains
                    assessment_content = assessment_content.replace('\\n', '\n')
                    elements.append(Paragraph(assessment_content, patient_assessment_style))
        
        # Add space between domains
        elements.append(Spacer(1, 0.2 * inch))

    return elements


async def format_bayley_data_for_html(data: dict) -> str:
    """
    Converts Bayley-4 structured JSON data into HTML format.
    Handles the nested structure with header, domain_summary, domain_details, and patient_assessment.
    
    Args:
        data (dict): Parsed Bayley-4 JSON with nested structure for each domain.

    Returns:
        str: HTML formatted string ready for web display.
    """
    html_parts = []
    
    for domain_key, domain_data in data.items():
        if not isinstance(domain_data, dict):
            continue
            
        # Add domain header
        if "header" in domain_data:
            header_content = domain_data["header"].get("content", "")
            if header_content:
                html_parts.append(f'<h3 style="text-decoration: underline; margin-top: 20px; margin-bottom: 10px;">{header_content}</h3>')
        
        # Add domain summary
        if "domain_summary" in domain_data:
            summary_content = domain_data["domain_summary"].get("content", "")
            if summary_content:
                html_parts.append(f'<p style="margin-bottom: 8px;">{summary_content}</p>')
        
        # Add domain details (bullet points)
        if "domain_details" in domain_data:
            details_content = domain_data["domain_details"].get("content", [])
            if details_content and isinstance(details_content, list):
                html_parts.append('<ul style="margin-left: 20px; margin-bottom: 10px;">')
                for bullet_point in details_content:
                    if bullet_point.strip():  # Only add non-empty bullet points
                        html_parts.append(f'<li style="margin-bottom: 5px;">{bullet_point}</li>')
                html_parts.append('</ul>')
        
        # Add patient assessment
        if "patient_assessment" in domain_data:
            assessment_content = domain_data["patient_assessment"].get("content", "")
            if assessment_content:
                if domain_key == "adaptive_behavior":
                    # Handle adaptive behavior with separate sub-domain keys
                    # Add the main assessment content
                    assessment_html = assessment_content.replace('\\n', '<br>')
                    html_parts.append(f'<p style="margin-bottom: 15px; line-height: 1.6;">{assessment_html}</p>')
                    
                    # Process individual sub-domains
                    subdomain_keys = [
                        ("receptive_communication", "Receptive Communication:"),
                        ("expressive_communication", "Expressive Communication:"),
                        ("personal_self_care", "Personal (Self-Care):"),
                        ("interpersonal_relationships", "Interpersonal Relationships:"),
                        ("play_and_leisure", "Play and Leisure:")
                    ]
                    
                    for subdomain_key, header_text in subdomain_keys:
                        if subdomain_key in domain_data:
                            subdomain_content = domain_data[subdomain_key].get("content", "")
                            if subdomain_content:
                                # Add the sub-domain header
                                html_parts.append(f'<h4 style="font-weight: bold; margin-top: 15px; margin-bottom: 8px;">{header_text}</h4>')
                                # Add the content
                                content_html = subdomain_content.replace('\\n', '<br>')
                                html_parts.append(f'<p style="margin-bottom: 15px; line-height: 1.6;">{content_html}</p>')
                else:
                    # Regular patient assessment for other domains
                    # Replace \n with <br> for proper HTML line breaks
                    assessment_html = assessment_content.replace('\\n', '<br>')
                    html_parts.append(f'<p style="margin-bottom: 15px; line-height: 1.6;">{assessment_html}</p>')
        
        # Add space between domains
        html_parts.append('<div style="margin-bottom: 20px;"></div>')
    
    return '\n'.join(html_parts)