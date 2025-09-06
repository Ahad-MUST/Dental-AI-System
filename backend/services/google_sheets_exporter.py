"""
Google Sheets export service with detailed transcripts and email alerts
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
    """Export call analysis results to Google Sheets with detailed transcripts"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self.credentials_file = settings.GOOGLE_CREDENTIALS_FILE
        self.use_google_sheets = settings.USE_GOOGLE_SHEETS
        self.client = None
        self.worksheet = None
        self.email_alert_service = EmailAlertService()
        
    async def initialize(self):
        """Initialize Google Sheets connection"""
        
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
            
            # Initialize headers if sheet is empty
            await self._ensure_headers_exist()
            
            logger.info("Google Sheets connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {str(e)}")
            logger.info("Falling back to CSV export")
            self.use_google_sheets = False
    
    async def _ensure_headers_exist(self):
        """Ensure the sheet has the correct headers including transcript"""
        
        try:
            # Check if headers already exist
            existing_values = self.worksheet.row_values(1)
            
            expected_headers = [
                "Call_File_Name",
                "Analysis_Date",
                "Analysis_Time", 
                "Full_Transcript_With_Timestamps",  # MOVED BEFORE Call_Summary
                "Call_Summary",
                "Representative_Name",
                "Representative_Score",
                "High_Value_Missed_Opportunity"
            ]
            
            if not existing_values or len(existing_values) < len(expected_headers):
                # Set headers in first row
                self.worksheet.update('A1:H1', [expected_headers])
                logger.info("Google Sheet headers updated with transcript column")
                
        except Exception as e:
            logger.error(f"Failed to set Google Sheet headers: {str(e)}")
    
    async def export_analysis_result(self, analysis_result: Dict) -> str:
        """
        Export analysis result to Google Sheets + send email alert if high opportunity missed
        """
        try:
            # Extract file info  
            audio_file = analysis_result.get("audio_file", "unknown.wav")
            file_stem = Path(audio_file).stem
            
            # Create detailed transcript file with timestamps
            transcript_path = self._export_detailed_transcript_file(analysis_result, file_stem)
            
            # Prepare row data (now includes timestamped transcript)
            row_data = self._prepare_row_data_with_transcript(analysis_result)
            
            # Check for high-value opportunity
            opportunity_analysis = analysis_result.get("opportunity_analysis", {})
            high_value_missed = opportunity_analysis.get("high_value_missed", False)
            
            logger.info(f"DEBUGGING - High value missed: {high_value_missed} (type: {type(high_value_missed)})")
            
            if self.use_google_sheets and self.worksheet:
                # Export to Google Sheets
                await self._append_to_google_sheet(row_data)
                logger.info(f"Results exported to Google Sheets")
                
                # Send email alert if high-value opportunity missed
                if high_value_missed is True or high_value_missed == True:
                    logger.info("HIGH-VALUE OPPORTUNITY DETECTED - SENDING EMAIL ALERT...")
                    try:
                        email_sent = await self.email_alert_service.send_high_opportunity_alert(analysis_result)
                        if email_sent:
                            logger.info("EMAIL ALERT SENT SUCCESSFULLY!")
                        else:
                            logger.error("EMAIL ALERT FAILED TO SEND!")
                    except Exception as email_error:
                        logger.error(f"EMAIL ALERT ERROR: {str(email_error)}")
                else:
                    logger.info(f"No high-value opportunity - email alert not needed")
                
                logger.info(f"Detailed transcript exported to: {transcript_path}")
                return "Google Sheets"
            else:
                # Fallback to CSV
                return await self._fallback_csv_export(analysis_result, transcript_path, high_value_missed)
                
        except Exception as e:
            logger.error(f"Google Sheets export failed: {str(e)}")
            # Fallback to CSV
            return await self._fallback_csv_export(analysis_result, transcript_path, high_value_missed)
    
    def _prepare_row_data_with_transcript(self, result: Dict) -> List:
        """Prepare row data for Google Sheets including timestamped transcript"""
        
        # Extract key information
        transcription = result.get("transcription", {})
        performance = result.get("performance_analysis", {})
        call_summary = result.get("call_summary", {})
        opportunity_analysis = result.get("opportunity_analysis", {})
        representative_name = result.get("representative_name", "Unknown")
        combined_transcript = result.get("combined_transcript", {})
        
        # Create timestamped transcript for sheet
        timestamped_transcript = self._create_timestamped_transcript(combined_transcript)
        
        # Prepare row data (now with transcript before summary)
        row_data = [
            result.get("audio_file", "unknown.wav"),
            datetime.now().strftime("%m/%d/%Y"),  # US format
            datetime.now().strftime("%H:%M:%S"),
            timestamped_transcript,  # TRANSCRIPT COLUMN (4th position)
            call_summary.get("call_summary", "Summary unavailable"),  # SUMMARY (5th position)
            representative_name,
            round(performance.get("overall_score", 0.0), 2),
            opportunity_analysis.get("high_value_missed", False)
        ]
        
        return row_data
    
    def _create_timestamped_transcript(self, combined_transcript: Dict) -> str:
        """Create timestamped transcript for Google Sheets"""
        
        segments = combined_transcript.get("segments", [])
        if not segments:
            return "Transcript not available"
        
        timestamped_lines = []
        for segment in segments:
            start_time = segment.get("start_time", 0)
            end_time = segment.get("end_time", 0)
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            
            if text:  # Only add segments with actual text
                # Format time as MM:SS
                start_formatted = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
                end_formatted = f"{int(end_time//60):02d}:{int(end_time%60):02d}"
                
                # Create timestamp entry
                timestamped_lines.append(f"[{start_formatted}-{end_formatted}] {speaker}: {text}")
        
        return "\n".join(timestamped_lines)
    
    def _export_detailed_transcript_file(self, result: Dict, file_stem: str) -> str:
        """Export detailed transcript file with speaker timestamps"""
        
        try:
            transcript_filename = f"{file_stem}_transcription.txt"
            transcript_path = self.output_dir / transcript_filename
            
            # Get data
            transcription = result.get("transcription", {})
            combined_transcript = result.get("combined_transcript", {})
            representative_name = result.get("representative_name", "Unknown")
            
            # Create detailed transcript file
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(f"DENTAL CALL TRANSCRIPTION\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(f"File: {result.get('audio_file', 'unknown.wav')}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {transcription.get('duration', 0):.1f} seconds\n")
                f.write(f"Speakers: {result.get('speaker_count', 0)}\n")
                f.write(f"Representative: {representative_name}\n\n")
                
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
                
                f.write(f"\n" + "=" * 50 + "\n")
                f.write("FULL TRANSCRIPT (No Timestamps):\n")
                f.write("-" * 35 + "\n")
                f.write(transcription.get("full_transcript", "Transcript not available"))
                f.write(f"\n\n" + "=" * 50 + "\n")
                f.write("End of Transcription")
            
            return str(transcript_path)
            
        except Exception as e:
            logger.error(f"Transcript export failed: {str(e)}")
            return ""
    
    async def _append_to_google_sheet(self, row_data: List):
        """Append row to Google Sheet (now with 8 columns)"""
        
        try:
            # Find next empty row
            values = self.worksheet.get_all_values()
            next_row = len(values) + 1
            
            # Append the row (A to H columns)
            range_name = f"A{next_row}:H{next_row}"
            self.worksheet.update(range_name, [row_data])
            
            logger.info(f"Added row {next_row} to Google Sheet with transcript")
            
        except Exception as e:
            logger.error(f"Failed to append to Google Sheet: {str(e)}")
            raise
    
    async def _fallback_csv_export(self, analysis_result: Dict, transcript_path: str, high_value_missed: bool) -> str:
        """Fallback to CSV export with email alert support"""
        
        try:
            from services.csv_exporter import CSVExporter
            csv_exporter = CSVExporter()
            csv_path = csv_exporter.export_analysis_result(analysis_result)
            
            # Send email alert even in CSV fallback mode
            if high_value_missed:
                logger.info("High-value opportunity detected - sending email alert...")
                email_sent = await self.email_alert_service.send_high_opportunity_alert(analysis_result)
                if email_sent:
                    logger.info("Email alert sent successfully")
                else:
                    logger.warning("Email alert failed to send")
            
            logger.info(f"Fallback CSV export completed: {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.error(f"Even CSV fallback failed: {str(e)}")
            return "Export failed"