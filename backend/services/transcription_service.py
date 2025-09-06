"""
Audio transcription service using OpenAI Whisper
"""
import whisper
import torch
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings
from utils.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Clean transcription service using Whisper"""
    
    def __init__(self):
        self.model = None
        self.device = self._get_device()
        self.audio_processor = AudioProcessor()
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def _get_device(self) -> str:
        """Determine optimal device for Whisper"""
        if settings.WHISPER_DEVICE == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps" 
            else:
                return "cpu"
        return settings.WHISPER_DEVICE
    
    async def load_model(self) -> None:
        """Load Whisper model"""
        if self.model is not None:
            return
            
        try:
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                lambda: whisper.load_model(settings.WHISPER_MODEL, device=self.device)
            )
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    async def transcribe_audio(self, audio_path: str) -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with transcription results
        """
        try:
            # Validate audio file
            if not self.audio_processor.validate_audio_file(audio_path):
                raise ValueError(f"Invalid audio file: {audio_path}")
            
            # Ensure model is loaded
            if self.model is None:
                await self.load_model()
            
            logger.info(f"Transcribing: {Path(audio_path).name}")
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                audio_path
            )
            
            # Process result
            processed_result = self._process_transcription_result(result, audio_path)
            
            logger.info(f"Transcription completed - Duration: {processed_result['duration']:.1f}s, "
                       f"Confidence: {processed_result['confidence']:.2f}")
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _transcribe_sync(self, audio_path: str) -> Dict:
        """Synchronous transcription"""
        result = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            verbose=False,
            temperature=0.0
        )
        return result
    
    def _process_transcription_result(self, raw_result: Dict, audio_path: str) -> Dict:
        """Process raw Whisper output into clean format"""
        
        segments = []
        total_confidence = 0
        word_count = 0
        
        for segment in raw_result.get("segments", []):
            # Calculate segment confidence from words
            words = segment.get("words", [])
            segment_confidence = 0.8  # Default
            
            if words:
                word_confidences = [w.get("probability", 0.8) for w in words]
                segment_confidence = sum(word_confidences) / len(word_confidences)
            
            processed_segment = {
                "start_time": round(segment["start"], 2),
                "end_time": round(segment["end"], 2),
                "text": segment["text"].strip(),
                "confidence": round(segment_confidence, 3),
                "words": words
            }
            
            segments.append(processed_segment)
            total_confidence += segment_confidence
            word_count += len(segment["text"].split())
        
        # Calculate overall metrics
        avg_confidence = total_confidence / len(segments) if segments else 0.0
        full_transcript = " ".join([seg["text"] for seg in segments])
        
        return {
            "full_transcript": full_transcript,
            "segments": segments,
            "duration": raw_result.get("duration", 0),
            "confidence": round(avg_confidence, 3),
            "word_count": word_count,
            "segment_count": len(segments),
            "language": raw_result.get("language", "en"),
            "audio_file": Path(audio_path).name
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.model:
            del self.model
            self.model = None