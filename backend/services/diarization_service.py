"""
Speaker diarization service using Pyannote
"""
import logging
import asyncio
import warnings
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

# Suppress warnings
warnings.filterwarnings("ignore")

try:
    from pyannote.audio import Pipeline
    import torch
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False

logger = logging.getLogger(__name__)

class DiarizationService:
    """Speaker diarization using Pyannote"""
    
    def __init__(self):
        self.pipeline = None
        self.device = self._get_device()
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def _get_device(self) -> str:
        """Get optimal device for processing"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    async def load_model(self) -> None:
        """Load Pyannote diarization pipeline"""
        if not PYANNOTE_AVAILABLE:
            logger.warning("Pyannote not available, using fallback speaker assignment")
            return
            
        if self.pipeline is not None:
            return
            
        try:
            logger.info("Loading Pyannote diarization model...")
            loop = asyncio.get_event_loop()
            self.pipeline = await loop.run_in_executor(
                self.executor,
                self._load_pipeline_sync
            )
            logger.info("Diarization model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load Pyannote pipeline: {str(e)}, using fallback")
            self.pipeline = None
    
    def _load_pipeline_sync(self):
        """Load pipeline synchronously"""
        try:
            pipeline = Pipeline.from_pretrained(
                settings.PYANNOTE_MODEL,
                use_auth_token=settings.HUGGINGFACE_TOKEN
            )
            
            if self.device != "cpu":
                pipeline = pipeline.to(torch.device(self.device))
            
            return pipeline
            
        except Exception as e:
            logger.warning(f"Pipeline loading failed: {str(e)}")
            return None
    
    async def diarize_speakers(self, audio_path: str) -> Dict:
        """
        Perform speaker diarization
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with speaker timeline
        """
        try:
            # Ensure pipeline is loaded
            if self.pipeline is None:
                await self.load_model()
            
            # If still no pipeline, use fallback
            if self.pipeline is None:
                return await self._fallback_speaker_assignment(audio_path)
            
            logger.info(f"Performing speaker diarization: {Path(audio_path).name}")
            
            # Run diarization in thread pool
            loop = asyncio.get_event_loop()
            diarization_result = await loop.run_in_executor(
                self.executor,
                self._diarize_sync,
                audio_path
            )
            
            if diarization_result is None:
                return await self._fallback_speaker_assignment(audio_path)
            
            # Process diarization result
            processed_result = self._process_diarization_result(diarization_result, audio_path)
            
            logger.info(f"Diarization completed - Found {processed_result['speaker_count']} speakers")
            
            return processed_result
            
        except Exception as e:
            logger.warning(f"Diarization failed: {str(e)}, using fallback")
            return await self._fallback_speaker_assignment(audio_path)
    
    def _diarize_sync(self, audio_path: str):
        """Synchronous diarization"""
        try:
            diarization = self.pipeline(audio_path)
            return diarization
        except Exception:
            return None
    
    def _process_diarization_result(self, diarization, audio_path: str) -> Dict:
        """Process diarization result into structured format"""
        
        speaker_timeline = []
        speakers_found = set()
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
            
            speaker_label = f"SPEAKER_{len(speakers_found):02d}" if speaker not in speakers_found else speaker
            speakers_found.add(speaker_label)
            
            segment = {
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
                "duration": round(end_time - start_time, 2),
                "speaker": speaker_label
            }
            
            speaker_timeline.append(segment)
        
        # Sort by start time
        speaker_timeline.sort(key=lambda x: x["start_time"])
        
        return {
            "speaker_timeline": speaker_timeline,
            "speaker_count": len(speakers_found),
            "speakers_found": list(speakers_found),
            "audio_file": Path(audio_path).name
        }
    
    async def _fallback_speaker_assignment(self, audio_path: str) -> Dict:
        """Fallback speaker assignment when diarization fails"""
        
        from utils.audio_processor import AudioProcessor
        audio_processor = AudioProcessor()
        
        try:
            duration = audio_processor.get_audio_duration(audio_path)
        except:
            duration = 60.0  # Default duration
        
        # Create alternating speaker segments
        speaker_timeline = []
        segment_duration = 8.0  # 8-second segments
        current_time = 0.0
        speaker_index = 0
        
        while current_time < duration:
            end_time = min(current_time + segment_duration, duration)
            speaker_label = f"SPEAKER_{speaker_index % 2:02d}"
            
            segment = {
                "start_time": round(current_time, 2),
                "end_time": round(end_time, 2), 
                "duration": round(end_time - current_time, 2),
                "speaker": speaker_label
            }
            
            speaker_timeline.append(segment)
            current_time = end_time
            speaker_index += 1
        
        logger.info("Using fallback speaker assignment")
        
        return {
            "speaker_timeline": speaker_timeline,
            "speaker_count": 2,
            "speakers_found": ["SPEAKER_00", "SPEAKER_01"],
            "audio_file": Path(audio_path).name,
            "fallback_used": True
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.pipeline:
            del self.pipeline
            self.pipeline = None