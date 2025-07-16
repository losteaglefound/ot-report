import json
import re
from collections import defaultdict

def get_text_from_block(block, block_map):
    """Recursively fetches and concatenates text from WORD blocks."""
    text = ""
    if 'Relationships' in block and block['Relationships']:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = block_map.get(child_id)
                    if child_block and child_block['BlockType'] == 'WORD':
                        text += child_block.get('Text', '') + ' '
                    elif child_block and (child_block['BlockType'] == 'CELL' or child_block['BlockType'] == 'LINE'):
                        text += get_text_from_block(child_block, block_map) + ' '
    return text.strip()

def parse_table_data(table_block, block_map):
    """Extracts and processes data from a single table block."""
    score_mapping = {'YES': 2, 'SOMETIMES': 1, 'NOT YET': 0}
    parsed_rows = []
    
    cells = []
    if 'Relationships' in table_block:
        for rel in table_block['Relationships']:
            if rel['Type'] == 'CHILD':
                for child_id in rel['Ids']:
                    cell = block_map.get(child_id)
                    if cell:
                        cells.append(cell)

    rows = defaultdict(list)
    for cell in cells:
        rows[cell['RowIndex']].append(cell)

    for row_index in rows:
        rows[row_index].sort(key=lambda x: x['ColumnIndex'])
        
    header_row = rows.get(2, [])

    for row_index in sorted(rows.keys()):
        if row_index <= 2:
            continue

        row_cells = rows[row_index]
        observation_text = get_text_from_block(row_cells[0], block_map) if row_cells else "N/A"
        
        response = "N/A"
        score = -1

        for cell in row_cells:
            is_selected = False
            if 'Relationships' in cell:
                for rel in cell['Relationships']:
                    if rel['Type'] == 'CHILD':
                        for child_id in rel['Ids']:
                            child_block = block_map.get(child_id)
                            if (child_block and 
                                child_block['BlockType'] == 'SELECTION_ELEMENT' and 
                                child_block['SelectionStatus'] == 'SELECTED'):
                                is_selected = True
                                break
                    if is_selected:
                        break
            
            if is_selected:
                col_index = cell['ColumnIndex']
                header_cell = next((h for h in header_row if h['ColumnIndex'] == col_index), None)
                if header_cell:
                    response_text = get_text_from_block(header_cell, block_map).upper()
                    response = response_text
                    score = score_mapping.get(response, -1)
                break 

        if response != "N/A":
            parsed_rows.append({
                "observation": observation_text,
                "response": response.title(),
                "score": score
            })
            
    return parsed_rows

def parse_chomps_json_from_file(file_path):
    """
    Parses a merged, multi-page Textract JSON file for a ChOMPS assessment, 
    correctly categorizing data across pages.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": "File not found."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

    block_map = {block['Id']: block for block in data['Blocks']}
    
    # --- 1. Extract Patient Details (optional, but good to keep) ---
    patient_details = {}
    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']
    
    for line in line_blocks:
        text = line.get('Text', '')
        if "Child's Name/ID:" in text:
            patient_details['name'] = re.search(r"Child's Name/ID:\s*(.*)", text).group(1).strip()
        elif "Child's Date of Birth:" in text:
            patient_details['dob'] = re.search(r"Child's Date of Birth:\s*(.*)", text).group(1).strip()
        elif "Today's Date:" in text:
            patient_details['assessmentDate'] = re.search(r"Today's Date:\s*(.*)", text).group(1).strip()

    # --- 2. Find Categories and Tables, now Page-Aware ---
    categories_to_find = [
        "COMPLEX MOVEMENT PATTERNS", 
        "BASIC MOVEMENT PATTERNS", 
        "ORAL MOTOR PATTERN", 
        "FUNDAMENTAL ORAL-MOTOR SKILLS"
    ]
    
    table_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'TABLE']
    category_blocks = [
        b for b in line_blocks 
        if b.get('Text', '').strip().upper() in categories_to_find
    ]
    
    # Sort categories by their appearance in the document (Page, then Top)
    category_blocks.sort(key=lambda b: (b['Page'], b['Geometry']['BoundingBox']['Top']))
    
    categorized_observations = defaultdict(list)
    
    for table in table_blocks:
        table_page = table.get('Page', 1)
        table_y_pos = table['Geometry']['BoundingBox']['Top']
        
        # Find the last category header that appeared before this table
        last_category_before_table = None
        for cat in category_blocks:
            cat_page = cat.get('Page', 1)
            cat_y_pos = cat['Geometry']['BoundingBox']['Top']
            
            if cat_page < table_page or (cat_page == table_page and cat_y_pos < table_y_pos):
                last_category_before_table = cat
            else:
                # Since the categories are sorted, we can stop once we pass the table's position
                break
        
        if last_category_before_table:
            category_name = last_category_before_table.get('Text', '').strip()
            table_data = parse_table_data(table, block_map)
            if table_data:
                categorized_observations[category_name].extend(table_data)

    # --- 3. Assemble Final Output ---
    final_output = {
        "patientInfo": patient_details,
        "observationsByCategory": categorized_observations
    }

    return final_output

if __name__ == "__main__":
    # Use the MERGED JSON file here
    json_file_path = 'outputs/aws_chomps_page_merged.json' 
    
    extracted_data = parse_chomps_json_from_file(json_file_path)
    
    print(json.dumps(extracted_data, indent=4))