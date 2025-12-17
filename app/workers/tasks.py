"""Celery tasks for email monitoring and spam detection."""

import json
from datetime import datetime

import redis
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.security import decrypt_password
from app.database import SessionLocal
from app.models.user import User
from app.services.imap_service import IMAPService
from app.services.spam_classifier import get_spam_classifier
from app.workers import celery_app


def get_redis_client():
    """Get Redis client for pub/sub."""
    from app.core.config import get_settings

    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def publish_email_event(user_id: int, event_data: dict):
    """Publish email event to Redis pub/sub for SSE."""
    redis_client = get_redis_client()
    channel_name = f"email_events:user:{user_id}"
    redis_client.publish(channel_name, json.dumps(event_data))


@celery_app.task(name="app.workers.tasks.monitor_user_emails")
def monitor_user_emails(user_id: int):
    """
    Monitor emails for a specific user.

    Fetches new emails, classifies them with spam detector,
    moves spam to Spam folder, and publishes SSE events.
    """
    db: Session = SessionLocal()

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active or not user.is_monitoring:
            return

        # Decrypt IMAP password
        imap_password = decrypt_password(user.encrypted_imap_password)

        # Get spam classifier
        classifier = get_spam_classifier()

        # Connect to IMAP
        with IMAPService(user.email, imap_password) as imap:
            # Get unread emails
            unread_emails = imap.get_unread_emails(folder="INBOX")

            for email in unread_emails:
                try:
                    # Get full email details
                    email_detail = imap.get_email_detail(email["id"], folder="INBOX")

                    # Combine subject and body for classification
                    email_text = f"{email_detail['subject']} {email_detail['body_plain']} {email_detail['body_html']}"

                    # Classify email
                    is_spam, confidence = classifier.predict_with_confidence(email_text)

                    if is_spam:
                        # Move to Spam folder
                        try:
                            imap.move_email(email["id"], "INBOX", "Spam")

                            # Publish spam detection event
                            publish_email_event(
                                user_id,
                                {
                                    "event_type": "spam_detected",
                                    "email_id": email["id"],
                                    "subject": email_detail["subject"],
                                    "from": email_detail["from"],
                                    "confidence": confidence,
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )

                            print(
                                f"✓ Spam detected and moved: {email_detail['subject']}"
                            )

                        except Exception as e:
                            print(f"✗ Failed to move spam email: {e}")

                    else:
                        # Legitimate email - publish event
                        publish_email_event(
                            user_id,
                            {
                                "event_type": "new_email",
                                "email_id": email["id"],
                                "subject": email_detail["subject"],
                                "from": email_detail["from"],
                                "is_spam": False,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        )

                except Exception as e:
                    print(f"✗ Error processing email {email['id']}: {e}")
                    # Publish error event
                    publish_email_event(
                        user_id,
                        {
                            "event_type": "error",
                            "error": str(e),
                            "email_id": email["id"],
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

        # Update last sync time
        user.last_sync_time = datetime.utcnow()
        db.commit()

        print(f"✓ Monitoring completed for user {user.email}")

    except Exception as e:
        print(f"✗ Error monitoring user {user_id}: {e}")
        # Publish error event
        try:
            publish_email_event(
                user_id,
                {
                    "event_type": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except:
            pass

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.monitor_all_users")
def monitor_all_users():
    """
    Monitor emails for all active users.

    Called periodically by Celery Beat.
    """
    db: Session = SessionLocal()

    try:
        # Get all active users with monitoring enabled
        active_users = (
            db.query(User)
            .filter(User.is_active == True, User.is_monitoring == True)
            .all()
        )

        print(f"📧 Monitoring {len(active_users)} active users")

        # Trigger monitoring task for each user
        for user in active_users:
            monitor_user_emails.delay(user.id)

    finally:
        db.close()
