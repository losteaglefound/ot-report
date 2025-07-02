import asyncio
from datetime import datetime
import logging
import os
import shutil
from typing import Dict, Any, Optional
from traceback import format_exc
import sys
import uuid
import json

# Load configuration first
from config import config, is_openai_enabled, is_email_enabled, is_google_docs_enabled, get_app_host, get_app_port


sys.stdout.reconfigure(encoding='utf-8')

# Create logs directory if needed
if config.app['log_to_file']:
    os.makedirs('logs', exist_ok=True)

# Configure logging based on config
log_handlers = [logging.StreamHandler()]
if config.app['log_to_file']:
    log_handlers.append(logging.FileHandler('logs/app.log', encoding='utf-8'))

logging.basicConfig(
    level=getattr(logging, config.app['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

# Configure module logger
logger = logging.getLogger(__name__)

# FastAPI imports
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import modules based on configuration
from pdf_processor import EnhancedPDFProcessor

# Conditional imports based on configuration
if is_openai_enabled():
    from openai_report_generator import OpenAIEnhancedReportGenerator
else:
    logger.warning("⚠️ OpenAI not configured - professional reports will use enhanced fallback templates")

if is_google_docs_enabled():
    from google_docs_integration import GoogleDocsReportGenerator
else:
    logger.warning("⚠️ Google Docs not configured - Google Docs integration disabled")

if is_email_enabled():
    from email_notifier import EmailNotifier
else:
    logger.warning("⚠️ Email not configured - email notifications disabled")

from report_generator import OTReportGenerator

# Initialize FastAPI app
app = FastAPI(
    title="Pediatric OT Report Generator",
    description="AI-Enhanced Occupational Therapy Report Generation System",
    version="2.0.0"
)

# Mount static files and templates
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components based on configuration
pdf_processor = None
openai_report_generator = None
google_docs_generator = None
email_notifier = None
report_generator = None

@app.on_event("startup")
async def startup_event():
    """Initialize application components based on configuration"""
    global pdf_processor, openai_report_generator, google_docs_generator, email_notifier, report_generator
    
    logger.info("🚀 Starting Pediatric OT Report Generator...")
    logger.info(f"📊 Configuration Summary: {config.get_configuration_summary()}")
    
    # Always initialize core components
    try:
        logger.info("📄 Initializing PDF processor...")
        pdf_processor = EnhancedPDFProcessor()
        logger.info("✅ PDF processor initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PDF processor: {e}")
    
    try:
        logger.info("📝 Initializing basic report generator...")
        report_generator = OTReportGenerator()
        logger.info("✅ Basic report generator initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize basic report generator: {e}")
    
    # Initialize optional components based on configuration
    if is_openai_enabled():
        try:
            logger.info("🧠 Initializing OpenAI enhanced report generator...")
            openai_report_generator = OpenAIEnhancedReportGenerator()
            logger.info("✅ OpenAI enhanced report generator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI report generator: {e}")
    
    if is_google_docs_enabled():
        try:
            logger.info("📄 Initializing Google Docs integration...")
            google_docs_generator = GoogleDocsReportGenerator()
            logger.info("✅ Google Docs integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Docs integration: {e}")
    
    if is_email_enabled():
        try:
            logger.info("📧 Initializing email notifier...")
            email_notifier = EmailNotifier()
            logger.info("✅ Email notifier initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize email notifier: {e}")
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    
    # Display startup status
    display_startup_status()
    
    logger.info("🎉 Application startup complete!")

def display_startup_status():
    """Display comprehensive startup status dashboard"""
    logger.info("=" * 60)
    logger.info("📊 SYSTEM STATUS DASHBOARD")
    logger.info("=" * 60)
    
    # Core components
    logger.info("🔧 CORE COMPONENTS:")
    logger.info(f"   📄 PDF Processor: {'✅ Ready' if pdf_processor else '❌ Failed'}")
    logger.info(f"   📝 Basic Reports: {'✅ Ready' if report_generator else '❌ Failed'}")
    
    # Enhanced features
    logger.info("🚀 ENHANCED FEATURES:")
    if is_openai_enabled():
        status = "✅ Ready" if openai_report_generator else "❌ Failed to Initialize"
        model = config.openai['model']
        logger.info(f"   🧠 AI Reports: {status} (Model: {model})")
    else:
        logger.info("   🧠 AI Reports: ⚠️ Not Configured (Will use enhanced fallback templates)")
    
    if is_google_docs_enabled():
        status = "✅ Ready" if google_docs_generator else "❌ Failed to Initialize"
        logger.info(f"   📄 Google Docs: {status}")
    else:
        logger.info("   📄 Google Docs: ⚠️ No Service Account")
    
    if is_email_enabled():
        status = "✅ Ready" if email_notifier else "❌ Failed to Initialize"
        provider = config.email['smtp_server']
        logger.info(f"   📧 Email: {status} (Provider: {provider})")
    else:
        logger.info("   📧 Email: ⚠️ No Credentials")
    
    # Configuration info
    logger.info("⚙️ CONFIGURATION:")
    logger.info(f"   🌐 Server: {get_app_host()}:{get_app_port()}")
    logger.info(f"   📊 Default Report Type: {config.app['default_report_type']}")
    logger.info(f"   📁 Default Output: {config.app['default_output_format']}")
    logger.info(f"   🔧 Debug Mode: {'Enabled' if config.app['debug_mode'] else 'Disabled'}")
    
    logger.info("=" * 60)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with configuration-aware interface"""
    feature_status = config.get_feature_status()
    configuration_summary = config.get_configuration_summary()
    notify_email = config.email['default_recipient'] if is_email_enabled() else "fushia.crooms@gmail.com"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "features": feature_status,
        "config": configuration_summary,
        "default_report_type": config.app['default_report_type'],
        "default_output_format": config.app['default_output_format'],
        "notify_email": notify_email
    })

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Feature testing dashboard"""
    return templates.TemplateResponse("test.html", {
        "request": request
    })

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
    # Report preferences with configuration-aware defaults
    output_format: str = Form(default=None),
    report_type: str = Form(default=None),
    notify_email: str = Form(default=None)
):
    """Upload multiple assessment files and generate comprehensive OT report"""
    try:
        # Apply configuration defaults if not provided
        if output_format is None:
            output_format = config.app['default_output_format']
        if report_type is None:
            report_type = config.app['default_report_type']
        if notify_email is None:
            notify_email = config.email['default_recipient'] if is_email_enabled() else "fushia.crooms@gmail.com"
        
        # Validate configuration-dependent requests
        if report_type == "professional" and not is_openai_enabled():
            logger.info(f"⚠️ Professional report requested but OpenAI not configured - using enhanced fallback")
            report_type = "enhanced_basic"  # Use enhanced fallback instead
        
        if output_format == "google_docs" and not is_google_docs_enabled():
            logger.warning(f"⚠️ Google Docs requested but not configured - switching to PDF")
            output_format = "pdf"
        
        session_id = str(uuid.uuid4())
        logger.info(f"🔄 Starting new report generation session: {session_id}")
        logger.info(f"👤 Patient: {patient_name}, Report Type: {report_type}, Output: {output_format}")
        
        # Generate unique session ID
        session_dir = os.path.join("uploads", session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save uploaded files
        uploaded_files = {}
        files_to_process = {
            'facesheet': facesheet_file,
            'bayley4_cognitive': bayley4_cognitive_file,
            'bayley4_social': bayley4_social_file,
            'sp2': sp2_file,
            'chomps': chomps_file,
            'pedieat': pedieat_file,
            'clinical_notes': clinical_notes_file
        }
        
        for file_type, file in files_to_process.items():
            if file:
                file_path = os.path.join(session_dir, f"{file_type}.pdf")
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                uploaded_files[file_type] = file_path
                logger.info(f"📄 Saved {file_type} file: {file_path}")
        
        # Calculate chronological age
        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            encounter = datetime.strptime(encounter_date, "%Y-%m-%d")
            chronological_age = pdf_processor.calculate_chronological_age(dob, encounter)
        except Exception as e:
            logger.error(f"❌ Failed to calculate chronological age: {e}")
            chronological_age = None
        
        # Compile report data
        report_data = {
            "patient_info": {
                "name": patient_name,
                "date_of_birth": date_of_birth,
                "encounter_date": encounter_date,
                "parent_guardian": parent_guardian,
                "uci_number": uci_number,
                "sex": sex,
                "language": language,
                "chronological_age": chronological_age
            },
            "uploaded_files": uploaded_files,
            "report_preferences": {
                "output_format": output_format,
                "report_type": report_type,
                "notify_email": notify_email
            }
        }
        
        # Save report data for potential regeneration
        report_data_path = os.path.join("outputs", f"report_data_{session_id}.json")
        with open(report_data_path, 'w') as f:
            json.dump(report_data, f)
        logger.info("✅ Report data compiled")
        
        # Initialize output links dictionary with error tracking
        output_links = {
            "pdf": None,
            "google_docs": None,
            "error": None,
            "session_id": session_id
        }
        
        # Generate reports based on output format preference
        if output_format in ["pdf", "both"]:
            logger.info(f"📝 Generating PDF report (type: {report_type})...")
            try:
                if report_type == "professional" and is_openai_enabled() and openai_report_generator:
                    # Use AI-enhanced report generation
                    pdf_path = await openai_report_generator.generate_comprehensive_report(report_data, session_id)
                    logger.info("✅ Professional AI-enhanced PDF report generated")
                else:
                    # Use basic report generation
                    pdf_path = await report_generator.generate_report(report_data, session_id)
                    logger.info("✅ Basic PDF report generated")
                
                output_links["pdf"] = f"/download/{session_id}"
                logger.info(f"✅ PDF report created: {pdf_path}")
            except Exception as e:
                error_msg = f"Failed to generate PDF report: {str(e)}"
                logger.error(f"❌ {error_msg}")
                output_links["error"] = error_msg
                output_links["pdf"] = None
        
        if output_format in ["google_docs", "both"]:
            logger.info(f"📝 Generating Google Docs report (type: {report_type})...")
            try:
                if not is_google_docs_enabled() or not google_docs_generator:
                    raise Exception("Google Docs generator not available")
                
                if report_type == "professional" and is_openai_enabled() and openai_report_generator:
                    doc_url = await openai_report_generator.generate_google_docs_report(report_data, session_id)
                    logger.info("✅ Professional AI-enhanced Google Docs report generated")
                else:
                    doc_url = await google_docs_generator.create_report(report_data, session_id)
                    logger.info("✅ Basic Google Docs report generated")
                
                output_links["google_docs"] = doc_url
                logger.info(f"✅ Google Docs report created: {doc_url}")
            except Exception as e:
                error_msg = f"Failed to generate Google Docs report: {str(e)}"
                logger.error(f"❌ {error_msg}")
                if not output_links["error"]:
                    output_links["error"] = error_msg
        
        # Return template response with output links and status
        return templates.TemplateResponse("result.html", {
            "request": request,
            "success": not output_links["error"],
            "error": output_links["error"],
            "patient_name": patient_name,
            "chronological_age": chronological_age,
            "output_links": output_links,
            "session_id": session_id,
            "assessments_processed": list(uploaded_files.keys()),
            "features": config.get_feature_status(),
            "notify_email": notify_email
        })
        
    except Exception as e:
        error_msg = f"Failed to process report generation: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return templates.TemplateResponse("result.html", {
            "request": request,
            "success": False,
            "error": error_msg,
            "session_id": session_id if 'session_id' in locals() else None,
            "features": config.get_feature_status()
        })

@app.get("/download/{session_id}")
async def download_report(session_id: str):
    """Download generated report"""
    logger.info(f"📥 Download request for session: {session_id}")
    
    # Look for PDF files in outputs directory
    outputs_dir = "outputs"
    potential_files = [
        f"professional_ot_report_{session_id}.pdf",
        f"ot_evaluation_report_{session_id}.pdf",
        f"Professional_OT_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    ]
    
    for filename in potential_files:
        file_path = os.path.join(outputs_dir, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
            logger.info(f"✅ Serving report: {filename}")
            logger.info(f"📁 File size: {file_size:.2f} MB")
            
            return FileResponse(
                path=file_path,
                filename=f"OT_Evaluation_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                media_type="application/pdf"
            )
    
    # If no specific file found, return the most recent PDF
    try:
        pdf_files = [f for f in os.listdir(outputs_dir) if f.endswith('.pdf')]
        if pdf_files:
            latest_file = max(pdf_files, key=lambda f: os.path.getctime(os.path.join(outputs_dir, f)))
            file_path = os.path.join(outputs_dir, latest_file)
            
            logger.info(f"✅ Serving latest report: {latest_file}")
            return FileResponse(
                path=file_path,
                filename=f"OT_Evaluation_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                media_type="application/pdf"
            )
    except Exception as e:
        logger.error(f"❌ Error finding report file: {e}")
    
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/health")
async def health_check():
    """Health check endpoint with configuration status"""
    feature_status = config.get_feature_status()
    configuration_summary = config.get_configuration_summary()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": feature_status,
        "configuration": configuration_summary,
        "components": {
            "pdf_processor": pdf_processor is not None,
            "openai_generator": openai_report_generator is not None,
            "google_docs_generator": google_docs_generator is not None,
            "email_notifier": email_notifier is not None,
            "basic_report_generator": report_generator is not None
        }
    }

@app.post("/test/google-docs")
async def test_google_docs():
    """Test Google Docs integration by creating a simple test document"""
    logger.info("🧪 Testing Google Docs integration...")
    
    if not is_google_docs_enabled():
        logger.warning("⚠️ Google Docs not configured")
        return {
            "success": False,
            "error": "Google Docs integration not configured",
            "message": "Add service_account.json file to enable Google Docs integration",
            "troubleshooting": {
                "service_account_setup": [
                    "1. Go to Google Cloud Console (https://console.cloud.google.com/)",
                    "2. Create or select a project",
                    "3. Enable Google Docs API and Google Drive API",
                    "4. Create a Service Account (IAM & Admin > Service Accounts)",
                    "5. Download the JSON key file and rename it to 'service_account.json'",
                    "6. Place the file in your project root directory"
                ],
                "expected_file_location": "service_account.json (in project root)",
                "environment_variable": "GOOGLE_SERVICE_ACCOUNT_FILE (optional)"
            }
        }
    
    if not google_docs_generator:
        logger.error("❌ Google Docs generator not initialized")
        
        # Try to get more detailed error information
        service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
        troubleshooting = {
            "service_account_file": service_account_path,
            "file_exists": os.path.exists(service_account_path),
        }
        
        # If file exists, try to validate it
        if os.path.exists(service_account_path):
            try:
                # Import GoogleDocsReportGenerator locally to access validation method
                from google_docs_integration import GoogleDocsReportGenerator
                temp_generator = GoogleDocsReportGenerator()
                if hasattr(temp_generator, '_validate_credentials_file'):
                    validation_result = temp_generator._validate_credentials_file(service_account_path)
                    troubleshooting.update({
                        "file_validation": validation_result,
                        "detailed_error": validation_result.get('error', 'Unknown validation error')
                    })
                    
                    if not validation_result.get('valid', False):
                        cred_type = validation_result.get('type', 'unknown')
                        if cred_type == 'oauth_client':
                            troubleshooting["fix_suggestions"] = [
                                "Your file appears to be OAuth2 client credentials (correct format!)",
                                "Ensure you have enabled Google Docs API and Google Drive API in Google Cloud Console",
                                "The system will open a browser window for authorization when you first use Google Docs",
                                "Make sure you can access a web browser for the OAuth flow"
                            ]
                        elif cred_type == 'service_account':
                            troubleshooting["fix_suggestions"] = [
                                "Download a fresh service account JSON from Google Cloud Console",
                                "Ensure the file is a complete Google service account key (not truncated)",
                                "Verify the file contains all required fields: type, project_id, private_key, client_email, etc.",
                                "Make sure you downloaded the JSON format (not P12 or other formats)"
                            ]
                        else:
                            troubleshooting["fix_suggestions"] = [
                                "Ensure you have a valid Google Cloud credentials file",
                                "File should be either OAuth2 client credentials (client_secret_*.json) or service account credentials",
                                "Download from Google Cloud Console > APIs & Services > Credentials",
                                "Verify the JSON file is complete and not corrupted"
                            ]
                else:
                    troubleshooting["validation_error"] = "Unable to access validation method"
                    
            except Exception as validation_error:
                troubleshooting["validation_error"] = str(validation_error)
        else:
            troubleshooting["missing_file_help"] = [
                "Create a service account in Google Cloud Console",
                "Download the JSON key file",
                "Save it as 'service_account.json' in the project root",
                "Or set GOOGLE_SERVICE_ACCOUNT_FILE environment variable to the file path"
            ]
        
        return {
            "success": False,
            "error": "Google Docs generator not available",
            "message": "Google Docs generator failed to initialize. Check service account configuration.",
            "troubleshooting": troubleshooting
        }
    
    try:
        # Create test document data
        test_data = {
            "patient_info": {
                "name": "Test Patient",
                "date_of_birth": "2022-01-01",
                "chronological_age": {"formatted": "2 years, 11 months, 27 days"},
                "parent_guardian": "Test Parent",
                "uci_number": "TEST123",
                "sex": "Test",
                "language": "English",
                "encounter_date": "2025-06-28",
                "report_date": datetime.now().strftime("%Y-%m-%d")
            },
            "extracted_data": {
                "bayley4_cognitive": {
                    "raw_scores": {"Cognitive": 10, "Fine Motor": 8},
                    "scaled_scores": {"Cognitive": 7, "Fine Motor": 6},
                    "interpretations": {"test": "This is a test document"}
                }
            },
            "assessments": {}
        }
        
        logger.info("📝 Creating test Google Docs report...")
        doc_url = await google_docs_generator.create_report(test_data, "test-session")
        
        logger.info(f"✅ Test Google Docs report created successfully: {doc_url}")
        
        return {
            "success": True,
            "message": "Google Docs integration test successful",
            "document_url": doc_url,
            "instructions": "You can view the test document at the provided URL",
            "service_account_info": {
                "project_id": getattr(google_docs_generator, 'project_id', 'Unknown'),
                "client_email": getattr(google_docs_generator, 'client_email', 'Unknown')
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Google Docs test failed: {e}")
        
        # Provide specific troubleshooting based on the error
        troubleshooting = {
            "error_details": str(e),
            "common_solutions": [
                "Verify the service account has Google Docs and Drive API access",
                "Check that the service account JSON file is valid and complete",
                "Ensure the service account has proper permissions",
                "Verify your Google Cloud project has the APIs enabled"
            ]
        }
        
        # Add specific error-based suggestions
        error_str = str(e).lower()
        if "authentication" in error_str or "credentials" in error_str:
            troubleshooting["auth_issue"] = "Authentication failed"
            troubleshooting["auth_solutions"] = [
                "Regenerate the service account key",
                "Verify the service account is not disabled",
                "Check the service account has the correct roles",
                "Ensure the JSON file is not corrupted"
            ]
        elif "permission" in error_str or "403" in error_str:
            troubleshooting["permission_issue"] = "Permission denied"
            troubleshooting["permission_solutions"] = [
                "Enable Google Docs API in Google Cloud Console",
                "Enable Google Drive API in Google Cloud Console", 
                "Add Editor role to the service account",
                "Check API quotas and billing"
            ]
        elif "api" in error_str or "service" in error_str:
            troubleshooting["api_issue"] = "API service error"
            troubleshooting["api_solutions"] = [
                "Check if Google APIs are enabled in your project",
                "Verify network connectivity",
                "Check Google Cloud service status",
                "Review API quotas and usage limits"
            ]
        
        return {
            "success": False,
            "error": str(e),
            "message": "Google Docs integration test failed. Check service account configuration and API permissions.",
            "troubleshooting": troubleshooting
        }

@app.post("/test/email")
async def test_email(
    recipient_email: str = Form(default=None),
    test_message: str = Form(default="This is a test email from the OT Report Generator system."),
    smtp_port: int = Form(default=None)
):
    """Test email functionality by sending a test email"""
    logger.info("📧 Testing email functionality...")
    
    if not is_email_enabled():
        logger.warning("⚠️ Email not configured")
        return {
            "success": False,
            "error": "Email integration not configured",
            "message": "Add EMAIL_ADDRESS and EMAIL_PASSWORD to .env file to enable email notifications",
            "smtp_troubleshooting": {
                "gmail_ports": {
                    "587": "STARTTLS (recommended) - starts plain text, upgrades to encrypted",
                    "465": "SSL/TLS - encrypted from start"
                },
                "setup_instructions": [
                    "1. Enable 2-factor authentication on your Gmail account",
                    "2. Generate an App Password: https://myaccount.google.com/apppasswords",
                    "3. Use the 16-character app password (not your regular Gmail password)"
                ]
            }
        }
    
    if not email_notifier:
        logger.error("❌ Email notifier not initialized")
        return {
            "success": False,
            "error": "Email notifier not available",
            "message": "Email notifier failed to initialize"
        }
    
    # Use provided recipient or default from config
    if not recipient_email:
        recipient_email = config.email['default_recipient']
    
    # Use provided SMTP port or default from config
    original_smtp_port = email_notifier.smtp_port
    if smtp_port:
        logger.info(f"🔧 Testing with custom SMTP port: {smtp_port}")
        email_notifier.smtp_port = smtp_port
    
    try:
        logger.info(f"📧 Sending test email to: {recipient_email}")
        logger.info(f"🔗 Using SMTP: {email_notifier.smtp_server}:{email_notifier.smtp_port}")
        
        # Send test email using the email notifier
        await email_notifier.send_test_email(
            recipient_email=recipient_email,
            test_message=test_message
        )
        
        logger.info(f"✅ Test email sent successfully to: {recipient_email}")
        
        return {
            "success": True,
            "message": f"Test email sent successfully to {recipient_email}",
            "recipient": recipient_email,
            "smtp_server": f"{email_notifier.smtp_server}:{email_notifier.smtp_port}",
            "port_used": email_notifier.smtp_port,
            "instructions": "Check the recipient's inbox (including spam folder) for the test email",
            "smtp_info": {
                "port_587": "STARTTLS - starts plain text, upgrades to encrypted",
                "port_465": "SSL/TLS - encrypted from start",
                "current_port": email_notifier.smtp_port
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Email test failed: {e}")
        
        # Provide specific troubleshooting based on the error
        troubleshooting = {
            "gmail_app_password": "Make sure you're using a Gmail App Password, not your regular password",
            "2fa_required": "2-factor authentication must be enabled on your Gmail account",
            "smtp_settings": f"Current: {email_notifier.smtp_server}:{email_notifier.smtp_port}",
            "port_options": {
                "587": "Try STARTTLS (most common for Gmail)",
                "465": "Try SSL/TLS if port 587 fails"
            }
        }
        
        # Add specific error-based suggestions
        error_str = str(e).lower()
        if "ssl" in error_str or "tls" in error_str:
            troubleshooting["ssl_issue"] = "SSL/TLS configuration issue detected"
            troubleshooting["solutions"] = [
                f"Try testing with port {'465' if email_notifier.smtp_port == 587 else '587'}",
                "Verify your email provider's SMTP settings",
                "Check if your network blocks SMTP ports"
            ]
        elif "authentication" in error_str:
            troubleshooting["auth_issue"] = "Authentication failed"
            troubleshooting["solutions"] = [
                "Verify your App Password is correct (16 characters)",
                "Ensure 2-factor authentication is enabled",
                "Try generating a new App Password"
            ]
        elif "connection" in error_str:
            troubleshooting["connection_issue"] = "Connection failed"
            troubleshooting["solutions"] = [
                "Check your internet connection",
                "Verify SMTP server and port",
                "Check if firewall blocks SMTP ports"
            ]
        
        return {
            "success": False,
            "error": str(e),
            "message": "Email test failed. Check email credentials and SMTP configuration.",
            "troubleshooting": troubleshooting,
            "test_suggestions": [
                f"Try testing with port 465: curl -X POST 'http://localhost:8000/test/email' -F 'smtp_port=465'",
                f"Try testing with port 587: curl -X POST 'http://localhost:8000/test/email' -F 'smtp_port=587'"
            ]
        }
    finally:
        # Restore original SMTP port
        email_notifier.smtp_port = original_smtp_port

@app.get("/test/openai")
async def test_openai():
    """Test OpenAI integration by generating a simple test response"""
    logger.info("🧠 Testing OpenAI integration...")
    
    if not is_openai_enabled():
        logger.warning("⚠️ OpenAI not configured")
        return {
            "success": False,
            "error": "OpenAI integration not configured",
            "message": "Add OPENAI_API_KEY to .env file to enable AI-enhanced reports"
        }
    
    if not openai_report_generator:
        logger.error("❌ OpenAI report generator not initialized")
        return {
            "success": False,
            "error": "OpenAI report generator not available", 
            "message": "OpenAI report generator failed to initialize"
        }
    
    try:
        logger.info("🤖 Testing OpenAI API connection...")
        
        # Test with a simple prompt
        test_prompt = "Write a brief professional summary for a pediatric occupational therapy evaluation. Keep it to 2-3 sentences."
        
        test_response = await openai_report_generator._generate_with_openai(test_prompt, max_tokens=150)
        
        logger.info(f"✅ OpenAI test successful - Generated {len(test_response)} characters")
        
        return {
            "success": True,
            "message": "OpenAI integration test successful",
            "model": config.openai['model'],
            "generated_text": test_response,
            "character_count": len(test_response),
            "instructions": "OpenAI is working correctly and can generate clinical content"
        }
        
    except Exception as e:
        logger.error(f"❌ OpenAI test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "OpenAI integration test failed. Check API key and model availability.",
            "troubleshooting": {
                "api_key_valid": "Verify your OpenAI API key is valid and has sufficient credits",
                "model_available": f"Check if model '{config.openai['model']}' is available",
                "rate_limits": "You may have hit rate limits - try again in a few minutes"
            }
        }

@app.get("/config")
async def get_configuration():
    """Get current configuration status"""
    return {
        "configuration": config.get_configuration_summary(),
        "features": config.get_feature_status(),
        "env_status": {
            "openai_configured": is_openai_enabled(),
            "email_configured": is_email_enabled(),
            "google_docs_configured": is_google_docs_enabled()
        }
    }

@app.get("/assessments/types")
async def get_assessment_types():
    """Get supported assessment types"""
    return {
        "supported_assessments": [
            {"type": "facesheet", "name": "Patient Facesheet", "required": False},
            {"type": "bayley4_cognitive", "name": "Bayley-4 Cognitive/Language/Motor", "required": True},
            {"type": "bayley4_social", "name": "Bayley-4 Social-Emotional/Adaptive", "required": True},
            {"type": "sp2", "name": "Sensory Profile 2", "required": False},
            {"type": "chomps", "name": "ChOMPS", "required": False},
            {"type": "pedieat", "name": "PediEAT", "required": False},
            {"type": "clinical_notes", "name": "Clinical Notes", "required": False}
        ]
    }

@app.post("/regenerate-report/{session_id}")
async def regenerate_report(session_id: str, output_format: str = "pdf"):
    """Regenerate report for a given session"""
    try:
        # Load saved report data
        report_data_path = os.path.join("outputs", f"report_data_{session_id}.json")
        if not os.path.exists(report_data_path):
            raise HTTPException(status_code=404, detail="Report data not found")
            
        with open(report_data_path, 'r') as f:
            report_data = json.load(f)
            
        output_links = {
            "pdf": None,
            "google_docs": None,
            "error": None,
            "session_id": session_id
        }
        
        # Regenerate PDF
        if output_format in ["pdf", "both"]:
            try:
                if is_openai_enabled() and openai_report_generator:
                    pdf_path = await openai_report_generator.generate_comprehensive_report(report_data, session_id)
                    logger.info("✅ Professional AI-enhanced PDF report regenerated")
                else:
                    pdf_path = await report_generator.generate_report(report_data, session_id)
                    logger.info("✅ Basic PDF report regenerated")
                    
                output_links["pdf"] = f"/download/{session_id}"
                logger.info(f"✅ PDF report regenerated: {pdf_path}")
            except Exception as e:
                error_msg = f"Failed to regenerate PDF report: {str(e)}"
                logger.error(f"❌ {error_msg}")
                output_links["error"] = error_msg
                
        # Regenerate Google Docs if requested
        if output_format in ["google_docs", "both"]:
            try:
                if not is_google_docs_enabled() or not google_docs_generator:
                    raise Exception("Google Docs generator not available")
                    
                if is_openai_enabled() and openai_report_generator:
                    doc_url = await openai_report_generator.generate_google_docs_report(report_data, session_id)
                    logger.info("✅ Professional AI-enhanced Google Docs report regenerated")
                else:
                    doc_url = await google_docs_generator.create_report(report_data, session_id)
                    logger.info("✅ Basic Google Docs report regenerated")
                    
                output_links["google_docs"] = doc_url
                logger.info(f"✅ Google Docs report regenerated: {doc_url}")
            except Exception as e:
                error_msg = f"Failed to regenerate Google Docs report: {str(e)}"
                logger.error(f"❌ {error_msg}")
                if not output_links["error"]:
                    output_links["error"] = error_msg
                    
        return output_links
        
    except Exception as e:
        error_msg = f"Failed to regenerate report: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    
    # Use configuration for server settings
    uvicorn.run(
        "main:app",
        host=get_app_host(),
        port=get_app_port(),
        reload=config.app['debug_mode'],
        log_level=config.app['log_level'].lower()
    ) 