"""Typed domain models — the contract between every DueCourse module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class TriageStatus(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"  # due within 14 days
    UPCOMING = "upcoming"  # due within 30 days
    OK = "ok"


class FilingKind(StrEnum):
    CONFIRMATION_STATEMENT = "confirmation_statement"
    ANNUAL_ACCOUNTS = "annual_accounts"


class ClientCompany(BaseModel):
    """One row of the practice's portfolio (portfolio.json)."""

    company_number: str
    name: str
    contact_name: str
    contact_email: str  # fictional — never a real address
    notes: str = ""  # practice context the agent may use, e.g. "always late in January"


class Deadline(BaseModel):
    """One filing obligation, straight from the Companies House profile."""

    company_number: str
    kind: FilingKind
    due_date: date
    period_end: date | None = None  # accounts only
    overdue_per_api: bool = False  # CH's own overdue flag, kept for cross-checking


class TriageItem(BaseModel):
    """A Deadline plus computed urgency. Produced only by triage.py — never by an LLM."""

    deadline: Deadline
    status: TriageStatus
    days_until_due: int  # negative when overdue
    as_of: date


class Citation(BaseModel):
    quote: str  # verbatim text from a guidance chunk
    source_title: str
    source_url: str


class DraftEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_number: str
    triage_item: TriageItem
    subject: str
    body: str
    citations: list[Citation] = Field(default_factory=list)
    model_used: str  # provenance: model id, or "template"
    created_at: datetime


class ReviewDecision(BaseModel):
    draft_id: str
    action: Literal["approved", "edited", "rejected"]
    edited_body: str | None = None
    reason: str | None = None  # required when action == "rejected" (enforced in store)
    decided_at: datetime
