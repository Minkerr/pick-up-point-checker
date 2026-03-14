from pydantic import BaseModel


class Coordinates(BaseModel):
    lat: float
    lon: float


class ExtraField(BaseModel):
    label: str
    value: str
    tooltip: str | None = None  # tooltip text explaining the field


class MarketplaceResult(BaseModel):
    status: str                                 # "approved" | "limited" | "denied" | "error"
    tariff: float | None = None
    financial_support: int | None = None
    financial_support_label: str | None = None
    extra_fields: list[ExtraField] = []
    raw: dict | None = None                     # full marketplace response for debugging


class CheckLocationResponse(BaseModel):
    coordinates: Coordinates
    ozon: MarketplaceResult
    wb: MarketplaceResult
    yandex_market: MarketplaceResult
