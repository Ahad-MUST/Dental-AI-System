"""
Management script for the file monitoring system
"""
import asyncio
import requests
import json
from config.settings import settings

class MonitorManager:
    """Simple manager for the monitoring API"""
    
    def __init__(self):
        self.api_base = f"http://{settings.API_HOST}:{settings.API_PORT}"
    
    def _make_request(self, method: str, endpoint: str) -> dict:
        """Make API request"""
        try:
            url = f"{self.api_base}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API server at {self.api_base}")
            print("Make sure the API server is running: python api_server.py")
            return {}
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {str(e)}")
            return {}
    
    def status(self):
        """Get system status"""
        print("Dental Call Analysis System Status")
        print("=" * 40)
        
        result = self._make_request("GET", "/")
        if result:
            print(f"API Status: {result.get('status', 'unknown')}")
            
            monitor_status = result.get('monitoring_status', {})
            print(f"Monitoring: {'✅ Running' if monitor_status.get('is_running') else '⏸️  Stopped'}")
            print(f"Monitor Directory: {monitor_status.get('monitor_directory', 'unknown')}")
            print(f"Queue Size: {monitor_status.get('queue_size', 0)}/{monitor_status.get('max_queue_size', 0)}")
            
            if monitor_status.get('files_in_queue'):
                print(f"Files in Queue: {', '.join(monitor_status['files_in_queue'])}")
    
    def start(self):
        """Start monitoring"""
        print("Starting file monitoring...")
        result = self._make_request("POST", "/monitor/start")
        
        if result:
            print(f"✅ {result.get('message', 'Started')}")
        else:
            print("❌ Failed to start monitoring")
    
    def stop(self):
        """Stop monitoring"""
        print("Stopping file monitoring...")
        result = self._make_request("POST", "/monitor/stop")
        
        if result:
            print(f"⏹️  {result.get('message', 'Stopped')}")
        else:
            print("❌ Failed to stop monitoring")
    
    def queue(self):
        """Show queue details"""
        print("Processing Queue Details")
        print("=" * 30)
        
        result = self._make_request("GET", "/monitor/queue")
        if result:
            print(f"Queue Size: {result.get('queue_size', 0)}")
            print(f"Max Capacity: {result.get('max_queue_size', 0)}")
            
            files = result.get('files_in_queue', [])
            if files:
                print("\nFiles in Queue:")
                for i, file_info in enumerate(files, 1):
                    print(f"  {i}. {file_info['filename']} ({file_info['size_mb']} MB)")
            else:
                print("\nNo files in queue")
    
    def stats(self):
        """Show processing statistics"""
        print("Processing Statistics")
        print("=" * 25)
        
        result = self._make_request("GET", "/stats")
        if result:
            print(f"Processed Files: {result.get('processed_files_count', 0)}")
            print(f"Pending Files: {result.get('pending_files_count', 0)}")
            print(f"Queue Size: {result.get('queue_size', 0)}")
            print(f"Monitor Running: {'Yes' if result.get('monitor_running') else 'No'}")
            
            latest = result.get('latest_processed', [])
            if latest:
                print(f"\nLatest Processed Files:")
                for file in latest:
                    print(f"  - {file}")
    
    def config(self):
        """Show current configuration"""
        print("System Configuration")
        print("=" * 22)
        
        result = self._make_request("GET", "/config")
        if result:
            print(f"Monitor Directory: {result.get('monitor_directory', 'unknown')}")
            print(f"Processed Directory: {result.get('processed_directory', 'unknown')}")
            print(f"Output Directory: {result.get('output_directory', 'unknown')}")
            print(f"Max Queue Size: {result.get('max_queue_size', 0)}")
            print(f"Processing Delay: {result.get('processing_delay', 0)}s")
            print(f"Google Sheets: {'Enabled' if result.get('google_sheets_enabled') else 'Disabled'}")
            print(f"Email Alerts: {'Enabled' if result.get('email_alerts_enabled') else 'Disabled'}")

def main():
    """CLI interface"""
    import sys
    
    manager = MonitorManager()
    
    if len(sys.argv) < 2:
        print("Dental Call Analysis Monitor Manager")
        print("Usage: python monitor_manager.py <command>")
        print("\nAvailable commands:")
        print("  status    - Show system status")
        print("  start     - Start file monitoring")
        print("  stop      - Stop file monitoring") 
        print("  queue     - Show processing queue")
        print("  stats     - Show processing statistics")
        print("  config    - Show configuration")
        print("\nExample: python monitor_manager.py status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        manager.status()
    elif command == "start":
        manager.start()
    elif command == "stop":
        manager.stop()
    elif command == "queue":
        manager.queue()
    elif command == "stats":
        manager.stats()
    elif command == "config":
        manager.config()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, start, stop, queue, stats, config")

if __name__ == "__main__":
    main()