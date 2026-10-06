"""Pure Python helpers that compute the `derived.*` facts the ported rules
need, replacing the Java helper functions and date/time logic that used to
live inside drools/custodian-banking-rules.drl.

These take plain data (dicts, dates, numbers) rather than ORM objects, so
they stay unit-testable without a database.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

SANCTIONED_COUNTRIES = {"IR", "KP", "SY", "CU"}
MARKET_OPEN_HOUR = 9
MARKET_CLOSE_HOUR = 16
BUSINESS_HOURS_START = 8
BUSINESS_HOURS_END = 17


def _as_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def is_sanctioned_country(country_code: Optional[str]) -> bool:
    return bool(country_code) and country_code in SANCTIONED_COUNTRIES


def has_pending_corporate_action(security_id: Optional[str]) -> bool:
    """Stub, matching drools' hasPendingCorporateAction — always False until
    a real corporate-actions data source is wired up."""
    return False


def is_market_open(now: Optional[datetime] = None) -> bool:
    hour = (now or datetime.now()).hour
    return MARKET_OPEN_HOUR <= hour <= MARKET_CLOSE_HOUR


def is_outside_business_hours(now: Optional[datetime] = None) -> bool:
    hour = (now or datetime.now()).hour
    return hour >= BUSINESS_HOURS_END or hour <= BUSINESS_HOURS_START


def get_security_exposure(portfolio: Dict[str, Any], security_id: str) -> float:
    exposures = portfolio.get("security_exposures") or {}
    return float(exposures.get(security_id, 0))


def build_trade_validation_derived(trade: Dict[str, Any]) -> Dict[str, Any]:
    trade_date = _as_date(trade.get("trade_date"))
    settlement_date = _as_date(trade.get("settlement_date"))
    return {
        "settlement_before_trade_date": bool(
            trade_date and settlement_date and settlement_date < trade_date
        ),
        "settlement_is_weekend": bool(settlement_date and settlement_date.weekday() >= 5),
    }


def build_risk_management_derived(
    trade: Dict[str, Any],
    portfolio: Dict[str, Any],
    same_day_trade_count: int = 0,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    total_exposure = float(portfolio.get("total_exposure", 0))
    trade_value = float(trade.get("trade_value", 0))
    return {
        "projected_exposure": total_exposure + trade_value,
        "security_exposure": get_security_exposure(portfolio, trade.get("security_id")),
        "is_outside_business_hours": is_outside_business_hours(now),
        "same_day_trade_count": same_day_trade_count,
        "is_market_open": is_market_open(now),
    }


def build_compliance_derived(client: Dict[str, Any], now: Optional[date] = None) -> Dict[str, Any]:
    last_review_date = _as_date(client.get("last_review_date"))
    cutoff = (now or date.today()) - timedelta(days=365)
    return {
        "is_sanctioned_country": is_sanctioned_country(client.get("country_code")),
        "kyc_review_stale": bool(last_review_date and last_review_date < cutoff),
    }


def build_settlement_derived(
    trade: Dict[str, Any],
    settlement: Dict[str, Any],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    cutoff_time = settlement.get("cutoff_time")
    past_cutoff = False
    if cutoff_time:
        cutoff_dt = cutoff_time if isinstance(cutoff_time, datetime) else datetime.fromisoformat(str(cutoff_time))
        past_cutoff = (now or datetime.now()) > cutoff_dt
    return {
        "past_cutoff_time": past_cutoff,
        "has_pending_corporate_action": has_pending_corporate_action(trade.get("security_id")),
    }
