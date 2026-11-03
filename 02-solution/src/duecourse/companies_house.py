"""Live Companies House API client.

Auth: HTTP Basic with the API key as username, empty password. Documented rate limit is
600 requests / 5 minutes; 429s are retried with exponential backoff. Every raw response is
cached to data/cache/ — fixtures for tests, offline re-runs, and bounded API usage.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import get_settings
from .models import Deadline, FilingKind

BASE_URL = "https://api.company-information.service.gov.uk"


class RateLimited(Exception):
    """Raised on HTTP 429 so tenacity backs off and retries."""


class FilingEvent(BaseModel):
    """One entry of GET /company/{number}/filing-history."""

    filed_on: date
    category: str
    description: str


class CompanyProfile(BaseModel):
    """The slice of GET /company/{number} that DueCourse uses."""

    company_number: str
    company_name: str
    company_status: str = ""
    company_type: str = ""
    accounts_next_due: date | None = None
    accounts_period_end: date | None = None
    accounts_overdue: bool = False
    confirmation_statement_next_due: date | None = None
    confirmation_statement_overdue: bool = False

    @classmethod
    def from_api(cls, raw: dict) -> CompanyProfile:
        accounts = raw.get("accounts") or {}
        next_accounts = accounts.get("next_accounts") or {}
        confirmation = raw.get("confirmation_statement") or {}
        return cls(
            company_number=raw["company_number"],
            company_name=raw.get("company_name", ""),
            company_status=raw.get("company_status", ""),
            company_type=raw.get("type", ""),
            accounts_next_due=accounts.get("next_due"),
            accounts_period_end=next_accounts.get("period_end_on"),
            accounts_overdue=bool(accounts.get("overdue", False)),
            confirmation_statement_next_due=confirmation.get("next_due"),
            confirmation_statement_overdue=bool(confirmation.get("overdue", False)),
        )


class CompaniesHouseClient:
    def __init__(self, api_key: str | None = None, cache_dir: Path | None = None):
        settings = get_settings()
        key = api_key if api_key is not None else settings.ch_api_key
        if not key:
            raise ValueError("CH_API_KEY is not set — get a free key, see .env.example")
        self.cache_dir = cache_dir if cache_dir is not None else settings.cache_dir
        self._http = httpx.Client(base_url=BASE_URL, auth=(key, ""), timeout=30)

    @retry(
        retry=retry_if_exception_type((RateLimited, httpx.TransportError)),
        wait=wait_exponential(multiplier=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _get(self, path: str, params: dict | None = None) -> dict:
        response = self._http.get(path, params=params)
        if response.status_code == 429:
            raise RateLimited(path)
        response.raise_for_status()
        return response.json()

    def _cache(self, name: str, raw: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {"fetched_at": datetime.now(UTC).isoformat(), "data": raw}
        (self.cache_dir / f"{name}.json").write_text(json.dumps(payload, indent=2))

    def search_advanced(
        self,
        *,
        sic_codes: str | None = None,
        incorporated_from: str | None = None,
        incorporated_to: str | None = None,
        company_status: str = "active",
        size: int = 100,
    ) -> list[dict]:
        """GET /advanced-search/companies — raw result items (used by the portfolio builder)."""
        params: dict = {"company_status": company_status, "size": size}
        if sic_codes:
            params["sic_codes"] = sic_codes
        if incorporated_from:
            params["incorporated_from"] = incorporated_from
        if incorporated_to:
            params["incorporated_to"] = incorporated_to
        return self._get("/advanced-search/companies", params=params).get("items", [])

    def get_company_profile(self, company_number: str) -> CompanyProfile:
        raw = self._get(f"/company/{company_number}")
        self._cache(company_number, raw)
        return CompanyProfile.from_api(raw)

    def get_filing_history(self, company_number: str, items: int = 10) -> list[FilingEvent]:
        raw = self._get(
            f"/company/{company_number}/filing-history", params={"items_per_page": items}
        )
        return [
            FilingEvent(
                filed_on=entry["date"],
                category=entry.get("category", ""),
                description=entry.get("description", ""),
            )
            for entry in raw.get("items", [])
            if "date" in entry
        ]

    def deadlines_for(self, company_number: str) -> list[Deadline]:
        """Derive the Deadline objects from the live profile — the system's ground truth.

        Edge cases to handle and test (see SPEC §6): extended/shortened accounting periods,
        dormant companies, no confirmation-statement record yet, dissolved companies.
        """
        profile = self.get_company_profile(company_number)
        deadlines: list[Deadline] = []
        if profile.accounts_next_due is not None:
            deadlines.append(
                Deadline(
                    company_number=company_number,
                    kind=FilingKind.ANNUAL_ACCOUNTS,
                    due_date=profile.accounts_next_due,
                    period_end=profile.accounts_period_end,
                    overdue_per_api=profile.accounts_overdue,
                )
            )
        if profile.confirmation_statement_next_due is not None:
            deadlines.append(
                Deadline(
                    company_number=company_number,
                    kind=FilingKind.CONFIRMATION_STATEMENT,
                    due_date=profile.confirmation_statement_next_due,
                    overdue_per_api=profile.confirmation_statement_overdue,
                )
            )
        return deadlines

    def close(self) -> None:
        self._http.close()
