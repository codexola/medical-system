import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import get_settings
from app.models import Reservation, ReservationStatus, Subscription, SubscriptionStatus, User

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_URL_SYNC)


def get_sync_session() -> Session:
    return Session(sync_engine)


@celery_app.task(name="app.tasks.send_reminder_1d")
def send_reminder_1d():
    tomorrow = date.today() + timedelta(days=1)
    with get_sync_session() as db:
        reservations = db.execute(
            select(Reservation).where(
                Reservation.date == tomorrow,
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.reminder_sent_1d == False,
            )
        ).scalars().all()

        for r in reservations:
            user = db.get(User, r.user_id)
            if user and user.line_user_id:
                msg = f"明日 {r.time.strftime('%H:%M')} に予約があります。お忘れなく。"
                asyncio.run(_push_line(user.line_user_id, msg))
                r.reminder_sent_1d = True
        db.commit()


@celery_app.task(name="app.tasks.send_reminder_1h")
def send_reminder_1h():
    now = datetime.now(timezone.utc)
    with get_sync_session() as db:
        reservations = db.execute(
            select(Reservation).where(
                Reservation.date == date.today(),
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.reminder_sent_1h == False,
            )
        ).scalars().all()

        for r in reservations:
            user = db.get(User, r.user_id)
            if user and user.line_user_id:
                msg = f"1時間後 ({r.time.strftime('%H:%M')}) に予約があります。"
                asyncio.run(_push_line(user.line_user_id, msg))
                r.reminder_sent_1h = True
        db.commit()


@celery_app.task(name="app.tasks.send_daily_checkin")
def send_daily_checkin():
    with get_sync_session() as db:
        active_users = db.execute(
            select(User).join(Subscription).where(
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
                User.line_user_id.isnot(None),
            )
        ).scalars().all()

        for user in active_users:
            msg = "おはようございます。今日の体調はいかがですか？"
            asyncio.run(_push_line(user.line_user_id, msg))


@celery_app.task(name="app.tasks.index_pdf")
def index_pdf(document_id: str, file_path: str):
    """Background task to process and index PDF documents."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    # Indexing would be done via async RAG service in production
    return {"document_id": document_id, "pages": len(reader.pages), "chars": len(text)}


async def _push_line(user_id: str, message: str):
    from app.line.client import LineClient

    client = LineClient()
    await client.push_message(user_id, message)
