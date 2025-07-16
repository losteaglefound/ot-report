#!/usr/bin/env python3
"""
AWS Textract OCR Table Analyzer
Extracts tables from PDF documents using Amazon Textract analyze_document API
Processes each page individually and saves responses with enumeration
"""

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
import time
from traceback import format_exc
from typing import Dict, List, Optional, Any
from PIL import Image
import io

import boto3
from dotenv import load_dotenv
import fitz  # PyMuPDF

# from aws_respnose_parser import parse_chomps_json

assert load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


full_response = {}

class AWSTextractOCRTableAnalyzer:
    """
    A class to analyze PDF documents page by page and extract table data using AWS Textract analyze_document API
    """
    
    def __init__(self, 
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
            region_name: str = 'us-east-1',
            output_dir: str = 'outputs'
        ):
        """
        Initialize the Textract OCR analyzer
        
        Args:
            aws_access_key_id: AWS access key ID (optional, can use env vars)
            aws_secret_access_key: AWS secret access key (optional, can use env vars)
            region_name: AWS region name
            output_dir: Directory to store output files
        """
        self.region_name = region_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize Textract client
        try:
            session_kwargs = {'region_name': region_name}
            if aws_access_key_id and aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                })
            
            self.textract_client = boto3.client('textract', **session_kwargs)
            self.logger.info(f"Initialized Textract client for region: {region_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Textract client: {e}")
            raise
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'textract_ocr_analyzer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_pages_as_bytes(self, pdf_path: str) -> List[bytes]:
        """
        Extract all pages from PDF as bytes
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of page bytes
        """
        try:
            self.logger.info(f"📄 Extracting pages from PDF: {pdf_path}")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            page_bytes_list = []
            
            for page_num in range(len(doc)):
                self.logger.info(f"🔄 Processing page {page_num + 1}/{len(doc)}")
                
                # Get page
                page = doc[page_num]
                
                # Convert page to image (PNG format)
                pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
                img_data = pix.tobytes("png")
                
                page_bytes_list.append(img_data)
            
            doc.close()
            self.logger.info(f"✅ Successfully extracted {len(page_bytes_list)} pages as bytes")
            return page_bytes_list
            
        except Exception as e:
            self.logger.error(f"Failed to extract pages from PDF: {e}")
            raise
    
    def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze a PDF document to extract tables using analyze_document API
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing all page analysis results
        """
        try:
            self.logger.info(f"🔍 Starting OCR table analysis of document: {pdf_path}")
            
            # Extract pages as bytes
            page_bytes_list = self.extract_pages_as_bytes(pdf_path)
            
            # Analyze each page
            all_responses = []
            
            for page_num, page_bytes in enumerate(page_bytes_list):
                self.logger.info(f"📊 Analyzing page {page_num + 1}/{len(page_bytes_list)}")
                
                try:
                    # Call Textract analyze_document for this page
                    response = self.textract_client.analyze_document(
                        Document={'Bytes': page_bytes},
                        FeatureTypes=['TABLES', 'FORMS']
                    )

                    with open(f"outputs/aws_pedieat_page_{page_num}.json", 'w+') as f:
                        f.write(json.dumps(response, indent=4))

                    # json_data = parse_chomps_json(response)
                    # if json_data.get('patientInfo', {}).get("name", ""):
                    #     full_response['patientInfo'] = json_data['patientInfo']
                    # if check1 := json_data.get("observations", []):
                    #     if check2 := full_response.get("observations", []):
                    #         full_response['observations'].extend(json_data['observations'])
                    #     else:
                    #         full_response['observations'] = json_data['observations']
                    
                    # Process the response
                    processed_response = self.process_textract_response(response, page_num + 1)
                    all_responses.append(processed_response)
                    
                    # Add small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(format_exc())
                    self.logger.error(f"Failed to analyze page {page_num + 1}: {e}")
                    # Continue with next page
                    error_response = {
                        'page_number': page_num + 1,
                        'error': str(e),
                        'tables': [],
                        'extracted_text': [],
                        'raw_response': None
                    }
                    all_responses.append(error_response)
            
            # Create final result
            final_result = {
                'pages': all_responses,
                'metadata': {
                    'source_file': pdf_path,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'total_pages': len(page_bytes_list),
                    'successful_pages': len([r for r in all_responses if 'error' not in r]),
                    'failed_pages': len([r for r in all_responses if 'error' in r]),
                    'aws_region': self.region_name,
                    'analysis_method': 'analyze_document'
                }
            }
            
            self.logger.info(f"✅ Successfully analyzed document: {pdf_path}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing document {pdf_path}: {e}")
            raise
    
    def process_textract_response(self, response: Dict[str, Any], page_number: int) -> Dict[str, Any]:
        """
        Process the Textract API response to extract table data
        
        Args:
            response: Raw response from Textract analyze_document API
            page_number: Page number being processed
            
        Returns:
            Processed table data for this page
        """
        try:
            self.logger.info(f"📄 Processing Textract response for page {page_number}")
            
            # Check if we have blocks
            if 'Blocks' not in response or not response['Blocks']:
                self.logger.warning(f"⚠️ No blocks found in Textract response for page {page_number}")
                return {
                    'page_number': page_number,
                    'tables': [],
                    'extracted_text': [],
                    'raw_response': response
                }
            
            blocks = response['Blocks']
            
            # Create mappings for easier data access
            block_map = {block['Id']: block for block in blocks}
            
            # Extract tables
            tables = []
            table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
            
            self.logger.info(f"📊 Found {len(table_blocks)} tables on page {page_number}")
            
            for i, table_block in enumerate(table_blocks):
                self.logger.info(f"🔍 Processing table {i+1}/{len(table_blocks)} on page {page_number}")
                table_data = self.extract_table_data(table_block, block_map)
                table_data['page_number'] = page_number
                tables.append(table_data)
            
            # Extract all text for reference
            text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
            extracted_text = [block['Text'] for block in text_blocks]
            
            return {
                'page_number': page_number,
                'tables': tables,
                'extracted_text': extracted_text,
                'raw_response': response
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Textract response for page {page_number}: {e}")
            raise
    
    def extract_table_data(self, table_block: Dict[str, Any], block_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from a table block
        
        Args:
            table_block: Table block from Textract response
            block_map: Mapping of block IDs to block data
            
        Returns:
            Structured table data
        """
        table_data = {
            'table_id': table_block['Id'],
            'confidence': table_block.get('Confidence', 0),
            'geometry': table_block.get('Geometry', {}),
            'rows': []
        }
        
        # Get all cells in the table
        cell_blocks = []
        if 'Relationships' in table_block:
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        cell_block = block_map.get(child_id)
                        if cell_block and cell_block['BlockType'] == 'CELL':
                            cell_blocks.append(cell_block)
        
        # Organize cells by row and column
        cells_by_position = {}
        for cell in cell_blocks:
            row_index = cell['RowIndex']
            col_index = cell['ColumnIndex']
            
            if row_index not in cells_by_position:
                cells_by_position[row_index] = {}
            
            # Extract cell text
            cell_text = self.extract_cell_text(cell, block_map)
            
            cells_by_position[row_index][col_index] = {
                'text': cell_text,
                'confidence': cell.get('Confidence', 0),
                'row_span': cell.get('RowSpan', 1),
                'column_span': cell.get('ColumnSpan', 1)
            }
        
        # Convert to structured rows
        for row_index in sorted(cells_by_position.keys()):
            row_data = {
                'row_index': row_index,
                'cells': []
            }
            
            row_cells = cells_by_position[row_index]
            for col_index in sorted(row_cells.keys()):
                row_data['cells'].append({
                    'column_index': col_index,
                    **row_cells[col_index]
                })
            
            table_data['rows'].append(row_data)
        
        return table_data
    
    def extract_cell_text(self, cell_block: Dict[str, Any], block_map: Dict[str, Any]) -> str:
        """
        Extract text from a cell block
        
        Args:
            cell_block: Cell block from Textract response
            block_map: Mapping of block IDs to block data
            
        Returns:
            Extracted text from the cell
        """
        cell_text = ""
        
        if 'Relationships' in cell_block:
            for relationship in cell_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        word_block = block_map.get(child_id)
                        if word_block and word_block['BlockType'] == 'WORD':
                            cell_text += word_block['Text'] + " "
        
        return cell_text.strip()
    
    def save_results(self, results: Dict[str, Any], output_filename: Optional[str] = None) -> str:
        """
        Save analysis results to files with enumeration
        
        Args:
            results: Analysis results dictionary
            output_filename: Optional custom filename
            
        Returns:
            Path to the main saved file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_name = Path(results['metadata']['source_file']).stem
            output_filename = f"textract_ocr_analysis_{source_name}_{timestamp}"
        
        # Save complete results JSON
        json_path = self.output_dir / f"{output_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save each page response with enumeration
        page_paths = []
        for i, page_result in enumerate(results['pages']):
            page_json_path = self.output_dir / f"{output_filename}_page_{i+1:03d}.json"
            with open(page_json_path, 'w', encoding='utf-8') as f:
                json.dump(page_result, f, indent=2, ensure_ascii=False)
            page_paths.append(page_json_path)
        
        # Save human-readable summary
        summary_path = self.output_dir / f"{output_filename}_summary.txt"
        self.save_summary(results, summary_path)
        
        # Save CSV files for each table with enumeration
        csv_paths = []
        table_counter = 1
        for page_num, page_result in enumerate(results['pages']):
            if 'error' in page_result:
                continue
            
            for table_idx, table in enumerate(page_result['tables']):
                csv_path = self.output_dir / f"{output_filename}_table_{table_counter:03d}_page_{page_num+1}.csv"
                self.save_table_csv(table, csv_path)
                csv_paths.append(csv_path)
                table_counter += 1
        
        # Log saved files
        self.logger.info(f"✅ Complete results saved to: {json_path}")
        self.logger.info(f"📄 Individual page results saved: {len(page_paths)} files")
        self.logger.info(f"📊 Table CSV files saved: {len(csv_paths)} files")
        self.logger.info(f"📋 Summary saved to: {summary_path}")
        
        return str(json_path)
    
    def save_summary(self, results: Dict[str, Any], summary_path: Path):
        """
        Save a human-readable summary of the analysis
        
        Args:
            results: Analysis results dictionary
            summary_path: Path to save the summary file
        """
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("AWS Textract OCR Table Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            metadata = results['metadata']
            f.write(f"Source File: {metadata['source_file']}\n")
            f.write(f"Analysis Date: {metadata['analysis_timestamp']}\n")
            f.write(f"Total Pages: {metadata['total_pages']}\n")
            f.write(f"Successful Pages: {metadata['successful_pages']}\n")
            f.write(f"Failed Pages: {metadata['failed_pages']}\n")
            f.write(f"AWS Region: {metadata['aws_region']}\n")
            f.write(f"Analysis Method: {metadata['analysis_method']}\n\n")
            
            # Page-by-page summary
            total_tables = 0
            for page_num, page_result in enumerate(results['pages']):
                f.write(f"Page {page_num + 1}:\n")
                
                if 'error' in page_result:
                    f.write(f"  ❌ Error: {page_result['error']}\n")
                else:
                    page_tables = len(page_result['tables'])
                    total_tables += page_tables
                    f.write(f"  📊 Tables found: {page_tables}\n")
                    f.write(f"  📝 Text lines: {len(page_result['extracted_text'])}\n")
                    
                    # Table details
                    for i, table in enumerate(page_result['tables']):
                        f.write(f"    Table {i+1}: {len(table['rows'])} rows, confidence: {table['confidence']:.1f}%\n")
                
                f.write("\n")
            
            f.write(f"Total Tables Found: {total_tables}\n")
    
    def save_table_csv(self, table: Dict[str, Any], csv_path: Path):
        """
        Save a table as CSV file
        
        Args:
            table: Table data dictionary
            csv_path: Path to save the CSV file
        """
        import csv
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write table rows
            for row in table['rows']:
                csv_row = [cell['text'] for cell in row['cells']]
                writer.writerow(csv_row)


def main():
    """Main function to run the script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze PDF documents using AWS Textract OCR (analyze_document API)')
    parser.add_argument(
        'pdf_path', 
        help='Path to the PDF file to analyze',
    )
    parser.add_argument(
        '--output-dir', 
        default='outputs', 
        help='Output directory for results',
    )
    parser.add_argument(
        '--output-filename', 
        help='Custom output filename (without extension)',
        default="chomps_image"
    )
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file '{args.pdf_path}' not found.")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        analyzer = AWSTextractOCRTableAnalyzer(
            aws_access_key_id=os.getenv("AMAZON_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AMAZON_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AMAZON_REGION"),
            output_dir=args.output_dir
        )
        
        # Analyze document
        print(f"🔍 Analyzing document: {args.pdf_path}")
        print("📄 Processing pages individually using OCR...")
        results = analyzer.analyze_document(args.pdf_path)
        
        # Save results
        output_path = analyzer.save_results(results, args.output_filename)
        
        print(f"\n🎉 Analysis complete! Results saved to: {output_path}")
        
        # Print summary
        metadata = results.get('metadata', {})
        print(f"📄 Total pages: {metadata.get('total_pages', 'Unknown')}")
        print(f"✅ Successful pages: {metadata.get('successful_pages', 'Unknown')}")
        print(f"❌ Failed pages: {metadata.get('failed_pages', 'Unknown')}")
        
        # Count total tables
        total_tables = 0
        for page_result in results['pages']:
            if 'error' not in page_result:
                total_tables += len(page_result['tables'])
        
        print(f"📊 Total tables found: {total_tables}")
        
        if total_tables > 0:
            print("\n📋 Page-by-page Summary:")
            for page_num, page_result in enumerate(results['pages']):
                if 'error' in page_result:
                    print(f"  📄 Page {page_num + 1}: ❌ Error - {page_result['error']}")
                else:
                    page_tables = len(page_result['tables'])
                    print(f"  📄 Page {page_num + 1}: {page_tables} tables")

        with open("aws_full_response_parse.json", 'w+') as f:
            json.dump(full_response, f, indent=4)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("🔧 Please check:")
        print("  - AWS credentials are configured correctly")
        print("  - You have sufficient Textract permissions")
        print("  - PDF file is not corrupted")
        print("  - PyMuPDF is installed (pip install PyMuPDF)")
        sys.exit(1)


if __name__ == "__main__":
    main() 