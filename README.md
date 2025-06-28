# Pediatric OT Report Generator - AI-Enhanced Professional System

🚀 **NEW: OpenAI-Powered Professional Reports** - Generate detailed, clinical-quality OT evaluation reports matching professional standards using advanced AI.

Automated generation of comprehensive pediatric occupational therapy evaluation reports from multiple assessment PDFs using AI-powered processing and professional report formatting.

## 🌟 AI-Enhanced Features

### Professional Report Generation with OpenAI
- **🧠 AI-Generated Clinical Narratives**: Sophisticated clinical language and detailed behavioral observations
- **📊 Intelligent Score Interpretation**: Evidence-based analysis of assessment results
- **🎯 Professional Formatting**: Matches the format and quality of professional OT evaluation reports
- **📋 SMART Goals Generation**: Specific, measurable treatment goals with timelines
- **🔍 Clinical Terminology**: Advanced medical and therapeutic language

### Report Quality Comparison

| Feature | Basic Report | Professional (AI-Enhanced) |
|---------|-------------|----------------------------|
| Clinical Narratives | Template-based | AI-generated, sophisticated |
| Terminology | Standard | Advanced clinical language |
| Observations | Generic | Detailed, personalized |
| Score Interpretation | Basic | Evidence-based, comprehensive |
| Goals | Template | SMART, specific, measurable |
| Formatting | Standard | Professional clinical format |

## 🌟 Enhanced Automation Features

Based on the automation workflow requirements, this system now supports:

### Multi-Assessment Processing
- **Facesheet Processing**: Patient demographics and basic information
- **Bayley-4 Assessments**: Cognitive, Language, Motor, Social-Emotional, and Adaptive Behavior
- **Sensory Profile 2 (SP2)**: Sensory processing assessment
- **ChOMPS**: Chicago Oral Motor and Feeding Assessment  
- **PediEAT**: Pediatric Eating Assessment Tool
- **Clinical Notes**: Observational notes and behavioral documentation

### Intelligent Data Extraction
- **Chronological Age Calculation**: Auto-calculates age in years, months, and days from DOB and encounter date
- **Score Interpretation**: Comprehensive interpretation of standard scores, percentiles, and age equivalents
- **Bullet-to-Narrative Conversion**: Transforms clinical observations into professional narrative format
- **Multi-Domain Analysis**: Integrates findings across all assessment domains

### Professional Output Options
- **Google Docs Integration**: Creates editable reports directly in Google Docs
- **PDF Generation**: Professional PDF reports with comprehensive formatting
- **Email Notifications**: Automatic completion notifications with report links
- **Session Management**: Secure handling of patient data with unique session IDs

## 📋 Assessment Types Supported

### Core Assessments (Required)
1. **Patient Demographics (Facesheet)**
   - Patient information, insurance, contact details
   - Referral information and case history

2. **Bayley-4 Cognitive, Language & Motor Scales**
   - Cognitive composite scores and domain-specific results
   - Language development (receptive and expressive)
   - Fine and gross motor skill assessment

3. **Bayley-4 Social-Emotional & Adaptive Behavior**
   - Social-emotional development composite
   - Adaptive behavior across multiple domains
   - Self-care and community living skills

### Additional Assessments (Optional)
4. **Sensory Profile 2 (SP2)**
   - Sensory processing quadrants analysis
   - Behavioral response patterns
   - Environmental impact assessment

5. **ChOMPS Feeding Assessment**
   - Oral motor and feeding skills evaluation
   - Safety risk assessment
   - Feeding behavior analysis

6. **PediEAT Assessment**
   - Eating and feeding difficulties
   - Physiological and behavioral factors
   - Mealtime behavior analysis

7. **Clinical Observations & Notes**
   - Behavioral observations during assessment
   - Structured clinical notes
   - Supplementary documentation

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
cd /home/lap-49/Documents/ot-report

# Activate virtual environment
source venv/ot-report/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. OpenAI Setup (for Professional Reports)
```bash
# Set your OpenAI API key for AI-enhanced reports
export OPENAI_API_KEY="your-openai-api-key"

# Or create .env file (recommended)
echo "OPENAI_API_KEY=your-openai-api-key" > .env
```
**📖 See [config_setup.md](config_setup.md) for detailed configuration guide**

### 3. Start the Application
```bash
# Start the server
python main.py

# Or use uvicorn directly
uvicorn main:app --host localhost --port 8000 --reload
```

### 4. Access the Application
- Open your browser to: `http://localhost:8000`
- Upload your assessment PDFs using the enhanced interface
- Fill in patient information (auto-calculates chronological age)
- **🎯 Select "Professional (AI-Enhanced)" for clinical-quality reports**
- **⚡ Or choose "Basic Report" for standard template-based reports**
- Select output preferences and notification email
- Generate comprehensive reports

## 📊 Report Generation Workflow

### Input Processing
1. **File Upload**: Multiple PDF assessments uploaded simultaneously
2. **Patient Information**: Demographics with automatic age calculation
3. **Data Extraction**: AI-powered parsing of assessment scores and observations
4. **Integration**: Cross-assessment analysis and synthesis

