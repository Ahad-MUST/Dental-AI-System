"""
Statistics Management and Reporting
Handles all statistics tracking and final report generation
"""
import logging
from typing import Dict
from config.settings import settings

logger = logging.getLogger(__name__)

class StatsManager:
    """Manages processing statistics and generates reports"""
    
    def __init__(self, employee_service, file_queue_service):
        self.employee_service = employee_service
        self.file_queue_service = file_queue_service
        
        # Processing stats
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'high_opportunities': 0,
            'sentiment_stats': {
                'positive': 0,
                'neutral': 0, 
                'negative': 0
            },
            'emotion_stats': {
                'high_emotion_calls': 0,
                'pain_detected': 0,
                'anxiety_detected': 0,
                'satisfaction_detected': 0
            },
            'tagging_stats': {},
            'speaker_assignment_stats': {
                'llm_based_assignments': 0,
                'rule_based_fallbacks': 0,
                'three_speaker_calls': 0
            }
        }
    
    def update_enhanced_stats(self, results: Dict):
        """Update enhanced statistics including employee list usage"""
        
        # Update sentiment stats
        try:
            sentiment_analysis = results.get("sentiment_analysis", {})
            overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
            sentiment_label = overall_sentiment.get("sentiment_label", "unknown")
            
            if sentiment_label in self.stats['sentiment_stats']:
                self.stats['sentiment_stats'][sentiment_label] += 1
        except Exception as e:
            logger.warning(f"Failed to update sentiment stats: {str(e)}")
        
        # Update emotion stats
        try:
            emotion_analysis = results.get("emotion_analysis", {})
            emotion_flags = emotion_analysis.get("emotion_flags", [])
            patient_emotions = emotion_analysis.get("patient_emotions", {})
            
            if patient_emotions.get("intensity") == "high":
                self.stats['emotion_stats']['high_emotion_calls'] += 1
            
            for flag in emotion_flags:
                if "PAIN" in flag or "pain" in flag.lower():
                    self.stats['emotion_stats']['pain_detected'] += 1
                elif "ANXIETY" in flag or "anxiety" in flag.lower():
                    self.stats['emotion_stats']['anxiety_detected'] += 1
                elif "SATISFACTION" in flag or "satisfaction" in flag.lower():
                    self.stats['emotion_stats']['satisfaction_detected'] += 1
        except Exception as e:
            logger.warning(f"Failed to update emotion stats: {str(e)}")
        
        # Update tagging stats
        try:
            call_tag_analysis = results.get("call_tag_analysis", {})
            primary_tag = call_tag_analysis.get("primary_tag", "unknown")
            
            if primary_tag not in self.stats['tagging_stats']:
                self.stats['tagging_stats'][primary_tag] = 0
            self.stats['tagging_stats'][primary_tag] += 1
        except Exception as e:
            logger.warning(f"Failed to update tagging stats: {str(e)}")
        
        # Update speaker assignment stats
        try:
            if results.get("speaker_role_assignment") == "llm_based":
                self.stats['speaker_assignment_stats']['llm_based_assignments'] += 1
            else:
                self.stats['speaker_assignment_stats']['rule_based_fallbacks'] += 1
                
            # Track three+ speaker calls
            if results.get("diarization_speaker_count", 0) >= 3:
                self.stats['speaker_assignment_stats']['three_speaker_calls'] += 1
        except Exception as e:
            logger.warning(f"Failed to update speaker assignment stats: {str(e)}")
    
    def increment_total_processed(self):
        """Increment total processed counter"""
        self.stats['total_processed'] += 1
    
    def increment_successful(self):
        """Increment successful counter"""
        self.stats['successful'] += 1
    
    def increment_failed(self):
        """Increment failed counter"""
        self.stats['failed'] += 1
    
    def increment_high_opportunities(self):
        """Increment high opportunities counter"""
        self.stats['high_opportunities'] += 1
    
    def get_stats(self):
        """Get current stats dictionary"""
        return self.stats.copy()
    
    def get_success_rate(self):
        """Calculate success rate percentage"""
        if self.stats['total_processed'] > 0:
            return (self.stats['successful'] / self.stats['total_processed']) * 100
        return 0.0
    
    def get_opportunity_rate(self):
        """Calculate missed opportunity rate percentage"""
        if self.stats['successful'] > 0:
            return (self.stats['high_opportunities'] / self.stats['successful']) * 100
        return 0.0
    
    def display_enhanced_final_stats(self):
        """Display enhanced final processing statistics"""
        print("\n" + "="*80)
        print("DENTAL CALL ANALYSIS - FINAL REPORT")
        print("="*80)
        
        # Processing summary
        print(f"\nProcessing Summary:")
        print(f"   Total calls processed: {self.stats['total_processed']}")
        print(f"   Successful: {self.stats['successful']}")
        print(f"   Failed: {self.stats['failed']}")
        if self.stats['total_processed'] > 0:
            success_rate = self.get_success_rate()
            print(f"   Success rate: {success_rate:.1f}%")
        
        # Employee list summary
        employees = self.employee_service.get_employees()
        print(f"\nEmployee List Management:")
        print(f"   Configured employees: {len(employees)}")
        print(f"   Employee names: {', '.join(employees)}")
        
        # Opportunity analysis
        print(f"\nOpportunity Analysis:")
        print(f"   High-value missed opportunities: {self.stats['high_opportunities']}")
        if self.stats['successful'] > 0:
            opportunity_rate = self.get_opportunity_rate()
            print(f"   Missed opportunity rate: {opportunity_rate:.1f}%")
        
        # Sentiment analysis
        print(f"\nSentiment Analysis:")
        for sentiment, count in self.stats['sentiment_stats'].items():
            if count > 0:
                print(f"   {sentiment.title()}: {count}")
        
        # Emotion analysis
        print(f"\nEmotion Analysis:")
        for emotion, count in self.stats['emotion_stats'].items():
            if count > 0:
                print(f"   {emotion.replace('_', ' ').title()}: {count}")
        
        # Call tagging
        if self.stats['tagging_stats']:
            print(f"\nCall Tagging:")
            for tag, count in self.stats['tagging_stats'].items():
                if count > 0:
                    print(f"   {tag.replace('_', ' ').title()}: {count}")
        
        # Speaker assignment stats
        print(f"\nSpeaker Assignment:")
        print(f"   LLM-based assignments: {self.stats['speaker_assignment_stats']['llm_based_assignments']}")
        print(f"   Rule-based fallbacks: {self.stats['speaker_assignment_stats']['rule_based_fallbacks']}")
        print(f"   Three+ speaker calls: {self.stats['speaker_assignment_stats']['three_speaker_calls']}")
        
        # Export information
        if settings.USE_GOOGLE_SHEETS:
            print("\nResults exported to Google Sheets for dashboard viewing")
        
        print("\nAll calls have been automatically categorized for better organization.")
        print("Speaker roles are now intelligently assigned using LLM analysis.")
        print("Representative names are extracted from predefined employee list.")
        
        print(f"\nMode: {'API' if settings.USE_API_MODE else 'Local Directory'}")
        print(f"Enhanced Features: Tagging ✅ | Emotion Detection ✅ | Smart Speaker Assignment ✅ | Employee List ✅")
        print(f"Processed files tracked in: {self.file_queue_service.processed_files_db}")
        print(f"Employee list stored in: {self.employee_service.employees_file}")
        print("="*80)
    
    def print_summary_stats(self):
        """Print quick summary stats during processing"""
        print(f"\nCurrent Stats: Processed: {self.stats['total_processed']} | "
              f"Success: {self.stats['successful']} | "
              f"Failed: {self.stats['failed']} | "
              f"High Opportunities: {self.stats['high_opportunities']}")
    
    def reset_stats(self):
        """Reset all statistics to zero"""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'high_opportunities': 0,
            'sentiment_stats': {
                'positive': 0,
                'neutral': 0, 
                'negative': 0
            },
            'emotion_stats': {
                'high_emotion_calls': 0,
                'pain_detected': 0,
                'anxiety_detected': 0,
                'satisfaction_detected': 0
            },
            'tagging_stats': {},
            'speaker_assignment_stats': {
                'llm_based_assignments': 0,
                'rule_based_fallbacks': 0,
                'three_speaker_calls': 0
            }
        }
        logger.info("Statistics reset to zero")
    
    def export_stats_to_dict(self):
        """Export current statistics as dictionary for JSON/API export"""
        employees = self.employee_service.get_employees()
        
        return {
            'processing_summary': {
                'total_processed': self.stats['total_processed'],
                'successful': self.stats['successful'],
                'failed': self.stats['failed'],
                'success_rate': self.get_success_rate()
            },
            'employee_management': {
                'configured_employees': len(employees),
                'employee_names': employees
            },
            'opportunity_analysis': {
                'high_value_missed': self.stats['high_opportunities'],
                'opportunity_rate': self.get_opportunity_rate()
            },
            'sentiment_analysis': self.stats['sentiment_stats'].copy(),
            'emotion_analysis': self.stats['emotion_stats'].copy(),
            'call_tagging': self.stats['tagging_stats'].copy(),
            'speaker_assignment': self.stats['speaker_assignment_stats'].copy(),
            'system_info': {
                'mode': 'API' if settings.USE_API_MODE else 'Local Directory',
                'google_sheets_enabled': settings.USE_GOOGLE_SHEETS,
                'processed_files_db': str(self.file_queue_service.processed_files_db),
                'employee_list_file': str(self.employee_service.employees_file)
            }
        }