"""Lead specialist lookup per hospital and department."""

from __future__ import annotations

import re
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Doctor, Hospital
from app.services.google_maps import GoogleMapsService
from app.services.hospital import DEPARTMENT_KEYWORDS, HospitalService

DEPARTMENT_LABELS_JA = {
    "internal_medicine": "内科",
    "cardiology": "心臓内科",
    "neurology": "神経内科",
    "dermatology": "皮膚科",
    "dentistry": "歯科",
    "orthopedics": "整形外科",
    "pediatrics": "小児科",
    "ophthalmology": "眼科",
    "psychiatry": "精神科",
    "gastroenterology": "消化器内科",
    "otolaryngology": "耳鼻咽喉科",
    "oncology": "腫瘍科",
    "emergency": "救急科",
}

# Enriched profiles for seeded hospitals (office = hospital campus, not personal home)
HOSPITAL_SPECIALIST_SEED: dict[str, dict] = {
    "東京大学医学部附属病院": {
        "internal_medicine": {
            "name": "鈴木 健一",
            "rank": "教授・内科部長",
            "experience_years": 28,
            "phone": "03-3815-5411（代表）",
            "office_address": "東京都文京区本郷7-3-1 東京大学医学部附属病院 内科棟3階",
        },
        "cardiology": {
            "name": "佐藤 美咲",
            "rank": "准教授・循環器内科",
            "experience_years": 22,
            "phone": "03-3815-5411（代表）",
            "office_address": "東京都文京区本郷7-3-1 東京大学医学部附属病院 循環器内科",
        },
    },
    "聖路加国際病院": {
        "internal_medicine": {
            "name": "田中 誠",
            "rank": "部長・総合内科",
            "experience_years": 25,
            "phone": "03-3541-5151（代表）",
            "office_address": "東京都中央区明石町9-1 聖路加国際病院 内科",
        },
        "dermatology": {
            "name": "高橋 裕子",
            "rank": "主任医師・皮膚科",
            "experience_years": 18,
            "phone": "03-3541-5151（代表）",
            "office_address": "東京都中央区明石町9-1 聖路加国際病院 皮膚科",
        },
    },
}


class SpecialistService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.maps = GoogleMapsService()
        self.hospitals = HospitalService(db)

    @staticmethod
    def _parse_doctor_bio(bio: Optional[str]) -> dict[str, Any]:
        if not bio:
            return {}
        years_match = re.search(r"(\d{1,2})\s*年", bio)
        rank_match = re.search(r"(教授|准教授|部長|主任医師|医長|専門医)", bio)
        return {
            "experience_years": int(years_match.group(1)) if years_match else None,
            "rank": rank_match.group(1) if rank_match else None,
        }

    async def _find_db_doctor(self, hospital_id: uuid.UUID, department: Optional[str]) -> Optional[Doctor]:
        query = (
            select(Doctor)
            .where(Doctor.hospital_id == hospital_id, Doctor.is_active == True)
            .options(selectinload(Doctor.hospital))
        )
        if department:
            query = query.where(Doctor.specialty == department)
        result = await self.db.execute(query.limit(5))
        doctors = result.scalars().all()
        if not doctors and department:
            result = await self.db.execute(
                select(Doctor)
                .where(Doctor.hospital_id == hospital_id, Doctor.is_active == True)
                .limit(1)
            )
            doctors = result.scalars().all()
        return doctors[0] if doctors else None

    def _seed_profile(self, hospital_name: str, department: Optional[str]) -> dict[str, Any]:
        dept = department or "internal_medicine"
        hospital_profiles = HOSPITAL_SPECIALIST_SEED.get(hospital_name, {})
        if dept in hospital_profiles:
            return hospital_profiles[dept]
        return {
            "name": f"{DEPARTMENT_LABELS_JA.get(dept, '内科')} 担当医",
            "rank": "専門医",
            "experience_years": 15,
            "phone": None,
            "office_address": None,
        }

    async def get_lead_specialist(
        self,
        hospital_rec: dict,
        department: Optional[str],
        user_lat: float,
        user_lng: float,
        language: str = "ja",
    ) -> Optional[dict[str, Any]]:
        hospital_id = hospital_rec.get("id")
        hospital_name = hospital_rec.get("name", "")
        dept = department or "internal_medicine"
        dept_label = DEPARTMENT_LABELS_JA.get(dept, dept) if language == "ja" else dept

        profile = self._seed_profile(hospital_name, dept)
        doctor: Optional[Doctor] = None

        if hospital_id:
            try:
                doctor = await self._find_db_doctor(uuid.UUID(str(hospital_id)), dept)
            except (ValueError, TypeError):
                doctor = None

        if doctor:
            parsed = self._parse_doctor_bio(doctor.bio)
            profile = {
                "name": doctor.name if language == "ja" else (doctor.name_en or doctor.name),
                "rank": parsed.get("rank") or profile.get("rank") or "専門医",
                "experience_years": parsed.get("experience_years") or profile.get("experience_years") or 15,
                "phone": hospital_rec.get("phone") or profile.get("phone"),
                "office_address": (
                    doctor.hospital.address if doctor.hospital else hospital_rec.get("address")
                ),
                "specialty": dept_label,
            }
        else:
            profile = {
                **profile,
                "phone": hospital_rec.get("phone") or profile.get("phone"),
                "office_address": profile.get("office_address") or hospital_rec.get("address"),
                "specialty": dept_label,
            }

        dest_lat = hospital_rec.get("latitude")
        dest_lng = hospital_rec.get("longitude")
        routes: dict[str, Any] = {}
        if dest_lat and dest_lng:
            routes = await self.maps.get_all_travel_modes(user_lat, user_lng, dest_lat, dest_lng, language)

        driving = routes.get("driving")
        transit = routes.get("transit")
        walking = routes.get("walking")

        route_summary_ja = []
        route_summary_en = []
        if driving:
            route_summary_ja.append(f"車で約{driving['duration_minutes']}分（{driving.get('distance_text', '')}）")
            route_summary_en.append(f"~{driving['duration_minutes']} min by car ({driving.get('distance_text', '')})")
        if transit:
            route_summary_ja.append(f"公共交通で約{transit['duration_minutes']}分")
            route_summary_en.append(f"~{transit['duration_minutes']} min by transit")
        if walking:
            route_summary_ja.append(f"徒歩約{walking['duration_minutes']}分")
            route_summary_en.append(f"~{walking['duration_minutes']} min on foot")

        return {
            "hospital_name": hospital_name,
            "hospital_id": hospital_id,
            "name": profile.get("name"),
            "rank": profile.get("rank"),
            "experience_years": profile.get("experience_years"),
            "specialty": profile.get("specialty", dept_label),
            "phone": profile.get("phone"),
            "office_address": profile.get("office_address"),
            "routes": routes,
            "route_summary": " / ".join(route_summary_ja if language == "ja" else route_summary_en),
            "directions_url": driving.get("maps_url") if driving else hospital_rec.get("directions_url"),
        }

    async def attach_specialists(
        self,
        user,
        hospitals: list[dict],
        department: Optional[str],
        language: str = "ja",
        limit: int = 3,
    ) -> list[dict]:
        lat, lng = await self.hospitals._resolve_user_location(user)
        specialists = []
        for h in hospitals[:limit]:
            spec = await self.get_lead_specialist(h, department, lat, lng, language)
            if spec:
                specialists.append(spec)
        return specialists
