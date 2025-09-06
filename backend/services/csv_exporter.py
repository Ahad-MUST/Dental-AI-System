"""
CSV export service with timestamped transcripts
"""
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
from config.settings import settings

logger = logging.getLogger(__name__)

class CSVExporter:
    """Export call analysis results with timestamped transcripts"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.csv_file = self.output_dir / settings.CSV_FILENAME
        
    def export_analysis_result(self, analysis_result: Dict) -> str:
        """
        Export analysis result to CSV + create detailed transcript file
        
        Args:
            analysis_result: Complete analysis result from main pipeline
            
        Returns:
            str: Path to CSV file
        """
        try:
            # Extract file info
            audio_file = analysis_result.get("audio_file", "unknown.wav")
            file_stem = Path(audio_file).stem
            
            # Create detailed transcript file
            transcript_path = self._export_detailed_transcript_file(analysis_result, file_stem)
            
            # Prepare CSV row data with transcript
            csv_row = self._prepare_csv_row_with_transcript(analysis_result)
            
            # Check if CSV exists, if not create with headers
            if not self.csv_file.exists():
                self._create_csv_with_transcript_headers()
            
            # Append to CSV
            self._append_to_csv(csv_row)
            
            logger.info(f"Results exported to CSV: {self.csv_file}")
            logger.info(f"Detailed transcript exported to: {transcript_path}")
            return str(self.csv_file)
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            raise
    
    def _prepare_csv_row_with_transcript(self, result: Dict) -> Dict:
        """Prepare CSV row with timestamped transcript included"""
        
        # Extract key information
        transcription = result.get("transcription", {})
        performance = result.get("performance_analysis", {})
        call_summary = result.get("call_summary", {})
        opportunity_analysis = result.get("opportunity_analysis", {})
        representative_name = result.get("representative_name", "Unknown")
        combined_transcript = result.get("combined_transcript", {})
        
        # Create timestamped transcript
        timestamped_transcript = self._create_timestamped_transcript(combined_transcript)
        
        # CSV row with transcript before summary
        csv_row = {
            "Call_File_Name": result.get("audio_file", "unknown.wav"),
            "Analysis_Date": datetime.now().strftime("%m/%d/%Y"),  # US format
            "Analysis_Time": datetime.now().strftime("%H:%M:%S"),
            "Full_Transcript_With_Timestamps": timestamped_transcript,  # 4th position
            "Call_Summary": call_summary.get("call_summary", "Summary unavailable"),  # 5th position
            "Representative_Name": representative_name,
            "Representative_Score": round(performance.get("overall_score", 0.0), 2),
            "High_Value_Missed_Opportunity": opportunity_analysis.get("high_value_missed", False)
        }
        
        return csv_row
    
    def _create_timestamped_transcript(self, combined_transcript: Dict) -> str:
        """Create timestamped transcript string"""
        
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
        
        return " | ".join(timestamped_lines)  # Use | separator for CSV
    
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
    
    def _create_csv_with_transcript_headers(self):
        """Create CSV file with headers including transcript column"""
        
        # Headers with transcript before summary
        columns_with_transcript = [
            "Call_File_Name",
            "Analysis_Date", 
            "Analysis_Time",
            "Full_Transcript_With_Timestamps",  # 4th position
            "Call_Summary",  # 5th position
            "Representative_Name",
            "Representative_Score",
            "High_Value_Missed_Opportunity"
        ]
        
        df = pd.DataFrame(columns=columns_with_transcript)
        df.to_csv(self.csv_file, index=False)
        
        logger.info(f"Created CSV with transcript column: {self.csv_file}")
    
    def _append_to_csv(self, row_data: Dict):
        """Append single row to existing CSV"""
        
        try:
            df = pd.read_csv(self.csv_file)
        except Exception as e:
            logger.warning(f"Could not read existing CSV: {str(e)}, creating new one")
            self._create_csv_with_transcript_headers()
            df = pd.read_csv(self.csv_file)
        
        # Add new row
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        
        # Write back to CSV
        df.to_csv(self.csv_file, index=False)
    
    def get_csv_path(self) -> str:
        """Get the path to the CSV file"""
        return str(self.csv_file)