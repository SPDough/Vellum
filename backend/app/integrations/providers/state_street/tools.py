"""State Street provider tool scaffold."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.integrations.contracts import build_contract_result

from .client import StateStreetClient
from .mapping import StateStreetMapper


class StateStreetTools:
    def __init__(self, client: StateStreetClient):
        self.client = client
        self.mapper = StateStreetMapper()

    def _result_envelope(self, tool_name: str, contract_name: str, normalized_items: Optional[list] = None) -> Dict[str, Any]:
        contract_meta = self.mapper.get_contract_metadata(contract_name)
        return build_contract_result(
            provider_id='state_street',
            tool_name=tool_name,
            domain='custody',
            contract_name=contract_meta['contract_name'],
            contract_version=contract_meta['contract_version'],
            normalized_items=normalized_items or [],
            live_enabled=False,
            message='State Street live API not connected yet; this tool is wired to the canonical contract registry scaffold.',
            source_metadata={
                'provider_id': 'state_street',
                'contract_name': contract_meta['contract_name'],
                'contract_version': contract_meta['contract_version'],
            },
        )

    def get_positions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sample_record = {
            'entityId': 'ENTITY-001',
            'accountId': 'ACCOUNT-001',
            'securityId': 'SEC-ABC',
            'instrumentId': 'INST-ABC',
            'quantity': 1000,
            'currencyCode': 'USD',
            'positionDate': '2026-03-31',
            'status': 'OPEN',
        }
        normalized = self.mapper.map_position(sample_record)
        return self._result_envelope('get_positions', 'position', [normalized])

    def get_cash_activity(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sample_record = {
            'entityId': 'ENTITY-001',
            'ddaId': 'ACCOUNT-001',
            'transactionId': 'TXN-001',
            'transactionType': 'CASH_MOVEMENT',
            'transactionStatusCode': 'POSTED',
            'cashNetAmount': 250000.75,
            'currencyCodeLocal': 'USD',
            'createDatetime': '2026-03-31T10:15:00Z',
            'debitCreditCode': 'CR',
        }
        normalized = self.mapper.map_cash_activity(sample_record)
        return self._result_envelope('get_cash_activity', 'cash-activity', [normalized])

    def get_trade_status(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sample_record = {
            'entityId': 'ENTITY-001',
            'accountId': 'ACCOUNT-001',
            'tradeId': 'TRADE-001',
            'clientTradeId': 'CLIENT-TRADE-001',
            'securityId': 'SEC-ABC',
            'tradeDate': '2026-03-28',
            'settlementDate': '2026-03-31',
            'settlementStatus': 'SETTLED',
            'quantity': 1000,
            'price': 99.5,
            'currencyCode': 'USD',
        }
        normalized = self.mapper.map_trade_status(sample_record)
        return self._result_envelope('get_trade_status', 'trade-status', [normalized])
