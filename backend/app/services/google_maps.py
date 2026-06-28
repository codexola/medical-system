import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GoogleMapsService:
    BASE = "https://maps.googleapis.com/maps/api"

    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY or settings.GOOGLE_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def geocode(self, address: str) -> Optional[dict[str, Any]]:
        if not self.is_configured or not address.strip():
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.BASE}/geocode/json",
                    params={"address": address, "key": self.api_key, "language": "ja", "region": "jp"},
                )
                data = res.json()
            if data.get("status") != "OK" or not data.get("results"):
                logger.warning("Geocode failed: %s", data.get("status"))
                return None
            result = data["results"][0]
            loc = result["geometry"]["location"]
            return {
                "latitude": loc["lat"],
                "longitude": loc["lng"],
                "formatted_address": result["formatted_address"],
            }
        except Exception as e:
            logger.error("Geocode error: %s", e)
            return None

    async def find_hospitals(
        self,
        latitude: float,
        longitude: float,
        keyword: str = "病院",
        radius_m: int = 20000,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.BASE}/place/nearbysearch/json",
                    params={
                        "location": f"{latitude},{longitude}",
                        "radius": radius_m,
                        "type": "hospital",
                        "keyword": keyword,
                        "key": self.api_key,
                        "language": "ja",
                    },
                )
                data = res.json()
            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.warning("Places search failed: %s", data.get("status"))
                return []

            hospitals = []
            for place in data.get("results", [])[:limit]:
                loc = place.get("geometry", {}).get("location", {})
                hospitals.append({
                    "place_id": place.get("place_id"),
                    "name": place.get("name", ""),
                    "address": place.get("vicinity", ""),
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lng"),
                    "rating": place.get("rating"),
                    "open_now": place.get("opening_hours", {}).get("open_now"),
                    "source": "google_maps",
                })
            return hospitals
        except Exception as e:
            logger.error("Places search error: %s", e)
            return []

    async def find_pharmacies(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 5000,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.BASE}/place/nearbysearch/json",
                    params={
                        "location": f"{latitude},{longitude}",
                        "radius": radius_m,
                        "type": "pharmacy",
                        "keyword": "ドラッグストア 薬局",
                        "key": self.api_key,
                        "language": "ja",
                    },
                )
                data = res.json()
            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.warning("Pharmacy search failed: %s", data.get("status"))
                return []

            pharmacies = []
            for place in data.get("results", [])[:limit]:
                loc = place.get("geometry", {}).get("location", {})
                pharmacies.append({
                    "place_id": place.get("place_id"),
                    "name": place.get("name", ""),
                    "address": place.get("vicinity", ""),
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lng"),
                    "rating": place.get("rating"),
                    "open_now": place.get("opening_hours", {}).get("open_now"),
                    "source": "google_maps",
                })
            return pharmacies
        except Exception as e:
            logger.error("Pharmacy search error: %s", e)
            return []

    async def get_place_details(self, place_id: str) -> Optional[dict[str, Any]]:
        if not self.is_configured or not place_id:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.BASE}/place/details/json",
                    params={
                        "place_id": place_id,
                        "fields": "formatted_phone_number,formatted_address,opening_hours,rating",
                        "key": self.api_key,
                        "language": "ja",
                    },
                )
                data = res.json()
            if data.get("status") != "OK":
                return None
            result = data.get("result", {})
            return {
                "phone": result.get("formatted_phone_number"),
                "address": result.get("formatted_address"),
                "rating": result.get("rating"),
                "open_now": result.get("opening_hours", {}).get("open_now"),
            }
        except Exception as e:
            logger.error("Place details error: %s", e)
            return None

    async def get_directions(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
        language: str = "ja",
    ) -> Optional[dict[str, Any]]:
        if not self.is_configured:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.BASE}/directions/json",
                    params={
                        "origin": f"{origin_lat},{origin_lng}",
                        "destination": f"{dest_lat},{dest_lng}",
                        "mode": mode,
                        "alternatives": "true",
                        "key": self.api_key,
                        "language": language,
                        "region": "jp",
                    },
                )
                data = res.json()
            if data.get("status") != "OK" or not data.get("routes"):
                return None

            routes = []
            for route in data["routes"]:
                leg = route["legs"][0]
                steps = [
                    s.get("html_instructions", "").replace("<b>", "").replace("</b>", "")
                    for s in leg.get("steps", [])[:5]
                ]
                routes.append({
                    "mode": mode,
                    "duration_minutes": leg["duration"]["value"] // 60,
                    "duration_text": leg["duration"]["text"],
                    "distance_km": round(leg["distance"]["value"] / 1000, 1),
                    "distance_text": leg["distance"]["text"],
                    "summary": route.get("summary", ""),
                    "steps": steps,
                    "maps_url": self.directions_url(origin_lat, origin_lng, dest_lat, dest_lng, mode),
                })

            routes.sort(key=lambda r: r["duration_minutes"])
            return {
                "fastest": routes[0] if routes else None,
                "alternatives": routes[1:3] if len(routes) > 1 else [],
                "all_routes": routes,
            }
        except Exception as e:
            logger.error("Directions error: %s", e)
            return None

    async def get_all_travel_modes(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        language: str = "ja",
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for mode in ("driving", "transit", "walking"):
            directions = await self.get_directions(
                origin_lat, origin_lng, dest_lat, dest_lng, mode=mode, language=language
            )
            if directions and directions.get("fastest"):
                result[mode] = directions["fastest"]
        return result

    @staticmethod
    def directions_url(
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
    ) -> str:
        return (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin_lat},{origin_lng}"
            f"&destination={dest_lat},{dest_lng}"
            f"&travelmode={mode}"
        )
