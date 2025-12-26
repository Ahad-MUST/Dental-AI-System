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

        # ORIGINAL 24 columns from existing CSV - DO NOT MODIFY ORDER
        self.standard_columns = [
            # Original columns (1-24)
            'Call_File_Name',
            'Analysis_Date',
            'Analysis_Time',
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
            'Call_Tag',
            'Coaching_Candidate',

            # NEW columns added for client requirements (25-31)
            # Patient Categorization & Conversion Tracking for Google Ads
            'Patient_Type',  # new_patient | existing_patient
            'Appointment_Booked',  # TRUE | FALSE
            'Conversion_Status',  # booked | not_booked (for Google Ads)

            # For New Patients
            'Script_Followed',  # TRUE | FALSE | (blank for existing patients)

            # For Existing Patients
            'Call_Concern_Type',  # issue | question | concern | query | (blank for new patients)
            'Issue_Resolved',  # TRUE | FALSE | (blank for new patients)

            # Detailed Coaching Analysis
            'Detailed_Analysis'  # Brutally honest coaching analysis for both patient types
        ]

    @staticmethod
    def _column_number_to_letter(n):
        """Convert column number (1-indexed) to Excel-style column letter (A, B, ..., Z, AA, AB, ...)"""
        result = ""
        while n > 0:
            n -= 1
            result = chr(ord('A') + n % 26) + result
            n //= 26
        return result

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

            # Use the EXISTING first sheet - DO NOT create new sheets
            # This ensures we append to the user's existing CSV structure
            logger.info("Using existing sheet - no new sheets will be created")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            self.client = None
            self.spreadsheet = None
    
    async def _get_first_sheet(self):
        """Get the first (existing) sheet from the spreadsheet - DO NOT create new sheets"""
        try:
            # Get all worksheets and use the first one (existing sheet)
            all_sheets = self.spreadsheet.worksheets()
            if not all_sheets:
                logger.error("No sheets found in spreadsheet")
                return None

            # Use the FIRST sheet (index 0) which is the existing sheet
            first_sheet = all_sheets[0]
            logger.info(f"Using existing sheet: '{first_sheet.title}' - appending data only")

            # Verify headers match our expected columns (but don't modify them)
            existing_headers = first_sheet.row_values(1) if first_sheet.row_count > 0 else []

            if existing_headers and existing_headers != self.standard_columns:
                # Check if existing headers are a subset (original 24 columns)
                if len(existing_headers) == 24 and existing_headers == self.standard_columns[:24]:
                    # Original sheet with 24 columns - we'll add 7 new columns
                    logger.info("Existing sheet has original 24 columns - will append new 7 columns to header")
                    # Update header row to include all 31 columns
                    first_sheet.update('1:1', [self.standard_columns])
                    logger.info("Header updated with 7 new columns (25-31)")
                else:
                    logger.warning(f"Sheet headers don't match expected structure. Found {len(existing_headers)} columns, expected {len(self.standard_columns)}")

            return first_sheet

        except Exception as e:
            logger.error(f"Error getting first sheet: {str(e)}")
            return None
    
    async def export_analysis_result(self, analysis_result: Dict) -> str:
        """Export a single analysis result to Google Sheets - EXISTING SHEET ONLY"""

        if not self.client or not self.spreadsheet:
            return "Google Sheets not available - saved locally only"

        try:
            # Prepare data for export
            call_data = self._prepare_call_data(analysis_result)

            # Export to the EXISTING first sheet ONLY (no master, no monthly sheets)
            export_result = await self._export_to_existing_sheet(call_data)

            return f"Exported to Google Sheets: {export_result}"

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

            # Prepare row data according to standard columns (ORIGINAL 24 + NEW 7 = 31 total)
            call_data = {
                # ORIGINAL COLUMNS (1-24) - Keep exact order
                'Call_File_Name': file_name,
                'Analysis_Date': now.strftime('%m/%d/%Y'),
                'Analysis_Time': now.strftime('%H:%M:%S'),
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
                'Call_Tag': call_tag_analysis.get("primary_tag", "general_inquiry"),

                # Coaching candidate flag (original column 24)
                'Coaching_Candidate': self._determine_coaching_candidate(
                    performance_analysis.get("representative_score", 0),
                    opportunity_analysis.get("high_value_missed", False),
                    sentiment_analysis.get("overall_sentiment", {}).get("sentiment_label", ""),
                    emotion_analysis.get("emotion_flags", [])
                ),

                # NEW COLUMNS (25-31) - Client requirements for Google Ads tracking
                # Patient Categorization & Conversion Tracking
                'Patient_Type': call_categorization.get("patient_type", "existing_patient"),
                'Appointment_Booked': call_categorization.get("appointment_booked", False),
                'Conversion_Status': call_categorization.get("conversion_status", "not_booked"),

                # For New Patients
                'Script_Followed': call_categorization.get("script_followed"),  # Can be None

                # For Existing Patients
                'Call_Concern_Type': call_categorization.get("call_concern_type"),  # Can be None
                'Issue_Resolved': call_categorization.get("issue_resolved"),  # Can be None

                # Detailed Analysis (Coaching)
                'Detailed_Analysis': call_categorization.get("detailed_analysis", "")
            }

            return call_data

        except Exception as e:
            logger.error(f"Error preparing call data: {str(e)}")
            return {}
    
    def _determine_coaching_candidate(self, rep_score: float, high_value_missed: bool,
                                      sentiment: str, emotion_flags: list) -> str:
        """
        Determine if call should be flagged for coaching
        Returns: "Yes" or "No"
        """
        try:
            # Flag for coaching if:
            # - Representative score is low (below 70)
            # - High value opportunity was missed
            # - Overall sentiment is negative
            # - Critical emotion flags present (pain, anxiety, disappointment not handled well)

            coaching_triggers = []

            if rep_score < 70:
                coaching_triggers.append("low_score")

            if high_value_missed:
                coaching_triggers.append("missed_opportunity")

            if sentiment == "negative":
                coaching_triggers.append("negative_sentiment")

            # Check for unhandled critical emotions
            critical_emotions = ["PAIN", "ANXIETY", "DISAPPOINTMENT"]
            if any(emotion in emotion_flags for emotion in critical_emotions):
                coaching_triggers.append("critical_emotion")

            # If 2 or more triggers, flag for coaching
            return "Yes" if len(coaching_triggers) >= 2 else "No"

        except Exception as e:
            logger.warning(f"Error determining coaching candidate: {str(e)}")
            return "No"

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
    
    async def _export_to_existing_sheet(self, call_data: Dict) -> str:
        """Export data to the EXISTING first sheet - NO new sheets created"""

        try:
            # Get the first (existing) sheet
            existing_sheet = await self._get_first_sheet()
            if not existing_sheet:
                logger.error("Could not get existing sheet")
                return "Failed to get existing sheet"

            # Prepare row values in correct column order (31 columns total)
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
            next_row = len(existing_sheet.get_all_values()) + 1

            # Append the data - use proper column letter conversion
            last_column = self._column_number_to_letter(len(self.standard_columns))
            range_name = f"A{next_row}:{last_column}{next_row}"
            existing_sheet.update(range_name, [row_values])

            logger.info(f"Appended row {next_row} to existing sheet '{existing_sheet.title}'")
            return f"Row {next_row} in '{existing_sheet.title}'"

        except Exception as e:
            logger.error(f"Error exporting to existing sheet: {str(e)}")
            return "Export to existing sheet failed"
    
    
    def is_available(self) -> bool:
        """Check if Google Sheets export is available"""
        return self.client is not None and self.spreadsheet is not None
    
    async def get_export_status(self) -> Dict:
        """Get current export status and statistics - EXISTING SHEET ONLY"""

        if not self.is_available():
            return {
                "available": False,
                "error": "Google Sheets not configured or not available"
            }

        try:
            # Get the first (existing) sheet statistics
            all_worksheets = self.spreadsheet.worksheets()
            if not all_worksheets:
                return {
                    "available": False,
                    "error": "No sheets found in spreadsheet"
                }

            existing_sheet = all_worksheets[0]  # First sheet
            total_rows = len(existing_sheet.get_all_values())

            return {
                "available": True,
                "spreadsheet_title": self.spreadsheet.title,
                "spreadsheet_url": self.spreadsheet.url,
                "sheet_name": existing_sheet.title,
                "total_records": max(0, total_rows - 1),  # Subtract header row
                "columns_count": len(self.standard_columns),
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting export status: {str(e)}")
            return {
                "available": False,
                "error": f"Status check failed: {str(e)}"
            }