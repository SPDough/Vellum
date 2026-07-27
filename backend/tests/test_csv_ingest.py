"""Tests for CSV position ingest (P1c)."""

from __future__ import annotations

import pytest

from app.oversight.csv_ingest import PositionCsvIngestError, parse_position_csv
from app.oversight.repository import InMemoryOversightRepository
from app.oversight.service import OversightService
from app.rules.engine import RuleEngine


SAMPLE_OMS = """entity_id,account_id,security_id,quantity,currency,position_date,market_value
ENT-ACME,ACCOUNT-001,SEC-ABC,1000,USD,2026-07-24,150000
ENT-ACME,ACCOUNT-001,SEC-XYZ,500,USD,2026-07-24,87500
"""

SAMPLE_ABOR = """entity_id,account_id,security_id,quantity,currency,position_date,market_value
ENT-ACME,ACCOUNT-001,SEC-ABC,900,USD,2026-07-24,135000
ENT-ACME,ACCOUNT-001,SEC-XYZ,500,USD,2026-07-24,91000
"""


def test_parse_position_csv_requires_columns():
    with pytest.raises(PositionCsvIngestError, match="missing required"):
        parse_position_csv("account_id,quantity\nA,1\n", book="oms")


@pytest.mark.asyncio
async def test_csv_ingest_slice_creates_breaks():
    service = OversightService(
        repository=InMemoryOversightRepository(), engine=RuleEngine()
    )
    snapshot = await service.run_csv_slice(SAMPLE_OMS, SAMPLE_ABOR)
    assert snapshot["summary"]["source"] == "csv_ingest"
    assert snapshot["summary"]["position_pairs"] == 2
    assert snapshot["summary"]["breaks"] >= 2
    reason_codes = {b["payload"]["reason_code"] for b in snapshot["breaks"]}
    assert "POSITION_QUANTITY_TOLERANCE_BREACH" in reason_codes
    assert "POSITION_VALUATION_MISMATCH" in reason_codes


@pytest.mark.asyncio
async def test_sample_csv_slice():
    service = OversightService(
        repository=InMemoryOversightRepository(), engine=RuleEngine()
    )
    snapshot = await service.run_sample_csv_slice()
    assert snapshot["summary"]["source"] == "csv_ingest"
    assert snapshot["summary"]["breaks"] >= 1
