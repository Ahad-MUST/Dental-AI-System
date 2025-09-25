"""
Speaker diarization service using SpeechBrain - Updated for centralized preprocessing
Removed excessive fallbacks to ensure pure SpeechBrain usage
"""
import logging
import asyncio
import warnings
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

# Suppress warnings
warnings.filterwarnings("ignore")

try:
    from speechbrain_engine import SpeechBrainEngine
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class DiarizationService:
    """Speaker diarization using SpeechBrain with centralized preprocessing"""
    
    def __init__(self):
        self.engine = None
        self.device = self._get_device()
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def _get_device(self) -> str:
        """Get optimal device for processing"""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        except ImportError:
            return "cpu"
    
    async def load_model(self) -> None:
        """Load SpeechBrain engine"""
        if not SPEECHBRAIN_AVAILABLE:
            logger.error("SpeechBrain not available - install with: pip install speechbrain")
            raise ImportError("SpeechBrain package not installed")
            
        if self.engine is not None:
            return
            
        try:
            logger.info("Loading SpeechBrain speaker diarization engine...")
            loop = asyncio.get_event_loop()
            self.engine = await loop.run_in_executor(
                self.executor,
                self._load_engine_sync
            )
            logger.info("SpeechBrain engine loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SpeechBrain engine: {str(e)}")
            raise RuntimeError(f"SpeechBrain initialization failed: {str(e)}")
    
    def _load_engine_sync(self):
        """Load SpeechBrain engine synchronously"""
        try:
            return SpeechBrainEngine(device=self.device)
        except Exception as e:
            logger.error(f"SpeechBrain engine loading failed: {str(e)}")
            raise

    async def diarize_speakers(self, preprocessed_audio_path: str) -> Dict:
        """
        Perform speaker diarization using SpeechBrain on preprocessed audio
        
        Args:
            preprocessed_audio_path: Path to PREPROCESSED audio file (from AudioPreprocessor)
            
        Returns:
            Dict with speaker timeline
        """
        try:
            # Ensure engine is loaded
            if self.engine is None:
                await self.load_model()
            
            logger.info(f"Performing SpeechBrain speaker diarization on preprocessed audio: {Path(preprocessed_audio_path).name}")
            
            # Get audio duration for timeout calculation
            duration = self._get_audio_duration(preprocessed_audio_path)
            
            # Calculate dynamic timeout based on audio length
            # Longer calls need more time, but cap at 10 minutes
            timeout_seconds = min(600, max(120, duration * 10))  # 2-10 minutes based on audio length
            
            logger.debug(f"Audio duration: {duration:.1f}s, timeout: {timeout_seconds}s")
            
            # Run diarization with retry logic
            diarization_result = await self._diarize_with_retry(preprocessed_audio_path, timeout_seconds)
            
            if diarization_result is None:
                raise RuntimeError("SpeechBrain diarization failed after all retry attempts")
            
            logger.info(f"Diarization completed - Found {diarization_result['speaker_count']} speakers")
            
            return diarization_result
            
        except Exception as e:
            logger.error(f"Diarization failed: {str(e)}")
            raise RuntimeError(f"SpeechBrain diarization failed: {str(e)}")
    
    async def _diarize_with_retry(self, audio_path: str, timeout_seconds: int) -> Dict:
        """Diarization with retry logic for different parameters"""
        
        retry_configs = [
            {"num_speakers": None, "max_speakers": 6},      # Auto-detect, up to 6 speakers
            {"num_speakers": None, "max_speakers": 4},      # Auto-detect, up to 4 speakers  
            {"num_speakers": 2, "max_speakers": 2},         # Force 2 speakers
            {"num_speakers": 3, "max_speakers": 3},         # Force 3 speakers
        ]
        
        loop = asyncio.get_event_loop()
        
        for i, config in enumerate(retry_configs, 1):
            try:
                logger.debug(f"Diarization attempt {i}/{len(retry_configs)} with config: {config}")
                
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._diarize_sync,
                        audio_path,
                        config
                    ),
                    timeout=timeout_seconds
                )
                
                if result is not None:
                    logger.info(f"Diarization successful on attempt {i}")
                    return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Attempt {i} timed out after {timeout_seconds}s")
                if i < len(retry_configs):
                    continue
                else:
                    raise RuntimeError(f"All diarization attempts timed out after {timeout_seconds}s")
                    
            except Exception as e:
                logger.warning(f"Attempt {i} failed: {str(e)}")
                if i < len(retry_configs):
                    continue
                else:
                    raise RuntimeError(f"All diarization attempts failed. Last error: {str(e)}")
        
        return None
    
    def _diarize_sync(self, audio_path: str, config: Dict) -> Dict:
        """Synchronous diarization using SpeechBrain"""
        try:
            logger.debug(f"Running SpeechBrain with config: {config}")
            
            # Use SpeechBrain engine for diarization
            # Audio is already preprocessed (16kHz, mono, normalized)
            speechbrain_result = self.engine.diarize_audio(
                audio_path=audio_path,
                num_speakers=config.get("num_speakers"),
                min_speakers=1,
                max_speakers=config.get("max_speakers", 6)
            )
            
            # Validate result
            if not speechbrain_result.get('segments'):
                logger.warning("SpeechBrain returned no segments")
                return None
            
            # Convert SpeechBrain result to our format
            speaker_timeline = []
            speakers_found = set()
            
            for segment in speechbrain_result['segments']:
                # Validate segment
                if segment.get('duration', 0) < 0.1:  # Skip very short segments
                    continue
                    
                speaker_segment = {
                    "start_time": round(segment['start'], 2),
                    "end_time": round(segment['end'], 2), 
                    "duration": round(segment['duration'], 2),
                    "speaker": segment['speaker']
                }
                speaker_timeline.append(speaker_segment)
                speakers_found.add(segment['speaker'])
            
            # Validate we have reasonable results
            if len(speaker_timeline) == 0:
                logger.warning("No valid segments after filtering")
                return None
                
            if len(speakers_found) == 0:
                logger.warning("No speakers found")
                return None
            
            # Sort by start time
            speaker_timeline.sort(key=lambda x: x["start_time"])
            
            # Fill small gaps between segments
            filled_timeline = self._fill_small_gaps(speaker_timeline)
            
            logger.debug(f"SpeechBrain completed: {len(speakers_found)} speakers, {len(filled_timeline)} segments")
            
            return {
                "speaker_timeline": filled_timeline,
                "speaker_count": len(speakers_found),
                "speakers_found": list(speakers_found),
                "audio_file": Path(audio_path).name,
                "method": "speechbrain",
                "preprocessing_applied": True,  # Flag to indicate centralized preprocessing was used
                "config_used": config,
                "engine_metadata": speechbrain_result.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"SpeechBrain sync diarization error: {str(e)}")
            return None
    
    def _fill_small_gaps(self, timeline: List[Dict]) -> List[Dict]:
        """Fill small gaps in the timeline (< 0.5s) with speaker assignments"""
        if not timeline or len(timeline) < 2:
            return timeline
        
        filled_timeline = [timeline[0]]  # Start with first segment
        gap_threshold = 0.5  # seconds
        
        for i in range(1, len(timeline)):
            current_segment = timeline[i]
            prev_segment = filled_timeline[-1]
            
            gap_duration = current_segment["start_time"] - prev_segment["end_time"]
            
            # If there's a small gap, fill it with the previous speaker
            if 0 < gap_duration <= gap_threshold:
                gap_segment = {
                    "start_time": prev_segment["end_time"],
                    "end_time": current_segment["start_time"],
                    "duration": round(gap_duration, 2),
                    "speaker": prev_segment["speaker"]  # Assign to previous speaker
                }
                filled_timeline.append(gap_segment)
            
            filled_timeline.append(current_segment)
        
        return filled_timeline
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration from the preprocessed (cropped) file"""
        try:
            import librosa
            # Get duration directly from the preprocessed file
            duration = librosa.get_duration(path=audio_path)
            logger.debug(f"Preprocessed audio duration: {duration:.2f}s")
            return duration
        except Exception as e:
            logger.warning(f"Failed to get audio duration: {e}")
            return 60.0  # Default fallback
    
    def get_diarization_quality_score(self, result: Dict) -> float:
        """Calculate quality score for diarization results"""
        try:
            speaker_count = result.get('speaker_count', 0)
            timeline = result.get('speaker_timeline', [])
            
            if not timeline or speaker_count == 0:
                return 0.0
            
            # Base score
            quality_score = 0.5
            
            # Reasonable speaker count (2-4 is most common for dental calls)
            if 2 <= speaker_count <= 4:
                quality_score += 0.3
            elif speaker_count == 1:
                quality_score += 0.1
            else:
                quality_score -= 0.1
            
            # Check segment distribution
            total_duration = sum(seg['duration'] for seg in timeline)
            if total_duration > 0:
                speaker_durations = {}
                for seg in timeline:
                    speaker = seg['speaker']
                    speaker_durations[speaker] = speaker_durations.get(speaker, 0) + seg['duration']
                
                # Check if speakers have reasonable balance (not one speaker dominating 95%)
                max_speaker_ratio = max(speaker_durations.values()) / total_duration
                if max_speaker_ratio < 0.95:
                    quality_score += 0.2
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception:
            return 0.5  # Default middle score
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.engine:
            self.engine._cleanup_temp_files()
            del self.engine
            self.engine = None
        logger.info("Diarization service cleaned up")