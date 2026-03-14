from abc import ABC, abstractmethod

import httpx

from app.schemas import Coordinates, MarketplaceResult


class BaseStrategy(ABC):
    """Base class for a marketplace pick-up point check strategy."""

    name: str  # human-readable identifier, e.g. "ozon", "wb"

    @abstractmethod
    async def check(self, coords: Coordinates) -> MarketplaceResult:
        """Query the marketplace API and return a normalized result."""
        ...

    # ---------- helpers ----------

    async def _get(self, url: str, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    def _error_result(self, exc: Exception) -> MarketplaceResult:
        return MarketplaceResult(status="error", raw={"error": str(exc)})
