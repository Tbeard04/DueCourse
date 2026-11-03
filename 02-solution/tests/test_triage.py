"""Boundary table for the deterministic triage — the module the risk register leans on."""

from datetime import date, timedelta

import pytest

from duecourse.models import Deadline, FilingKind, TriageStatus
from duecourse.triage import triage, triage_portfolio

TODAY = date(2026, 11, 10)


@pytest.mark.parametrize(
    ("days_until_due", "expected"),
    [
        (31, TriageStatus.OK),
        (30, TriageStatus.UPCOMING),
        (15, TriageStatus.UPCOMING),
        (14, TriageStatus.DUE_SOON),
        (1, TriageStatus.DUE_SOON),
        (0, TriageStatus.DUE_SOON),  # due today is urgent, not overdue
        (-1, TriageStatus.OVERDUE),
    ],
)
def test_triage_boundaries(days_until_due: int, expected: TriageStatus) -> None:
    deadline = Deadline(
        company_number="X",
        kind=FilingKind.ANNUAL_ACCOUNTS,
        due_date=TODAY + timedelta(days=days_until_due),
    )
    item = triage(deadline, TODAY)
    assert item.status == expected
    assert item.days_until_due == days_until_due
    assert item.as_of == TODAY


def test_portfolio_sorted_most_urgent_first() -> None:
    deadlines = [
        Deadline(
            company_number="A", kind=FilingKind.ANNUAL_ACCOUNTS, due_date=TODAY + timedelta(days=40)
        ),
        Deadline(
            company_number="B", kind=FilingKind.ANNUAL_ACCOUNTS, due_date=TODAY - timedelta(days=3)
        ),
        Deadline(
            company_number="C",
            kind=FilingKind.CONFIRMATION_STATEMENT,
            due_date=TODAY + timedelta(days=5),
        ),
    ]
    ordered = [item.deadline.company_number for item in triage_portfolio(deadlines, TODAY)]
    assert ordered == ["B", "C", "A"]
