from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch

def add_logo(canvas, doc):
    logo_path = "/home/lap-49/Documents/ot-report/assets/images/header-small.png"
    logo_width = 1.5 * inch
    logo_height = 0.75 * inch

    # Place logo at top-left corner inside the margin
    # x = doc.rightMargin
    # y = doc.height + doc.topMargin - logo_height  # Align top

    # Place logo at top-right corner inside the margin
    x = doc.pagesize[0] - doc.rightMargin - logo_width  # Right-aligned
    y = doc.height + doc.topMargin - logo_height        # Top-aligned

    canvas.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True)

# Document setup
doc = SimpleDocTemplate("with_logo.pdf", pagesize=LETTER,
                        topMargin=1.5*inch,  # Make room for logo
                        leftMargin=0.75*inch, rightMargin=0.75*inch, bottomMargin=0.75*inch)

Story = [
    Spacer(1, 0.5*inch),
    Paragraph("This is content below the logo.", style=None),
]

doc.build(Story, onFirstPage=add_logo, onLaterPages=add_logo)
