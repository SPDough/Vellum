"""Load and mutate procedure documents with PostgreSQL persistence."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procedure_document_row import ProcedureDocumentRow
from app.schemas.procedure_document import (
    ExceptionDecisionRequest,
    ExceptionDecisionResponse,
    ExceptionResolution,
    ProcedureDocument,
    SignoffRequest,
    SignoffResponse,
)


class ProcedureDocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_document(self, doc_id: str, seed: Dict[str, Any]) -> ProcedureDocument:
        async with self.session.begin():
            row = await self.session.get(ProcedureDocumentRow, doc_id)
            if row is None:
                if doc_id != seed["id"]:
                    raise HTTPException(
                        status_code=404, detail="Procedure document not found"
                    )
                payload = copy.deepcopy(seed)
                self.session.add(
                    ProcedureDocumentRow(
                        id=doc_id,
                        document_json=payload,
                        row_version=1,
                    )
                )
                return ProcedureDocument.model_validate(payload)
            return ProcedureDocument.model_validate(copy.deepcopy(row.document_json))

    async def decide_exception(
        self,
        doc_id: str,
        cell_id: str,
        payload: ExceptionDecisionRequest,
        decided_by: str,
    ) -> ExceptionDecisionResponse:
        async with self.session.begin():
            row = await self.session.get(ProcedureDocumentRow, doc_id)
            if row is None:
                raise HTTPException(
                    status_code=404, detail="Procedure document not found"
                )

            doc = copy.deepcopy(row.document_json)
            cell = self._get_cell_or_404_dict(doc, cell_id)
            if cell.get("cell_role") != "exception":
                raise HTTPException(status_code=400, detail="Cell is not an exception cell")

            option_ids = {o["id"] for o in cell.get("remediation_options", [])}
            if payload.option_id not in option_ids:
                raise HTTPException(status_code=400, detail="Unknown remediation option")

            resolution = {
                "option_id": payload.option_id,
                "rationale": payload.rationale,
                "decided_by": decided_by,
                "decided_at": datetime.now(timezone.utc).isoformat(),
            }
            cell["resolution"] = resolution
            row.document_json = doc
            row.row_version = row.row_version + 1

            return ExceptionDecisionResponse(
                cell_id=cell_id,
                resolution=ExceptionResolution(**resolution),
            )

    async def signoff_cell(
        self,
        doc_id: str,
        cell_id: str,
        _payload: SignoffRequest,
        signed_by: str,
    ) -> SignoffResponse:
        async with self.session.begin():
            row = await self.session.get(ProcedureDocumentRow, doc_id)
            if row is None:
                raise HTTPException(
                    status_code=404, detail="Procedure document not found"
                )

            doc = copy.deepcopy(row.document_json)
            cell = self._get_cell_or_404_dict(doc, cell_id)
            if cell.get("cell_role") != "signoff":
                raise HTTPException(status_code=400, detail="Cell is not a signoff cell")

            unresolved = [
                c
                for c in doc["cells"]
                if c.get("cell_role") == "exception" and not c.get("resolution")
            ]
            if unresolved:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot sign off while exceptions remain unresolved",
                )

            signed_at = datetime.now(timezone.utc).isoformat()
            cell["signed_by"] = signed_by
            cell["signed_at"] = signed_at
            doc["status"] = "signed"
            row.document_json = doc
            row.row_version = row.row_version + 1

            return SignoffResponse(
                cell_id=cell_id, signed_by=signed_by, signed_at=signed_at
            )

    @staticmethod
    def _get_cell_or_404_dict(doc: Dict[str, Any], cell_id: str) -> Dict[str, Any]:
        for cell in doc["cells"]:
            if cell["cell_id"] == cell_id:
                return cell
        raise HTTPException(status_code=404, detail="Cell not found")
