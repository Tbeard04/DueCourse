"""Triage accuracy vs live Companies House ground truth.

For every item in the stored triage snapshot, re-fetch the live profile, recompute the
ground-truth status with the same pure function at the same as-of date, and exact-match.
Target 100%. Every miss is reported with a diagnosis — a due date that moved because the
company filed since the snapshot is a legitimate register change, not a triage bug, and the
report says which is which.

Run from 02-solution:  uv run python ../03-evals/triage_eval.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from _common import write_results

from duecourse.companies_house import CompaniesHouseClient
from duecourse.config import get_settings
from duecourse.store import Store
from duecourse.triage import triage


def main() -> int:
    store = Store(get_settings().db_path)
    snapshot = store.latest_triage()
    if not snapshot:
        sys.exit("No triage snapshot in the store — run: uv run duecourse triage")

    ch = CompaniesHouseClient()
    matches: list[dict] = []
    misses: list[dict] = []
    try:
        for item in snapshot:
            fresh = {d.kind: d for d in ch.deadlines_for(item.deadline.company_number)}
            truth_deadline = fresh.get(item.deadline.kind)
            record = {
                "company_number": item.deadline.company_number,
                "filing_kind": item.deadline.kind.value,
                "predicted_status": item.status.value,
                "predicted_days": item.days_until_due,
            }
            if truth_deadline is None:
                misses.append(
                    record
                    | {"diagnosis": "deadline no longer on the register (filed or data change)"}
                )
                continue
            truth = triage(truth_deadline, item.as_of)
            if truth.status == item.status and truth.days_until_due == item.days_until_due:
                matches.append(record)
            else:
                date_moved = truth_deadline.due_date != item.deadline.due_date
                misses.append(
                    record
                    | {
                        "truth_status": truth.status.value,
                        "truth_days": truth.days_until_due,
                        "snapshot_due": item.deadline.due_date.isoformat(),
                        "live_due": truth_deadline.due_date.isoformat(),
                        "diagnosis": (
                            "due date changed on the register since the snapshot"
                            " (company filed) — register change, not a triage bug"
                            if date_moved
                            else "same due date, different result — INVESTIGATE: triage bug"
                        ),
                    }
                )
    finally:
        ch.close()
        store.close()

    total = len(matches) + len(misses)
    accuracy = len(matches) / total if total else 0.0
    payload = {
        "ran_at": datetime.now(UTC).isoformat(),
        "as_of": snapshot[0].as_of.isoformat(),
        "deadlines_checked": total,
        "exact_matches": len(matches),
        "accuracy": round(accuracy, 4),
        "misses": misses,
    }
    path = write_results("triage_results.json", payload)

    print(f"Triage accuracy: {len(matches)}/{total} = {accuracy:.1%} (vs live API ground truth)")
    for miss in misses:
        print(f"  MISS {miss['company_number']} {miss['filing_kind']}: {miss['diagnosis']}")
    print(f"Full results -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
