"""State Street field mapping scaffold using spreadsheet-derived API hints."""

from __future__ import annotations

from typing import Any, Dict, List

from app.integrations.contracts.registry import get_contract_registry
from app.integrations.domain.custody import CustodyCashActivity, CustodyPosition, CustodyTradeStatus


class StateStreetMapper:
    def __init__(self):
        self.contract_registry = get_contract_registry()

    def get_contract_metadata(self, contract_name: str, version: str = '1.0.0') -> Dict[str, Any]:
        contract = self.contract_registry.get_contract(contract_name, version)
        return {
            'contract_name': contract.contract_name,
            'contract_version': contract.version,
            'schema': contract.schema,
            'dictionary': contract.dictionary,
            'fibo_alignment': contract.fibo_alignment,
        }

    @staticmethod
    def _clean_str(value: Any) -> str:
        if value is None:
            return ''
        return str(value).strip()

    @staticmethod
    def _coalesce(*values: Any) -> Any:
        for value in values:
            if value not in (None, '', []):
                return value
        return None

    def _quality_flags(self, payload: Dict[str, Any], required_fields: List[str]) -> List[str]:
        flags: List[str] = []
        for field in required_fields:
            value = payload.get(field)
            if value in (None, '', []):
                flags.append(f'missing:{field}')
        return flags

    def map_position(self, record: Dict[str, Any]) -> Dict[str, Any]:
        contract = self.get_contract_metadata('position')
        normalized = CustodyPosition(
            entity_id=self._coalesce(record.get('entityId'), record.get('entity_id')),
            account_id=self._coalesce(record.get('accountId'), record.get('account_id'), record.get('ddaId')),
            instrument_id=self._coalesce(record.get('instrumentId'), record.get('instrument_id')),
            security_id=self._coalesce(record.get('securityId'), record.get('security_id'), record.get('cusip'), record.get('isin')),
            quantity=self._coalesce(record.get('quantity'), record.get('positionQuantity')),
            currency=self._coalesce(record.get('currencyCode'), record.get('currencyCodeLocal'), record.get('currency')),
            position_date=self._coalesce(record.get('positionDate'), record.get('asOfDate'), record.get('businessDate')),
            status=self._coalesce(record.get('status'), record.get('positionStatus')),
            custodian='state_street',
            source_record=record,
        )
        payload = {
            'entity_id': self._clean_str(normalized.entity_id),
            'account_id': self._clean_str(normalized.account_id),
            'security_id': self._clean_str(normalized.security_id),
            'instrument_id': self._clean_str(normalized.instrument_id),
            'quantity': normalized.quantity or 0,
            'currency': self._clean_str(normalized.currency),
            'position_date': self._clean_str(normalized.position_date),
            'status': self._clean_str(normalized.status or 'UNKNOWN'),
        }
        return {
            'contract_type': contract['schema']['properties']['contract_type']['const'],
            'contract_version': contract['contract_version'],
            'source_system': 'state_street',
            'source_type': 'api',
            'source_record_id': self._clean_str(self._coalesce(record.get('positionId'), record.get('securityId'), record.get('instrumentId'))),
            'lineage': {
                'provider_id': 'state_street',
                'connector_class': 'api',
                'mapping_version': '1.0.0',
                'source_aliases_used': ['entityId', 'accountId', 'securityId', 'instrumentId', 'quantity', 'currencyCode', 'positionDate'],
            },
            'payload': payload,
            'data_quality_flags': self._quality_flags(payload, ['entity_id', 'account_id', 'security_id', 'quantity', 'currency', 'position_date']),
        }

    def map_cash_activity(self, record: Dict[str, Any]) -> Dict[str, Any]:
        contract = self.get_contract_metadata('cash-activity')
        normalized = CustodyCashActivity(
            transaction_id=self._coalesce(record.get('transactionId'), record.get('cashActivityId')),
            transaction_id_client=self._coalesce(record.get('transactionIdClient'), record.get('clientTransactionId')),
            create_datetime=self._coalesce(record.get('createDatetime'), record.get('effectiveDate'), record.get('businessDate')),
            cash_net_amount=self._coalesce(record.get('cashNetAmount'), record.get('transactionAmount'), record.get('amount')),
            currency_code_local=self._coalesce(record.get('currencyCodeLocal'), record.get('currencyCode'), record.get('currency')),
            debit_credit_code=self._coalesce(record.get('debitCreditCode'), record.get('debitCreditIndicator')),
            transaction_type=self._coalesce(record.get('transactionType'), record.get('activityType')),
            transaction_status_code=self._coalesce(record.get('transactionStatusCode'), record.get('statusCode'), record.get('status')),
            transaction_status_description=self._coalesce(record.get('transactionStatusDescription'), record.get('statusReason')),
            entity_id=self._coalesce(record.get('entityId'), record.get('entity_id')),
            dda_id=self._coalesce(record.get('ddaId'), record.get('accountId'), record.get('cashAccountId')),
            iban=self._coalesce(record.get('iban'), record.get('IBAN')),
            custodian='state_street',
            source_record=record,
        )
        effective_date = self._clean_str(normalized.create_datetime)[:10] if normalized.create_datetime else ''
        payload = {
            'entity_id': self._clean_str(normalized.entity_id),
            'account_id': self._clean_str(normalized.dda_id),
            'transaction_id': self._clean_str(normalized.transaction_id),
            'transaction_type': self._clean_str(normalized.transaction_type),
            'transaction_status': self._clean_str(normalized.transaction_status_code),
            'amount': normalized.cash_net_amount or 0,
            'currency': self._clean_str(normalized.currency_code_local),
            'effective_date': effective_date,
            'debit_credit_indicator': self._clean_str(normalized.debit_credit_code),
        }
        return {
            'contract_type': contract['schema']['properties']['contract_type']['const'],
            'contract_version': contract['contract_version'],
            'source_system': 'state_street',
            'source_type': 'api',
            'source_record_id': self._clean_str(normalized.transaction_id),
            'lineage': {
                'provider_id': 'state_street',
                'connector_class': 'api',
                'mapping_version': '1.0.0',
                'source_aliases_used': ['transactionId', 'transactionType', 'transactionStatusCode', 'cashNetAmount', 'currencyCodeLocal', 'createDatetime', 'ddaId', 'entityId'],
            },
            'payload': payload,
            'data_quality_flags': self._quality_flags(payload, ['entity_id', 'account_id', 'transaction_id', 'transaction_type', 'transaction_status', 'amount', 'currency', 'effective_date']),
        }

    def map_trade_status(self, record: Dict[str, Any]) -> Dict[str, Any]:
        contract = self.get_contract_metadata('trade-status')
        normalized = CustodyTradeStatus(
            trade_id=self._coalesce(record.get('tradeId'), record.get('transactionId')),
            client_trade_id=self._coalesce(record.get('clientTradeId'), record.get('transactionIdClient')),
            settlement_status=self._coalesce(record.get('settlementStatus'), record.get('transactionStatusCode'), record.get('status')),
            settlement_date=self._coalesce(record.get('settlementDate'), record.get('actualSettlementDate')),
            trade_date=self._coalesce(record.get('tradeDate'), record.get('executionDate'), record.get('businessDate')),
            security_id=self._coalesce(record.get('securityId'), record.get('instrumentId'), record.get('cusip'), record.get('isin')),
            counterparty_id=self._coalesce(record.get('counterpartyId'), record.get('brokerId')),
            quantity=self._coalesce(record.get('quantity'), record.get('tradeQuantity')),
            price=self._coalesce(record.get('price'), record.get('tradePrice')),
            currency=self._coalesce(record.get('currencyCode'), record.get('currency')),
            status_reason=self._coalesce(record.get('statusReason'), record.get('transactionStatusDescription')),
            custodian='state_street',
            source_record=record,
        )
        payload = {
            'entity_id': self._clean_str(self._coalesce(record.get('entityId'), record.get('entity_id'))),
            'account_id': self._clean_str(self._coalesce(record.get('accountId'), record.get('account_id'))),
            'trade_id': self._clean_str(normalized.trade_id),
            'client_trade_id': self._clean_str(normalized.client_trade_id),
            'security_id': self._clean_str(normalized.security_id),
            'trade_date': self._clean_str(normalized.trade_date),
            'settlement_date': self._clean_str(normalized.settlement_date),
            'settlement_status': self._clean_str(normalized.settlement_status),
            'quantity': normalized.quantity or 0,
            'price': normalized.price or 0,
            'currency': self._clean_str(normalized.currency),
        }
        return {
            'contract_type': contract['schema']['properties']['contract_type']['const'],
            'contract_version': contract['contract_version'],
            'source_system': 'state_street',
            'source_type': 'api',
            'source_record_id': self._clean_str(normalized.trade_id),
            'lineage': {
                'provider_id': 'state_street',
                'connector_class': 'api',
                'mapping_version': '1.0.0',
                'source_aliases_used': ['tradeId', 'clientTradeId', 'settlementStatus', 'tradeDate', 'settlementDate', 'securityId', 'quantity', 'price', 'currencyCode'],
            },
            'payload': payload,
            'data_quality_flags': self._quality_flags(payload, ['trade_id', 'security_id', 'trade_date', 'settlement_date', 'settlement_status']),
        }
