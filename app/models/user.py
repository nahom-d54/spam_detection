"""User model for storing user credentials and monitoring state."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model with encrypted IMAP credentials."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # For API authentication
    encrypted_imap_password = Column(String, nullable=False)  # Encrypted IMAP password
    is_active = Column(Boolean, default=True, nullable=False)
    is_monitoring = Column(Boolean, default=False, nullable=False)  # Active monitoring status
    last_sync_time = Column(DateTime(timezone=True), nullable=True)  # Last email sync timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
