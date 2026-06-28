import math
import uuid
from typing import Optional

from geopy.distance import geodesic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hospital, User
from app.services.google_maps import GoogleMapsService


DEPARTMENT_KEYWORDS = {
    "発熱": "internal_medicine", "fever": "internal_medicine",
    "胸": "cardiology", "chest": "cardiology", "心臓": "cardiology",
    "頭痛": "neurology", "headache": "neurology",
    "皮膚": "dermatology", "skin": "dermatology", "かゆ": "dermatology",
    "歯": "dentistry", "tooth": "dentistry",
    "骨": "orthopedics", "骨折": "orthopedics", "bone": "orthopedics",
    "子供": "pediatrics", "child": "pediatrics", "小児": "pediatrics",
    "目": "ophthalmology", "eye": "ophthalmology",
    "精神": "psychiatry", "mental": "psychiatry", "うつ": "psychiatry",
    "胃": "gastroenterology", "腹痛": "gastroenterology", "stomach": "gastroenterology",
    "咳": "internal_medicine", "cough": "internal_medicine",
    "喉": "otolaryngology", "throat": "otolaryngology",
}


class HospitalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.maps = GoogleMapsService()

    def _infer_department(self, symptoms: str) -> Optional[str]:
        symptoms_lower = symptoms.lower()
        for key, dept in DEPARTMENT_KEYWORDS.items():
            if key in symptoms_lower:
                return dept
        return None

    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 20,
        department: Optional[str] = None,
        emergency_only: bool = False,
        language: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))

        query = select(Hospital).where(
            Hospital.is_active == True,
            Hospital.latitude.between(latitude - lat_delta, latitude + lat_delta),
            Hospital.longitude.between(longitude - lon_delta, longitude + lon_delta),
        )
        if department:
            query = query.where(Hospital.departments.contains([department]))
        if emergency_only:
            query = query.where(Hospital.emergency_available == True)

        result = await self.db.execute(query.limit(limit * 3))
        hospitals = result.scalars().all()

        scored = []
        for h in hospitals:
            dist = geodesic((latitude, longitude), (h.latitude, h.longitude)).km
            if dist > radius_km:
                continue
            if language and language not in (h.languages or []):
                continue
            scored.append({"hospital": h, "distance_km": round(dist, 2)})

        scored.sort(key=lambda x: x["distance_km"])
        return scored[:limit]

    async def _enrich_with_routes(
        self,
        recommendations: list[dict],
        origin_lat: float,
        origin_lng: float,
        language: str = "ja",
    ) -> list[dict]:
        for rec in recommendations[:5]:
            dest_lat = rec.get("latitude")
            dest_lng = rec.get("longitude")
            if not dest_lat or not dest_lng:
                continue
            routes = await self.maps.get_all_travel_modes(origin_lat, origin_lng, dest_lat, dest_lng, language)
            rec["routes"] = routes
            driving = routes.get("driving")
            if driving:
                rec["travel_time_minutes"] = driving["duration_minutes"]
                rec["route_summary"] = driving.get("summary", "") or (
                    f"車で約{driving['duration_minutes']}分"
                    if language == "ja"
                    else f"~{driving['duration_minutes']} min by car"
                )
                rec["directions_url"] = driving.get("maps_url")
        return recommendations

    async def recommend_hospitals(
        self,
        latitude: float,
        longitude: float,
        symptoms: str,
        urgency: str = "low",
        department: Optional[str] = None,
        language: str = "ja",
        limit: int = 5,
        include_routes: bool = True,
    ) -> list[dict]:
        emergency = urgency in ("high", "emergency")
        department = department or self._infer_department(symptoms)
        keyword = "救急病院" if emergency else (department or "病院 クリニック")

        recommendations: list[dict] = []
        seen_names: set[str] = set()

        # Database hospitals
        db_results = await self.search_nearby(
            latitude, longitude,
            radius_km=30 if emergency else 20,
            department=department,
            emergency_only=emergency,
            language=language if language != "ja" else None,
            limit=limit,
        )
        for item in db_results:
            h = item["hospital"]
            name = h.name if language == "ja" else (h.name_en or h.name)
            if name in seen_names:
                continue
            seen_names.add(name)
            recommendations.append({
                "id": str(h.id),
                "name": name,
                "address": h.address,
                "distance_km": item["distance_km"],
                "phone": h.phone,
                "departments": h.departments or [],
                "emergency_available": h.emergency_available,
                "reservation_url": h.reservation_url,
                "rating": h.rating,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "reason": self._build_reason(h, department, language),
                "source": "database",
            })

        # Google Maps hospitals
        if self.maps.is_configured:
            google_hospitals = await self.maps.find_hospitals(
                latitude, longitude,
                keyword=keyword,
                radius_m=30000 if emergency else 20000,
                limit=limit * 2,
            )
            for gh in google_hospitals:
                if gh["name"] in seen_names:
                    continue
                seen_names.add(gh["name"])
                phone = None
                address = gh["address"]
                if gh.get("place_id"):
                    details = await self.maps.get_place_details(gh["place_id"])
                    if details:
                        phone = details.get("phone")
                        address = details.get("address") or address
                dist = geodesic((latitude, longitude), (gh["latitude"], gh["longitude"])).km
                recommendations.append({
                    "id": gh.get("place_id", ""),
                    "name": gh["name"],
                    "address": address,
                    "distance_km": round(dist, 1),
                    "phone": phone,
                    "departments": [],
                    "emergency_available": emergency,
                    "rating": gh.get("rating"),
                    "latitude": gh["latitude"],
                    "longitude": gh["longitude"],
                    "reason": self._google_reason(gh, department, language),
                    "source": "google_maps",
                })

        recommendations.sort(key=lambda x: (not x.get("emergency_available", False), x["distance_km"]))
        recommendations = recommendations[:limit]

        if include_routes:
            recommendations = await self._enrich_with_routes(recommendations, latitude, longitude, language)

        return recommendations

    async def _resolve_user_location(self, user: User) -> tuple[float, float]:
        lat, lng = user.latitude, user.longitude
        if (not lat or not lng) and user.address:
            geo = await self.maps.geocode(user.address)
            if geo:
                lat, lng = geo["latitude"], geo["longitude"]
                user.latitude = lat
                user.longitude = lng
                await self.db.flush()
        if not lat or not lng:
            lat, lng = 35.6762, 139.6503
        return lat, lng

    async def filter_for_user(
        self,
        user: User,
        symptoms: str,
        sort_by: str = "nearest",
        department: Optional[str] = None,
        excellence_only: bool = False,
        urgency: str = "low",
        language: Optional[str] = None,
        limit: int = 10,
        include_routes: bool = True,
    ) -> list[dict]:
        lang = language or user.preferred_language or "ja"
        lat, lng = await self._resolve_user_location(user)
        dept = department or self._infer_department(symptoms)

        recs = await self.recommend_hospitals(
            lat, lng, symptoms, urgency, department=dept, language=lang,
            limit=limit * 3, include_routes=include_routes,
        )

        if excellence_only:
            recs = [
                r for r in recs
                if (r.get("rating") or 0) >= 4.3 or r.get("source") == "database"
            ]

        if sort_by == "rating":
            recs.sort(key=lambda x: (-(x.get("rating") or 0), x.get("distance_km", 999)))
        elif sort_by == "specialty":
            def specialty_score(r: dict) -> tuple:
                depts = r.get("departments") or []
                match = 1 if dept and dept in depts else 0
                partner = 1 if "提携" in (r.get("reason") or "") or "partner" in (r.get("reason") or "").lower() else 0
                return (-match, -partner, -(r.get("rating") or 0), r.get("distance_km", 999))

            recs.sort(key=specialty_score)
        else:
            recs.sort(key=lambda x: x.get("distance_km", 999))

        return recs[:limit]

    async def recommend_for_user(
        self,
        user: User,
        symptoms: str,
        urgency: str = "low",
        language: Optional[str] = None,
    ) -> list[dict]:
        lang = language or user.preferred_language or "ja"
        lat, lng = await self._resolve_user_location(user)
        return await self.recommend_hospitals(lat, lng, symptoms, urgency, language=lang)

    async def get_directions_to_hospital(
        self,
        user: User,
        hospital_name: str,
        hospital_address: Optional[str] = None,
        hospital_lat: Optional[float] = None,
        hospital_lng: Optional[float] = None,
        language: str = "ja",
    ) -> dict:
        origin_lat = user.latitude
        origin_lng = user.longitude
        if (not origin_lat or not origin_lng) and user.address:
            geo = await self.maps.geocode(user.address)
            if geo:
                origin_lat, origin_lng = geo["latitude"], geo["longitude"]

        if not origin_lat or not origin_lng:
            return {"error": "Home address not configured. Please update your profile."}

        dest_lat, dest_lng = hospital_lat, hospital_lng
        if (not dest_lat or not dest_lng) and hospital_address:
            geo = await self.maps.geocode(hospital_address)
            if geo:
                dest_lat, dest_lng = geo["latitude"], geo["longitude"]

        if not dest_lat or not dest_lng:
            result = await self.db.execute(
                select(Hospital).where(Hospital.name.ilike(f"%{hospital_name}%")).limit(1)
            )
            hospital = result.scalar_one_or_none()
            if hospital:
                dest_lat, dest_lng = hospital.latitude, hospital.longitude

        if not dest_lat or not dest_lng:
            return {"error": f"Could not locate hospital: {hospital_name}"}

        routes = await self.maps.get_all_travel_modes(origin_lat, origin_lng, dest_lat, dest_lng, language)
        return {
            "hospital_name": hospital_name,
            "origin": user.address or f"{origin_lat},{origin_lng}",
            "routes": routes,
            "fastest": routes.get("driving"),
            "safest_note": "For emergencies, call 119. Driving routes avoid highways when possible via Google Maps.",
        }

    def _build_reason(self, hospital, department: Optional[str], language: str) -> str:
        if language == "ja":
            parts = []
            if department:
                parts.append(f"{department}の診療科に対応")
            if hospital.emergency_available:
                parts.append("救急対応可能")
            if hospital.is_partner:
                parts.append("Kenko AI提携病院")
            return "、".join(parts) or "お住まいから近い医療機関"
        parts = []
        if department:
            parts.append(f"Matches {department} specialty")
        if hospital.emergency_available:
            parts.append("Emergency care available")
        if hospital.is_partner:
            parts.append("Kenko AI partner hospital")
        return ", ".join(parts) or "Nearby facility from your home"

    def _google_reason(self, place: dict, department: Optional[str], language: str) -> str:
        if language == "ja":
            parts = ["Google Mapsで確認された医療機関"]
            if department:
                parts.append(f"{department}関連の症状に対応可能")
            if place.get("open_now"):
                parts.append("現在診療中の可能性あり")
            if place.get("rating"):
                parts.append(f"評価 {place['rating']}")
            return "、".join(parts)
        parts = ["Verified via Google Maps"]
        if department:
            parts.append(f"May treat {department}-related symptoms")
        if place.get("rating"):
            parts.append(f"Rating {place['rating']}")
        return ", ".join(parts)
