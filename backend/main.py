"""
Dental Call Analysis System with Employee List Management
Main processing script with comprehensive analysis pipeline - REFACTORED VERSION
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Import configuration and utilities
from config.settings import settings
from utils.logger import setup_logging
# REMOVED: from utils.audio_processor import AudioProcessor  # This is now handled by AudioPreprocessor

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
from services.call_categorization_service import CallCategorizationService  # NEW

# Import new modular components
from call_analyzer import CallAnalyzer
from stats_manager import StatsManager

logger = None

class DentalCallAnalyzer:
    """Dental call analyzer with employee list management - Refactored"""
    
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
        # REMOVED: self.audio_processor = AudioProcessor()  # Now handled by CallAnalyzer's AudioPreprocessor
        
        # Services
        self.call_tagging_service = None  # Will be initialized with LLM analyzer
        self.coaching_analyzer = CoachingAnalyzer()
        self.speaker_role_service = None  # Will be initialized with LLM analyzer
        self.call_categorization_service = None  # NEW: Will be initialized for patient type/booking tracking

        # NEW: Employee list service
        self.employee_service = EmployeeListService()
        
        # Initialize modular components
        self.call_analyzer = None  # Will be initialized after services
        self.stats_manager = None  # Will be initialized after services
    
    async def initialize(self):
        """Initialize all services including employee list management"""
        logger.info("Initializing Dental Call Analysis System with Employee List Management...")
        
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

            # NEW: Initialize call categorization service (patient type, booking status, etc.)
            self.call_categorization_service = CallCategorizationService()
            await self.call_categorization_service.initialize()
            logger.info("Call categorization service initialized (patient type, booking tracking)")

            # Initialize other services
            await self.transcription_service.load_model()
            await self.diarization_service.load_model()
            
            # Initialize Google Sheets connection with LLM analyzer for tagging
            await self.google_sheets_exporter.initialize(self.llm_analyzer)
            
            # Initialize modular components
            services_dict = {
                # REMOVED 'audio_processor': self.audio_processor,  # Now handled internally by CallAnalyzer
                'transcription_service': self.transcription_service,
                'diarization_service': self.diarization_service,
                'llm_analyzer': self.llm_analyzer,
                'sentiment_service': self.sentiment_service,
                'performance_scorer': self.performance_scorer,
                'opportunity_detector': self.opportunity_detector,
                'google_sheets_exporter': self.google_sheets_exporter,
                'call_tagging_service': self.call_tagging_service,
                'coaching_analyzer': self.coaching_analyzer,
                'speaker_role_service': self.speaker_role_service,
                'employee_service': self.employee_service,
                'call_categorization_service': self.call_categorization_service  # NEW
            }
            
            self.call_analyzer = CallAnalyzer(services_dict)
            self.stats_manager = StatsManager(self.employee_service, self.file_queue_service)
            
            # Log employee list status
            employees = self.employee_service.get_employees()
            logger.info(f"Employee list initialized with {len(employees)} employees: {', '.join(employees)}")
            
            logger.info("All services initialized successfully")
            logger.info(f"Audio Preprocessing: Enabled")
            logger.info(f"LLM Sentiment Analysis: {'Enabled' if self.sentiment_service.is_initialized else 'Fallback Mode'}")
            logger.info(f"Call Classification: {'AI-Powered' if self.llm_analyzer.is_initialized else 'Rules Only'}")
            logger.info(f"Coaching Analysis: {'Active' if self.coaching_analyzer else 'Offline'}")
            logger.info(f"Speaker Identification: {'AI-Powered' if self.llm_analyzer.is_initialized else 'Rules Only'}")
            logger.info(f"Employee Management: Active with {len(employees)} employees")            
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
        
        # Display final statistics
        self.stats_manager.display_enhanced_final_stats()
    
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
                    # Analyze the audio file using CallAnalyzer
                    # CallAnalyzer now handles preprocessing internally
                    results = await self.call_analyzer.analyze_single_file_enhanced(audio_file)
                    
                    # Update statistics using StatsManager
                    self.stats_manager.increment_total_processed()
                    self.stats_manager.increment_successful()
                    self.stats_manager.update_enhanced_stats(results)
                    
                    # Check for high-value opportunities
                    if results.get('opportunity_analysis', {}).get('high_value_missed', False):
                        self.stats_manager.increment_high_opportunities()
                    
                    # Mark as processed
                    self.file_queue_service.mark_as_processed(audio_file.name)
                    
                except Exception as e:
                    logger.error(f"Failed to process {audio_file.name}: {str(e)}")
                    self.stats_manager.increment_total_processed()
                    self.stats_manager.increment_failed()
                    continue
        
        except Exception as e:
            logger.error(f"Error processing local files: {str(e)}")
    
    async def _process_api_files(self):
        """Process files from API endpoint (future implementation)"""
        logger.info("API mode processing not yet implemented")
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            await self.transcription_service.cleanup()
            await self.diarization_service.cleanup()
            await self.llm_analyzer.cleanup()
            await self.sentiment_service.cleanup()
            
            # Cleanup preprocessing
            if self.call_analyzer and hasattr(self.call_analyzer, 'audio_preprocessor'):
                self.call_analyzer.audio_preprocessor.cleanup_temp_files()
            
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")

async def main():
    """Main function for batch processing with employee list management"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL, settings.LOGS_DIR)
    global logger
    logger = logging.getLogger(__name__)
    
    print(f"\n🏥 Dental Call Analysis System")
    print(f"📊 Features: Audio Processing | AI Sentiment Analysis | Call Classification | Performance Scoring | Training Analysis | Employee Management")
    print(f"⚙️  Mode: {'API Integration' if settings.USE_API_MODE else 'Local Directory Processing'}")
    if not settings.USE_API_MODE:
        print(f"📁 Directory: {settings.AUDIO_INPUT_DIR}")
    print("="*80)
    
    # Initialize analyzer
    analyzer = DentalCallAnalyzer()
    
    try:
        # Initialize all services
        await analyzer.initialize()
        
        # Process all available files
        await analyzer.process_all_files()
        
        logger.info("Call analysis processing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Cleanup resources
        await analyzer.cleanup()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())