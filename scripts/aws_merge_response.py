import json
import glob
import os

def merge_textract_json_files(file_paths, output_file):
    """
    Merges multiple AWS Textract JSON response files into a single file.

    Args:
        file_paths (list): A list of paths to the JSON files to merge.
        output_file (str): The path to save the merged JSON file.
    """
    if not file_paths:
        print("No files to merge.")
        return

    # Use the first file as the base for the merged data
    with open(file_paths[0], 'r') as f:
        merged_data = json.load(f)

    with open(file_paths[0], 'r') as f:
        merged_data = json.load(f)

    # Overwrite page count based on files merged
    merged_data["DocumentMetadata"]["Pages"] = len(file_paths)

    # Append blocks from remaining files
    for idx, file_path in enumerate(file_paths[1:], start=2):
        with open(file_path, 'r') as f:
            data = json.load(f)
            for block in data.get('Blocks', []):
                block['Page'] = idx
            merged_data['Blocks'].extend(data.get('Blocks', []))

    # Save the merged data to the output file
    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=4)
        
    print(f"Successfully merged {len(file_paths)} files into {output_file}")


if __name__ == '__main__':
    # --- How to use this script ---
    
    # 1. Place all your Textract JSON files for a single document in one folder.
    #    For example: 'textract_outputs/page_1.json', 'textract_outputs/page_2.json', ...
    
    # 2. Specify the folder and the pattern to find your files.
    #    Here, we're looking for all .json files in a folder named 'textract_responses'
    folder_path = 'outputs/'
    json_files = glob.glob(os.path.join(folder_path, 'aws_sp2_page_*.json'))
    print(json_files)
    
    # 3. Specify the name for the merged output file.
    merged_output_file = 'outputs/aws_sp2_page_merged.json'
    

    # 4. Run the merge function.
    if json_files:
        merge_textract_json_files(sorted(json_files), merged_output_file) # Sort to maintain page order
    else:
        print(f"No JSON files found in the directory: {folder_path}")