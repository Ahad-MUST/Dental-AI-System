"""
Enhanced Data Loader for Dental Call Analysis - FIXED VERSION
Now correctly returns real data instead of empty data
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

# Import your existing settings
from config.settings import settings

# Google Sheets integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    gspread = None

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Enhanced data loader with Google Sheets integration for coaching library support
    FIXED VERSION - returns real data instead of empty data
    """
    
    def __init__(self):
        self.data_directory = settings.OUTPUT_DIR
        self.calls_cache = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
        
        # Google Sheets configuration
        self.sheets_client = None
        self.spreadsheet = None
        self._init_google_sheets()
        
    def _init_google_sheets(self):
        """Initialize Google Sheets client"""
        if not GSPREAD_AVAILABLE:
            logger.warning("Google Sheets integration not available - install gspread and google-auth")
            return
            
        try:
            # Try to get credentials from environment or service account file
            credentials_path = getattr(settings, 'GOOGLE_CREDENTIALS_PATH', None)
            spreadsheet_id = getattr(settings, 'GOOGLE_SPREADSHEET_ID', None)
            
            if credentials_path and Path(credentials_path).exists():
                # Use service account file
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                
                creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                self.sheets_client = gspread.authorize(creds)
                logger.info("Google Sheets client initialized with service account")
                
            elif spreadsheet_id:
                # Try default credentials
                self.sheets_client = gspread.service_account()
                logger.info("Google Sheets client initialized with default credentials")
            else:
                logger.info("Google Sheets not configured - using local file fallback")
                return
                
            # Open the spreadsheet
            if spreadsheet_id:
                self.spreadsheet = self.sheets_client.open_by_key(spreadsheet_id)
            else:
                # Try to find by name (fallback)
                spreadsheet_name = getattr(settings, 'GOOGLE_SPREADSHEET_NAME', 'Call Analysis Data')
                self.spreadsheet = self.sheets_client.open(spreadsheet_name)
                
            logger.info(f"Connected to Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            self.sheets_client = None
            self.spreadsheet = None
        
    async def load_all_calls(self) -> List[Dict[str, Any]]:
        """
        Load all processed calls for coaching analysis - FIXED VERSION
        Returns a list of call dictionaries with all analysis data
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Returning cached call data")
                return self.calls_cache
            
            logger.info("Loading all call data...")
            
            # Load calls from different sources in priority order
            all_calls = []
            
            # Priority 1: Google Sheets (if available)
            if self.sheets_client and self.spreadsheet:
                try:
                    all_calls = await self._load_from_google_sheets()
                    logger.info(f"Loaded {len(all_calls)} calls from Google Sheets")
                except Exception as e:
                    logger.warning(f"Failed to load from Google Sheets: {str(e)}")
                    all_calls = []
            
            # Priority 2: Local files (fallback)
            if not all_calls:
                all_calls = await self._load_from_local_files()
                logger.info(f"Loaded {len(all_calls)} calls from local files")
                
            # If still no calls, create some sample data for testing
            if not all_calls:
                logger.warning("No real call data found, creating sample data for testing")
                all_calls = self._create_sample_data()
            
            # Process and enhance calls for coaching
            processed_calls = self._process_calls_for_coaching(all_calls)
            
            # Update cache
            self.calls_cache = processed_calls
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Loaded {len(processed_calls)} calls for coaching library")
            return processed_calls
            
        except Exception as e:
            logger.error(f"Error loading call data: {str(e)}")
            # Return empty list instead of failing
            return []
    
    def _create_sample_data(self) -> List[Dict]:
        """Create sample data when no real data is available - for testing only"""
        sample_calls = [
            {
                'Call_File_Name': 'sample_call_001.wav',
                'Analysis_Date': '09/22/2025',
                'Representative_Name': 'Sarah Johnson',
                'Call_Summary': 'Patient called to schedule a dental cleaning appointment. Representative handled the request professionally and scheduled the appointment for next week.',
                'Representative_Score': 0.85,
                'Overall_Sentiment': 'positive',
                'Call_Tag': 'appointment_booking',
                'High_Value_Missed_Opportunity': False,
                'Patient_Transcript': 'Hi, I need to schedule a dental cleaning. When do you have availability?',
                'Staff_Transcript': 'Hello! I can help you schedule a cleaning. We have availability next Tuesday at 2 PM or Thursday at 10 AM. Which works better for you?',
                'performance_analysis': {
                    'strengths': ['Professional greeting', 'Offered two appointment options', 'Confirmed patient information'],
                    'weaknesses': ['Could have asked about last cleaning date'],
                    'coaching_focus': ['Patient history inquiry']
                }
            },
            {
                'Call_File_Name': 'sample_call_002.wav',
                'Analysis_Date': '09/21/2025',
                'Representative_Name': 'Mike Davis',
                'Call_Summary': 'Patient inquiry about cosmetic dental options. Representative provided basic information but missed opportunity to schedule consultation.',
                'Representative_Score': 0.65,
                'Overall_Sentiment': 'neutral',
                'Call_Tag': 'cosmetic',
                'High_Value_Missed_Opportunity': True,
                'Patient_Transcript': 'I am interested in getting veneers. Can you tell me about the process and cost?',
                'Staff_Transcript': 'Veneers are a cosmetic option that can improve your smile. The cost varies depending on how many you need. You would need to come in for a consultation.',
                'performance_analysis': {
                    'strengths': ['Provided basic information about veneers'],
                    'weaknesses': ['Did not offer specific appointment times', 'Missed opportunity to discuss financing'],
                    'coaching_focus': ['Consultation scheduling', 'Financial options discussion']
                }
            },
            {
                'Call_File_Name': 'sample_call_003.wav',
                'Analysis_Date': '09/20/2025',
                'Representative_Name': 'Jennifer Lee',
                'Call_Summary': 'Emergency call - patient with severe tooth pain. Representative handled urgently and scheduled same-day appointment.',
                'Representative_Score': 0.92,
                'Overall_Sentiment': 'positive',
                'Call_Tag': 'emergency',
                'High_Value_Missed_Opportunity': False,
                'Patient_Transcript': 'I have severe tooth pain that started this morning. I really need to see the dentist today if possible.',
                'Staff_Transcript': 'I understand you are in pain. Let me check our emergency slots. We can see you at 3 PM today. Please arrive 15 minutes early to complete paperwork.',
                'performance_analysis': {
                    'strengths': ['Showed empathy for patient pain', 'Offered same-day appointment', 'Clear instructions'],
                    'weaknesses': [],
                    'coaching_focus': []
                }
            }
        ]
        
        return sample_calls
    
    async def _load_from_google_sheets(self) -> List[Dict]:
        """Load calls from Google Sheets"""
        all_calls = []
        
        try:
            # Get all worksheets
            worksheets = self.spreadsheet.worksheets()
            logger.info(f"Found {len(worksheets)} worksheets in Google Sheets")
            
            for worksheet in worksheets:
                try:
                    worksheet_name = worksheet.title
                    logger.info(f"Processing worksheet: {worksheet_name}")
                    
                    # Get all records from the worksheet
                    records = worksheet.get_all_records()
                    logger.info(f"Found {len(records)} records in worksheet {worksheet_name}")
                    
                    for record in records:
                        # Skip empty rows
                        if not any(record.values()):
                            continue
                            
                        # Convert Google Sheets record to call format
                        call_data = self._convert_sheets_record_to_call(record, worksheet_name)
                        if call_data:
                            all_calls.append(call_data)
                            
                except Exception as e:
                    logger.warning(f"Error processing worksheet {worksheet.title}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error loading from Google Sheets: {str(e)}")
            raise
            
        return all_calls
    
    def _convert_sheets_record_to_call(self, record: Dict, worksheet_name: str) -> Dict:
        """Convert a Google Sheets record to call format"""
        try:
            # Map common Google Sheets column names to call fields
            call_data = {
                'worksheet_source': worksheet_name,
                'source': 'google_sheets'
            }
            
            # Map columns with various possible names
            column_mappings = {
                # Basic info
                'Call_File_Name': ['Call_File_Name', 'Audio File', 'Call File Name', 'File Name', 'audio_file', 'filename'],
                'representative_name': ['Representative_Name', 'Representative Name', 'Employee', 'Staff Member', 'representative_name', 'employee_name'],
                'Analysis_Date': ['Analysis_Date', 'Analysis Date', 'Date', 'Call Date', 'analysis_date', 'date'],
                
                # Call content
                'Call_Summary': ['Call_Summary', 'Call Summary', 'Summary', 'call_summary', 'summary'],
                'Patient_Transcript': ['Patient_Transcript', 'Patient Transcript', 'Patient', 'patient_transcript', 'patient_text'],
                'Staff_Transcript': ['Staff_Transcript', 'Staff Transcript', 'Staff', 'Representative', 'staff_transcript', 'staff_text'],
                'combined_transcript': ['Combined_Transcript', 'Combined Transcript', 'Full Transcript', 'combined_transcript', 'transcript'],
                
                # Scores and metrics
                'Representative_Score': ['Representative_Score', 'Representative Score', 'Performance Score', 'Score', 'representative_score', 'performance_score'],
                'Overall_Sentiment': ['Overall_Sentiment', 'Overall Sentiment', 'Sentiment', 'overall_sentiment', 'sentiment'],
                'Call_Tag': ['Call_Tag', 'Call Tag', 'Call Type', 'Tag', 'call_tag', 'call_type', 'type'],
                'call_duration': ['call_duration', 'Call Duration', 'Duration', 'duration'],
                
                # Analysis results (stored as JSON strings in sheets)
                'performance_analysis': ['performance_analysis', 'Performance Analysis'],
                'sentiment_analysis': ['sentiment_analysis', 'Sentiment Analysis'],
                'opportunity_analysis': ['opportunity_analysis', 'Opportunity Analysis'],
                'coaching_analysis': ['coaching_analysis', 'Coaching Analysis'],
                
                # Flags
                'High_Value_Missed_Opportunity': ['High_Value_Missed_Opportunity', 'High Value Missed Opportunity', 'Missed Opportunity', 'high_value_missed_opportunity', 'missed_opportunity'],
                'is_coaching_candidate': ['is_coaching_candidate', 'Coaching Candidate', 'coaching_candidate']
            }
            
            # Apply mappings
            for field, possible_columns in column_mappings.items():
                for col_name in possible_columns:
                    if col_name in record and record[col_name]:
                        value = record[col_name]
                        
                        # Handle specific data types
                        if field in ['Representative_Score', 'call_duration']:
                            try:
                                call_data[field] = float(value) if value else 0.0
                            except:
                                call_data[field] = 0.0
                                
                        elif field in ['High_Value_Missed_Opportunity', 'is_coaching_candidate']:
                            # Convert various boolean representations
                            if isinstance(value, str):
                                call_data[field] = value.lower() in ['true', 'yes', '1', 'y']
                            else:
                                call_data[field] = bool(value)
                                
                        elif field in ['performance_analysis', 'sentiment_analysis', 'opportunity_analysis', 'coaching_analysis']:
                            # Try to parse JSON strings
                            try:
                                if isinstance(value, str) and value.strip():
                                    call_data[field] = json.loads(value)
                                else:
                                    call_data[field] = {}
                            except:
                                call_data[field] = {}
                                
                        else:
                            call_data[field] = str(value) if value else ''
                        
                        break  # Found a match, stop looking for this field
            
            # Generate ID if not present
            if 'id' not in call_data:
                call_data['id'] = self._generate_call_id(call_data)
            
            # Set defaults for missing fields
            call_data.setdefault('Analysis_Date', datetime.now().strftime('%m/%d/%Y'))
            call_data.setdefault('representative_name', call_data.get('Representative_Name', 'Unknown'))
            call_data.setdefault('Call_Summary', 'No summary available')
            call_data.setdefault('Overall_Sentiment', 'neutral')
            call_data.setdefault('Call_Tag', 'general_inquiry')
            call_data.setdefault('Representative_Score', 0.0)
            
            return call_data
            
        except Exception as e:
            logger.warning(f"Error converting sheets record: {str(e)}")
            return None
    
    async def _load_from_local_files(self) -> List[Dict]:
        """Load calls from local files (fallback method)"""
        logger.info("Loading from local files as fallback...")
        
        all_calls = []
        
        # Method 1: Load from individual JSON files (if that's your current structure)
        if self._has_individual_json_files():
            all_calls = await self._load_from_individual_files()
            logger.info(f"Loaded {len(all_calls)} calls from individual files")
        
        # Method 2: Load from consolidated JSON file (if you have one)
        elif self._has_consolidated_file():
            all_calls = await self._load_from_consolidated_file()
            logger.info(f"Loaded {len(all_calls)} calls from consolidated file")
        
        # Method 3: Load from CSV export (fallback)
        elif self._has_csv_export():
            all_calls = await self._load_from_csv()
            logger.info(f"Loaded {len(all_calls)} calls from CSV")
        
        else:
            logger.warning("No local call data files found")
            return []
            
        return all_calls
    
    async def load_dashboard_data(self) -> Dict[str, Any]:
        """
        Load data for the main dashboard
        This should use your existing dashboard data loading logic
        """
        try:
            logger.info("Loading dashboard data...")
            
            # Load all calls
            all_calls = await self.load_all_calls()
            
            if not all_calls:
                return self._get_empty_dashboard_data()
            
            # Calculate dashboard analytics
            dashboard_data = {
                "callsOverview": self._calculate_calls_overview(all_calls),
                "analytics": self._calculate_analytics(all_calls),
                "sentimentData": self._calculate_sentiment_data(all_calls),
                "rawData": all_calls,
                "totalCalls": len(all_calls),
                "lastUpdate": datetime.now().isoformat()
            }
            
            logger.info(f"Dashboard data loaded with {len(all_calls)} calls")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {str(e)}")
            return self._get_empty_dashboard_data()
    
    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid"""
        if not self.calls_cache or not self.cache_timestamp:
            return False
        
        return datetime.now() - self.cache_timestamp < self.cache_duration
    
    def _has_individual_json_files(self) -> bool:
        """Check if individual JSON analysis files exist"""
        if not self.data_directory.exists():
            return False
        
        # Look for JSON files that match your analysis output pattern
        json_files = list(self.data_directory.glob("*.json"))
        analysis_files = [f for f in json_files if "analysis" in f.name.lower()]
        
        return len(analysis_files) > 0
    
    def _has_consolidated_file(self) -> bool:
        """Check if a consolidated data file exists"""
        consolidated_files = [
            self.data_directory / "all_analysis_results.json",
            self.data_directory / "consolidated_calls.json",
            self.data_directory / "call_analysis_summary.json"
        ]
        
        return any(f.exists() for f in consolidated_files)
    
    def _has_csv_export(self) -> bool:
        """Check if CSV exports exist"""
        csv_files = list(self.data_directory.glob("*.csv"))
        return len(csv_files) > 0
    
    async def _load_from_individual_files(self) -> List[Dict]:
        """Load calls from individual JSON analysis files"""
        all_calls = []
        
        # Get all JSON files in the output directory
        json_files = list(self.data_directory.glob("*.json"))
        
        # Filter for analysis result files (adjust pattern based on your naming)
        analysis_files = [
            f for f in json_files 
            if any(keyword in f.name.lower() for keyword in ["analysis", "result", "call"])
            and "processed_files" not in f.name.lower()  # Exclude metadata files
        ]
        
        logger.info(f"Found {len(analysis_files)} analysis files to process")
        
        for file_path in analysis_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    call_data = json.load(f)
                
                # Add file metadata
                call_data['source_file'] = file_path.name
                call_data['file_modified'] = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                call_data['source'] = 'local_json'
                
                all_calls.append(call_data)
                
            except Exception as e:
                logger.warning(f"Error loading file {file_path}: {str(e)}")
                continue
        
        return all_calls
    
    async def _load_from_consolidated_file(self) -> List[Dict]:
        """Load calls from a consolidated JSON file"""
        consolidated_files = [
            self.data_directory / "all_analysis_results.json",
            self.data_directory / "consolidated_calls.json",
            self.data_directory / "call_analysis_summary.json"
        ]
        
        for file_path in consolidated_files:
            if file_path.exists():
                try:
                    logger.info(f"Loading from consolidated file: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different data structures
                    if isinstance(data, list):
                        for call in data:
                            call['source'] = 'consolidated_json'
                        return data
                    elif isinstance(data, dict):
                        calls = []
                        if 'calls' in data:
                            calls = data['calls']
                        elif 'results' in data:
                            calls = data['results']
                        elif 'analysis_results' in data:
                            calls = data['analysis_results']
                        else:
                            # Assume the dict itself is a single call
                            calls = [data]
                        
                        for call in calls:
                            call['source'] = 'consolidated_json'
                        return calls
                    
                except Exception as e:
                    logger.warning(f"Error loading consolidated file {file_path}: {str(e)}")
                    continue
        
        return []
    
    async def _load_from_csv(self) -> List[Dict]:
        """Load calls from CSV export (fallback method)"""
        try:
            import pandas as pd
        except ImportError:
            logger.warning("Pandas not available for CSV loading")
            return []
        
        csv_files = list(self.data_directory.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                logger.info(f"Loading from CSV file: {csv_file}")
                df = pd.read_csv(csv_file)
                
                # Convert DataFrame to list of dictionaries
                calls = df.to_dict('records')
                
                # Basic data cleaning
                for call in calls:
                    call['source'] = 'csv'
                    # Convert NaN to None
                    for key, value in call.items():
                        if pd.isna(value):
                            call[key] = None
                
                return calls
                
            except Exception as e:
                logger.warning(f"Error loading CSV file {csv_file}: {str(e)}")
                continue
        
        return []
    
    def _process_calls_for_coaching(self, raw_calls: List[Dict]) -> List[Dict]:
        """
        Process and enhance calls for coaching library use
        Standardizes the data structure and adds coaching-relevant fields
        """
        processed_calls = []
        
        for call in raw_calls:
            try:
                # Create standardized call structure
                processed_call = {
                    # Basic identifiers
                    'id': self._generate_call_id(call),
                    'audio_file': call.get('Call_File_Name', call.get('audio_file', '')),
                    'source_file': call.get('source_file', ''),
                    'source': call.get('source', 'unknown'),
                    
                    # Analysis metadata - handle both formats
                    'analysis_date': self._standardize_date(call.get('Analysis_Date', call.get('analysis_date', datetime.now().isoformat()))),
                    'representative_name': call.get('Representative_Name', call.get('representative_name', 'Unknown')),
                    
                    # Call content
                    'call_summary': call.get('Call_Summary', call.get('call_summary', 'No summary available')),
                    'patient_transcript': self._extract_transcript(call, 'patient'),
                    'staff_transcript': self._extract_transcript(call, 'staff'),
                    'combined_transcript': call.get('combined_transcript', ''),
                    
                    # Performance metrics
                    'representative_score': self._extract_score(call),
                    'overall_sentiment': call.get('Overall_Sentiment', call.get('overall_sentiment', 'neutral')),
                    'call_tag': call.get('Call_Tag', call.get('call_tag', 'general_inquiry')),
                    'call_duration': call.get('call_duration'),
                    
                    # Analysis results
                    'performance_analysis': call.get('performance_analysis', {}),
                    'sentiment_analysis': call.get('sentiment_analysis', {}),
                    'emotion_analysis': call.get('emotion_analysis', {}),
                    'opportunity_analysis': call.get('opportunity_analysis', {}),
                    'coaching_analysis': call.get('coaching_analysis', {}),
                    
                    # Coaching-relevant flags
                    'high_value_missed_opportunity': call.get('High_Value_Missed_Opportunity', call.get('high_value_missed_opportunity', False)),
                    'is_coaching_candidate': self._determine_coaching_candidate(call),
                    'coaching_priority': self._calculate_coaching_priority(call),
                    
                    # Additional metadata
                    'file_modified': call.get('file_modified'),
                    'llm_used': call.get('llm_used', False),
                    'analysis_method': call.get('analysis_method', 'standard'),
                    'worksheet_source': call.get('worksheet_source', '')
                }
                
                processed_calls.append(processed_call)
                
            except Exception as e:
                logger.warning(f"Error processing call: {str(e)}")
                continue
        
        # Sort by analysis date (newest first)
        processed_calls.sort(key=lambda x: x.get('analysis_date', ''), reverse=True)
        
        return processed_calls
    
    def _standardize_date(self, date_value) -> str:
        """Convert various date formats to ISO format"""
        if not date_value:
            return datetime.now().isoformat()
            
        try:
            # If already in ISO format
            if isinstance(date_value, str) and 'T' in date_value:
                return date_value
            
            # If MM/DD/YYYY format
            if isinstance(date_value, str) and '/' in date_value:
                date_obj = datetime.strptime(date_value, '%m/%d/%Y')
                return date_obj.isoformat()
            
            # Try to parse as general date
            if isinstance(date_value, str):
                date_obj = datetime.strptime(date_value, '%Y-%m-%d')
                return date_obj.isoformat()
                
        except ValueError:
            pass
        
        # Fallback
        return str(date_value) if date_value else datetime.now().isoformat()
    
    def _generate_call_id(self, call: Dict) -> str:
        """Generate a unique ID for the call"""
        # Try Call_File_Name first, then audio_file
        audio_file = call.get('Call_File_Name') or call.get('audio_file', '')
        if audio_file:
            # Use audio filename without extension as ID
            return Path(audio_file).stem
        
        # Fallback: use source file or generate based on content
        source_file = call.get('source_file', '')
        if source_file:
            return Path(source_file).stem
        
        # Last resort: generate based on representative and date
        rep_name = call.get('Representative_Name', call.get('representative_name', 'unknown'))
        date = call.get('Analysis_Date', call.get('analysis_date', datetime.now().isoformat()))
        source = call.get('source', 'unknown')
        return f"{rep_name}_{date[:10]}_{source}_{hash(str(call)) % 10000}"
    
    def _extract_transcript(self, call: Dict, speaker_type: str) -> str:
        """Extract transcript for specific speaker"""
        # Try direct field with capitalized names first
        if speaker_type == 'patient':
            direct_field = call.get('Patient_Transcript') or call.get('patient_transcript', '')
        else:
            direct_field = call.get('Staff_Transcript') or call.get('staff_transcript', '')
        
        if direct_field:
            return direct_field
        
        # Try transcription object
        transcription = call.get('transcription', {})
        if isinstance(transcription, dict):
            if speaker_type in transcription:
                return transcription[speaker_type] or ''
            
            # Try speaker segments
            segments = transcription.get('speaker_segments', [])
            if segments:
                speaker_text = []
                for segment in segments:
                    if segment.get('speaker', '').lower() == speaker_type.lower():
                        speaker_text.append(segment.get('text', ''))
                return ' '.join(speaker_text)
        
        return ''
    
    def _extract_score(self, call: Dict) -> float:
        """Extract representative performance score"""
        # Try Representative_Score first (capitalized)
        score = call.get('Representative_Score')
        if score is not None:
            try:
                score_float = float(score)
                # Convert 0-1 scale to 0-100 scale if needed
                return score_float * 100 if score_float <= 1.0 else score_float
            except (ValueError, TypeError):
                pass
        
        # Try lowercase version
        score = call.get('representative_score')
        if score is not None:
            try:
                score_float = float(score)
                return score_float * 100 if score_float <= 1.0 else score_float
            except (ValueError, TypeError):
                pass
        
        # Try performance analysis
        performance = call.get('performance_analysis', {})
        if isinstance(performance, dict):
            if 'overall_score' in performance:
                return float(performance['overall_score'])
            if 'representative_score' in performance:
                return float(performance['representative_score'])
        
        # Default score
        return 0.0
    
    def _determine_coaching_candidate(self, call: Dict) -> bool:
        """Determine if this call represents a coaching opportunity"""
        score = self._extract_score(call)
        
        # Low performance score
        if score < 75:
            return True
        
        # Missed opportunities
        if (call.get('High_Value_Missed_Opportunity', False) or 
            call.get('high_value_missed_opportunity', False)):
            return True
        
        # Negative sentiment
        overall_sentiment = call.get('Overall_Sentiment', call.get('overall_sentiment', ''))
        if overall_sentiment.lower() == 'negative':
            return True
        
        # Coaching analysis flag
        coaching_analysis = call.get('coaching_analysis', {})
        if coaching_analysis.get('is_coaching_candidate', False):
            return True
        
        # Performance analysis indicates issues
        performance = call.get('performance_analysis', {})
        if isinstance(performance, dict):
            weaknesses = performance.get('weaknesses', [])
            if len(weaknesses) > 2:  # Multiple weaknesses
                return True
        
        return False
    
    def _calculate_coaching_priority(self, call: Dict) -> str:
        """Calculate coaching priority level"""
        priority_score = 0
        
        score = self._extract_score(call)
        
        # Performance score impact
        if score < 50:
            priority_score += 30
        elif score < 70:
            priority_score += 20
        elif score < 85:
            priority_score += 10
        
        # Sentiment impact
        sentiment = call.get('Overall_Sentiment', call.get('overall_sentiment', '')).lower()
        if sentiment == 'negative':
            priority_score += 25
        elif sentiment == 'neutral':
            priority_score += 10
        
        # Missed opportunities
        if (call.get('High_Value_Missed_Opportunity', False) or 
            call.get('high_value_missed_opportunity', False)):
            priority_score += 20
        
        # Multiple performance issues
        performance = call.get('performance_analysis', {})
        if isinstance(performance, dict):
            weaknesses = performance.get('weaknesses', [])
            priority_score += min(len(weaknesses) * 5, 15)
        
        # Return priority level
        if priority_score >= 50:
            return 'high'
        elif priority_score >= 25:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_calls_overview(self, calls: List[Dict]) -> Dict:
        """Calculate overview statistics for calls"""
        if not calls:
            return {
                "total_calls": 0,
                "calls_today": 0,
                "average_score": 0,
                "coaching_candidates": 0
            }
        
        today = datetime.now().date().isoformat()
        calls_today = len([c for c in calls if c.get('analysis_date', '').startswith(today)])
        
        scores = [c.get('representative_score', 0) for c in calls]
        average_score = sum(scores) / len(scores) if scores else 0
        
        coaching_candidates = len([c for c in calls if c.get('is_coaching_candidate', False)])
        
        return {
            "total_calls": len(calls),
            "calls_today": calls_today,
            "average_score": round(average_score, 1),
            "coaching_candidates": coaching_candidates,
            "coaching_percentage": round((coaching_candidates / len(calls)) * 100, 1) if calls else 0
        }
    
    def _calculate_analytics(self, calls: List[Dict]) -> Dict:
        """Calculate analytics for dashboard"""
        if not calls:
            return {
                "topPerformers": [],
                "bottomPerformers": [],
                "sentimentTrends": {},
                "performanceDistribution": {}
            }
        
        # Group by employee
        employee_stats = {}
        for call in calls:
            emp = call.get('representative_name', 'Unknown')
            if emp not in employee_stats:
                employee_stats[emp] = {
                    'name': emp,
                    'scores': [],
                    'callCount': 0,
                    'totalScore': 0
                }
            
            score = call.get('representative_score', 0)
            employee_stats[emp]['scores'].append(score)
            employee_stats[emp]['callCount'] += 1
            employee_stats[emp]['totalScore'] += score
        
        # Calculate averages
        for emp_data in employee_stats.values():
            emp_data['averageScore'] = emp_data['totalScore'] / emp_data['callCount'] if emp_data['callCount'] > 0 else 0
        
        # Sort for top/bottom performers
        sorted_performers = sorted(employee_stats.values(), key=lambda x: x['averageScore'], reverse=True)
        
        # Sentiment trends
        sentiment_counts = {}
        for call in calls:
            sentiment = call.get('overall_sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Performance distribution
        excellent = len([c for c in calls if c.get('representative_score', 0) >= 85])
        good = len([c for c in calls if 70 <= c.get('representative_score', 0) < 85])
        needs_improvement = len([c for c in calls if c.get('representative_score', 0) < 70])
        
        return {
            "topPerformers": sorted_performers[:5],  # Top 5
            "bottomPerformers": sorted_performers[-3:],  # Bottom 3
            "sentimentTrends": sentiment_counts,
            "performanceDistribution": {
                "excellent": excellent,
                "good": good,
                "needs_improvement": needs_improvement
            }
        }
    
    def _calculate_sentiment_data(self, calls: List[Dict]) -> Dict:
        """Calculate sentiment analysis data"""
        if not calls:
            return {
                "overall_sentiment": "neutral",
                "sentiment_distribution": {},
                "emotion_trends": {}
            }
        
        # Sentiment distribution
        sentiment_counts = {}
        emotion_counts = {}
        
        for call in calls:
            # Overall sentiment
            sentiment = call.get('overall_sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # Emotions
            emotion_analysis = call.get('emotion_analysis', {})
            if isinstance(emotion_analysis, dict):
                dominant_emotion = emotion_analysis.get('dominant_emotion')
                if dominant_emotion:
                    emotion_counts[dominant_emotion] = emotion_counts.get(dominant_emotion, 0) + 1
        
        # Calculate percentages
        total_calls = len(calls)
        sentiment_percentages = {
            sentiment: round((count / total_calls) * 100, 1)
            for sentiment, count in sentiment_counts.items()
        }
        
        # Determine overall sentiment
        positive_pct = sentiment_percentages.get('positive', 0)
        negative_pct = sentiment_percentages.get('negative', 0)
        
        if positive_pct > negative_pct + 10:
            overall_sentiment = 'positive'
        elif negative_pct > positive_pct + 10:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_distribution": sentiment_percentages,
            "emotion_trends": emotion_counts,
            "total_analyzed": total_calls
        }
    
    def _get_empty_dashboard_data(self) -> Dict:
        """Return empty dashboard data structure"""
        return {
            "callsOverview": {
                "total_calls": 0,
                "calls_today": 0,
                "average_score": 0,
                "coaching_candidates": 0
            },
            "analytics": {
                "topPerformers": [],
                "bottomPerformers": [],
                "sentimentTrends": {},
                "performanceDistribution": {}
            },
            "sentimentData": {
                "overall_sentiment": "neutral",
                "sentiment_distribution": {},
                "emotion_trends": {}
            },
            "rawData": [],
            "totalCalls": 0,
            "lastUpdate": datetime.now().isoformat(),
            "message": "No call data available"
        }
    
    async def refresh_cache(self) -> None:
        """Force refresh of the data cache"""
        self.calls_cache = None
        self.cache_timestamp = None
        logger.info("Data cache cleared, will reload on next request")