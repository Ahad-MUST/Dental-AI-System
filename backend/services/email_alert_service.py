"""
Email alert service for high-value missed opportunities
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailAlertService:
    """Send email alerts for high-value missed opportunities"""
    
    def __init__(self):
        self.enabled = settings.EMAIL_ALERTS_ENABLED
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.sender_email = settings.SENDER_EMAIL
        self.sender_password = settings.SENDER_PASSWORD
        self.alert_email = settings.ALERT_EMAIL
        self.clinic_name = settings.CLINIC_NAME
        
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.enabled,
            self.sender_email,
            self.sender_password,
            self.alert_email
        ])
    
    async def send_high_opportunity_alert(self, analysis_result: Dict) -> bool:
        """
        Send email alert for high-value missed opportunity
        
        Args:
            analysis_result: Complete analysis result
            
        Returns:
            bool: Success status
        """
        if not self.is_configured():
            logger.warning("Email alerts not properly configured - skipping alert")
            return False
            
        try:
            # Extract key information
            audio_file = analysis_result.get("audio_file", "unknown.wav")
            call_summary = analysis_result.get("call_summary", {})
            representative_name = analysis_result.get("representative_name", "Unknown")
            performance = analysis_result.get("performance_analysis", {})
            transcription = analysis_result.get("transcription", {})
            
            # Create email content
            subject = f"ðŸš¨ HIGH-VALUE OPPORTUNITY MISSED - {audio_file}"
            
            html_content = self._create_email_html(
                audio_file=audio_file,
                call_summary=call_summary.get("call_summary", "Summary not available"),
                representative_name=representative_name,
                performance_score=performance.get("overall_score", 0.0),
                call_duration=transcription.get("duration", 0),
                full_transcript=transcription.get("full_transcript", "Transcript not available")
            )
            
            # Send email
            success = await self._send_email(subject, html_content)
            
            if success:
                logger.info(f"High-opportunity alert sent for {audio_file}")
            else:
                logger.error(f"Failed to send high-opportunity alert for {audio_file}")
                
            return success
            
        except Exception as e:
            logger.error(f"Email alert failed: {str(e)}")
            return False
    
    def _create_email_html(self, audio_file: str, call_summary: str, representative_name: str, 
                          performance_score: float, call_duration: float, full_transcript: str) -> str:
        """Create HTML email content"""
        
        # Truncate transcript if too long
        max_transcript_length = 1000
        display_transcript = full_transcript
        if len(full_transcript) > max_transcript_length:
            display_transcript = full_transcript[:max_transcript_length] + "... [TRUNCATED]"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .alert-box {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .info-table th, .info-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .info-table th {{ background-color: #f2f2f2; font-weight: bold; }}
        .transcript-box {{ background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        .action-required {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ðŸš¨ HIGH-VALUE OPPORTUNITY MISSED</h1>
        <p>Immediate Follow-up Required</p>
    </div>
    
    <div class="content">
        <div class="alert-box">
            <h3>âš ï¸ URGENT: Revenue Opportunity Not Captured</h3>
            <p>A patient inquiry with high revenue potential was not properly converted to an appointment. 
            Immediate follow-up is recommended to capture this opportunity.</p>
        </div>
        
        <table class="info-table">
            <tr>
                <th>Call File</th>
                <td>{audio_file}</td>
            </tr>
            <tr>
                <th>Date & Time</th>
                <td>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</td>
            </tr>
            <tr>
                <th>Representative</th>
                <td>{representative_name}</td>
            </tr>
            <tr>
                <th>Call Duration</th>
                <td>{call_duration:.1f} seconds</td>
            </tr>
            <tr>
                <th>Performance Score</th>
                <td>{performance_score:.3f} ({self._score_to_grade(performance_score)})</td>
            </tr>
        </table>
        
        <h3>ðŸ“‹ Call Summary</h3>
        <div class="transcript-box">
            <p>{call_summary}</p>
        </div>
        
        <h3>ðŸ“ž Call Transcript</h3>
        <div class="transcript-box">
            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{display_transcript}</pre>
        </div>
        
        <div class="action-required">
            <h3>ðŸŽ¯ Recommended Actions</h3>
            <ul>
                <li><strong>Immediate Follow-up:</strong> Contact the patient within 24 hours</li>
                <li><strong>Staff Coaching:</strong> Review call with {representative_name} for improvement</li>
                <li><strong>Process Review:</strong> Analyze why this opportunity was missed</li>
                <li><strong>Revenue Recovery:</strong> Attempt to convert this inquiry to an appointment</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p>This alert was automatically generated by the {settings.CLINIC_NAME} Call Analysis System</p>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
</body>
</html>
"""
        return html_content
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.97: return "A+"
        elif score >= 0.93: return "A"
        elif score >= 0.90: return "A-"
        elif score >= 0.87: return "B+"
        elif score >= 0.83: return "B"
        elif score >= 0.80: return "B-"
        elif score >= 0.77: return "C+"
        elif score >= 0.73: return "C"
        elif score >= 0.70: return "C-"
        elif score >= 0.67: return "D+"
        elif score >= 0.63: return "D"
        elif score >= 0.60: return "D-"
        else: return "F"
    
    async def _send_email(self, subject: str, html_content: str) -> bool:
        """Send the email"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return False
    
    async def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        
        if not self.is_configured():
            logger.error("Email not properly configured for testing")
            return False
            
        try:
            subject = "Test - Dental Call Analysis System"
            html_content = f"""
            <html>
            <body>
                <h2>Test Email - Dental Call Analysis System</h2>
                <p>This is a test email to verify your email configuration.</p>
                <p><strong>Clinic:</strong> {self.clinic_name}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>If you receive this email, your alert system is working correctly!</p>
            </body>
            </html>
            """
            
            success = await self._send_email(subject, html_content)
            
            if success:
                logger.info("Test email sent successfully")
            else:
                logger.error("Test email failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Test email failed: {str(e)}")
            return False