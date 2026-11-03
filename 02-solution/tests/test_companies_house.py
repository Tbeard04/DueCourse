"""Companies House client against mocked (respx) responses — no network, no key."""

from datetime import date

import httpx
import respx

from duecourse.companies_house import BASE_URL, CompaniesHouseClient
from duecourse.models import FilingKind

PROFILE = {
    "company_number": "00000006",
    "company_name": "MARINE AND GENERAL MUTUAL LIFE ASSURANCE SOCIETY",
    "accounts": {
        "next_due": "2027-01-31",
        "overdue": False,
        "next_accounts": {"period_end_on": "2026-04-30"},
    },
    "confirmation_statement": {"next_due": "2026-11-20", "overdue": False},
}


@respx.mock
def test_deadlines_for(tmp_path) -> None:
    respx.get(f"{BASE_URL}/company/00000006").mock(return_value=httpx.Response(200, json=PROFILE))
    client = CompaniesHouseClient(api_key="test-key", cache_dir=tmp_path)
    deadlines = {d.kind: d for d in client.deadlines_for("00000006")}

    assert deadlines[FilingKind.ANNUAL_ACCOUNTS].due_date == date(2027, 1, 31)
    assert deadlines[FilingKind.ANNUAL_ACCOUNTS].period_end == date(2026, 4, 30)
    assert deadlines[FilingKind.CONFIRMATION_STATEMENT].due_date == date(2026, 11, 20)
    assert (tmp_path / "00000006.json").exists()  # raw response cached as a future fixture


@respx.mock
def test_missing_confirmation_statement(tmp_path) -> None:
    """Edge case: a company with no confirmation-statement record yet."""
    profile = {k: v for k, v in PROFILE.items() if k != "confirmation_statement"}
    respx.get(f"{BASE_URL}/company/00000006").mock(return_value=httpx.Response(200, json=profile))
    client = CompaniesHouseClient(api_key="test-key", cache_dir=tmp_path)
    kinds = {d.kind for d in client.deadlines_for("00000006")}
    assert kinds == {FilingKind.ANNUAL_ACCOUNTS}
