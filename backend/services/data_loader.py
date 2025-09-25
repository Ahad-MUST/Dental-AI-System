"""
Enhanced Data Loader for Dental Call Analysis - CLEANED VERSION
Handles unified transcripts and only includes existing Google Sheets fields
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
    Enhanced data loader with Google Sheets integration - CLEANED VERSION
    Only includes fields that actually exist in Google Sheets
    """
    
    def __init__(self):
        self.data_directory = settings.OUTPUT_DIR
        self.calls_cache = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=5)
        
        # Google Sheets configuration
        self.sheets_client = None
        self.spreadsheet = None
        self._init_google_sheets()
        
    def _init_google_sheets(self):
        """Initialize Google Sheets client"""
        if not GSPREAD_AVAILABLE:
            logger.warning("Google Sheets integration not available")
            return
            
        try:
            credentials_path = getattr(settings, 'GOOGLE_CREDENTIALS_FILE', None)
            spreadsheet_id = getattr(settings, 'GOOGLE_SHEET_ID', None)
            use_google_sheets = getattr(settings, 'USE_GOOGLE_SHEETS', False)
            
            logger.info(f"Google Sheets config: enabled={use_google_sheets}")
            
            if not use_google_sheets:
                logger.info("Google Sheets disabled in settings")
                return
            
            if credentials_path and Path(credentials_path).exists():
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                
                creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                self.sheets_client = gspread.authorize(creds)
                logger.info("Google Sheets client initialized")
                
            elif spreadsheet_id:
                self.sheets_client = gspread.service_account()
                logger.info("Google Sheets client initialized with default credentials")
            else:
                logger.warning("Google Sheets not configured properly")
                return
                
            if spreadsheet_id:
                self.spreadsheet = self.sheets_client.open_by_key(spreadsheet_id)
                logger.info(f"Connected to Google Sheets: {self.spreadsheet.title}")
            else:
                logger.error("No Google Sheet ID provided")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            self.sheets_client = None
            self.spreadsheet = None
        
    async def load_all_calls(self) -> List[Dict[str, Any]]:
        """
        Load all processed calls - CLEANED VERSION with only existing fields
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Returning cached call data")
                return self.calls_cache
            
            logger.info("Loading all call data...")
            
            all_calls = []
            
            # Priority 1: Google Sheets
            if self.sheets_client and self.spreadsheet:
                try:
                    all_calls = await self._load_from_google_sheets()
                    logger.info(f"Loaded {len(all_calls)} calls from Google Sheets")
                except Exception as e:
                    logger.warning(f"Failed to load from Google Sheets: {str(e)}")
                    all_calls = []
            
            # Priority 2: Local files
            if not all_calls:
                all_calls = await self._load_from_local_files()
                logger.info(f"Loaded {len(all_calls)} calls from local files")
                
            if not all_calls:
                logger.error("No call data found from any source")
                return []
            
            # Process calls for coaching (only include existing fields)
            processed_calls = self._process_calls_for_coaching(all_calls)
            
            # Update cache
            self.calls_cache = processed_calls
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Loaded {len(processed_calls)} calls for coaching library")
            return processed_calls
            
        except Exception as e:
            logger.error(f"Error loading call data: {str(e)}")
            return []
    
    async def _load_from_google_sheets(self) -> List[Dict]:
        """Load calls from Google Sheets - only existing fields"""
        all_calls = []
        
        try:
            worksheets = self.spreadsheet.worksheets()
            logger.info(f"Found {len(worksheets)} worksheets")
            
            for worksheet in worksheets:
                try:
                    worksheet_name = worksheet.title
                    logger.info(f"Processing worksheet: {worksheet_name}")
                    
                    records = worksheet.get_all_records()
                    logger.info(f"Found {len(records)} records in worksheet {worksheet_name}")
                    
                    for record in records:
                        if not any(record.values()):
                            continue
                            
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
        """Convert Google Sheets record to call format - only existing fields"""
        try:
            call_data = {
                'worksheet_source': worksheet_name,
                'source': 'google_sheets'
            }
            
            # Direct field mappings for ONLY existing Google Sheets columns
            field_mappings = {
                'Call_File_Name': 'Call_File_Name',
                'Analysis_Date': 'Analysis_Date', 
                'Analysis_Time': 'Analysis_Time',
                'Full_Transcript_With_Timestamps': 'Full_Transcript_With_Timestamps',
                'Call_Summary': 'Call_Summary',
                'Representative_Name': 'Representative_Name',
                'Representative_Score': 'Representative_Score',
                'High_Value_Missed_Opportunity': 'High_Value_Missed_Opportunity',
                'Patient_Sentiment': 'Patient_Sentiment',
                'Staff_Sentiment': 'Staff_Sentiment',
                'Overall_Sentiment': 'Overall_Sentiment',
                'Sentiment_Confidence': 'Sentiment_Confidence',
                'Sentiment_Summary': 'Sentiment_Summary',
                'Patient_Primary_Emotion': 'Patient_Primary_Emotion',
                'Patient_Emotion_Confidence': 'Patient_Emotion_Confidence',
                'Patient_Emotion_Intensity': 'Patient_Emotion_Intensity',
                'Staff_Primary_Emotion': 'Staff_Primary_Emotion',
                'Staff_Emotion_Confidence': 'Staff_Emotion_Confidence',
                'Emotion_Flags': 'Emotion_Flags',
                'Call_Emotional_Health': 'Call_Emotional_Health',
                'Emotional_Alignment': 'Emotional_Alignment',
                'Escalation_Pattern': 'Escalation_Pattern',
                'Call_Tag': 'Call_Tag',
                'Coaching_Candidate': 'Coaching_Candidate'
            }
            
            # Apply direct mappings
            for target_field, source_field in field_mappings.items():
                if source_field in record and record[source_field]:
                    value = record[source_field]
                    
                    # Handle data type conversions
                    if target_field in ['Representative_Score', 'Sentiment_Confidence', 
                                      'Patient_Emotion_Confidence', 'Staff_Emotion_Confidence', 
                                      'Escalation_Pattern']:
                        try:
                            call_data[target_field] = float(value) if value else 0.0
                        except:
                            call_data[target_field] = 0.0
                            
                    elif target_field in ['High_Value_Missed_Opportunity', 'Coaching_Candidate']:
                        if isinstance(value, str):
                            call_data[target_field] = value.lower() in ['true', 'yes', '1', 'y']
                        else:
                            call_data[target_field] = bool(value)
                            
                    else:
                        call_data[target_field] = str(value) if value else ''
            
            # Generate ID from filename
            if 'Call_File_Name' in call_data:
                call_data['id'] = Path(call_data['Call_File_Name']).stem
            else:
                call_data['id'] = f"call_{hash(str(call_data)) % 100000}"
            
            # Ensure required fields exist with defaults
            call_data.setdefault('Analysis_Date', datetime.now().strftime('%m/%d/%Y'))
            call_data.setdefault('Representative_Name', 'Unknown')
            call_data.setdefault('Call_Summary', '')
            call_data.setdefault('Overall_Sentiment', 'neutral')
            call_data.setdefault('Call_Tag', 'general_inquiry')
            call_data.setdefault('Representative_Score', 0.0)
            call_data.setdefault('Full_Transcript_With_Timestamps', '')
            
            return call_data
            
        except Exception as e:
            logger.warning(f"Error converting sheets record: {str(e)}")
            return None
    
    async def _load_from_local_files(self) -> List[Dict]:
        """Load calls from local files"""
        logger.info("Loading from local files as fallback...")
        all_calls = []
        
        # Try CSV files first (matching the uploaded format)
        csv_files = list(self.data_directory.glob("*.csv"))
        if csv_files:
            try:
                import pandas as pd
                for csv_file in csv_files:
                    logger.info(f"Loading from CSV: {csv_file}")
                    df = pd.read_csv(csv_file)
                    calls = df.to_dict('records')
                    
                    for call in calls:
                        call['source'] = 'csv'
                        # Convert NaN to empty string
                        for key, value in call.items():
                            if pd.isna(value):
                                call[key] = ''
                    
                    all_calls.extend(calls)
                    
            except ImportError:
                logger.warning("Pandas not available for CSV loading")
            except Exception as e:
                logger.error(f"Error loading CSV: {str(e)}")
        
        # Try JSON files if no CSV
        if not all_calls:
            json_files = list(self.data_directory.glob("*.json"))
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        all_calls.extend(data)
                    elif isinstance(data, dict):
                        all_calls.append(data)
                        
                except Exception as e:
                    logger.warning(f"Error loading JSON file {json_file}: {str(e)}")
        
        return all_calls
    
    def _process_calls_for_coaching(self, raw_calls: List[Dict]) -> List[Dict]:
        """
        Process calls for coaching - CLEANED VERSION with only existing fields
        """
        processed_calls = []
        
        for call in raw_calls:
            try:
                processed_call = {
                    # Basic identifiers
                    'id': call.get('Call_File_Name', '').replace('.wav', '').replace('.mp3', '') or f"call_{hash(str(call)) % 100000}",
                    'source': call.get('source', 'unknown'),
                    
                    # ONLY FRONTEND DISPLAY FIELDS (as requested)
                    'analysis_date': self._standardize_date(call.get('Analysis_Date', '')),
                    'analysis_time': call.get('Analysis_Time', ''),
                    'representative_name': call.get('Representative_Name', 'Unknown'),
                    'full_transcript': call.get('Full_Transcript_With_Timestamps', ''),
                    'call_tag': call.get('Call_Tag', 'general_inquiry'),
                    'representative_score': self._normalize_score(call.get('Representative_Score', 0)),
                    'overall_sentiment': call.get('Overall_Sentiment', 'neutral'),
                    'call_summary': call.get('Call_Summary', ''),
                    
                    # Additional fields that exist in sheets but not displayed on frontend
                    'high_value_missed_opportunity': self._parse_boolean(call.get('High_Value_Missed_Opportunity', False)),
                }
                
                processed_calls.append(processed_call)
                
            except Exception as e:
                logger.warning(f"Error processing call: {str(e)}")
                continue
        
        # Sort by date (newest first)
        processed_calls.sort(key=lambda x: x.get('analysis_date', ''), reverse=True)
        
        return processed_calls
    
    def _standardize_date(self, date_value) -> str:
        """Convert date to ISO format"""
        if not date_value:
            return datetime.now().isoformat()
            
        try:
            if isinstance(date_value, str) and 'T' in date_value:
                return date_value
            
            if isinstance(date_value, str) and '/' in date_value:
                date_obj = datetime.strptime(date_value, '%m/%d/%Y')
                return date_obj.isoformat()
            
        except ValueError:
            pass
        
        return str(date_value) if date_value else datetime.now().isoformat()
    
    def _normalize_score(self, score) -> float:
        """Normalize score to 0-100 range"""
        try:
            score_float = float(score)
            if score_float <= 1.0:
                return score_float * 100
            return max(0, min(100, score_float))
        except:
            return 0.0
    
    def _parse_boolean(self, value) -> bool:
        """Parse boolean values from various formats"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        return bool(value)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.calls_cache or not self.cache_timestamp:
            return False
        return datetime.now() - self.cache_timestamp < self.cache_duration
    
    async def refresh_cache(self) -> None:
        """Force refresh cache"""
        self.calls_cache = None
        self.cache_timestamp = None
        logger.info("Cache cleared")

    # Dashboard support methods - simplified for cleaned data
    async def load_dashboard_data(self) -> Dict[str, Any]:
        """Load dashboard data"""
        try:
            all_calls = await self.load_all_calls()
            
            if not all_calls:
                return self._get_empty_dashboard_data()
            
            dashboard_data = {
                "callsOverview": self._calculate_calls_overview(all_calls),
                "analytics": self._calculate_analytics(all_calls),
                "sentimentData": self._calculate_sentiment_data(all_calls),
                "rawData": all_calls,
                "totalCalls": len(all_calls),
                "lastUpdate": datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {str(e)}")
            return self._get_empty_dashboard_data()
    
    def _calculate_calls_overview(self, calls: List[Dict]) -> Dict:
        """Calculate overview stats from real data"""
        if not calls:
            return {"total_calls": 0, "calls_today": 0, "average_score": 0, "coaching_candidates": 0}
        
        today = datetime.now().date().isoformat()
        calls_today = len([c for c in calls if c.get('analysis_date', '').startswith(today)])
        
        scores = [c.get('representative_score', 0) for c in calls]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Count potential coaching candidates based on low scores or missed opportunities
        coaching_candidates = len([c for c in calls 
                                 if c.get('representative_score', 100) < 75 or 
                                    c.get('high_value_missed_opportunity', False)])
        
        return {
            "total_calls": len(calls),
            "calls_today": calls_today,
            "average_score": round(average_score, 1),
            "coaching_candidates": coaching_candidates
        }
    
    def _calculate_analytics(self, calls: List[Dict]) -> Dict:
        """Calculate analytics from real data"""
        if not calls:
            return {"topPerformers": [], "bottomPerformers": [], 
                   "sentimentTrends": {}, "performanceDistribution": {}}
        
        # Group by employee
        employee_stats = {}
        for call in calls:
            emp = call.get('representative_name', 'Unknown')
            if emp not in employee_stats:
                employee_stats[emp] = {'name': emp, 'scores': [], 'callCount': 0, 'totalScore': 0}
            
            score = call.get('representative_score', 0)
            employee_stats[emp]['scores'].append(score)
            employee_stats[emp]['callCount'] += 1
            employee_stats[emp]['totalScore'] += score
        
        # Calculate averages
        for emp_data in employee_stats.values():
            emp_data['averageScore'] = emp_data['totalScore'] / emp_data['callCount'] if emp_data['callCount'] > 0 else 0
        
        sorted_performers = sorted(employee_stats.values(), key=lambda x: x['averageScore'], reverse=True)
        
        # Sentiment trends
        sentiment_counts = {}
        for call in calls:
            sentiment = call.get('overall_sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        return {
            "topPerformers": sorted_performers[:5],
            "bottomPerformers": sorted_performers[-3:],
            "sentimentTrends": sentiment_counts,
            "performanceDistribution": self._calculate_performance_distribution(calls)
        }
    
    def _calculate_performance_distribution(self, calls: List[Dict]) -> Dict:
        """Calculate performance distribution"""
        excellent = len([c for c in calls if c.get('representative_score', 0) >= 85])
        good = len([c for c in calls if 70 <= c.get('representative_score', 0) < 85])
        needs_improvement = len([c for c in calls if c.get('representative_score', 0) < 70])
        
        return {
            "excellent": excellent,
            "good": good, 
            "needs_improvement": needs_improvement
        }
    
    def _calculate_sentiment_data(self, calls: List[Dict]) -> Dict:
        """Calculate sentiment data from real data"""
        if not calls:
            return {"overall_sentiment": "neutral", "sentiment_distribution": {}}
        
        sentiment_counts = {}
        for call in calls:
            sentiment = call.get('overall_sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
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
            "total_analyzed": total_calls
        }
    
    def _get_empty_dashboard_data(self) -> Dict:
        """Return empty dashboard structure"""
        return {
            "callsOverview": {"total_calls": 0, "calls_today": 0, "average_score": 0, "coaching_candidates": 0},
            "analytics": {"topPerformers": [], "bottomPerformers": [], "sentimentTrends": {}, "performanceDistribution": {}},
            "sentimentData": {"overall_sentiment": "neutral", "sentiment_distribution": {}},
            "rawData": [],
            "totalCalls": 0,
            "lastUpdate": datetime.now().isoformat(),
            "message": "No call data available"
        }