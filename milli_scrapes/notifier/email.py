"""
Asynchronous SMTP/TLS Email Notifier.
Dispatches real-time alerts when monitored websites change or seats become available.
Attaches in-memory JPEG snapshots directly from transient RAM (0 bytes secondary storage).
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Optional, List, Dict, Any


class EmailNotifier:
    """
    Email notification dispatcher supporting Gmail, SMTP relays, and dry-run testing.
    """

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_email: str = "analystx.raju@gmail.com",
        dry_run: bool = False
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email
        self.dry_run = dry_run or not (sender_email and sender_password)

    def send_alert(
        self,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        snapshot_jpeg: Optional[bytes] = None,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an alert email with optional in-memory JPEG snapshot attachment.
        """
        target_to = recipient or self.recipient_email

        if self.dry_run:
            print(f"[EmailNotifier DRY-RUN] Alert generated for <{target_to}>: '{subject}'")
            if snapshot_jpeg:
                print(f"  ↳ Attached in-memory visual snapshot: {len(snapshot_jpeg)} bytes (0 bytes saved to disk).")
            return {
                "status": "simulated",
                "recipient": target_to,
                "subject": subject,
                "attachment_bytes": len(snapshot_jpeg) if snapshot_jpeg else 0
            }

        # Compose multipart message
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = target_to

        # Body alternative
        msg_alt = MIMEMultipart("alternative")
        msg.attach(msg_alt)

        part_text = MIMEText(body_text, "plain")
        msg_alt.attach(part_text)

        if body_html:
            part_html = MIMEText(body_html, "html")
            msg_alt.attach(part_html)

        # Attach JPEG snapshot from RAM
        if snapshot_jpeg:
            img_part = MIMEImage(snapshot_jpeg, name="live_snapshot.jpg")
            img_part.add_header("Content-ID", "<live_snapshot>")
            msg.attach(img_part)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, target_to, msg.as_string())

            return {
                "status": "sent",
                "recipient": target_to,
                "subject": subject,
                "attachment_bytes": len(snapshot_jpeg) if snapshot_jpeg else 0
            }
        except Exception as e:
            return {
                "status": "error",
                "recipient": target_to,
                "error": str(e)
            }
