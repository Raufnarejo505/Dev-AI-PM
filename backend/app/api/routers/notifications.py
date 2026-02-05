from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_engineer
from app.models.user import User
from app.services import notification_service, webhook_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TestEmailRequest(BaseModel):
    to: EmailStr | None = None


@router.post("/test-email")
async def trigger_test_email(payload: TestEmailRequest | None = None):
    """Test email sending with improved error messages"""
    if not notification_service.email_configured():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "ok": False, 
                "error": "Email SMTP credentials are not configured. Please configure SMTP settings in backend/.env file."
            },
        )

    # Try to verify email transport first (non-blocking)
    email_ready, last_error = notification_service.email_status()
    if not email_ready:
        try:
            await notification_service.verify_email_transport()
            email_ready, last_error = notification_service.email_status()
        except Exception as e:
            logger.warning(f"Email transport verification failed: {e}")

    # Attempt to send test email (this will provide better error messages)
    ok, error = await notification_service.send_test_email(payload.to if payload else None)
    
    if ok:
        return {"ok": True, "message": "Test email sent successfully"}
    
    # Return user-friendly error message
    error_message = error or "Unable to send email"
    
    # Provide helpful guidance for common Gmail errors
    if "535" in error_message or "BadCredentials" in error_message or "authentication" in error_message.lower():
        error_message = (
            "Gmail authentication failed. To fix this:\n\n"
            "1. Enable 2-Step Verification on your Google account\n"
            "2. Go to https://myaccount.google.com/apppasswords\n"
            "3. Generate a new App Password for 'Mail'\n"
            "4. Use the generated App Password (16 characters) in your SMTP configuration\n"
            "5. Update backend/.env with: EMAIL_SMTP_PASS=your_app_password\n\n"
            "Note: You cannot use your regular Gmail password for SMTP."
        )
    
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"ok": False, "error": error_message},
    )


class TestWebhookRequest(BaseModel):
    url: str
    event_type: str = "test.event"


@router.post("/test-webhook")
async def trigger_test_webhook(
    payload: TestWebhookRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Test a webhook URL with a test event"""
    from app.models.webhook import Webhook
    from app.schemas.webhook import WebhookCreate
    
    # Create a temporary webhook for testing
    test_webhook = Webhook(
        name="test_webhook",
        url=payload.url,
        events=[payload.event_type],
        is_active=True,
    )
    
    success = await webhook_service.trigger_webhook(
        test_webhook,
        payload.event_type,
        {
            "test": True,
            "message": "This is a test webhook event",
            "timestamp": "2025-11-25T12:00:00Z",
        }
    )
    
    if success:
        return {"ok": True, "message": "Webhook triggered successfully"}
    else:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"ok": False, "error": "Webhook request failed"},
        )

