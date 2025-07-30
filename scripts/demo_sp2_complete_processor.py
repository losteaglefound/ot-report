#!/usr/bin/env python3
"""
Demo script for AWS SP2 Complete Processor
Shows various usage patterns and integration examples
"""

import json
import os
from pathlib import Path
from aws_sp2_complete_processor import AWSSP2CompleteProcessor

def demo_basic_usage():
    """Demonstrate basic SP2 processing from PDF"""
    print("🚀 Demo: Basic SP2 Processing")
    print("=" * 50)
    
    # Example PDF path (replace with your actual SP2 PDF)
    pdf_path = "/home/lap-49/Documents/ot-report/assets/inputs/Sensory-Profile-2-Summary-Report_70247631_1751134355067.pdf"  # Change this to your PDF path
    
    if not os.path.exists(pdf_path):
        print(f"❌ Demo PDF not found: {pdf_path}")
        print("📝 Please update pdf_path to point to your SP2 PDF file")
        return
    
    try:
        # Initialize processor
        processor = AWSSP2CompleteProcessor(
            aws_access_key_id=os.getenv("AMAZON_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AMAZON_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AMAZON_REGION", "us-east-1"),
            output_dir="demo_outputs"
        )
        
        print(f"📄 Processing PDF: {pdf_path}")
        
        # Process the SP2 PDF
        results = processor.process_sp2_pdf_complete(pdf_path, "demo_sp2")
        
        print(f"✅ Processing completed successfully!")
        print(f"📊 SP2 Report: {results['files']['sp2_report']}")
        print(f"📋 Metadata: {results['files']['metadata']}")
        
        # Display summary
        metadata = results['metadata']
        print(f"\n📈 Processing Summary:")
        print(f"  📄 Pages processed: {metadata['pages_processed']}")
        print(f"  📝 Total items extracted: {metadata['total_items_extracted']}")
        print(f"  📊 Sections with data: {', '.join(metadata['sections_with_data'])}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔧 Check your AWS credentials and PDF file")
        return None


def demo_api_integration(results):
    """Demonstrate how to integrate SP2 data with report system"""
    print("\n🔗 Demo: API Integration")
    print("=" * 50)
    
    if not results:
        print("❌ No results from previous demo")
        return
    
    # Extract SP2 data
    sp2_data = results['sp2_report']['sp2']
    
    # Example: Extract specific information for report
    print("📊 Quadrant Scores:")
    for quadrant, scores in sp2_data['quadrant_score_summary'].items():
        print(f"  • {quadrant}: {scores['raw_score']} ({scores['classification']})")
    
    print("\n📈 Sensory Section Scores:")
    for section, scores in sp2_data['sensory_and_behavioral_section_score_summary'].items():
        if 'Processing' in section:  # Focus on main processing sections
            print(f"  • {section}: {scores['raw_score']} ({scores['classification']})")
    
    print("\n📝 Sample Assessment Items:")
    item_count = 0
    for section_name, section_data in sp2_data['processing'].items():
        if section_data['items'] and item_count < 3:
            for item in section_data['items'][:1]:  # Show 1 item per section
                print(f"  • {section_name} Item {item['item_no']}: {item['item_description'][:60]}...")
                item_count += 1
                if item_count >= 3:
                    break


def demo_report_integration():
    """Demonstrate integration with existing report system"""
    print("\n📋 Demo: Report System Integration")
    print("=" * 50)
    
    # Example: Load existing report data
    existing_report_data = {
        "patient_info": {
            "name": "Sample Patient",
            "age": "5:2",
            "date": "2024-11-21"
        },
        "assessment_type": "SP2",
        "therapist": "Dr. Smith"
    }
    
    # Example: Load SP2 data from saved file
    sp2_file = "demo_outputs/demo_sp2_sp2_report.json"
    if os.path.exists(sp2_file):
        with open(sp2_file, 'r') as f:
            sp2_data = json.load(f)
        
        # Merge SP2 data with existing report
        combined_report = {**existing_report_data, **sp2_data}
        
        print("✅ Successfully merged SP2 data with existing report structure")
        print(f"📊 Report now contains: {list(combined_report.keys())}")
        
        # Example: Extract key insights for summary
        sp2_section = combined_report['sp2']
        total_items = sum(len(section['items']) for section in sp2_section['processing'].values())
        high_concern_quadrants = [
            name for name, scores in sp2_section['quadrant_score_summary'].items()
            if 'Much More Than Others' in scores['classification']
        ]
        
        print(f"\n📈 Key Insights:")
        print(f"  • Total assessment items: {total_items}")
        print(f"  • Quadrants of concern: {', '.join(high_concern_quadrants) if high_concern_quadrants else 'None'}")
        
        # Save combined report
        combined_file = "demo_outputs/combined_report.json"
        with open(combined_file, 'w') as f:
            json.dump(combined_report, f, indent=4)
        print(f"💾 Combined report saved to: {combined_file}")
    
    else:
        print(f"❌ SP2 file not found: {sp2_file}")
        print("📝 Run demo_basic_usage() first to generate SP2 data")


