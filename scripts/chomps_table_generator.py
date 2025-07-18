from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def create_chomps_concern_table(domain_data: list, include_total: bool = True) -> Table:
    """
    Create a ReportLab table showing ChOMPS domain scores with concern levels.
    
    Args:
        domain_data (list): List of dictionaries with format:
                           [{"domain_name": "", "score": int, "status": ""}]
        include_total (bool): Whether to include a total row
        
    Returns:
        Table: ReportLab Table object
    """
    
    # Calculate total score if needed
    total_score = sum(item["score"] for item in domain_data) if include_total else 0
    
    # Determine total status based on the highest concern level
    if include_total:
        concern_levels = [item["status"] for item in domain_data]
        if "High Concern" in concern_levels:
            total_status = "High Concern"
        elif "Concern" in concern_levels:
            total_status = "Concern"
        else:
            total_status = "No Concern"
    
    # Create table data
    table_data = []
    
    # Header row
    table_data.append([
        "Domain",
        "Score", 
        "No\nConcern",
        "Concern", 
        "High Concern"
    ])
    
    # Data rows
    for item in domain_data:
        domain_name = item["domain_name"].replace("MOVEMENT", "Movement").replace("PATTERNS", "Patterns").replace("ORAL-MOTOR", "Oral-Motor").replace("COORDINATION", "Coordination").replace("FUNDAMENTAL", "Fundamental").replace("SKILLS", "Skills")
        score = item["score"]
        status = item["status"]
        
        # Create checkmarks for appropriate columns
        no_concern_check = "✓" if status == "No Concern" else ""
        concern_check = "✓" if status == "Concern" else ""
        high_concern_check = "✓" if status == "High Concern" else ""
        
        table_data.append([
            domain_name,
            str(score),
            no_concern_check,
            concern_check,
            high_concern_check
        ])
    
    # Add total row if requested
    if include_total:
        total_no_concern = "✓" if total_status == "No Concern" else ""
        total_concern = "✓" if total_status == "Concern" else ""
        total_high_concern = "✓" if total_status == "High Concern" else ""
        
        table_data.append([
            "Total",
            str(total_score),
            total_no_concern,
            total_concern,
            total_high_concern
        ])
    
    # Create the table
    table = Table(table_data, colWidths=[2.5*inch, 0.7*inch, 0.8*inch, 0.8*inch, 1.0*inch])
    
    # Apply table styling
    table_style = TableStyle([
        # Header row formatting
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align domain names
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        
        # Grid lines
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        
        # Row heights and padding
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightblue]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        
        # Special formatting for checkmarks
        ('FONTNAME', (2, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 1), (-1, -1), 12),
        ('TEXTCOLOR', (2, 1), (-1, -1), colors.green),
    ])
    
    # Add special formatting for total row if included
    if include_total:
        total_row_index = len(table_data) - 1
        table_style.add('BACKGROUND', (0, total_row_index), (-1, total_row_index), colors.lightgrey)
        table_style.add('FONTNAME', (0, total_row_index), (-1, total_row_index), 'Helvetica-Bold')
        table_style.add('LINEABOVE', (0, total_row_index), (-1, total_row_index), 1, colors.black)
    
    table.setStyle(table_style)
    
    return table


def create_chomps_report_with_table(domain_data: list, output_filename: str = "chomps_report.pdf"):
    """
    Create a complete PDF report with the ChOMPS concern table.
    
    Args:
        domain_data (list): List of dictionaries with ChOMPS domain data
        output_filename (str): Name of the output PDF file
        
    Returns:
        str: Path to the generated PDF file
    """
    
    # Create document
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        topMargin=1*inch,
        bottomMargin=1*inch,
        leftMargin=1*inch,
        rightMargin=1*inch
    )
    
    # Build story
    story = []
    
    # Title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    title = Paragraph("ChOMPS Assessment Results", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Create and add the table
    table = create_chomps_concern_table(domain_data, include_total=True)
    story.append(table)
    
    # Add some explanatory text
    story.append(Spacer(1, 20))
    explanation_style = ParagraphStyle(
        'Explanation',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10
    )
    
    explanation_text = """
    <b>Level of Concern Interpretation:</b><br/>
    • <b>No Concern:</b> Score is within normal range (>10th percentile)<br/>
    • <b>Concern:</b> Score indicates some concern (5th-10th percentile)<br/>
    • <b>High Concern:</b> Score indicates significant concern (<5th percentile)
    """
    
    explanation = Paragraph(explanation_text, explanation_style)
    story.append(explanation)
    
    # Build the PDF
    doc.build(story)
    
    return output_filename


# Example usage and testing
if __name__ == "__main__":
    # Example data from the terminal
    sample_data = [
        {
            "domain_name": "COMPLEX MOVEMENT PATTERNS",
            "score": 24,
            "status": "Concern"
        },
        {
            "domain_name": "BASIC MOVEMENT PATTERNS",
            "score": 36,
            "status": "High Concern"
        },
        {
            "domain_name": "ORAL-MOTOR COORDINATION",
            "score": 24,
            "status": "High Concern"
        },
        {
            "domain_name": "FUNDAMENTAL ORAL-MOTOR SKILLS",
            "score": 6,
            "status": "High Concern"
        }
    ]
    
    # Test creating just the table
    print("Creating ChOMPS concern table...")
    table = create_chomps_concern_table(sample_data)
    print("✅ Table created successfully")
    
    # Test creating full PDF report
    print("Creating full PDF report...")
    pdf_path = create_chomps_report_with_table(sample_data, "chomps_assessment_report.pdf")
    print(f"✅ PDF report created: {pdf_path}")
    
    # Also test with the other data format from terminal
    terminal_data = [
        {
            "domain_name": "COMPLEX MOVEMENT PATTERNS",
            "score": 10,
            "status": "High Concern"
        },
        {
            "domain_name": "BASIC MOVEMENT PATTERNS",
            "score": 32,
            "status": "High Concern"
        },
        {
            "domain_name": "ORAL-MOTOR COORDINATION",
            "score": 8,
            "status": "High Concern"
        },
        {
            "domain_name": "FUNDAMENTAL ORAL-MOTOR SKILLS",
            "score": 6,
            "status": "High Concern"
        }
    ]
    
    print("Creating report with terminal data...")
    pdf_path2 = create_chomps_report_with_table(terminal_data, "chomps_terminal_data_report.pdf")
    print(f"✅ Second PDF report created: {pdf_path2}") 