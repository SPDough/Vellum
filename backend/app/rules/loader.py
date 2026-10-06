"""Loader utilities for Vellum JSON-native deterministic rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .models import RuleDefinitionRecord

NON_RULE_FILES = {'schema.json', 'dictionary.json', 'fibo-alignment.json'}

# Coarse rule_family names that historically aliased a single legacy rule_id
# before this loader could scan a whole directory of rules per family.
LEGACY_FAMILY_ALIASES = {
    'custody': 'custody.unsettled_trade_aging',
}


class RuleLoader:
    """Loads versioned rule definitions from the repo-level contracts registry."""

    def __init__(self, rules_root: Optional[Path] = None):
        if rules_root is None:
            rules_root = Path(__file__).resolve().parents[3] / 'contracts' / 'rule-definition'
        self.rules_root = rules_root

    def load_rule(self, rule_family: str, version: str) -> RuleDefinitionRecord:
        index = self._scan_version(version)

        rule_path = index.get(rule_family)
        if rule_path is None:
            alias = LEGACY_FAMILY_ALIASES.get(rule_family)
            if alias:
                rule_path = index.get(alias)
        if rule_path is None:
            raise FileNotFoundError(f'Rule definition not indexed: {rule_family}/{version}')

        definition = self._read_json(rule_path)
        payload = definition.get('payload', {})

        return RuleDefinitionRecord(
            rule_family=payload.get('rule_family', rule_family),
            version=version,
            definition=definition,
            base_path=rule_path.parent,
        )

    def list_rule_ids_by_tag(self, tag: str, version: str) -> List[str]:
        index = self._scan_version(version)
        matches = []
        for rule_id, path in index.items():
            definition = self._read_json(path)
            payload = definition.get('payload', {})
            if payload.get('status') != 'active':
                continue
            if tag in (payload.get('tags') or []):
                matches.append(rule_id)
        return sorted(matches)

    def list_rule_definitions(self, version: str) -> List[RuleDefinitionRecord]:
        """List every rule definition in a version, for catalog/listing endpoints."""
        index = self._scan_version(version)
        records = []
        for rule_family, path in sorted(index.items()):
            definition = self._read_json(path)
            payload = definition.get('payload', {})
            records.append(
                RuleDefinitionRecord(
                    rule_family=payload.get('rule_family', rule_family),
                    version=version,
                    definition=definition,
                    base_path=path.parent,
                )
            )
        return records

    def list_rule_versions(self) -> Dict[str, str]:
        if not self.rules_root.exists():
            return {}
        return {
            version_dir.name: str(version_dir)
            for version_dir in sorted(self.rules_root.iterdir())
            if version_dir.is_dir()
        }

    def _scan_version(self, version: str) -> Dict[str, Path]:
        rule_dir = self.rules_root / version
        if not rule_dir.exists():
            raise FileNotFoundError(f'Rule definition version not found: {version}')

        index: Dict[str, Path] = {}
        for path in sorted(rule_dir.glob('*.json')):
            if path.name in NON_RULE_FILES:
                continue
            definition = self._read_json(path)
            rule_id = definition.get('payload', {}).get('rule_id')
            if rule_id:
                index[rule_id] = path
        return index

    @staticmethod
    def _read_json(path: Path):
        with path.open('r', encoding='utf-8') as fh:
            return json.load(fh)
