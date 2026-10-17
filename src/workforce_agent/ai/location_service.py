"""
Location service for geocoding and distance calculation.

Supports both static mode (fixture data) and dynamic mode (OpenStreetMap API).
"""

from typing import Optional
from pydantic import BaseModel
from workforce_agent.config import settings


class Location(BaseModel):
    latitude: float
    longitude: float
    display_name: str
    city: str
    state: str
    country: str


class StaticLocationService:
    """Static location service using fixture data (no API calls)"""

    def __init__(self):
        self.locations = self._load_static_locations()

    def _load_static_locations(self):
        """Load locations from fixture file"""
        import json
        try:
            with open(settings.fixture_path, 'r') as f:
                data = json.load(f)
                return data.get('locations', {})
        except Exception as e:
            print(f"Error loading static locations: {e}")
            return {}

    async def geocode(self, address: str) -> Optional[Location]:
        """Return static location data (no API call)"""
        # Search for address in static data
        for site_id, site_data in self.locations.items():
            if address.lower() in site_data['display_name'].lower():
                return Location(
                    latitude=site_data['latitude'],
                    longitude=site_data['longitude'],
                    display_name=site_data['display_name'],
                    city=site_data['city'],
                    state=site_data['state'],
                    country=site_data['country']
                )
        return None

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371
        return c * r


class OSMLocationService:
    """OpenStreetMap location service (requires internet)"""

    OSM_NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

    def __init__(self):
        import httpx
        self.client = httpx.AsyncClient(
            headers={"User-Agent": "ClimateResilientWorkforce/1.0"}
        )

    async def geocode(self, address: str) -> Optional[Location]:
        """Convert address to coordinates using OpenStreetMap Nominatim API"""
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }

            response = await self.client.get(
                f"{self.OSM_NOMINATIM_BASE}/search",
                params=params,
                timeout=settings.osm_timeout
            )
            response.raise_for_status()

            data = response.json()
            if not data:
                return None

            result = data[0]
            return Location(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                display_name=result["display_name"],
                city=result.get("address", {}).get("city", ""),
                state=result.get("address", {}).get("state", ""),
                country=result.get("address", {}).get("country", "")
            )
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371
        return c * r

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
