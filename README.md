# 🩺 Pediatric OT Report Generator

**AI-Enhanced Occupational Therapy Report Generation System**

An advanced, configurable system for generating professional pediatric occupational therapy evaluation reports from multiple assessment PDFs with optional AI enhancement, Google Docs integration, and email notifications.

## ✨ Key Features

- **📄 PDF Report Generation**: Always available core functionality
- **🧠 AI-Enhanced Reports**: Professional clinical narratives using OpenAI (configurable)
- **☁️ Google Docs Integration**: Cloud-based report creation and sharing (configurable)  
- **📧 Email Notifications**: Automatic delivery notifications (configurable)
- **📊 Multi-Assessment Support**: Bayley-4, SP2, ChOMPS, PediEAT, and more
- **⚙️ Flexible Configuration**: Easy .env-based setup with optional features

## 🚀 Quick Setup

### Option 1: Interactive Configuration (Recommended)
```bash
# 1. Clone and setup
git clone <repository>
cd ot-report
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Run interactive setup
python setup_config.py

# 3. Start the application
python main.py
```

### Option 2: Manual Configuration
```bash
# 1. Setup environment
git clone <repository>
cd ot-report
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure manually
cp .env.example .env
# Edit .env with your preferred settings

# 3. Start the application
python main.py
```

## ⚙️ Configuration Options

The application uses a `.env` file for configuration. All features are optional and can be enabled/disabled as needed.

### 🧠 OpenAI Configuration (AI-Enhanced Reports)
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

**Setup Instructions:**
1. Visit: https://platform.openai.com/api-keys
2. Create an API key
3. Add to your `.env` file

**Benefits:** Professional clinical narratives, sophisticated interpretations, evidence-based content

### 📧 Email Configuration (Notifications)
```bash
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_16_character_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
DEFAULT_RECIPIENT=fushia.crooms@gmail.com
```

**Setup Instructions:**
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password (not your regular Gmail password)

**Benefits:** Automatic email notifications when reports are generated and shared

### 🔧 Google Docs Integration

The system now supports **both** Google authentication methods:

### 📱 **OAuth2 Client Credentials (Recommended for individual use)**
✅ **CURRENTLY CONFIGURED AND WORKING**

Your system is configured with OAuth2 client credentials and has been successfully authorized!

**Setup Process:**
1. ✅ Downloaded OAuth2 client credentials from Google Cloud Console  
2. ✅ Set `GOOGLE_SERVICE_ACCOUNT_FILE` environment variable
3. ✅ OAuth2 authorization flow completed automatically
4. ✅ `token.json` file created with valid credentials

**Files Created:**
- `token.json` - Contains your authorized OAuth2 tokens (automatically refreshed)

### 🔐 **Service Account (Alternative for server deployments)**
Alternative method using service account JSON files for server-to-server authentication.

**Authentication Methods Supported:**
- ✅ OAuth2 Client Credentials (`client_secret_*.json`) - **Active**
- ✅ Service Account Credentials (`service_account.json`) - Available
- ✅ Automatic credential type detection
- ✅ Token refresh and management
- ✅ Comprehensive validation and error reporting

**Google APIs Enabled:**
- ✅ Google Docs API - For document creation
- ✅ Google Drive API - For file sharing and permissions

### 🔧 Application Settings
```bash
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG_MODE=false
DEFAULT_REPORT_TYPE=professional
DEFAULT_OUTPUT_FORMAT=pdf
MAX_FILE_SIZE_MB=50
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

## 📊 Feature Comparison

| Feature | Without Configuration | With Full Configuration |
|---------|----------------------|------------------------|
| **PDF Reports** | ✅ Basic professional reports | ✅ Enhanced professional reports |
| **Clinical Narratives** | ✅ Enhanced fallback templates | 🧠 AI-generated clinical content |
| **Report Delivery** | ✅ Download links | 📧 Email notifications + ☁️ Google Docs |
| **Collaboration** | ❌ Local files only | ✅ Cloud sharing and editing |
| **Customization** | ⚠️ Limited options | ✅ Full configuration control |

## 📱 Usage

1. **Start the application**: `python main.py`
2. **Open browser**: Navigate to `http://localhost:8000`
3. **Upload assessments**: 
   - Required: Bayley-4 Cognitive/Language/Motor + Social-Emotional/Adaptive
   - Optional: SP2, ChOMPS, PediEAT, Clinical Notes, Facesheet
4. **Configure report**: Select report type and output format
5. **Generate report**: System processes files and creates comprehensive evaluation

## 🧪 Testing Features

The application provides dedicated endpoints for testing individual features:

### Test Email Integration
```bash
# Test email functionality (POST request)
curl -X POST "http://localhost:8000/test/email" \
  -F "recipient_email=test@example.com" \
  -F "test_message=Custom test message"

# Or use default recipient from config
curl -X POST "http://localhost:8000/test/email"
```

**Response includes:**
- ✅ Success/failure status
- 📧 SMTP server details  
- 🔧 Troubleshooting information
- 📝 Configuration validation

### Test Google Docs Integration
```bash
# Test Google Docs document creation
curl -X POST "http://localhost:8000/test/google-docs"
```

**Response includes:**
- ✅ Success/failure status
- 🔗 Generated document URL
- 📄 Service account validation
- 🔧 API permissions check

### Test OpenAI Integration
```bash
# Test OpenAI API connection and text generation
curl -X GET "http://localhost:8000/test/openai"
```

