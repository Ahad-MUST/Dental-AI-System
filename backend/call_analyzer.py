"""
Core Call Analysis Logic - Updated for centralized preprocessing
Handles the main analysis pipeline for individual audio files
"""
import logging
import time
from pathlib import Path
from typing import Dict
from utils.audio_preprocessor import AudioPreprocessor

logger = logging.getLogger(__name__)

class CallAnalyzer:
    """Handles individual call analysis with centralized preprocessing"""
    
    def __init__(self, services_dict):
        """Initialize with all required services"""
        # Core services
        self.transcription_service = services_dict['transcription_service']
        self.diarization_service = services_dict['diarization_service']
        self.llm_analyzer = services_dict['llm_analyzer']
        self.sentiment_service = services_dict['sentiment_service']
        self.performance_scorer = services_dict['performance_scorer']
        self.opportunity_detector = services_dict['opportunity_detector']
        self.google_sheets_exporter = services_dict['google_sheets_exporter']
        
        # Enhanced services
        self.call_tagging_service = services_dict['call_tagging_service']
        self.coaching_analyzer = services_dict['coaching_analyzer']
        self.speaker_role_service = services_dict['speaker_role_service']
        self.employee_service = services_dict['employee_service']
        
        # NEW: Centralized audio preprocessor
        self.audio_preprocessor = AudioPreprocessor()
    
    async def analyze_single_file_enhanced(self, audio_file: Path) -> Dict:
        """
        Analyze a single audio file with centralized preprocessing and enhanced features
        """
        start_time = time.time()
        preprocessed_audio_path = None
        
        try:
            logger.info(f"Starting enhanced analysis of {audio_file.name}...")
            
            # Step 1: Validate original audio file
            logger.info("Validating audio file...")
            if not self.audio_preprocessor.validate_audio_file(str(audio_file)):
                raise Exception("Audio file validation failed")
            
            # Step 2: CENTRALIZED PREPROCESSING - This happens once for both services
            logger.info("Applying centralized audio preprocessing...")
            preprocessed_audio_path = self.audio_preprocessor.preprocess_for_analysis(str(audio_file))
            logger.info(f"Preprocessing completed: {Path(preprocessed_audio_path).name}")
            
            # Step 3: Transcribe preprocessed audio
            logger.info("Transcribing preprocessed audio...")
            transcription_result = await self.transcription_service.transcribe_audio(preprocessed_audio_path)
            
            if not transcription_result or not transcription_result.get("full_transcript"):
                raise Exception("Transcription failed or returned empty result")
            
            # Step 4: Perform speaker diarization on preprocessed audio
            logger.info("Performing speaker diarization on preprocessed audio...")
            diarization_result = await self.diarization_service.diarize_speakers(preprocessed_audio_path)
            
            # Step 5: Combine transcription with speaker labels
            logger.info("Combining transcription with speakers...")
            combined_transcript = self._combine_transcription_diarization(
                transcription_result, diarization_result
            )
            
            # Step 6: LLM-based speaker role assignment
            logger.info("Performing LLM-based speaker role assignment...")
            patient_text, staff_text = await self.speaker_role_service.assign_speaker_roles(combined_transcript)
            
            # Log the results of speaker assignment
            logger.info(f"Speaker role assignment completed - Patient: {len(patient_text)} chars, Staff: {len(staff_text)} chars")
            
            # Step 7: Generate call summary using LLM
            logger.info("Generating call summary...")
            call_summary = await self.llm_analyzer.analyze_call_summary(
                transcription_result["full_transcript"]
            )
            
            # Step 8: Extract representative name using LLM WITH EMPLOYEE LIST
            logger.info("Extracting representative name from employee list...")
            representative_name = await self.llm_analyzer.extract_representative_name(
                transcription_result["full_transcript"]
            )
            
            # Step 9: LLM-based sentiment analysis
            logger.info("Analyzing sentiment and emotions using LLM...")
            sentiment_analysis = await self.sentiment_service.analyze_call_segments_sentiment(
                patient_text, staff_text
            )
            
            # Step 10: Score call performance
            logger.info("Scoring performance...")
            performance_analysis = await self.performance_scorer.score_call_performance(
                combined_transcript, patient_text, staff_text
            )
            
            # Step 11: Detect missed opportunities
            logger.info("Detecting opportunities...")
            opportunity_analysis = await self.opportunity_detector.detect_opportunities(
                patient_text, staff_text, call_summary, {}
            )
            
            # Step 12: Call tagging analysis
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
            
            # Step 13: Coaching analysis
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
            
            # Step 14: Compile comprehensive analysis result with preprocessing info
            final_results = {
                "audio_file": str(audio_file),
                "preprocessed_audio_file": preprocessed_audio_path,
                "transcription": transcription_result,
                "call_summary": call_summary,
                "representative_name": representative_name,
                "sentiment_analysis": sentiment_analysis,
                "emotion_analysis": sentiment_analysis.get("emotion_analysis", {}),
                "performance_analysis": performance_analysis,
                "opportunity_analysis": opportunity_analysis,
                "combined_transcript": combined_transcript,
                "call_tag_analysis": call_tag_analysis,
                "coaching_analysis": coaching_analysis,
                "diarization_result": diarization_result,
                
                # Analysis metadata
                "analysis_method": "enhanced_llm_based_with_centralized_preprocessing",
                "preprocessing_applied": True,
                "llm_used": self.llm_analyzer.is_initialized,
                "sentiment_enabled": self.sentiment_service.is_initialized,
                "tagging_enabled": self.call_tagging_service is not None,
                "coaching_enabled": self.coaching_analyzer is not None,
                "speaker_role_assignment": "llm_based",
                "employee_list_used": self.employee_service.get_employees(),
                "employee_count": len(self.employee_service.get_employees()),
                "processing_time": processing_time,
                "diarization_speaker_count": diarization_result.get("speaker_count", 0),
                
                # Quality scores
                "transcription_quality": self.transcription_service.get_transcription_quality_score(transcription_result) if hasattr(self.transcription_service, 'get_transcription_quality_score') else None,
                "diarization_quality": self.diarization_service.get_diarization_quality_score(diarization_result) if hasattr(self.diarization_service, 'get_diarization_quality_score') else None
            }
            
            # Step 15: Export enhanced results to Google Sheets
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
            logger.info(f"Preprocessing: Applied centrally before analysis")
            
            if emotion_flags:
                logger.info(f"Emotion flags detected: {', '.join(emotion_flags)}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {str(e)}")
            raise
        finally:
            # Clean up preprocessed file
            if preprocessed_audio_path:
                try:
                    self.audio_preprocessor.cleanup_temp_files()
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup preprocessed files: {cleanup_error}")
    
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