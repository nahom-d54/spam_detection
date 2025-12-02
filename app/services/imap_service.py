"""IMAP service for email operations."""
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header
from typing import List, Dict, Optional, Any
from datetime import datetime
import email.utils
from app.core.config import get_settings

settings = get_settings()


class IMAPService:
    """Service for IMAP email operations."""
    
    def __init__(self, email_address: str, password: str):
        """
        Initialize IMAP service with user credentials.
        
        Args:
            email_address: User's email address
            password: User's decrypted IMAP password
        """
        self.email_address = email_address
        self.password = password
        self.client: Optional[IMAPClient] = None
    
    def connect(self) -> 'IMAPService':
        """Connect to IMAP server."""
        try:
            self.client = IMAPClient(
                settings.IMAP_HOST,
                port=settings.IMAP_PORT,
                ssl=settings.IMAP_USE_SSL
            )
            self.client.login(self.email_address, self.password)
            print(f"✓ Connected to IMAP server for {self.email_address}")
            return self
        except Exception as e:
            raise ConnectionError(f"Failed to connect to IMAP server: {e}")
    
    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.client:
            try:
                self.client.logout()
            except:
                pass
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def list_folders(self) -> List[Dict[str, Any]]:
        """
        List all mail folders.
        
        Returns:
            List of folder dictionaries with name and flags
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        folders = []
        for flags, delimiter, name in self.client.list_folders():
            folders.append({
                "name": name,
                "flags": [flag.decode() if isinstance(flag, bytes) else flag for flag in flags],
                "delimiter": delimiter
            })
        return folders
    
    def list_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        offset: int = 0,
        only_unread: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List emails in a folder with metadata.
        
        Args:
            folder: Folder name (default: INBOX)
            limit: Maximum number of emails to fetch
            offset: Number of emails to skip
            only_unread: Only fetch unread emails
            
        Returns:
            List of email metadata dictionaries
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        self.client.select_folder(folder, readonly=True)
        
        # Search criteria
        search_criteria = ['UNSEEN'] if only_unread else ['ALL']
        messages = self.client.search(search_criteria)
        
        # Apply pagination
        messages = list(messages)
        messages.reverse()  # Most recent first
        paginated_messages = messages[offset:offset + limit]
        
        if not paginated_messages:
            return []
        
        # Fetch email metadata
        fetch_data = self.client.fetch(paginated_messages, ['FLAGS', 'RFC822.SIZE', 'ENVELOPE', 'BODY.PEEK[HEADER]'])
        
        emails = []
        for msg_id, data in fetch_data.items():
            envelope = data[b'ENVELOPE']
            flags = data[b'FLAGS']
            
            # Parse email header for additional info
            header_data = data[b'BODY[HEADER]']
            msg = message_from_bytes(header_data)
            
            emails.append({
                "id": msg_id,
                "from": self._decode_address(envelope.from_[0]) if envelope.from_ else "",
                "to": self._decode_address(envelope.to[0]) if envelope.to else "",
                "subject": self._decode_header(envelope.subject),
                "date": envelope.date.isoformat() if envelope.date else None,
                "size": data[b'RFC822.SIZE'],
                "is_read": b'\\Seen' in flags,
                "is_flagged": b'\\Flagged' in flags,
                "has_attachments": self._has_attachments(msg)
            })
        
        return emails
    
    def get_email_detail(self, email_id: int, folder: str = "INBOX") -> Dict[str, Any]:
        """
        Get full email details including body and attachments.
        
        Args:
            email_id: Email message ID
            folder: Folder containing the email
            
        Returns:
            Complete email data dictionary
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        self.client.select_folder(folder, readonly=True)
        
        # Fetch complete email
        fetch_data = self.client.fetch([email_id], ['RFC822', 'FLAGS'])
        
        if email_id not in fetch_data:
            raise ValueError(f"Email {email_id} not found")
        
        data = fetch_data[email_id]
        msg = message_from_bytes(data[b'RFC822'])
        flags = data[b'FLAGS']
        
        # Extract email parts
        body_html = ""
        body_plain = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    # Handle attachment
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": self._decode_header(filename),
                            "content_type": content_type,
                            "size": len(part.get_payload(decode=True) or b"")
                        })
                elif content_type == "text/plain" and not body_plain:
                    body_plain = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == "text/html" and not body_html:
                    body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            # Single part message
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode('utf-8', errors='ignore')
                if content_type == "text/html":
                    body_html = decoded
                else:
                    body_plain = decoded
        
        return {
            "id": email_id,
            "from": msg.get('From', ''),
            "to": msg.get('To', ''),
            "cc": msg.get('Cc', ''),
            "bcc": msg.get('Bcc', ''),
            "subject": self._decode_header(msg.get('Subject', '')),
            "date": email.utils.parsedate_to_datetime(msg.get('Date', '')).isoformat() if msg.get('Date') else None,
            "body_html": body_html,
            "body_plain": body_plain,
            "attachments": attachments,
            "is_read": b'\\Seen' in flags,
            "is_flagged": b'\\Flagged' in flags,
            "message_id": msg.get('Message-ID', ''),
            "in_reply_to": msg.get('In-Reply-To', ''),
            "references": msg.get('References', '')
        }
    
    def mark_as_read(self, email_id: int, folder: str = "INBOX"):
        """Mark an email as read."""
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        self.client.select_folder(folder)
        self.client.add_flags([email_id], [b'\\Seen'])
    
    def mark_as_unread(self, email_id: int, folder: str = "INBOX"):
        """Mark an email as unread."""
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        self.client.select_folder(folder)
        self.client.remove_flags([email_id], [b'\\Seen'])
    
    def move_email(self, email_id: int, source_folder: str, dest_folder: str):
        """
        Move an email from one folder to another.
        
        Args:
            email_id: Email message ID
            source_folder: Source folder name
            dest_folder: Destination folder name
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        self.client.select_folder(source_folder)
        
        # Copy to destination
        self.client.copy([email_id], dest_folder)
        
        # Mark as deleted in source
        self.client.add_flags([email_id], [b'\\Deleted'])
        
        # Expunge to permanently delete
        self.client.expunge()
    
    def delete_email(self, email_id: int, folder: str = "INBOX"):
        """
        Delete an email (move to Trash or mark as deleted).
        
        Args:
            email_id: Email message ID
            folder: Folder containing the email
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        try:
            # Try to move to Trash folder
            self.move_email(email_id, folder, "Trash")
        except:
            # If Trash doesn't exist, just mark as deleted
            self.client.select_folder(folder)
            self.client.add_flags([email_id], [b'\\Deleted'])
            self.client.expunge()
    
    def search_emails(self, query: str, folder: str = "INBOX") -> List[int]:
        """
        Search for emails matching a query.
        
        Args:
            query: Search query (subject, from, etc.)
            folder: Folder to search in
            
        Returns:
            List of matching email IDs
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")
        
        self.client.select_folder(folder, readonly=True)
        
        # Search by subject or from
        messages = self.client.search(['OR', f'SUBJECT "{query}"', f'FROM "{query}"'])
        return list(messages)
    
    def get_unread_emails(self, folder: str = "INBOX") -> List[Dict[str, Any]]:
        """Get all unread emails from a folder."""
        return self.list_emails(folder=folder, only_unread=True, limit=100)
    
    @staticmethod
    def _decode_header(header: Any) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        if isinstance(header, bytes):
            header = header.decode('utf-8', errors='ignore')
        
        decoded_parts = decode_header(str(header))
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += str(part)
        
        return decoded_string
    
    @staticmethod
    def _decode_address(address_tuple) -> str:
        """Decode email address from IMAP envelope."""
        if not address_tuple:
            return ""
        
        name, email_local, email_domain = address_tuple.name, address_tuple.mailbox, address_tuple.host
        
        if name:
            decoded_name = IMAPService._decode_header(name)
            return f"{decoded_name} <{email_local.decode()}@{email_domain.decode()}>"
        else:
            return f"{email_local.decode()}@{email_domain.decode()}"
    
    @staticmethod
    def _has_attachments(msg) -> bool:
        """Check if email has attachments."""
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                return True
        return False
