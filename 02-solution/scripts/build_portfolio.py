"""Build the 60-company demo portfolio (portfolio.json).

Picks real, active UK private limited companies from the Companies House advanced-search
endpoint — spread across sectors and incorporation months so filing due dates stagger
realistically through the year — then attaches FICTIONAL practice contacts (seeded RNG,
@example.test addresses). Never real people, never real addresses.

Deterministic given the same API results (seeded with SEED), and committed as
portfolio.json so the demo portfolio is inspectable and reproducible.

Run from 02-solution:  uv run python scripts/build_portfolio.py
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from duecourse.companies_house import CompaniesHouseClient

SEED = 42
TARGET = 60
MAX_PER_DUE_MONTH = 8  # force a realistic stagger of accounts due dates
# Keep recently-missed deadlines (realistic for a practice) but exclude zombie companies that
# are years overdue and heading for strike-off — no practice has those as paying clients.
MAX_OVERDUE_DAYS = 90

# A believable small-practice client mix: trades, hospitality, consultancies, online retail.
SIC_CODES = ["62020", "70229", "56101", "43210", "96020", "47910", "86230", "81210"]

# One incorporation window per quarter across several years: accounting reference dates
# usually track the incorporation month, so this staggers the due dates.
INCORPORATION_WINDOWS = [
    ("2015-02-01", "2015-04-30"),
    ("2016-05-01", "2016-07-31"),
    ("2017-08-01", "2017-10-31"),
    ("2018-11-01", "2019-01-31"),
    ("2020-02-01", "2020-04-30"),
    ("2021-05-01", "2021-07-31"),
    ("2022-08-01", "2022-10-31"),
    ("2023-11-01", "2024-01-31"),
]

FIRST_NAMES = [
    "Priya",
    "James",
    "Amara",
    "Tom",
    "Sofia",
    "Daniel",
    "Grace",
    "Omar",
    "Ellie",
    "Marcus",
    "Hannah",
    "Kwame",
    "Lucy",
    "Ravi",
    "Megan",
    "Callum",
    "Zara",
    "Patrick",
    "Nadia",
    "Owen",
]
LAST_NAMES = [
    "Patel",
    "Hughes",
    "Okafor",
    "Williams",
    "Rossi",
    "Clarke",
    "Thompson",
    "Hassan",
    "Price",
    "Johnson",
    "Murray",
    "Mensah",
    "Barnes",
    "Sharma",
    "Evans",
    "Doyle",
    "Ahmed",
    "Kelly",
    "Nowak",
    "Griffiths",
]
NOTES = [
    "",
    "",
    "",
    "",
    "",  # most clients have no special notes
    "prefers a phone call before month end",
    "always late with records in January",
    "sends records as paper bundles — allow extra time",
    "new client this year — first filing cycle with us",
    "director travels a lot; email the bookkeeper too",
]


def fictional_contact(rng: random.Random) -> tuple[str, str]:
    first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    return f"{first} {last}", f"{first.lower()}.{last.lower()}@example.test"


def main() -> int:
    rng = random.Random(SEED)
    ch = CompaniesHouseClient()
    try:
        # 1) Candidates: one sector x one incorporation window per (code, window) pair.
        candidates: list[str] = []
        seen: set[str] = set()
        for sic, (start, end) in zip(SIC_CODES, INCORPORATION_WINDOWS, strict=True):
            items = ch.search_advanced(sic_codes=sic, incorporated_from=start, incorporated_to=end)
            numbers = [
                item["company_number"]
                for item in items
                if item.get("company_type", "ltd") == "ltd" and item.get("company_number")
            ]
            rng.shuffle(numbers)
            for number in numbers[:30]:
                if number not in seen:
                    seen.add(number)
                    candidates.append(number)
        print(f"{len(candidates)} candidates from {len(SIC_CODES)} sector/vintage searches")

        # 2) Keep companies with live deadlines, capping each accounts-due month for stagger.
        rng.shuffle(candidates)
        portfolio: list[dict] = []
        month_load: Counter[int] = Counter()
        for number in candidates:
            if len(portfolio) >= TARGET:
                break
            profile = ch.get_company_profile(number)
            if profile.company_status != "active" or profile.company_type != "ltd":
                continue
            if profile.accounts_next_due is None or profile.confirmation_statement_next_due is None:
                continue
            oldest_allowed = date.today() - timedelta(days=MAX_OVERDUE_DAYS)
            if (
                min(profile.accounts_next_due, profile.confirmation_statement_next_due)
                < oldest_allowed
            ):
                continue
            month = profile.accounts_next_due.month
            if month_load[month] >= MAX_PER_DUE_MONTH:
                continue
            month_load[month] += 1
            contact_name, contact_email = fictional_contact(rng)
            portfolio.append(
                {
                    "company_number": profile.company_number,
                    "name": profile.company_name,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "notes": rng.choice(NOTES),
                }
            )

        if len(portfolio) < TARGET:
            print(f"WARNING: only {len(portfolio)} of {TARGET} companies qualified")
        portfolio.sort(key=lambda entry: entry["name"])
        Path("portfolio.json").write_text(
            json.dumps(portfolio, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        months = ", ".join(f"{m:02d}:{n}" for m, n in sorted(month_load.items()))
        print(f"Wrote portfolio.json with {len(portfolio)} companies")
        print(f"Accounts-due month spread -> {months}")
        return 0
    finally:
        ch.close()


if __name__ == "__main__":
    sys.exit(main())
