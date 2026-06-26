import smtplib
import ssl
import httpx
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

class NotificationService:
    """
    Handles sending alerts via various channels: email, webhooks, etc.
    """
    
    def __init__(self):
        self.email_config = {
            'enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('SENDER_EMAIL', ''),
            'sender_password': os.getenv('SENDER_PASSWORD', ''),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
        
        self.webhook_config = {
            'enabled': os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true',
            'timeout': int(os.getenv('WEBHOOK_TIMEOUT', '10'))
        }
        
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def send_alert(self, alert_data: Dict, recipients: List[str] = None, channels: List[str] = None):
        """
        Send alert through specified channels.
        
        Args:
            alert_data: Dictionary containing alert details (title, message, severity, etc.)
            recipients: List of email addresses for notifications
            channels: List of channels to use ['email', 'webhook']
        """
        if channels is None:
            channels = []
            if self.email_config['enabled']:
                channels.append('email')
            if self.webhook_config['enabled']:
                channels.append('webhook')
        
        # Send notifications asynchronously
        for channel in channels:
            if channel == 'email' and recipients:
                self.executor.submit(self._send_email_alert, alert_data, recipients)
            elif channel == 'webhook':
                self.executor.submit(self._send_webhook_alert, alert_data)
    
    def _send_email_alert(self, alert_data: Dict, recipients: List[str]):
        """Send email alert asynchronously."""
        try:
            if not self.email_config['enabled'] or not self.email_config['sender_email']:
                return
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[PPE Alert] {alert_data.get('severity', 'INFO').upper()}: {alert_data['title']}"
            message["From"] = self.email_config['sender_email']
            message["To"] = ", ".join(recipients)
            
            # Create HTML content
            html_content = self._create_email_html(alert_data)
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                if self.email_config['use_tls']:
                    server.starttls(context=context)
                
                if self.email_config['sender_password']:
                    server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                
                server.sendmail(self.email_config['sender_email'], recipients, message.as_string())
            
            print(f"Email alert sent successfully to {len(recipients)} recipients")
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, alert_data: Dict):
        """Send webhook alert asynchronously."""
        try:
            webhook_url = os.getenv('WEBHOOK_URL', '')
            if not webhook_url or not self.webhook_config['enabled']:
                return
            
            # Prepare webhook payload
            payload = {
                'timestamp': datetime.utcnow().isoformat(),
                'alert': alert_data,
                'source': 'ppe_detection_system',
                'environment': os.getenv('ENVIRONMENT', 'production')
            }
            
            # Send webhook
            with httpx.Client(timeout=self.webhook_config['timeout']) as client:
                response = client.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
            
            print(f"Webhook alert sent successfully to {webhook_url}")
            
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
    
    def _create_email_html(self, alert_data: Dict) -> str:
        """Create HTML content for email alert."""
        severity_colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'critical': '#c0392b'
        }
        
        color = severity_colors.get(alert_data.get('severity', 'info'), '#3498db')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .alert-details {{ background-color: white; padding: 15px; margin-top: 15px; border-left: 4px solid {color}; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .timestamp {{ color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PPE Detection Alert</h1>
                </div>
                <div class="content">
                    <h2>{alert_data['title']}</h2>
                    <p class="timestamp">Time: {alert_data.get('time', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                    
                    <div class="alert-details">
                        <h3>Alert Details</h3>
                        <p><strong>Severity:</strong> {alert_data.get('severity', 'info').upper()}</p>
                        <p><strong>Type:</strong> {alert_data.get('type', 'Unknown')}</p>
                        <p><strong>Message:</strong> {alert_data['message']}</p>
                        
                        {f"<p><strong>Video Source:</strong> {alert_data.get('video_source')}</p>" if alert_data.get('video_source') else ""}
                        {f"<p><strong>Class:</strong> {alert_data.get('class_name')}</p>" if alert_data.get('class_name') else ""}
                        {f"<p><strong>Confidence:</strong> {alert_data.get('confidence', 0):.1f}%</p>" if alert_data.get('confidence') else ""}
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated alert from the PPE Detection System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def send_daily_summary(self, stats_data: Dict, recipients: List[str]):
        """Send daily summary report via email."""
        try:
            if not recipients or not self.email_config['enabled']:
                return
            
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[PPE Daily Summary] {datetime.utcnow().strftime('%Y-%m-%d')}"
            message["From"] = self.email_config['sender_email']
            message["To"] = ", ".join(recipients)
            
            html_content = self._create_summary_html(stats_data)
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                if self.email_config['use_tls']:
                    server.starttls(context=context)
                
                if self.email_config['sender_password']:
                    server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                
                server.sendmail(self.email_config['sender_email'], recipients, message.as_string())
            
            print(f"Daily summary sent to {len(recipients)} recipients")
            
        except Exception as e:
            print(f"Failed to send daily summary: {e}")
    
    def _create_summary_html(self, stats_data: Dict) -> str:
        """Create HTML content for daily summary report."""
        compliance_rate = stats_data.get('compliance_rate', 0)
        
        # Determine compliance level color
        if compliance_rate >= 90:
            level_color = '#27ae60'  # Green
            level_text = 'Excellent'
        elif compliance_rate >= 75:
            level_color = '#f39c12'  # Orange
            level_text = 'Good'
        elif compliance_rate >= 50:
            level_color = '#e67e22'  # Dark Orange
            level_text = 'Fair'
        else:
            level_color = '#e74c3c'  # Red
            level_text = 'Poor'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ color: #7f8c8d; font-size: 14px; }}
                .compliance-rate {{ text-align: center; padding: 20px; background: white; border-radius: 8px; margin: 20px 0; }}
                .compliance-value {{ font-size: 48px; font-weight: bold; color: {level_color}; }}
                .compliance-level {{ font-size: 18px; color: {level_color}; margin-top: 10px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PPE Detection Daily Summary</h1>
                    <p>{datetime.utcnow().strftime('%Y-%m-%d')}</p>
                </div>
                <div class="content">
                    <div class="compliance-rate">
                        <div class="compliance-value">{compliance_rate:.1f}%</div>
                        <div class="compliance-level">Compliance Rate - {level_text}</div>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{stats_data.get('total', 0)}</div>
                            <div class="stat-label">Total Detections</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #27ae60;">{stats_data.get('compliance', 0)}</div>
                            <div class="stat-label">Compliance</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #e74c3c;">{stats_data.get('violations', 0)}</div>
                            <div class="stat-label">Violations</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #3498db;">{stats_data.get('other', 0)}</div>
                            <div class="stat-label">Other</div>
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <h3>Top Violation Types</h3>
                        <ul>
            """
        
        # Add top violations if available
        class_counts = stats_data.get('class_counts', {})
        violations = {k: v for k, v in class_counts.items() if 'NO-' in k}
        sorted_violations = sorted(violations.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for violation_type, count in sorted_violations:
            html += f"<li><strong>{violation_type}:</strong> {count} occurrences</li>"
        
        if not sorted_violations:
            html += "<li>No violations recorded today!</li>"
        
        html += """
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated daily summary from the PPE Detection System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def shutdown(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=False)


# Global notification service instance
notification_service = NotificationService()