"""Normalized reference/master data records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SecurityMasterRecord:
    security_id: Optional[str] = None
    symbol: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    name: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountRecord:
    account_id: Optional[str] = None
    entity_id: Optional[str] = None
    account_name: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)
