"""The Monday-morning digest: a pure function over the store. No LLM."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from .models import TriageStatus
from .store import Store

STATUS_HEADINGS = {
    TriageStatus.OVERDUE: "🔴 Overdue",
    TriageStatus.DUE_SOON: "🟠 Due within 14 days",
    TriageStatus.UPCOMING: "🟡 Due within 30 days",
}


class DigestReport(BaseModel):
    as_of: date
    counts: dict[str, int]
    pending_drafts: int
    markdown: str


def build_digest(store: Store, as_of: date) -> DigestReport:
    items = store.latest_triage()
    pending = len(store.pending_drafts())
    counts = {status.value: 0 for status in TriageStatus}
    for item in items:
        counts[item.status.value] += 1

    lines = [
        f"# DueCourse weekly digest — {as_of.strftime('%A %d %B %Y')}",
        "",
        (
            f"**{counts['overdue']} overdue · {counts['due_soon']} due ≤14 days · "
            f"{counts['upcoming']} due ≤30 days** · {pending} drafts awaiting review"
        ),
        "",
    ]
    for status, heading in STATUS_HEADINGS.items():
        section = [item for item in items if item.status == status]
        if not section:
            continue
        lines += [f"## {heading}", ""]
        for item in section:
            client = store.client(item.deadline.company_number)
            name = client.name if client else item.deadline.company_number
            kind = item.deadline.kind.value.replace("_", " ")
            lines.append(
                f"- **{name}** — {kind} due {item.deadline.due_date.isoformat()}"
                f" ({item.days_until_due:+d} days)"
            )
        lines.append("")

    stats = store.decision_stats()
    if stats:
        lines += [
            "## Review activity",
            "",
            " · ".join(f"{count} {action}" for action, count in sorted(stats.items())),
            "",
        ]
    return DigestReport(
        as_of=as_of, counts=counts, pending_drafts=pending, markdown="\n".join(lines)
    )
