"""Celery worker configuration and tasks."""
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "spam_detection_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.workers.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    'monitor-all-active-users': {
        'task': 'app.workers.tasks.monitor_all_users',
        'schedule': settings.EMAIL_CHECK_INTERVAL_SECONDS,
    },
}
