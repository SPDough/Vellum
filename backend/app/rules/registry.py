"""In-memory registry facade for Vellum JSON-native deterministic rules."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict

from .loader import RuleLoader
from .models import RuleDefinitionRecord


class RuleRegistry:
    def __init__(self, loader: RuleLoader | None = None):
        self.loader = loader or RuleLoader()

    def get_rule(self, rule_family: str, version: str) -> RuleDefinitionRecord:
        return self.loader.load_rule(rule_family, version)

    def list_rule_versions(self) -> Dict[str, str]:
        return self.loader.list_rule_versions()


@lru_cache(maxsize=1)
def get_rule_registry() -> RuleRegistry:
    return RuleRegistry()
