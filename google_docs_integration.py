import os
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

try:
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

# Import OpenAI capabilities for enhanced content generation
try:
    import openai
    from config import get_openai_api_key, get_openai_model, is_openai_enabled
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging for this module (after imports)
logger = logging.getLogger(__name__)

if GOOGLE_APIS_AVAILABLE:
    logger.info("✅ Google API libraries imported successfully")
else:
    logger.warning("⚠️ Google API libraries not available - install with: pip install google-api-python-client google-auth")

if OPENAI_AVAILABLE:
    logger.info("✅ OpenAI capabilities imported successfully")
else:
    logger.warning("⚠️ OpenAI not available - will use fallback content generation")

class GoogleDocsReportGenerator:
    """Generate OT reports in Google Docs format using Google Docs API with OpenAI-enhanced content"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("📄 Initializing Google Docs Report Generator with OpenAI enhancement...")
        
        # Check for Google API availability first
        if not GOOGLE_APIS_AVAILABLE:
            self.logger.error("❌ Google API libraries not available")
            self.service = None
            self.drive_service = None
            self.openai_client = None
            return
        
        # Set up credentials path
        self.credentials_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
        
        self.service = None
        self.drive_service = None
        self.template_doc_id = None  # Template document ID if using templates
        
        # Initialize OpenAI client for enhanced content generation
        self.openai_client = None
        self._initialize_openai_client()
        
        self._initialize_google_services()
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client for content generation"""
        if not OPENAI_AVAILABLE:
            self.logger.warning("⚠️ OpenAI not available for content enhancement")
            return
            
        if not is_openai_enabled():
            self.logger.info("🔧 OpenAI disabled in configuration")
            return
            
        try:
            api_key = get_openai_api_key()
            if not api_key:
                self.logger.warning("⚠️ OpenAI API key not configured")
                return
                
            self.openai_client = openai.OpenAI(api_key=api_key)
            self.logger.info("✅ OpenAI client initialized for enhanced content generation")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def _initialize_google_services(self):
        """Initialize Google Docs and Drive services with enhanced validation"""
        self.logger.info("🔑 Initializing Google services...")
        
        credentials_path = self.credentials_path
        self.logger.info(f"🔍 Looking for credentials at: {credentials_path}")
        
        if not os.path.exists(credentials_path):
            self.logger.warning(f"⚠️ Credentials file not found at {credentials_path}")
            self.logger.info("💡 Google Docs integration will be unavailable")
            return
        
        try:
            # First, validate and detect the credentials file type
            self.logger.info("🔍 Validating credentials file format...")
            validation_result = self._validate_credentials_file(credentials_path)
            
            if not validation_result['valid']:
                self.logger.error(f"❌ Credentials file validation failed: {validation_result['error']}")
                self.logger.info("💡 Please check your Google credentials JSON file format")
                return
            
            self.logger.info(f"✅ Credentials file format validated: {validation_result['type']}")
            
            # Initialize based on credentials type
            if validation_result['type'] == 'service_account':
                credentials = self._initialize_service_account(credentials_path)
            elif validation_result['type'] == 'oauth_client':
                credentials = self._initialize_oauth_client(credentials_path)
            else:
                self.logger.error(f"❌ Unsupported credentials type: {validation_result['type']}")
                return
            
            if not credentials:
                self.logger.error("❌ Failed to obtain valid credentials")
                return
            
            # Build services
            self.logger.info("🔨 Building Google Docs service...")
            self.service = build('docs', 'v1', credentials=credentials)
            
            self.logger.info("🔨 Building Google Drive service...")
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            self.logger.info("✅ Google services initialized successfully")
            
            # Test service connectivity
            try:
                # Simple test call to verify credentials work
                self.service.documents().get(documentId='test').execute()
            except HttpError as e:
                if e.resp.status == 404:
                    self.logger.info("✅ Google services connectivity test passed (404 expected)")
                else:
                    self.logger.warning(f"⚠️ Google services test failed: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google services: {e}")
            self.service = None
            self.drive_service = None
    
    def _initialize_service_account(self, credentials_path: str):
        """Initialize using service account credentials"""
        try:
            self.logger.info("🔑 Loading service account credentials...")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            self.logger.info("✅ Service account credentials loaded")
            return credentials
        except Exception as e:
            self.logger.error(f"❌ Failed to load service account credentials: {e}")
            return None
    
    def _initialize_oauth_client(self, credentials_path: str):
        """Initialize using OAuth2 client credentials"""
        try:
            self.logger.info("🔑 Loading OAuth2 client credentials...")
            
            # Check if we have existing token file
            token_file = 'token.json'
            credentials = None
            
            if os.path.exists(token_file):
                self.logger.info("🎫 Found existing token file, loading credentials...")
                try:
                    credentials = Credentials.from_authorized_user_file(
                        token_file,
                        scopes=[
                            'https://www.googleapis.com/auth/documents',
                            'https://www.googleapis.com/auth/drive'
                        ]
                    )
                    if credentials and credentials.valid:
                        self.logger.info("✅ Existing credentials are valid")
                        return credentials
                    elif credentials and credentials.expired and credentials.refresh_token:
                        self.logger.info("🔄 Refreshing expired credentials...")
                        credentials.refresh()
                        # Save refreshed credentials
                        with open(token_file, 'w') as token:
                            token.write(credentials.to_json())
                        self.logger.info("✅ Credentials refreshed successfully")
                        return credentials
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to load existing credentials: {e}")
            
            # Need to run OAuth flow
            self.logger.info("🔐 Starting OAuth2 authorization flow...")
            self.logger.info("⚠️ This will open a browser window for authorization")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            # Run local server for authorization
            credentials = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_file, 'w') as token:
                token.write(credentials.to_json())
            
            self.logger.info("✅ OAuth2 authorization completed and credentials saved")
            return credentials
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OAuth2 credentials: {e}")
            self.logger.info("💡 Make sure you have a valid client_secret.json file and can access a web browser")
            return None
    
    def _validate_credentials_file(self, file_path: str) -> Dict[str, Any]:
        """Validate and detect the type of Google credentials JSON file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
            
            # Check if file is empty
            if not content:
                return {
                    'valid': False,
                    'error': 'Credentials file is empty'
                }
            
            # Try to parse JSON
            try:
                credentials_data = json.loads(content)
            except json.JSONDecodeError as e:
                return {
                    'valid': False,
                    'error': f'Invalid JSON format: {e}'
                }
            
            # Check if it's a dictionary
            if not isinstance(credentials_data, dict):
                return {
                    'valid': False,
                    'error': 'Credentials file must contain a JSON object'
                }
            
            # Detect credentials type
            if 'type' in credentials_data and credentials_data.get('type') == 'service_account':
                # Service account credentials
                return self._validate_service_account_credentials(credentials_data)
            elif 'installed' in credentials_data or 'web' in credentials_data or ('client_id' in credentials_data and 'client_secret' in credentials_data):
                # OAuth2 client credentials (check for 'installed'/'web' first, then direct format)
                return self._validate_oauth_client_credentials(credentials_data)
            else:
                return {
                    'valid': False,
                    'error': 'Unknown credentials type. Expected either service account or OAuth2 client credentials',
                    'help': 'File should be either a service account JSON or OAuth2 client secrets JSON',
                    'found_fields': list(credentials_data.keys())
                }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error reading credentials file: {e}'
            }
    
    def _validate_service_account_credentials(self, credentials_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate service account credentials format"""
        required_fields = [
            'type',
            'project_id',
            'private_key_id',
            'private_key',
            'client_email',
            'client_id',
            'auth_uri',
            'token_uri',
            'auth_provider_x509_cert_url',
            'client_x509_cert_url'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in credentials_data:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'valid': False,
                'type': 'service_account',
                'error': f'Missing required service account fields: {", ".join(missing_fields)}',
                'missing_fields': missing_fields,
                'found_fields': list(credentials_data.keys()),
                'help': 'This should be a Google Cloud service account JSON file downloaded from the Google Cloud Console'
            }
        
        # Additional validation for key fields
        if not credentials_data.get('client_email', '') or '@' not in credentials_data.get('client_email', ''):
            return {
                'valid': False,
                'type': 'service_account',
                'error': 'Invalid client_email format - should be a valid email address'
            }
        
        if not credentials_data.get('private_key', '').startswith('-----BEGIN'):
            return {
                'valid': False,
                'type': 'service_account',
                'error': 'Invalid private_key format - should start with "-----BEGIN"'
            }
        
        return {
            'valid': True,
            'type': 'service_account',
            'project_id': credentials_data.get('project_id'),
            'client_email': credentials_data.get('client_email')
        }
    
    def _validate_oauth_client_credentials(self, credentials_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate OAuth2 client credentials format"""
        
        # Check if it has the 'installed' or 'web' application type
        app_type = None
        app_data = None
        
        if 'installed' in credentials_data:
            app_type = 'installed'
            app_data = credentials_data['installed']
        elif 'web' in credentials_data:
            app_type = 'web'
            app_data = credentials_data['web']
        else:
            # Check for direct client credentials (older format)
            if 'client_id' in credentials_data and 'client_secret' in credentials_data:
                app_type = 'direct'
                app_data = credentials_data
        
        if not app_data:
            return {
                'valid': False,
                'type': 'oauth_client',
                'error': 'OAuth2 client credentials must have "installed", "web", or direct client_id/client_secret fields',
                'found_fields': list(credentials_data.keys()),
                'help': 'This should be a Google OAuth2 client secrets JSON file downloaded from Google Cloud Console'
            }
        
        # Required fields for OAuth2 client
        required_fields = ['client_id', 'client_secret']
        missing_fields = []
        
        for field in required_fields:
            if field not in app_data:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'valid': False,
                'type': 'oauth_client',
                'error': f'Missing required OAuth2 client fields: {", ".join(missing_fields)}',
                'missing_fields': missing_fields,
                'found_fields': list(app_data.keys()),
                'help': 'OAuth2 client credentials must include client_id and client_secret'
            }
        
        return {
            'valid': True,
            'type': 'oauth_client',
            'app_type': app_type,
            'client_id': app_data.get('client_id'),
            'project_id': app_data.get('project_id', 'Unknown')
        }
    
    async def create_report(self, report_data: Dict[str, Any], session_id: str) -> str:
        """Create a comprehensive OT report in Google Docs using OpenAI-enhanced content"""
        patient_name = report_data.get("patient_info", {}).get("name", "Unknown")
        self.logger.info(f"📄 Creating Google Docs report for {patient_name} (session: {session_id})")
        
        if not self.service:
            self.logger.error("❌ Google Docs service not available")
            raise Exception("Google Docs service not initialized")
        
        try:
            # Enhance report data with OpenAI-generated content
            self.logger.info("🤖 Enhancing report data with AI-generated content...")
            enhanced_data = await self._enhance_report_data_for_docs(report_data)
            
            # Create a new document
            self.logger.info("📝 Creating new Google Doc...")
            document_title = f"OT Evaluation Report - {patient_name} - {datetime.now().strftime('%Y-%m-%d')}"
            
            document = {
                'title': document_title
            }
            
            doc = self.service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            doc_url = f"https://docs.google.com/document/d/{doc_id}"
            
            self.logger.info(f"✅ Document created: {doc_id}")
            self.logger.info(f"🔗 Document URL: {doc_url}")
            
            # Build document content with AI-enhanced narratives
            self.logger.info("🔨 Building document content with AI enhancement...")
            requests = []
            
            # Add header
            self.logger.info("📋 Adding header section...")
            requests.extend(self._create_header_requests(enhanced_data))
            
            # Add enhanced content sections using AI
            self.logger.info("🤖 Adding AI-enhanced background section...")
            requests.extend(await self._create_enhanced_background_requests(enhanced_data))
            
            self.logger.info("👥 Adding AI-enhanced caregiver concerns...")
            requests.extend(await self._create_enhanced_caregiver_concerns_requests(enhanced_data))
            
            self.logger.info("👁️ Adding AI-enhanced clinical observations...")
            requests.extend(await self._create_enhanced_clinical_observations_requests(enhanced_data))
            
            # Add assessment results with AI enhancement
            self.logger.info("📊 Adding AI-enhanced assessment results...")
            requests.extend(await self._create_enhanced_assessment_results_requests(enhanced_data))
            
            # Add AI-enhanced recommendations
            self.logger.info("💡 Adding AI-enhanced recommendations...")
            requests.extend(await self._create_enhanced_recommendations_requests(enhanced_data))
            
            # Add AI-enhanced OT goals
            self.logger.info("🎯 Adding AI-enhanced OT goals...")
            requests.extend(await self._create_enhanced_goals_requests(enhanced_data))
            
            # Add AI-enhanced summary
            self.logger.info("📋 Adding AI-enhanced summary...")
            requests.extend(await self._create_enhanced_summary_requests(enhanced_data))
            
            # Add signature block
            self.logger.info("✍️ Adding signature block...")
            requests.extend(self._create_signature_requests())
            
            # Execute batch update
            if requests:
                self.logger.info(f"📤 Executing {len(requests)} document updates...")
                batch_update_body = {
                    'requests': requests
                }
                
                self.service.documents().batchUpdate(
                    documentId=doc_id,
                    body=batch_update_body
                ).execute()
                
                self.logger.info("✅ Document content added successfully")
            
            # Make document shareable
            self.logger.info("🔓 Making document publicly readable...")
            try:
                if self.drive_service:
                    permission = {
                        'type': 'anyone',
                        'role': 'reader'
                    }
                    self.drive_service.permissions().create(
                        fileId=doc_id,
                        body=permission
                    ).execute()
                    self.logger.info("✅ Document permissions set")
                else:
                    self.logger.warning("⚠️ Drive service not available, document may not be shareable")
            except Exception as perm_error:
                self.logger.warning(f"⚠️ Failed to set document permissions: {perm_error}")
            
            self.logger.info(f"🎉 Google Docs report created successfully: {doc_url}")
            return doc_url
            
        except HttpError as e:
            self.logger.error(f"❌ Google API error: {e}")
            raise Exception(f"Google Docs API error: {e}")
        except Exception as e:
            self.logger.error(f"❌ Failed to create Google Docs report: {e}")
            raise
    
    async def _enhance_report_data_for_docs(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance report data with AI-generated content similar to PDF generator"""
        enhanced_data = report_data.copy()
        
        # Enhanced patient info with chronological age calculation
        patient_info = enhanced_data.get("patient_info", {})
        if patient_info.get("date_of_birth") and patient_info.get("encounter_date"):
            try:
                from datetime import datetime
                dob = datetime.strptime(patient_info["date_of_birth"], "%Y-%m-%d")
                encounter = datetime.strptime(patient_info["encounter_date"], "%Y-%m-%d")
                chron_age = self._calculate_chronological_age(dob, encounter)
                patient_info["chronological_age"] = chron_age
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to calculate chronological age: {e}")
        
        # Generate consolidated narratives using OpenAI (similar to PDF generator)
        self.logger.info("🤖 Generating consolidated AI narratives...")
        enhanced_data["consolidated_narratives"] = await self._generate_consolidated_report_narratives(enhanced_data)
        
        return enhanced_data
    
    def _calculate_chronological_age(self, date_of_birth: datetime, encounter_date: datetime) -> Dict[str, Any]:
        """Calculate chronological age (borrowed from PDF processor logic)"""
        total_days = (encounter_date - date_of_birth).days
        
        years = total_days // 365
        remaining_days = total_days % 365
        months = remaining_days // 30
        days = remaining_days % 30
        
        age_parts = []
        if years > 0:
            age_parts.append(f"{years} year{'s' if years != 1 else ''}")
        if months > 0:
            age_parts.append(f"{months} month{'s' if months != 1 else ''}")
        if days > 0 and years == 0:
            age_parts.append(f"{days} day{'s' if days != 1 else ''}")
        
        formatted = ", ".join(age_parts) if age_parts else "0 days"
        
        return {
            "years": years,
            "months": months,
            "days": days,
            "total_days": total_days,
            "formatted": formatted
        }
    
    async def _generate_consolidated_report_narratives(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate ALL report narratives in a single OpenAI call (same approach as PDF generator)"""
        patient_info = report_data.get("patient_info", {})
        child_name = patient_info.get("name", "the child")
        age = patient_info.get("chronological_age", {}).get("formatted", "unknown age")
        parent_name = patient_info.get("parent_guardian", "The caregiver")
        
        # Extract assessment context
        extracted_data = report_data.get("extracted_data", {})
        assessments = report_data.get("assessments", {})
        
        consolidated_prompt = f"""
        Generate ALL sections for a pediatric OT evaluation report for {child_name} (age: {age}). 
        
        Patient Info: {child_name}, age {age}, caregiver: {parent_name}
        Assessment Data: {assessments}
        
        Generate these EXACT sections with clear section markers:
        
        [BACKGROUND]
        Write 2-3 sentences: "A comprehensive developmental evaluation was recommended to determine {child_name}'s current level of performance across multiple developmental domains..."
        
        [CAREGIVER_CONCERNS]  
        Write 3-4 sentences about {parent_name}'s specific concerns regarding {child_name}'s development, attention, fine motor skills, transitions, feeding, communication, etc.
        
        [OBSERVATIONS]
        Write 6-8 sentences about {child_name}'s clinical presentation including affect, muscle tone, attention span, engagement patterns, response to cues, fine motor coordination, behavioral observations, and impact on testing validity.
        
        [BAYLEY_INTERPRETATION]
        Write detailed Bayley-4 assessment interpretation covering cognitive, language, motor, social-emotional, and adaptive behavior domains with specific clinical analysis.
        
        [SP2_INTERPRETATION]
        Write detailed Sensory Profile 2 interpretation covering sensory processing patterns, quadrant scores, and functional implications.
        
        [FEEDING_INTERPRETATION]
        Write detailed feeding assessment interpretation covering ChOMPS and PediEAT findings, safety considerations, and nutritional concerns.
        
        [FINDINGS_ANALYSIS]
        Write comprehensive analysis covering areas of strength and areas of need with specific examples and clinical reasoning.
        
        [SUMMARY]
        Write comprehensive 6-8 sentence summary covering assessment findings, strengths, needs, intervention recommendations, and family-centered approach.
        
        [RECOMMENDATIONS]
        List 6-8 specific, evidence-based therapy recommendations with frequencies and rationale.
        
        [GOALS]
        List 4-6 specific SMART OT goals with timelines, measurable criteria, and assistance levels.
        
        Use professional clinical language consistent with pediatric OT evaluation reports. Be specific, detailed, and clinically accurate.
        """
        
        try:
            if self.openai_client:
                # Single consolidated OpenAI call
                self.logger.info("🤖 Generating consolidated narratives with OpenAI...")
                consolidated_response = await self._generate_with_openai(consolidated_prompt, max_tokens=3000)
                
                # Parse the response into sections
                sections = {}
                current_section = None
                current_content = []
                
                for line in consolidated_response.split('\n'):
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        # Save previous section
                        if current_section:
                            sections[current_section] = '\n'.join(current_content).strip()
                        # Start new section
                        current_section = line[1:-1].lower()
                        current_content = []
                    elif line and current_section:
                        current_content.append(line)
                
                # Save last section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                self.logger.info(f"✅ Generated {len(sections)} AI-enhanced sections")
                
            else:
                self.logger.warning("⚠️ OpenAI not available, using enhanced fallback content")
                sections = {}
            
            # Provide enhanced fallbacks for missing sections
            fallback_sections = {
                'background': f"A comprehensive developmental evaluation was recommended to determine {child_name}'s current level of performance across multiple developmental domains and to guide evidence-based intervention planning for optimal developmental outcomes.",
                'caregiver_concerns': f"{parent_name} expressed concerns regarding {child_name}'s overall development, including challenges with attention span during structured activities, fine motor coordination, behavioral regulation during transitions, and developmental milestone achievement compared to same-age peers.",
                'observations': f"{child_name} participated in a comprehensive in-clinic evaluation with {parent_name} present. {child_name} presented with variable attention span and required frequent redirection to maintain engagement. Muscle tone appeared within typical limits with adequate range of motion observed. Fine motor coordination demonstrated areas for development, with tasks requiring verbal and visual cues for completion. These factors impacted standardized testing validity and required clinical modifications.",
                'bayley_interpretation': f"The Bayley Scales of Infant and Toddler Development, Fourth Edition revealed a mixed profile of developmental strengths and areas requiring targeted intervention across cognitive, language, motor, social-emotional, and adaptive behavior domains.",
                'sp2_interpretation': f"Sensory Profile 2 assessment indicated variability in sensory processing patterns with implications for daily functional participation and learning.",
                'feeding_interpretation': f"Feeding assessment revealed considerations for oral motor development, swallowing safety, and mealtime participation requiring specialized intervention strategies.",
                'findings_analysis': f"Assessment findings indicate {child_name} demonstrates emerging developmental skills with specific areas requiring targeted therapeutic intervention to support optimal developmental progression.",
                'summary': f"{child_name} (chronological age: {age}) was assessed using standardized pediatric assessment tools revealing both developmental strengths and areas requiring evidence-based intervention. A comprehensive, family-centered approach involving occupational therapy services is recommended to address identified needs and promote optimal developmental outcomes.",
                'recommendations': "• Individual occupational therapy services 2x weekly\n• Sensory integration therapy\n• Fine motor skill development programming\n• Family education and home programming\n• Interdisciplinary team collaboration\n• Environmental modifications\n• Regular progress monitoring and reassessment",
                'goals': "1. Within 6 months, {child_name} will demonstrate improved fine motor coordination by stacking 5 blocks independently in 4/5 opportunities with minimal verbal cues.\n2. Within 6 months, {child_name} will use pincer grasp for manipulation of small objects in 4/5 opportunities during structured activities.\n3. Within 6 months, {child_name} will maintain attention to tabletop activities for 5 minutes in 4/5 opportunities with minimal redirection.\n4. Within 6 months, {child_name} will demonstrate improved bilateral coordination during age-appropriate play activities in 4/5 opportunities."
            }
            
            # Ensure all sections are present
            for section, fallback in fallback_sections.items():
                if section not in sections or not sections[section]:
                    sections[section] = fallback.format(child_name=child_name)
            
            return sections
            
        except Exception as e:
            self.logger.error(f"❌ Consolidated generation failed: {e}")
            # Return enhanced fallbacks
            return {
                'background': f"A comprehensive developmental evaluation was recommended to determine {child_name}'s current level of performance and guide intervention planning.",
                'caregiver_concerns': f"{parent_name} expressed concerns regarding {child_name}'s overall development and functional abilities.",
                'observations': f"{child_name} participated in a comprehensive evaluation demonstrating variable performance across assessed domains.",
                'bayley_interpretation': f"Standardized assessment revealed areas of strength and developmental needs requiring targeted intervention.",
                'summary': f"{child_name} demonstrates a mixed developmental profile requiring evidence-based occupational therapy intervention.",
                'recommendations': "Individual occupational therapy services with family-centered approach recommended.",
                'goals': f"Therapeutic goals focused on promoting {child_name}'s developmental progression and functional independence."
            }
    
    async def _generate_with_openai(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using OpenAI with clinical context (same method as PDF generator)"""
        self.logger.info(f"🤖 Generating text with OpenAI (max_tokens: {max_tokens})")
        
        if not self.openai_client:
            self.logger.warning("⚠️ OpenAI client not available, using fallback")
            return await self._generate_fallback_text(prompt)
        
        # Get configured model
        model = get_openai_model()
        
        try:
            self.logger.info(f"📡 Sending request to OpenAI API with model: {model}...")
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional pediatric occupational therapist writing clinical evaluation reports. Use sophisticated clinical terminology, evidence-based interpretations, and maintain a professional, objective tone. Base your responses on standard pediatric developmental assessments and best practices in occupational therapy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            generated_text = response.choices[0].message.content.strip()
            self.logger.info(f"✅ OpenAI generation successful ({len(generated_text)} characters)")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI generation failed: {e}")
            self.logger.info("🔄 Falling back to enhanced template text")
            return await self._generate_fallback_text(prompt)
    
    async def _generate_fallback_text(self, prompt: str) -> str:
        """Generate enhanced fallback text when OpenAI is not available"""
        self.logger.info("🔄 Generating enhanced fallback content...")
        
        if "background" in prompt.lower():
            return "A comprehensive developmental evaluation was recommended to assess current functional abilities and guide evidence-based intervention planning for optimal developmental outcomes."
        elif "concern" in prompt.lower():
            return "The caregiver expressed concerns regarding overall development, including attention span, fine motor coordination, and behavioral regulation during daily activities."
        elif "observation" in prompt.lower():
            return "The child participated in a comprehensive evaluation demonstrating variable attention span and requiring verbal cues for task completion. Clinical observations indicated areas for therapeutic intervention."
        elif "summary" in prompt.lower():
            return "Assessment findings reveal both developmental strengths and areas requiring targeted intervention through evidence-based occupational therapy services."
        else:
            return "Professional clinical assessment completed with recommendations for evidence-based therapeutic intervention."
    
    def _build_document_content(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Build the document content requests for batch update"""
        requests = []
        
        patient_info = report_data['patient_info']
        assessments = report_data.get('assessments', {})
        
        # Document title and header
        content = []
        
        # Header section
        content.extend([
            "PEDIATRIC OCCUPATIONAL THERAPY EVALUATION REPORT\n\n",
            "FMRC Health Group\n\n",
            f"Client Name: {patient_info.get('name', '')}\n",
            f"Date of Birth: {patient_info.get('date_of_birth', '')}\n",
            f"Chronological Age: {patient_info.get('chronological_age', {}).get('formatted', '')}\n",
            f"UCI Number: {patient_info.get('uci_number', '')}\n",
            f"Sex: {patient_info.get('sex', '')}\n",
            f"Language: {patient_info.get('language', '')}\n",
            f"Parent/Guardian: {patient_info.get('parent_guardian', '')}\n",
            f"Date of Encounter: {patient_info.get('encounter_date', '')}\n",
            f"Date of Report: {patient_info.get('report_date', '')}\n\n"
        ])
        
        # Background Information
        content.extend([
            "BACKGROUND INFORMATION\n\n",
            f"This pediatric occupational therapy evaluation was conducted to assess {patient_info.get('name', 'the client')}'s ",
            "developmental skills and functional abilities across multiple domains. The comprehensive assessment included ",
            "standardized testing using validated pediatric assessment tools to evaluate cognitive, motor, sensory processing, ",
            "feeding, and adaptive behavior skills.\n\n"
        ])
        
        # Assessment Results
        content.append("ASSESSMENT RESULTS\n\n")
        
        # Bayley-4 Results
        if assessments.get('bayley4'):
            content.extend(self._format_bayley4_results(assessments['bayley4']))
        
        # SP2 Results
        if assessments.get('sp2'):
            content.extend(self._format_sp2_results(assessments['sp2']))
        
        # ChOMPS Results
        if assessments.get('chomps'):
            content.extend(self._format_chomps_results(assessments['chomps']))
        
        # PediEAT Results
        if assessments.get('pedieat'):
            content.extend(self._format_pedieat_results(assessments['pedieat']))
        
        # Clinical Observations
        content.extend(self._format_clinical_observations(report_data))
        
        # Findings and Analysis
        content.extend(self._format_findings_analysis(report_data))
        
        # Recommendations
        content.extend(self._format_recommendations(report_data))
        
        # Treatment Goals
        content.extend(self._format_treatment_goals(report_data))
        
        # Summary
        content.extend(self._format_summary(report_data))
        
        # Insert all content
        full_text = ''.join(content)
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': full_text
            }
        })
        
        # Apply formatting
        requests.extend(self._get_formatting_requests(len(full_text)))
        
        return requests
    
    def _format_bayley4_results(self, bayley_data: Dict[str, Any]) -> List[str]:
        """Format Bayley-4 assessment results"""
        content = ["Bayley Scales of Infant and Toddler Development, Fourth Edition (Bayley-4)\n\n"]
        
        # Composite scores
        if bayley_data.get('composite_scores'):
            content.append("Composite Scores:\n")
            for composite, score in bayley_data['composite_scores'].items():
                interpretation = bayley_data.get('interpretations', {}).get(composite, {})
                classification = interpretation.get('classification', 'Not available')
                percentile = interpretation.get('percentile', 'Not available')
                
                content.append(f"• {composite}: {score} ({classification}, {percentile}th percentile)\n")
            content.append("\n")
        
        # Domain scores
        if bayley_data.get('raw_scores') or bayley_data.get('scaled_scores'):
            content.append("Domain Scores:\n")
            raw_scores = bayley_data.get('raw_scores', {})
            scaled_scores = bayley_data.get('scaled_scores', {})
            age_equivalents = bayley_data.get('age_equivalents', {})
            
            for domain in raw_scores.keys():
                raw = raw_scores.get(domain, 'N/A')
                scaled = scaled_scores.get(domain, 'N/A')
                age_eq = age_equivalents.get(domain, 'N/A')
                content.append(f"• {domain}: Raw Score {raw}, Scaled Score {scaled}, Age Equivalent {age_eq}\n")
            content.append("\n")
        
        return content
    
    def _format_sp2_results(self, sp2_data: Dict[str, Any]) -> List[str]:
        """Format Sensory Profile 2 results"""
        content = ["Sensory Profile 2 (SP2)\n\n"]
        
        if sp2_data.get('quadrant_scores'):
            content.append("Sensory Processing Quadrants:\n")
            for quadrant, data in sp2_data['quadrant_scores'].items():
                score = data.get('raw_score', 'N/A')
                classification = data.get('classification', 'N/A')
                interpretation = data.get('interpretation', '')
                
                content.append(f"• {quadrant}: {score} ({classification})\n")
                if interpretation:
                    content.append(f"  {interpretation}\n")
            content.append("\n")
        
        if sp2_data.get('clinical_implications'):
            content.append("Clinical Implications:\n")
            for implication in sp2_data['clinical_implications']:
                content.append(f"• {implication}\n")
            content.append("\n")
        
        return content
    
    def _format_chomps_results(self, chomps_data: Dict[str, Any]) -> List[str]:
        """Format ChOMPS feeding assessment results"""
        content = ["Chicago Oral Motor and Feeding Assessment (ChOMPS)\n\n"]
        
        if chomps_data.get('domain_scores'):
            content.append("Domain Scores and Risk Levels:\n")
            domain_scores = chomps_data.get('domain_scores', {})
            risk_levels = chomps_data.get('risk_levels', {})
            
            for domain, score in domain_scores.items():
                risk = risk_levels.get(domain, 'N/A')
                content.append(f"• {domain}: Score {score} ({risk} Risk)\n")
            content.append("\n")
        
        if chomps_data.get('feeding_concerns'):
            content.append("Feeding Concerns:\n")
            for concern in chomps_data['feeding_concerns']:
                content.append(f"• {concern}\n")
            content.append("\n")
        
        if chomps_data.get('safety_issues'):
            content.append("Safety Considerations:\n")
            for safety in chomps_data['safety_issues']:
                content.append(f"• {safety}\n")
            content.append("\n")
        
        return content
    
    def _format_pedieat_results(self, pedieat_data: Dict[str, Any]) -> List[str]:
        """Format PediEAT assessment results"""
        content = ["Pediatric Eating Assessment Tool (PediEAT)\n\n"]
        
        if pedieat_data.get('domain_scores'):
            content.append("Domain T-Scores:\n")
            domain_scores = pedieat_data.get('domain_scores', {})
            symptom_levels = pedieat_data.get('symptom_levels', {})
            
            for domain, score in domain_scores.items():
                level = symptom_levels.get(domain, '')
                content.append(f"• {domain}: T-Score {score} {level}\n")
            content.append("\n")
        
        return content
    
    def _format_clinical_observations(self, report_data: Dict[str, Any]) -> List[str]:
        """Format clinical observations section"""
        content = ["CLINICAL OBSERVATIONS\n\n"]
        
        # Process clinical notes if available
        clinical_notes = report_data.get('assessments', {}).get('clinical_notes', {})
        
        if clinical_notes.get('converted_narratives'):
            content.append("Behavioral and Performance Observations:\n")
            for narrative in clinical_notes['converted_narratives']:
                content.append(f"• {narrative}\n")
            content.append("\n")
        
        # Add general observations
        patient_name = report_data['patient_info'].get('name', 'The client')
        content.extend([
            f"During the assessment, {patient_name} demonstrated varying levels of engagement and cooperation. ",
            "The following observations were noted across assessment activities:\n\n",
            
            "Attention and Focus:\n",
            "• Attention span and sustained focus during structured tasks\n",
            "• Response to verbal and visual cues from examiner\n",
            "• Distractibility and environmental awareness\n\n",
            
            "Motor Performance:\n",
            "• Gross motor coordination, balance, and postural control\n",
            "• Fine motor precision, bilateral coordination, and tool use\n",
            "• Visual-motor integration and planning abilities\n\n",
            
            "Social-Emotional Regulation:\n",
            "• Emotional responses and self-regulation strategies\n",
            "• Social interaction patterns with examiner\n",
            "• Adaptation to task demands and transitions\n\n"
        ])
        
        return content
    
    def _format_findings_analysis(self, report_data: Dict[str, Any]) -> List[str]:
        """Format findings and analysis section"""
        content = ["FINDINGS AND ANALYSIS\n\n"]
        
        # Collect strengths from all assessments
        all_strengths = []
        all_needs = []
        
        for assessment_type, data in report_data.get('assessments', {}).items():
            if isinstance(data, dict):
                all_strengths.extend(data.get('strengths', []))
                all_needs.extend(data.get('needs', []))
        
        # Areas of Strength
        content.append("Areas of Strength:\n")
        if all_strengths:
            for strength in all_strengths:
                content.append(f"• {strength}\n")
        else:
            content.extend([
                "• Demonstrates age-appropriate visual attention and engagement\n",
                "• Shows interest in social interaction with familiar adults\n",
                "• Exhibits appropriate emotional responses to routine activities\n",
                "• Demonstrates emerging problem-solving strategies\n"
            ])
        content.append("\n")
        
        # Areas of Need
        content.append("Areas of Need:\n")
        if all_needs:
            for need in all_needs:
                content.append(f"• {need}\n")
        else:
            content.extend([
                "• Fine motor coordination and precision skills\n",
                "• Gross motor balance and postural control\n",
                "• Sensory processing and modulation strategies\n",
                "• Adaptive behavior skills for daily activities\n"
            ])
        content.append("\n")
        
        return content
    
    def _format_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Format recommendations section"""
        content = ["RECOMMENDATIONS\n\n"]
        
        # Collect recommendations from all assessments
        all_recommendations = []
        for assessment_type, data in report_data.get('assessments', {}).items():
            if isinstance(data, dict):
                all_recommendations.extend(data.get('recommendations', []))
        
        if not all_recommendations:
            all_recommendations = [
                "Individual occupational therapy services to address identified areas of need",
                "Sensory integration therapy to support sensory processing challenges",
                "Fine motor skill development through structured play activities",
                "Feeding therapy to address oral motor and swallowing concerns",
                "Parent education and training for home-based intervention strategies",
                "Environmental modifications to support optimal development",
                "Interdisciplinary team collaboration for comprehensive care",
                "Regular reassessment to monitor progress and adjust interventions"
            ]
        
        for i, recommendation in enumerate(all_recommendations, 1):
            content.append(f"{i}. {recommendation}\n")
        content.append("\n")
        
        return content
    
    def _format_treatment_goals(self, report_data: Dict[str, Any]) -> List[str]:
        """Format treatment goals section"""
        content = ["TREATMENT GOALS\n\n"]
        
        patient_name = report_data['patient_info'].get('name', 'the client')
        
        content.extend([
            f"The following treatment goals are recommended for {patient_name} based on assessment findings:\n\n",
            
            "Short-term Goals (3-6 months):\n",
            "• Improve fine motor coordination for age-appropriate manipulation tasks\n",
            "• Enhance gross motor skills including balance and postural stability\n",
            "• Develop sensory processing and self-regulation strategies\n",
            "• Increase attention span and task engagement\n",
            "• Support feeding skills and oral motor development\n\n",
            
            "Long-term Goals (6-12 months):\n",
            "• Achieve developmental milestones across all assessed domains\n",
            "• Demonstrate independence in age-appropriate daily living activities\n",
            "• Exhibit functional sensory processing in various environments\n",
            "• Show improved self-regulation and coping strategies\n",
            "• Participate successfully in family and community activities\n\n"
        ])
        
        return content
    
    def _format_summary(self, report_data: Dict[str, Any]) -> List[str]:
        """Format summary section"""
        content = ["SUMMARY\n\n"]
        
        patient_name = report_data['patient_info'].get('name', 'The client')
        chronological_age = report_data['patient_info'].get('chronological_age', {}).get('formatted', '')
        
        content.extend([
            f"{patient_name} (chronological age: {chronological_age}) was assessed using multiple standardized ",
            "pediatric assessment tools to evaluate developmental functioning across cognitive, motor, sensory processing, ",
            "feeding, and adaptive behavior domains. The comprehensive evaluation revealed both areas of strength ",
            "and areas requiring targeted intervention support.\n\n",
            
            "Based on the assessment findings, occupational therapy services are recommended to address identified ",
            "areas of need and support optimal developmental progression. A collaborative, family-centered approach ",
            "involving occupational therapy and related services will be beneficial to address the client's ",
            "comprehensive developmental needs.\n\n",
            
            "Regular monitoring and reassessment will be important to track progress and adjust intervention ",
            "strategies as needed. Family involvement and education will be crucial components of the intervention ",
            "plan to ensure carryover of skills into daily routines and activities.\n\n",
            
            "This assessment provides a foundation for developing an individualized intervention plan that addresses ",
            "the client's unique profile of strengths and needs while promoting optimal developmental outcomes.\n\n",
            
            "_________________________________\n",
            "Occupational Therapist\n",
            "FMRC Health Group\n",
            f"Date: {datetime.now().strftime('%B %d, %Y')}\n"
        ])
        
        return content
    
    def _get_formatting_requests(self, text_length: int) -> List[Dict]:
        """Get formatting requests for the document"""
        requests = []
        
        # Title formatting (first line)
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': 1, 'endIndex': 50},
                'textStyle': {
                    'bold': True,
                    'fontSize': {'magnitude': 16, 'unit': 'PT'}
                },
                'fields': 'bold,fontSize'
            }
        })
        
        return requests
    
    def _make_document_shareable(self, doc_id: str) -> str:
        """Make the document shareable and return the URL"""
        try:
            # Make document publicly viewable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.drive_service.permissions().create(
                fileId=doc_id,
                body=permission
            ).execute()
            
            return f"https://docs.google.com/document/d/{doc_id}/edit"
            
        except Exception as e:
            self.logger.error(f"Error making document shareable: {e}")
            return f"https://docs.google.com/document/d/{doc_id}/edit"
    
    async def _create_text_fallback(self, report_data: Dict[str, Any], session_id: str) -> str:
        """Create a text file fallback when Google Docs is not available"""
        output_path = os.path.join("outputs", f"ot_report_text_{session_id}.txt")
        
        try:
            # Build content similar to Google Docs format
            content = []
            content.extend(self._build_text_content(report_data))
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(content))
            
            self.logger.info(f"Text fallback report created: {output_path}")
            return f"/download-text/{session_id}"
            
        except Exception as e:
            self.logger.error(f"Error creating text fallback: {e}")
            return ""
    
    def _build_text_content(self, report_data: Dict[str, Any]) -> List[str]:
        """Build text content for fallback report"""
        content = []
        
        # Use same formatting methods but for plain text
        content.extend([
            "PEDIATRIC OCCUPATIONAL THERAPY EVALUATION REPORT\n",
            "=" * 50 + "\n\n"
        ])
        
        patient_info = report_data['patient_info']
        content.extend([
            f"Client Name: {patient_info.get('name', '')}\n",
            f"Date of Birth: {patient_info.get('date_of_birth', '')}\n",
            f"Chronological Age: {patient_info.get('chronological_age', {}).get('formatted', '')}\n",
            f"Date of Report: {patient_info.get('report_date', '')}\n\n"
        ])
        
        # Add all other sections using the same methods
        content.extend(self._format_bayley4_results(report_data.get('assessments', {}).get('bayley4', {})))
        content.extend(self._format_clinical_observations(report_data))
        content.extend(self._format_findings_analysis(report_data))
        content.extend(self._format_recommendations(report_data))
        content.extend(self._format_summary(report_data))
        
        return content
    
    def _create_header_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create header section requests for Google Docs"""
        requests = []
        patient_info = report_data['patient_info']
        
        # Header content
        header_text = f"""PEDIATRIC OCCUPATIONAL THERAPY EVALUATION REPORT

