"""Equity pricing calculation pipeline.

Ported from drools/equity-pricing-rules.drl's calculation rules (Calculate
Market Price, Apply Liquidity Adjustment, Apply Volatility Adjustment, Fair
Value Price Calculation, Finalize Equity Price). This is arithmetic, not a
conditional trigger, so it lives here as plain Python rather than as a JSON
rule — the four boolean *alert* rules from that file (price variance, stale
data, zero/negative price, low confidence) still go through
app.rules.engine.RuleEngine against this module's output, tagged
"pricing_alerts".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

LIQUIDITY_VOLUME_THRESHOLD = 10_000
LIQUIDITY_DISCOUNT = 0.02
VOLATILITY_THRESHOLD = 0.30
VOLATILITY_DISCOUNT_FACTOR = 0.05
VOLATILITY_DISCOUNT_CAP = 0.10
FAIR_VALUE_HIGH_VOLUME_THRESHOLD = 100_000
FAIR_VALUE_PREMIUM = 1.01
FAIR_VALUE_STALE_MINUTES = 15
FAIR_VALUE_TIME_DISCOUNT_PER_MINUTE = 0.001
FAIR_VALUE_TIME_DISCOUNT_CAP = 0.05


@dataclass
class CalculatedPrice:
    request_id: str
    symbol: str
    base_price: float
    adjusted_price: float
    pricing_method: str
    confidence: float


def calculate_market_price(
    request_id: str,
    symbol: str,
    last_price: float,
    bid_price: Optional[float],
    ask_price: Optional[float],
    volume: int,
    volatility: float,
) -> CalculatedPrice:
    """Market-method pricing: mid of bid/ask (fallback to last price), then
    liquidity and volatility adjustments."""
    base_price = last_price
    if bid_price is not None and ask_price is not None:
        base_price = round((bid_price + ask_price) / 2, 4)

    adjusted_price = base_price
    confidence = 0.95

    if volume < LIQUIDITY_VOLUME_THRESHOLD:
        adjusted_price = round(adjusted_price * (1 - LIQUIDITY_DISCOUNT), 4)
        confidence -= 0.10

    if volatility > VOLATILITY_THRESHOLD:
        volatility_discount = min(volatility * VOLATILITY_DISCOUNT_FACTOR, VOLATILITY_DISCOUNT_CAP)
        adjusted_price = round(adjusted_price * (1 - volatility_discount), 4)

    return CalculatedPrice(
        request_id=request_id,
        symbol=symbol,
        base_price=base_price,
        adjusted_price=adjusted_price,
        pricing_method="MARKET",
        confidence=confidence,
    )


def calculate_fair_value_price(
    request_id: str,
    symbol: str,
    last_price: float,
    volume: int,
    market_data_timestamp: datetime,
    now: Optional[datetime] = None,
) -> CalculatedPrice:
    """Fair-value method pricing: volume premium plus a time-decay discount
    for stale market data."""
    now = now or datetime.now()
    fair_value_price = last_price

    if volume > FAIR_VALUE_HIGH_VOLUME_THRESHOLD:
        fair_value_price *= FAIR_VALUE_PREMIUM

    minutes_old = (now - market_data_timestamp).total_seconds() / 60
    if minutes_old > FAIR_VALUE_STALE_MINUTES:
        time_discount = min(minutes_old * FAIR_VALUE_TIME_DISCOUNT_PER_MINUTE, FAIR_VALUE_TIME_DISCOUNT_CAP)
        fair_value_price *= (1 - time_discount)

    return CalculatedPrice(
        request_id=request_id,
        symbol=symbol,
        base_price=last_price,
        adjusted_price=round(fair_value_price, 4),
        pricing_method="FAIR_VALUE",
        confidence=0.85,
    )


def build_pricing_alert_facts(
    calculated: CalculatedPrice,
    last_price: float,
    market_data_timestamp: datetime,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build the fact dict fed to RuleEngine.evaluate_rule_group("pricing_alerts", ...)."""
    now = now or datetime.now()
    variance_ratio = abs(calculated.adjusted_price - last_price) / last_price if last_price else 0.0
    data_age_minutes = (now - market_data_timestamp).total_seconds() / 60

    return {
        "pricing": {
            "request_id": calculated.request_id,
            "symbol": calculated.symbol,
            "calculated_price": calculated.adjusted_price,
            "confidence": calculated.confidence,
            "variance_ratio": round(variance_ratio, 4),
        },
        "market": {
            "data_age_minutes": round(data_age_minutes, 1),
        },
    }
