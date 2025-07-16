import json
import re

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
                    # If a cell contains lines or other cells, recurse
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

    # Group cells by row index
    rows = {}
    for cell in cells:
        row_index = cell['RowIndex']
        if row_index not in rows:
            rows[row_index] = []
        rows[row_index].append(cell)

    # Sort cells within each row by column index
    for row_index in rows:
        rows[row_index].sort(key=lambda x: x['ColumnIndex'])
        
    # Assuming the header is the second row in the CHOMPS table structure
    header_row = rows.get(2, [])

    # Process each data row (starting from row 3)
    for row_index in sorted(rows.keys()):
        if row_index <= 2:  # Skip header rows
            continue

        row_cells = rows[row_index]
        observation_text = get_text_from_block(row_cells[0], block_map) if row_cells else "N/A"
        
        response = "N/A"
        score = -1

        # Find the selected element in the row
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
                # Find the header cell with the matching column index to get the response text
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
    Parses a Textract JSON file for a ChOMPS assessment, categorizes the data,
    and extracts all tables.

    Args:
        file_path (str): The path to the input JSON file.

    Returns:
        dict: A dictionary containing the structured patient data and categorized observations.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": "File not found."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

    block_map = {block['Id']: block for block in data['Blocks']}
    
    # --- 1. Extract Patient Details ---
    patient_details = {}
    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']
    
    for line in line_blocks:
        text = line.get('Text', '')
        if "Child's Name/ID:" in text:
            match = re.search(r"Child's Name/ID:\s*(.*)", text)
            if match:
                patient_details['name'] = match.group(1).strip()
        elif "Child's Date of Birth:" in text:
            match = re.search(r"Child's Date of Birth:\s*(.*)", text)
            if match:
                patient_details['dob'] = match.group(1).strip()
        elif "Today's Date:" in text:
            match = re.search(r"Today's Date:\s*(.*)", text)
            if match:
                patient_details['assessmentDate'] = match.group(1).strip()

    # --- 2. Find Categories and Associate Tables ---
    categories_to_find = [
        "COMPLEX MOVEMENT PATTERNS", 
        "BASIC MOVEMENT PATTERNS", 
        "ORAL-MOTOR COORDINATION", 
        "FUNDAMENTAL ORAL-MOTOR SKILLS"
    ]
    
    table_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'TABLE']
    category_blocks = [b for b in line_blocks if b.get('Text', '').strip().upper() in categories_to_find]
    
    categorized_observations = {}
    
    for cat_block in category_blocks:
        category_name = cat_block.get('Text', '').strip()
        cat_y_position = cat_block['Geometry']['BoundingBox']['Top']
        
        # Find tables that are positioned after this category header
        associated_table_data = []
        for table_block in table_blocks:
            table_y_position = table_block['Geometry']['BoundingBox']['Top']
            # Simple check: if table is below the category header
            if table_y_position > cat_y_position:
                # More robust: check if it's not already claimed by a closer category
                is_claimed = False
                for other_cat_block in category_blocks:
                    if other_cat_block['Id'] != cat_block['Id']:
                        other_cat_y = other_cat_block['Geometry']['BoundingBox']['Top']
                        # If another category is between this category and the table
                        if cat_y_position < other_cat_y < table_y_position:
                            is_claimed = True
                            break
                if not is_claimed:
                    table_data = parse_table_data(table_block, block_map)
                    associated_table_data.extend(table_data)

        if associated_table_data:
            categorized_observations[category_name] = associated_table_data


    # --- 3. Assemble Final Output ---
    final_output = {
        "patientInfo": patient_details,
        "observationsByCategory": categorized_observations
    }

    return final_output


if __name__ == "__main__":
    # Use the JSON file you have from Textract.
    # I am using the one from our previous conversation for this example.
    json_file_path = 'outputs/aws_chomps_page_merged.json'
    
    # Parse the file
    extracted_data = parse_chomps_json_from_file(json_file_path)
    
    # Print the structured data as a formatted JSON string
    print(json.dumps(extracted_data, indent=4))