#!/usr/bin/env python3
"""
Configuration Setup Script for Pediatric OT Report Generator
Helps users easily configure their .env file with interactive prompts
"""

import os
import sys
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🔧 PEDIATRIC OT REPORT GENERATOR - CONFIGURATION SETUP")
    print("=" * 60)
    print()

def print_section(title):
    """Print section header"""
    print(f"\n{'='*10} {title} {'='*10}")

def get_user_input(prompt, default=None, is_optional=False):
    """Get user input with default value"""
    if default:
        prompt_text = f"{prompt} [{default}]: "
    elif is_optional:
        prompt_text = f"{prompt} (optional): "
    else:
        prompt_text = f"{prompt}: "
    
    user_input = input(prompt_text).strip()
    
    if not user_input and default:
        return default
    elif not user_input and is_optional:
        return ""
    
    return user_input

def setup_openai_config():
    """Setup OpenAI configuration"""
    print_section("OpenAI Configuration (for AI-Enhanced Reports)")
    print("To enable AI-enhanced professional reports:")
    print("1. Visit: https://platform.openai.com/api-keys")
    print("2. Create an API key")
    print("3. Copy and paste it below")
    print()
    
    api_key = get_user_input("OpenAI API Key", is_optional=True)
    model = get_user_input("OpenAI Model", default="gpt-3.5-turbo")
    
    return {
        'OPENAI_API_KEY': api_key,
        'OPENAI_MODEL': model
    }

