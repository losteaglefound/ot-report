import glob
import json
import re

def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        text += f"SELECTION_ELEMENT: {word['SelectionStatus']}" + ' '
    return text.strip()

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map[child_id]
                if cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows

def is_question_row(text):
    return re.match(r'^\d+\.', text.strip())

def is_section_header(row):
    # A section header is in column 1, is uppercase, and not a question.
    return 1 in row and isinstance(row[1], str) and row[1].isupper() and not is_question_row(row[1])

def parse_pedieat_assessment(file_path):
    with open(file_path, 'r') as file:
        response = json.load(file)

    blocks = response['Blocks']
    blocks_map = {block['Id']: block for block in blocks}
    
    table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
    
    if not table_blocks:
        print("No tables found in the document.")
        return

    for table_index, table_result in enumerate(table_blocks):
        print(f"--- Processing Table {table_index + 1}/{len(table_blocks)} ---")
        rows = get_rows_columns_map(table_result, blocks_map)
        
        # Correctly identify score columns from the first row that contains single-digit numbers
        score_columns = {}
        header_row_index = -1
        for i, row in sorted(rows.items()):
            if any(cell.strip().isdigit() and len(cell.strip()) == 1 for cell in row.values()):
                score_columns = {col_index: cell.strip() for col_index, cell in row.items() if cell.strip().isdigit()}
                header_row_index = i
                break

        if not score_columns:
            print("Could not find the score values row for this table.")
            continue

        # Group rows into sections based on headers
        sections = {}
        current_section_title = "General"
        sections[current_section_title] = []

        # Remove header row from rows to process
        if header_row_index != -1:
            del rows[header_row_index]

        for _, row in sorted(rows.items()):
            if 1 not in row:
                # Append rows without column 1 to the current section as they might be continuations
                if sections[current_section_title]: # only if there is a section to append to
                     sections[current_section_title].append(row)
                continue

            if is_section_header(row):
                current_section_title = row[1]
                if current_section_title not in sections:
                    sections[current_section_title] = []
            else:
                # Add any row that is not a section header to the current section
                sections[current_section_title].append(row)

        # Process each section
        for title, section_rows in sections.items():
            if not section_rows:
                continue
            print(f"--- {title} ---")
            
            i = 0
            while i < len(section_rows):
                row = section_rows[i]
                
                if 1 not in row or not is_question_row(row.get(1, '')):
                    i += 1
                    continue

                question_text = row.get(1, '').strip()
                
                # Combine multi-line questions
                j = i + 1
                while j < len(section_rows):
                    next_row = section_rows[j]
                    if 1 in next_row and is_question_row(next_row.get(1,'')):
                        break
                    
                    if 1 in next_row:
                        question_text += " " + next_row.get(1, '').strip()
                    j += 1
                
                # Clean up question text from instructional phrases
                question_text = re.sub(r'If you would like to explain.*$', '', question_text).strip()
                question_text = re.sub(r'\s{2,}', ' ', question_text) # Replace multiple spaces with a single space

                selected_score = "Not Found"
                for k in range(i, j):
                    current_question_row = section_rows[k]
                    for col_index, cell in current_question_row.items():
                        if "SELECTION_ELEMENT: SELECTED" in cell:
                            if col_index in score_columns:
                                selected_score = score_columns[col_index]
                                break
                    if selected_score != "Not Found":
                        break
                
                print(f"Question: {question_text}")
                print(f"Score: {selected_score}")
                print("-" * 20)
                i = j

if __name__ == "__main__":
    files = glob.glob("outputs/aws_pedieat_page_merged.json")
    files = sorted(files)
    for f in files:
        parse_pedieat_assessment(f) 