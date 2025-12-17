"""Email management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import decrypt_password
from app.database import get_db
from app.models.user import User
from app.schemas import (
    ConfirmSpamRequest,
    EmailDetail,
    EmailMetadata,
    Folder,
    MarkReadRequest,
    MessageResponse,
    MoveEmailRequest,
    ReplyEmailRequest,
    SendEmailRequest,
    SpamDetectionRequest,
    SpamDetectionResponse,
)
from app.services.imap_service import IMAPService
from app.services.smtp_service import SMTPService
from app.services.spam_classifier import get_spam_classifier

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("", response_model=List[EmailMetadata])
async def list_emails(
    folder: str = Query(default="INBOX", description="Folder name"),
    limit: int = Query(default=50, le=100, description="Maximum emails to fetch"),
    offset: int = Query(default=0, ge=0, description="Number of emails to skip"),
    only_unread: bool = Query(default=False, description="Only fetch unread emails"),
    current_user: User = Depends(get_current_user),
):
    """
    List emails in a folder with pagination.
    """
    try:
        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and fetch emails
        with IMAPService(current_user.email, imap_password) as imap:
            emails = imap.list_emails(
                folder=folder, limit=limit, offset=offset, only_unread=only_unread
            )

        return emails

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}",
        )


@router.get("/{email_id}", response_model=EmailDetail)
async def get_email(
    email_id: int,
    folder: str = Query(default="INBOX", description="Folder containing the email"),
    current_user: User = Depends(get_current_user),
):
    """
    Get full email details including body and attachments.
    """
    try:
        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and fetch email detail
        with IMAPService(current_user.email, imap_password) as imap:
            email = imap.get_email_detail(email_id, folder=folder)

        # Run spam detection
        email_text = f"{email['subject']} {email.get('body_plain', '')}"
        _classifier_instance = get_spam_classifier()
        is_spam, confidence = _classifier_instance.predict_with_confidence(email_text)

        # Add spam detection results to the email object
        email["is_spam"] = is_spam
        email["confidence"] = confidence

        return email

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch email: {str(e)}",
        )


@router.put("/{email_id}/read", response_model=MessageResponse)
async def mark_email_read(
    email_id: int,
    request: MarkReadRequest,
    folder: str = Query(default="INBOX", description="Folder containing the email"),
    current_user: User = Depends(get_current_user),
):
    """
    Mark an email as read or unread.
    """
    try:
        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and mark email
        with IMAPService(current_user.email, imap_password) as imap:
            if request.is_read:
                imap.mark_as_read(email_id, folder=folder)
            else:
                imap.mark_as_unread(email_id, folder=folder)

        status_text = "read" if request.is_read else "unread"
        return MessageResponse(message=f"Email marked as {status_text}", success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email: {str(e)}",
        )


@router.post("/{email_id}/move", response_model=MessageResponse)
async def move_email(
    email_id: int,
    request: MoveEmailRequest,
    source_folder: str = Query(default="INBOX", description="Source folder"),
    current_user: User = Depends(get_current_user),
):
    """
    Move an email to another folder.
    """
    try:
        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and move email
        with IMAPService(current_user.email, imap_password) as imap:
            imap.move_email(email_id, source_folder, request.dest_folder)

        return MessageResponse(
            message=f"Email moved to {request.dest_folder}", success=True
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move email: {str(e)}",
        )


@router.delete("/{email_id}", response_model=MessageResponse)
async def delete_email(
    email_id: int,
    folder: str = Query(default="INBOX", description="Folder containing the email"),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an email (move to Trash).
    """
    try:
        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and delete email
        with IMAPService(current_user.email, imap_password) as imap:
            imap.delete_email(email_id, folder=folder)

        return MessageResponse(message="Email deleted successfully", success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email: {str(e)}",
        )


@router.post("/send", response_model=MessageResponse)
async def send_email(
    request: SendEmailRequest, current_user: User = Depends(get_current_user)
):
    """
    Send a new email.
    """
    try:
        # Decrypt IMAP password (same as SMTP password)
        smtp_password = decrypt_password(current_user.encrypted_imap_password)

        # Send email via SMTP
        smtp = SMTPService(current_user.email, smtp_password)
        await smtp.send_email(
            to=request.to,
            subject=request.subject,
            body_html=request.body_html,
            body_plain=request.body_plain,
            cc=request.cc,
            bcc=request.bcc,
        )

        return MessageResponse(message="Email sent successfully", success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.post("/{email_id}/reply", response_model=MessageResponse)
async def reply_to_email(
    email_id: int,
    request: ReplyEmailRequest,
    folder: str = Query(default="INBOX", description="Folder containing the email"),
    current_user: User = Depends(get_current_user),
):
    """
    Reply to an email.
    """
    try:
        # Decrypt passwords
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Get original email details
        with IMAPService(current_user.email, imap_password) as imap:
            original_email = imap.get_email_detail(email_id, folder=folder)

        # Send reply via SMTP
        smtp = SMTPService(current_user.email, imap_password)
        await smtp.reply_to_email(
            original_email=original_email,
            body_html=request.body_html,
            body_plain=request.body_plain,
            include_original=request.include_original,
        )

        return MessageResponse(message="Reply sent successfully", success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reply: {str(e)}",
        )


@router.get("/folders/list", response_model=List[Folder])
async def list_folders(current_user: User = Depends(get_current_user)):
    """
    List all email folders.
    """
    try:
        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and list folders
        with IMAPService(current_user.email, imap_password) as imap:
            folders = imap.list_folders()

        return folders

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch folders: {str(e)}",
        )


@router.post("/email/detect_spam", response_model=SpamDetectionResponse)
async def detect_spam(payload: SpamDetectionRequest):
    """
    Detect if an email is spam based on its content.
    """
    try:
        from app.services.spam_classifier import get_spam_classifier

        # Combine subject and body for classification
        email_text = (
            f"{payload.subject} {payload.body_plain or ''} {payload.body_html or ''}"
        )

        # Get spam classifier and predict

        _classifier_instance = get_spam_classifier()
        is_spam, confidence = _classifier_instance.predict_with_confidence(email_text)

        return SpamDetectionResponse(is_spam=is_spam, confidence=confidence)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect spam: {str(e)}",
        )


@router.post("/{email_id}/confirm-spam", response_model=MessageResponse)
async def confirm_spam(
    email_id: int,
    request: ConfirmSpamRequest,
    source_folder: str = Query(default="INBOX", description="Source folder"),
    current_user: User = Depends(get_current_user),
):
    """
    Confirm an email is spam and move it to spam folder.
    This endpoint allows users to confirm spam detection and move the email.
    """
    try:
        if not request.confirmed:
            return MessageResponse(
                message="Spam not confirmed, email remains in current folder",
                success=True,
            )

        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and move email to spam folder
        with IMAPService(current_user.email, imap_password) as imap:
            imap.move_email(email_id, source_folder, request.dest_folder)

        return MessageResponse(
            message=f"Email confirmed as spam and moved to {request.dest_folder}",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move spam email: {str(e)}",
        )
