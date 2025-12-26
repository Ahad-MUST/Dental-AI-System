"""
Audio transcription service using OpenAI Whisper - Updated for centralized preprocessing
"""
import whisper
import torch
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Clean transcription service using Whisper with centralized preprocessing"""
    
    def __init__(self):
        self.model = None
        self.device = self._get_device()
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
            logger.info(f"Loading OpenAI Whisper {settings.WHISPER_MODEL} model on {self.device}...")
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                lambda: whisper.load_model(settings.WHISPER_MODEL, device=self.device)
            )
            logger.info(f"✓ OpenAI Whisper {settings.WHISPER_MODEL} model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    async def transcribe_audio(self, preprocessed_audio_path: str) -> Dict:
        """
        Transcribe preprocessed audio file to text
        
        Args:
            preprocessed_audio_path: Path to PREPROCESSED audio file (from AudioPreprocessor)
            
        Returns:
            Dict with transcription results
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                await self.load_model()
            
            logger.info(f"Transcribing with Whisper {settings.WHISPER_MODEL}: {Path(preprocessed_audio_path).name}")
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                preprocessed_audio_path
            )
            
            # Process result
            processed_result = self._process_transcription_result(result, preprocessed_audio_path)
            
            logger.info(f"Transcription completed - Duration: {processed_result['duration']:.1f}s, "
                       f"Confidence: {processed_result['confidence']:.2f}")
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _transcribe_sync(self, audio_path: str) -> Dict:
        """Synchronous transcription using preprocessed audio"""
        try:
            # Since audio is already preprocessed (16kHz, mono, normalized), 
            # Whisper can work more efficiently
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False,
                temperature=0.0,
                # Since audio is already preprocessed, we can be more confident
                # in the quality and use more aggressive settings
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6
            )
            return result
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            raise
    
    def _process_transcription_result(self, raw_result: Dict, audio_path: str) -> Dict:
        """Process raw Whisper output into clean format"""
        
        segments = []
        total_confidence = 0
        word_count = 0
        
        for segment in raw_result.get("segments", []):
            # Calculate segment confidence from words
            words = segment.get("words", [])
            segment_confidence = 0.8  # Default confidence
            
            if words:
                word_confidences = [w.get("probability", 0.8) for w in words if w.get("probability")]
                if word_confidences:
                    segment_confidence = sum(word_confidences) / len(word_confidences)
            
            # Clean text
            text = segment["text"].strip()
            if not text:  # Skip empty segments
                continue
                
            processed_segment = {
                "start_time": round(segment["start"], 2),
                "end_time": round(segment["end"], 2),
                "text": text,
                "confidence": round(segment_confidence, 3),
                "words": words
            }
            
            segments.append(processed_segment)
            total_confidence += segment_confidence
            word_count += len(text.split())
        
        # Calculate overall metrics - Fix duration calculation
        avg_confidence = total_confidence / len(segments) if segments else 0.0
        full_transcript = " ".join([seg["text"] for seg in segments])
        
        # Fix duration: use actual duration from segments if raw_result duration is 0
        duration = raw_result.get("duration", 0)
        if duration == 0 and segments:
            # Calculate duration from last segment
            duration = max([seg["end_time"] for seg in segments])
        
        # Enhanced result with preprocessing info
        result = {
            "full_transcript": full_transcript,
            "segments": segments,
            "duration": duration,  # Use corrected duration
            "confidence": round(avg_confidence, 3),
            "word_count": word_count,
            "segment_count": len(segments),
            "language": raw_result.get("language", "en"),
            "audio_file": Path(audio_path).name,
            "preprocessing_applied": True,  # Flag to indicate centralized preprocessing was used
            "whisper_model": settings.WHISPER_MODEL,
            "device_used": self.device
        }
        
        return result
    
    def get_transcription_quality_score(self, result: Dict) -> float:
        """Calculate quality score based on transcription metrics"""
        try:
            confidence = result.get('confidence', 0)
            segment_count = result.get('segment_count', 0)
            word_count = result.get('word_count', 0)
            duration = result.get('duration', 1)
            
            # Base score from confidence
            quality_score = confidence
            
            # Adjust for reasonable speaking rate (words per minute)
            words_per_minute = (word_count / duration) * 60 if duration > 0 else 0
            if 100 <= words_per_minute <= 200:  # Normal speaking rate
                quality_score += 0.1
            elif words_per_minute < 50 or words_per_minute > 300:  # Unusual rate
                quality_score -= 0.1
            
            # Adjust for segment density (reasonable pauses)
            if duration > 0:
                segments_per_minute = (segment_count / duration) * 60
                if 10 <= segments_per_minute <= 30:  # Reasonable segmentation
                    quality_score += 0.05
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception:
            return 0.5  # Default middle score on error
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.model:
            del self.model
            self.model = None
        logger.info("Transcription service cleaned up")