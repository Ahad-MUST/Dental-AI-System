"""
Google Sheets export service - SIMPLIFIED VERSION with only 2 new columns
Call_Tag and Coaching_Candidate (Yes/No)
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import json

from config.settings import settings
from services.email_alert_service import EmailAlertService

# Google Sheets imports
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

logger = logging.getLogger(__name__)

class GoogleSheetsExporter:
    """Export call analysis results to Google Sheets with simplified 2 new columns: Call_Tag and Coaching_Candidate"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self.credentials_file = settings.GOOGLE_CREDENTIALS_FILE
        self.use_google_sheets = settings.USE_GOOGLE_SHEETS
        self.client = None
        self.worksheet = None
        self.email_alert_service = EmailAlertService()
        
        # Store LLM analyzer reference for tagging
        self.llm_analyzer = None
        
        # PREDEFINED CALL CATEGORIES - No new categories per call
        self.predefined_categories = [
            "new_patient",
            "emergency", 
            "insurance",
            "appointment_booking",
            "appointment_confirm",
            "appointment_cancel",
            "general_inquiry",
            "cleaning",
            "cosmetic",
            "major_treatment",
            "billing"
        ]
        
    async def initialize(self, llm_analyzer=None):
        """Initialize Google Sheets connection"""
        
        # Store LLM analyzer reference
        self.llm_analyzer = llm_analyzer
        
        if not self.use_google_sheets:
            logger.info("Google Sheets disabled, using CSV fallback")
            return
            
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.warning("Google Sheets libraries not installed. Run: pip install gspread google-auth")
            self.use_google_sheets = False
            return
            
        try:
            # Load credentials
            if not self.credentials_file.exists():
                logger.error(f"Google credentials file not found: {self.credentials_file}")
                self.use_google_sheets = False
                return
                
            # Authenticate with Google Sheets
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scope
            )
            
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            if not self.sheet_id:
                logger.error("Google Sheet ID not provided in .env file")
                self.use_google_sheets = False
                return
                
            spreadsheet = self.client.open_by_key(self.sheet_id)
            self.worksheet = spreadsheet.sheet1  # Use first sheet
            
            # Initialize headers with simplified columns
            await self._ensure_simplified_headers_exist()
            
            logger.info("Google Sheets connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            logger.info("Falling back to CSV export")
            self.use_google_sheets = False
    
    async def _ensure_simplified_headers_exist(self):
        """Ensure the sheet has headers with ONLY 2 new columns: Call_Tag and Coaching_Candidate"""
        
        try:
            # Check if headers already exist
            existing_values = self.worksheet.row_values(1)
            
            # SIMPLIFIED headers - keeping existing + only 2 new columns
            expected_headers = [
                "Call_File_Name",                    # A
                "Analysis_Date",                     # B
                "Analysis_Time",                     # C
                "Full_Transcript_With_Timestamps",   # D
                "Call_Summary",                      # E
                "Representative_Name",               # F
                "Representative_Score",              # G
                "High_Value_Missed_Opportunity",     # H
                "Patient_Sentiment",                 # I - Existing sentiment
                "Staff_Sentiment",                   # J - Existing sentiment
                "Overall_Sentiment",                 # K - Existing sentiment
                "Sentiment_Confidence",              # L - Existing sentiment
                "Sentiment_Summary",                 # M - Existing sentiment
                "Patient_Primary_Emotion",           # N - Existing emotion
                "Patient_Emotion_Confidence",        # O - Existing emotion
                "Patient_Emotion_Intensity",         # P - Existing emotion
                "Staff_Primary_Emotion",             # Q - Existing emotion
                "Staff_Emotion_Confidence",          # R - Existing emotion
                "Emotion_Flags",                     # S - Existing emotion
                "Call_Emotional_Health",             # T - Existing emotion
                "Emotional_Alignment",               # U - Existing emotion
                "Escalation_Pattern",                # V - Existing emotion
                "Call_Tag",                          # W - NEW: Predefined call category
                "Coaching_Candidate"                 # X - NEW: Yes/No for coaching
            ]
            
            # Update headers if needed (W and X columns only)
            if not existing_values or len(existing_values) < len(expected_headers):
                # Set headers in first row (A1 to X1)
                self.worksheet.update('A1:X1', [expected_headers])
                logger.info("Google Sheet headers updated with simplified Call_Tag and Coaching_Candidate columns")
                
        except Exception as e:
            logger.error(f"Failed to set Google Sheet headers: {str(e)}")
    
    async def export_analysis_result(self, analysis_result: Dict) -> str:
        """Export analysis result to Google Sheets with simplified 2 new columns"""
        
        # Initialize transcript path for detailed export
        audio_file = analysis_result.get("audio_file", "unknown.wav")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_filename = f"transcript_{Path(audio_file).stem}_{timestamp}.txt"
        transcript_path = self.output_dir / transcript_filename
        
        try:
            if self.use_google_sheets and self.worksheet:
                logger.info("Exporting to Google Sheets with simplified tagging and coaching...")
                
                # Prepare simplified row data
                row_data = await self._prepare_simplified_row_data(analysis_result)
                
                # Append to Google Sheets
                await self._append_simplified_to_google_sheet(row_data)
                
                # Check for high-value missed opportunities and send email
                high_value_missed = analysis_result.get("opportunity_analysis", {}).get("high_value_missed", False)
                
                if high_value_missed and self.email_alert_service.is_configured():
                    try:
                        email_success = await self.email_alert_service.send_opportunity_alert(analysis_result)
                        if email_success:
                            logger.info("HIGH-VALUE OPPORTUNITY EMAIL ALERT SENT!")
                        else:
                            logger.error("EMAIL ALERT FAILED TO SEND!")
                    except Exception as email_error:
                        logger.error(f"EMAIL ALERT ERROR: {str(email_error)}")
                else:
                    logger.info(f"No high-value opportunity - email alert not needed")
                
                # Export detailed transcript
                await self._export_detailed_transcript(analysis_result, transcript_path, high_value_missed)
                
                logger.info(f"Simplified analysis exported to Google Sheets with transcript: {transcript_path}")
                return "Google Sheets"
            else:
                # Fallback to CSV
                return await self._fallback_csv_export(analysis_result, transcript_path, high_value_missed)
                
        except Exception as e:
            logger.error(f"Google Sheets export failed: {str(e)}")
            # Fallback to CSV
            return await self._fallback_csv_export(analysis_result, transcript_path, high_value_missed)
    
    async def _prepare_simplified_row_data(self, result: Dict) -> List:
        """Prepare row data with ONLY 2 new columns: Call_Tag and Coaching_Candidate"""
        
        # Extract key information
        transcription = result.get("transcription", {})
        performance = result.get("performance_analysis", {})
        call_summary = result.get("call_summary", {})
        opportunity_analysis = result.get("opportunity_analysis", {})
        representative_name = result.get("representative_name", "Unknown")
        combined_transcript = result.get("combined_transcript", {})
        sentiment_analysis = result.get("sentiment_analysis", {})
        emotion_analysis = result.get("emotion_analysis", {})
        call_tag_analysis = result.get("call_tag_analysis", {})
        coaching_analysis = result.get("coaching_analysis", {})
        
        # Create timestamped transcript
        timestamped_transcript = self._create_timestamped_transcript(combined_transcript)
        
        # Extract sentiment data
        patient_sentiment = sentiment_analysis.get("patient_sentiment", {})
        staff_sentiment = sentiment_analysis.get("staff_sentiment", {})
        overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
        sentiment_summary = sentiment_analysis.get("sentiment_summary", "No sentiment analysis available")
        
        # Extract emotion data
        patient_emotions = emotion_analysis.get("patient_emotions", {})
        staff_emotions = emotion_analysis.get("staff_emotions", {})
        call_dynamics = emotion_analysis.get("call_dynamics", {})
        emotion_flags = emotion_analysis.get("emotion_flags", [])
        
        # Get primary emotions
        patient_primary_emotion = patient_emotions.get("primary_emotion", {})
        staff_primary_emotion = staff_emotions.get("primary_emotion", {})
        
        # Get emotional health and alignment
        emotional_health = call_dynamics.get("call_emotional_health", {})
        emotional_alignment = call_dynamics.get("emotional_alignment", {})
        escalation_pattern = call_dynamics.get("escalation_pattern", {})
        
        # Get call tag from predefined categories
        raw_call_tag = call_tag_analysis.get("primary_tag", "general_inquiry")
        call_tag = raw_call_tag if raw_call_tag in self.predefined_categories else "general_inquiry"
        
        # Get coaching candidate (Yes/No)
        is_coaching_candidate = coaching_analysis.get("is_coaching_candidate", False)
        coaching_candidate = "Yes" if is_coaching_candidate else "No"
        
        # Prepare simplified row data (24 columns total - existing 22 + 2 new)
        row_data = [
            result.get("audio_file", "unknown.wav"),                                    # A
            datetime.now().strftime("%m/%d/%Y"),                                        # B
            datetime.now().strftime("%H:%M:%S"),                                        # C
            timestamped_transcript,                                                     # D
            call_summary.get("call_summary", "Summary unavailable"),                   # E
            representative_name,                                                        # F
            round(performance.get("overall_score", 0.0), 2),                          # G
            opportunity_analysis.get("high_value_missed", False),                      # H
            patient_sentiment.get("sentiment_label", "unknown"),                       # I
            staff_sentiment.get("sentiment_label", "unknown"),                         # J
            overall_sentiment.get("sentiment_label", "unknown"),                       # K
            round(overall_sentiment.get("confidence", 0.0), 3),                       # L
            sentiment_summary,                                                          # M
            patient_primary_emotion.get("emotion", "unknown"),                         # N
            round(patient_primary_emotion.get("confidence", 0.0), 3),                 # O
            patient_emotions.get("intensity", "unknown"),                              # P
            staff_primary_emotion.get("emotion", "unknown"),                           # Q
            round(staff_primary_emotion.get("confidence", 0.0), 3),                   # R
            ", ".join(emotion_flags) if emotion_flags else "None",                     # S
            emotional_health.get("health_level", "unknown"),                           # T
            emotional_alignment.get("alignment_score", "unknown"),                     # U
            escalation_pattern.get("pattern_detected", "None"),                        # V
            # SIMPLIFIED NEW COLUMNS (only 2):
            call_tag,                                                                   # W - Call Tag (predefined only)
            coaching_candidate                                                          # X - Coaching Candidate (Yes/No)
        ]
        
        return row_data
    
    def _create_timestamped_transcript(self, combined_transcript: Dict) -> str:
        """Create a timestamped transcript for the sheet"""
        
        segments = combined_transcript.get("segments", [])
        if not segments:
            return "No timestamped transcript available"
        
        transcript_lines = []
        
        for segment in segments:
            start_time = segment.get("start_time", 0)
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            
            if text:  # Only include segments with actual text
                # Format time as MM:SS
                start_formatted = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
                transcript_lines.append(f"[{start_formatted}] {speaker}: {text}")
        
        return "\n".join(transcript_lines)
    
    async def _append_simplified_to_google_sheet(self, row_data: List):
        """Append row to Google Sheet with simplified columns (24 columns total)"""
        
        try:
            # Find next empty row
            values = self.worksheet.get_all_values()
            next_row = len(values) + 1
            
            # Append the row (A to X columns - 24 columns)
            range_name = f"A{next_row}:X{next_row}"
            self.worksheet.update(range_name, [row_data])
            
            logger.info(f"Added simplified row {next_row} to Google Sheet")
            
        except Exception as e:
            logger.error(f"Failed to append simplified row to Google Sheet: {str(e)}")
            raise
    
    async def _export_detailed_transcript(self, result: Dict, transcript_path: Path, high_value_missed: bool):
        """Export detailed transcript (unchanged from existing implementation)"""
        
        try:
            # Create output directory if it doesn't exist
            transcript_path.parent.mkdir(parents=True, exist_ok=True)
            
            transcription = result.get("transcription", {})
            performance = result.get("performance_analysis", {})
            call_summary = result.get("call_summary", {})
            opportunity_analysis = result.get("opportunity_analysis", {})
            representative_name = result.get("representative_name", "Unknown")
            combined_transcript = result.get("combined_transcript", {})
            sentiment_analysis = result.get("sentiment_analysis", {})
            emotion_analysis = result.get("emotion_analysis", {})
            
            # Extract sentiment and emotion data
            patient_sentiment = sentiment_analysis.get("patient_sentiment", {})
            staff_sentiment = sentiment_analysis.get("staff_sentiment", {})
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            
            patient_emotions = emotion_analysis.get("patient_emotions", {})
            staff_emotions = emotion_analysis.get("staff_emotions", {})
            call_dynamics = emotion_analysis.get("call_dynamics", {})
            emotion_flags = emotion_analysis.get("emotion_flags", [])
            
            # Write comprehensive transcript file
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write("DENTAL CALL ANALYSIS REPORT\n")
                f.write("=" * 70 + "\n\n")
                
                # Basic call information
                f.write("CALL INFORMATION:\n")
                f.write("-" * 20 + "\n")
                f.write(f"File: {result.get('audio_file', 'unknown.wav')}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {transcription.get('duration', 0):.1f} seconds\n")
                f.write(f"Speakers: {result.get('speaker_count', 0)}\n")
                f.write(f"Representative: {representative_name}\n\n")
                
                # Performance summary
                f.write("PERFORMANCE SUMMARY:\n")
                f.write("-" * 25 + "\n")
                f.write(f"Overall Score: {performance.get('overall_score', 0):.2f}/100\n")
                f.write(f"Call Summary: {call_summary.get('call_summary', 'N/A')}\n")
                f.write(f"High-Value Missed Opportunity: {'YES' if high_value_missed else 'NO'}\n\n")
                
                # Sentiment analysis summary
                f.write("SENTIMENT ANALYSIS SUMMARY:\n")
                f.write("-" * 35 + "\n")
                f.write(f"Patient Sentiment: {patient_sentiment.get('sentiment_label', 'unknown')} ")
                f.write(f"(confidence: {patient_sentiment.get('confidence', 0):.3f})\n")
                f.write(f"Staff Sentiment: {staff_sentiment.get('sentiment_label', 'unknown')} ")
                f.write(f"(confidence: {staff_sentiment.get('confidence', 0):.3f})\n")
                f.write(f"Overall Sentiment: {overall_sentiment.get('sentiment_label', 'unknown')} ")
                f.write(f"(confidence: {overall_sentiment.get('confidence', 0):.3f})\n")
                f.write(f"Summary: {sentiment_analysis.get('sentiment_summary', 'No summary available')}\n\n")
                
                # Write timestamped transcript
                f.write("TIMESTAMPED TRANSCRIPT:\n")
                f.write("-" * 25 + "\n")
                
                segments = combined_transcript.get("segments", [])
                if segments:
                    for segment in segments:
                        start_time = segment.get("start_time", 0)
                        end_time = segment.get("end_time", 0)
                        speaker = segment.get("speaker", "UNKNOWN")
                        text = segment.get("text", "").strip()
                        
                        if text:  # Only write segments with actual text
                            # Format time as MM:SS
                            start_formatted = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
                            end_formatted = f"{int(end_time//60):02d}:{int(end_time%60):02d}"
                            
                            f.write(f"[{start_formatted}-{end_formatted}] {speaker}: {text}\n")
                else:
                    f.write("No timestamped segments available\n")
                
                f.write(f"\n" + "=" * 70 + "\n")
                f.write("End of Analysis Report")
            
            return str(transcript_path)
            
        except Exception as e:
            logger.error(f"Transcript export failed: {str(e)}")
            return ""
    
    async def _fallback_csv_export(self, analysis_result: Dict, transcript_path: str, high_value_missed: bool) -> str:
        """Fallback to CSV export when Google Sheets is unavailable"""
        
        try:
            from services.csv_exporter import CSVExporter
            
            csv_exporter = CSVExporter()
            await csv_exporter.initialize()
            
            # Export to CSV
            csv_path = await csv_exporter.export_analysis_result(analysis_result)
            
            # Send email alert even in CSV fallback mode
            if high_value_missed and self.email_alert_service.is_configured():
                logger.info("High-value opportunity detected - sending email alert...")
                email_sent = await self.email_alert_service.send_opportunity_alert(analysis_result)
                if email_sent:
                    logger.info("Email alert sent successfully")
                else:
                    logger.warning("Email alert failed to send")
            
            # Export detailed transcript
            await self._export_detailed_transcript(analysis_result, transcript_path, high_value_missed)
            
            logger.info(f"Fallback CSV export completed: {csv_path}")
            return f"CSV: {csv_path}"
            
        except Exception as e:
            logger.error(f"Fallback CSV export failed: {str(e)}")
            return "Export failed"