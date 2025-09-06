"""
Windows-compatible logging configuration (no emoji issues)
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output (Windows safe)"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logging(log_level: str = "INFO", log_dir: Path = None):
    """Setup Windows-compatible logging configuration"""
    
    # Force UTF-8 encoding for Windows
    if os.name == 'nt':  # Windows
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Try to set console to UTF-8 mode
        try:
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
    
    # Create logs directory if specified
    if log_dir:
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"dental_analysis_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors (Windows safe)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Windows-safe formatter (no emojis)
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Set encoding for Windows
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass
    
    root_logger.addHandler(console_handler)
    
    # File handler (if log directory is specified)
    if log_dir:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('whisper').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('pyannote').setLevel(logging.WARNING)
    
    return root_logger