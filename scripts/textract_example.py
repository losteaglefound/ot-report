#!/usr/bin/env python3
"""
Example script demonstrating how to use the AWS Textract Table Analyzer
"""

import os
import sys
from pathlib import Path

# Add the current directory to sys.path to import the analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aws_textract_start_document_analysis import AWSTextractTableAnalyzer

def main():
    """
    Example usage of the AWS Textract Table Analyzer
    """
    
    # Configuration
    PDF_PATH = "../uploads/sample.pdf"  # Update this path to your PDF
    OUTPUT_DIR = "../outputs"
    
    # AWS Configuration (you can also set these as environment variables)
    # AWS_ACCESS_KEY_ID = "your_access_key_here"
    # AWS_SECRET_ACCESS_KEY = "your_secret_key_here"
    REGION = "us-east-1"
    
    print("AWS Textract Table Analyzer Example")
    print("=" * 40)
    
    # Check if PDF exists
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file '{PDF_PATH}' not found.")
        print("Please update the PDF_PATH variable or place a PDF file in the uploads directory.")
        return
    
    try:
        # Initialize the analyzer
        # Note: If you don't provide AWS credentials here, boto3 will look for them in:
        # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 2. AWS credentials file (~/.aws/credentials)
        # 3. IAM roles (if running on EC2)
        
        analyzer = AWSTextractTableAnalyzer(
            # aws_access_key_id=AWS_ACCESS_KEY_ID,      # Uncomment if providing directly
            # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,  # Uncomment if providing directly
            region_name=REGION,
            output_dir=OUTPUT_DIR
        )
        
        print(f"Analyzing document: {PDF_PATH}")
        print("This may take a moment...")
        
        # Analyze the document
        results = analyzer.analyze_document(PDF_PATH)
        
        # Save results
        output_path = analyzer.save_results(results)
        
        # Print summary
        print("\nAnalysis Complete!")
        print(f"✓ Results saved to: {output_path}")
        print(f"✓ Found {len(results['tables'])} tables in the document")
        print(f"✓ Total pages analyzed: {results['metadata']['total_pages']}")
        
        # Print table details
        if results['tables']:
            print("\nTable Details:")
            for i, table in enumerate(results['tables']):
                print(f"  Table {i+1}:")
                print(f"    - Page: {table['page']}")
                print(f"    - Confidence: {table['confidence']:.2f}%")
                print(f"    - Rows: {len(table['rows'])}")
                if table['rows']:
                    max_cols = max(len(row['cells']) for row in table['rows'])
                    print(f"    - Columns: {max_cols}")
                print()
        
        print("Check the outputs directory for detailed results:")
        print(f"  - JSON file: Complete analysis data")
        print(f"  - Summary file: Human-readable summary")
        print(f"  - CSV files: Individual tables as CSV")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your AWS credentials are configured")
        print("2. Ensure you have the required permissions for Textract")
        print("3. Check that the PDF file is valid and readable")
        print("4. Verify your AWS region setting")


if __name__ == "__main__":
    main() 