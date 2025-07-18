from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


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
