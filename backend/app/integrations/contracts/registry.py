"""In-memory contract registry facade for Vellum JSON data contracts."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict

from .loader import ContractLoader
from .models import ContractDefinition


class ContractRegistry:
    def __init__(self, loader: ContractLoader | None = None):
        self.loader = loader or ContractLoader()

    def get_contract(self, contract_name: str, version: str) -> ContractDefinition:
        return self.loader.load_contract(contract_name, version)

    def list_contracts(self) -> Dict[str, Dict[str, str]]:
        listing = self.loader.list_contracts()
        return {
            contract_name: {version: str(path) for version, path in versions.items()}
            for contract_name, versions in listing.items()
        }


@lru_cache(maxsize=1)
def get_contract_registry() -> ContractRegistry:
    return ContractRegistry()
