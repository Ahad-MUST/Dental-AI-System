"""
Enhanced CSV export service with detailed transcripts, sentiment analysis, emotion detection, call tagging, and coaching analysis
"""
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from config.settings import settings

logger = logging.getLogger(__name__)

class CSVExporter:
    """Export call analysis results to CSV with enhanced features including call tagging and coaching analysis"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.csv_file = self.output_dir / settings.CSV_FILENAME
        
    async def initialize(self):
        """Initialize CSV exporter with enhanced headers"""
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create CSV with enhanced headers if it doesn't exist
        if not self.csv_file.exists():
            self._create_enhanced_csv_headers()
            logger.info(f"Created enhanced CSV file: {self.csv_file}")
        else:
            # Check if we need to update headers for new columns
            df = pd.read_csv(self.csv_file)
            expected_columns = self._get_enhanced_column_names()
            
            # Add missing columns if needed
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                for col in missing_columns:
                    df[col] = ""  # Add empty column
                df.to_csv(self.csv_file, index=False)
                logger.info(f"Updated CSV with new columns: {missing_columns}")
    
    def _get_enhanced_column_names(self) -> List[str]:
        """Get the complete list of column names including new features"""
        
        return [
            "Call_File_Name",
            "Analysis_Date", 
            "Analysis_Time",
            "Full_Transcript_With_Timestamps",
            "Call_Summary",
            "Representative_Name",
            "Representative_Score",
            "High_Value_Missed_Opportunity",
            # Sentiment columns
            "Patient_Sentiment",
            "Staff_Sentiment",
            "Overall_Sentiment",
            "Sentiment_Confidence",
            "Sentiment_Summary",
            # Emotion columns
            "Patient_Primary_Emotion",
            "Patient_Emotion_Confidence",
            "Patient_Emotion_Intensity",
            "Staff_Primary_Emotion",
            "Staff_Emotion_Confidence",
            "Emotion_Flags",
            "Call_Emotional_Health",
            "Emotional_Alignment",
            "Escalation_Pattern",
            # NEW: Call tagging columns
            "Call_Tag",
            "Call_Tag_Confidence",
            # NEW: Coaching analysis columns
            "Coaching_Candidate",
            "Coaching_Score",
            "Coaching_Category",
            "Coaching_Value"
        ]
    
    def _create_enhanced_csv_headers(self):
        """Create CSV file with enhanced headers including call tagging and coaching columns"""
        
        columns = self._get_enhanced_column_names()
        df = pd.DataFrame(columns=columns)
        df.to_csv(self.csv_file, index=False)
        
        logger.info(f"Created enhanced CSV with {len(columns)} columns: {self.csv_file}")
    
    async def export_analysis_result(self, analysis_result: Dict) -> str:
        """
        Export enhanced analysis result to CSV
        """
        
        try:
            # Prepare enhanced row data
            row_data = await self._prepare_enhanced_row_data(analysis_result)
            
            # Append to CSV
            self._append_to_csv(row_data)
            
            # Export detailed transcript if enabled
            if settings.EXPORT_DETAILED_REPORTS:
                transcript_path = await self._export_detailed_transcript(analysis_result)
                logger.info(f"Detailed transcript exported to: {transcript_path}")
            
            logger.info(f"Enhanced analysis exported to CSV: {self.csv_file}")
            return str(self.csv_file)
            
        except Exception as e:
            logger.error(f"Enhanced CSV export failed: {str(e)}")
            return ""
    
    async def _prepare_enhanced_row_data(self, result: Dict) -> Dict:
        """Prepare row data for CSV including all enhanced features"""
        
        # Extract key information
        transcription = result.get("transcription", {})
        performance = result.get("performance_analysis", {})
        call_summary = result.get("call_summary", {})
        opportunity_analysis = result.get("opportunity_analysis", {})
        representative_name = result.get("representative_name", "Unknown")
        combined_transcript = result.get("combined_transcript", {})
        sentiment_analysis = result.get("sentiment_analysis", {})
        emotion_analysis = result.get("emotion_analysis", {})
        call_tag_analysis = result.get("call_tag_analysis", {})  # NEW
        coaching_analysis = result.get("coaching_analysis", {})  # NEW
        
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
        
        # Prepare complete row data dictionary
        row_data = {
            "Call_File_Name": result.get("audio_file", "unknown.wav"),
            "Analysis_Date": datetime.now().strftime("%m/%d/%Y"),
            "Analysis_Time": datetime.now().strftime("%H:%M:%S"),
            "Full_Transcript_With_Timestamps": timestamped_transcript,
            "Call_Summary": call_summary.get("call_summary", "Summary unavailable"),
            "Representative_Name": representative_name,
            "Representative_Score": round(performance.get("overall_score", 0.0), 2),
            "High_Value_Missed_Opportunity": opportunity_analysis.get("high_value_missed", False),
            # Sentiment data
            "Patient_Sentiment": patient_sentiment.get("sentiment_label", "unknown"),
            "Staff_Sentiment": staff_sentiment.get("sentiment_label", "unknown"),
            "Overall_Sentiment": overall_sentiment.get("sentiment_label", "unknown"),
            "Sentiment_Confidence": round(overall_sentiment.get("confidence", 0.0), 3),
            "Sentiment_Summary": sentiment_summary,
            # Emotion data
            "Patient_Primary_Emotion": patient_primary_emotion.get("emotion", "unknown"),
            "Patient_Emotion_Confidence": round(patient_primary_emotion.get("confidence", 0.0), 3),
            "Patient_Emotion_Intensity": patient_emotions.get("intensity", "unknown"),
            "Staff_Primary_Emotion": staff_primary_emotion.get("emotion", "unknown"),
            "Staff_Emotion_Confidence": round(staff_primary_emotion.get("confidence", 0.0), 3),
            "Emotion_Flags": ", ".join(emotion_flags) if emotion_flags else "None",
            "Call_Emotional_Health": emotional_health.get("health_level", "unknown"),
            "Emotional_Alignment": emotional_alignment.get("alignment_score", "unknown"),
            "Escalation_Pattern": escalation_pattern.get("pattern_detected", "None"),
            # NEW: Call tagging data
            "Call_Tag": call_tag_analysis.get("primary_tag", "general_inquiry"),
            "Call_Tag_Confidence": round(call_tag_analysis.get("confidence_score", 0.0), 3),
            # NEW: Coaching analysis data
            "Coaching_Candidate": coaching_analysis.get("is_coaching_candidate", False),
            "Coaching_Score": coaching_analysis.get("coaching_score", 0),
            "Coaching_Category": coaching_analysis.get("coaching_category", "none"),
            "Coaching_Value": coaching_analysis.get("coaching_value", "none")
        }
        
        return row_data
    
    def _create_timestamped_transcript(self, combined_transcript: Dict) -> str:
        """Create a timestamped transcript for CSV"""
        
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
    
    def _append_to_csv(self, row_data: Dict):
        """Append single row to existing CSV"""
        
        try:
            df = pd.read_csv(self.csv_file)
        except Exception as e:
            logger.warning(f"Could not read existing CSV: {str(e)}, creating new one")
            self._create_enhanced_csv_headers()
            df = pd.read_csv(self.csv_file)
        
        # Add new row
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        
        # Write back to CSV
        df.to_csv(self.csv_file, index=False)
    
    async def _export_detailed_transcript(self, result: Dict) -> str:
        """Export detailed transcript with all enhanced analysis data"""
        
        try:
            # Create transcript filename
            audio_file = result.get("audio_file", "unknown.wav")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_filename = f"enhanced_transcript_{Path(audio_file).stem}_{timestamp}.txt"
            transcript_path = self.output_dir / transcript_filename
            
            # Extract all analysis data
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
            
            # Extract detailed data
            patient_sentiment = sentiment_analysis.get("patient_sentiment", {})
            staff_sentiment = sentiment_analysis.get("staff_sentiment", {})
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            
            patient_emotions = emotion_analysis.get("patient_emotions", {})
            staff_emotions = emotion_analysis.get("staff_emotions", {})
            call_dynamics = emotion_analysis.get("call_dynamics", {})
            emotion_flags = emotion_analysis.get("emotion_flags", [])
            
            # Write comprehensive transcript file
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write("ENHANCED DENTAL CALL ANALYSIS REPORT\n")
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
                f.write(f"High-Value Missed Opportunity: {'YES' if opportunity_analysis.get('high_value_missed', False) else 'NO'}\n\n")
                
                # NEW: Enhanced call tagging information
                f.write("CALL TAGGING ANALYSIS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Primary Tag: {call_tag_analysis.get('primary_tag', 'unknown')}\n")
                f.write(f"Tag Confidence: {call_tag_analysis.get('confidence_score', 0):.3f}\n")
                f.write(f"Tag Reasoning: {call_tag_analysis.get('reasoning', 'N/A')}\n")
                if call_tag_analysis.get('keyword_matches'):
                    f.write(f"Matched Keywords: {', '.join(call_tag_analysis['keyword_matches'])}\n")
                if call_tag_analysis.get('pattern_matches'):
                    f.write(f"Matched Patterns: {len(call_tag_analysis['pattern_matches'])} patterns\n")
                f.write(f"\n")
                
                # NEW: Enhanced coaching analysis
                f.write("COACHING ANALYSIS:\n")
                f.write("-" * 25 + "\n")
                f.write(f"Coaching Candidate: {'YES' if coaching_analysis.get('is_coaching_candidate') else 'NO'}\n")
                f.write(f"Coaching Score: {coaching_analysis.get('coaching_score', 0)}/100\n")
                f.write(f"Coaching Value: {coaching_analysis.get('coaching_value', 'none').title()}\n")
                f.write(f"Coaching Category: {coaching_analysis.get('coaching_category', 'none')}\n")
                
                if coaching_analysis.get('strengths_demonstrated'):
                    f.write(f"\nStrengths Demonstrated:\n")
                    for strength in coaching_analysis['strengths_demonstrated']:
                        f.write(f"  • {strength}\n")
                
                if coaching_analysis.get('usage_recommendations'):
                    f.write(f"\nTraining Usage Recommendations:\n")
                    for rec in coaching_analysis['usage_recommendations']:
                        f.write(f"  • {rec}\n")
                
                if coaching_analysis.get('reasons_included'):
                    f.write(f"\nReasons for Inclusion:\n")
                    for reason in coaching_analysis['reasons_included']:
                        f.write(f"  • {reason}\n")
                
                if coaching_analysis.get('reasons_excluded'):
                    f.write(f"\nReasons for Exclusion:\n")
                    for reason in coaching_analysis['reasons_excluded']:
                        f.write(f"  • {reason}\n")
                f.write(f"\n")
                
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
                
                # Emotion analysis summary
                f.write("EMOTION DETECTION SUMMARY:\n")
                f.write("-" * 32 + "\n")
                
                # Patient emotions
                patient_primary = patient_emotions.get("primary_emotion", {})
                f.write(f"Patient Primary Emotion: {patient_primary.get('emotion', 'unknown')} ")
                f.write(f"(confidence: {patient_primary.get('confidence', 0):.3f})\n")
                f.write(f"Patient Emotion Intensity: {patient_emotions.get('intensity', 'unknown')}\n")
                
                # Staff emotions
                staff_primary = staff_emotions.get("primary_emotion", {})
                f.write(f"Staff Primary Emotion: {staff_primary.get('emotion', 'unknown')} ")
                f.write(f"(confidence: {staff_primary.get('confidence', 0):.3f})\n")
                
                # Emotion flags
                if emotion_flags:
                    f.write(f"Emotion Flags: {', '.join(emotion_flags)}\n")
                
                # Call dynamics
                f.write(f"Call Emotional Health: {call_dynamics.get('call_emotional_health', {}).get('health_level', 'unknown')}\n")
                f.write(f"Emotional Alignment: {call_dynamics.get('emotional_alignment', {}).get('alignment_score', 'unknown')}\n")
                f.write(f"Escalation Pattern: {call_dynamics.get('escalation_pattern', {}).get('pattern_detected', 'None')}\n\n")
                
                # Performance breakdown
                if performance.get('component_scores'):
                    f.write("PERFORMANCE BREAKDOWN:\n")
                    f.write("-" * 30 + "\n")
                    for component, score in performance['component_scores'].items():
                        f.write(f"{component.replace('_', ' ').title()}: {score:.2f}\n")
                    f.write(f"\n")
                
                # Strengths and weaknesses
                if performance.get('strengths'):
                    f.write("STRENGTHS:\n")
                    f.write("-" * 15 + "\n")
                    for strength in performance['strengths']:
                        f.write(f"• {strength}\n")
                    f.write(f"\n")
                
                if performance.get('weaknesses'):
                    f.write("AREAS FOR IMPROVEMENT:\n")
                    f.write("-" * 30 + "\n")
                    for weakness in performance['weaknesses']:
                        f.write(f"• {weakness}\n")
                    f.write(f"\n")
                
                # Coaching focus areas
                if performance.get('coaching_focus'):
                    f.write("COACHING FOCUS AREAS:\n")
                    f.write("-" * 30 + "\n")
                    for focus in performance['coaching_focus']:
                        f.write(f"• {focus}\n")
                    f.write(f"\n")
                
                # Write detailed sentiment scores
                f.write("DETAILED SENTIMENT SCORES:\n")
                f.write("-" * 30 + "\n")
                f.write("Patient Sentiment Breakdown:\n")
                patient_sent_scores = patient_sentiment.get("all_scores", {})
                for sentiment, score in patient_sent_scores.items():
                    f.write(f"  {sentiment.title()}: {score:.3f}\n")
                    
                f.write("\nStaff Sentiment Breakdown:\n")
                staff_sent_scores = staff_sentiment.get("all_scores", {})
                for sentiment, score in staff_sent_scores.items():
                    f.write(f"  {sentiment.title()}: {score:.3f}\n")
                    
                f.write("\nOverall Call Sentiment Breakdown:\n")
                overall_sent_scores = overall_sentiment.get("all_scores", {})
                for sentiment, score in overall_sent_scores.items():
                    f.write(f"  {sentiment.title()}: {score:.3f}\n")
                
                f.write(f"\n")
                
                # Write detailed emotion scores
                f.write("DETAILED EMOTION SCORES:\n")
                f.write("-" * 28 + "\n")
                
                # Patient emotion details
                f.write("Patient Emotion Breakdown:\n")
                patient_all_emotions = patient_emotions.get("all_emotions", {})
                for emotion, score in patient_all_emotions.items():
                    f.write(f"  {emotion.title()}: {score:.3f}\n")
                
                # Staff emotion details  
                f.write("\nStaff Emotion Breakdown:\n")
                staff_all_emotions = staff_emotions.get("all_emotions", {})
                for emotion, score in staff_all_emotions.items():
                    f.write(f"  {emotion.title()}: {score:.3f}\n")
                
                f.write(f"\n")
                
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
                f.write("End of Enhanced Analysis Report")
            
            return str(transcript_path)
            
        except Exception as e:
            logger.error(f"Enhanced transcript export failed: {str(e)}")
            return ""
    
    def get_csv_path(self) -> str:
        """Get the path to the CSV file"""
        return str(self.csv_file)
    
    def get_statistics(self) -> Dict:
        """Get statistics from the CSV data"""
        
        try:
            if not self.csv_file.exists():
                return {"error": "No CSV file found"}
            
            df = pd.read_csv(self.csv_file)
            
            if df.empty:
                return {"error": "CSV file is empty"}
            
            stats = {
                "total_calls": len(df),
                "average_rep_score": df['Representative_Score'].mean() if 'Representative_Score' in df.columns else 0,
                "missed_opportunities": df['High_Value_Missed_Opportunity'].sum() if 'High_Value_Missed_Opportunity' in df.columns else 0,
                "coaching_candidates": df['Coaching_Candidate'].sum() if 'Coaching_Candidate' in df.columns else 0,
                "sentiment_distribution": df['Overall_Sentiment'].value_counts().to_dict() if 'Overall_Sentiment' in df.columns else {},
                "tag_distribution": df['Call_Tag'].value_counts().to_dict() if 'Call_Tag' in df.columns else {},
                "coaching_value_distribution": df['Coaching_Value'].value_counts().to_dict() if 'Coaching_Value' in df.columns else {}
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {"error": str(e)}