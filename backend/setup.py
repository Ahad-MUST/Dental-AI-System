#!/usr/bin/env python3
"""
Enhanced Setup Script for Dental Call Analysis System with SpeechBrain
"""
import subprocess
import sys
import time
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing Python packages...")
    
    # Use the updated requirements.txt
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {str(e)}")
        return False

def test_speechbrain_models():
    """Test SpeechBrain model loading"""
    print("\n🧠 Testing SpeechBrain models...")
    
    test_speechbrain_script = """
try:
    from speechbrain_engine import SpeechBrainEngine
    print("✅ SpeechBrain engine import successful")
    
    # Test engine initialization (this will download models if needed)
    engine = SpeechBrainEngine(device="cpu")  # Use CPU for setup
    print("✅ SpeechBrain models loaded successfully")
    print(f"Device: {engine.device}")
    print(f"VAD Available: {engine.vad_model is not None}")
    
except ImportError as e:
    print(f"❌ SpeechBrain import failed: {str(e)}")
    print("Please run: pip install speechbrain")
except Exception as e:
    print(f"⚠️ SpeechBrain model loading failed: {str(e)}")
    print("Models will be downloaded automatically on first use")
"""
    
    try:
        exec(test_speechbrain_script)
    except Exception as e:
        print(f"⚠️ SpeechBrain test failed: {str(e)}")
        print("SpeechBrain models will be downloaded automatically when first used")

def setup_environment():
    """Setup the complete environment"""
    print("🦷 Dental Call Analysis System Setup (SpeechBrain Edition)")
    print("=" * 60)
    
    # Install packages
    if not install_requirements():
        print("❌ Setup failed at package installation")
        return False
    
    # Test SpeechBrain
    test_speechbrain_models()
    
    # Test emotion detection model download
    print("\n😊 Testing emotion detection models...")
    test_download_script = """
try:
    from transformers import pipeline
    print("Loading emotion detection model...")
    classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        device=-1  # CPU
    )
    result = classifier("I am feeling great today!")
    print(f"Test result: {result[0]['label']} ({result[0]['score']:.3f})")
except Exception as e:
    print(f"❌ Emotion detection model test failed: {str(e)}")
    print("Model will be downloaded on first use")
"""
    
    try:
        exec(test_download_script)
    except Exception as e:
        print(f"⚠️ Emotion model pre-download failed: {str(e)}")
        print("Model will be downloaded automatically when first used")
    
    # Create directories
    print("\n📁 Creating directories...")
    directories = ['audio_files', 'outputs', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/")
    
    # Setup example .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        print("\n⚙️ Creating .env configuration file...")
        with open('.env', 'w') as f:
            f.write("""# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo
OPENAI_TEMPERATURE=0.1

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_DEVICE=auto

# SpeechBrain Configuration
# No special tokens needed for SpeechBrain - models download automatically
SPEECHBRAIN_DEVICE=auto

# Processing Configuration
MAX_WORKERS=2
AUDIO_SAMPLE_RATE=16000

# Output Configuration
OUTPUT_DIR=outputs
AUDIO_INPUT_DIR=audio_files
LOG_LEVEL=INFO

# CSV Export Configuration
CSV_FILENAME=call_analysis_results.csv
EXPORT_DETAILED_REPORTS=true

# Google Sheets Configuration (Optional)
USE_GOOGLE_SHEETS=false
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_FILE=google_credentials.json

# Email Alert Configuration (Optional)
EMAIL_ALERTS_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
ALERT_EMAIL=owner@dentaloffice.com
CLINIC_NAME=Your Dental Clinic

# API Configuration (Optional)
USE_API_MODE=false
API_ENDPOINT=https://your-api-endpoint.com/audio-files
API_KEY=your_api_key_here
API_POLLING_INTERVAL=300

# Audio Processing
AUDIO_CROP_START_SECONDS=3
""")
        print("✅ Created .env file")
        print("⚠️ IMPORTANT: Add your OpenAI API key to .env file before running!")
        print("ℹ️ SpeechBrain models will download automatically (no token required)")
    
    # Create test script for emotion detection
    print("\n🧪 Creating emotion detection test script...")
    test_script_path = Path('test_emotions.py')
    if not test_script_path.exists():
        with open('test_emotions.py', 'w') as f:
            f.write("""#!/usr/bin/env python3
# Quick test script for emotion detection
import asyncio
from services.emotion_detection_service import EmotionDetectionService

async def quick_test():
    service = EmotionDetectionService()
    await service.initialize()
    
    patient_text = "I'm in terrible pain and really scared about my appointment."
    staff_text = "I understand your concern and we'll take great care of you."
    
    results = await service.analyze_call_emotions(patient_text, staff_text)
    
    print("Emotion Detection Test Results:")
    print(f"Patient: {results['patient_emotions']['primary_emotion']}")
    print(f"Staff: {results['staff_emotions']['primary_emotion']}")
    
    await service.cleanup()

if __name__ == "__main__":
    asyncio.run(quick_test())
""")
        print("✅ Created test_emotions.py")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Place audio files in audio_files/ directory")
    print("2. Run: python main.py")
    print("3. Test emotion detection: python test_emotion_detection.py")
    print("4. Quick emotion test: python test_emotions.py")
    
    print("\n🆕 SPEECHBRAIN FEATURES:")
    print("✅ Advanced speaker diarization using ECAPA-TDNN embeddings")
    print("✅ Voice Activity Detection (VAD) with neural networks")
    print("✅ Automatic model downloading (no tokens required)")
    print("✅ Improved clustering with cosine distance")
    print("✅ Better handling of overlapping speech")
    print("✅ No HuggingFace token dependency")
    
    print(f"\n📊 Your analysis pipeline now includes:")
    print("• Transcription + SpeechBrain Speaker Diarization")
    print("• LLM-based Analysis + Performance Scoring")
    print("• Sentiment Analysis")
    print("• 🆕 Emotion Detection (pain, anxiety, satisfaction, etc.)")
    print("• 🆕 Professional Tone Analysis")
    print("• Opportunity Detection + Email Alerts")
    print("• Google Sheets Export + Detailed Reports")
    
    print(f"\n🔄 MIGRATION FROM PYANNOTE:")
    print("• Removed HuggingFace token requirement")
    print("• Better speaker separation accuracy")
    print("• Faster processing with optimized models")
    print("• More robust handling of audio formats")
    
    return True

if __name__ == "__main__":
    setup_environment()