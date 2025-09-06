"""
Dental Call Analysis System - Batch Processing with API Integration
Automatically processes all audio files in directory or from API
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
from services.performance_scorer import PerformanceScorer
from services.opportunity_detector import OpportunityDetector
from services.google_sheets_exporter import GoogleSheetsExporter
from services.file_queue_service import FileQueueService

class DentalCallAnalyzer:
    """Main orchestrator for batch dental call analysis"""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.diarization_service = DiarizationService()
        self.llm_analyzer = LLMAnalyzer()
        self.performance_scorer = None  # Will be initialized after LLM
        self.opportunity_detector = None  # Will be initialized after LLM
        self.google_sheets_exporter = GoogleSheetsExporter()
        self.file_queue_service = FileQueueService()
        self.audio_processor = AudioProcessor()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'high_opportunities': 0
        }
        
    async def initialize(self):
        """Initialize all services"""
        logger.info("Initializing Dental Call Analysis System for batch processing...")
        
        try:
            # Initialize LLM analyzer first (other services depend on it)
            await self.llm_analyzer.initialize()
            
            # Initialize services that depend on LLM
            self.performance_scorer = PerformanceScorer(self.llm_analyzer)
            self.opportunity_detector = OpportunityDetector(self.llm_analyzer)
            
            # Initialize other services
            await self.transcription_service.load_model()
            await self.diarization_service.load_model()
            
            # Initialize Google Sheets connection
            await self.google_sheets_exporter.initialize()
            
            logger.info("All services initialized successfully")
            
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
        
        # Display final statistics
        self._display_final_stats()
    
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
                    # Analyze the call
                    results = await self.analyze_call(str(audio_file))
                    
                    # Mark as processed
                    self.file_queue_service.mark_as_processed(audio_file.name)
                    
                    # Update stats
                    self.stats['successful'] += 1
                    if results.get('opportunity_analysis', {}).get('high_value_missed', False):
                        self.stats['high_opportunities'] += 1
                    
                    logger.info(f"Successfully processed: {audio_file.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process {audio_file.name}: {str(e)}")
                    self.stats['failed'] += 1
                
                self.stats['total_processed'] += 1
                
                # Small delay between files to prevent overload
                await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
    
    async def _process_api_files(self):
        """Process files from API endpoint"""
        
        try:
            # Get files from API
            api_files = await self.file_queue_service.get_api_audio_files()
            
            if not api_files:
                logger.info("No new audio files found from API")
                return
            
            logger.info(f"Found {len(api_files)} files from API to process")
            
            # Process each file
            for i, file_info in enumerate(api_files, 1):
                filename = file_info.get('filename', 'unknown')
                logger.info(f"\n--- Processing API file {i}/{len(api_files)}: {filename} ---")
                
                temp_file = None
                try:
                    # Download file from API
                    logger.info(f"Downloading {filename}...")
                    temp_file = await self.file_queue_service.download_audio_file(file_info)
                    
                    # Analyze the call
                    results = await self.analyze_call(str(temp_file))
                    
                    # Update results with original filename from API
                    results['audio_file'] = filename
                    
                    # Mark as processed
                    self.file_queue_service.mark_as_processed(filename)
                    
                    # Update stats
                    self.stats['successful'] += 1
                    if results.get('opportunity_analysis', {}).get('high_value_missed', False):
                        self.stats['high_opportunities'] += 1
                    
                    logger.info(f"Successfully processed API file: {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to process API file {filename}: {str(e)}")
                    self.stats['failed'] += 1
                
                finally:
                    # Cleanup temp file
                    if temp_file:
                        self.file_queue_service.cleanup_temp_file(temp_file)
                
                self.stats['total_processed'] += 1
                
                # Delay between API files
                await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Error processing API files: {str(e)}")
    
    async def analyze_call(self, audio_file_path: str) -> Dict:
        """
        Complete call analysis pipeline (same as before but streamlined logging)
        """
        start_time = time.time()
        audio_file = Path(audio_file_path)
        
        try:
            # Step 1: Validate audio file
            if not self.audio_processor.validate_audio_file(audio_file_path):
                raise ValueError(f"Invalid or unsupported audio file: {audio_file_path}")
            
            # Step 2: Transcribe audio
            logger.info("Transcribing...")
            transcription_result = await self.transcription_service.transcribe_audio(audio_file_path)
            
            # Step 3: Speaker diarization
            logger.info("Diarizing speakers...")
            diarization_result = await self.diarization_service.diarize_speakers(audio_file_path)
            
            # Step 4: Combine transcription with speaker information
            combined_transcript = self._combine_transcription_and_speakers(
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
            
            # Step 8: Score call performance
            logger.info("Scoring performance...")
            performance_analysis = await self.performance_scorer.score_call_performance(
                combined_transcript, patient_text, staff_text
            )
            
            # Step 9: Detect missed opportunities
            logger.info("Detecting opportunities...")
            opportunity_analysis = await self.opportunity_detector.detect_opportunities(
                patient_text, staff_text, call_summary, {}
            )
            
            # Step 10: Compile final results
            processing_time = time.time() - start_time
            final_results = {
                "audio_file": audio_file.name,
                "processing_time": round(processing_time, 2),
                "transcription": transcription_result,
                "speaker_count": diarization_result["speaker_count"],
                "call_summary": call_summary,
                "representative_name": representative_name,
                "performance_analysis": performance_analysis,
                "opportunity_analysis": opportunity_analysis,
                "combined_transcript": combined_transcript,
                "analysis_method": "batch_pipeline",
                "llm_used": self.llm_analyzer.is_initialized
            }
            
            # Step 11: Export to Google Sheets (with automatic email alert)
            logger.info("Exporting...")
            export_result = await self.google_sheets_exporter.export_analysis_result(final_results)
            
            logger.info(f"Analysis completed in {processing_time:.1f}s - {export_result}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def _combine_transcription_and_speakers(self, transcription: Dict, diarization: Dict) -> Dict:
        """Combine transcription segments with speaker information"""
        
        transcript_segments = transcription["segments"]
        speaker_timeline = diarization["speaker_timeline"]
        
        combined_segments = []
        
        for segment in transcript_segments:
            start_time = segment["start_time"]
            end_time = segment["end_time"]
            
            # Find corresponding speaker
            speaker = self._find_speaker_for_timeframe(speaker_timeline, start_time, end_time)
            
            combined_segment = {
                "start_time": start_time,
                "end_time": end_time,
                "text": segment["text"],
                "speaker": speaker,
                "confidence": segment["confidence"]
            }
            
            combined_segments.append(combined_segment)
        
        return {
            "segments": combined_segments,
            "full_transcript": transcription["full_transcript"],
            "duration": transcription["duration"],
            "speaker_count": diarization["speaker_count"]
        }
    
    def _find_speaker_for_timeframe(self, speaker_timeline: list, start_time: float, end_time: float) -> str:
        """Find the most likely speaker for a given timeframe"""
        
        best_speaker = "SPEAKER_00"  # Default
        max_overlap = 0
        
        segment_duration = end_time - start_time
        
        for speaker_segment in speaker_timeline:
            overlap_start = max(start_time, speaker_segment["start_time"])
            overlap_end = min(end_time, speaker_segment["end_time"])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            overlap_percentage = overlap_duration / segment_duration if segment_duration > 0 else 0
            
            if overlap_percentage > max_overlap:
                max_overlap = overlap_percentage
                best_speaker = speaker_segment["speaker"]
        
        return best_speaker
    
    def _separate_patient_staff_speech(self, combined_transcript: Dict) -> tuple[str, str]:
        """Separate patient and staff speech"""
        
        patient_segments = []
        staff_segments = []
        
        for segment in combined_transcript["segments"]:
            if segment["speaker"] == "SPEAKER_01":  # Patient
                patient_segments.append(segment["text"])
            else:  # Staff (SPEAKER_00 or others)
                staff_segments.append(segment["text"])
        
        patient_text = " ".join(patient_segments)
        staff_text = " ".join(staff_segments)
        
        return patient_text, staff_text
    
    def _display_final_stats(self):
        """Display batch processing statistics"""
        
        print("\n" + "="*60)
        print("BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"Total Files Processed: {self.stats['total_processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"High-Value Opportunities Found: {self.stats['high_opportunities']}")
        
        if self.stats['high_opportunities'] > 0:
            print(f"\nALERT: {self.stats['high_opportunities']} high-value opportunities detected!")
            print("Email alerts have been sent for immediate follow-up.")
        
        print(f"\nMode: {'API' if settings.USE_API_MODE else 'Local Directory'}")
        print(f"Processed files tracked in: {self.file_queue_service.processed_files_db}")
        print("="*60)
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            await self.transcription_service.cleanup()
            await self.diarization_service.cleanup()
            await self.llm_analyzer.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")

async def main():
    """Main function for batch processing"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL, settings.LOGS_DIR)
    global logger
    logger = logging.getLogger(__name__)
    
    print(f"\nDental Call Analysis System - Batch Processing")
    print(f"Mode: {'API Integration' if settings.USE_API_MODE else 'Local Directory Processing'}")
    if not settings.USE_API_MODE:
        print(f"Directory: {settings.AUDIO_INPUT_DIR}")
    print("="*60)
    
    # Initialize analyzer
    analyzer = DentalCallAnalyzer()
    
    try:
        # Initialize all services
        await analyzer.initialize()
        
        # Process all available files
        await analyzer.process_all_files()
        
        logger.info("Batch processing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Batch processing interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Cleanup resources
        await analyzer.cleanup()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())