FMRC Health Group

Client Name: {patient_info.get('name', '')}
Date of Birth: {patient_info.get('date_of_birth', '')}
Chronological Age: {patient_info.get('chronological_age', {}).get('formatted', '')}
UCI Number: {patient_info.get('uci_number', '')}
Sex: {patient_info.get('sex', '')}
Language: {patient_info.get('language', '')}
Parent/Guardian: {patient_info.get('parent_guardian', '')}
Date of Encounter: {patient_info.get('encounter_date', '')}
Date of Report: {patient_info.get('report_date', '')}

"""
        
        # Insert header text
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': header_text
            }
        })
        
        return requests
    
    def _create_patient_info_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create patient information section requests"""
        requests = []
        patient_info = report_data['patient_info']
        
        info_text = f"""PATIENT INFORMATION

Name: {patient_info.get('name', '')}
Date of Birth: {patient_info.get('date_of_birth', '')}
Age: {patient_info.get('chronological_age', {}).get('formatted', '')}
Parent/Guardian: {patient_info.get('parent_guardian', '')}
UCI Number: {patient_info.get('uci_number', '')}

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': info_text
            }
        })
        
        return requests
    
    def _create_background_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create background section requests"""
        requests = []
        patient_name = report_data['patient_info'].get('name', 'the client')
        
        background_text = f"""BACKGROUND INFORMATION

This pediatric occupational therapy evaluation was conducted to assess {patient_name}'s developmental skills and functional abilities across multiple domains. The comprehensive assessment included standardized testing using validated pediatric assessment tools to evaluate cognitive, motor, sensory processing, feeding, and adaptive behavior skills.

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': background_text
            }
        })
        
        return requests
    
    def _create_assessment_results_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create assessment results section requests"""
        requests = []
        assessments = report_data.get('assessments', {})
        
        results_text = "ASSESSMENT RESULTS\n\n"
        
        # Add Bayley-4 results if available
        if assessments.get('bayley4'):
            bayley_content = self._format_bayley4_results(assessments['bayley4'])
            results_text += ''.join(bayley_content)
        
        # Add SP2 results if available
        if assessments.get('sp2'):
            sp2_content = self._format_sp2_results(assessments['sp2'])
            results_text += ''.join(sp2_content)
        
        # Add ChOMPS results if available
        if assessments.get('chomps'):
            chomps_content = self._format_chomps_results(assessments['chomps'])
            results_text += ''.join(chomps_content)
        
        # Add PediEAT results if available
        if assessments.get('pedieat'):
            pedieat_content = self._format_pedieat_results(assessments['pedieat'])
            results_text += ''.join(pedieat_content)
        
        # Add clinical observations
        clinical_content = self._format_clinical_observations(report_data)
        results_text += ''.join(clinical_content)
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': results_text
            }
        })
        
        return requests
    
    def _create_recommendations_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create recommendations section requests"""
        requests = []
        
        recommendations_content = self._format_recommendations(report_data)
        recommendations_text = ''.join(recommendations_content)
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': recommendations_text
            }
        })
        
        return requests
    
    def _create_goals_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create treatment goals section requests"""
        requests = []
        
        goals_content = self._format_treatment_goals(report_data)
        goals_text = ''.join(goals_content)
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': goals_text
            }
        })
        
        return requests
    
    def _create_signature_requests(self) -> List[Dict]:
        """Create signature block requests"""
        requests = []
        
        signature_text = f"""
_________________________________
Occupational Therapist
FMRC Health Group
Date: {datetime.now().strftime('%B %d, %Y')}
"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': signature_text
            }
        })
        
        return requests
    
    async def _create_enhanced_background_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced background section using AI-generated content"""
        requests = []
        
        # Get AI-generated background narrative
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        background_text = consolidated_narratives.get("background", "")
        
        if not background_text:
            background_text = "A comprehensive developmental evaluation was recommended to assess current functional abilities and guide evidence-based intervention planning."
        
        background_content = f"""BACKGROUND INFORMATION

{background_text}

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': background_content
            }
        })
        
        return requests
    
    async def _create_enhanced_caregiver_concerns_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced caregiver concerns section using AI-generated content"""
        requests = []
        
        # Get AI-generated caregiver concerns narrative
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        concerns_text = consolidated_narratives.get("caregiver_concerns", "")
        
        if not concerns_text:
            parent_name = report_data.get("patient_info", {}).get("parent_guardian", "The caregiver")
            child_name = report_data.get("patient_info", {}).get("name", "the child")
            concerns_text = f"{parent_name} expressed concerns regarding {child_name}'s overall development and functional abilities."
        
        concerns_content = f"""CAREGIVER CONCERNS

{concerns_text}

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': concerns_content
            }
        })
        
        return requests
    
    async def _create_enhanced_clinical_observations_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced clinical observations section using AI-generated content"""
        requests = []
        
        # Get AI-generated observations narrative
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        observations_text = consolidated_narratives.get("observations", "")
        
        if not observations_text:
            child_name = report_data.get("patient_info", {}).get("name", "The child")
            observations_text = f"{child_name} participated in a comprehensive evaluation demonstrating variable attention span and requiring verbal cues for task completion."
        
        observations_content = f"""CLINICAL OBSERVATIONS

{observations_text}

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': observations_content
            }
        })
        
        return requests
    
    async def _create_enhanced_assessment_results_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced assessment results section using AI-generated content"""
        requests = []
        
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        
        # Build comprehensive assessment results section
        results_content = "ASSESSMENT RESULTS\n\n"
        
        # Bayley-4 Interpretation
        bayley_interpretation = consolidated_narratives.get("bayley_interpretation", "")
        if bayley_interpretation:
            results_content += f"Bayley Scales of Infant and Toddler Development, Fourth Edition (Bayley-4)\n\n{bayley_interpretation}\n\n"
        
        # Sensory Profile 2 Interpretation
        sp2_interpretation = consolidated_narratives.get("sp2_interpretation", "")
        if sp2_interpretation:
            results_content += f"Sensory Profile 2 (SP2)\n\n{sp2_interpretation}\n\n"
        
        # Feeding Assessment Interpretation
        feeding_interpretation = consolidated_narratives.get("feeding_interpretation", "")
        if feeding_interpretation:
            results_content += f"Feeding Assessment\n\n{feeding_interpretation}\n\n"
        
        # Findings and Analysis
        findings_analysis = consolidated_narratives.get("findings_analysis", "")
        if findings_analysis:
            results_content += f"FINDINGS AND ANALYSIS\n\n{findings_analysis}\n\n"
        
        # If no AI content available, use enhanced fallback
        if len(results_content) < 50:
            assessments = report_data.get("assessments", {})
            results_content = "ASSESSMENT RESULTS\n\n"
            
            if assessments.get("bayley4"):
                results_content += "Bayley Scales of Infant and Toddler Development, Fourth Edition revealed a mixed profile of developmental strengths and areas requiring targeted intervention.\n\n"
            
            if assessments.get("sp2"):
                results_content += "Sensory Profile 2 assessment indicated variability in sensory processing patterns with implications for functional participation.\n\n"
            
            if assessments.get("chomps") or assessments.get("pedieat"):
                results_content += "Feeding assessment revealed considerations for oral motor development and mealtime participation.\n\n"
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': results_content
            }
        })
        
        return requests
    
    async def _create_enhanced_recommendations_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced recommendations section using AI-generated content"""
        requests = []
        
        # Get AI-generated recommendations
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        recommendations_text = consolidated_narratives.get("recommendations", "")
        
        if not recommendations_text:
            recommendations_text = """• Individual occupational therapy services 2x weekly
