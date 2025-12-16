"""
Google Sheets Export Service - UPDATED
Exports call analysis results to Google Sheets with automatic worksheet management
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Google Sheets API imports
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    gspread = None

from config.settings import settings

logger = logging.getLogger(__name__)

class GoogleSheetsExporter:
    """Enhanced Google Sheets exporter with automatic worksheet management"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.llm_analyzer = None
        
        # Standard column order with NEW client requirements for Google Ads tracking
        self.standard_columns = [
            'Call_File_Name',
            'Analysis_Date',
            'Analysis_Time',

            # NEW: Patient Categorization & Conversion Tracking
            'Patient_Type',  # new_patient | existing_patient
            'Appointment_Booked',  # TRUE | FALSE
            'Conversion_Status',  # booked | not_booked (for Google Ads)

            # NEW: For New Patients
            'Script_Followed',  # TRUE | FALSE | (blank for existing patients)

            # NEW: For Existing Patients
            'Call_Concern_Type',  # issue | question | concern | query | (blank for new patients)
            'Issue_Resolved',  # TRUE | FALSE | (blank for new patients)

            # NEW: Detailed Analysis
            'Detailed_Analysis',  # Brutally honest coaching analysis

            # Existing columns
            'Full_Transcript_With_Timestamps',
            'Call_Summary',
            'Representative_Name',
            'Representative_Score',
            'High_Value_Missed_Opportunity',
            'Patient_Sentiment',
            'Staff_Sentiment',
            'Overall_Sentiment',
            'Sentiment_Confidence',
            'Sentiment_Summary',
            'Patient_Primary_Emotion',
            'Patient_Emotion_Confidence',
            'Patient_Emotion_Intensity',
            'Staff_Primary_Emotion',
            'Staff_Emotion_Confidence',
            'Emotion_Flags',
            'Call_Emotional_Health',
            'Emotional_Alignment',
            'Escalation_Pattern',
            'Call_Tag'
        ]
    
    async def initialize(self, llm_analyzer=None):
        """Initialize Google Sheets connection"""
        self.llm_analyzer = llm_analyzer
        
        if not settings.USE_GOOGLE_SHEETS:
            logger.info("Google Sheets export disabled in settings")
            return
        
        if not GSPREAD_AVAILABLE:
            logger.error("Google Sheets libraries not available. Install gspread and google-auth.")
            return
        
        try:
            # Setup credentials
            credentials_file = Path(settings.GOOGLE_CREDENTIALS_FILE)
            if not credentials_file.exists():
                logger.error(f"Google credentials file not found: {credentials_file}")
                return
            
            # Define required scopes
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate and create client
            creds = Credentials.from_service_account_file(str(credentials_file), scopes=scope)
            self.client = gspread.authorize(creds)
            
            # Connect to spreadsheet
            if settings.GOOGLE_SHEET_ID:
                self.spreadsheet = self.client.open_by_key(settings.GOOGLE_SHEET_ID)
                logger.info(f"Connected to Google Sheets: {self.spreadsheet.title}")
            else:
                logger.error("No Google Sheet ID provided in settings")
                return
            
            # Ensure master sheet exists with proper headers
            await self._ensure_master_sheet()
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            self.client = None
            self.spreadsheet = None
    
    async def _ensure_master_sheet(self):
        """Ensure master sheet exists with proper column headers"""
        try:
            master_sheet_name = "Master_Analysis_Data"
            
            # Check if master sheet exists
            try:
                master_sheet = self.spreadsheet.worksheet(master_sheet_name)
                logger.info(f"Master sheet '{master_sheet_name}' found")
            except gspread.exceptions.WorksheetNotFound:
                # Create master sheet
                logger.info(f"Creating master sheet: {master_sheet_name}")
                master_sheet = self.spreadsheet.add_worksheet(
                    title=master_sheet_name, 
                    rows=1000, 
                    cols=len(self.standard_columns)
                )
            
            # Update headers if needed
            existing_headers = master_sheet.row_values(1) if master_sheet.row_count > 0 else []
            
            if existing_headers != self.standard_columns:
                logger.info("Updating master sheet headers")
                master_sheet.update('1:1', [self.standard_columns])
                
                # Format header row
                master_sheet.format('1:1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
                })
            
        except Exception as e:
            logger.error(f"Error setting up master sheet: {str(e)}")
    
    async def export_analysis_result(self, analysis_result: Dict) -> str:
        """Export a single analysis result to Google Sheets"""
        
        if not self.client or not self.spreadsheet:
            return "Google Sheets not available - saved locally only"
        
        try:
            # Prepare data for export
            call_data = self._prepare_call_data(analysis_result)
            
            # Export to master sheet
            master_result = await self._export_to_master_sheet(call_data)
            
            # Export to monthly worksheet 
            monthly_result = await self._export_to_monthly_worksheet(call_data)
            
            return f"Exported to Google Sheets: {master_result}, {monthly_result}"
            
        except Exception as e:
            logger.error(f"Google Sheets export failed: {str(e)}")
            return f"Export failed: {str(e)}"
    
    def _prepare_call_data(self, analysis_result: Dict) -> Dict:
        """Prepare analysis data for Google Sheets export - WITH NEW client requirements"""

        try:
            # Extract basic information
            audio_file = analysis_result.get("audio_file", "")
            file_name = Path(audio_file).name if audio_file else "Unknown"

            transcription = analysis_result.get("transcription", {})
            call_summary = analysis_result.get("call_summary", {})
            sentiment_analysis = analysis_result.get("sentiment_analysis", {})
            emotion_analysis = analysis_result.get("emotion_analysis", {})
            performance_analysis = analysis_result.get("performance_analysis", {})
            opportunity_analysis = analysis_result.get("opportunity_analysis", {})
            call_tag_analysis = analysis_result.get("call_tag_analysis", {})
            call_categorization = analysis_result.get("call_categorization", {})  # NEW

            # Get current timestamp
            now = datetime.now()

            # Prepare row data according to standard columns (WITH new client requirements)
            call_data = {
                'Call_File_Name': file_name,
                'Analysis_Date': now.strftime('%m/%d/%Y'),
                'Analysis_Time': now.strftime('%H:%M:%S'),

                # NEW: Patient Categorization & Conversion Tracking
                'Patient_Type': call_categorization.get("patient_type", "existing_patient"),
                'Appointment_Booked': call_categorization.get("appointment_booked", False),
                'Conversion_Status': call_categorization.get("conversion_status", "not_booked"),

                # NEW: For New Patients
                'Script_Followed': call_categorization.get("script_followed"),  # Can be None

                # NEW: For Existing Patients
                'Call_Concern_Type': call_categorization.get("call_concern_type"),  # Can be None
                'Issue_Resolved': call_categorization.get("issue_resolved"),  # Can be None

                # NEW: Detailed Analysis
                'Detailed_Analysis': call_categorization.get("detailed_analysis", ""),

                # Existing columns
                'Full_Transcript_With_Timestamps': self._format_transcript_with_timestamps(analysis_result.get("combined_transcript", {})),
                'Call_Summary': call_summary.get("call_summary", ""),
                'Representative_Name': analysis_result.get("representative_name", "Unknown"),
                'Representative_Score': performance_analysis.get("representative_score", 0),
                'High_Value_Missed_Opportunity': opportunity_analysis.get("high_value_missed", False),

                # Sentiment data
                'Patient_Sentiment': sentiment_analysis.get("patient_sentiment", {}).get("sentiment_label", ""),
                'Staff_Sentiment': sentiment_analysis.get("staff_sentiment", {}).get("sentiment_label", ""),
                'Overall_Sentiment': sentiment_analysis.get("overall_sentiment", {}).get("sentiment_label", ""),
                'Sentiment_Confidence': sentiment_analysis.get("overall_sentiment", {}).get("confidence", 0),
                'Sentiment_Summary': sentiment_analysis.get("sentiment_summary", ""),

                # Emotion data
                'Patient_Primary_Emotion': emotion_analysis.get("patient_emotions", {}).get("primary_emotion", ""),
                'Patient_Emotion_Confidence': emotion_analysis.get("patient_emotions", {}).get("confidence", 0),
                'Patient_Emotion_Intensity': emotion_analysis.get("patient_emotions", {}).get("intensity", ""),
                'Staff_Primary_Emotion': emotion_analysis.get("staff_emotions", {}).get("primary_emotion", ""),
                'Staff_Emotion_Confidence': emotion_analysis.get("staff_emotions", {}).get("confidence", 0),
                'Emotion_Flags': ", ".join(emotion_analysis.get("emotion_flags", [])),
                'Call_Emotional_Health': emotion_analysis.get("emotional_health_score", ""),
                'Emotional_Alignment': emotion_analysis.get("emotional_alignment", ""),
                'Escalation_Pattern': emotion_analysis.get("escalation_pattern", ""),

                # Call tagging
                'Call_Tag': call_tag_analysis.get("primary_tag", "general_inquiry")
            }

            return call_data

        except Exception as e:
            logger.error(f"Error preparing call data: {str(e)}")
            return {}
    
    def _format_transcript_with_timestamps(self, combined_transcript: Dict) -> str:
        """Format transcript with timestamps for Google Sheets"""
        
        try:
            segments = combined_transcript.get("segments", [])
            if not segments:
                return "No transcript available"
            
            formatted_lines = []
            for segment in segments:
                start_time = segment.get("start_time", 0)
                speaker = segment.get("speaker", "UNKNOWN")
                text = segment.get("text", "").strip()
                
                if text:
                    # Format: [MM:SS] SPEAKER: text
                    minutes = int(start_time // 60)
                    seconds = int(start_time % 60)
                    timestamp = f"[{minutes:02d}:{seconds:02d}]"
                    formatted_lines.append(f"{timestamp} {speaker}: {text}")
            
            return "\n".join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"Error formatting transcript: {str(e)}")
            return "Transcript formatting error"
    
    async def _export_to_master_sheet(self, call_data: Dict) -> str:
        """Export data to the master analysis sheet"""
        
        try:
            master_sheet = self.spreadsheet.worksheet("Master_Analysis_Data")
            
            # Prepare row values in correct column order
            row_values = []
            for column in self.standard_columns:
                value = call_data.get(column, "")

                # Handle None values (leave blank for null fields)
                if value is None:
                    row_values.append("")
                # Handle boolean values
                elif isinstance(value, bool):
                    row_values.append("TRUE" if value else "FALSE")
                # Handle numeric values
                elif isinstance(value, (int, float)):
                    row_values.append(str(value))
                # Handle strings
                else:
                    row_values.append(str(value) if value else "")

            
            # Find next empty row
            next_row = len(master_sheet.get_all_values()) + 1
            
            # Append the data
            range_name = f"A{next_row}:{chr(ord('A') + len(self.standard_columns) - 1)}{next_row}"
            master_sheet.update(range_name, [row_values])
            
            return f"Master sheet row {next_row}"
            
        except Exception as e:
            logger.error(f"Error exporting to master sheet: {str(e)}")
            return "Master export failed"
    
    async def _export_to_monthly_worksheet(self, call_data: Dict) -> str:
        """Export data to monthly worksheet for organization"""
        
        try:
            # Generate worksheet name based on current month
            now = datetime.now()
            worksheet_name = now.strftime("%Y_%m_%B")  # e.g., "2024_03_March"
            
            # Get or create monthly worksheet
            try:
                monthly_sheet = self.spreadsheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create new monthly worksheet
                monthly_sheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows=500, 
                    cols=len(self.standard_columns)
                )
                
                # Add headers
                monthly_sheet.update('1:1', [self.standard_columns])
                monthly_sheet.format('1:1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
                })
            
            # Prepare row values
            row_values = []
            for column in self.standard_columns:
                value = call_data.get(column, "")

                # Handle None values (leave blank for null fields)
                if value is None:
                    row_values.append("")
                # Handle boolean values
                elif isinstance(value, bool):
                    row_values.append("TRUE" if value else "FALSE")
                # Handle numeric values
                elif isinstance(value, (int, float)):
                    row_values.append(str(value))
                # Handle strings
                else:
                    row_values.append(str(value) if value else "")
            
            # Find next empty row
            next_row = len(monthly_sheet.get_all_values()) + 1
            
            # Append the data
            range_name = f"A{next_row}:{chr(ord('A') + len(self.standard_columns) - 1)}{next_row}"
            monthly_sheet.update(range_name, [row_values])
            
            return f"{worksheet_name} row {next_row}"
            
        except Exception as e:
            logger.error(f"Error exporting to monthly worksheet: {str(e)}")
            return "Monthly export failed"
    
    def is_available(self) -> bool:
        """Check if Google Sheets export is available"""
        return self.client is not None and self.spreadsheet is not None
    
    async def get_export_status(self) -> Dict:
        """Get current export status and statistics"""
        
        if not self.is_available():
            return {
                "available": False,
                "error": "Google Sheets not configured or not available"
            }
        
        try:
            # Get master sheet statistics
            master_sheet = self.spreadsheet.worksheet("Master_Analysis_Data")
            total_rows = len(master_sheet.get_all_values())
            
            # Get list of monthly worksheets
            all_worksheets = self.spreadsheet.worksheets()
            monthly_sheets = [ws.title for ws in all_worksheets if "_" in ws.title and ws.title != "Master_Analysis_Data"]
            
            return {
                "available": True,
                "spreadsheet_title": self.spreadsheet.title,
                "spreadsheet_url": self.spreadsheet.url,
                "total_records": max(0, total_rows - 1),  # Subtract header row
                "monthly_worksheets": len(monthly_sheets),
                "monthly_sheets": monthly_sheets,
                "columns_count": len(self.standard_columns),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting export status: {str(e)}")
            return {
                "available": False,
                "error": f"Status check failed: {str(e)}"
            }