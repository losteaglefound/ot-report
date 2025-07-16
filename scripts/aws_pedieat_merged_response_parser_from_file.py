import json

def parse_pedieat_textract_json(file_path):
    import json
    import re
    from collections import defaultdict

    # Scoring direction
    REVERSE_SCORED = set(range(46, 51))  # Positive Mealtime Behaviors

    # Subscale mapping by item number
    SUBSCALE_RANGES = {
        "Physiologic Symptoms": range(1, 28),
        "Problematic Mealtime Behaviors": range(28, 36),
        "Positive Mealtime Behaviors": range(46, 51),
        "Selective/Restrictive Eating": range(51, 66),
        "Oral Processing": range(66, 79),
    }

    # Map selection index (left to right) to score
    def get_score_from_position(pos, item_num):
        if item_num in REVERSE_SCORED:
            return 5 - pos  # reverse scoring
        return pos  # normal scoring

    with open(file_path, 'r') as f:
        data = json.load(f)

    block_map = {b['Id']: b for b in data['Blocks']}
    table_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'TABLE']
    line_blocks = [b for b in data['Blocks'] if b['BlockType'] == 'LINE']

    # --- Extract Patient Info (optional) ---
    patient_info = {}
    for line in line_blocks:
        txt = line.get('Text', '')
        if "Child's Name:" in txt:
            patient_info['name'] = txt.split(":", 1)[-1].strip()
        elif "Date of Birth:" in txt:
            patient_info['dob'] = txt.split(":", 1)[-1].strip()

    def get_text(block):
        text = ''
        if 'Relationships' in block:
            for rel in block['Relationships']:
                if rel['Type'] == 'CHILD':
                    for cid in rel['Ids']:
                        child = block_map.get(cid)
                        if child and child['BlockType'] == 'WORD':
                            text += child.get('Text', '') + ' '
        return text.strip()

    def extract_table_data(table):
        items = []

        if 'Relationships' not in table:
            return items

        # Step 1: Gather all cells in table
        cells = []
        for rel in table['Relationships']:
            if rel['Type'] == 'CHILD':
                for cid in rel['Ids']:
                    block = block_map.get(cid)
                    if block and block['BlockType'] == 'CELL':
                        cells.append(block)

        # Step 2: Group cells by row
        from collections import defaultdict
        rows = defaultdict(list)
        for cell in cells:
            rows[cell['RowIndex']].append(cell)
        for r in rows.values():
            r.sort(key=lambda x: x['ColumnIndex'])

        # Step 3: Process rows
        for row_idx in sorted(rows):
            row = rows[row_idx]
            if not row:
                continue

            question_text = get_text(row[0])
            match = re.match(r"(\d+)\.\s*(.+)", question_text)
            if not match:
                continue

            q_num = int(match.group(1))
            label = match.group(2)

            # Find selected checkbox
            selected_index = None
            for i, cell in enumerate(row[1:], start=0):  # start=0: leftmost checkbox = score 0
                for rel in cell.get('Relationships', []):
                    if rel['Type'] == 'CHILD':
                        for cid in rel['Ids']:
                            child = block_map.get(cid)
                            if (child and child['BlockType'] == 'SELECTION_ELEMENT' and
                                    child['SelectionStatus'] == 'SELECTED'):
                                selected_index = i
                                break
                if selected_index is not None:
                    break

            if selected_index is None:
                continue

            score = get_score_from_position(selected_index, q_num)

            # Assign to subscale
            subscale = None
            for name, rng in SUBSCALE_RANGES.items():
                if q_num in rng:
                    subscale = name
                    break

            if not subscale:
                subscale = "Other"

            items.append({
                "questionNumber": q_num,
                "observation": label,
                "responseScore": score,
                "subscale": subscale
            })

        return items

    # Collect data
    subscale_map = defaultdict(list)
    for table in table_blocks:
        items = extract_table_data(table)
        for item in items:
            subscale_map[item['subscale']].append(item)

    return {
        "patientInfo": patient_info,
        "subscales": dict(subscale_map)
    }


if __name__ == "__main__":
    result = parse_pedieat_textract_json("outputs/aws_chomps_page_merged.json")
    print(json.dumps(result, indent=2))
