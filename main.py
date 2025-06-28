from fastapi import FastAPI, File, UploadFile, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio
import logging

# Configure logging
os.makedirs("logs", exist_ok=True)  # Create logs directory first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from report_generator import OTReportGenerator
from pdf_processor import EnhancedPDFProcessor
from google_docs_integration import GoogleDocsReportGenerator
from email_notifier import EmailNotifier
from openai_report_generator import OpenAIEnhancedReportGenerator

app = FastAPI(title="Pediatric OT Report Generator", description="Automated Pediatric OT Report Generation from Multiple Assessment PDFs")

# Create directories if they don't exist
directories = ["uploads", "outputs", "static", "templates", "logs"]
for directory in directories:
    os.makedirs(directory, exist_ok=True)
    logger.info(f"✅ Directory ensured: {directory}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("✅ Static files mounted")

# Setup templates
templates = Jinja2Templates(directory="templates")
logger.info("✅ Templates configured")

# Initialize processors with logging
try:
    pdf_processor = EnhancedPDFProcessor()
    logger.info("✅ PDF processor initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize PDF processor: {e}")
    pdf_processor = None

try:
    report_generator = OTReportGenerator()
    logger.info("✅ Basic report generator initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize basic report generator: {e}")
    report_generator = None

try:
    openai_report_generator = OpenAIEnhancedReportGenerator()
    if openai_report_generator.openai_client:
        logger.info("✅ OpenAI-enhanced report generator initialized with API access")
    else:
        logger.warning("⚠️ OpenAI-enhanced report generator initialized without API key")
except Exception as e:
    logger.error(f"❌ Failed to initialize OpenAI report generator: {e}")
    openai_report_generator = None

try:
    google_docs_generator = GoogleDocsReportGenerator()
    logger.info("✅ Google Docs generator initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Google Docs generator: {e}")
    google_docs_generator = None

try:
    email_notifier = EmailNotifier()
    logger.info("✅ Email notifier initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize email notifier: {e}")
    email_notifier = None

def log_startup_status():
    """Log system status on startup"""
    logger.info("🚀 Pediatric OT Report Generator starting up...")
    logger.info(f"📊 System Status:")
    logger.info(f"   PDF Processor: {'✅ Ready' if pdf_processor else '❌ Failed'}")
    logger.info(f"   Basic Reports: {'✅ Ready' if report_generator else '❌ Failed'}")
    logger.info(f"   AI Reports: {'✅ Ready' if openai_report_generator and openai_report_generator.openai_client else '⚠️ No API Key' if openai_report_generator else '❌ Failed'}")
    logger.info(f"   Google Docs: {'✅ Ready' if google_docs_generator and hasattr(google_docs_generator, 'service') and google_docs_generator.service else '⚠️ No Service Account' if google_docs_generator else '❌ Failed'}")
    logger.info(f"   Email: {'✅ Ready' if email_notifier else '❌ Failed'}")

# Log startup status immediately
log_startup_status()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with enhanced file upload interface"""
    logger.info("📄 Home page requested")
    try:
        response = templates.TemplateResponse("index.html", {"request": request})
        logger.info("✅ Home page rendered successfully")
        return response
    except Exception as e:
        logger.error(f"❌ Failed to render home page: {e}")
        raise HTTPException(status_code=500, detail="Failed to load home page")

@app.post("/upload-files/")
async def upload_files(
    request: Request,
    # Required files
    facesheet_file: Optional[UploadFile] = File(None),
    bayley4_cognitive_file: Optional[UploadFile] = File(None),
    bayley4_social_file: Optional[UploadFile] = File(None),
    # Optional assessment files
    sp2_file: Optional[UploadFile] = File(None),
    chomps_file: Optional[UploadFile] = File(None),
    pedieat_file: Optional[UploadFile] = File(None),
    clinical_notes_file: Optional[UploadFile] = File(None),
    # Patient information
    patient_name: str = Form(...),
    date_of_birth: str = Form(...),
    encounter_date: str = Form(...),
    parent_guardian: str = Form(...),
    uci_number: str = Form(...),
    sex: str = Form(...),
    language: str = Form(...),
    # Report preferences
    output_format: str = Form("google_docs"),  # google_docs, pdf, both
    report_type: str = Form("professional"),  # professional (OpenAI), basic
    notify_email: str = Form("fushia.crooms@gmail.com")
):
    """Upload multiple assessment files and generate comprehensive OT report"""
    session_id = str(uuid.uuid4())
    logger.info(f"🔄 Starting new report generation session: {session_id}")
    logger.info(f"👤 Patient: {patient_name}, Report Type: {report_type}, Output: {output_format}")
    
    try:
        # Generate unique session ID
        session_dir = os.path.join("uploads", session_id)
        os.makedirs(session_dir, exist_ok=True)
        logger.info(f"📁 Created session directory: {session_dir}")
        
        # Save uploaded files
        uploaded_files = {}
        file_mappings = {
            "facesheet": facesheet_file,
            "bayley4_cognitive": bayley4_cognitive_file,
            "bayley4_social": bayley4_social_file,
            "sp2": sp2_file,
            "chomps": chomps_file,
            "pedieat": pedieat_file,
            "clinical_notes": clinical_notes_file
        }
        
        logger.info("📄 Processing uploaded files...")
        for file_type, file_obj in file_mappings.items():
            if file_obj and file_obj.filename:
                file_path = os.path.join(session_dir, f"{file_type}.pdf")
                try:
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file_obj.file, buffer)
                    uploaded_files[file_type] = file_path
                    file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                    logger.info(f"✅ Saved {file_type}: {file_obj.filename} ({file_size:.2f} MB)")
                except Exception as e:
                    logger.error(f"❌ Failed to save {file_type}: {e}")
            else:
                logger.info(f"⏭️ Skipped {file_type}: No file provided")
        
        logger.info(f"📊 Total files uploaded: {len(uploaded_files)}")
        
        # Calculate chronological age
        logger.info("🧮 Calculating chronological age...")
        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            encounter = datetime.strptime(encounter_date, "%Y-%m-%d")
            
            if not pdf_processor:
                raise Exception("PDF processor not available")
                
            chronological_age = pdf_processor.calculate_chronological_age(dob, encounter)
            logger.info(f"✅ Age calculated: {chronological_age.get('formatted', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ Failed to calculate age: {e}")
            chronological_age = {"formatted": "Unknown", "total_days": 0}
        
        # Process all uploaded PDFs
        logger.info("🔍 Processing PDF assessments...")
        try:
            if not pdf_processor:
                raise Exception("PDF processor not initialized")
                
            extracted_data = await pdf_processor.process_multiple_assessments(uploaded_files)
            logger.info("✅ PDF processing completed successfully")
            
            # Log what was extracted
            for assessment_type, data in extracted_data.items():
                if data:
                    logger.info(f"📋 Extracted data from {assessment_type}: {len(str(data))} characters")
                else:
                    logger.warning(f"⚠️ No data extracted from {assessment_type}")
                    
        except Exception as e:
            logger.error(f"❌ PDF processing failed: {e}")
            extracted_data = {}
        
        # Compile patient information
        patient_info = {
            "name": patient_name,
            "date_of_birth": date_of_birth,
            "encounter_date": encounter_date,
            "chronological_age": chronological_age,
            "parent_guardian": parent_guardian,
            "uci_number": uci_number,
            "sex": sex,
            "language": language,
            "report_date": datetime.now().strftime("%Y-%m-%d")
        }
        logger.info("✅ Patient information compiled")
        
        # Compile comprehensive report data
        report_data = {
            "patient_info": patient_info,
            "extracted_data": extracted_data,
            "assessments": {
                "bayley4": extracted_data.get("bayley4_cognitive", {}) or extracted_data.get("bayley4_social", {}),
                "sp2": extracted_data.get("sp2", {}),
                "chomps": extracted_data.get("chomps", {}),
                "pedieat": extracted_data.get("pedieat", {}),
                "clinical_notes": extracted_data.get("clinical_notes", {})
            }
        }
        logger.info("✅ Report data compiled")
        
        # Generate reports based on output format preference
        output_links = {}
        logger.info(f"📝 Generating reports in {output_format} format...")
        
        if output_format in ["pdf", "both"]:
            logger.info(f"📄 Generating PDF report (type: {report_type})...")
            try:
                if report_type == "professional":
                    if not openai_report_generator:
                        raise Exception("OpenAI report generator not available")
                    pdf_path = await openai_report_generator.generate_comprehensive_report(report_data, session_id)
                    logger.info("✅ Professional AI-enhanced PDF report generated")
                else:
                    if not report_generator:
                        raise Exception("Basic report generator not available")
                    pdf_path = await report_generator.generate_report(report_data, session_id)
                    logger.info("✅ Basic PDF report generated")
                    
                output_links["pdf"] = f"/download/{session_id}"
                logger.info(f"✅ PDF download link created: {output_links['pdf']}")
                
            except Exception as e:
                logger.error(f"❌ PDF generation failed: {e}")
                # Continue processing for other formats
        
        if output_format in ["google_docs", "both"]:
            logger.info("📝 Generating Google Docs report...")
            try:
                if not google_docs_generator:
                    raise Exception("Google Docs generator not available")
                    
                doc_url = await google_docs_generator.create_report(report_data, session_id)
                output_links["google_docs"] = doc_url
                logger.info(f"✅ Google Docs report created: {doc_url}")
                
                # Send email notification
                logger.info("📧 Sending email notification...")
                try:
                    if not email_notifier:
                        raise Exception("Email notifier not available")
                        
                    await email_notifier.send_completion_notification(
                        recipient_email=notify_email,
                        patient_name=patient_name,
                        doc_url=doc_url,
                        session_id=session_id
                    )
                    logger.info(f"✅ Email notification sent to: {notify_email}")
                    
                except Exception as e:
                    logger.error(f"❌ Email notification failed: {e}")
                    # Continue processing
                    
            except Exception as e:
                logger.error(f"❌ Google Docs generation failed: {e}")
                # Continue processing
        
        logger.info(f"🎉 Report generation completed for session {session_id}")
        logger.info(f"📊 Generated outputs: {list(output_links.keys())}")
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "success": True,
            "patient_name": patient_name,
            "chronological_age": chronological_age,
            "output_links": output_links,
            "session_id": session_id,
            "assessments_processed": list(uploaded_files.keys())
        })
        
    except Exception as e:
        logger.error(f"💥 Critical error in session {session_id}: {e}")
        return templates.TemplateResponse("result.html", {
            "request": request,
            "success": False,
            "error": str(e)
        })

@app.get("/download/{session_id}")
async def download_report(session_id: str):
    """Download generated PDF report"""
    logger.info(f"📥 Download request for session: {session_id}")
    
    # Try professional report first, then basic report
    professional_path = os.path.join("outputs", f"professional_ot_report_{session_id}.pdf")
    basic_path = os.path.join("outputs", f"ot_report_{session_id}.pdf")
    
    if os.path.exists(professional_path):
        report_path = professional_path
        filename = f"Professional_OT_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        logger.info(f"✅ Serving professional report: {filename}")
    elif os.path.exists(basic_path):
        report_path = basic_path
        filename = f"Basic_OT_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        logger.info(f"✅ Serving basic report: {filename}")
    else:
        logger.error(f"❌ Report not found for session: {session_id}")
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        file_size = os.path.getsize(report_path) / 1024 / 1024  # MB
        logger.info(f"📁 File size: {file_size:.2f} MB")
        
        return FileResponse(
            path=report_path,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"❌ Failed to serve download: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve file")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("❤️ Health check requested")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "pdf_processor": "ready" if pdf_processor else "unavailable",
            "basic_reports": "ready" if report_generator else "unavailable", 
            "ai_reports": "ready" if openai_report_generator and openai_report_generator.openai_client else "no_api_key" if openai_report_generator else "unavailable",
            "google_docs": "ready" if google_docs_generator and hasattr(google_docs_generator, 'service') and google_docs_generator.service else "no_service_account" if google_docs_generator else "unavailable",
            "email": "ready" if email_notifier else "unavailable"
        }
    }
    
    logger.info(f"📊 Health status: {health_status['components']}")
    return health_status

@app.get("/assessments/types")
async def get_assessment_types():
    """Get available assessment types and their requirements"""
    logger.info("📋 Assessment types requested")
    
    assessment_info = {
        "required": ["facesheet", "bayley4_cognitive", "bayley4_social"],
        "optional": ["sp2", "chomps", "pedieat", "clinical_notes"],
        "descriptions": {
            "facesheet": "Patient demographics and basic information",
            "bayley4_cognitive": "Bayley-4 Cognitive, Language & Motor Scales",
            "bayley4_social": "Bayley-4 Social-Emotional & Adaptive Behavior",
            "sp2": "Sensory Profile 2 Assessment",
            "chomps": "ChOMPS Feeding Assessment",
            "pedieat": "PediEAT Pediatric Eating Assessment Tool",
            "clinical_notes": "Clinical observations and notes"
        }
    }
    
    logger.info("✅ Assessment types information provided")
    return assessment_info

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting server directly...")
    uvicorn.run(app, host="localhost", port=8000) 