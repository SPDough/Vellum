"""Models for the lightweight Vellum contract registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ContractDefinition:
    contract_name: str
    version: str
    schema: Dict[str, Any]
    dictionary: Dict[str, Any]
    fibo_alignment: Optional[Dict[str, Any]]
    base_path: Path
