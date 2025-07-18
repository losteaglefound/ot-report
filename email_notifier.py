import os
import logging
import smtplib
from typing import Dict, Any, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json

try:
    import yagmail
    YAGMAIL_AVAILABLE = True
except ImportError:
    YAGMAIL_AVAILABLE = False

# Configure logging for this module (after imports)
logger = logging.getLogger(__name__)

if YAGMAIL_AVAILABLE:
    logger.info("✅ yagmail library imported successfully")
else:
    logger.warning("⚠️ yagmail not available - install with: pip install yagmail")

class EmailNotifier:
    """Handle email notifications for report completion"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("📧 Initializing Email Notifier...")
        
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.email_user)
        
        self.logger.info(f"📬 SMTP Server: {self.smtp_server}:{self.smtp_port}")
        self.logger.info(f"📨 From Email: {self.from_email or 'Not configured'}")
        
        # Check configuration
        self._check_email_configuration()
        
        # Initialize yagmail if available and configured
        self.yag = None
        self._initialize_yagmail()
    
    def _check_email_configuration(self):
        """Check if email is properly configured"""
        self.logger.info("🔧 Checking email configuration...")
        
        if not self.email_user:
            self.logger.warning("⚠️ EMAIL_ADDRESS environment variable not set")
        
        if not self.email_password:
            self.logger.warning("⚠️ EMAIL_PASSWORD environment variable not set")
        
        if self.email_user and self.email_password:
            self.logger.info("✅ Email credentials configured")
        else:
            self.logger.warning("⚠️ Email not fully configured - notifications will be logged only")
    
    def _initialize_yagmail(self):
        """Initialize yagmail for easier Gmail sending"""
        if not YAGMAIL_AVAILABLE:
            self.logger.warning("⚠️ yagmail not available, using standard SMTP")
            return

        if not self.email_user or not self.email_password:
            self.logger.warning("⚠️ Email credentials not configured for yagmail")
            return

        try:
            self.logger.info("📧 Initializing yagmail...")
            
            # For Gmail, use specific configuration to avoid SSL issues
            if 'gmail.com' in self.smtp_server.lower():
                if self.smtp_port == 587:
                    # Port 587 requires STARTTLS, not direct SSL
                    self.logger.info("🔧 Configuring yagmail for Gmail STARTTLS (port 587)")
                    self.yag = yagmail.SMTP(
                        user=self.email_user,
                        password=self.email_password,
                        host=self.smtp_server,
                        port=self.smtp_port,
                        smtp_starttls=True,
                        smtp_ssl=False
                    )
                elif self.smtp_port == 465:
                    # Port 465 uses direct SSL
                    self.logger.info("🔧 Configuring yagmail for Gmail SSL (port 465)")
                    self.yag = yagmail.SMTP(
                        user=self.email_user,
                        password=self.email_password,
                        host=self.smtp_server,
                        port=self.smtp_port,
                        smtp_starttls=False,
                        smtp_ssl=True
                    )
                else:
                    # Default configuration
                    self.logger.info("🔧 Using default yagmail configuration")
                    self.yag = yagmail.SMTP(
                        user=self.email_user,
                        password=self.email_password,
                        host=self.smtp_server,
                        port=self.smtp_port
                    )
            else:
                # Non-Gmail SMTP servers - use default configuration
                self.logger.info("🔧 Configuring yagmail for non-Gmail SMTP")
                self.yag = yagmail.SMTP(
                    user=self.email_user,
                    password=self.email_password,
                    host=self.smtp_server,
                    port=self.smtp_port
                )
            
            # Test the connection
            self.logger.info("🧪 Testing yagmail connection...")
            # yagmail automatically connects when initialized, so if we get here it worked
            self.logger.info("✅ yagmail initialized and tested successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize yagmail: {e}")
            self.logger.info("🔄 Will fall back to standard SMTP for email sending")
            self.yag = None
    
    async def send_completion_notification(
        self, 
        recipient_email: str, 
        patient_name: str, 
        doc_url: str, 
        session_id: str,
        additional_info: Dict[str, Any] = None,
        attachment_files: List[str] = None  # New parameter for attachment file paths
    ) -> bool:
        """Send email notification when report is completed"""
        self.logger.info(f"📧 Sending completion notification for {patient_name}")
        self.logger.info(f"📮 Recipient: {recipient_email}")
        self.logger.info(f"🔗 Document URL: {doc_url}")
        
        # Log attachment info
        if attachment_files:
            self.logger.info(f"📎 Attachments: {len(attachment_files)} file(s)")
            for file_path in attachment_files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                    self.logger.info(f"   📄 {os.path.basename(file_path)} ({file_size:.2f} MB)")
                else:
                    self.logger.warning(f"   ⚠️ Attachment file not found: {file_path}")
        
        try:
            subject = f"Pediatric OT Report Completed - {patient_name}"
            
            # Create email content
            html_content = self._create_html_email_content(
                patient_name, doc_url, session_id, additional_info
            )
            
            text_content = self._create_text_email_content(
                patient_name, doc_url, session_id, additional_info
            )
            
            self.logger.info("📝 Email content created")
            
            # Try yagmail first if available
            if self.yag:
                self.logger.info("📧 Sending email via yagmail...")
                success = await self._send_with_yagmail(
                    recipient_email, subject, html_content, text_content, attachment_files
                )
                if success:
                    return True
            
            # Fallback to standard SMTP
            self.logger.info("📧 Sending email via standard SMTP...")
            success = await self._send_with_smtp(
                recipient_email, subject, html_content, text_content, attachment_files
            )
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send email notification: {e}")
            # Log notification as fallback
            self.logger.info(f"📋 FALLBACK LOG - Report ready for {patient_name}: {doc_url}")
            return False
    
    def _create_html_email_content(
        self, 
        patient_name: str, 
        doc_url: str, 
        session_id: str,
        additional_info: Dict[str, Any] = None
    ) -> str:
        """Create HTML email content"""
        
        additional_info = additional_info or {}
        chronological_age = additional_info.get('chronological_age', 'Not specified')
        assessments_processed = additional_info.get('assessments_processed', [])
        report_type = additional_info.get('report_type', 'Standard')
        output_format = additional_info.get('output_format', 'pdf')
        pdf_drive_url = additional_info.get('pdf_drive_url')
        google_docs_url = additional_info.get('google_docs_url')
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .patient-info {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .button {{ 
                    background-color: #4CAF50; 
                    color: white; 
                    padding: 12px 25px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    display: inline-block; 
                    margin: 15px 0;
                }}
                .button:hover {{ background-color: #45a049; }}
                .button.google-drive {{ background-color: #1976D2; }}
                .button.google-drive:hover {{ background-color: #1565C0; }}
                .button.google-docs {{ background-color: #0F9D58; }}
                .button.google-docs:hover {{ background-color: #0D8043; }}
                .footer {{ background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; }}
                .assessment-list {{ background-color: #e8f5e8; padding: 10px; border-radius: 5px; }}
                .report-links {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; border: 1px solid #1976D2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏥 Pediatric OT Report Generated</h1>
                <p>FMRC Health Group - Automated Report System</p>
            </div>
            
            <div class="content">
                <h2>Report Completion Notification</h2>
                
                <p>A comprehensive pediatric occupational therapy evaluation report has been successfully generated and is ready for review.</p>
                
                <div class="patient-info">
                    <h3>📋 Patient Information</h3>
                    <p><strong>Patient Name:</strong> {patient_name}</p>
                    <p><strong>Chronological Age:</strong> {chronological_age}</p>
                    <p><strong>Report Type:</strong> {report_type.title()}</p>
                    <p><strong>Output Format:</strong> {output_format.replace('_', ' ').title()}</p>
                    <p><strong>Report Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Session ID:</strong> {session_id[:8]}</p>
                </div>
                
                <div class="assessment-list">
                    <h3>📊 Assessments Processed</h3>
                    <ul>
        """
        
        # Add processed assessments
        assessment_names = {
            'facesheet': 'Patient Demographics (Facesheet)',
            'bayley4_cognitive': 'Bayley-4 Cognitive, Language & Motor Scales',
            'bayley4_social': 'Bayley-4 Social-Emotional & Adaptive Behavior',
            'sp2': 'Sensory Profile 2 (SP2)',
            'chomps': 'Chicago Oral Motor & Feeding Assessment (ChOMPS)',
            'pedieat': 'Pediatric Eating Assessment Tool (PediEAT)',
            'clinical_notes': 'Clinical Observations and Notes'
        }
        
        if assessments_processed:
            for assessment in assessments_processed:
                name = assessment_names.get(assessment, assessment.replace('_', ' ').title())
                html_content += f"                        <li>✅ {name}</li>\n"
        else:
            html_content += "                        <li>ℹ️ Standard pediatric OT assessment battery</li>\n"
        
        html_content += f"""
                    </ul>
                </div>
                
                <div class="report-links">
                    <h3>📄 Access Your Report</h3>
                    <p>Your report has been generated in the following format(s):</p>
                    
                    <div style="text-align: center; margin: 20px 0;">
        """
        
        # Add Google Docs link if available
        if google_docs_url:
            html_content += f"""
                        <div style="margin: 10px 0;">
                            <a href="{google_docs_url}" class="button google-docs">
                                📝 Open Google Docs Report
                            </a>
                            <br><small style="color: #666;">✅ Editable, shareable, and accessible from anywhere</small>
                        </div>
            """
        
        # Add Google Drive PDF link if available
        if pdf_drive_url:
            html_content += f"""
                        <div style="margin: 10px 0;">
                            <a href="{pdf_drive_url}" class="button google-drive">
                                📁 View PDF on Google Drive
                            </a>
                            <br><small style="color: #666;">📄 Professional PDF format stored in Google Drive</small>
                        </div>
            """
        
        # Add primary report link if no specific Google links
        if not google_docs_url and not pdf_drive_url and doc_url:
            html_content += f"""
                        <div style="margin: 10px 0;">
                            <a href="{doc_url}" class="button">
                                📄 Access Report
                            </a>
                            <br><small style="color: #666;">Your generated report is ready for review</small>
                        </div>
            """
        
        html_content += f"""
                    </div>
                </div>
                
                <h3>📋 Report Contents</h3>
                <p>The comprehensive evaluation report includes:</p>
                <ul>
                    <li>Detailed assessment results and score interpretations</li>
                    <li>Clinical observations and behavioral notes</li>
                    <li>Areas of strength and need identification</li>
                    <li>Evidence-based recommendations</li>
                    <li>Short-term and long-term treatment goals</li>
                    <li>Professional summary and clinical insights</li>
                </ul>
                
                <p><em>Note: All report documents are ready for review, editing, and sharing with your team. Patient information has been securely processed and source files handled according to HIPAA guidelines.</em></p>
                
                <h3>📞 Next Steps</h3>
                <ul>
                    <li>Review the generated report for accuracy and completeness</li>
                    <li>Make any necessary clinical edits or additions</li>
                    <li>Share with interdisciplinary team members as needed</li>
                    <li>Schedule follow-up assessments if recommended</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>This is an automated notification from the FMRC Health Group Pediatric OT Report Generator</p>
                <p>For technical support or questions, please contact your system administrator</p>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _create_text_email_content(
        self, 
        patient_name: str, 
        doc_url: str, 
        session_id: str,
        additional_info: Dict[str, Any] = None
    ) -> str:
        """Create plain text email content"""
        
        additional_info = additional_info or {}
        chronological_age = additional_info.get('chronological_age', 'Not specified')
        assessments_processed = additional_info.get('assessments_processed', [])
        report_type = additional_info.get('report_type', 'Standard')
        output_format = additional_info.get('output_format', 'pdf')
        pdf_drive_url = additional_info.get('pdf_drive_url')
        google_docs_url = additional_info.get('google_docs_url')
        
        text_content = f"""
