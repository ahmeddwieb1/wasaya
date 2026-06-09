from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.core.security import settings
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/test", tags=["test"])

class TestEmailRequest(BaseModel):
    email: str
    subject: str = "Test Email from Wasaya"
    message: str = "This is a test email from your FastAPI application."

@router.post("/email")
async def test_email(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        notification_service = NotificationService()

        # Force the from email to match your Brevo account
        # Modify the message to use correct from address
        msg = MIMEMultipart("alternative")
        msg["Subject"] = request.subject
        msg["From"] = "ahmeddwieb713@gmail.com"  # Force this
        msg["To"] = request.email
        msg.attach(MIMEText(request.message, "plain"))

        # Send manually
        import smtplib
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail("ahmeddwieb713@gmail.com", request.email, msg.as_string())

        return {"success": True, "message": f"Email sent to {request.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")