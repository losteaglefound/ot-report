import os
import json
import re


from sconfig import config as script_config
from config import config as server_sconfig


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
                    # If a cell contains lines, recurse
                    elif child_block and child_block['BlockType'] == 'CELL':
                         text += get_text_from_block(child_block, block_map) + ' '
    return text.strip()

def parse_chomps_json(response: dict):
    """
    Parses a Textract JSON file for a ChOMPS assessment and extracts the data.

    Args:
        file_path (str): The path to the input JSON file.

    Returns:
        dict: A dictionary containing the structured patient data and scores.
    """
    data = response
    # Create a map of block IDs to blocks for easy lookup
    block_map = {block['Id']: block for block in data['Blocks']}
    
    # --- 1. Extract Patient Details ---
    patient_details = {}
    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']
    
    for line in line_blocks:
        text = line.get('Text', '')
        if "Child's Name/ID:" in text:
            # Use regex to find the name after the label
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

    # --- 2. Extract Table Data ---
    table_data = []
    score_mapping = {'YES': 2, 'SOMETIMES': 1, 'NOT YET': 0}
    
    # Find the first table block
    table_block = next((b for b in data['Blocks'] if b['BlockType'] == 'TABLE'), None)

    if not table_block:
        return {"error": "No table found in the document."}

    # Get all cell blocks related to this table
    cell_ids = []
    for rel in table_block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            cell_ids.extend(rel['Ids'])

    cells = [block_map[cid] for cid in cell_ids if cid in block_map]

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
        
    # Get header text (second row in this specific table structure)
    header_row = rows.get(2, [])
    header_texts = [get_text_from_block(cell, block_map).upper() for cell in header_row]

    # Process each data row (starting from row 3)
    for row_index in sorted(rows.keys()):
        if row_index <= 2:  # Skip header rows
            continue

        row_cells = rows[row_index]
        observation_text = get_text_from_block(row_cells[0], block_map) if row_cells else "N/A"
        
        response = "N/A"
        score = -1

        # Find the selected element in the row
        for i, cell in enumerate(row_cells):
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
                # Find corresponding header text by column index
                col_index = cell['ColumnIndex']
                # Find the header cell with the matching column index
                header_cell = next((h for h in header_row if h['ColumnIndex'] == col_index), None)
                if header_cell:
                    response_text = get_text_from_block(header_cell, block_map).upper()
                    response = response_text
                    score = score_mapping.get(response, -1)
                break # Move to the next row once a selection is found

        if response != "N/A":
            table_data.append({
                "observation": observation_text,
                "response": response.title(),
                "score": score
            })

    # --- 3. Assemble Final Output ---
    final_output = {
        "patientInfo": patient_details,
        "observations": table_data
    }

    return final_output


if __name__ == "__main__":
    # The name of the JSON file from Textract
    json_file_path = 'outputs/aws_chomps_page_2.json'
    
    # Parse the file
    extracted_data = parse_chomps_json(json_file_path)
    
    # Print the structured data as a formatted JSON string
    print(json.dumps(extracted_data, indent=2))