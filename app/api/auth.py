"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    encrypt_password,
    hash_password,
    pwd_context,
    verify_password,
    verify_token,
)
from app.database import get_db
from app.models.user import User
from app.schemas import (
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.

    Creates a new user account with encrypted IMAP credentials.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    try:
        hashed_pw = hash_password(user_data.password)
    except ValueError as exc:
        # Passlib/bcrypt may raise ValueError when password is too long
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        encrypted_imap_password=encrypt_password(user_data.imap_password),
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return MessageResponse(message="User registered successfully", success=True)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return access and refresh tokens.

    Authenticates user credentials and starts email monitoring.
    """
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Verify password (catch hashing errors like long-password ValueError)
    try:
        ok = verify_password(credentials.password, user.hashed_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Create tokens
    # If the stored hash is using an old scheme (e.g. bcrypt) and the
    # context is configured with a newer default (argon2), rehash the
    # password to the new scheme on successful login to transparently
    # migrate user hashes.
    if pwd_context.needs_update(user.hashed_password):
        try:
            user.hashed_password = hash_password(credentials.password)
            db.commit()
        except Exception:
            # If rehashing fails for any reason, we silently continue; the
            # user can still authenticate using the old hash.
            pass

    token_data = {"sub": user.email, "user_id": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Start monitoring (mark user as monitoring)
    user.is_monitoring = True
    db.commit()

    # TODO: Trigger Celery task to start monitoring emails for this user
    # from app.workers.tasks import start_monitoring
    # start_monitoring.delay(user.id)

    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    payload = verify_token(request.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Create new access token
    token_data = {"sub": payload["sub"], "user_id": payload["user_id"]}
    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Logout user and stop email monitoring.
    """
    # Stop monitoring
    current_user.is_monitoring = False
    db.commit()

    # TODO: Stop Celery task for this user
    # from app.workers.tasks import stop_monitoring
    # stop_monitoring.delay(current_user.id)

    return MessageResponse(message="Logged out successfully", success=True)