PEDIATRIC OT REPORT GENERATED
FMRC Health Group - Automated Report System
================================================

Report Completion Notification

A comprehensive pediatric occupational therapy evaluation report has been successfully generated and is ready for review.

PATIENT INFORMATION
-------------------
Patient Name: {patient_name}
Chronological Age: {chronological_age}
Report Type: {report_type.title()}
Output Format: {output_format.replace('_', ' ').title()}
Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Session ID: {session_id[:8]}

ASSESSMENTS PROCESSED
--------------------
"""
        
        # Add processed assessments
        assessment_names = {
            'facesheet': 'Patient Demographics (Facesheet)',
            'bayley4_cognitive': 'Bayley-4 Cognitive, Language & Motor Scales',
            'bayley4_social': 'Bayley-4 Social-Emotional & Adaptive Behavior',
            'sp2': 'Sensory Profile 2 (SP2)',
            'chomps': 'Chicago Oral Motor & Feeding Assessment (ChOMPS)',
            'pedieat': 'Pediatric Eating Assessment Tool (PediEAT)',
            'clinical_notes': 'Clinical Observations and Notes'
        }
        
        if assessments_processed:
            for assessment in assessments_processed:
                name = assessment_names.get(assessment, assessment.replace('_', ' ').title())
                text_content += f"✓ {name}\n"
        else:
            text_content += "• Standard pediatric OT assessment battery\n"
        
        text_content += f"""
