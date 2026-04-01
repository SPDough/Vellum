"""Normalized fund accounting domain records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class FundNavRecord:
    entity_id: Optional[str] = None
    nav_date: Optional[str] = None
    nav_value: Optional[float] = None
    currency: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountingPosition:
    entity_id: Optional[str] = None
    security_id: Optional[str] = None
    quantity: Optional[float] = None
    market_value: Optional[float] = None
    source_record: Dict[str, Any] = field(default_factory=dict)
