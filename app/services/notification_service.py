import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.models.emergency_contact import EmergencyContact
from app.models.user import User

settings = get_settings()


class NotificationService:

    def _send_email(self, to_email: str, subject: str, html_body: str) -> None:
        """Low-level SMTP send. Raises on failure."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()

            # ✅ Use STARTTLS only if configured (MailHog doesn't need it)
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()

            # ✅ Only login if credentials are provided (MailHog has no auth)
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)

            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def send_verification_email(self, user: User, raw_token: str) -> None:
        verify_url = (
            f"{settings.frontend_base_url}/api/v1/auth/verify-email?token={raw_token}"
        )
        subject = "Confirm your Wasaya account"
        body = _render_verify_email(user.full_name or user.email, verify_url)
        self._send_email(user.email, subject, body)

    def send_checkin_email(self, user: User, raw_token: str) -> None:
        confirm_url = (
            f"{settings.frontend_base_url}/api/v1/checkin/confirm?token={raw_token}"
        )
        subject = "Your Wasaya check-in"
        body = _render_checkin_email(user.full_name or user.email, confirm_url)
        self._send_email(user.email, subject, body)

    def send_alert_email(self, user: User, contact: EmergencyContact) -> None:
        if not contact.email:
            return
        subject = f"A note about {user.full_name or user.email}"
        body = _render_alert_email(
            contact_name=contact.name,
            user_name=user.full_name or user.email,
        )
        self._send_email(contact.email, subject, body)


# ------------------------------------------------------------------
# HTML email templates
# ------------------------------------------------------------------

_BASE_STYLE = """
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f9f9f9;
  color: #222;
  max-width: 540px;
  margin: 40px auto;
  background: #fff;
  border-radius: 10px;
  padding: 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
"""

_BUTTON_STYLE = """
  display: inline-block;
  background: #4f6ef7;
  color: #fff !important;
  text-decoration: none;
  padding: 14px 28px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 24px;
"""

_FOOTER = """
  <p style="margin-top:40px; font-size:13px; color:#999;">
    You're receiving this because you have a Wasaya account.
    If this wasn't you, you can safely ignore this message.
  </p>
"""


def _render_verify_email(name: str, verify_url: str) -> str:
    return f"""
    <div style="{_BASE_STYLE}">
      <h2 style="margin-top:0; color:#4f6ef7;">Welcome to Wasaya 👋</h2>
      <p>Hi {name},</p>
      <p>
        Thanks for creating your account. Before we get started,
        please confirm your email address by clicking the button below.
      </p>
      <a href="{verify_url}" style="{_BUTTON_STYLE}">Confirm my email</a>
      <p style="margin-top:24px; font-size:14px; color:#666;">
        This link expires in 24 hours.
      </p>
      {_FOOTER}
    </div>
    """


def _render_checkin_email(name: str, confirm_url: str) -> str:
    return f"""
    <div style="{_BASE_STYLE}">
      <h2 style="margin-top:0; color:#4f6ef7;">A quick check-in 👋</h2>
      <p>Hi {name},</p>
      <p>
        This is your regular Wasaya check-in. Just let us know you're doing well
        by clicking the button below — it only takes a second.
      </p>
      <a href="{confirm_url}" style="{_BUTTON_STYLE}">I'm doing well ✓</a>
      <p style="margin-top:24px; font-size:14px; color:#666;">
        If you don't respond, your emergency contact may be notified.
      </p>
      {_FOOTER}
    </div>
    """


def _render_alert_email(contact_name: str, user_name: str) -> str:
    return f"""
    <div style="{_BASE_STYLE}">
      <h2 style="margin-top:0; color:#e07b54;">A note about {user_name}</h2>
      <p>Hi {contact_name},</p>
      <p>
        You're listed as an emergency contact for <strong>{user_name}</strong>
        on Wasaya, a safety check-in service.
      </p>
      <p>
        {user_name} has not responded to their recent check-in.
        This could be nothing — perhaps they were just busy or missed the message.
        It might be worth reaching out to make sure everything is okay.
      </p>
      <p style="margin-top:24px; font-size:14px; color:#666;">
        This is an automated message. No action is required unless you're concerned.
      </p>
      {_FOOTER}
    </div>
    """