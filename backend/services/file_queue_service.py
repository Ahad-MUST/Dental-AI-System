"""
File queue service to manage audio file processing and API integration
"""
import logging
import json
import aiohttp
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

class FileQueueService:
    """Manage audio file queue and API integration"""
    
    def __init__(self):
        self.processed_files_db = settings.OUTPUT_DIR / "processed_files.json"
        self.processed_files: Set[str] = set()
        self.load_processed_files()
        
    def load_processed_files(self):
        """Load list of already processed files"""
        try:
            if self.processed_files_db.exists():
                with open(self.processed_files_db, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                logger.info(f"Loaded {len(self.processed_files)} processed files from database")
            else:
                logger.info("No processed files database found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading processed files database: {str(e)}")
            self.processed_files = set()
    
    def save_processed_files(self):
        """Save processed files list to database"""
        try:
            data = {
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processed_files_db, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Processed files database saved")
        except Exception as e:
            logger.error(f"Error saving processed files database: {str(e)}")
    
    def mark_as_processed(self, filename: str):
        """Mark a file as processed"""
        self.processed_files.add(filename)
        self.save_processed_files()
        logger.info(f"Marked as processed: {filename}")
    
    def is_processed(self, filename: str) -> bool:
        """Check if file has already been processed"""
        return filename in self.processed_files
    
    async def get_local_audio_files(self) -> List[Path]:
        """Get all unprocessed audio files from local directory"""
        try:
            audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
            audio_files = []
            
            if not settings.AUDIO_INPUT_DIR.exists():
                logger.warning(f"Audio input directory does not exist: {settings.AUDIO_INPUT_DIR}")
                return []
            
            for file_path in settings.AUDIO_INPUT_DIR.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() in audio_extensions and
                    not self.is_processed(file_path.name)):
                    audio_files.append(file_path)
            
            # Sort by modification time (oldest first)
            audio_files.sort(key=lambda x: x.stat().st_mtime)
            
            logger.info(f"Found {len(audio_files)} unprocessed audio files")
            return audio_files
            
        except Exception as e:
            logger.error(f"Error scanning local audio files: {str(e)}")
            return []
    
    async def get_api_audio_files(self) -> List[Dict]:
        """Get audio files from API endpoint (future implementation)"""
        if not settings.USE_API_MODE:
            return []
            
        if not settings.API_ENDPOINT or not settings.API_KEY:
            logger.warning("API mode enabled but endpoint or key not configured")
            return []
            
        try:
            logger.info(f"Fetching audio files from API: {settings.API_ENDPOINT}")
            
            headers = {
                'Authorization': f'Bearer {settings.API_KEY}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.API_ENDPOINT, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Filter out already processed files
                        audio_files = []
                        for file_info in data.get('audio_files', []):
                            filename = file_info.get('filename', '')
                            if filename and not self.is_processed(filename):
                                audio_files.append(file_info)
                        
                        logger.info(f"Retrieved {len(audio_files)} unprocessed files from API")
                        return audio_files
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching files from API: {str(e)}")
            return []
    
    async def download_audio_file(self, file_info: Dict) -> Path:
        """Download audio file from API to local temp directory"""
        try:
            download_url = file_info.get('download_url')
            filename = file_info.get('filename')
            
            if not download_url or not filename:
                raise ValueError("Missing download_url or filename in API response")
            
            # Create temp directory for API downloads
            temp_dir = settings.OUTPUT_DIR / "temp_downloads"
            temp_dir.mkdir(exist_ok=True)
            
            local_path = temp_dir / filename
            
            headers = {
                'Authorization': f'Bearer {settings.API_KEY}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, headers=headers) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        logger.info(f"Downloaded audio file: {filename}")
                        return local_path
                    else:
                        raise Exception(f"Download failed with status {response.status}")
                        
        except Exception as e:  
            logger.error(f"Error downloading audio file: {str(e)}")
            raise
    
    def cleanup_temp_file(self, file_path: Path):
        """Clean up temporary downloaded file"""
        try:
            if file_path.exists() and "temp_downloads" in str(file_path):
                file_path.unlink()
                logger.debug(f"Cleaned up temp file: {file_path.name}")
        except Exception as e:
            logger.warning(f"Error cleaning up temp file: {str(e)}")
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        return {
            'total_processed': len(self.processed_files),
            'processed_files': list(self.processed_files),
            'last_updated': datetime.now().isoformat()
        }