"""
Setup script for Dental Call Analysis System with Emotion Detection
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def setup_environment():
    """Setup the environment for dental call analysis with emotion detection"""
    
    print("🦷 Setting up Dental Call Analysis System with Emotion Detection...")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3.8, 0):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Install requirements
    print("\n📦 Installing Python packages...")
    if not run_command("pip install -r requirements.txt"):
        print("❌ Failed to install requirements")
        return False
    
    # Check if Ollama is installed
    print("\n🤖 Checking Ollama installation...")
    if not run_command("ollama --version"):
        print("❌ Ollama not found. Please install from: https://ollama.ai")
        print("Then run: ollama pull qwen2.5:7b-instruct")
        return False
    
    # Pull Qwen model
    print("\n🧠 Pulling Qwen2.5 model...")
    if not run_command("ollama pull qwen2.5:7b-instruct"):
        print("❌ Failed to pull Qwen model")
        return False
    
    # Test emotion detection model download
    print("\n🎭 Testing emotion detection model download...")
    test_download_script = """
import warnings
warnings.filterwarnings("ignore")
try:
    from transformers import pipeline
    print("Testing emotion model download...")
    emotion_pipeline = pipeline("text-classification", 
                               model="j-hartmann/emotion-english-distilroberta-base",
                               return_all_scores=True)
    
    # Test with sample text
    result = emotion_pipeline("I am happy to test this model")
    print("✅ Emotion detection model downloaded and working!")
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
            f.write("""# Ollama Configuration
OLLAMA_URL=http://localhost:11434
LLM_MODEL_NAME=qwen2.5:7b-instruct

# Whisper Configuration  
WHISPER_MODEL=base
WHISPER_DEVICE=auto

# Pyannote Configuration
HUGGINGFACE_TOKEN=your_token_here
PYANNOTE_MODEL=pyannote/speaker-diarization-3.1

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
""")
        print("✅ Created .env file")
        print("⚠️ Please edit .env file and add your HuggingFace token for speaker diarization")
    
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
    print("1. Edit .env file with your HuggingFace token")
    print("2. Place audio files in audio_files/ directory")
    print("3. Run: python main.py")
    print("4. Test emotion detection: python test_emotion_detection.py")
    print("5. Quick emotion test: python test_emotions.py")
    
    print("\n🆕 NEW FEATURES ADDED:")
    print("✅ Emotion/Tone Detection using AI models")
    print("✅ Dental-specific emotion patterns (pain, anxiety, satisfaction)")
    print("✅ Professional tone analysis for staff")
    print("✅ Emotional alignment assessment")
    print("✅ Call escalation pattern detection")
    print("✅ Enhanced CSV/Google Sheets export with emotion data")
    
    print(f"\n📊 Your analysis pipeline now includes:")
    print("• Transcription + Speaker Diarization")
    print("• LLM-based Analysis + Performance Scoring")
    print("• Sentiment Analysis")
    print("• 🆕 Emotion Detection (pain, anxiety, satisfaction, etc.)")
    print("• 🆕 Professional Tone Analysis")
    print("• Opportunity Detection + Email Alerts")
    print("• Google Sheets Export + Detailed Reports")
    
    return True

if __name__ == "__main__":
    setup_environment()