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
                    elif child_block and (child_block['BlockType'] == 'CELL' or child_block['BlockType'] == 'LINE'):
                         text += get_text_from_block(child_block, block_map) + ' '
    return text.strip()

def get_table_data(table_block, block_map):
    """Extracts data from a table block."""
    table_data = []
    rows = {}
    for relationship in table_block.get('Relationships', []):
        if relationship['Type'] == 'CHILD':
            for cell_id in relationship['Ids']:
                cell_block = block_map.get(cell_id)
                if cell_block and cell_block['BlockType'] == 'CELL':
                    row_index = cell_block['RowIndex']
                    col_index = cell_block['ColumnIndex']
                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][col_index] = get_text_from_block(cell_block, block_map)

    # Sort rows and columns to maintain order
    for row_index in sorted(rows.keys()):
        row_data = []
        for col_index in sorted(rows[row_index].keys()):
            row_data.append(rows[row_index][col_index])
        table_data.append(row_data)

    return table_data

def parse_chomps_json(response: dict):
    """
    Parses a Textract JSON file for a ChOMPS assessment and extracts the data.

    Args:
        response (dict): The AWS Textract response as a dictionary.

    Returns:
        dict: A dictionary containing the structured patient data and scores.
    """
    data = response
    block_map = {block['Id']: block for block in data['Blocks']}
    
    # Categories to look for in the document
    categories = [
        "COMPLEX MOVEMENT PATTERNS",
        "BASIC MOVEMENT PATTERNS",
        "ORAL MOTOR PATTERN",
        "FUNDAMENTAL ORAL-MOTOR SKILLS"
    ]
    
    extracted_data = {}
    current_category = None

    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']
    table_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'TABLE']
    
    # First, let's find the category and associate tables to it
    category_and_tables = {}
    
    # Identify which tables fall under which category based on their position
    # This is a simple approach, a more robust one would analyze y-coordinates
    # of the category title and the table
    
    # We will find all line blocks that are categories
    category_blocks = [block for block in line_blocks if block.get('Text', '').strip().upper() in categories]
    
    for category_block in category_blocks:
        category_text = category_block.get('Text', '').strip().upper()
        category_and_tables[category_text] = []
        
        # Find tables that appear after this category header
        # Based on geometry. A more robust way is needed if the document is complex.
        category_y_position = category_block['Geometry']['BoundingBox']['Top']

        for table_block in table_blocks:
            table_y_position = table_block['Geometry']['BoundingBox']['Top']
            if table_y_position > category_y_position:
                 # Check if the table is already assigned to a category
                 is_assigned = any(table_block['Id'] in [tb['Id'] for tb in table_list] for table_list in category_and_tables.values())
                 if not is_assigned:
                    category_and_tables[category_text].append(table_block)

    # Now parse the tables for each category
    for category, tables in category_and_tables.items():
        extracted_data[category] = []
        for table_block in tables:
            table_data = get_table_data(table_block, block_map)
            # Process the raw table data to a more structured format if needed
            # For now, we will just add the raw table data
            extracted_data[category].append(table_data)

    return extracted_data

if __name__ == '__main__':
    # Load the JSON data from the file
    with open(r'C:\Users\91930\Downloads\outputs\outputs\aws_final_full_response.json', 'r') as f:
        aws_response = json.load(f)

    # Parse the JSON data
    parsed_data = parse_chomps_json(aws_response)

    # Print the extracted data
    print(json.dumps(parsed_data, indent=4))