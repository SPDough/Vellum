"""Standardized normalized result envelope helpers for provider-backed tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_contract_result(
    provider_id: str,
    tool_name: str,
    domain: str,
    contract_name: str,
    contract_version: str,
    normalized_items: Optional[List[Dict[str, Any]]] = None,
    live_enabled: bool = False,
    message: Optional[str] = None,
    next_cursor: Optional[str] = None,
    source_metadata: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    items = normalized_items or []
    return {
        'provider_id': provider_id,
        'tool_name': tool_name,
        'domain': domain,
        'contract_name': contract_name,
        'contract_version': contract_version,
        'normalized_items': items,
        'raw_count': len(items),
        'next_cursor': next_cursor,
        'source_metadata': source_metadata or {},
        'live_enabled': live_enabled,
        'message': message,
        'errors': errors or [],
    }
