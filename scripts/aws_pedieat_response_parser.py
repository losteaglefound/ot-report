import json
import os
import re
import csv
import argparse
from collections import defaultdict

# --- Configuration for PediEAT Scoring ---
# This dictionary defines the scoring rules for each page.
# For each page, specify which question numbers have reversed scoring.
# Page 1 (index 0) has no reversed scoring questions in your example.
# Other pages might, so you would add them here (e.g., 1: {'reversed_questions': [46, 47, 48, 49, 50]})
SCORING_CONFIG = {
    0: {'reversed_questions': []},
    1: {'reversed_questions': [36, 46, 47, 48, 49, 50]},
    2: {'reversed_questions': list(range(51, 63))},
    3: {'reversed_questions': [75, 76, 77, 78]}
}


def get_question_text_and_geometry(blocks):
    """
    Parses blocks to aggregate multi-line questions and get their geometry.
    Returns a list of dictionaries, each containing the full question text and geometry.
    """
    lines = sorted([b for b in blocks if b['BlockType'] == 'LINE'], key=lambda x: x['Geometry']['BoundingBox']['Top'])
    
    questions = []
    current_question_lines = []
    current_question_geom = None
    question_num_regex = re.compile(r"^\s*\d{1,2}\.")

    for line in lines:
        text = line.get('Text', '')
        is_new_question = question_num_regex.match(text)
        
        if is_new_question:
            # If we have a pending question, save it
            if current_question_lines:
                questions.append({
                    'text': ' '.join(current_question_lines),
                    'geometry': current_question_geom
                })
            
            # Start a new question
            current_question_lines = [text]
            current_question_geom = line['Geometry']['BoundingBox']
        elif current_question_lines and line['Geometry']['BoundingBox']['Left'] > 0.08:
            # This is likely a continuation of a multi-line question
            current_question_lines.append(text)
    
    # Add the last pending question
    if current_question_lines:
        questions.append({
            'text': ' '.join(current_question_lines),
            'geometry': current_question_geom
        })
        
    return questions


def determine_score(selection_box, config, page_number):
    """Determines the score based on the horizontal position of the checkbox."""
    
    # X-coordinate ranges for score columns [0-5]
    # Format: (score, min_x, max_x)
    # These ranges are estimated from the form's layout.
    score_columns = [
        (0, 0.53, 0.58), (1, 0.59, 0.63), (2, 0.64, 0.70),
        (3, 0.71, 0.75), (4, 0.77, 0.82), (5, 0.83, 0.88)
    ]
    
    # Some pages have reversed scoring columns.
    if page_number == 2: # Page 3 of PDF (Selective/Restrictive) has a different layout for some questions
         score_columns = [
            (5, 0.53, 0.58), (4, 0.59, 0.63), (3, 0.64, 0.70),
            (2, 0.71, 0.75), (1, 0.77, 0.82), (0, 0.83, 0.88)
        ]

    sel_x_center = selection_box['Left'] + selection_box['Width'] / 2
    
    final_score = -1 # Default/error value
    
    for score, min_x, max_x in score_columns:
        if min_x <= sel_x_center <= max_x:
            final_score = score
            break
            
    # Apply reversed scoring logic for specific questions
    question_num = int(config['question_text'].split('.')[0])
    page_config = SCORING_CONFIG.get(page_number, {})
    reversed_questions = page_config.get('reversed_questions', [])
    
    if question_num in reversed_questions:
        return 5 - final_score
        
    return final_score


def parse_pedieat_page(json_path):
    """
    Parses a single Textract JSON file for a PediEAT page.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading {json_path}: {e}")
        return []

    blocks = data['Blocks']
    page_number_match = re.search(r'_page_(\d+)\.json$', json_path)
    page_number = int(page_number_match.group(1)) if page_number_match else 0
    
    # 1. Get all questions and their geometry
    questions = get_question_text_and_geometry(blocks)
    
    # 2. Get all selected checkboxes
    selected_elements = [
        b['Geometry']['BoundingBox'] for b in blocks 
        if b['BlockType'] == 'SELECTION_ELEMENT' and b.get('SelectionStatus') == 'SELECTED'
    ]
    
    results = []
    # 3. Match selected checkboxes to questions
    for sel_box in selected_elements:
        sel_y_center = sel_box['Top'] + sel_box['Height'] / 2
        
        # Find the question on the same vertical level
        for q in questions:
            q_geom = q['geometry']
            q_y_center = q_geom['Top'] + q_geom['Height'] / 2
            
            # Check if the selection is vertically aligned with the question
            if abs(sel_y_center - q_y_center) < (q_geom['Height'] / 2) + 0.01: # 0.01 is a tolerance
                
                # We found a match, now determine the score
                result_config = {'question_text': q['text']}
                score = determine_score(sel_box, result_config, page_number)

                if score != -1:
                    results.append({
                        "question_number": int(result_config['question_text'].split('.')[0]),
                        "observation": ' '.join(result_config['question_text'].split(' ')[1:]).strip(),
                        "score": score
                    })
                break # Move to the next selected element
                
    return results


def main():
    """Main function to process a directory of JSON files."""
    # parser = argparse.ArgumentParser(description="Parse PediEAT assessment forms from AWS Textract JSON output.")
    # parser.add_argument("input_dir", type=str, help="Directory containing the Textract JSON files.")
    # parser.add_argument("output_csv", type=str, help="Path to the output CSV file.")
    
    # args = parser.parse_args()
    
    all_results = []
    
    # Group files by patient/assessment name
    # files_by_patient = defaultdict(list)
    # for filename in os.listdir(args.input_dir):
    #     if filename.endswith(".json"):
    #         patient_name = filename.split('_page_')[0]
    #         files_by_patient[patient_name].append(os.path.join(args.input_dir, filename))

    # # Process each patient's files
    # for patient, files in files_by_patient.items():
    #     print(f"--- Processing patient: {patient} ---")
    #     patient_results = []
    #     for file_path in sorted(files): # Sort to process pages in order
    #         page_results = parse_pedieat_page(file_path)
    #         for res in page_results:
    #             # Add patient identifier to each result
    #             res['patient_file'] = patient
    #             patient_results.append(res)
        
    #     # Sort results by question number and add to the main list
    #     all_results.extend(sorted(patient_results, key=lambda x: x['question_number']))
    patient_results = []

    page_results = parse_pedieat_page("outputs/aws_pedieat_page_1.json")
    for res in page_results:
        # Add patient identifier to each result
        res['patient_file'] = ""
        patient_results.append(res)
    
    # Sort results by question number and add to the main list
    all_results.extend(sorted(patient_results, key=lambda x: x['question_number']))


    # Write to CSV
    if not all_results:
        print("No data extracted. Exiting.")
        return
        
    with open("outputs/aws_pedieat_page_0.csv", 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['patient_file', 'question_number', 'observation', 'score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
            
    print(f"\n✅ Success! All data has been exported to outputs/aws_pedieat_page_1.csv")


if __name__ == '__main__':
    main()