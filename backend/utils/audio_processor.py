"""
Audio preprocessing utilities
"""
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio preprocessing for optimal transcription"""
    
    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate
    
    def load_and_preprocess(self, audio_path: str) -> tuple[np.ndarray, int]:
        """
        Load and preprocess audio file
        
        Returns:
            tuple: (audio_data, sample_rate)
        """
        try:
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=self.target_sample_rate)
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            # Remove silence from beginning and end
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            return audio, sr
            
        except Exception as e:
            logger.error(f"Error preprocessing audio {audio_path}: {str(e)}")
            raise
    
    def save_preprocessed_audio(self, audio_data: np.ndarray, sample_rate: int, 
                              output_path: str) -> str:
        """Save preprocessed audio to file"""
        try:
            sf.write(output_path, audio_data, sample_rate)
            return output_path
        except Exception as e:
            logger.error(f"Error saving preprocessed audio: {str(e)}")
            raise
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception as e:
            logger.warning(f"Could not get duration for {audio_path}: {str(e)}")
            return 0.0
    
    def validate_audio_file(self, audio_path: str) -> bool:
        """Validate if audio file is processable"""
        try:
            audio_path = Path(audio_path)
            
            # Check if file exists
            if not audio_path.exists():
                return False
            
            # Check file extension
            valid_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
            if audio_path.suffix.lower() not in valid_extensions:
                return False
            
            # Try to load file
            librosa.load(str(audio_path), sr=None, duration=1.0)
            return True
            
        except Exception:
            return False