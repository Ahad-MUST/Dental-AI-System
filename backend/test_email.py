"""
Test script to verify email configuration
"""
import asyncio
import logging
from config.settings import settings
from utils.logger import setup_logging
from services.email_alert_service import EmailAlertService

async def test_email_configuration():
    """Test email configuration"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL, settings.LOGS_DIR)
    logger = logging.getLogger(__name__)
    
    print("Testing Email Configuration...")
    print("=" * 40)
    
    # Initialize email service
    email_service = EmailAlertService()
    
    # Check configuration
    if not email_service.is_configured():
        print("❌ Email not properly configured!")
        print("\nRequired .env variables:")
        print("- EMAIL_ALERTS_ENABLED=true")
        print("- SENDER_EMAIL=your_email@gmail.com")
        print("- SENDER_PASSWORD=your_app_password")
        print("- ALERT_EMAIL=owner@dentaloffice.com")
        return False
    
    print("✅ Email configuration found")
    print(f"Sender: {settings.SENDER_EMAIL}")
    print(f"Alert Recipient: {settings.ALERT_EMAIL}")
    print(f"SMTP Server: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
    
    # Send test email
    print("\n📧 Sending test email...")
    success = await email_service.send_test_email()
    
    if success:
        print("✅ Test email sent successfully!")
        print(f"Check {settings.ALERT_EMAIL} for the test message")
        return True
    else:
        print("❌ Test email failed!")
        print("Check your email credentials and settings")
        return False

if __name__ == "__main__":
    asyncio.run(test_email_configuration())