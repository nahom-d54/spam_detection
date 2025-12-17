"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# Auth Schemas
class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr
    # Limit password length to avoid hashing issues and DoS by huge inputs
    password: str = Field(min_length=8, max_length=256, description="8-256 characters")
    imap_password: str = Field(description="IMAP email password")


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


# Email Schemas
class EmailMetadata(BaseModel):
    """Email metadata for list view."""

    id: int
    from_address: str = Field(alias="from")
    to: str
    subject: str
    date: Optional[str]
    size: int
    is_read: bool
    is_flagged: bool
    has_attachments: bool

    class Config:
        populate_by_name = True


class EmailAttachment(BaseModel):
    """Email attachment information."""

    filename: str
    content_type: str
    size: int


class EmailDetail(BaseModel):
    """Complete email details."""

    id: int
    from_address: str = Field(alias="from")
    to: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: str
    date: Optional[str]
    body_html: str
    body_plain: str
    attachments: List[EmailAttachment]
    is_read: bool
    is_flagged: bool
    message_id: str
    in_reply_to: Optional[str] = None
    references: Optional[str] = None
    is_spam: Optional[bool] = None
    confidence: Optional[float] = None

    class Config:
        populate_by_name = True


class SendEmailRequest(BaseModel):
    """Request to send a new email."""

    to: List[EmailStr]
    subject: str
    body_html: Optional[str] = None
    body_plain: Optional[str] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None


class ReplyEmailRequest(BaseModel):
    """Request to reply to an email."""

    email_id: int
    body_html: Optional[str] = None
    body_plain: Optional[str] = None
    include_original: bool = True


class MoveEmailRequest(BaseModel):
    """Request to move an email."""

    dest_folder: str


class MarkReadRequest(BaseModel):
    """Request to mark email as read/unread."""

    is_read: bool


# Folder Schemas
class Folder(BaseModel):
    """Email folder information."""

    name: str
    flags: List[str]
    delimiter: str


# Monitoring Schemas
class EmailEvent(BaseModel):
    """SSE email event."""

    event_type: str  # "new_email", "spam_detected", "error"
    email_id: Optional[int] = None
    subject: Optional[str] = None
    from_address: Optional[str] = Field(None, alias="from")
    is_spam: Optional[bool] = None
    confidence: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


# Generic Schemas
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None


class SpamDetectionRequest(BaseModel):
    """Request schema for spam detection."""

    subject: str
    body_html: Optional[str] = None
    body_plain: Optional[str] = None


class SpamDetectionResponse(BaseModel):
    """Response schema for spam detection."""

    is_spam: bool
    confidence: float


class UserOut(BaseModel):
    """Public user details."""

    id: int
    email: EmailStr
    is_active: bool
    is_monitoring: bool
    last_sync_time: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserUpdate(BaseModel):
    """Fields allowed to be updated by the user."""

    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    """Change password request payload."""

    old_password: str = Field(min_length=8, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class ConfirmSpamRequest(BaseModel):
    """Confirm spam and move to spam folder."""

    confirmed: bool = Field(description="User confirms the email is spam")
    dest_folder: str = Field(default="Spam", description="Destination spam folder")


class UserStats(BaseModel):
    """User statistics and metrics."""

    total_emails: int = Field(description="Total emails in INBOX")
    unread_emails: int = Field(description="Number of unread emails")
    spam_detected: int = Field(
        description="Estimated spam emails based on recent scans"
    )
    folders_count: int = Field(description="Total number of email folders")
    is_monitoring: bool = Field(description="Whether monitoring is active")
    last_sync_time: Optional[datetime] = Field(description="Last email sync timestamp")
    account_age_days: int = Field(description="Days since account creation")
