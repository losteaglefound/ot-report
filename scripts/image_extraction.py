import pdfplumber

from pdf_pages_to_images import convert_to_image_pdf

input_file = convert_to_image_pdf()
input_file = "assets/inputs/Sensory-Profile-2-Summary-Report_70247631_1751134355067.pdf"

with pdfplumber.open(input_file) as pdf:
    score_profile_found = False
    extracted_tables = []

    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(i)
        if "SCORE PROFILE" in text.upper():
            score_profile_found = True
            continue  # Go to next page where tables begin
        
        if score_profile_found:
            tables = page.extract_tables()
            for table in tables:
                # Basic filter to exclude small or invalid tables
                if len(table) > 2 and len(table[0]) > 1:
                    extracted_tables.append(table)
                if len(extracted_tables) == 2:
                    break
        if len(extracted_tables) == 2:
            break

# Print or process extracted tables
for idx, table in enumerate(extracted_tables):
    print(f"\nTable {idx+1}:")
    for row in table:
        print(row)
