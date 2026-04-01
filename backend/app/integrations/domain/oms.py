"""Normalized OMS domain records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class OmsOrder:
    order_id: Optional[str] = None
    account_id: Optional[str] = None
    security_id: Optional[str] = None
    side: Optional[str] = None
    quantity: Optional[float] = None
    status: Optional[str] = None
    source_record: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OmsExecution:
    execution_id: Optional[str] = None
    order_id: Optional[str] = None
    execution_status: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    source_record: Dict[str, Any] = field(default_factory=dict)