• Sensory integration therapy
• Fine motor skill development programming
• Family education and home programming
• Interdisciplinary team collaboration
• Environmental modifications
• Regular progress monitoring and reassessment"""
        
        recommendations_content = f"""RECOMMENDATIONS

Based on the comprehensive assessment findings, the following evidence-based recommendations are provided:

{recommendations_text}

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': recommendations_content
            }
        })
        
        return requests
    
    async def _create_enhanced_goals_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced treatment goals section using AI-generated content"""
        requests = []
        
        # Get AI-generated goals
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        goals_text = consolidated_narratives.get("goals", "")
        
        if not goals_text:
            child_name = report_data.get("patient_info", {}).get("name", "the child")
            goals_text = f"""1. Within 6 months, {child_name} will demonstrate improved fine motor coordination by stacking 5 blocks independently in 4/5 opportunities with minimal verbal cues.
2. Within 6 months, {child_name} will use pincer grasp for manipulation of small objects in 4/5 opportunities during structured activities.
3. Within 6 months, {child_name} will maintain attention to tabletop activities for 5 minutes in 4/5 opportunities with minimal redirection.
4. Within 6 months, {child_name} will demonstrate improved bilateral coordination during age-appropriate play activities in 4/5 opportunities."""
        
        patient_name = report_data.get("patient_info", {}).get("name", "the client")
        
        goals_content = f"""TREATMENT GOALS

The following evidence-based treatment goals are recommended for {patient_name}:

{goals_text}

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': goals_content
            }
        })
        
        return requests
    
    async def _create_enhanced_summary_requests(self, report_data: Dict[str, Any]) -> List[Dict]:
        """Create enhanced summary section using AI-generated content"""
        requests = []
        
        # Get AI-generated summary
        consolidated_narratives = report_data.get("consolidated_narratives", {})
        summary_text = consolidated_narratives.get("summary", "")
        
        if not summary_text:
            child_name = report_data.get("patient_info", {}).get("name", "the child")
            age = report_data.get("patient_info", {}).get("chronological_age", {}).get("formatted", "unknown age")
            summary_text = f"{child_name} (chronological age: {age}) was assessed using standardized pediatric assessment tools revealing both developmental strengths and areas requiring evidence-based intervention. A comprehensive, family-centered approach involving occupational therapy services is recommended to address identified needs and promote optimal developmental outcomes."
        
        summary_content = f"""SUMMARY

{summary_text}

This assessment provides a foundation for developing an individualized intervention plan that addresses the client's unique profile of strengths and needs while promoting optimal developmental outcomes through evidence-based occupational therapy services.

"""
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': summary_content
            }
        })
        
        return requests 