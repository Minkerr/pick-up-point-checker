"""
Ozon strategy.

API: https://pvz-map.ozon.ru/api/task/creation-availability
Params: location.lat, location.lon, layer, withNearestPoints
"""

from curl_cffi.requests import AsyncSession

from app.config import settings
from app.schemas import Coordinates, ExtraField, MarketplaceResult
from app.strategies.base import BaseStrategy

_OZON_URL = "https://pvz-map.ozon.ru/api/task/creation-availability"

_HEADERS = {
    "Referer": "https://pvz-map.ozon.ru/",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

_DIFF_TARIFF_NAMES = {
    "MaxBrand":  "MaxBrand",
    "HomePoint": "HomePoint",
    "Corporate": "Corporate",
}
# Display priority: best plan first
_DIFF_TARIFF_PRIORITY = ["MaxBrand", "HomePoint", "Corporate"]


class OzonStrategy(BaseStrategy):
    name = "ozon"

    async def check(self, coords: Coordinates) -> MarketplaceResult:
        params = {
            "location.lat": coords.lat,
            "location.lon": coords.lon,
            "layer": "PvzGroup",
            "withNearestPoints": "false",
        }
        headers = {**_HEADERS}
        if settings.ozon_cookie:
            headers["Cookie"] = settings.ozon_cookie

        try:
            # curl_cffi impersonates Chrome TLS fingerprint to bypass bot protection
            async with AsyncSession(impersonate="chrome124") as session:
                resp = await session.get(_OZON_URL, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            return self._error_result(exc)

        return self._parse(data)

    def _parse(self, data: dict) -> MarketplaceResult:
        allowed: bool = data.get("allowed", False)
        status = "approved" if allowed else "denied"

        tariff: float | None = None
        financial_support: int | None = None
        financial_support_label: str | None = None
        extra: list[ExtraField] = []

        mb = data.get("tariffs", {}).get("mb") or {}

        if mb:
            # Zone with MB program: elevated tariff + financial support
            tariff = mb.get("increasedTariff")
            flex = mb.get("flexSupport") or []
            if flex:
                financial_support = flex[0].get("totalSupport")
                gmv_periods = flex[0].get("flexMinGmv") or []
                if gmv_periods:
                    max_days = max(p.get("for", 0) for p in gmv_periods)
                    financial_support_label = f"за {max_days} дней (итого по программе)"

                    conditions = []
                    for p in gmv_periods:
                        days = p.get("for", 0)
                        gmv = p.get("minGmv", 0)
                        if gmv:
                            conditions.append(f"{days} дн → {gmv:,} ₽".replace(",", "\u00a0"))
                        else:
                            conditions.append(f"{days} дн → без требований к обороту")
                    extra.append(ExtraField(
                        label="Условия по обороту",
                        value="; ".join(conditions),
                        tooltip="Минимальный оборот ПВЗ за период для получения субсидии",
                    ))
                else:
                    financial_support_label = "за период программы"

        else:
            # Standard zone: show the best available tariff plan from diffTariffs
            diff = data.get("diffTariffs") or {}
            available_plans = []
            chosen = False
            for plan_key in _DIFF_TARIFF_PRIORITY:
                plan = diff.get(plan_key, {}).get("now") or {}
                pct = plan.get("percent")
                if pct is not None:
                    label = _DIFF_TARIFF_NAMES.get(plan_key, plan_key)
                    available_plans.append(f"{label} {pct}%")
                    if not chosen:
                        tariff = float(pct)
                        chosen = True

            if available_plans:
                extra.append(ExtraField(
                    label="Доступные форматы",
                    value=", ".join(available_plans),
                    tooltip="Тарифные планы, доступные для открытия ПВЗ в данной зоне",
                ))

            if not chosen:
                tp = data.get("tariffPercent")
                if tp is not None:
                    tariff = float(tp)

        # Address resolved by Ozon's internal geocoder
        full_text = data.get("geocode", {}).get("fullText")
        if full_text:
            extra.append(ExtraField(
                label="Адрес (Ozon)",
                value=full_text,
                tooltip="Адрес, определённый внутренним геокодером Ozon",
            ))

        return MarketplaceResult(
            status=status,
            tariff=tariff,
            financial_support=financial_support,
            financial_support_label=financial_support_label,
            extra_fields=extra,
            raw=data,
        )
