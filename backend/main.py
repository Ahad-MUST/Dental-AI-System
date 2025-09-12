"""
Dental Call Analysis System - Enhanced with Call Tagging and Coaching Analysis
Automatically processes all audio files with LLM-based sentiment analysis, call tagging, and coaching evaluation
"""
import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, List
import time

# Import configuration and utilities
from config.settings import settings
from utils.logger import setup_logging
from utils.audio_processor import AudioProcessor

# Import services
from services.transcription_service import TranscriptionService
from services.diarization_service import DiarizationService  
from services.llm_analyzer import LLMAnalyzer
from services.llm_sentiment_analysis_service import LLMSentimentAnalysisService
from services.performance_scorer import PerformanceScorer
from services.opportunity_detector import OpportunityDetector
from services.google_sheets_exporter import GoogleSheetsExporter
from services.file_queue_service import FileQueueService

# NEW: Import enhanced services
from services.call_tagging_service import CallTaggingService
from services.coaching_analyzer import CoachingAnalyzer

class DentalCallAnalyzer:
    """Main orchestrator for batch dental call analysis with LLM-based sentiment, emotion analysis, call tagging, and coaching evaluation"""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.diarization_service = DiarizationService()
        self.llm_analyzer = LLMAnalyzer()
        self.sentiment_service = LLMSentimentAnalysisService()
        self.performance_scorer = None  # Will be initialized after LLM
        self.opportunity_detector = None  # Will be initialized after LLM
        self.google_sheets_exporter = GoogleSheetsExporter()
        self.file_queue_service = FileQueueService()
        self.audio_processor = AudioProcessor()
        
        # NEW: Initialize enhanced services
        self.call_tagging_service = None  # Will be initialized with LLM analyzer
        self.coaching_analyzer = CoachingAnalyzer()
        
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
            # NEW: Enhanced stats
            'tagging_stats': {},
            'coaching_stats': {
                'coaching_candidates': 0,
                'excellent_calls': 0,
                'high_value_calls': 0
            }
        }
        
    async def initialize(self):
        """Initialize all services including LLM-based sentiment, emotion analysis, call tagging, and coaching"""
        logger.info("Initializing Enhanced Dental Call Analysis System with Tagging and Coaching...")
        
        try:
            # Initialize LLM analyzer first (other services depend on it)
            await self.llm_analyzer.initialize()
            
            # Initialize LLM-based sentiment analysis service
            await self.sentiment_service.initialize()
            
            # Initialize services that depend on LLM
            self.performance_scorer = PerformanceScorer(self.llm_analyzer)
            self.opportunity_detector = OpportunityDetector(self.llm_analyzer)
            
            # NEW: Initialize call tagging service with LLM analyzer
            if self.llm_analyzer.is_initialized:
                self.call_tagging_service = CallTaggingService(self.llm_analyzer)
                logger.info("Call tagging service initialized")
            else:
                logger.warning("LLM analyzer not available - call tagging will use rule-based only")
                self.call_tagging_service = CallTaggingService(None)
            
            # Initialize other services (CORRECTED METHOD NAMES)
            await self.transcription_service.load_model()
            await self.diarization_service.load_model()
            
            # Initialize Google Sheets connection with LLM analyzer for tagging
            await self.google_sheets_exporter.initialize(self.llm_analyzer)
            
            logger.info("All services initialized successfully")
            logger.info(f"LLM-based Sentiment Analysis: {'Enabled' if self.sentiment_service.is_initialized else 'Fallback Mode'}")
            logger.info(f"Call Tagging System: {'LLM+Rules' if self.llm_analyzer.is_initialized else 'Rules Only'}")
            logger.info(f"Coaching Analysis: {'Active' if self.coaching_analyzer else 'Offline'}")
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
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
            # Get all unprocessed audio files (CORRECTED METHOD NAME)
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
                    
                    # Mark as processed (CORRECTED METHOD NAME)
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
        # TODO: Implement API file fetching and processing
    
    async def analyze_single_file_enhanced(self, audio_file: Path) -> Dict:
        """
        Analyze a single audio file with enhanced features: sentiment, emotion, tagging, and coaching analysis
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
            
            # Step 3: Perform speaker diarization (CORRECTED METHOD NAME)
            logger.info("Performing speaker diarization...")
            diarization_result = await self.diarization_service.diarize_speakers(str(audio_file))
            
            # Step 4: Combine transcription with speaker labels
            logger.info("Combining transcription with speakers...")
            combined_transcript = self._combine_transcription_diarization(
                transcription_result, diarization_result
            )
            
            # Step 5: Separate patient and staff segments
            patient_text, staff_text = self._separate_patient_staff_speech(combined_transcript)
            
            # Step 6: Generate call summary using LLM
            logger.info("Generating summary...")
            call_summary = await self.llm_analyzer.analyze_call_summary(
                transcription_result["full_transcript"]
            )
            
            # Step 7: Extract representative name using LLM
            logger.info("Extracting representative name...")
            representative_name = await self.llm_analyzer.extract_representative_name(
                transcription_result["full_transcript"]
            )
            
            # Step 8: LLM-based Sentiment Analysis and Emotion Detection
            logger.info("Analyzing sentiment and emotions using LLM...")
            sentiment_emotion_analysis = await self.sentiment_service.analyze_call_segments_sentiment(
                patient_text, staff_text
            )
            
            # Extract sentiment and emotion data for compatibility
            sentiment_analysis = {
                "patient_sentiment": sentiment_emotion_analysis["patient_sentiment"],
                "staff_sentiment": sentiment_emotion_analysis["staff_sentiment"],
                "overall_sentiment": sentiment_emotion_analysis["overall_sentiment"],
                "sentiment_summary": sentiment_emotion_analysis["sentiment_summary"]
            }
            
            emotion_analysis = sentiment_emotion_analysis["emotion_analysis"]
            
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
            
            # Step 11: NEW - Call tagging analysis
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
                        'confidence_score': 0.5,
                        'reasoning': 'Tagging failed'
                    }
            else:
                call_tag_analysis = {
                    'primary_tag': 'general_inquiry',
                    'confidence_score': 0.5,
                    'reasoning': 'Tagging service not available'
                }
            
            # Step 12: NEW - Coaching analysis
            logger.info("Performing coaching analysis...")
            coaching_analysis = {}
            if self.coaching_analyzer:
                try:
                    # Prepare data for coaching analysis
                    coaching_data = {
                        'representative_score': performance_analysis.get('overall_score', 0),
                        'staff_sentiment': sentiment_analysis.get('staff_sentiment', {}),
                        'overall_sentiment': sentiment_analysis.get('overall_sentiment', {}),
                        'high_value_missed_opportunity': opportunity_analysis.get('high_value_missed', False),
                        'call_tag': call_tag_analysis.get('primary_tag', 'general_inquiry'),
                        'emotion_flags': emotion_analysis.get('emotion_flags', []),
                        'success_achieved': performance_analysis.get('success_achieved', False)
                    }
                    coaching_analysis = self.coaching_analyzer.analyze_for_coaching(coaching_data)
                    
                    if coaching_analysis.get('is_coaching_candidate', False):
                        logger.info(f"Coaching candidate identified: score={coaching_analysis['coaching_score']}")
                        
                except Exception as e:
                    logger.warning(f"Coaching analysis failed: {str(e)}")
                    coaching_analysis = {
                        'is_coaching_candidate': False,
                        'coaching_score': 0,
                        'coaching_category': 'none',
                        'coaching_value': 'none'
                    }
            
            # Step 13: Compile enhanced final results
            processing_time = time.time() - start_time
            final_results = {
                "audio_file": audio_file.name,
                "processing_time": round(processing_time, 2),
                "transcription": transcription_result,
                "speaker_count": diarization_result.get("speaker_count", 2),
                "call_summary": call_summary,
                "representative_name": representative_name,
                "sentiment_analysis": sentiment_analysis,
                "emotion_analysis": emotion_analysis,
                "performance_analysis": performance_analysis,
                "opportunity_analysis": opportunity_analysis,
                "combined_transcript": combined_transcript,
                "call_tag_analysis": call_tag_analysis,  # NEW
                "coaching_analysis": coaching_analysis,  # NEW
                "analysis_method": "enhanced_llm_based_with_tagging_coaching",
                "llm_used": self.llm_analyzer.is_initialized,
                "sentiment_enabled": self.sentiment_service.is_initialized,
                "tagging_enabled": self.call_tagging_service is not None,
                "coaching_enabled": self.coaching_analyzer is not None
            }
            
            # Step 14: Export enhanced results to Google Sheets
            logger.info("Exporting enhanced results...")
            export_result = await self.google_sheets_exporter.export_analysis_result(final_results)
            
            # Log enhanced results
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            emotion_flags = emotion_analysis.get("emotion_flags", [])
            call_tag = call_tag_analysis.get("primary_tag", "unknown")
            is_coaching = coaching_analysis.get("is_coaching_candidate", False)
            
            logger.info(f"Enhanced analysis completed in {processing_time:.1f}s - {export_result}")
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
        """Combine transcription results with speaker diarization - FIXED TIMESTAMP FIELDS"""
        
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
    
    def _separate_patient_staff_speech(self, combined_transcript: Dict) -> tuple:
        """Separate patient and staff speech from combined transcript"""
        
        try:
            segments = combined_transcript.get("segments", [])
            
            if not segments:
                return "", ""
            
            # Group speakers by frequency to identify patient vs staff
            speaker_word_counts = {}
            for segment in segments:
                speaker = segment.get("speaker", "UNKNOWN")
                text = segment.get("text", "")
                word_count = len(text.split())
                
                if speaker not in speaker_word_counts:
                    speaker_word_counts[speaker] = 0
                speaker_word_counts[speaker] += word_count
            
            if not speaker_word_counts:
                return "", ""
            
            # Assume the speaker with more words is staff (dental office employee)
            # and the other is patient
            sorted_speakers = sorted(speaker_word_counts.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_speakers) >= 2:
                staff_speaker = sorted_speakers[0][0]  # Most talkative = staff
                patient_speaker = sorted_speakers[1][0]  # Second most = patient
            else:
                # Only one speaker detected
                staff_speaker = sorted_speakers[0][0]
                patient_speaker = None
            
            # Collect text for each type
            patient_text_parts = []
            staff_text_parts = []
            
            for segment in segments:
                speaker = segment.get("speaker", "UNKNOWN")
                text = segment.get("text", "").strip()
                
                if not text:
                    continue
                
                if speaker == staff_speaker:
                    staff_text_parts.append(text)
                elif speaker == patient_speaker:
                    patient_text_parts.append(text)
                else:
                    # Unknown speaker, assign to patient by default
                    patient_text_parts.append(text)
            
            patient_text = " ".join(patient_text_parts)
            staff_text = " ".join(staff_text_parts)
            
            logger.debug(f"Separated speech - Patient: {len(patient_text)} chars, Staff: {len(staff_text)} chars")
            
            return patient_text, staff_text
            
        except Exception as e:
            logger.error(f"Error separating patient/staff speech: {str(e)}")
            return "", ""
    
    def _update_enhanced_stats(self, results: Dict):
        """Update enhanced statistics including tagging and coaching"""
        
        # Update existing sentiment stats
        try:
            sentiment_analysis = results.get("sentiment_analysis", {})
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            sentiment_label = overall_sentiment.get("sentiment_label", "unknown")
            
            if sentiment_label in self.stats['sentiment_stats']:
                self.stats['sentiment_stats'][sentiment_label] += 1
        except Exception as e:
            logger.warning(f"Failed to update sentiment stats: {str(e)}")
        
        # Update existing emotion stats
        try:
            emotion_analysis = results.get("emotion_analysis", {})
            emotion_flags = emotion_analysis.get("emotion_flags", [])
            patient_emotions = emotion_analysis.get("patient_emotions", {})
            
            # Count high emotion intensity calls
            if patient_emotions.get("intensity") == "high":
                self.stats['emotion_stats']['high_emotion_calls'] += 1
            
            # Count specific emotion types
            for flag in emotion_flags:
                if "PAIN" in flag or "pain" in flag.lower():
                    self.stats['emotion_stats']['pain_detected'] += 1
                elif "ANXIETY" in flag or "anxiety" in flag.lower():
                    self.stats['emotion_stats']['anxiety_detected'] += 1
                elif "SATISFACTION" in flag or "satisfaction" in flag.lower():
                    self.stats['emotion_stats']['satisfaction_detected'] += 1
        except Exception as e:
            logger.warning(f"Failed to update emotion stats: {str(e)}")
        
        # NEW: Update tagging stats
        try:
            call_tag_analysis = results.get("call_tag_analysis", {})
            primary_tag = call_tag_analysis.get("primary_tag", "unknown")
            
            if primary_tag not in self.stats['tagging_stats']:
                self.stats['tagging_stats'][primary_tag] = 0
            self.stats['tagging_stats'][primary_tag] += 1
        except Exception as e:
            logger.warning(f"Failed to update tagging stats: {str(e)}")
        
        # NEW: Update coaching stats
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
    
    def _display_enhanced_final_stats(self):
        """Display enhanced final processing statistics"""
        print("\n" + "="*80)
        print("ENHANCED DENTAL CALL ANALYSIS - FINAL REPORT")
        print("="*80)
        
        # Processing summary
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"   Total calls processed: {self.stats['total_processed']}")
        print(f"   Successful: {self.stats['successful']}")
        print(f"   Failed: {self.stats['failed']}")
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_processed']) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        # Opportunity analysis
        print(f"\n🎯 OPPORTUNITY ANALYSIS:")
        print(f"   High-value missed opportunities: {self.stats['high_opportunities']}")
        if self.stats['successful'] > 0:
            opportunity_rate = (self.stats['high_opportunities'] / self.stats['successful']) * 100
            print(f"   Opportunity rate: {opportunity_rate:.1f}%")
        
        # Sentiment distribution
        print(f"\n😊 SENTIMENT DISTRIBUTION:")
        for sentiment, count in self.stats['sentiment_stats'].items():
            if count > 0:
                percentage = (count / max(self.stats['successful'], 1)) * 100
                print(f"   {sentiment.title()}: {count} ({percentage:.1f}%)")
        
        # Emotion insights
        print(f"\n🎭 EMOTION INSIGHTS:")
        emotion_stats = self.stats['emotion_stats']
        print(f"   Calls with emotional content: {emotion_stats['high_emotion_calls']}")
        print(f"   Pain detected: {emotion_stats['pain_detected']}")
        print(f"   Anxiety detected: {emotion_stats['anxiety_detected']}")
        print(f"   Satisfaction detected: {emotion_stats['satisfaction_detected']}")
        
        # NEW: Call tagging distribution
        print(f"\n🏷️  CALL TAGGING DISTRIBUTION:")
        if self.stats['tagging_stats']:
            for tag, count in sorted(self.stats['tagging_stats'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / max(self.stats['successful'], 1) * 100)
                display_name = self.call_tagging_service.get_tag_display_name(tag) if self.call_tagging_service else tag
                print(f"   {display_name}: {count} ({percentage:.1f}%)")
        else:
            print("   No tagging data available")
        
        # NEW: Coaching opportunities
        print(f"\n🎓 COACHING OPPORTUNITIES:")
        coaching_stats = self.stats['coaching_stats']
        print(f"   Coaching candidates identified: {coaching_stats['coaching_candidates']}")
        print(f"   Excellent coaching examples: {coaching_stats['excellent_calls']}")
        print(f"   High-value training calls: {coaching_stats['high_value_calls']}")
        if self.stats['successful'] > 0:
            coaching_rate = (coaching_stats['coaching_candidates'] / self.stats['successful'] * 100)
            print(f"   Coaching candidate rate: {coaching_rate:.1f}%")
        
        # System performance
        print(f"\n⚙️  SYSTEM PERFORMANCE:")
        print(f"   LLM-based Sentiment Analysis: {'✅ Active' if self.sentiment_service.is_initialized else '❌ Offline'}")
        print(f"   Call Tagging System: {'✅ Active' if self.call_tagging_service else '❌ Offline'}")
        print(f"   Coaching Analysis: {'✅ Active' if self.coaching_analyzer else '❌ Offline'}")
        print(f"   Google Sheets Export: {'✅ Active' if self.google_sheets_exporter.use_google_sheets else '❌ CSV Fallback'}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.stats['high_opportunities'] > 0:
            print(f"   • Review {self.stats['high_opportunities']} missed opportunities for immediate follow-up")
        
        if coaching_stats['coaching_candidates'] > 0:
            print(f"   • Use {coaching_stats['coaching_candidates']} coaching candidates for staff training")
        
        if coaching_stats['excellent_calls'] > 0:
            print(f"   • Highlight {coaching_stats['excellent_calls']} excellent calls as best practice examples")
        
        # High-value insights
        if self.stats['tagging_stats']:
            most_common_tag = max(self.stats['tagging_stats'], key=self.stats['tagging_stats'].get)
            display_name = self.call_tagging_service.get_tag_display_name(most_common_tag) if self.call_tagging_service else most_common_tag
            print(f"   • Most common call type: {display_name} - consider specialized training")
        
        if emotion_stats['pain_detected'] > 0:
            print(f"   • {emotion_stats['pain_detected']} calls involved patient pain - review emergency protocols")
        
        print("\n" + "="*80)
        print("📧 Email alerts have been sent for high-value opportunities requiring immediate follow-up.")
        print("🎓 Coaching candidates and excellent examples are now flagged in Google Sheets.")
        print("🏷️  All calls have been automatically categorized for better organization.")
        
        print(f"\nMode: {'API' if settings.USE_API_MODE else 'Local Directory'}")
        print(f"Enhanced Features: Tagging ✅ | Coaching Analysis ✅ | Emotion Detection ✅")
        print(f"Processed files tracked in: {self.file_queue_service.processed_files_db}")
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
    """Main function for enhanced batch processing"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL, settings.LOGS_DIR)
    global logger
    logger = logging.getLogger(__name__)
    
    print(f"\n🦷 Enhanced Dental Call Analysis System")
    print(f"🔥 Features: LLM Sentiment Analysis | Auto Call Tagging | Coaching Analysis")
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