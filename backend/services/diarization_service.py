"""
Speaker diarization service using SpeechBrain
"""
import logging
import asyncio
import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

# Suppress warnings
warnings.filterwarnings("ignore")

try:
    from speechbrain.pretrained import SpeakerRecognition, VAD
    import torchaudio
    import torch
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class DiarizationService:
    """Speaker diarization using SpeechBrain"""
    
    def __init__(self):
        self.speaker_model = None
        self.vad_model = None
        self.device = self._get_device()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.sample_rate = 16000
        
    def _get_device(self) -> str:
        """Get optimal device for processing"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    async def load_model(self) -> None:
        """Load SpeechBrain models"""
        if not SPEECHBRAIN_AVAILABLE:
            logger.warning("SpeechBrain not available, using fallback speaker assignment")
            return
            
        if self.speaker_model is not None and self.vad_model is not None:
            return
            
        try:
            logger.info("Loading SpeechBrain speaker recognition and VAD models...")
            loop = asyncio.get_event_loop()
            self.speaker_model, self.vad_model = await loop.run_in_executor(
                self.executor,
                self._load_models_sync
            )
            logger.info("SpeechBrain models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load SpeechBrain models: {str(e)}, using fallback")
            self.speaker_model = None
            self.vad_model = None
    
    def _load_models_sync(self):
        """Load models synchronously"""
        try:
            # Load speaker recognition model
            speaker_model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device": self.device}
            )
            
            # Load VAD model
            vad_model = VAD.from_hparams(
                source="speechbrain/vad-crdnn-libriparty",
                savedir="pretrained_models/vad-crdnn-libriparty",
                run_opts={"device": self.device}
            )
            
            return speaker_model, vad_model
            
        except Exception as e:
            logger.warning(f"Model loading failed: {str(e)}")
            return None, None
    
    async def diarize_speakers(self, audio_path: str) -> Dict:
        """
        Perform speaker diarization using SpeechBrain
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with speaker timeline
        """
        try:
            # Ensure models are loaded
            if self.speaker_model is None or self.vad_model is None:
                await self.load_model()
            
            # If still no models, use fallback
            if self.speaker_model is None or self.vad_model is None:
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
            
            logger.info(f"Diarization completed - Found {diarization_result['speaker_count']} speakers")
            
            return diarization_result
            
        except Exception as e:
            logger.warning(f"Diarization failed: {str(e)}, using fallback")
            return await self._fallback_speaker_assignment(audio_path)
    
    def _diarize_sync(self, audio_path: str) -> Dict:
        """Synchronous diarization using SpeechBrain"""
        try:
            # Load audio
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
                waveform = resampler(waveform)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Move to device
            waveform = waveform.to(self.device)
            
            # Get audio duration
            duration = waveform.shape[1] / self.sample_rate
            
            # Perform VAD to detect speech segments
            speech_segments = self._detect_speech_segments(waveform)
            
            # Extract speaker embeddings and perform clustering
            speaker_timeline = self._extract_speakers_and_cluster(waveform, speech_segments, duration)
            
            # Count unique speakers
            speakers_found = list(set([seg["speaker"] for seg in speaker_timeline]))
            
            return {
                "speaker_timeline": speaker_timeline,
                "speaker_count": len(speakers_found),
                "speakers_found": speakers_found,
                "audio_file": Path(audio_path).name
            }
            
        except Exception as e:
            logger.error(f"SpeechBrain diarization error: {str(e)}")
            return None
    
    def _detect_speech_segments(self, waveform: torch.Tensor) -> List[Tuple[float, float]]:
        """Detect speech segments using VAD"""
        try:
            # Run VAD
            speech_prob = self.vad_model.get_speech_prob_file(waveform)
            
            # Convert probabilities to binary decisions
            speech_threshold = 0.5
            speech_binary = (speech_prob > speech_threshold).float()
            
            # Find speech segments
            segments = []
            in_speech = False
            start_time = 0
            
            frame_duration = 1.0 / self.sample_rate * 512  # Assuming 512 samples per frame
            
            for i, is_speech in enumerate(speech_binary):
                current_time = i * frame_duration
                
                if is_speech and not in_speech:
                    # Start of speech segment
                    start_time = current_time
                    in_speech = True
                elif not is_speech and in_speech:
                    # End of speech segment
                    if current_time - start_time > 0.5:  # Minimum 0.5s segment
                        segments.append((start_time, current_time))
                    in_speech = False
            
            # Handle case where speech continues to end
            if in_speech:
                final_time = len(speech_binary) * frame_duration
                if final_time - start_time > 0.5:
                    segments.append((start_time, final_time))
            
            return segments if segments else [(0, waveform.shape[1] / self.sample_rate)]
            
        except Exception as e:
            logger.warning(f"VAD failed: {str(e)}, using full audio")
            # Return full audio as single segment
            duration = waveform.shape[1] / self.sample_rate
            return [(0, duration)]
    
    def _extract_speakers_and_cluster(self, waveform: torch.Tensor, speech_segments: List[Tuple[float, float]], duration: float) -> List[Dict]:
        """Extract speaker embeddings and perform clustering"""
        try:
            embeddings = []
            segment_info = []
            
            # Extract embeddings for each speech segment
            for start_time, end_time in speech_segments:
                start_sample = int(start_time * self.sample_rate)
                end_sample = int(end_time * self.sample_rate)
                
                # Extract segment
                segment_waveform = waveform[:, start_sample:end_sample]
                
                # Skip very short segments
                if segment_waveform.shape[1] < self.sample_rate * 0.5:  # Skip segments < 0.5s
                    continue
                
                try:
                    # Extract speaker embedding
                    embedding = self.speaker_model.encode_batch(segment_waveform.unsqueeze(0))
                    embeddings.append(embedding.squeeze().cpu().numpy())
                    segment_info.append({
                        "start_time": round(start_time, 2),
                        "end_time": round(end_time, 2),
                        "duration": round(end_time - start_time, 2)
                    })
                except Exception as e:
                    logger.warning(f"Failed to extract embedding for segment {start_time}-{end_time}: {str(e)}")
                    continue
            
            if not embeddings:
                # Fallback: create simple alternating segments
                return self._create_alternating_segments(duration)
            
            # Perform clustering to identify speakers
            speaker_labels = self._cluster_speakers(embeddings)
            
            # Assign speaker labels
            speaker_timeline = []
            for i, (segment, label) in enumerate(zip(segment_info, speaker_labels)):
                segment["speaker"] = f"SPEAKER_{label:02d}"
                speaker_timeline.append(segment)
            
            # Fill gaps between segments with alternating speakers
            speaker_timeline = self._fill_gaps(speaker_timeline, duration)
            
            return speaker_timeline
            
        except Exception as e:
            logger.warning(f"Speaker clustering failed: {str(e)}")
            return self._create_alternating_segments(duration)
    
    def _cluster_speakers(self, embeddings: List[np.ndarray]) -> List[int]:
        """Cluster speaker embeddings to identify unique speakers"""
        try:
            if len(embeddings) <= 1:
                return [0] * len(embeddings)
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # Use simple distance-based clustering
            from sklearn.cluster import AgglomerativeClustering
            
            # Start with assumption of 2 speakers (typical for dental calls)
            n_clusters = min(2, len(embeddings))
            
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='average',
                metric='cosine'
            )
            
            labels = clustering.fit_predict(embeddings_array)
            
            return labels.tolist()
            
        except Exception as e:
            logger.warning(f"Clustering failed: {str(e)}, using alternating assignment")
            # Fallback: alternate between two speakers
            return [i % 2 for i in range(len(embeddings))]
    
    def _fill_gaps(self, speaker_timeline: List[Dict], total_duration: float) -> List[Dict]:
        """Fill gaps between detected speech segments"""
        if not speaker_timeline:
            return self._create_alternating_segments(total_duration)
        
        # Sort by start time
        speaker_timeline.sort(key=lambda x: x["start_time"])
        
        filled_timeline = []
        current_time = 0.0
        
        for segment in speaker_timeline:
            # Fill gap before this segment
            if current_time < segment["start_time"]:
                gap_duration = segment["start_time"] - current_time
                if gap_duration > 0.1:  # Only fill gaps > 0.1s
                    # Use previous speaker or alternate
                    prev_speaker = filled_timeline[-1]["speaker"] if filled_timeline else "SPEAKER_00"
                    gap_segment = {
                        "start_time": round(current_time, 2),
                        "end_time": round(segment["start_time"], 2),
                        "duration": round(gap_duration, 2),
                        "speaker": prev_speaker
                    }
                    filled_timeline.append(gap_segment)
            
            filled_timeline.append(segment)
            current_time = segment["end_time"]
        
        # Fill final gap if needed
        if current_time < total_duration:
            gap_duration = total_duration - current_time
            if gap_duration > 0.1:
                final_speaker = filled_timeline[-1]["speaker"] if filled_timeline else "SPEAKER_00"
                gap_segment = {
                    "start_time": round(current_time, 2),
                    "end_time": round(total_duration, 2),
                    "duration": round(gap_duration, 2),
                    "speaker": final_speaker
                }
                filled_timeline.append(gap_segment)
        
        return filled_timeline
    
    def _create_alternating_segments(self, duration: float) -> List[Dict]:
        """Create alternating speaker segments as fallback"""
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
        
        return speaker_timeline
    
    async def _fallback_speaker_assignment(self, audio_path: str) -> Dict:
        """Fallback speaker assignment when diarization fails"""
        
        from utils.audio_processor import AudioProcessor
        audio_processor = AudioProcessor()
        
        try:
            duration = audio_processor.get_audio_duration(audio_path)
        except:
            duration = 60.0  # Default duration
        
        # Create alternating speaker segments
        speaker_timeline = self._create_alternating_segments(duration)
        
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
        if self.speaker_model:
            del self.speaker_model
            self.speaker_model = None
        if self.vad_model:
            del self.vad_model
            self.vad_model = None