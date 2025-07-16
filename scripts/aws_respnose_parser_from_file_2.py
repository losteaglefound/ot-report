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


def parse_chomps_json(file_path):
    """
    Parses a Textract JSON file for a ChOMPS assessment and extracts the data.

    Args:
        file_path (str): The path to the input JSON file.

    Returns:
        dict: A dictionary containing the structured patient data and scores.
    """
    import json
    import re

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": "File not found."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format."}

    block_map = {block['Id']: block for block in data['Blocks']}
    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']

    # --- 1. Extract Patient Info ---
    patient_details = {}
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

    # --- 2. Parse All Tables ---
    score_mapping = {'YES': 2, 'SOMETIMES': 1, 'NOT YET': 0}
    table_data = []

    table_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'TABLE']
    if not table_blocks:
        return {"error": "No table found in the document."}

    def get_text_from_block(block, block_map):
        """Recursively fetches and concatenates text from WORD blocks."""
        text = ""
        if 'Relationships' in block:
            for rel in block['Relationships']:
                if rel['Type'] == 'CHILD':
                    for child_id in rel['Ids']:
                        child_block = block_map.get(child_id)
                        if child_block and child_block['BlockType'] == 'WORD':
                            text += child_block.get('Text', '') + ' '
                        elif child_block and child_block['BlockType'] == 'CELL':
                            text += get_text_from_block(child_block, block_map) + ' '
        return text.strip()

    for table_block in table_blocks:
        # Step 1: Get all cell blocks in this table
        cell_ids = []
        for rel in table_block.get('Relationships', []):
            if rel['Type'] == 'CHILD':
                cell_ids.extend(rel['Ids'])
        cells = [block_map[cid] for cid in cell_ids if cid in block_map]

        # Step 2: Group cells by row index
        rows = {}
        for cell in cells:
            row_index = cell['RowIndex']
            if row_index not in rows:
                rows[row_index] = []
            rows[row_index].append(cell)
        for row_index in rows:
            rows[row_index].sort(key=lambda x: x['ColumnIndex'])

        # Step 3: Find the header row (must contain YES/SOMETIMES/NOT YET)
        header_row = None
        for row_idx in sorted(rows.keys()):
            row_texts = [get_text_from_block(cell, block_map).upper() for cell in rows[row_idx]]
            if any(resp in row_texts for resp in score_mapping.keys()):
                header_row = rows[row_idx]
                break

        if not header_row:
            continue  # skip table

        # Map: column index -> header text
        header_col_indices = {
            cell['ColumnIndex']: get_text_from_block(cell, block_map).upper()
            for cell in header_row
        }

        # Step 4: Parse data rows after header
        for row_idx in sorted(rows.keys()):
            if row_idx <= header_row[0]['RowIndex']:
                continue

            row_cells = rows[row_idx]
            if not row_cells:
                continue

            observation_text = get_text_from_block(row_cells[0], block_map)

            response = "N/A"
            score = -1

            for cell in row_cells:
                if 'Relationships' not in cell:
                    continue
                for rel in cell['Relationships']:
                    if rel['Type'] != 'CHILD':
                        continue
                    for child_id in rel['Ids']:
                        child_block = block_map.get(child_id)
                        if (child_block and
                            child_block['BlockType'] == 'SELECTION_ELEMENT' and
                            child_block['SelectionStatus'] == 'SELECTED'):

                            col_index = cell['ColumnIndex']
                            response_text = header_col_indices.get(col_index, '')
                            response = response_text
                            score = score_mapping.get(response, -1)
                            break
                    if response != "N/A":
                        break
                if response != "N/A":
                    break

            if response != "N/A":
                table_data.append({
                    "observation": observation_text,
                    "response": response.title(),
                    "score": score
                })

    # --- 3. Final Output ---
    return {
        "patientInfo": patient_details,
        "observations": table_data
    }


if __name__ == "__main__":
    # The name of the JSON file from Textract
    json_file_path = 'outputs/aws_chomps_page_1.json'
    
    # Parse the file
    extracted_data = parse_chomps_json(json_file_path)
    
    # Print the structured data as a formatted JSON string
    print(json.dumps(extracted_data, indent=2))