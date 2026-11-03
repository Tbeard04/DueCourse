"""SQLite persistence: portfolio, triage snapshots, drafts, and the append-only audit trail.

Schema lives in schema.sql (single source of truth), applied idempotently on open.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from .models import ClientCompany, DraftEmail, ReviewDecision, TriageItem

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema.sql"


class Store:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: pydantic-ai runs sync tools/instructions in worker threads,
        # and Streamlit reruns on fresh threads. Access is sequential by design; WAL mode on.
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # --- portfolio -------------------------------------------------------

    def upsert_client(self, client: ClientCompany) -> None:
        self._db.execute(
            "INSERT INTO clients VALUES (:company_number, :name, :contact_name, :contact_email,"
            " :notes) ON CONFLICT(company_number) DO UPDATE SET name=:name,"
            " contact_name=:contact_name, contact_email=:contact_email, notes=:notes",
            client.model_dump(),
        )
        self._db.commit()

    def prune_clients(self, keep: list[str]) -> int:
        """Remove clients no longer in the portfolio; returns how many were removed.

        portfolio.json is the source of truth — sync upserts its entries, then prunes the rest.
        Their past drafts and decisions stay: the audit trail is never deleted.
        """
        placeholders = ",".join("?" for _ in keep) or "''"
        cursor = self._db.execute(
            f"DELETE FROM clients WHERE company_number NOT IN ({placeholders})", keep
        )
        self._db.commit()
        return cursor.rowcount

    def clients(self) -> list[ClientCompany]:
        rows = self._db.execute("SELECT * FROM clients ORDER BY name").fetchall()
        return [ClientCompany(**dict(row)) for row in rows]

    def client(self, company_number: str) -> ClientCompany | None:
        row = self._db.execute(
            "SELECT * FROM clients WHERE company_number = ?", (company_number,)
        ).fetchone()
        return ClientCompany(**dict(row)) if row else None

    # --- runs ------------------------------------------------------------

    def start_run(self, kind: str, as_of: date) -> str:
        run_id = str(uuid.uuid4())
        self._db.execute(
            "INSERT INTO runs (id, kind, as_of_date, started_at) VALUES (?, ?, ?, ?)",
            (run_id, kind, as_of.isoformat(), datetime.now(UTC).isoformat()),
        )
        self._db.commit()
        return run_id

    def finish_run(self, run_id: str) -> None:
        self._db.execute(
            "UPDATE runs SET finished_at = ? WHERE id = ?",
            (datetime.now(UTC).isoformat(), run_id),
        )
        self._db.commit()

    # --- triage snapshots --------------------------------------------------

    def save_triage(self, run_id: str, items: list[TriageItem]) -> None:
        self._db.executemany(
            "INSERT INTO triage VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    run_id,
                    item.deadline.company_number,
                    item.deadline.kind.value,
                    item.deadline.due_date.isoformat(),
                    item.status.value,
                    item.days_until_due,
                )
                for item in items
            ],
        )
        self._db.commit()

    def latest_triage(self) -> list[TriageItem]:
        """The most recent triage snapshot, most urgent first."""
        run = self._db.execute(
            "SELECT id, as_of_date FROM runs WHERE kind = 'triage' AND finished_at IS NOT NULL"
            " ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if run is None:
            return []
        rows = self._db.execute(
            "SELECT * FROM triage WHERE run_id = ? ORDER BY days_until_due", (run["id"],)
        ).fetchall()
        return [
            TriageItem.model_validate(
                {
                    "deadline": {
                        "company_number": row["company_number"],
                        "kind": row["filing_kind"],
                        "due_date": row["due_date"],
                    },
                    "status": row["status"],
                    "days_until_due": row["days_until_due"],
                    "as_of": run["as_of_date"],
                }
            )
            for row in rows
        ]

    # --- drafts & decisions (the audit trail) --------------------------------

    def save_draft(self, run_id: str | None, draft: DraftEmail) -> None:
        self._db.execute(
            "INSERT INTO drafts (id, run_id, company_number, subject, body, citations_json,"
            " triage_json, model_used, created_at, state)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
            (
                draft.id,
                run_id,
                draft.company_number,
                draft.subject,
                draft.body,
                json.dumps([c.model_dump() for c in draft.citations]),
                draft.triage_item.model_dump_json(),
                draft.model_used,
                draft.created_at.isoformat(),
            ),
        )
        self._db.commit()

    def pending_drafts(self) -> list[DraftEmail]:
        rows = self._db.execute(
            "SELECT * FROM drafts WHERE state = 'pending' ORDER BY created_at"
        ).fetchall()
        return [
            DraftEmail(
                id=row["id"],
                company_number=row["company_number"],
                triage_item=json.loads(row["triage_json"]),
                subject=row["subject"],
                body=row["body"],
                citations=json.loads(row["citations_json"]),
                model_used=row["model_used"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def record_decision(self, decision: ReviewDecision) -> None:
        """Append-only: decisions are never updated or deleted."""
        if decision.action == "rejected" and not decision.reason:
            raise ValueError("a rejection requires a reason — it feeds next week's drafting")
        self._db.execute(
            "INSERT INTO decisions VALUES (?, ?, ?, ?, ?)",
            (
                decision.draft_id,
                decision.action,
                decision.edited_body,
                decision.reason,
                decision.decided_at.isoformat(),
            ),
        )
        self._db.execute("UPDATE drafts SET state = 'decided' WHERE id = ?", (decision.draft_id,))
        self._db.commit()

    def recent_rejections(self, n: int = 10) -> list[str]:
        """The latest rejection reasons — summarised into the drafting prompt (feedback loop)."""
        rows = self._db.execute(
            "SELECT reason FROM decisions WHERE action = 'rejected' AND reason IS NOT NULL"
            " ORDER BY decided_at DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [row["reason"] for row in rows]

    def decision_stats(self) -> dict[str, int]:
        rows = self._db.execute(
            "SELECT action, COUNT(*) AS n FROM decisions GROUP BY action"
        ).fetchall()
        return {row["action"]: row["n"] for row in rows}

    def close(self) -> None:
        self._db.close()
