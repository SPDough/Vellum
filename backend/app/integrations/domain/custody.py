"""Normalized custody-domain records used across providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CustodyPosition:
    account_id: Optional[str] = None
    entity_id: Optional[str] = None
    instrument_id: Optional[str] = None
    security_id: Optional[str] = None
    quantity: Optional[float] = None
    currency: Optional[str] = None
    position_date: Optional[str] = None
    custodian: Optional[str] = None
    status: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustodyCashActivity:
    transaction_id: Optional[str] = None
    transaction_id_client: Optional[str] = None
    create_datetime: Optional[str] = None
    cash_net_amount: Optional[float] = None
    currency_code_local: Optional[str] = None
    debit_credit_code: Optional[str] = None
    transaction_type: Optional[str] = None
    transaction_status_code: Optional[str] = None
    transaction_status_description: Optional[str] = None
    entity_id: Optional[str] = None
    dda_id: Optional[str] = None
    iban: Optional[str] = None
    custodian: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustodyTradeStatus:
    trade_id: Optional[str] = None
    client_trade_id: Optional[str] = None
    settlement_status: Optional[str] = None
    settlement_date: Optional[str] = None
    trade_date: Optional[str] = None
    security_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    status_reason: Optional[str] = None
    custodian: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)
