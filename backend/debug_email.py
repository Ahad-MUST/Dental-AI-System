"""
Debug script to test email functionality with sample data
"""
import asyncio
import logging
from config.settings import settings
from utils.logger import setup_logging
from services.email_alert_service import EmailAlertService

async def test_high_opportunity_email():
    """Test email with mock high-opportunity call data"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL, settings.LOGS_DIR)
    logger = logging.getLogger(__name__)
    
    print("Testing High-Opportunity Email Alert...")
    print("=" * 50)
    
    # Create mock analysis result (similar to your actual call)
    mock_analysis_result = {
        "audio_file": "sample_call_11.mp3",
        "processing_time": 61.9,
        "transcription": {
            "full_transcript": "This call may be recorded for quality and training purposes. Hi, thank you for calling Lincoln Wood Family Dental. This is Whitney. How can I help you? Hi, I have a question about insurance. Do you accept Blue Cross Blue Shield Community Insurance Medicaid? We only accept PPO insurances, so Medicaid, no. Okay, thank you. You're welcome. Have a good day. You too.",
            "duration": 85.2,
            "confidence": 0.96
        },
        "speaker_count": 2,
        "call_summary": {
            "call_summary": "The main purpose of the call was to inquire about the acceptance of Blue Cross Blue Shield Community Insurance (Medicaid) at Lincoln Wood Family Dental. The discussion revealed that the office only accepts PPO insurances, leading to the conclusion that Medicaid is not accepted, and this information was confirmed by both parties."
        },
        "representative_name": "Whitney",
        "performance_analysis": {
            "overall_score": 0.750,
            "overall_grade": "C",
            "performance_level": "Satisfactory",
            "call_type": "insurance_verification"
        },
        "opportunity_analysis": {
            "high_value_missed": True
        }
    }
    
    # Initialize email service
    email_service = EmailAlertService()
    
    # Check configuration
    print(f"Email enabled: {email_service.enabled}")
    print(f"Email configured: {email_service.is_configured()}")
    print(f"Sender: {email_service.sender_email}")
    print(f"Alert recipient: {email_service.alert_email}")
    
    if not email_service.is_configured():
        print("\n❌ Email not properly configured!")
        return False
    
    # Test sending high-opportunity alert
    print(f"\n📧 Sending high-opportunity alert for {mock_analysis_result['audio_file']}...")
    
    success = await email_service.send_high_opportunity_alert(mock_analysis_result)
    
    if success:
        print("✅ High-opportunity alert sent successfully!")
        print(f"Check {settings.ALERT_EMAIL} for the alert email")
        return True
    else:
        print("❌ High-opportunity alert failed!")
        print("Check email configuration and logs for errors")
        return False

if __name__ == "__main__":
    asyncio.run(test_high_opportunity_email())