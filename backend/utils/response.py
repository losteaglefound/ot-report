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
    header_style = ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        leading=18,
        spaceAfter=6,
        spaceBefore=12,
        underlineWidth=1,
    )

    for key, value in data.items():
        content_type = value.get("type")
        content = value.get("content", "")

        if content_type == "header":
            elements.append(Paragraph(content, header_style))
            elements.append(Spacer(1, 0.1 * inch))

        elif content_type == "paragraph":
            elements.append(Paragraph(content, styles['BodyText']))
            elements.append(Spacer(1, 0.15 * inch))

        elif content_type == "bullet_points":
            if content:
                bullet_items = [ListItem(Paragraph(point, styles['BodyText'])) for point in content]
                elements.append(ListFlowable(bullet_items, bulletType='bullet'))
                elements.append(Spacer(1, 0.15 * inch))

    return elements