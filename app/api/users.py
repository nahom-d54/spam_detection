"""Users API endpoints: profile and password management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas import (
    ChangePasswordRequest,
    MessageResponse,
    UserOut,
    UserStats,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return current authenticated user's profile."""
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_monitoring=current_user.is_monitoring,
        last_sync_time=current_user.last_sync_time,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/me", response_model=UserOut)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile (email only for now)."""
    if payload.email and payload.email != current_user.email:
        # Check uniqueness
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        current_user.email = payload.email
        db.commit()
        db.refresh(current_user)

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_monitoring=current_user.is_monitoring,
        last_sync_time=current_user.last_sync_time,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post("/me/password", response_model=MessageResponse)
async def change_my_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user's password.

    Requires correct current/old password, and new password is hashed and stored.
    """
    # Verify old password; catch ValueError for bcrypt long password
    try:
        ok = verify_password(payload.old_password, current_user.hashed_password)
    except ValueError as exc:
        # similar handling as other auth endpoints
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password"
        )

    # Hash and update
    new_hash = hash_password(payload.new_password)
    current_user.hashed_password = new_hash
    db.commit()
    return MessageResponse(message="Password changed successfully", success=True)


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
):
    """Get current user's email statistics and metrics."""
    try:
        from datetime import datetime, timezone

        from app.core.security import decrypt_password
        from app.services.imap_service import IMAPService

        # Decrypt IMAP password
        imap_password = decrypt_password(current_user.encrypted_imap_password)

        # Connect to IMAP and fetch stats
        with IMAPService(current_user.email, imap_password) as imap:
            # Get folder count
            folders = imap.list_folders()
            folders_count = len(folders)

            # Get INBOX email counts
            imap.client.select_folder("INBOX", readonly=True)
            all_messages = imap.client.search(["ALL"])
            unread_messages = imap.client.search(["UNSEEN"])
            total_emails = len(all_messages)
            unread_emails = len(unread_messages)

        # Calculate account age
        if current_user.created_at:
            account_age = datetime.now(timezone.utc) - current_user.created_at.replace(
                tzinfo=timezone.utc
            )
            account_age_days = account_age.days
        else:
            account_age_days = 0

        # Estimate spam (placeholder - in production, query from database/cache)
        spam_detected = 0

        return UserStats(
            total_emails=total_emails,
            unread_emails=unread_emails,
            spam_detected=spam_detected,
            folders_count=folders_count,
            is_monitoring=current_user.is_monitoring,
            last_sync_time=current_user.last_sync_time,
            account_age_days=account_age_days,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user stats: {str(e)}",
        )
