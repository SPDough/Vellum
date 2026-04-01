"""Loader utilities for Vellum JSON-native deterministic rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .models import RuleDefinitionRecord


class RuleLoader:
    """Loads versioned rule definitions from the repo-level contracts registry."""

    RULE_INDEX = {
        ('custody', '1.0.0'): 'example.json',
        ('custody.cash_activity_value_date_breach', '1.0.0'): 'cash_activity_value_date_breach.json',
        ('reconciliation.position_quantity_tolerance_breach', '1.0.0'): 'position_quantity_tolerance_breach.json',
    }

    def __init__(self, rules_root: Optional[Path] = None):
        if rules_root is None:
            rules_root = Path(__file__).resolve().parents[3] / 'contracts' / 'rule-definition'
        self.rules_root = rules_root

    def load_rule(self, rule_family: str, version: str) -> RuleDefinitionRecord:
        rule_dir = self.rules_root / version
        if not rule_dir.exists():
            raise FileNotFoundError(f'Rule definition version not found: {version}')

        filename = self.RULE_INDEX.get((rule_family, version))
        if filename is None:
            raise FileNotFoundError(f'Rule definition not indexed: {rule_family}/{version}')

        rule_path = rule_dir / filename
        if not rule_path.exists():
            raise FileNotFoundError(f'Rule definition file not found: {rule_path}')

        definition = self._read_json(rule_path)
        payload = definition.get('payload', {})
        loaded_rule_family = payload.get('rule_family', rule_family)

        return RuleDefinitionRecord(
            rule_family=loaded_rule_family,
            version=version,
            definition=definition,
            base_path=rule_dir,
        )

    def list_rule_versions(self) -> Dict[str, str]:
        if not self.rules_root.exists():
            return {}
        return {
            version_dir.name: str(version_dir)
            for version_dir in sorted(self.rules_root.iterdir())
            if version_dir.is_dir()
        }

    @staticmethod
    def _read_json(path: Path):
        with path.open('r', encoding='utf-8') as fh:
            return json.load(fh)
