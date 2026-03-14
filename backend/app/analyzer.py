"""
Analyzer: runs all strategies in parallel and aggregates results.
To add a new marketplace, add its strategy to STRATEGIES.
"""

import asyncio

from app.schemas import Coordinates, MarketplaceResult
from app.strategies.ozon import OzonStrategy
from app.strategies.wb import WBStrategy
from app.strategies.yandex_market import YandexMarketStrategy

# Strategy registry. To add a new marketplace — just append here.
STRATEGIES = [
    OzonStrategy(),
    WBStrategy(),
    YandexMarketStrategy(),
]


async def analyze(coords: Coordinates) -> dict[str, MarketplaceResult]:
    """Returns a dict {strategy.name: MarketplaceResult}."""
    results: list[MarketplaceResult] = await asyncio.gather(
        *[strategy.check(coords) for strategy in STRATEGIES]
    )
    return {strategy.name: result for strategy, result in zip(STRATEGIES, results)}
