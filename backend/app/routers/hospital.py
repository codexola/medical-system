from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import HospitalFilterRequest, HospitalRecommendRequest, HospitalResponse, HospitalSearchRequest
from app.database.session import get_db
from app.models import Hospital, User
from app.routers.auth import get_current_user
from app.services.hospital import HospitalService

router = APIRouter(prefix="/hospital", tags=["hospital"])


def _to_response(r: dict) -> HospitalResponse:
    return HospitalResponse(
        id=UUID(r["id"]) if r.get("id") and len(str(r["id"])) == 36 else None,
        name=r["name"],
        address=r["address"],
        distance_km=r.get("distance_km"),
        phone=r.get("phone"),
        departments=r.get("departments", []),
        emergency_available=r.get("emergency_available", False),
        rating=r.get("rating"),
        reason=r.get("reason"),
        latitude=r.get("latitude"),
        longitude=r.get("longitude"),
        directions_url=r.get("directions_url"),
        travel_time_minutes=r.get("travel_time_minutes"),
        route_summary=r.get("route_summary"),
        routes=r.get("routes"),
    )


@router.post("/search", response_model=list[HospitalResponse])
async def search_hospitals(data: HospitalSearchRequest, db: AsyncSession = Depends(get_db)):
    service = HospitalService(db)
    results = await service.search_nearby(
        data.latitude,
        data.longitude,
        data.radius_km,
        data.department,
        data.emergency_only,
        language=data.language,
    )
    return [
        HospitalResponse(
            id=r["hospital"].id,
            name=r["hospital"].name,
            address=r["hospital"].address,
            distance_km=r["distance_km"],
            phone=r["hospital"].phone,
            departments=r["hospital"].departments or [],
            emergency_available=r["hospital"].emergency_available,
            rating=r["hospital"].rating,
            latitude=r["hospital"].latitude,
            longitude=r["hospital"].longitude,
        )
        for r in results
    ]


@router.post("/filter", response_model=list[HospitalResponse])
async def filter_hospitals(
    data: HospitalFilterRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = HospitalService(db)
    results = await service.filter_for_user(
        user,
        data.symptoms,
        sort_by=data.sort_by,
        department=data.department,
        excellence_only=data.excellence_only,
        urgency=data.urgency,
        language=data.language,
        limit=data.limit,
    )
    return [_to_response(r) for r in results]


@router.post("/recommend", response_model=list[HospitalResponse])
async def recommend_hospitals(
    data: HospitalRecommendRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = HospitalService(db)
    if data.latitude is not None and data.longitude is not None:
        results = await service.recommend_hospitals(
            data.latitude, data.longitude, data.symptoms, data.urgency, language=data.language
        )
    else:
        results = await service.recommend_for_user(user, data.symptoms, data.urgency, data.language)
    return [_to_response(r) for r in results]


@router.get("/directions")
async def get_directions(
    hospital_name: str = Query(...),
    hospital_address: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = HospitalService(db)
    return await service.get_directions_to_hospital(
        user, hospital_name, hospital_address, language=user.preferred_language or "ja"
    )


@router.get("/list")
async def list_hospitals(
    prefecture: str = Query(None),
    department: str = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Hospital).where(Hospital.is_active == True)
    if prefecture:
        query = query.where(Hospital.prefecture == prefecture)
    if department:
        query = query.where(Hospital.departments.contains([department]))
    query = query.limit(limit)
    result = await db.execute(query)
    hospitals = result.scalars().all()
    return [
        {
            "id": str(h.id),
            "name": h.name,
            "prefecture": h.prefecture,
            "city": h.city,
            "departments": h.departments,
            "emergency_available": h.emergency_available,
        }
        for h in hospitals
    ]


@router.get("/{hospital_id}")
async def get_hospital(hospital_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).where(Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        return {"error": "Not found"}
    return {
        "id": str(hospital.id),
        "name": hospital.name,
        "name_en": hospital.name_en,
        "address": hospital.address,
        "phone": hospital.phone,
        "departments": hospital.departments,
        "opening_hours": hospital.opening_hours,
        "emergency_available": hospital.emergency_available,
        "languages": hospital.languages,
        "description": hospital.description,
    }
