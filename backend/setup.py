"""
Setup script for Dental Call Analysis System
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
    """Setup the environment for dental call analysis"""
    
    print("🦷 Setting up Dental Call Analysis System...")
    print("=" * 50)
    
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
""")
        print("✅ Created .env file")
        print("⚠️  Please edit .env file and add your HuggingFace token for speaker diarization")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your HuggingFace token")
    print("2. Place audio files in audio_files/ directory")
    print("3. Run: python main.py your_audio_file.wav")
    
    return True

if __name__ == "__main__":
    setup_environment()