"""
Geocoder: address string -> (lat, lon)

Provider: Nominatim (free, OpenStreetMap)
"""

import httpx
from app.config import settings
from app.schemas import Coordinates


async def geocode(address: str) -> Coordinates:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": settings.nominatim_user_agent}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if not data:
        raise ValueError(f"Address not found: {address!r}")

    return Coordinates(lat=float(data[0]["lat"]), lon=float(data[0]["lon"]))
