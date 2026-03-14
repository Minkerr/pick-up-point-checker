"""
Yandex Market strategy.

API: https://hubs.market.yandex.ru/api/partner-gateway/outlet-map/point-available
Params: lat, lng, countryCode
"""

from app.schemas import Coordinates, ExtraField, MarketplaceResult
from app.strategies.base import BaseStrategy

_YM_URL = "https://hubs.market.yandex.ru/api/partner-gateway/outlet-map/point-available"

_SUBSIDY_TYPE_LABELS: dict[str, str] = {
    "SUBSIDY_WELLDONE": "Высокая субсидия (WellDone)",
    "SUBSIDY_MEDIUM":   "Средняя субсидия",
    "SUBSIDY_TOGETHER": "Совместная программа",
    "SUBSIDY_RARE":     "Субсидия за редкость зоны",
    "NO_SUBSIDY":       "Без субсидии",
    "NOT_DEFINED":      "Не определено",
}


class YandexMarketStrategy(BaseStrategy):
    name = "yandex_market"

    async def check(self, coords: Coordinates) -> MarketplaceResult:
        try:
            data = await self._get(
                _YM_URL,
                {"lat": coords.lat, "lng": coords.lon, "countryCode": "RU"},
            )
        except Exception as exc:
            return self._error_result(exc)

        return self._parse(data)

    def _parse(self, data: dict) -> MarketplaceResult:
        avail = data.get("availability") or {}
        tariff_code = avail.get("tariff", "NOT_DEFINED")

        if tariff_code == "SUBSIDY":
            status = "approved"
        else:
            status = "limited"

        financial_support: int | None = avail.get("additionalPayment") or None
        financial_support_label = "в месяц" if financial_support else None

        extra: list[ExtraField] = []

        subtype = avail.get("subsidyType")
        if subtype:
            extra.append(ExtraField(
                label="Тип субсидии",
                value=_SUBSIDY_TYPE_LABELS.get(subtype, subtype),
                tooltip="Программа субсидирования, действующая в этой зоне",
            ))

        target = avail.get("targetTurnover")
        if target:
            extra.append(ExtraField(
                label="Целевой оборот",
                value=f"{target:,} ₽".replace(",", "\u00a0"),
                tooltip="Минимальный оборот ПВЗ в месяц для получения полной субсидии",
            ))

        one_time = avail.get("oneTimePayment")
        if one_time:
            extra.append(ExtraField(
                label="Единоврем. выплата",
                value=f"{one_time:,} ₽".replace(",", "\u00a0"),
                tooltip="Разовая выплата при открытии ПВЗ",
            ))

        address = data.get("address")
        if address:
            extra.append(ExtraField(
                label="Адрес (ЯМ)",
                value=address,
                tooltip="Адрес, определённый геокодером Яндекс.Маркета",
            ))

        return MarketplaceResult(
            status=status,
            financial_support=financial_support,
            financial_support_label=financial_support_label,
            extra_fields=extra,
            raw=data,
        )
