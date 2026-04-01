"""Pagination primitives for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar('T')


@dataclass
class CursorPage(Generic[T]):
    items: List[T]
    next_cursor: Optional[str] = None


@dataclass
class OffsetPage(Generic[T]):
    items: List[T]
    offset: int = 0
    limit: int = 0
    total: Optional[int] = None
