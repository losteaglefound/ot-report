"""
Configuration Management for Pediatric OT Report Generator
Loads and validates environment variables from .env file
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Configure logging
logger = logging.getLogger(__name__)

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🔧 Loading application configuration...")
        
        # Load all configuration sections
        self.openai = self._load_openai_config()
        self.email = self._load_email_config()
        self.google = self._load_google_config()
        self.app = self._load_app_config()
        self.dev = self._load_dev_config()
        
        # Validate configuration
        self._validate_config()
        
        self.logger.info("✅ Configuration loaded successfully")
    
    def _load_openai_config(self) -> Dict[str, Any]:
        """Load OpenAI configuration"""
        config = {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'enabled': bool(os.getenv('OPENAI_API_KEY'))
        }
        
        if config['enabled']:
            self.logger.info("✅ OpenAI configuration found")
        else:
            self.logger.warning("⚠️ OpenAI API key not configured - will use fallback templates")
        
        return config
    
    def _load_email_config(self) -> Dict[str, Any]:
        """Load email configuration"""
        config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_address': os.getenv('EMAIL_ADDRESS'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'default_recipient': os.getenv('DEFAULT_RECIPIENT', 'fushia.crooms@gmail.com'),
            'enabled': bool(os.getenv('EMAIL_ADDRESS') and os.getenv('EMAIL_PASSWORD'))
        }
        
        if config['enabled']:
            self.logger.info("✅ Email configuration found")
        else:
            self.logger.warning("⚠️ Email credentials not configured - notifications will be disabled")
        
        return config
    
    def _load_google_config(self) -> Dict[str, Any]:
        """Load Google Docs configuration"""
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', '/home/lap-49/Downloads/client_secret_1098388858128-27igda26a5bvomu30l7s0bj33g7spijd.apps.googleusercontent.com.json')
        
        config = {
            'service_account_file': service_account_file,
            'drive_folder_id': os.getenv('GOOGLE_DRIVE_FOLDER_ID', ''),
            'template_doc_id': os.getenv('GOOGLE_TEMPLATE_DOC_ID', ''),
            'enabled': os.path.exists(service_account_file)
        }
        
        if config['enabled']:
            self.logger.info("✅ Google Docs configuration found")
        else:
            self.logger.warning("⚠️ Google service account not found - Google Docs integration disabled")
        
        return config
    
    def _load_app_config(self) -> Dict[str, Any]:
        """Load application configuration"""
        config = {
            'host': os.getenv('APP_HOST', '127.0.0.1'),
            'port': int(os.getenv('APP_PORT', '8000')),
            'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            'default_report_type': os.getenv('DEFAULT_REPORT_TYPE', 'professional'),
            'default_output_format': os.getenv('DEFAULT_OUTPUT_FORMAT', 'pdf'),
            'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', '50')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_to_file': os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
        }
        
        self.logger.info(f"📊 App configuration loaded - Host: {config['host']}:{config['port']}")
        return config
    
    def _load_dev_config(self) -> Dict[str, Any]:
        """Load development configuration"""
        config = {
            'dev_mode': os.getenv('DEV_MODE', 'false').lower() == 'true'
        }
        
        if config['dev_mode']:
            self.logger.info("🔧 Development mode enabled")
        
        return config
    
    def _validate_config(self):
        """Validate configuration and log warnings for missing features"""
        self.logger.info("🔍 Validating configuration...")
        
        issues = []
        warnings = []
        
        # Check for common configuration issues
        if not self.openai['enabled']:
            warnings.append("OpenAI API key not configured - AI-enhanced reports will use fallback templates")
        
        if not self.email['enabled']:
            warnings.append("Email credentials not configured - email notifications disabled")
        
        if not self.google['enabled']:
            warnings.append("Google service account not found - Google Docs integration disabled")
        
        # Log warnings
        for warning in warnings:
            self.logger.warning(f"⚠️ {warning}")
        
        # Log available features
        available_features = []
        if self.openai['enabled']:
            available_features.append("AI-Enhanced Reports")
        if self.email['enabled']:
            available_features.append("Email Notifications")
        if self.google['enabled']:
            available_features.append("Google Docs Integration")
        
        available_features.append("PDF Reports")  # Always available
        
        self.logger.info(f"✅ Available features: {', '.join(available_features)}")
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of all features"""
        return {
            'pdf_reports': True,  # Always available
            'ai_enhanced_reports': self.openai['enabled'],
            'email_notifications': self.email['enabled'],
            'google_docs_integration': self.google['enabled']
        }
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""
        return {
            'features': self.get_feature_status(),
            'app_settings': {
                'host': self.app['host'],
                'port': self.app['port'],
                'debug_mode': self.app['debug_mode'],
                'default_report_type': self.app['default_report_type'],
                'default_output_format': self.app['default_output_format']
            },
            'openai_model': self.openai['model'] if self.openai['enabled'] else None,
            'email_provider': self.email['smtp_server'] if self.email['enabled'] else None
        }

# Global configuration instance
config = Config()

# Convenience functions for easy access
def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key"""
    return config.openai['api_key']

def get_openai_model() -> str:
    """Get OpenAI model"""
    return config.openai['model']

def is_openai_enabled() -> bool:
    """Check if OpenAI is enabled"""
    return config.openai['enabled']

def is_email_enabled() -> bool:
    """Check if email is enabled"""
    return config.email['enabled']

def is_google_docs_enabled() -> bool:
    """Check if Google Docs is enabled"""
    return config.google['enabled']

def get_app_host() -> str:
    """Get application host"""
    return config.app['host']

def get_app_port() -> int:
    """Get application port"""
    return config.app['port']

def is_dev_mode() -> bool:
    """Check if development mode is enabled"""
    return config.dev['dev_mode'] 