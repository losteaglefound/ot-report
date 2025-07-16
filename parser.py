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

def parse_pedieat_assessment(file_path):
    with open(file_path, 'r') as file:
        response = json.load(file)

    blocks = response['Blocks']
    blocks_map = {block['Id']: block for block in blocks}
    
    table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
    
    if not table_blocks:
        print("No tables found in the document.")
        return

    table_result = table_blocks[0]
    rows = get_rows_columns_map(table_result, blocks_map)
    
    # Correctly identify score columns from the first row that contains single-digit numbers
    score_columns = {}
    for i, row in sorted(rows.items()):
        if any(cell.strip().isdigit() and len(cell.strip()) == 1 for cell in row.values()):
            score_columns = {col_index: cell.strip() for col_index, cell in row.items() if cell.strip().isdigit()}
            break

    if not score_columns:
        print("Could not find the score values row.")
        return

    # Group rows into sections based on headers like 'PHYSIOLOGIC SYMPTOMS'
    sections = {}
    current_section_title = "General"
    
    for i, row in sorted(rows.items()):
        if 1 in row and row[1].isupper() and not is_question_row(row[1]):
            current_section_title = row[1]
            sections[current_section_title] = []
        elif is_question_row(row[1]):
            if current_section_title not in sections:
                sections[current_section_title] = []
            sections[current_section_title].append(row)

    # Process each section
    for title, section_rows in sections.items():
        print(f"--- {title} ---")
        
        i = 0
        while i < len(section_rows):
            row = section_rows[i]
            question_text = row[1]
            
            # Combine multi-line questions
            j = i + 1
            while j < len(section_rows) and not is_question_row(section_rows[j][1]):
                question_text += " " + section_rows[j][1]
                j += 1
            
            selected_score = "Not Found"
            for col_index, cell in row.items():
                if "SELECTION_ELEMENT: SELECTED" in cell:
                    if col_index in score_columns:
                        selected_score = score_columns[col_index]
                        break
            
            print(f"Question: {question_text}")
            print(f"Score: {selected_score}")
            print("-" * 20)
            i = j

if __name__ == "__main__":
    parse_pedieat_assessment('outputs/aws_pedieat_page_0.json') 