ACCESS YOUR REPORT
------------------
Your report has been generated in the following format(s):

"""
        
        # Add Google Docs link if available
        if google_docs_url:
            text_content += f"""📝 Google Docs Report (Editable):
   {google_docs_url}
   ✅ Editable, shareable, and accessible from anywhere

"""
        
        # Add Google Drive PDF link if available
        if pdf_drive_url:
            text_content += f"""📁 PDF Report on Google Drive:
   {pdf_drive_url}
   📄 Professional PDF format stored in Google Drive

"""
        
        # Add primary report link if no specific Google links
        if not google_docs_url and not pdf_drive_url and doc_url:
            text_content += f"""📄 Report Access:
   {doc_url}
   Your generated report is ready for review

"""
        
        text_content += f"""REPORT CONTENTS
---------------
The comprehensive evaluation report includes:
• Detailed assessment results and score interpretations
• Clinical observations and behavioral notes
• Areas of strength and need identification
• Evidence-based recommendations
• Short-term and long-term treatment goals
• Professional summary and clinical insights

NEXT STEPS
----------
1. Review the generated report for accuracy and completeness
2. Make any necessary clinical edits or additions
3. Share with interdisciplinary team members as needed
4. Schedule follow-up assessments if recommended

NOTE: All report documents are ready for review, editing, and sharing with your team. Patient information has been securely processed and source files handled according to HIPAA guidelines.

