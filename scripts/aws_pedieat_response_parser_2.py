import glob
import json
import re
import os

CATEGORIES = [
    "PHYSIOLOGIC SYMPTOMS",
    "PROBLEMATIC MEALTIME BEHAVIORS",
    "SELECTIVE / RESTRICTIVE EATING",
    "ORAL PROCESSING"
]

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

def find_category_for_question(question_block, all_blocks):
    # Search for the category title on the page of the question
    for block in all_blocks:
        if block.get('Page') == question_block.get('Page') and block['BlockType'] == 'LINE':
            for category in CATEGORIES:
                if category in block['Text']:
                    return category
    return "General"


def parse_pedieat_assessment(file_path, output_filename):
    with open(file_path, 'r') as file:
        response = json.load(file)

    blocks = response['Blocks']
    blocks_map = {block['Id']: block for block in blocks}
    
    parsed_data = {category: [] for category in CATEGORIES}
    parsed_data["General"] = []

    score_columns = {}

    for table_result in [b for b in blocks if b['BlockType'] == 'TABLE']:
        rows = get_rows_columns_map(table_result, blocks_map)
        
        header_row_index = -1
        # Find score columns in the current table
        for i, row in sorted(rows.items()):
            digit_cells = {col_index: cell.strip() for col_index, cell in row.items() if cell.strip().isdigit() and len(cell.strip()) == 1}
            if len(digit_cells) > 2:
                score_columns = digit_cells
                header_row_index = i
                break
        
        if header_row_index != -1:
            del rows[header_row_index]

        if not score_columns:
            print(f"Warning: No valid score columns found for a table. Questions in this table might not have scores.")
            continue
        
        i = 0
        section_rows = sorted(rows.values(), key=lambda r: min(r.keys()) if r else 0)

        while i < len(section_rows):
            row = section_rows[i]
            
            if 1 not in row or not is_question_row(row.get(1, '')):
                i += 1
                continue

            question_text = row.get(1, '').strip()
            
            # Find the block for the first line of the question to determine its page.
            question_start_block = None
            for block in blocks:
                if block['BlockType'] == 'LINE' and question_text.startswith(block['Text'].strip()):
                     question_start_block = block
                     break
            
            j = i + 1
            while j < len(section_rows):
                next_row = section_rows[j]
                if 1 in next_row and is_question_row(next_row.get(1,'')):
                    break
                
                if 1 in next_row:
                    question_text += " " + next_row.get(1, '').strip()
                j += 1
            
            question_text = re.sub(r'If you would like to explain.*$', '', question_text).strip()
            question_text = re.sub(r'\s{2,}', ' ', question_text)

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
            
            category = find_category_for_question(question_start_block, blocks) if question_start_block else "General"

            observation = {
                "question": question_text,
                "score": selected_score
            }
            
            parsed_data[category].append(observation)
            i = j

    with open(output_filename, 'w') as f:
        json.dump(parsed_data, f, indent=4)
    print(f"Successfully created JSON output at {output_filename}")


if __name__ == "__main__":
    merged_file = "outputs/aws_pedieat_page_merged.json"
    output_json_file = "outputs/parsed_pedieat_assessment.json"
    
    if os.path.exists(merged_file):
        parse_pedieat_assessment(merged_file, output_json_file)
    else:
        print(f"Merged file not found: {merged_file}")
        print("Please run the merge script first.") 