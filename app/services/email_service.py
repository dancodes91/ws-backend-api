"""Email service - SendGrid, SMTP, or no-op."""
import logging
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def send_email(to: str | list[str], subject: str, body_html: str, body_text: str | None = None) -> bool:
    """Send email. Returns True if sent or skipped (no config), False on error."""
    if settings.email_api_key:
        return _send_sendgrid(to, subject, body_html, body_text)
    if settings.use_smtp and settings.smtp_host:
        return _send_smtp(to, subject, body_html, body_text)
    logger.warning("No email configured - skipping send to %s", to)
    return True


def _send_sendgrid(to: str | list[str], subject: str, body_html: str, body_text: str | None) -> bool:
    try:
        import httpx
        recipients = [to] if isinstance(to, str) else to
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.email_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": e} for e in recipients]}],
                "from": {"email": settings.email_from, "name": "Wallace DMS"},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body_text or body_html[:500]},
                    {"type": "text/html", "value": body_html},
                ],
            },
            timeout=10,
        )
        return resp.status_code in (200, 202)
    except Exception as e:
        logger.exception("SendGrid send failed: %s", e)
        return False


def _send_smtp(to: str | list[str], subject: str, body_html: str, body_text: str | None) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        recipients = [to] if isinstance(to, str) else to
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body_text or body_html, "plain"))
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, recipients, msg.as_string())
        return True
    except Exception as e:
        logger.exception("SMTP send failed: %s", e)
        return False


def send_download_link_email(dealer_email: str, dealer_name: str, links: list[dict]) -> bool:
    """Send email with secure download links to dealer."""
    items = "\n".join(
        f"<li><a href=\"{l['link']}\">{l['vendor']} - {l['filename']}</a> (expires {l['expires_at']})</li>"
        for l in links
    )
    html = f"""
    <html><body>
    <p>Hello {dealer_name},</p>
    <p>Your price file download links are ready:</p>
    <ul>{items}</ul>
    <p>Click each link to download. If you have the Wallace Updater installed, it will place the file automatically.</p>
    <p>Best regards,<br/>Wallace DMS</p>
    </body></html>
    """
    return send_email(dealer_email, "Your Price File Download Links", html)


def send_upload_notification_email(emails: list[str], vendor: str, dealer_name: str, filename: str) -> bool:
    """Notify Jack/Tom that a file was uploaded."""
    html = f"""
    <html><body>
    <p>A new price file was uploaded to the portal.</p>
    <ul>
    <li>Vendor: {vendor}</li>
    <li>Dealer: {dealer_name}</li>
    <li>File: {filename}</li>
    </ul>
    <p>Wallace Price File Portal</p>
    </body></html>
    """
    return send_email(emails, "Price File Uploaded", html)


def send_welcome_email(dealer_email: str, dealer_name: str, login_url: str) -> bool:
    html = f"""
    <html><body>
    <p>Hello {dealer_name},</p>
    <p>Your dealer portal account has been created. You can log in at:</p>
    <p><a href="{login_url}">{login_url}</a></p>
    <p>Best regards,<br/>Wallace DMS</p>
    </body></html>
    """
    return send_email(dealer_email, "Welcome to Wallace Dealer Portal", html)


def send_password_reset_email(email: str, reset_url: str) -> bool:
    html = f"""
    <html><body>
    <p>You requested a password reset. Click the link below:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>If you did not request this, ignore this email.</p>
    <p>Best regards,<br/>Wallace DMS</p>
    </body></html>
    """
    return send_email(email, "Password Reset - Wallace Dealer Portal", html)
