from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "kenko",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    beat_schedule={
        "send-appointment-reminders-1d": {
            "task": "app.tasks.send_reminder_1d",
            "schedule": crontab(hour=9, minute=0),
        },
        "send-appointment-reminders-1h": {
            "task": "app.tasks.send_reminder_1h",
            "schedule": crontab(minute="*/30"),
        },
        "daily-health-checkin": {
            "task": "app.tasks.send_daily_checkin",
            "schedule": crontab(hour=8, minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app"])
