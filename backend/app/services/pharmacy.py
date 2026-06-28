"""Nearby pharmacy lookup for OTC medication purchase guidance."""

from __future__ import annotations

from geopy.distance import geodesic

from app.models import User
from app.services.google_maps import GoogleMapsService
from app.services.hospital import HospitalService


class PharmacyService:
    def __init__(self, db):
        self.db = db
        self.maps = GoogleMapsService()
        self._hospital_svc = HospitalService(db)

    async def recommend_for_user(
        self,
        user: User,
        language: str = "ja",
        limit: int = 5,
    ) -> list[dict]:
        lat, lng = await self._hospital_svc._resolve_user_location(user)
        return await self.recommend_nearby(lat, lng, language=language, limit=limit)

    async def recommend_nearby(
        self,
        latitude: float,
        longitude: float,
        language: str = "ja",
        limit: int = 5,
    ) -> list[dict]:
        if not self.maps.is_configured:
            return self._fallback_pharmacies(latitude, longitude, language, limit)

        places = await self.maps.find_pharmacies(latitude, longitude, limit=limit * 2)
        results: list[dict] = []
        for place in places[:limit]:
            phone = place.get("phone")
            address = place.get("address", "")
            if place.get("place_id") and not phone:
                details = await self.maps.get_place_details(place["place_id"])
                if details:
                    phone = details.get("phone") or phone
                    address = details.get("address") or address

            dist = geodesic(
                (latitude, longitude),
                (place["latitude"], place["longitude"]),
            ).km
            results.append({
                "id": place.get("place_id", ""),
                "name": place["name"],
                "address": address,
                "phone": phone,
                "distance_km": round(dist, 1),
                "rating": place.get("rating"),
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "open_now": place.get("open_now"),
                "source": "google_maps",
            })

        results.sort(key=lambda x: x["distance_km"])
        return results[:limit]

    async def recommend_for_user_with_routes(
        self,
        user: User,
        language: str = "ja",
        limit: int = 5,
    ) -> list[dict]:
        recs = await self.recommend_for_user(user, language=language, limit=limit)
        lat, lng = await self._hospital_svc._resolve_user_location(user)
        for rec in recs:
            dest_lat, dest_lng = rec.get("latitude"), rec.get("longitude")
            if not dest_lat or not dest_lng:
                continue
            routes = await self.maps.get_all_travel_modes(lat, lng, dest_lat, dest_lng, language)
            rec["routes"] = routes
            driving = routes.get("driving")
            if driving:
                rec["travel_time_minutes"] = driving["duration_minutes"]
                rec["directions_url"] = driving.get("maps_url")
                rec["route_summary"] = (
                    f"車で約{driving['duration_minutes']}分"
                    if language == "ja"
                    else f"~{driving['duration_minutes']} min by car"
                )
        return recs

    @staticmethod
    def _fallback_pharmacies(lat: float, lng: float, language: str, limit: int) -> list[dict]:
        """Static examples when Google Maps is not configured (Tokyo area)."""
        samples = [
            {
                "name": "マツモトキヨシ 渋谷店",
                "address": "東京都渋谷区道玄坂1-2-3",
                "phone": "03-0000-0001",
                "latitude": 35.6595,
                "longitude": 139.7004,
            },
            {
                "name": "ウエルシア 新宿店",
                "address": "東京都新宿区西新宿1-1-1",
                "phone": "03-0000-0002",
                "latitude": 35.6896,
                "longitude": 139.6917,
            },
            {
                "name": "ツルハドラッグ 池袋店",
                "address": "東京都豊島区南池袋1-28-1",
                "phone": "03-0000-0003",
                "latitude": 35.7295,
                "longitude": 139.7109,
            },
        ]
        out = []
        for s in samples[:limit]:
            dist = geodesic((lat, lng), (s["latitude"], s["longitude"])).km
            out.append({
                **s,
                "distance_km": round(dist, 1),
                "source": "fallback",
            })
        out.sort(key=lambda x: x["distance_km"])
        return out
