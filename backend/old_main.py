"""
Enhanced Dental Call Analysis System with Employee List Management
Main processing script with comprehensive analysis pipeline - COMPLETE VERSION
"""
import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import configuration and utilities
from config.settings import settings
from utils.logger import setup_logging
from backend.utils.audio_preprocessor import AudioProcessor

# Import all services
from services.transcription_service import TranscriptionService
from services.diarization_service import DiarizationService
from services.llm_analyzer import LLMAnalyzer
from services.llm_sentiment_analysis_service import LLMSentimentAnalysisService
from services.performance_scorer import PerformanceScorer
from services.opportunity_detector import OpportunityDetector
from services.call_tagging_service import CallTaggingService
from services.google_sheets_exporter import GoogleSheetsExporter
from services.file_queue_service import FileQueueService
from services.speaker_role_assignment_service import SpeakerRoleAssignmentService
from services.coaching_analyzer import CoachingAnalyzer
from services.employee_list_service import EmployeeListService

logger = None

class DentalCallAnalyzer:
    """Enhanced dental call analyzer with employee list management"""
    
    def __init__(self):
        # Core services
        self.transcription_service = TranscriptionService()
        self.diarization_service = DiarizationService()
        self.llm_analyzer = LLMAnalyzer()
        self.sentiment_service = LLMSentimentAnalysisService()
        self.performance_scorer = None  # Will be initialized after LLM
        self.opportunity_detector = None  # Will be initialized after LLM
        self.google_sheets_exporter = GoogleSheetsExporter()
        self.file_queue_service = FileQueueService()
        self.audio_processor = AudioProcessor()
        
        # Enhanced services
        self.call_tagging_service = None  # Will be initialized with LLM analyzer
        self.coaching_analyzer = CoachingAnalyzer()
        self.speaker_role_service = None  # Will be initialized with LLM analyzer
        
        # NEW: Employee list service
        self.employee_service = EmployeeListService()
        
        # Processing stats
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'high_opportunities': 0,
            'sentiment_stats': {
                'positive': 0,
                'neutral': 0, 
                'negative': 0
            },
            'emotion_stats': {
                'high_emotion_calls': 0,
                'pain_detected': 0,
                'anxiety_detected': 0,
                'satisfaction_detected': 0
            },
            'tagging_stats': {},
            'coaching_stats': {
                'coaching_candidates': 0,
                'excellent_calls': 0,
                'high_value_calls': 0
            },
            'speaker_assignment_stats': {
                'llm_based_assignments': 0,
                'rule_based_fallbacks': 0,
                'three_speaker_calls': 0
            }
        }
    
    async def initialize(self):
        """Initialize all services including employee list management"""
        logger.info("Initializing Enhanced Dental Call Analysis System with Employee List Management...")
        
        try:
            # Initialize LLM analyzer first (other services depend on it)
            await self.llm_analyzer.initialize()
            
            # Initialize LLM-based sentiment analysis service
            await self.sentiment_service.initialize()
            
            # Initialize services that depend on LLM
            self.performance_scorer = PerformanceScorer(self.llm_analyzer)
            self.opportunity_detector = OpportunityDetector(self.llm_analyzer)
            
            # Initialize call tagging service with LLM analyzer
            if self.llm_analyzer.is_initialized:
                self.call_tagging_service = CallTaggingService(self.llm_analyzer)
                logger.info("Call tagging service initialized")
            else:
                logger.warning("LLM analyzer not available - call tagging will use rule-based only")
                self.call_tagging_service = CallTaggingService(None)
            
            # Initialize LLM-based speaker role assignment service
            if self.llm_analyzer.is_initialized:
                self.speaker_role_service = SpeakerRoleAssignmentService(self.llm_analyzer)
                logger.info("LLM-based speaker role assignment service initialized")
            else:
                logger.warning("LLM analyzer not available - speaker role assignment will use rule-based fallback")
                self.speaker_role_service = SpeakerRoleAssignmentService(None)
            
            # Initialize other services
            await self.transcription_service.load_model()
            await self.diarization_service.load_model()
            
            # Initialize Google Sheets connection with LLM analyzer for tagging
            await self.google_sheets_exporter.initialize(self.llm_analyzer)
            
            # Log employee list status
            employees = self.employee_service.get_employees()
            logger.info(f"Employee list initialized with {len(employees)} employees: {', '.join(employees)}")
            
            logger.info("All services initialized successfully")
            logger.info(f"LLM-based Sentiment Analysis: {'Enabled' if self.sentiment_service.is_initialized else 'Fallback Mode'}")
            logger.info(f"Call Tagging System: {'LLM+Rules' if self.llm_analyzer.is_initialized else 'Rules Only'}")
            logger.info(f"Coaching Analysis: {'Active' if self.coaching_analyzer else 'Offline'}")
            logger.info(f"Speaker Role Assignment: {'LLM+Rules' if self.llm_analyzer.is_initialized else 'Rules Only'}")
            logger.info(f"Employee List Management: Active with {len(employees)} employees")            
        except Exception as e:
            logger.error(f"Service initialization failed: {str(e)}")
            raise
    
    async def process_all_files(self):
        """Process all available audio files from local directory or API"""
        
        if settings.USE_API_MODE:
            logger.info("API mode enabled - fetching files from client API")
            await self._process_api_files()
        else:
            logger.info("Local mode - processing files from audio_files directory")
            await self._process_local_files()
        
        # Display enhanced final statistics
        self._display_enhanced_final_stats()
    
    async def _process_local_files(self):
        """Process all unprocessed files from local audio_files directory"""
        
        try:
            # Get all unprocessed audio files
            audio_files = await self.file_queue_service.get_local_audio_files()
            
            if not audio_files:
                logger.info("No new audio files found to process")
                return
            
            logger.info(f"Found {len(audio_files)} files to process")
            
            # Process each file
            for i, audio_file in enumerate(audio_files, 1):
                logger.info(f"\n--- Processing file {i}/{len(audio_files)}: {audio_file.name} ---")
                
                try:
                    # Analyze the audio file with enhanced features
                    results = await self.analyze_single_file_enhanced(audio_file)
                    
                    # Update statistics
                    self.stats['total_processed'] += 1
                    self.stats['successful'] += 1
                    self._update_enhanced_stats(results)
                    
                    # Check for high-value opportunities
                    if results.get('opportunity_analysis', {}).get('high_value_missed', False):
                        self.stats['high_opportunities'] += 1
                    
                    # Mark as processed
                    self.file_queue_service.mark_as_processed(audio_file.name)
                    
                except Exception as e:
                    logger.error(f"Failed to process {audio_file.name}: {str(e)}")
                    self.stats['total_processed'] += 1
                    self.stats['failed'] += 1
                    continue
        
        except Exception as e:
            logger.error(f"Error processing local files: {str(e)}")
    
    async def _process_api_files(self):
        """Process files from API endpoint (future implementation)"""
        logger.info("API mode processing not yet implemented")
    
    async def analyze_single_file_enhanced(self, audio_file: Path) -> Dict:
        """
        Analyze a single audio file with enhanced features including employee list management
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting enhanced analysis of {audio_file.name}...")
            
            # Step 1: Validate audio file
            logger.info("Validating audio file...")
            if not self.audio_processor.validate_audio_file(str(audio_file)):
                raise Exception("Audio file validation failed")
            
            # Step 2: Transcribe audio
            logger.info("Transcribing audio...")
            transcription_result = await self.transcription_service.transcribe_audio(str(audio_file))
            
            if not transcription_result or not transcription_result.get("full_transcript"):
                raise Exception("Transcription failed or returned empty result")
            
            # Step 3: Perform speaker diarization
            logger.info("Performing speaker diarization...")
            diarization_result = await self.diarization_service.diarize_speakers(str(audio_file))
            
            # Step 4: Combine transcription with speaker labels
            logger.info("Combining transcription with speakers...")
            combined_transcript = self._combine_transcription_diarization(
                transcription_result, diarization_result
            )
            
            # Step 5: LLM-based speaker role assignment
            logger.info("Performing LLM-based speaker role assignment...")
            patient_text, staff_text = await self.speaker_role_service.assign_speaker_roles(combined_transcript)
            
            # Update speaker assignment stats
            if diarization_result.get("speaker_count", 0) >= 3:
                self.stats['speaker_assignment_stats']['three_speaker_calls'] += 1
            
            # Log the results of speaker assignment
            logger.info(f"Speaker role assignment completed - Patient: {len(patient_text)} chars, Staff: {len(staff_text)} chars")
            
            # Step 6: Generate call summary using LLM
            logger.info("Generating call summary...")
            call_summary = await self.llm_analyzer.analyze_call_summary(
                transcription_result["full_transcript"]
            )
            
            # Step 7: Extract representative name using LLM WITH EMPLOYEE LIST
            logger.info("Extracting representative name from employee list...")
            representative_name = await self.llm_analyzer.extract_representative_name(
                transcription_result["full_transcript"]
            )
            
            # Step 8: LLM-based sentiment analysis
            logger.info("Analyzing sentiment and emotions using LLM...")
            sentiment_analysis = await self.sentiment_service.analyze_call_segments_sentiment(
                patient_text, staff_text
            )
            
            # Step 9: Score call performance
            logger.info("Scoring performance...")
            performance_analysis = await self.performance_scorer.score_call_performance(
                combined_transcript, patient_text, staff_text
            )
            
            # Step 10: Detect missed opportunities
            logger.info("Detecting opportunities...")
            opportunity_analysis = await self.opportunity_detector.detect_opportunities(
                patient_text, staff_text, call_summary, {}
            )
            
            # Step 11: Call tagging analysis
            logger.info("Performing call tagging analysis...")
            call_tag_analysis = {}
            if self.call_tagging_service:
                try:
                    call_tag_analysis = await self.call_tagging_service.analyze_and_tag_call(
                        patient_text, staff_text, call_summary.get("call_summary", "")
                    )
                    logger.info(f"Call tagged as: {call_tag_analysis.get('primary_tag', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Call tagging failed: {str(e)}")
                    call_tag_analysis = {
                        'primary_tag': 'general_inquiry',
                        'confidence': 0.0,
                        'all_tags': [],
                        'tag_explanations': {}
                    }
            
            # Step 12: Coaching analysis
            logger.info("Performing coaching analysis...")
            coaching_analysis = {}
            if self.coaching_analyzer:
                try:
                    coaching_analysis = await self.coaching_analyzer.analyze_coaching_potential(
                        patient_text, staff_text, performance_analysis, sentiment_analysis
                    )
                except Exception as e:
                    logger.warning(f"Coaching analysis failed: {str(e)}")
                    coaching_analysis = {
                        'is_coaching_candidate': False,
                        'coaching_value': 'none',
                        'coaching_reasons': []
                    }
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Step 13: Compile comprehensive analysis result
            final_results = {
                "audio_file": str(audio_file),
                "transcription": transcription_result,
                "call_summary": call_summary,
                "representative_name": representative_name,  # Now uses employee list
                "sentiment_analysis": sentiment_analysis,
                "emotion_analysis": sentiment_analysis.get("emotion_analysis", {}),
                "performance_analysis": performance_analysis,
                "opportunity_analysis": opportunity_analysis,
                "combined_transcript": combined_transcript,
                "call_tag_analysis": call_tag_analysis,
                "coaching_analysis": coaching_analysis,
                "analysis_method": "enhanced_llm_based_with_employee_list",
                "llm_used": self.llm_analyzer.is_initialized,
                "sentiment_enabled": self.sentiment_service.is_initialized,
                "tagging_enabled": self.call_tagging_service is not None,
                "coaching_enabled": self.coaching_analyzer is not None,
                "speaker_role_assignment": "llm_based",
                "employee_list_used": self.employee_service.get_employees(),
                "employee_count": len(self.employee_service.get_employees()),
                "processing_time": processing_time
            }
            
            # Step 14: Export enhanced results to Google Sheets
            logger.info("Exporting enhanced results...")
            export_result = await self.google_sheets_exporter.export_analysis_result(final_results)
            
            # Log enhanced results
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            emotion_flags = sentiment_analysis.get("emotion_analysis", {}).get("emotion_flags", [])
            call_tag = call_tag_analysis.get("primary_tag", "unknown")
            is_coaching = coaching_analysis.get("is_coaching_candidate", False)
            
            logger.info(f"Enhanced analysis completed in {processing_time:.1f}s - {export_result}")
            logger.info(f"Representative: {representative_name} (from employee list)")
            logger.info(f"Overall sentiment: {overall_sentiment.get('sentiment_label', 'unknown')} "
                       f"(confidence: {overall_sentiment.get('confidence', 0):.3f})")
            logger.info(f"Call tag: {call_tag}")
            logger.info(f"Coaching candidate: {'Yes' if is_coaching else 'No'}")
            
            if emotion_flags:
                logger.info(f"Emotion flags detected: {', '.join(emotion_flags)}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {str(e)}")
            raise
    
    def _combine_transcription_diarization(self, transcription: Dict, diarization: Dict) -> Dict:
        """Combine transcription results with speaker diarization"""
        
        try:
            segments = transcription.get("segments", [])
            speaker_timeline = diarization.get("speaker_timeline", [])
            
            if not segments or not speaker_timeline:
                logger.warning("Missing segments for combination")
                return {"segments": segments}
            
            # Create a mapping of time to speaker
            def get_speaker_at_time(timestamp: float) -> str:
                """Get speaker at specific timestamp"""
                for speaker_seg in speaker_timeline:
                    if speaker_seg["start_time"] <= timestamp <= speaker_seg["end_time"]:
                        return speaker_seg["speaker"]
                return "SPEAKER_00"  # Default speaker
            
            # Assign speakers to transcription segments
            combined_segments = []
            for segment in segments:
                segment_start = segment.get("start_time", 0)
                segment_end = segment.get("end_time", segment_start + 1)
                segment_speaker = get_speaker_at_time(segment_start)
                
                # Use consistent field names
                combined_segment = {
                    "start_time": segment_start,
                    "end_time": segment_end,
                    "text": segment.get("text", ""),
                    "speaker": segment_speaker
                }
                combined_segments.append(combined_segment)
            
            return {"segments": combined_segments}
            
        except Exception as e:
            logger.error(f"Error combining transcription and diarization: {str(e)}")
            return {"segments": transcription.get("segments", [])}
    
    def _update_enhanced_stats(self, results: Dict):
        """Update enhanced statistics including employee list usage"""
        
        # Update existing stats
        try:
            sentiment_analysis = results.get("sentiment_analysis", {})
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            sentiment_label = overall_sentiment.get("sentiment_label", "unknown")
            
            if sentiment_label in self.stats['sentiment_stats']:
                self.stats['sentiment_stats'][sentiment_label] += 1
        except Exception as e:
            logger.warning(f"Failed to update sentiment stats: {str(e)}")
        
        try:
            emotion_analysis = results.get("emotion_analysis", {})
            emotion_flags = emotion_analysis.get("emotion_flags", [])
            patient_emotions = emotion_analysis.get("patient_emotions", {})
            
            if patient_emotions.get("intensity") == "high":
                self.stats['emotion_stats']['high_emotion_calls'] += 1
            
            for flag in emotion_flags:
                if "PAIN" in flag or "pain" in flag.lower():
                    self.stats['emotion_stats']['pain_detected'] += 1
                elif "ANXIETY" in flag or "anxiety" in flag.lower():
                    self.stats['emotion_stats']['anxiety_detected'] += 1
                elif "SATISFACTION" in flag or "satisfaction" in flag.lower():
                    self.stats['emotion_stats']['satisfaction_detected'] += 1
        except Exception as e:
            logger.warning(f"Failed to update emotion stats: {str(e)}")
        
        try:
            call_tag_analysis = results.get("call_tag_analysis", {})
            primary_tag = call_tag_analysis.get("primary_tag", "unknown")
            
            if primary_tag not in self.stats['tagging_stats']:
                self.stats['tagging_stats'][primary_tag] = 0
            self.stats['tagging_stats'][primary_tag] += 1
        except Exception as e:
            logger.warning(f"Failed to update tagging stats: {str(e)}")
        
        try:
            coaching_analysis = results.get("coaching_analysis", {})
            if coaching_analysis.get("is_coaching_candidate", False):
                self.stats['coaching_stats']['coaching_candidates'] += 1
                
                coaching_value = coaching_analysis.get("coaching_value", "none")
                if coaching_value == "excellent":
                    self.stats['coaching_stats']['excellent_calls'] += 1
                elif coaching_value in ["high", "excellent"]:
                    self.stats['coaching_stats']['high_value_calls'] += 1
        except Exception as e:
            logger.warning(f"Failed to update coaching stats: {str(e)}")
        
        # Update speaker assignment stats
        try:
            if results.get("speaker_role_assignment") == "llm_based":
                self.stats['speaker_assignment_stats']['llm_based_assignments'] += 1
            else:
                self.stats['speaker_assignment_stats']['rule_based_fallbacks'] += 1
        except Exception as e:
            logger.warning(f"Failed to update speaker assignment stats: {str(e)}")
    
    def _display_enhanced_final_stats(self):
        """Display enhanced final processing statistics"""
        print("\n" + "="*80)
        print("ENHANCED DENTAL CALL ANALYSIS - FINAL REPORT")
        print("="*80)
        
        # Processing summary
        print(f"\nðŸ“Š PROCESSING SUMMARY:")
        print(f"   Total calls processed: {self.stats['total_processed']}")
        print(f"   Successful: {self.stats['successful']}")
        print(f"   Failed: {self.stats['failed']}")
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_processed']) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        # Employee list summary
        employees = self.employee_service.get_employees()
        print(f"\nðŸ‘¥ EMPLOYEE LIST MANAGEMENT:")
        print(f"   Configured employees: {len(employees)}")
        print(f"   Employee names: {', '.join(employees)}")
        
        # Opportunity analysis
        print(f"\nðŸŽ¯ OPPORTUNITY ANALYSIS:")
        print(f"   High-value missed opportunities: {self.stats['high_opportunities']}")
        if self.stats['successful'] > 0:
            opportunity_rate = (self.stats['high_opportunities'] / self.stats['successful']) * 100
            print(f"   Missed opportunity rate: {opportunity_rate:.1f}%")
        
        # Sentiment analysis
        print(f"\nðŸ˜Š SENTIMENT ANALYSIS:")
        for sentiment, count in self.stats['sentiment_stats'].items():
            if count > 0:
                print(f"   {sentiment.title()}: {count}")
        
        # Emotion analysis
        print(f"\nðŸŽ­ EMOTION ANALYSIS:")
        for emotion, count in self.stats['emotion_stats'].items():
            if count > 0:
                print(f"   {emotion.replace('_', ' ').title()}: {count}")
        
        # Call tagging
        if self.stats['tagging_stats']:
            print(f"\nðŸ·ï¸  CALL TAGGING:")
            for tag, count in self.stats['tagging_stats'].items():
                if count > 0:
                    print(f"   {tag.replace('_', ' ').title()}: {count}")
        
        # Coaching analysis
        print(f"\nðŸŽ“ COACHING ANALYSIS:")
        print(f"   Coaching candidates: {self.stats['coaching_stats']['coaching_candidates']}")
        print(f"   Excellent calls: {self.stats['coaching_stats']['excellent_calls']}")
        print(f"   High-value calls: {self.stats['coaching_stats']['high_value_calls']}")
        
        # Speaker assignment stats
        print(f"\nðŸ—£ï¸  SPEAKER ASSIGNMENT:")
        print(f"   LLM-based assignments: {self.stats['speaker_assignment_stats']['llm_based_assignments']}")
        print(f"   Rule-based fallbacks: {self.stats['speaker_assignment_stats']['rule_based_fallbacks']}")
        print(f"   Three+ speaker calls: {self.stats['speaker_assignment_stats']['three_speaker_calls']}")
        
        # Export information
        if settings.USE_GOOGLE_SHEETS:
            print("\nðŸ“Š Results exported to Google Sheets for dashboard viewing")
        
        print("\nðŸŽ¯ Coaching candidates and excellent examples are now flagged in Google Sheets.")
        print("ðŸ·ï¸  All calls have been automatically categorized for better organization.")
        print("ðŸ—£ï¸  Speaker roles are now intelligently assigned using LLM analysis.")
        print("ðŸ‘¥ Representative names are extracted from predefined employee list.")
        
        print(f"\nMode: {'API' if settings.USE_API_MODE else 'Local Directory'}")
        print(f"Enhanced Features: Tagging âœ… | Coaching Analysis âœ… | Emotion Detection âœ… | Smart Speaker Assignment âœ… | Employee List âœ…")
        print(f"Processed files tracked in: {self.file_queue_service.processed_files_db}")
        print(f"Employee list stored in: {self.employee_service.employees_file}")
        print("="*80)
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            await self.transcription_service.cleanup()
            await self.diarization_service.cleanup()
            await self.llm_analyzer.cleanup()
            await self.sentiment_service.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")

async def main():
    """Main function for enhanced batch processing with employee list management"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL, settings.LOGS_DIR)
    global logger
    logger = logging.getLogger(__name__)
    
    print(f"\nðŸ¦· Enhanced Dental Call Analysis System")
    print(f"ðŸ”¥ Features: LLM Sentiment Analysis | Auto Call Tagging | Coaching Analysis | Smart Speaker Assignment | Employee List Management")
    print(f"Mode: {'API Integration' if settings.USE_API_MODE else 'Local Directory Processing'}")
    if not settings.USE_API_MODE:
        print(f"Directory: {settings.AUDIO_INPUT_DIR}")
    print("="*80)
    
    # Initialize analyzer
    analyzer = DentalCallAnalyzer()
    
    try:
        # Initialize all services
        await analyzer.initialize()
        
        # Process all available files
        await analyzer.process_all_files()
        
        logger.info("Enhanced batch processing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Batch processing interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Enhanced batch processing failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Cleanup resources
        await analyzer.cleanup()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())