### Content Generation
1. **Assessment Results**: Detailed scores, percentiles, and interpretations
2. **Clinical Observations**: Professional narrative from bullet points
3. **Strengths & Needs**: Evidence-based identification across domains
4. **Recommendations**: Targeted intervention strategies
5. **Treatment Goals**: Short-term and long-term objectives

### Output Delivery
1. **Google Docs**: Live, editable reports with professional formatting
2. **PDF Download**: Print-ready comprehensive evaluation reports
3. **Email Notification**: Automatic delivery with secure links
4. **Session Management**: Secure data handling and cleanup

## 🔧 Configuration Options

### Google Docs Integration
To enable Google Docs output, set up service account credentials:

```bash
# Set environment variable for credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
```

### Email Notifications
Configure email settings using environment variables:

```bash
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
```

### Optional Dependencies
For enhanced features:
```bash
pip install google-api-python-client google-auth yagmail
```

## 📁 Project Structure

```
ot-report/
├── main.py                     # Enhanced FastAPI application
├── pdf_processor.py            # Multi-assessment PDF processing
├── report_generator.py         # Comprehensive report generation
├── google_docs_integration.py  # Google Docs API integration
├── email_notifier.py          # Email notification system
├── templates/
│   ├── index.html             # Enhanced multi-upload interface
│   └── result.html            # Results with multiple output options
├── uploads/                   # Temporary file storage
├── outputs/                   # Generated reports and logs
├── requirements.txt           # All dependencies
└── README.md                 # This file
```

## 🎯 Key Features

### Enhanced Data Processing
- **Multi-PDF Processing**: Simultaneous handling of different assessment types
- **Intelligent Parsing**: Context-aware extraction of scores and observations
- **Age Calculation**: Automatic chronological age computation
- **Score Interpretation**: Professional-level analysis of assessment results

### Professional Report Generation
- **Comprehensive Structure**: Background, results, observations, findings, recommendations
- **Clinical Formatting**: Professional medical report standards
- **Multi-Domain Integration**: Synthesis across all assessment areas
- **Evidence-Based Content**: Research-informed interpretations and recommendations

### Modern User Experience
- **Intuitive Interface**: Clear upload areas for different assessment types
- **Progress Tracking**: Real-time processing updates
- **Flexible Output**: Choice of Google Docs, PDF, or both
- **Email Integration**: Automatic notifications with secure links

### Security & Compliance
- **Session-Based Security**: Unique session IDs for data protection
- **Temporary Storage**: Automatic cleanup of uploaded files
- **HIPAA Considerations**: Secure handling of patient information
- **Error Handling**: Comprehensive error reporting and recovery

## 📋 Usage Examples

### Basic Workflow
1. **Access Application**: Navigate to `http://localhost:8000`
2. **Enter Patient Info**: Name, DOB, encounter date (age auto-calculated)
3. **Upload Assessments**: 
   - Required: Facesheet, Bayley-4 Cognitive, Bayley-4 Social-Emotional
   - Optional: SP2, ChOMPS, PediEAT, Clinical Notes
4. **Set Preferences**: Output format and notification email
5. **Generate Report**: Comprehensive processing and professional output

### Advanced Features
- **Multiple Assessment Types**: Upload any combination of supported assessments
- **Automatic Integration**: Synthesizes findings across all uploaded assessments
- **Professional Narratives**: Converts clinical observations to narrative format
- **Treatment Planning**: Evidence-based goals and recommendations

## 🔧 Troubleshooting

### Common Issues

**PDF Processing Errors**
- Ensure PDFs are text-based (not scanned images)
- Verify files contain expected assessment data
- Check file sizes (recommended < 10MB each)

**Google Docs Integration**
- Verify service account credentials are properly configured
- Check Google API permissions and scopes
- Ensure network connectivity for API calls

**Email Notifications**
- Verify email credentials and SMTP settings
- Check app-specific passwords for Gmail
- Review firewall/network restrictions

## 📞 Support & Development

### System Requirements
- Python 3.8+
- FastAPI framework
- PDF processing libraries (pdfplumber, PyPDF2)
- Optional: Google API libraries, email libraries

### API Endpoints
- `GET /`: Main upload interface
- `POST /upload-files/`: Enhanced multi-file processing
- `GET /download/{session_id}`: PDF download
- `GET /download-text/{session_id}`: Text fallback
- `GET /health`: System health check

### Development Mode
```bash
# Start with auto-reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📄 Version History

### v2.0.0 - Enhanced Automation
- Multi-assessment PDF processing (Bayley-4, SP2, ChOMPS, PediEAT)
- Google Docs integration with professional formatting
- Email notification system
- Chronological age auto-calculation
- Bullet-to-narrative conversion
- Enhanced UI with categorized uploads
- Session-based security improvements
- Comprehensive error handling

### v1.0.0 - Initial Release
- Basic Bayley-4 report processing
- PDF report generation
- Simple web interface
- Core assessment functionality

---

**FMRC Health Group - Pediatric OT Report Generator**  
*Automated Excellence in Pediatric Occupational Therapy Documentation* 