"""Deterministic deadline triage.

No LLM anywhere in this module — this is the property the risk register leans on. The thresholds
below are quoted in 05-handover/runbook.md; change them in both places or not at all.
"""

from datetime import date

from .models import Deadline, TriageItem, TriageStatus

DUE_SOON_DAYS = 14
UPCOMING_DAYS = 30


def triage(deadline: Deadline, today: date) -> TriageItem:
    """Pure function: date arithmetic -> urgency. `today` is a parameter, never date.today()."""
    days = (deadline.due_date - today).days
    if days < 0:
        status = TriageStatus.OVERDUE
    elif days <= DUE_SOON_DAYS:
        status = TriageStatus.DUE_SOON
    elif days <= UPCOMING_DAYS:
        status = TriageStatus.UPCOMING
    else:
        status = TriageStatus.OK
    return TriageItem(deadline=deadline, status=status, days_until_due=days, as_of=today)


def triage_portfolio(deadlines: list[Deadline], today: date) -> list[TriageItem]:
    """Triage every deadline, most urgent first."""
    return sorted(
        (triage(d, today) for d in deadlines),
        key=lambda item: item.days_until_due,
    )
