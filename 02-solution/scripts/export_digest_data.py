"""Export the latest triage snapshot as JSON for the Next.js digest frontend.

Writes web/data/digest.json — the build-time input for the statically exported site that
.github/workflows/publish-digest.yml publishes to GitHub Pages every Monday. Deliberately
contains only public register data (company names, filing kinds, due dates, urgency):
no contacts, no drafts, no LLM involved anywhere.

The checked-in digest.json is a fixture so `npm run build` works from a fresh clone;
CI regenerates it from the live register before every deploy.

Run from 02-solution:  uv run python scripts/export_digest_data.py [out_file]
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from duecourse.config import get_settings
from duecourse.models import TriageStatus
from duecourse.store import Store

SECTIONS = [
    (TriageStatus.OVERDUE, "Overdue", "overdue"),
    (TriageStatus.DUE_SOON, "Due within 14 days", "due-soon"),
    (TriageStatus.UPCOMING, "Due within 30 days", "upcoming"),
    (TriageStatus.OK, "On track", "ok"),
]


def main() -> int:
    out_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "web" / "data" / "digest.json"
    )
    store = Store(get_settings().db_path)
    items = store.latest_triage()
    if not items:
        sys.exit("No triage snapshot — run: uv run duecourse triage")
    names = {}
    for item in items:
        number = item.deadline.company_number
        if number not in names:
            client = store.client(number)
            names[number] = client.name if client else number
    store.close()

    as_of = items[0].as_of
    sections = [
        {
            "slug": slug,
            "label": label,
            "items": [
                {
                    "companyName": names[i.deadline.company_number],
                    "companyNumber": i.deadline.company_number,
                    "filing": i.deadline.kind.value.replace("_", " "),
                    "dueDate": i.deadline.due_date.isoformat(),
                    "daysUntilDue": i.days_until_due,
                }
                for i in items
                if i.status == status
            ],
        }
        for status, label, slug in SECTIONS
    ]
    digest = {
        # Dates preformatted here so the page renders identically at build and hydration.
        "asOf": as_of.strftime("%d %B %Y"),
        "generated": datetime.now(UTC).strftime("%A %d %B %Y, %H:%M UTC"),
        "portfolioSize": len(names),
        "sections": sections,
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(digest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_file} ({len(items)} deadlines, as of {as_of})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
