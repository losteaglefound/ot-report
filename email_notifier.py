import os
import logging
import smtplib
from typing import Dict, Any
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
        self.email_user = os.getenv('EMAIL_USER')
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
            self.logger.warning("⚠️ EMAIL_USER environment variable not set")
        
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
            self.yag = yagmail.SMTP(
                user=self.email_user,
                password=self.email_password,
                host=self.smtp_server,
                port=self.smtp_port
            )
            self.logger.info("✅ yagmail initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize yagmail: {e}")
            self.yag = None
    
    async def send_completion_notification(
        self, 
        recipient_email: str, 
        patient_name: str, 
        doc_url: str, 
        session_id: str,
        additional_info: Dict[str, Any] = None
    ) -> bool:
        """Send email notification when report is completed"""
        self.logger.info(f"📧 Sending completion notification for {patient_name}")
        self.logger.info(f"📮 Recipient: {recipient_email}")
        self.logger.info(f"🔗 Document URL: {doc_url}")
        
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
                    recipient_email, subject, html_content, text_content
                )
                if success:
                    return True
            
            # Fallback to standard SMTP
            self.logger.info("📧 Sending email via standard SMTP...")
            success = await self._send_with_smtp(
                recipient_email, subject, html_content, text_content
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
                .footer {{ background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; }}
                .assessment-list {{ background-color: #e8f5e8; padding: 10px; border-radius: 5px; }}
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
                
                <h3>📄 Access Your Report</h3>
                <p>The comprehensive evaluation report includes:</p>
                <ul>
                    <li>Detailed assessment results and score interpretations</li>
                    <li>Clinical observations and behavioral notes</li>
                    <li>Areas of strength and need identification</li>
                    <li>Evidence-based recommendations</li>
                    <li>Short-term and long-term treatment goals</li>
                    <li>Professional summary and clinical insights</li>
                </ul>
                
                <p style="text-align: center;">
                    <a href="{doc_url}" class="button">🔗 Access Report in Google Docs</a>
                </p>
                
                <p><em>Note: The report document is ready for review, editing, and sharing with your team. All patient information has been securely processed and the source files have been handled according to HIPAA guidelines.</em></p>
                
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
The comprehensive evaluation report includes:
• Detailed assessment results and score interpretations
• Clinical observations and behavioral notes
• Areas of strength and need identification
• Evidence-based recommendations
• Short-term and long-term treatment goals
• Professional summary and clinical insights

Report URL: {doc_url}

NEXT STEPS
----------
1. Review the generated report for accuracy and completeness
2. Make any necessary clinical edits or additions
3. Share with interdisciplinary team members as needed
4. Schedule follow-up assessments if recommended

NOTE: The report document is ready for review, editing, and sharing with your team. All patient information has been securely processed and the source files have been handled according to HIPAA guidelines.

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
        text_content: str
    ) -> bool:
        """Send email using yagmail"""
        try:
            self.logger.info("📤 Attempting to send via yagmail...")
            
            self.yag.send(
                to=recipient,
                subject=subject,
                contents=[text_content, html_content]
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
        text_content: str
    ) -> bool:
        """Send email using standard SMTP"""
        if not self.email_user or not self.email_password:
            self.logger.warning("⚠️ SMTP credentials not configured")
            return False
        
        try:
            self.logger.info("📤 Attempting to send via SMTP...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient
            
            # Add both plain and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                self.logger.info(f"🔗 Connecting to {self.smtp_server}:{self.smtp_port}")
                server.starttls()
                
                self.logger.info("🔑 Authenticating...")
                server.login(self.email_user, self.email_password)
                
                self.logger.info("📤 Sending message...")
                server.send_message(msg)
            
            self.logger.info("✅ Email sent successfully via SMTP")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"❌ SMTP authentication failed: {e}")
            self.logger.info("💡 Check email credentials and app-specific passwords")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ SMTP sending failed: {e}")
            return False
    
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
            status["issues"].append("EMAIL_USER environment variable not set")
        
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