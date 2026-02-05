import asyncio
import json
import smtplib
from email.message import EmailMessage
from typing import Optional

import httpx
from loguru import logger

from app.core.config import get_settings
from app.models.alarm import Alarm
from app.models.sensor import Sensor

settings = get_settings()

_email_ready: bool = False
_email_last_error: Optional[str] = None


def email_configured() -> bool:
    """Check whether SMTP settings are present."""
    return bool(settings.email_smtp_host and settings.email_smtp_user and settings.email_smtp_pass)


def email_status() -> tuple[bool, Optional[str]]:
    """Return last known email transport status."""
    return _email_ready, _email_last_error


async def verify_email_transport() -> None:
    """
    Perform a lightweight SMTP connectivity check and cache the result.
    This is used by the /notifications/test-email endpoint.
    """
    global _email_ready, _email_last_error

    if not email_configured():
        _email_ready = False
        _email_last_error = "SMTP credentials not configured"
        return

    try:
        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.email_smtp_user, settings.email_smtp_pass)
        _email_ready = True
        _email_last_error = None
        logger.info("SMTP transport verified successfully")
    except Exception as exc:
        _email_ready = False
        _email_last_error = str(exc)
        logger.warning("SMTP transport verification failed: {}", exc)


async def _send_email(subject: str, body: str, to_override: Optional[str] = None) -> None:
    """Send email with improved error handling"""
    if not email_configured():
        logger.warning("Email not configured, skipping email send")
        raise ValueError("Email SMTP credentials not configured")
    
    message = EmailMessage()
    message["From"] = settings.email_smtp_user
    message["To"] = to_override or settings.notification_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.email_smtp_user, settings.email_smtp_pass)
            server.send_message(message)
            logger.info("Email notification sent successfully")
    except smtplib.SMTPAuthenticationError as exc:
        error_msg = str(exc)
        # Provide helpful error message for Gmail authentication issues
        if "BadCredentials" in error_msg or "535" in error_msg:
            detailed_error = (
                "Gmail authentication failed. This usually means:\n"
                "1. The password is incorrect, OR\n"
                "2. You need to use an App Password instead of your regular password\n"
                "3. 2-Step Verification must be enabled on your Google account\n\n"
                "To fix: Go to https://myaccount.google.com/apppasswords and generate an App Password, "
                "then use that password in your SMTP configuration."
            )
            logger.error(f"SMTP Authentication Error: {detailed_error}")
            raise ValueError(detailed_error) from exc
        else:
            logger.error(f"SMTP Authentication Error: {error_msg}")
            raise ValueError(f"SMTP authentication failed: {error_msg}") from exc
    except smtplib.SMTPException as exc:
        error_msg = f"SMTP error: {str(exc)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from exc
    except Exception as exc:
        error_msg = f"Email send failed: {str(exc)}"
        logger.warning(error_msg)
        raise ValueError(error_msg) from exc


async def _send_slack(body: dict) -> None:
    if not settings.slack_webhook_url:
        logger.info("Slack webhook not configured, skipping notification")
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(settings.slack_webhook_url, json=body)


async def send_password_reset_email(email: str, reset_link: str) -> None:
    """Send password reset email"""
    subject = "Password Reset Request"
    body = f"""
    You have requested to reset your password.
    
    Click the following link to reset your password:
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you did not request this, please ignore this email.
    """
    await _send_email(subject, body, to_override=email)


async def send_test_email(to_override: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Send a simple test email either to the provided address or to
    settings.notification_email.
    Returns (success: bool, error_message: str | None)
    """
    if not email_configured():
        return False, "Email SMTP credentials are not configured. Please configure SMTP settings in backend/.env"
    
    subject = "Predictive Maintenance – Test Email"
    body = "This is a test email from the Predictive Maintenance Platform."
    try:
        await _send_email(subject, body, to_override=to_override)
        return True, None
    except ValueError as exc:
        # ValueError contains user-friendly error message
        return False, str(exc)
    except Exception as exc:  # pragma: no cover - defensive
        error_msg = str(exc)
        # Extract meaningful error from exception
        if "535" in error_msg or "BadCredentials" in error_msg:
            return False, (
                "Gmail authentication failed. Please:\n"
                "1. Enable 2-Step Verification on your Google account\n"
                "2. Generate an App Password at https://myaccount.google.com/apppasswords\n"
                "3. Use the App Password (not your regular password) in SMTP configuration"
            )
        logger.warning("Test email failed: {}", exc)
        return False, f"Failed to send email: {error_msg}"


async def send_welcome_email(email: str, full_name: str) -> None:
    """Send welcome email to newly registered user"""
    if not email_configured():
        logger.warning("Email not configured, skipping welcome email")
        return
    
    subject = "Welcome to Predictive Maintenance Platform"
    body = f"""
    Hello {full_name},
    
    Welcome to the Predictive Maintenance Platform!
    
    Your account has been successfully created. You can now:
    - Monitor machine health and sensor data in real-time
    - View AI-powered predictions and anomaly detection
    - Generate reports and manage alarms
    - Access the dashboard at: http://localhost:3000
    
    If you have any questions, please contact your administrator.
    
    Best regards,
    Predictive Maintenance Platform Team
    """
    try:
        await _send_email(subject, body, to_override=email)
        logger.info(f"Welcome email sent to {email}")
    except Exception as exc:
        logger.warning(f"Failed to send welcome email to {email}: {exc}")


async def send_prediction_alert_email(machine_id: str, sensor_id: str, prediction_status: str, score: float, confidence: float) -> None:
    """Send email notification for critical/warning predictions to tanirajsingh574@gmail.com"""
    if not email_configured():
        logger.warning("Email not configured, skipping prediction alert")
        return
    
    severity = "CRITICAL" if prediction_status in ["critical", "anomaly"] or score > 0.8 else "WARNING"
    subject = f"[PM Alert] {severity} Prediction Detected - Machine {machine_id}"
    body = f"""
    Predictive Maintenance Alert
    
    A {prediction_status.upper()} prediction has been detected:
    
    - Machine ID: {machine_id}
    - Sensor ID: {sensor_id}
    - Prediction Status: {prediction_status}
    - Anomaly Score: {score:.2f}
    - Confidence: {confidence:.2f}
    
    Please review the dashboard and take appropriate action.
    
    Dashboard: http://localhost:3000
    
    This is an automated notification from the Predictive Maintenance Platform.
    """
    try:
        # Send to specific email address
        await _send_email(subject, body, to_override="tanirajsingh574@gmail.com")
        logger.info(f"Prediction alert email sent to tanirajsingh574@gmail.com for machine {machine_id}")
    except Exception as exc:
        logger.warning(f"Failed to send prediction alert email: {exc}")


def enqueue_alarm_notification(alarm: Alarm, sensor: Optional[Sensor]) -> None:
    subject = f"[PM] {alarm.severity.upper()} alarm on {sensor.name if sensor else alarm.machine_id}"
    body = json.dumps(
        {
            "machine_id": str(alarm.machine_id),
            "sensor": sensor.name if sensor else None,
            "status": alarm.status,
            "message": alarm.message,
        },
        indent=2,
    )
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    loop.create_task(_send_email(subject, body))
    loop.create_task(
        _send_slack(
            {
                "text": subject,
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Alarm:* {alarm.message}"}},
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"*Severity:* {alarm.severity}"},
                            {"type": "mrkdwn", "text": f"*Machine:* {alarm.machine_id}"},
                        ],
                    },
                ],
            }
        )
    )

