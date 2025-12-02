"""SMTP service for sending emails."""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()


class SMTPService:
    """Service for sending emails via SMTP."""
    
    def __init__(self, email_address: str, password: str):
        """
        Initialize SMTP service with user credentials.
        
        Args:
            email_address: User's email address
            password: User's decrypted SMTP password
        """
        self.email_address = email_address
        self.password = password
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body_html: Optional[str] = None,
        body_plain: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body_html: HTML body content
            body_plain: Plain text body content
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment dicts with 'filename' and 'content' keys
            in_reply_to: Message-ID of email being replied to (for threading)
            references: References header for email threading
            
        Returns:
            True if sent successfully
        """
        # Create message
        if body_html and body_plain:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body_plain, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
        elif body_html:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body_html, 'html'))
        elif body_plain:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body_plain, 'plain'))
        else:
            raise ValueError("Either body_html or body_plain must be provided")
        
        # Set headers
        msg['From'] = self.email_address
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject
        
        if cc:
            msg['Cc'] = ', '.join(cc)
        
        if in_reply_to:
            msg['In-Reply-To'] = in_reply_to
        
        if references:
            msg['References'] = references
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                self._add_attachment(msg, attachment)
        
        # Prepare recipient list
        recipients = to.copy()
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)
        
        # Send email
        try:
            if settings.SMTP_USE_TLS:
                await aiosmtplib.send(
                    msg,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=self.email_address,
                    password=self.password,
                    start_tls=True
                )
            else:
                await aiosmtplib.send(
                    msg,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=self.email_address,
                    password=self.password,
                    use_tls=True
                )
            
            print(f"✓ Email sent successfully to {', '.join(to)}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            raise RuntimeError(f"Failed to send email: {e}")
    
    async def reply_to_email(
        self,
        original_email: Dict[str, Any],
        body_html: Optional[str] = None,
        body_plain: Optional[str] = None,
        include_original: bool = True
    ) -> bool:
        """
        Reply to an email.
        
        Args:
            original_email: Original email data dict (from get_email_detail)
            body_html: HTML reply body
            body_plain: Plain text reply body
            include_original: Whether to include original message in reply
            
        Returns:
            True if sent successfully
        """
        # Extract original email info
        original_from = original_email.get('from', '')
        original_subject = original_email.get('subject', '')
        original_message_id = original_email.get('message_id', '')
        original_references = original_email.get('references', '')
        
        # Prepare reply subject
        reply_subject = original_subject if original_subject.startswith('Re:') else f"Re: {original_subject}"
        
        # Include original message if requested
        if include_original:
            original_body_html = original_email.get('body_html', '')
            original_body_plain = original_email.get('body_plain', '')
            original_date = original_email.get('date', '')
            
            if body_html and original_body_html:
                body_html = f"{body_html}<br><br>---<br>On {original_date}, {original_from} wrote:<br>{original_body_html}"
            
            if body_plain and original_body_plain:
                body_plain = f"{body_plain}\n\n---\nOn {original_date}, {original_from} wrote:\n{original_body_plain}"
        
        # Build References header for threading
        references = original_references
        if original_message_id:
            if references:
                references = f"{references} {original_message_id}"
            else:
                references = original_message_id
        
        # Extract recipient (parse "Name <email@domain.com>" format)
        import re
        email_match = re.search(r'<(.+?)>', original_from)
        reply_to = email_match.group(1) if email_match else original_from
        
        # Send reply
        return await self.send_email(
            to=[reply_to],
            subject=reply_subject,
            body_html=body_html,
            body_plain=body_plain,
            in_reply_to=original_message_id,
            references=references
        )
    
    @staticmethod
    def _add_attachment(msg: MIMEMultipart, attachment: Dict[str, Any]):
        """
        Add an attachment to the email message.
        
        Args:
            msg: MIME multipart message
            attachment: Dict with 'filename' and 'content' (bytes) keys
        """
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment['content'])
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f"attachment; filename= {attachment['filename']}"
        )
        msg.attach(part)
