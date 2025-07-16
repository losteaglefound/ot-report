import json
import re
from collections import defaultdict

CATEGORY_NAMES = [
    "COMPLEX MOVEMENT PATTERNS",
    "BASIC MOVEMENT PATTERNS",
    "ORAL-MOTOR COORDINATION",
    "FUNDAMENTAL ORAL-MOTOR SKILLS"
]

SCORE_MAPPING = {
    'YES': 2,
    'SOMETIMES': 1,
    'NOT YET': 0
}

def get_text_from_block(block, block_map):
    text = ""
    if 'Relationships' in block:
        for rel in block['Relationships']:
            if rel['Type'] == 'CHILD':
                for child_id in rel['Ids']:
                    child = block_map.get(child_id)
                    if child and child['BlockType'] in ['WORD', 'LINE']:
                        text += child.get('Text', '') + ' '
                    elif child and child['BlockType'] == 'CELL':
                        text += get_text_from_block(child, block_map) + ' '
    return text.strip()

def detect_header_row(rows, block_map):
    for idx in sorted(rows.keys()):
        row_texts = [get_text_from_block(cell, block_map).upper() for cell in rows[idx]]
        if any(val in row_texts for val in SCORE_MAPPING.keys()):
            return rows[idx]
    return []

def parse_table(table_block, block_map):
    if 'Relationships' not in table_block:
        return []

    cell_ids = []
    for rel in table_block['Relationships']:
        if rel['Type'] == 'CHILD':
            cell_ids.extend(rel['Ids'])

    cells = [block_map[cid] for cid in cell_ids if cid in block_map and block_map[cid]['BlockType'] == 'CELL']

    rows = defaultdict(list)
    for cell in cells:
        rows[cell['RowIndex']].append(cell)
    for row in rows.values():
        row.sort(key=lambda x: x['ColumnIndex'])

    header_row = detect_header_row(rows, block_map)
    if not header_row:
        return []

    header_map = {
        cell['ColumnIndex']: get_text_from_block(cell, block_map).upper()
        for cell in header_row
    }

    data = []
    header_row_idx = header_row[0]['RowIndex']
    for row_idx in sorted(rows.keys()):
        if row_idx <= header_row_idx:
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
                    child = block_map.get(child_id)
                    if child and child['BlockType'] == 'SELECTION_ELEMENT' and child['SelectionStatus'] == 'SELECTED':
                        col = cell['ColumnIndex']
                        header_text = header_map.get(col, '').upper()
                        response = header_text
                        score = SCORE_MAPPING.get(response, -1)
                        break
                if response != "N/A":
                    break
            if response != "N/A":
                break

        if response != "N/A":
            data.append({
                "observation": observation_text,
                "response": response.title(),
                "score": score
            })

    return data

def parse_chomps_json_response(state):
    aws_merged_response = state['aws_merged_response']
    data = aws_merged_response

    block_map = {b['Id']: b for b in data['Blocks']}
    table_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'TABLE']
    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']

    # --- Extract Patient Info ---
    patient_info = {}
    for line in line_blocks:
        txt = line.get('Text', '')
        if "Child's Name/ID:" in txt:
            patient_info['name'] = txt.split(":", 1)[-1].strip()
        elif "Child's Date of Birth:" in txt:
            patient_info['dob'] = txt.split(":", 1)[-1].strip()
        elif "Today's Date:" in txt:
            patient_info['assessmentDate'] = txt.split(":", 1)[-1].strip()

    # --- Detect Category Headings ---
    category_blocks = []
    for b in line_blocks:
        text_upper = b.get('Text', '').strip().upper()
        for cat in CATEGORY_NAMES:
            if cat in text_upper:
                category_blocks.append((b.get('Page', 1), b['Geometry']['BoundingBox']['Top'], cat))
                break

    category_blocks.sort()  # Sort by (Page, Y-position)

    categorized = defaultdict(list)

    for table in table_blocks:
        table_page = table.get('Page', 1)
        table_top = table['Geometry']['BoundingBox']['Top']
        table_data = parse_table(table, block_map)
        if not table_data:
            continue

        # Match category by nearest previous header
        category = None
        for cat_page, cat_top, cat_name in reversed(category_blocks):
            if cat_page < table_page or (cat_page == table_page and cat_top < table_top):
                category = cat_name
                break

        if category:
            categorized[category].extend(table_data)
        else:
            print(f"⚠️ Table on Page {table_page} at Y={table_top:.3f} could not be categorized.")

    observation_data = {
        "patientInfo": patient_info,
        "observationsByCategory": dict(categorized)
    }

    with open("outputs/aws_chomps_observation_data.json", "w+") as f:
        f.write(json.dumps(observation_data, indent=2))

    state['observation_data'] = observation_data
    return state
