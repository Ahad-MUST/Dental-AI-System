"""
Configuration settings for Dental Call Analysis System
Updated with API server and employee management configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    AUDIO_INPUT_DIR = BASE_DIR / os.getenv("AUDIO_INPUT_DIR", "audio_files")
    OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
    LOGS_DIR = BASE_DIR / "logs"
    
    # Ollama/LLM Configuration
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5:7b-instruct")
    
    # Whisper Configuration
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")
    
    # SpeechBrain Configuration (replacing Pyannote)
    SPEECHBRAIN_SPEAKER_MODEL = os.getenv("SPEECHBRAIN_SPEAKER_MODEL", "speechbrain/spkrec-ecapa-voxceleb")
    SPEECHBRAIN_VAD_MODEL = os.getenv("SPEECHBRAIN_VAD_MODEL", "speechbrain/vad-crdnn-libriparty")
    SPEECHBRAIN_DEVICE = os.getenv("SPEECHBRAIN_DEVICE", "auto")
    
    # Legacy Pyannote Configuration (kept for backwards compatibility)
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    PYANNOTE_MODEL = os.getenv("PYANNOTE_MODEL", "pyannote/speaker-diarization-3.1")
    
    # Processing Configuration
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CSV Export Configuration (kept for backup)
    CSV_FILENAME = os.getenv("CSV_FILENAME", "call_analysis_results.csv")
    EXPORT_DETAILED_REPORTS = os.getenv("EXPORT_DETAILED_REPORTS", "true").lower() == "true"
    
    # Google Sheets Configuration
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_CREDENTIALS_FILE = BASE_DIR / os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
    USE_GOOGLE_SHEETS = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
    
    # Email Alert Configuration
    EMAIL_ALERTS_ENABLED = os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true"
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
    ALERT_EMAIL = os.getenv("ALERT_EMAIL")
    CLINIC_NAME = os.getenv("CLINIC_NAME", "Dental Clinic")
    
    # API Configuration (for future client integration)
    USE_API_MODE = os.getenv("USE_API_MODE", "false").lower() == "true"
    API_ENDPOINT = os.getenv("API_ENDPOINT")
    API_KEY = os.getenv("API_KEY")
    API_POLLING_INTERVAL = int(os.getenv("API_POLLING_INTERVAL", "300"))  # 5 minutes default
    
    # API Server Configuration (NEW)
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_CORS_ORIGINS = os.getenv("API_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    # Employee Management Configuration (NEW)
    DEFAULT_EMPLOYEES = [
        "Aminah Jafri",
        "Jovana Vanegas", 
        "Melina Rodriguez",
        "Whitney Minor",
        "Yuseli Saldana"
    ]
    
    def __init__(self):
        """Create necessary directories"""
        self.AUDIO_INPUT_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)

# Global settings instance
settings = Settings()