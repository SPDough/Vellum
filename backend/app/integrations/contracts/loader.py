"""Loader utilities for Vellum JSON contract registry files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .models import ContractDefinition


class ContractLoader:
    """Loads versioned contract definitions from the repo-level contracts registry."""

    def __init__(self, contracts_root: Optional[Path] = None):
        if contracts_root is None:
            contracts_root = Path(__file__).resolve().parents[4] / 'contracts'
        self.contracts_root = contracts_root

    def load_contract(self, contract_name: str, version: str) -> ContractDefinition:
        contract_dir = self.contracts_root / contract_name / version
        if not contract_dir.exists():
            raise FileNotFoundError(f'Contract not found: {contract_name}/{version}')

        schema = self._read_json(contract_dir / 'schema.json')
        dictionary = self._read_json(contract_dir / 'dictionary.json')
        fibo_path = contract_dir / 'fibo-alignment.json'
        fibo_alignment = self._read_json(fibo_path) if fibo_path.exists() else None

        return ContractDefinition(
            contract_name=contract_name,
            version=version,
            schema=schema,
            dictionary=dictionary,
            fibo_alignment=fibo_alignment,
            base_path=contract_dir,
        )

    def list_contract_versions(self, contract_name: str) -> Dict[str, Path]:
        contract_root = self.contracts_root / contract_name
        if not contract_root.exists():
            return {}
        return {
            version_dir.name: version_dir
            for version_dir in sorted(contract_root.iterdir())
            if version_dir.is_dir()
        }

    def list_contracts(self) -> Dict[str, Dict[str, Path]]:
        if not self.contracts_root.exists():
            return {}
        return {
            contract_dir.name: self.list_contract_versions(contract_dir.name)
            for contract_dir in sorted(self.contracts_root.iterdir())
            if contract_dir.is_dir()
        }

    @staticmethod
    def _read_json(path: Path):
        with path.open('r', encoding='utf-8') as fh:
            return json.load(fh)
