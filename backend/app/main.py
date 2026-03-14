from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze
from app.config import settings
from app.geocoder import geocode
from app.schemas import CheckLocationResponse, Coordinates

app = FastAPI(title="Pick-Up Point Checker", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/check-location", response_model=CheckLocationResponse)
async def check_location(
    address: str | None = Query(None, description="Адрес для проверки"),
    lat: float | None = Query(None, description="Широта"),
    lon: float | None = Query(None, description="Долгота"),
):
    if lat is not None and lon is not None:
        coords = Coordinates(lat=lat, lon=lon)
    elif address:
        try:
            coords = await geocode(address)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Ошибка геокодера: {exc}")
    else:
        raise HTTPException(status_code=422, detail="Нужно передать address или lat+lon")

    marketplace_results = await analyze(coords)

    return CheckLocationResponse(
        coordinates=coords,
        ozon=marketplace_results["ozon"],
        wb=marketplace_results["wb"],
        yandex_market=marketplace_results["yandex_market"],
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
