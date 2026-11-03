from datetime import date

import pytest

from duecourse.models import ClientCompany, Deadline, FilingKind


@pytest.fixture
def deadline() -> Deadline:
    return Deadline(
        company_number="00000006",
        kind=FilingKind.CONFIRMATION_STATEMENT,
        due_date=date(2026, 12, 1),
    )


@pytest.fixture
def client_company() -> ClientCompany:
    return ClientCompany(
        company_number="00000006",
        name="Marine and General Mutual Life Assurance Society",
        contact_name="Alex Example",
        contact_email="alex@example.test",
        notes="prefers a phone call before month end",
    )
