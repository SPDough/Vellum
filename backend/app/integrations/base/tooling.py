"""Generic tool metadata for integration providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class IntegrationTool:
    """Describes a generic tool exposed by an integration provider."""

    name: str
    description: str
    input_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
