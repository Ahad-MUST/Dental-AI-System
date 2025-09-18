"""
Speaker diarization service using SpeechBrain (Updated from PyAnnote)
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
    """Speaker diarization using SpeechBrain"""
    
    def __init__(self):
        self.engine = None
        self.device = self._get_device()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.sample_rate = 16000
        
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
            logger.warning("SpeechBrain not available, using fallback speaker assignment")
            return
            
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
            logger.warning(f"Failed to load SpeechBrain engine: {str(e)}, using fallback")
            self.engine = None
    
    def _load_engine_sync(self):
        """Load SpeechBrain engine synchronously"""
        try:
            engine = SpeechBrainEngine(device=self.device)
            return engine
            
        except Exception as e:
            logger.error(f"SpeechBrain engine loading failed: {str(e)}")
            return None

    async def diarize_speakers(self, audio_path: str) -> Dict:
        """
        Perform speaker diarization using SpeechBrain with timeout protection
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with speaker timeline
        """
        try:
            # Ensure engine is loaded
            if self.engine is None:
                await self.load_model()
            
            # If still no engine, use fallback
            if self.engine is None:
                return await self._fallback_speaker_assignment(audio_path)
            
            logger.info(f"Performing SpeechBrain speaker diarization: {Path(audio_path).name}")
            
            # Run diarization in thread pool with timeout
            loop = asyncio.get_event_loop()
            try:
                # Set a reasonable timeout (5 minutes for most files)
                diarization_result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._diarize_sync,
                        audio_path
                    ),
                    timeout=300  # 5 minutes timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Diarization timed out after 5 minutes, using fallback")
                return await self._fallback_speaker_assignment(audio_path)
            
            if diarization_result is None:
                return await self._fallback_speaker_assignment(audio_path)
            
            logger.info(f"Diarization completed - Found {diarization_result['speaker_count']} speakers")
            
            return diarization_result
            
        except Exception as e:
            logger.warning(f"Diarization failed: {str(e)}, using fallback")
            return await self._fallback_speaker_assignment(audio_path)
    
    def _diarize_sync(self, audio_path: str) -> Dict:
        """Synchronous diarization using SpeechBrain with timeout protection"""
        try:
            logger.info("Running SpeechBrain speaker diarization...")
            
            # Run the SpeechBrain diarization
            logger.info(f"Processing audio file: {Path(audio_path).name}")
            
            # Use SpeechBrain engine for diarization
            # Auto-detect speakers with reasonable limits
            speechbrain_result = self.engine.diarize_audio(
                audio_path=audio_path,
                num_speakers=None,  # Auto-detect
                min_speakers=1,
                max_speakers=10
            )
            
            # Convert SpeechBrain result to our format
            speaker_timeline = []
            speakers_found = set()
            
            logger.info("Converting SpeechBrain results...")
            segment_count = 0
            
            for segment in speechbrain_result['segments']:
                speaker_segment = {
                    "start_time": round(segment['start'], 2),
                    "end_time": round(segment['end'], 2), 
                    "duration": round(segment['duration'], 2),
                    "speaker": segment['speaker']
                }
                speaker_timeline.append(speaker_segment)
                speakers_found.add(segment['speaker'])
                segment_count += 1
            
            logger.info(f"Found {segment_count} speaker segments")
            
            # Sort by start time
            speaker_timeline.sort(key=lambda x: x["start_time"])
            
            # Fill gaps between segments
            filled_timeline = self._fill_timeline_gaps(speaker_timeline)
            
            logger.info(f"SpeechBrain diarization completed successfully with {len(speakers_found)} speakers")
            
            return {
                "speaker_timeline": filled_timeline,
                "speaker_count": len(speakers_found),
                "speakers_found": list(speakers_found),
                "audio_file": Path(audio_path).name,
                "method": "speechbrain",
                "engine_metadata": speechbrain_result.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"SpeechBrain diarization error: {str(e)}")
            return None
    
    def _fill_timeline_gaps(self, timeline: List[Dict]) -> List[Dict]:
        """Fill gaps in the timeline with speaker assignments"""
        if not timeline:
            return timeline
        
        filled_timeline = []
        gap_threshold = 0.5  # seconds
        
        for i, segment in enumerate(timeline):
            if i == 0:
                filled_timeline.append(segment)
                continue
            
            prev_segment = filled_timeline[-1]
            gap_duration = segment["start_time"] - prev_segment["end_time"]
            
            # If there's a significant gap, fill it
            if gap_duration > gap_threshold:
                # Assign gap to the speaker who speaks next (or previous if very short)
                gap_speaker = segment["speaker"] if gap_duration > 2.0 else prev_segment["speaker"]
                
                gap_segment = {
                    "start_time": round(prev_segment["end_time"], 2),
                    "end_time": round(segment["start_time"], 2),
                    "duration": round(gap_duration, 2),
                    "speaker": gap_speaker
                }
                filled_timeline.append(gap_segment)
            
            filled_timeline.append(segment)
        
        return filled_timeline
    
    def _create_alternating_segments(self, duration: float) -> List[Dict]:
        """Create alternating speaker segments as fallback"""
        # Define common call patterns for dental offices
        patterns = [
            {"speaker": "SPEAKER_00", "duration_range": (8, 15)},   # Staff opening
            {"speaker": "SPEAKER_01", "duration_range": (3, 8)},    # Patient response
            {"speaker": "SPEAKER_00", "duration_range": (10, 20)},  # Staff explanation
            {"speaker": "SPEAKER_01", "duration_range": (2, 6)},    # Patient question
            {"speaker": "SPEAKER_00", "duration_range": (5, 12)},   # Staff answer
        ]
        
        speaker_timeline = []
        current_time = 0.0
        pattern_index = 0
        
        while current_time < duration:
            pattern = patterns[pattern_index % len(patterns)]
            
            # Random duration within range
            import random
            min_dur, max_dur = pattern["duration_range"]
            segment_duration = min(
                random.uniform(min_dur, max_dur),
                duration - current_time
            )
            
            if segment_duration > 0.5:  # Only add segments longer than 0.5 seconds
                segment = {
                    "start_time": round(current_time, 2),
                    "end_time": round(current_time + segment_duration, 2),
                    "duration": round(segment_duration, 2),
                    "speaker": pattern["speaker"]
                }
                speaker_timeline.append(segment)
            
            current_time += segment_duration
            pattern_index += 1
        
        return speaker_timeline
    
    async def _fallback_speaker_assignment(self, audio_path: str) -> Dict:
        """Enhanced fallback speaker assignment when diarization fails"""
        
        from utils.audio_processor import AudioProcessor
        audio_processor = AudioProcessor()
        
        try:
            duration = audio_processor.get_audio_duration(audio_path)
        except:
            duration = 60.0  # Default duration
        
        # Create more realistic alternating speaker segments
        speaker_timeline = self._create_alternating_segments(duration)
        
        logger.info("Using enhanced fallback speaker assignment with realistic patterns")
        
        return {
            "speaker_timeline": speaker_timeline,
            "speaker_count": 2,
            "speakers_found": ["SPEAKER_00", "SPEAKER_01"],
            "audio_file": Path(audio_path).name,
            "fallback_used": True,
            "method": "enhanced_fallback"
        }
    
    def _smart_speaker_assignment(self, audio_path: str, duration: float) -> List[Dict]:
        """Smart speaker assignment based on audio analysis"""
        try:
            # Load audio for basic analysis
            import librosa
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Detect voice activity using energy thresholds
            frame_length = int(0.5 * sr)  # 0.5 second frames
            hop_length = int(0.25 * sr)   # 0.25 second hop
            
            # Calculate energy for each frame
            energy = []
            for i in range(0, len(y) - frame_length, hop_length):
                frame = y[i:i + frame_length]
                frame_energy = np.sum(frame ** 2)
                energy.append(frame_energy)
            
            # Threshold for voice activity
            energy_threshold = np.percentile(energy, 30)  # Bottom 30% is likely silence
            
            # Create segments based on energy
            segments = []
            current_time = 0.0
            speaker_index = 0
            min_segment_duration = 2.0  # Minimum 2 seconds per segment
            
            in_speech = False
            segment_start = 0.0
            
            for i, e in enumerate(energy):
                time_stamp = i * 0.25  # 0.25 second hop
                
                if e > energy_threshold and not in_speech:
                    # Start of speech
                    segment_start = time_stamp
                    in_speech = True
                elif e <= energy_threshold and in_speech:
                    # End of speech
                    segment_duration = time_stamp - segment_start
                    
                    if segment_duration >= min_segment_duration:
                        segments.append({
                            "start_time": round(segment_start, 2),
                            "end_time": round(time_stamp, 2),
                            "duration": round(segment_duration, 2),
                            "speaker": f"SPEAKER_{speaker_index % 2:02d}"
                        })
                        speaker_index += 1
                    
                    in_speech = False
            
            # Handle final segment
            if in_speech and duration - segment_start >= min_segment_duration:
                segments.append({
                    "start_time": round(segment_start, 2),
                    "end_time": round(duration, 2),
                    "duration": round(duration - segment_start, 2),
                    "speaker": f"SPEAKER_{speaker_index % 2:02d}"
                })
            
            # If no good segments found, fall back to alternating
            if not segments:
                return self._create_alternating_segments(duration)
            
            return segments
            
        except Exception as e:
            logger.warning(f"Smart assignment failed: {str(e)}, using alternating pattern")
            return self._create_alternating_segments(duration)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.engine:
            self.engine._cleanup_temp_files()
            del self.engine
            self.engine = None