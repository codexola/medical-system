from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AvailabilityRequest, ReservationCreate, ReservationResponse
from app.database.session import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.services.notification import NotificationService
from app.services.reservation import ReservationService

router = APIRouter(prefix="/reservation", tags=["reservation"])


@router.get("/", response_model=list[ReservationResponse])
async def list_reservations(
    upcoming: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReservationService(db)
    reservations = await service.get_user_reservations(user.id, upcoming_only=upcoming)
    return [
        ReservationResponse(
            id=r.id,
            date=r.date,
            time=r.time.isoformat(),
            status=r.status.value,
            department=r.department,
            symptoms=r.symptoms,
        )
        for r in reservations
    ]


@router.post("/availability")
async def check_availability(data: AvailabilityRequest, db: AsyncSession = Depends(get_db)):
    service = ReservationService(db)
    slots = await service.get_available_slots(data.doctor_id, data.date, data.period)
    return {"slots": slots}


@router.post("/", response_model=ReservationResponse)
async def create_reservation(
    data: ReservationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.doctor_id:
        raise HTTPException(status_code=400, detail="doctor_id is required")
    slot_time = datetime.strptime(data.time, "%H:%M").time()
    service = ReservationService(db)
    reservation = await service.create_reservation(
        user.id, data.doctor_id, data.date, slot_time, data.symptoms, data.department, data.hospital_id
    )

    lang = user.preferred_language or "ja"
    msg = (
        f"予約が確定しました。\n日時: {data.date} {data.time}"
        if lang == "ja"
        else f"Reservation confirmed.\nDate: {data.date} {data.time}"
    )
    await NotificationService(db).create_notification(user.id, "reservation_confirmed", "予約確認", msg)

    return ReservationResponse(
        id=reservation.id,
        date=reservation.date,
        time=reservation.time.isoformat(),
        status=reservation.status.value,
        department=reservation.department,
        symptoms=reservation.symptoms,
    )


@router.delete("/{reservation_id}")
async def cancel_reservation(
    reservation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReservationService(db)
    reservation = await service.cancel_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"status": "cancelled"}