def demo_batch_processing():
    """Demonstrate batch processing of multiple SP2 PDFs"""
    print("\n🔄 Demo: Batch Processing")
    print("=" * 50)
    
    # Example PDF paths (replace with your actual SP2 PDFs)
    pdf_files = [
        "assessment1.pdf",
        "assessment2.pdf", 
        "assessment3.pdf"
    ]
    
    # Filter to only existing files
    existing_files = [f for f in pdf_files if os.path.exists(f)]
    
    if not existing_files:
        print("❌ No demo PDFs found")
        print("📝 This demo requires multiple SP2 PDF files")
        print("💡 To test batch processing:")
        print("   1. Place multiple SP2 PDFs in the project directory")
        print("   2. Update the pdf_files list above")
        return
    
    try:
        processor = AWSSP2CompleteProcessor(output_dir="batch_outputs")
        
        batch_results = []
        for pdf_file in existing_files:
            print(f"📄 Processing: {pdf_file}")
            result = processor.process_sp2_pdf_complete(pdf_file)
            batch_results.append(result)
            print(f"✅ Completed: {result['metadata']['total_items_extracted']} items extracted")
        
        print(f"\n🎉 Batch processing completed!")
        print(f"📊 Processed {len(batch_results)} files")
        total_items = sum(r['metadata']['total_items_extracted'] for r in batch_results)
        print(f"📝 Total items extracted across all files: {total_items}")
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")


def demo_csv_fallback():
    """Demonstrate processing from CSV data (fallback method)"""
    print("\n📊 Demo: CSV Fallback Processing")
    print("=" * 50)
    
    # Use existing CSV if available
    csv_file = "notebook/output.csv"
    
    if os.path.exists(csv_file):
        print(f"📄 Processing CSV file: {csv_file}")
        
        try:
            # Import the standalone parser
            from aws_sp2_data_extract_report_format import parse_sp2_csv_to_report_format
            
            # Process CSV directly
            sp2_report = parse_sp2_csv_to_report_format(csv_file)
            
            # Save result
            output_file = "demo_outputs/csv_fallback_report.json"
            os.makedirs("demo_outputs", exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump({"sp2": sp2_report}, f, indent=4)
            
            print(f"✅ CSV processing completed!")
            print(f"💾 Report saved to: {output_file}")
            
            # Show summary and validation
            total_items = sum(len(section["items"]) for section in sp2_report["processing"].values())
            print(f"📝 Total items extracted: {total_items}")
            
            # Show detailed breakdown
            print(f"\n📊 Items by section:")
            for section_name, section_data in sp2_report["processing"].items():
                item_count = len(section_data["items"])
                raw_score = section_data["raw_score"]
                calculated_score = sum(item["score"] for item in section_data["items"])
                match_status = "✅" if raw_score == calculated_score else "❌"
                print(f"  • {section_name}: {item_count} items, Raw: {raw_score}, Calculated: {calculated_score} {match_status}")
            
            # Show sample items with scores
            print(f"\n📋 Sample items with scores:")
            sample_count = 0
            for section_name, section_data in sp2_report["processing"].items():
                if section_data["items"] and sample_count < 6:
                    for item in section_data["items"][:2]:
                        print(f"  • {section_name} #{item['item_no']}: {item['item_description'][:50]}... (Score: {item['score']})")
                        sample_count += 1
                        if sample_count >= 6:
                            break
            
            # Debug: Check for potential missing items by looking at raw vs calculated scores
            print(f"\n🔍 Debug Analysis:")
            for section_name, section_data in sp2_report["processing"].items():
                raw_score = section_data["raw_score"]
                calculated_score = sum(item["score"] for item in section_data["items"])
                if raw_score != calculated_score:
                    diff = raw_score - calculated_score
                    print(f"  • {section_name}: Missing {diff} points - might be {abs(diff)//1} items with avg 1 point or {abs(diff)//5} items with 5 points")
            
            # Check for zero-score items (DNA responses)
            zero_items = []
            for section_name, section_data in sp2_report["processing"].items():
                for item in section_data["items"]:
                    if item["score"] == 0:
                        zero_items.append(f"{section_name} #{item['item_no']}")
            
            if zero_items:
                print(f"\n⚠️  Items with score=0 (DNA): {', '.join(zero_items)}")
            else:
                print(f"\n✅ No DNA responses found (all items have scores > 0)")
            
        except Exception as e:
            print(f"❌ CSV processing error: {e}")
    
    else:
        print(f"❌ CSV file not found: {csv_file}")
        print("📝 This demo requires a SP2 CSV file for fallback processing")


def main():
    """Run all demos"""
    print("🎯 AWS SP2 Complete Processor - Demo Suite")
    print("=" * 60)
    
    # Create demo outputs directory
    os.makedirs("demo_outputs", exist_ok=True)
    
    # Demo 1: Basic processing
    results = demo_basic_usage()
    
    # Demo 2: API integration
    demo_api_integration(results)
    
    # Demo 3: Report integration
    demo_report_integration()
    
    # Demo 4: CSV fallback
    demo_csv_fallback()
    
    # Demo 5: Batch processing (if multiple PDFs available)
    demo_batch_processing()
    
    print("\n🎉 All demos completed!")
    print("📁 Check 'demo_outputs' directory for generated files")
    print("\n💡 Next Steps:")
    print("  1. Review the generated SP2 report JSON files")
    print("  2. Integrate the SP2 data structure into your report system")
    print("  3. Customize the processor for your specific needs")
    print("  4. Set up batch processing for multiple assessments")


if __name__ == "__main__":
    main() 