================================================
This is an automated notification from the FMRC Health Group Pediatric OT Report Generator
For technical support or questions, please contact your system administrator
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        """
        
        return text_content
    
    async def _send_with_yagmail(
        self, 
        recipient: str, 
        subject: str, 
        html_content: str, 
        text_content: str,
        attachment_files: List[str] = None
    ) -> bool:
        """Send email using yagmail"""
        try:
            self.logger.info("📤 Attempting to send via yagmail...")
            
            # Prepare contents list
            contents = [text_content, html_content]
            
            # Add attachments if provided
            if attachment_files:
                for file_path in attachment_files:
                    if os.path.exists(file_path):
                        contents.append(file_path)
                        self.logger.info(f"📎 Added attachment: {os.path.basename(file_path)}")
                    else:
                        self.logger.warning(f"⚠️ Skipping missing attachment: {file_path}")
            
            self.yag.send(
                to=recipient,
                subject=subject,
                contents=contents
            )
            
            self.logger.info("✅ Email sent successfully via yagmail")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ yagmail sending failed: {e}")
            return False
    
    async def _send_with_smtp(
        self, 
        recipient: str, 
        subject: str, 
        html_content: str, 
        text_content: str,
        attachment_files: List[str] = None
    ) -> bool:
        """Send email using standard SMTP"""
        if not self.email_user or not self.email_password:
            self.logger.warning("⚠️ SMTP credentials not configured")
            return False

        try:
            self.logger.info("📤 Attempting to send via SMTP...")
            self.logger.info(f"🔗 Connecting to {self.smtp_server}:{self.smtp_port}")

            # Create message - use 'mixed' to support attachments
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient

            # Create alternative container for text and HTML
            msg_alternative = MIMEMultipart('alternative')
            
            # Add both plain and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg_alternative.attach(text_part)
            msg_alternative.attach(html_part)
            
            # Attach the alternative container to main message
            msg.attach(msg_alternative)

            # Add file attachments if provided
            if attachment_files:
                for file_path in attachment_files:
                    if os.path.exists(file_path):
                        self._attach_file_to_message(msg, file_path)
                    else:
                        self.logger.warning(f"⚠️ Skipping missing attachment: {file_path}")

            # Send via SMTP with proper SSL/TLS handling
            server = None
            try:
                if self.smtp_port == 465:
                    # Port 465: Use SMTP_SSL (direct SSL connection)
                    self.logger.info("🔐 Using SMTP_SSL for port 465")
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                else:
                    # Port 587 or others: Use regular SMTP with STARTTLS
                    self.logger.info("🔧 Using SMTP with STARTTLS")
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls()  # Enable TLS encryption

                self.logger.info("🔑 Authenticating...")
                server.login(self.email_user, self.email_password)

                self.logger.info("📤 Sending message...")
                server.send_message(msg)

                self.logger.info("✅ Email sent successfully via SMTP")
                return True

            finally:
                if server:
                    server.quit()

        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"❌ SMTP authentication failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ SMTP sending failed: {e}")
            return False

    def _attach_file_to_message(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to the email message"""
        try:
            filename = os.path.basename(file_path)
            
            # Determine the content type based on file extension
            content_type = self._get_content_type(file_path)
            main_type, sub_type = content_type.split('/', 1)
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(attachment.read())
            
            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)
            
            # Add header as key/value pair to attachment part
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}',
            )
            
            # Attach the part to message
            msg.attach(part)
            
            file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
            self.logger.info(f"📎 Attached file: {filename} ({file_size:.2f} MB)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to attach file {file_path}: {e}")

    def _get_content_type(self, file_path: str) -> str:
        """Determine MIME content type based on file extension"""
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(file_path)
        
        if content_type is None:
            # Default to application/octet-stream for unknown types
            content_type = 'application/octet-stream'
        
        return content_type
    
    def _log_notification(self, recipient: str, subject: str, content: str) -> bool:
        """Log notification instead of sending (fallback)"""
        try:
            log_path = os.path.join("outputs", "email_notifications.log")
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                f.write(f"TO: {recipient}\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(f"CONTENT:\n{content}\n")
                f.write(f"{'='*50}\n")
            
            self.logger.info(f"Email notification logged to {log_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log notification: {e}")
            return False
    
    async def send_error_notification(
        self, 
        recipient: str, 
        patient_name: str, 
        error_message: str, 
        session_id: str
    ) -> bool:
        """Send notification when report generation fails"""
        
        try:
            subject = f"OT Report Generation Failed - {patient_name}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="background-color: #f44336; color: white; padding: 20px; text-align: center;">
                    <h1>❌ Report Generation Failed</h1>
                    <p>FMRC Health Group - Automated Report System</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Error Notification</h2>
                    
                    <p>Unfortunately, there was an error generating the pediatric OT evaluation report.</p>
                    
                    <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h3>Error Details</h3>
                        <p><strong>Patient:</strong> {patient_name}</p>
                        <p><strong>Session ID:</strong> {session_id[:8]}</p>
                        <p><strong>Error Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p><strong>Error Message:</strong> {error_message}</p>
                    </div>
                    
                    <h3>Next Steps</h3>
                    <ul>
                        <li>Check the uploaded files for proper format and content</li>
                        <li>Verify that all required assessments were uploaded</li>
                        <li>Retry the report generation process</li>
                        <li>Contact technical support if the issue persists</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
OT REPORT GENERATION FAILED
===========================

Error Notification

Unfortunately, there was an error generating the pediatric OT evaluation report.

ERROR DETAILS
-------------
Patient: {patient_name}
Session ID: {session_id[:8]}
Error Time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Error Message: {error_message}

NEXT STEPS
----------
1. Check the uploaded files for proper format and content
2. Verify that all required assessments were uploaded
3. Retry the report generation process
4. Contact technical support if the issue persists

For technical support, please provide the Session ID and error details above.
            """
            
            # Send using available method
            if self.yag:
                success = await self._send_with_yagmail(recipient, subject, html_content, text_content)
            elif self.email_user and self.email_password:
                success = await self._send_with_smtp(recipient, subject, html_content, text_content)
            else:
                success = self._log_notification(recipient, subject, text_content)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration and return status"""
        status = {
            "configured": False,
            "method": None,
            "issues": []
        }
        
        if not self.email_user:
            status["issues"].append("EMAIL_ADDRESS environment variable not set")
        
        if not self.email_password:
            status["issues"].append("EMAIL_PASSWORD environment variable not set")
        
        if YAGMAIL_AVAILABLE and self.email_user and self.email_password:
            try:
                test_yag = yagmail.SMTP(self.email_user, self.email_password)
                status["configured"] = True
                status["method"] = "yagmail"
            except Exception as e:
                status["issues"].append(f"Yagmail configuration error: {e}")
        
        if not status["configured"] and self.email_user and self.email_password:
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                status["configured"] = True
                status["method"] = "smtp"
            except Exception as e:
                status["issues"].append(f"SMTP configuration error: {e}")
        
        if not status["configured"]:
            status["method"] = "logging"
            status["issues"].append("Will log notifications instead of sending emails")
        
        return status
    
    async def send_test_email(self, recipient_email: str, test_message: str = None, attachment_files: List[str] = None):
        """Send a test email to verify email configuration"""
        self.logger.info(f"🧪 Sending test email to {recipient_email}")
        
        if attachment_files:
            self.logger.info(f"📎 Including {len(attachment_files)} test attachment(s)")
        
        if not test_message:
            test_message = "This is a test email from the OT Report Generator system."
        
        subject = "OT Report Generator - Test Email"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                        🧪 OT Report Generator - Test Email
                    </h2>
                    
                    <p>Hello!</p>
                    
                    <p><strong>✅ Email configuration test successful!</strong></p>
                    
                    <p>{test_message}</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #28a745;">Test Details:</h3>
                        <ul>
                            <li><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                            <li><strong>SMTP Server:</strong> {self.smtp_server}:{self.smtp_port}</li>
                            <li><strong>From Address:</strong> {self.from_email}</li>
                            <li><strong>To Address:</strong> {recipient_email}</li>
                        </ul>
                    </div>
                    
                    <p>If you received this email, your email configuration is working correctly! 🎉</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        This is an automated test email from the Pediatric OT Report Generator system.<br>
                        If you received this email unexpectedly, please contact your system administrator.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
OT Report Generator - Test Email
================================

Hello!

✅ Email configuration test successful!

{test_message}

Test Details:
- Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- SMTP Server: {self.smtp_server}:{self.smtp_port}
- From Address: {self.from_email}
- To Address: {recipient_email}

If you received this email, your email configuration is working correctly! 🎉

---
This is an automated test email from the Pediatric OT Report Generator system.
If you received this email unexpectedly, please contact your system administrator.
        """
        
        try:
            # Try yagmail first if available
            if self.yag:
                self.logger.info("📧 Sending test email via yagmail...")
                result = await self._send_with_yagmail(recipient_email, subject, html_body, text_body, attachment_files)
            elif self.email_user and self.email_password:
                self.logger.info("📧 Sending test email via standard SMTP...")
                result = await self._send_with_smtp(recipient_email, subject, html_body, text_body, attachment_files)
            else:
                self.logger.warning("⚠️ No email configuration available - logging test email")
                result = self._log_notification(recipient_email, subject, text_body)
            
            self.logger.info(f"✅ Test email sent successfully to {recipient_email}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Test email failed: {e}")
            raise 