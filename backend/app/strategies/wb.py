"""
Wildberries strategy.

API: https://pvz-map-backend.wildberries.ru/api/v2/map/check-point
Params: point.longitude, point.latitude, area, tariff_type
"""

from app.schemas import Coordinates, ExtraField, MarketplaceResult
from app.strategies.base import BaseStrategy

_WB_URL = "https://pvz-map-backend.wildberries.ru/api/v2/map/check-point"
_DEFAULT_AREA = 70
_DEFAULT_TARIFF_TYPE = "BasicTariff"


class WBStrategy(BaseStrategy):
    name = "wb"

    async def check(self, coords: Coordinates) -> MarketplaceResult:
        try:
            data = await self._get(
                _WB_URL,
                {
                    "point.longitude": coords.lon,
                    "point.latitude": coords.lat,
                    "area": _DEFAULT_AREA,
                    "tariff_type": _DEFAULT_TARIFF_TYPE,
                },
            )
        except Exception as exc:
            return self._error_result(exc)

        return self._parse(data)

    def _parse(self, data: dict) -> MarketplaceResult:
        can_open: bool = data.get("can_open", False)
        status = "approved" if can_open else "denied"

        tariff: float | None = None
        financial_support: int | None = None
        extra: list[ExtraField] = []

        point_info = data.get("point_info") or {}
        tariffs_info: list[dict] = point_info.get("tariffs_info") or []

        if tariffs_info:
            t = tariffs_info[0]
            tariff = t.get("total_tariff")
            financial_support = t.get("reward")

            base = t.get("base_tariff")
            bonus = t.get("bonus_tariff")
            profit = t.get("profit")

            if base is not None:
                extra.append(ExtraField(
                    label="Базовый тариф",
                    value=f"{base}%",
                    tooltip="Процент от оборота, начисляемый без учёта бонусов",
                ))
            if bonus:
                extra.append(ExtraField(
                    label="Бонусный тариф",
                    value=f"+{bonus}%",
                    tooltip="Дополнительный процент при выполнении условий WB",
                ))
            if profit is not None:
                extra.append(ExtraField(
                    label="Чистая прибыль",
                    value=f"{profit:,} ₽".replace(",", "\u00a0"),
                    tooltip="Расчётная прибыль партнёра в месяц после всех расходов (модель WB)",
                ))

        area_info = point_info.get("area_info") or {}
        min_area = area_info.get("min_area")
        if min_area is not None:
            extra.append(ExtraField(
                label="Мин. площадь",
                value=f"{min_area} м²",
                tooltip="Минимальная площадь помещения для открытия ПВЗ в этой зоне",
            ))

        zone = (point_info.get("zone_info") or {}).get("number_code")
        if zone is not None:
            extra.append(ExtraField(
                label="Тарифная зона",
                value=str(zone),
                tooltip="Внутренний номер тарифной зоны WB. Зона влияет на размер тарифа",
            ))

        return MarketplaceResult(
            status=status,
            tariff=tariff,
            financial_support=financial_support,
            financial_support_label="в месяц (вознаграждение)" if financial_support is not None else None,
            extra_fields=extra,
            raw=data,
        )