def setup_email_config():
    """Setup email configuration"""
    print_section("Email Configuration (for Notifications)")
    print("To enable email notifications:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
    print("3. Use the 16-character app password (not your regular Gmail password)")
    print()
    
    email_address = get_user_input("Email Address", is_optional=True)
    email_password = ""
    if email_address:
        email_password = get_user_input("App Password (16 characters)", is_optional=True)
    
    smtp_server = get_user_input("SMTP Server", default="smtp.gmail.com")
    smtp_port = get_user_input("SMTP Port", default="587")
    default_recipient = get_user_input("Default Recipient Email", default="fushia.crooms@gmail.com")
    
    return {
        'EMAIL_ADDRESS': email_address,
        'EMAIL_PASSWORD': email_password,
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'DEFAULT_RECIPIENT': default_recipient
    }

def setup_google_config():
    """Setup Google Docs configuration"""
    print_section("Google Docs Configuration (for Cloud Reports)")
    print("To enable Google Docs integration:")
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select existing")
    print("3. Enable Google Docs API and Google Drive API")
    print("4. Create Service Account credentials")
    print("5. Download the JSON file and save as 'service_account.json'")
    print()
    
    service_account_file = get_user_input("Service Account File", default="service_account.json")
    drive_folder_id = get_user_input("Google Drive Folder ID", is_optional=True)
    
    return {
        'GOOGLE_SERVICE_ACCOUNT_FILE': service_account_file,
        'GOOGLE_DRIVE_FOLDER_ID': drive_folder_id
    }

def setup_app_config():
    """Setup application configuration"""
    print_section("Application Configuration")
    
    host = get_user_input("Server Host", default="127.0.0.1")
    port = get_user_input("Server Port", default="8000")
    debug_mode = get_user_input("Debug Mode (true/false)", default="false")
    default_report_type = get_user_input("Default Report Type (professional/basic)", default="professional")
    default_output_format = get_user_input("Default Output Format (pdf/google_docs)", default="pdf")
    max_file_size = get_user_input("Max File Size (MB)", default="50")
    log_level = get_user_input("Log Level (DEBUG/INFO/WARNING/ERROR)", default="INFO")
    
    return {
        'APP_HOST': host,
        'APP_PORT': port,
        'DEBUG_MODE': debug_mode,
        'DEFAULT_REPORT_TYPE': default_report_type,
        'DEFAULT_OUTPUT_FORMAT': default_output_format,
        'MAX_FILE_SIZE_MB': max_file_size,
        'LOG_LEVEL': log_level,
        'LOG_TO_FILE': 'true'
    }

def write_env_file(config):
    """Write configuration to .env file"""
    env_path = Path('.env')
    
    # Backup existing .env file
    if env_path.exists():
        backup_path = Path('.env.backup')
        backup_path.write_text(env_path.read_text())
        print(f"📄 Backed up existing .env to .env.backup")
    
    # Write new configuration
    with open(env_path, 'w') as f:
        f.write("# =============================================================================\n")
        f.write("# PEDIATRIC OT REPORT GENERATOR - CONFIGURATION FILE\n")
        f.write("# Generated by setup_config.py\n")
        f.write("# =============================================================================\n\n")
        
        # OpenAI Configuration
        f.write("# =============================================================================\n")
        f.write("# OPENAI CONFIGURATION\n")
        f.write("# =============================================================================\n")
        if config['OPENAI_API_KEY']:
            f.write(f"OPENAI_API_KEY={config['OPENAI_API_KEY']}\n")
        else:
            f.write("# OPENAI_API_KEY=your_openai_api_key_here\n")
        f.write(f"OPENAI_MODEL={config['OPENAI_MODEL']}\n\n")
        
        # Email Configuration
        f.write("# =============================================================================\n")
        f.write("# EMAIL CONFIGURATION\n")
        f.write("# =============================================================================\n")
        if config['EMAIL_ADDRESS']:
            f.write(f"EMAIL_ADDRESS={config['EMAIL_ADDRESS']}\n")
            f.write(f"EMAIL_PASSWORD={config['EMAIL_PASSWORD']}\n")
        else:
            f.write("# EMAIL_ADDRESS=your_email@gmail.com\n")
            f.write("# EMAIL_PASSWORD=your_16_character_app_password\n")
        f.write(f"SMTP_SERVER={config['SMTP_SERVER']}\n")
        f.write(f"SMTP_PORT={config['SMTP_PORT']}\n")
        f.write(f"DEFAULT_RECIPIENT={config['DEFAULT_RECIPIENT']}\n\n")
        
        # Google Configuration
        f.write("# =============================================================================\n")
        f.write("# GOOGLE DOCS CONFIGURATION\n")
        f.write("# =============================================================================\n")
        f.write(f"GOOGLE_SERVICE_ACCOUNT_FILE={config['GOOGLE_SERVICE_ACCOUNT_FILE']}\n")
        if config['GOOGLE_DRIVE_FOLDER_ID']:
            f.write(f"GOOGLE_DRIVE_FOLDER_ID={config['GOOGLE_DRIVE_FOLDER_ID']}\n")
        else:
            f.write("# GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id\n")
        f.write("\n")
        
        # Application Configuration
        f.write("# =============================================================================\n")
        f.write("# APPLICATION SETTINGS\n")
        f.write("# =============================================================================\n")
        f.write(f"APP_HOST={config['APP_HOST']}\n")
        f.write(f"APP_PORT={config['APP_PORT']}\n")
        f.write(f"DEBUG_MODE={config['DEBUG_MODE']}\n")
        f.write(f"DEFAULT_REPORT_TYPE={config['DEFAULT_REPORT_TYPE']}\n")
        f.write(f"DEFAULT_OUTPUT_FORMAT={config['DEFAULT_OUTPUT_FORMAT']}\n")
        f.write(f"MAX_FILE_SIZE_MB={config['MAX_FILE_SIZE_MB']}\n")
        f.write(f"LOG_LEVEL={config['LOG_LEVEL']}\n")
        f.write(f"LOG_TO_FILE={config['LOG_TO_FILE']}\n")
    
    print(f"✅ Configuration saved to .env")

def main():
    """Main setup function"""
    print_header()
    
    print("This script will help you configure the Pediatric OT Report Generator.")
    print("Press Enter to use default values, or type your own values.")
    print("You can skip optional configurations by pressing Enter.")
    print()
    
    # Collect all configuration
    config = {}
    
    # OpenAI Configuration
    openai_config = setup_openai_config()
    config.update(openai_config)
    
    # Email Configuration
    email_config = setup_email_config()
    config.update(email_config)
    
    # Google Configuration
    google_config = setup_google_config()
    config.update(google_config)
    
    # Application Configuration
    app_config = setup_app_config()
    config.update(app_config)
    
    # Summary
    print_section("Configuration Summary")
    enabled_features = []
    
    if config['OPENAI_API_KEY']:
        enabled_features.append("✅ AI-Enhanced Reports")
    else:
        enabled_features.append("⚠️ AI-Enhanced Reports (not configured)")
    
    if config['EMAIL_ADDRESS']:
        enabled_features.append("✅ Email Notifications")
    else:
        enabled_features.append("⚠️ Email Notifications (not configured)")
    
    if os.path.exists(config['GOOGLE_SERVICE_ACCOUNT_FILE']):
        enabled_features.append("✅ Google Docs Integration")
    else:
        enabled_features.append("⚠️ Google Docs Integration (service account not found)")
    
    enabled_features.append("✅ PDF Reports (always available)")
    
    print("Features that will be enabled:")
    for feature in enabled_features:
        print(f"  {feature}")
    
    print(f"\nServer will run on: {config['APP_HOST']}:{config['APP_PORT']}")
    
    # Confirm and save
    print()
    confirm = input("Save this configuration? (y/n): ").lower().strip()
    
    if confirm in ['y', 'yes']:
        write_env_file(config)
        print()
        print("🎉 Configuration setup complete!")
        print()
        print("Next steps:")
        print("1. Run: python main.py")
        print("2. Open: http://localhost:8000")
        print("3. Upload assessment files to generate reports")
        print()
        if not config['OPENAI_API_KEY']:
            print("💡 To enable AI-enhanced reports, add your OpenAI API key to .env")
        if not config['EMAIL_ADDRESS']:
            print("💡 To enable email notifications, add your email credentials to .env")
        if not os.path.exists(config['GOOGLE_SERVICE_ACCOUNT_FILE']):
            print("💡 To enable Google Docs integration, add your service account JSON file")
    else:
        print("❌ Configuration cancelled")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1) 