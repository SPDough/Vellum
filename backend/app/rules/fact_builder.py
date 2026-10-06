"""Builds RuleEngine fact dicts from the camelCase data shapes callers
already send (the same shapes DroolsService.RuleFact used), so API routes,
LangGraph nodes, and the frontend don't need to change their request
payloads for the Drools -> native rules engine migration.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional

from app.services import pricing_service

from . import derived_facts

_CAMEL_BOUNDARY = re.compile(r'(?<!^)(?=[A-Z])')


def camel_to_snake(key: str) -> str:
    return _CAMEL_BOUNDARY.sub('_', key).lower()


def to_snake_dict(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {camel_to_snake(key): value for key, value in (data or {}).items()}


def build_trade_validation_facts(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    trade = to_snake_dict(trade_data)
    return {'trade': trade, 'derived': derived_facts.build_trade_validation_derived(trade)}


def build_risk_management_facts(
    trade_data: Dict[str, Any],
    portfolio_data: Dict[str, Any],
    same_day_trade_count: int = 0,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    trade = to_snake_dict(trade_data)
    portfolio = to_snake_dict(portfolio_data)
    return {
        'trade': trade,
        'portfolio': portfolio,
        'derived': derived_facts.build_risk_management_derived(trade, portfolio, same_day_trade_count, now),
    }


def build_compliance_facts(
    trade_data: Dict[str, Any],
    client_data: Dict[str, Any],
    now=None,
) -> Dict[str, Any]:
    trade = to_snake_dict(trade_data)
    client = to_snake_dict(client_data)
    return {'trade': trade, 'client': client, 'derived': derived_facts.build_compliance_derived(client, now)}


def build_settlement_facts(
    trade_data: Dict[str, Any],
    settlement_data: Dict[str, Any],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    trade = to_snake_dict(trade_data)
    settlement = to_snake_dict(settlement_data)
    return {
        'trade': trade,
        'settlement': settlement,
        'derived': derived_facts.build_settlement_derived(trade, settlement, now),
    }


def build_pricing_alert_facts(
    equity_request_data: Dict[str, Any],
    market_data: Dict[str, Any],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Runs the pricing calculation pipeline against raw EquityPricingRequest
    + MarketData facts, then builds the pricing_alerts fact dict from its
    output."""
    request = to_snake_dict(equity_request_data)
    market = to_snake_dict(market_data)
    now = now or datetime.now()

    market_timestamp_raw = market.get('timestamp')
    market_timestamp = (
        datetime.fromisoformat(str(market_timestamp_raw)) if market_timestamp_raw else now
    )
    last_price = float(market.get('last_price', request.get('market_data_price', 0)) or 0)
    symbol = request.get('symbol') or market.get('symbol', '')
    request_id = request.get('request_id', 'unknown')

    if request.get('pricing_method') == 'FAIR_VALUE':
        calculated = pricing_service.calculate_fair_value_price(
            request_id=request_id,
            symbol=symbol,
            last_price=last_price,
            volume=int(market.get('volume', 0) or 0),
            market_data_timestamp=market_timestamp,
            now=now,
        )
    else:
        calculated = pricing_service.calculate_market_price(
            request_id=request_id,
            symbol=symbol,
            last_price=last_price,
            bid_price=market.get('bid_price'),
            ask_price=market.get('ask_price'),
            volume=int(market.get('volume', 0) or 0),
            volatility=float(market.get('volatility', 0) or 0),
        )

    return pricing_service.build_pricing_alert_facts(
        calculated, last_price=last_price, market_data_timestamp=market_timestamp, now=now
    )
