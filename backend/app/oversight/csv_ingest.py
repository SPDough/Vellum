"""CSV ingest → Position-shaped rows for oversight (one real adapter path)."""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, TextIO


REQUIRED_COLUMNS = {
    "entity_id",
    "account_id",
    "security_id",
    "quantity",
    "currency",
    "position_date",
}


class PositionCsvIngestError(ValueError):
    pass


def parse_position_csv(
    content: str | bytes,
    *,
    book: str,
    source_system: str | None = None,
    custodian: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Parse a UTF-8 CSV of positions into fixture-compatible row dicts.

    Expected headers (case-sensitive):
      entity_id, account_id, security_id, quantity, currency, position_date
    Optional: instrument_id, market_value, status, source_record_id
    """
    if isinstance(content, bytes):
        text = content.decode("utf-8-sig")
    else:
        text = content.lstrip("\ufeff")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise PositionCsvIngestError("CSV has no header row")

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise PositionCsvIngestError(
            f"CSV missing required columns: {', '.join(sorted(missing))}"
        )

    rows: List[Dict[str, Any]] = []
    for index, raw in enumerate(reader, start=2):
        try:
            quantity = float(raw["quantity"])
        except (TypeError, ValueError) as exc:
            raise PositionCsvIngestError(
                f"Invalid quantity on row {index}: {raw.get('quantity')!r}"
            ) from exc

        market_value = None
        if raw.get("market_value") not in (None, ""):
            try:
                market_value = float(raw["market_value"])
            except (TypeError, ValueError) as exc:
                raise PositionCsvIngestError(
                    f"Invalid market_value on row {index}: {raw.get('market_value')!r}"
                ) from exc

        account_id = str(raw["account_id"]).strip()
        security_id = str(raw["security_id"]).strip()
        row: Dict[str, Any] = {
            "entity_id": str(raw["entity_id"]).strip(),
            "account_id": account_id,
            "security_id": security_id,
            "instrument_id": str(raw.get("instrument_id") or "").strip(),
            "quantity": quantity,
            "currency": str(raw["currency"]).strip() or "USD",
            "position_date": str(raw["position_date"]).strip(),
            "status": str(raw.get("status") or "open").strip(),
            "source_system": source_system or book,
            "source_record_id": str(
                raw.get("source_record_id") or f"csv-{book}-{account_id}-{security_id}"
            ).strip(),
        }
        if market_value is not None:
            row["market_value"] = market_value
        if custodian:
            row["custodian"] = custodian
        rows.append(row)

    if not rows:
        raise PositionCsvIngestError("CSV contained no data rows")
    return rows


def parse_position_csv_file(
    file_obj: TextIO,
    *,
    book: str,
    source_system: str | None = None,
    custodian: str | None = None,
) -> List[Dict[str, Any]]:
    content = file_obj.read()
    return parse_position_csv(
        content,
        book=book,
        source_system=source_system,
        custodian=custodian,
    )
