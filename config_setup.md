# Configuration Setup Guide

## OpenAI Integration Setup (for Professional AI-Enhanced Reports)

### 1. Get OpenAI API Key
1. Visit [OpenAI's website](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key

### 2. Set Environment Variable
Choose one of the following methods:

#### Option A: Set for current session
```bash
export OPENAI_API_KEY="your-api-key-here"
```

#### Option B: Add to .bashrc (permanent)
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### Option C: Create .env file (recommended)
```bash
# Create .env file in project directory
cat > .env << 'EOF'
OPENAI_API_KEY=your-api-key-here

# Optional: Email configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your-email@gmail.com

# Optional: Google Docs integration
GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
EOF
```

### 3. Install python-dotenv (if using .env file)
```bash
pip install python-dotenv
```

### 4. Update main.py to load .env (if using .env file)
Add to the top of main.py:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Email Notifications Setup

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password (not your regular password)

### Environment Variables
```bash
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
```

## Google Docs Integration Setup

### 1. Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Docs API and Google Drive API
4. Create service account credentials
5. Download JSON credentials file

### 2. Set Environment Variable
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
```

## Features Available

### Without OpenAI API Key
- ✅ Basic PDF report generation
- ✅ Multi-assessment PDF processing  
- ✅ Google Docs integration (if configured)
- ✅ Email notifications (if configured)
- ❌ AI-enhanced professional narratives

### With OpenAI API Key
- ✅ All basic features
- ✅ **Professional AI-enhanced reports**
- ✅ **Clinical narrative generation**
- ✅ **Sophisticated terminology**
- ✅ **Evidence-based interpretations**

## Testing the Setup

### 1. Check OpenAI Integration
```bash
python -c "
import os
from openai_report_generator import OpenAIEnhancedReportGenerator

generator = OpenAIEnhancedReportGenerator()
if generator.openai_client:
    print('✅ OpenAI integration working')
else:
    print('❌ OpenAI API key not configured')
"
```

### 2. Test the Application
1. Start the server: `python main.py`
2. Open browser: `http://localhost:8000`
3. Upload sample assessment files
4. Select "Professional (AI-Enhanced)" report type
5. Generate report

## Report Quality Comparison

### Basic Report
- Template-based narratives
- Standard clinical language
- Basic score interpretations
- Functional but generic

### Professional (AI-Enhanced) Report
- **AI-generated clinical narratives**
- **Sophisticated clinical terminology**
- **Detailed behavioral observations**
- **Evidence-based interpretations**
- **Professional formatting matching sample**
- **Specific, measurable goals**

## Troubleshooting

### OpenAI API Issues
- Check API key is valid and has credits
- Verify internet connection
- Check OpenAI service status

### Email Issues
- Verify Gmail app password (not regular password)
- Check 2-factor authentication is enabled
- Test SMTP connection

### Google Docs Issues
- Verify service account has proper permissions
- Check API is enabled in Google Cloud Console
- Ensure credentials file path is correct

## Cost Considerations

### OpenAI API Costs
- Professional reports use GPT-4
- Typical report: ~$0.50-1.00 per report
- Set usage limits in OpenAI dashboard
- Monitor usage regularly

### Recommendations
- Use professional reports for important evaluations
- Use basic reports for testing/drafts
- Set OpenAI usage alerts 