**Response includes:**
- ✅ Success/failure status
- 🤖 Generated sample text
- 📊 Model information
- 💰 API key validation

### Common Testing Scenarios

**Email Testing:**
- Verifies SMTP connectivity
- Tests Gmail App Password authentication
- Validates recipient delivery
- Checks HTML/text formatting

**Google Docs Testing:**
- Validates service account permissions
- Tests document creation and sharing
- Verifies API quota and access
- Checks Drive folder permissions

**OpenAI Testing:**
- Validates API key and credits
- Tests model availability
- Checks rate limiting
- Verifies response generation

### Troubleshooting with Test Endpoints

**Email Issues:**
```bash
# Test with specific recipient
curl -X POST "http://localhost:8000/test/email" \
  -F "recipient_email=your-email@gmail.com"

# Check response for specific error details
```

**Google Docs Issues:**
```bash
# Test document creation
curl -X POST "http://localhost:8000/test/google-docs"

# Check response for service account errors
```

**OpenAI Issues:**
```bash
# Test API connection
curl -X GET "http://localhost:8000/test/openai"

# Check response for model/credit issues
```

## 🔧 Supported Assessments

| Assessment | Type | Description |
|------------|------|-------------|
| **Bayley-4 Cognitive/Language/Motor** | Required | Primary developmental assessment |
| **Bayley-4 Social-Emotional/Adaptive** | Required | Social-emotional and adaptive behavior |
| **Sensory Profile 2 (SP2)** | Optional | Sensory processing assessment |
| **ChOMPS** | Optional | Feeding assessment tool |
| **PediEAT** | Optional | Pediatric eating assessment |
| **Clinical Notes** | Optional | Therapist observations |
| **Patient Facesheet** | Optional | Demographics and basic info |

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Memory**: 2GB RAM minimum
- **Storage**: 1GB free space
- **Network**: Internet connection (for AI features)

## 🔍 Health Monitoring

The application provides comprehensive health monitoring:

- **Health Check**: `GET /health` - System status and feature availability
- **Configuration Status**: `GET /config` - Current configuration summary
- **Startup Dashboard**: Detailed component status on application start

## 🎛️ Configuration Management

### Interactive Setup
Run `python setup_config.py` for guided configuration with:
- Step-by-step prompts
- Default value suggestions
- Feature explanation
- Validation and backup

### Manual Configuration
Edit `.env` file directly or use environment variables:
```bash
export OPENAI_API_KEY="your-key-here"
export DEFAULT_REPORT_TYPE="professional"
python main.py
```

### Configuration Validation
The system automatically:
- ✅ Validates all configuration options
- ⚠️ Warns about missing optional features
- 📊 Shows available features on startup
- 🔄 Gracefully handles missing configurations

## 🚨 Troubleshooting

### Common Issues

**"OpenAI client not available"**
- Add `OPENAI_API_KEY` to `.env` file
- Verify API key is valid and has sufficient credits
- Reports will use enhanced fallback templates

**"Google Docs service not available"**
- Add `service_account.json` file to project directory
- Verify Google APIs are enabled in your project
- Check service account permissions

**"Email notifications disabled"**
- Add `EMAIL_ADDRESS` and `EMAIL_PASSWORD` to `.env`
- Use Gmail App Password, not regular password
- Verify 2-factor authentication is enabled

**Port already in use**
- Change `APP_PORT` in `.env` file
- Or kill existing process: `lsof -ti:8000 | xargs kill -9`

### Debug Mode
Enable detailed logging:
```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## 🔄 Migration from Previous Versions

If upgrading from a previous version:

1. **Backup existing configuration**:
   ```bash
   cp .env .env.backup  # If exists
   ```

2. **Run configuration setup**:
   ```bash
   python setup_config.py
   ```

3. **Start with new configuration**:
   ```bash
   python main.py
   ```

## 📈 Performance

- **Startup Time**: < 5 seconds
- **Report Generation**: 10-30 seconds (depending on features)
- **File Processing**: Supports files up to 50MB (configurable)
- **Concurrent Users**: Supports multiple simultaneous report generations

## 🛡️ Security

- **API Keys**: Stored securely in `.env` file (not committed to version control)
- **File Handling**: Temporary files automatically cleaned up
- **Service Accounts**: Google service account credentials isolated
- **Network**: Configurable host/port binding

## 📞 Support

### Quick Start Issues
1. Run `python setup_config.py` for guided setup
2. Check `logs/app.log` for detailed error information
3. Verify all requirements are installed: `pip install -r requirements.txt`

### Feature-Specific Help
- **OpenAI Issues**: Check API key validity and model availability
- **Google Docs Issues**: Verify service account permissions and API enablement
- **Email Issues**: Confirm App Password setup and 2FA enabled

### Development
- **Debug Mode**: Set `DEBUG_MODE=true` for detailed logging
- **Log Files**: Check `logs/app.log` for system events
- **Health Endpoint**: Monitor `/health` for component status

---

## 🎯 Quick Feature Enable Guide

**Want AI-enhanced reports?** → Add `OPENAI_API_KEY` to `.env`  
**Want email notifications?** → Add `EMAIL_ADDRESS` and `EMAIL_PASSWORD` to `.env`  
**Want Google Docs integration?** → Add `service_account.json` file  
**Want all features?** → Run `python setup_config.py` for guided setup  

The system works with any combination of features - enable what you need, when you need it! 🚀 