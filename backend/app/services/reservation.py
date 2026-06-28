import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Doctor, DoctorSchedule, Reservation, ReservationStatus


class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_slots(
        self,
        doctor_id: uuid.UUID,
        target_date: date,
        period: Optional[str] = None,
    ) -> list[dict]:
        day_of_week = target_date.weekday()
        result = await self.db.execute(
            select(DoctorSchedule).where(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.day_of_week == day_of_week,
                DoctorSchedule.is_active == True,
            )
        )
        schedules = result.scalars().all()
        if not schedules:
            return []

        booked_result = await self.db.execute(
            select(Reservation.time).where(
                Reservation.doctor_id == doctor_id,
                Reservation.date == target_date,
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            )
        )
        booked_times = {t for (t,) in booked_result.fetchall()}

        slots = []
        for schedule in schedules:
            current = datetime.combine(target_date, schedule.start_time)
            end = datetime.combine(target_date, schedule.end_time)
            delta = timedelta(minutes=schedule.slot_duration_minutes)

            while current + delta <= end:
                slot_time = current.time()
                if slot_time not in booked_times:
                    period_label = "morning" if slot_time.hour < 12 else "afternoon"
                    if period is None or period == period_label:
                        slots.append({"time": slot_time.isoformat(), "period": period_label})
                current += delta

        return slots

    async def create_reservation(
        self,
        user_id: uuid.UUID,
        doctor_id: uuid.UUID,
        target_date: date,
        slot_time: time,
        symptoms: Optional[str] = None,
        department: Optional[str] = None,
        hospital_id: Optional[uuid.UUID] = None,
    ) -> Reservation:
        reservation = Reservation(
            user_id=user_id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            date=target_date,
            time=slot_time,
            symptoms=symptoms,
            department=department,
            status=ReservationStatus.CONFIRMED,
        )
        self.db.add(reservation)
        await self.db.flush()
        return reservation

    async def cancel_reservation(self, reservation_id: uuid.UUID) -> Optional[Reservation]:
        result = await self.db.execute(select(Reservation).where(Reservation.id == reservation_id))
        reservation = result.scalar_one_or_none()
        if reservation:
            reservation.status = ReservationStatus.CANCELLED
            await self.db.flush()
        return reservation

    async def get_user_reservations(self, user_id: uuid.UUID, upcoming_only: bool = False) -> list[Reservation]:
        query = select(Reservation).where(Reservation.user_id == user_id)
        if upcoming_only:
            query = query.where(
                Reservation.date >= date.today(),
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            )
        query = query.order_by(Reservation.date.desc(), Reservation.time.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_today_reservations(self, hospital_id: Optional[uuid.UUID] = None) -> list[Reservation]:
        query = select(Reservation).where(Reservation.date == date.today())
        if hospital_id:
            query = query.where(Reservation.hospital_id == hospital_id)
        query = query.order_by(Reservation.time)
        result = await self.db.execute(query.options(selectinload(Reservation.user), selectinload(Reservation.doctor)))
        return list(result.scalars().all())
