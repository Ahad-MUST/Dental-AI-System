"""
Centralized Audio Preprocessing for Whisper + SpeechBrain
Handles all audio preprocessing in one place before analysis
"""
import librosa
import soundfile as sf
import numpy as np
import tempfile
import os
import logging
from pathlib import Path
from typing import Tuple, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """Centralized audio preprocessing for consistent analysis pipeline"""
    
    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate
        self.temp_files = []
        
        # Preprocessing parameters
        self.min_duration = 1.0  # seconds
        self.normalization_level = 0.95
        self.trim_db = 20  # dB for silence trimming
        self.crop_start_seconds = getattr(settings, 'AUDIO_CROP_START_SECONDS', 3)  # Crop first n seconds
    
    def preprocess_for_analysis(self, audio_path: str) -> str:
        """
        Centralized preprocessing for both Whisper and SpeechBrain
        
        Args:
            audio_path: Path to original audio file
            
        Returns:
            str: Path to preprocessed audio file
        """
        try:
            logger.info(f"Preprocessing audio: {Path(audio_path).name}")
            
            # Step 1: Load and resample to 16kHz
            audio_data, sr = librosa.load(audio_path, sr=self.target_sample_rate, mono=True)
            logger.debug(f"Loaded audio: {len(audio_data)/sr:.2f}s at {sr}Hz")
            
            # Step 2: Crop first n seconds (remove recorded message)
            if self.crop_start_seconds > 0:
                crop_samples = int(self.crop_start_seconds * sr)
                if len(audio_data) > crop_samples:
                    audio_data = audio_data[crop_samples:]
                    logger.debug(f"Cropped first {self.crop_start_seconds}s: {len(audio_data)/sr:.2f}s remaining")
                else:
                    logger.warning(f"Audio too short to crop {self.crop_start_seconds}s, using full audio")
            
            # Step 3: Convert to mono (already done by librosa.load with mono=True)
            # No additional step needed
            
            # Step 4: Remove silence from beginning and end
            audio_data, _ = librosa.effects.trim(audio_data, top_db=self.trim_db)
            logger.debug(f"After trimming: {len(audio_data)/sr:.2f}s")
            
            # Step 5: Ensure minimum duration
            min_samples = int(self.min_duration * sr)
            if len(audio_data) < min_samples:
                # Pad with zeros to reach minimum duration
                padding_needed = min_samples - len(audio_data)
                audio_data = np.pad(audio_data, (0, padding_needed), mode='constant', constant_values=0)
                logger.debug(f"Padded to minimum duration: {len(audio_data)/sr:.2f}s")
            
            # Step 6: Normalize amplitude
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data)) * self.normalization_level
                logger.debug("Audio normalized")
            
            # Step 7: Apply additional preprocessing
            audio_data = self._apply_additional_preprocessing(audio_data, sr)
            
            # Step 8: Create temporary preprocessed file
            preprocessed_path = self._save_preprocessed_audio(audio_data, sr, audio_path)
            
            logger.info(f"Preprocessing completed: {Path(preprocessed_path).name} (cropped {self.crop_start_seconds}s)")
            return preprocessed_path
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {str(e)}")
            raise RuntimeError(f"Failed to preprocess audio: {str(e)}")
    
    def _apply_additional_preprocessing(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply additional preprocessing steps
        Can be extended with noise reduction, filtering, etc.
        """
        try:
            # Optional: Apply pre-emphasis filter (common in speech processing)
            # Helps with high-frequency components
            pre_emphasis = 0.97
            audio_data = np.append(audio_data[0], audio_data[1:] - pre_emphasis * audio_data[:-1])
            
            # Optional: Apply gentle high-pass filter to remove low-frequency noise
            # This removes rumble and some background noise
            audio_data = librosa.effects.preemphasis(audio_data, coef=0.97)
            
            logger.debug("Applied additional preprocessing filters")
            return audio_data
            
        except Exception as e:
            logger.warning(f"Additional preprocessing failed: {str(e)}, using basic preprocessing")
            return audio_data
    
    def _save_preprocessed_audio(self, audio_data: np.ndarray, sr: int, original_path: str) -> str:
        """Save preprocessed audio to temporary file"""
        try:
            # Create temporary file with descriptive name
            original_name = Path(original_path).stem
            temp_fd, temp_path = tempfile.mkstemp(
                suffix='.wav', 
                prefix=f'preprocessed_{original_name}_',
                dir=tempfile.gettempdir()
            )
            os.close(temp_fd)
            
            # Save as 16-bit WAV for compatibility
            sf.write(temp_path, audio_data, sr, subtype='PCM_16')
            
            # Verify the saved file duration
            actual_duration = len(audio_data) / sr
            logger.debug(f"Saved preprocessed audio: {temp_path}, duration: {actual_duration:.2f}s")
            
            # Track temp file for cleanup
            self.temp_files.append(temp_path)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to save preprocessed audio: {str(e)}")
            raise
    
    def validate_audio_file(self, audio_path: str) -> bool:
        """Enhanced audio file validation"""
        try:
            audio_path = Path(audio_path)
            
            # Check if file exists
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return False
            
            # Check file size (must be > 1KB)
            if audio_path.stat().st_size < 1024:
                logger.error(f"Audio file too small: {audio_path}")
                return False
            
            # Check file extension
            valid_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.mp4', '.aac'}
            if audio_path.suffix.lower() not in valid_extensions:
                logger.error(f"Unsupported audio format: {audio_path.suffix}")
                return False
            
            # Try to load file metadata
            try:
                duration = librosa.get_duration(path=str(audio_path))
                if duration < 0.5:  # Less than 0.5 seconds
                    logger.error(f"Audio file too short: {duration:.2f}s")
                    return False
                    
                logger.debug(f"Audio validation passed: {duration:.2f}s")
                return True
                
            except Exception as e:
                logger.error(f"Cannot read audio file {audio_path}: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Audio validation error: {str(e)}")
            return False
    
    def get_audio_info(self, audio_path: str) -> dict:
        """Get detailed audio file information"""
        try:
            # Get basic info without loading full file
            duration = librosa.get_duration(path=audio_path)
            
            # Load small sample to get more details
            y_sample, sr_original = librosa.load(audio_path, sr=None, duration=1.0)
            
            return {
                'duration': duration,
                'original_sample_rate': sr_original,
                'target_sample_rate': self.target_sample_rate,
                'file_size': Path(audio_path).stat().st_size,
                'channels': 'mono' if len(y_sample.shape) == 1 else 'stereo',
                'valid': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {str(e)}")
            return {
                'duration': 0,
                'valid': False,
                'error': str(e)
            }
    
    def cleanup_temp_files(self):
        """Clean up all temporary preprocessed files"""
        cleaned = 0
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    cleaned += 1
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        
        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} temporary audio files")
        
        self.temp_files.clear()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup_temp_files()