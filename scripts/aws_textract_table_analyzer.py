#!/usr/bin/env python3
"""
AWS Textract Table Analyzer
Extracts tables from PDF documents using Amazon Textract
"""

import boto3
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
import time
from traceback import format_exc
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv


assert load_dotenv()


# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AWSTextractTableAnalyzer:
    """
    A class to analyze PDF documents and extract table data using AWS Textract
    """
    
    def __init__(self, 
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
            region_name: str = 'us-east-1',
            bucket_name: str | None = None,
            output_dir: str = 'outputs'
        ):
        """
        Initialize the Textract analyzer
        
        Args:
            aws_access_key_id: AWS access key ID (optional, can use env vars)
            aws_secret_access_key: AWS secret access key (optional, can use env vars)
            region_name: AWS region name
            output_dir: Directory to store output files
        """
        self.region_name = region_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.bucket_name = bucket_name
        
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
            self.s3_client = boto3.client("s3", **session_kwargs)
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
                logging.FileHandler(log_dir / 'textract_analyzer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)


    def upload_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Upload file to S3 bucket.

        Args:
            pdf_path: path of local file
        
        Returns:
            dict: Upload response information
        """
        
        try:
            filename = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # Size in MB
            
            self.logger.info(f"📤 Uploading {filename} ({file_size:.2f} MB) to S3 bucket: {self.bucket_name}")
            
            # Upload to S3
            self.s3_client.upload_file(
                pdf_path, 
                self.bucket_name, 
                filename
            )
            
            self.logger.info(f"✅ Successfully uploaded {filename} to S3")
            
            return {
                'success': True,
                'filename': filename,
                'bucket': self.bucket_name,
                'file_size_mb': file_size,
                'local_path': pdf_path
            }
            
        except Exception as e:
            error_msg = f"Failed to upload {os.path.basename(pdf_path)} to S3: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    
    def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze a PDF document to extract tables
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted table data and metadata
        """
        try:
            # Validate prerequisites
            if not self.bucket_name:
                raise ValueError("S3 bucket name is required for document analysis. Please set AMAZON_S3_BUCKET environment variable.")
            
            self.logger.info(f"Starting analysis of document: {pdf_path}")
            
            # Get the filename to use for S3 upload
            filename = os.path.basename(pdf_path)
            
            # Call Textract to analyze the document
            start_response = self.textract_client.start_document_analysis(
                    DocumentLocation={
                        'S3Object': {
                            'Bucket': self.bucket_name,
                            'Name': filename
                        }
                    },
                    FeatureTypes=["TABLES"]
            )
            print(f"Started analysis job: {start_response['JobId']}")
            
            # Process the response and get final results
            analysis_results = self.process_textract_response(start_response)
            
            # Add metadata using the final analysis result
            final_result = analysis_results.get('final_analysis_result')
            if final_result and final_result.get('Blocks'):
                blocks = final_result['Blocks']
                analysis_results['metadata'] = {
                    'source_file': pdf_path,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'total_pages': len(set(block.get('Page', 1) for block in blocks)),
                    'total_blocks': len(blocks),
                    'aws_region': self.region_name,
                    'job_id': start_response['JobId']
                }
            else:
                # Fallback metadata if no blocks available
                analysis_results['metadata'] = {
                    'source_file': pdf_path,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'total_pages': 0,
                    'total_blocks': 0,
                    'aws_region': self.region_name,
                    'job_id': start_response['JobId']
                }
            
            self.logger.info(f"Successfully analyzed document: {pdf_path}")
            return analysis_results
            
        except Exception as e:
            print(format_exc())
            self.logger.error(f"Error analyzing document {pdf_path}: {e}")
            raise
    
    def process_textract_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the Textract API response to extract table data
        
        Args:
            response: Raw response from Textract start_document_analysis API
            
        Returns:
            Processed table data
        """
        
        job_id = response['JobId']
        self.logger.info(f"🔄 Processing Textract job: {job_id}")
        
        # Poll for job completion
        while True:
            result = self.textract_client.get_document_analysis(JobId=job_id)
            status = result['JobStatus']
            
            if status == 'SUCCEEDED':
                self.logger.info("✅ Textract job completed successfully")
                
                with open("outputs/chomps_aws_result.json", 'w+') as f:
                    f.write(json.dumps(result, indent=4))
                
                break
            elif status == 'FAILED':
                error_msg = f"Textract job failed: {result.get('StatusMessage', 'Unknown error')}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
            elif status == 'PARTIAL_SUCCESS':
                self.logger.warning("⚠️ Textract job completed with partial success")
                break
            elif status == 'IN_PROGRESS':
                print("⏳ Waiting for job to complete...")
                time.sleep(5)
            else:
                print(f"⏳ Job status: {status}, waiting...")
                time.sleep(5)

       

        # Final status check
        if result['JobStatus'] == 'FAILED':
            error_msg = f"Textract analysis failed: {result.get('StatusMessage', 'Unknown error')}"
            raise Exception(error_msg)

        # Now result contains the analyzed document
        self.logger.info("📄 Processing extracted blocks...")

        print("\n\n")
        print(result)
        print("\n\n")
        # Check if we have blocks
        if 'Blocks' not in result or not result['Blocks']:
            self.logger.warning("⚠️ No blocks found in Textract response")
            return {
                'tables': [],
                'extracted_text': [],
                'raw_response': response,
                'final_analysis_result': result,
                'job_status': result['JobStatus'],
                'job_id': job_id
            }
        
        # Print extracted text for debugging (limit to first 10 lines)
        line_blocks = [block for block in result['Blocks'] if block['BlockType'] == 'LINE']
        for i, block in enumerate(line_blocks[:10]):
            print(f"📝 {block['Text']}")
        
        if len(line_blocks) > 10:
            print(f"📝 ... and {len(line_blocks) - 10} more lines")

        blocks = result['Blocks']
        
        # Create mappings for easier data access
        block_map = {block['Id']: block for block in blocks}
        
        # Extract tables
        tables = []
        table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
        
        self.logger.info(f"📊 Found {len(table_blocks)} tables to process")
        
        for i, table_block in enumerate(table_blocks):
            self.logger.info(f"🔍 Processing table {i+1}/{len(table_blocks)}")
            table_data = self.extract_table_data(table_block, block_map)
            tables.append(table_data)
        
        # Extract all text for reference
        text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
        extracted_text = [block['Text'] for block in text_blocks]

        return {
            'tables': tables,
            'extracted_text': extracted_text,
            'raw_response': response,  # Original start response for reference
            'final_analysis_result': result,  # Final analysis result with blocks
            'job_status': result['JobStatus'],
            'job_id': job_id
        }
    
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
            'page': table_block.get('Page', 1),
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
        Save analysis results to files
        
        Args:
            results: Analysis results dictionary
            output_filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_name = Path(results['metadata']['source_file']).stem
            output_filename = f"textract_analysis_{source_name}_{timestamp}"
        
        # Save JSON results
        json_path = self.output_dir / f"{output_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save human-readable summary
        summary_path = self.output_dir / f"{output_filename}_summary.txt"
        self.save_summary(results, summary_path)
        
        # Save CSV files for each table
        csv_paths = []
        for i, table in enumerate(results['tables']):
            csv_path = self.output_dir / f"{output_filename}_table_{i+1}.csv"
            self.save_table_csv(table, csv_path)
            csv_paths.append(csv_path)
        
        self.logger.info(f"Results saved to: {json_path}")
        self.logger.info(f"Summary saved to: {summary_path}")
        for csv_path in csv_paths:
            self.logger.info(f"Table CSV saved to: {csv_path}")
        
        return str(json_path)
    
    def save_summary(self, results: Dict[str, Any], summary_path: Path):
        """
        Save a human-readable summary of the analysis
        
        Args:
            results: Analysis results dictionary
            summary_path: Path to save the summary file
        """
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("AWS Textract Table Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            metadata = results['metadata']
            f.write(f"Source File: {metadata['source_file']}\n")
            f.write(f"Analysis Date: {metadata['analysis_timestamp']}\n")
            f.write(f"Total Pages: {metadata['total_pages']}\n")
            f.write(f"Total Blocks: {metadata['total_blocks']}\n")
            f.write(f"AWS Region: {metadata['aws_region']}\n\n")
            
            # Tables summary
            f.write(f"Number of Tables Found: {len(results['tables'])}\n\n")
            
            for i, table in enumerate(results['tables']):
                f.write(f"Table {i+1}:\n")
                f.write(f"  - Table ID: {table['table_id']}\n")
                f.write(f"  - Page: {table['page']}\n")
                f.write(f"  - Confidence: {table['confidence']:.2f}%\n")
                f.write(f"  - Rows: {len(table['rows'])}\n")
                
                if table['rows']:
                    max_cols = max(len(row['cells']) for row in table['rows'])
                    f.write(f"  - Columns: {max_cols}\n")
                
                f.write("\n")
    
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
    
    parser = argparse.ArgumentParser(description='Analyze PDF documents using AWS Textract')
    parser.add_argument('pdf_path', help='Path to the PDF file to analyze')
    parser.add_argument('--output-dir', default='outputs', help='Output directory for results')
    parser.add_argument('--output-filename', help='Custom output filename (without extension)')
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF file '{args.pdf_path}' not found.")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        analyzer = AWSTextractTableAnalyzer(
            aws_access_key_id=os.getenv("AMAZON_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AMAZON_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AMAZON_REGION"),
            bucket_name=os.getenv("AMAZON_S3_BUCKET"),
            output_dir=args.output_dir
        )

        # Upload file to S3 first
        print(f"📤 Uploading file to S3...")
        upload_response = analyzer.upload_document(args.pdf_path)
        print(f"✅ Successfully uploaded to S3")
        
        # Analyze document
        print(f"🔍 Analyzing document: {args.pdf_path}")
        print("⏳ This may take a few minutes for large documents...")
        results = analyzer.analyze_document(args.pdf_path)
        
        # Save results
        output_path = analyzer.save_results(results, args.output_filename)
        
        print(f"\n🎉 Analysis complete! Results saved to: {output_path}")
        print(f"📊 Found {len(results['tables'])} tables in the document.")
        
        # Print summary
        metadata = results.get('metadata', {})
        print(f"📄 Total pages: {metadata.get('total_pages', 'Unknown')}")
        print(f"🔢 Total blocks: {metadata.get('total_blocks', 'Unknown')}")
        print(f"🆔 Job ID: {metadata.get('job_id', 'Unknown')}")
        
        if results['tables']:
            print("\n📋 Table Summary:")
            for i, table in enumerate(results['tables']):
                print(f"  📊 Table {i+1}: {len(table['rows'])} rows, confidence: {table['confidence']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("🔧 Please check:")
        print("  - AWS credentials are configured correctly")
        print("  - S3 bucket exists and you have write permissions")
        print("  - PDF file is not corrupted")
        print("  - You have sufficient Textract permissions")
        sys.exit(1)


if __name__ == "__main__":
    main() 