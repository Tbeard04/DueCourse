"""Agent contracts, tested offline with pydantic-ai's TestModel (no network, no key)."""

from datetime import date

from pydantic_ai.models.test import TestModel

from duecourse import llm
from duecourse.agent import AgentDraft, DraftDeps, build_agent, draft_for
from duecourse.triage import triage


def test_agent_produces_structured_draft(deadline, client_company) -> None:
    """All four tools register and the agent returns a valid AgentDraft."""
    item = triage(deadline, date(2026, 11, 25))
    agent = build_agent(TestModel())
    result = agent.run_sync(
        "Draft the chasing email.", deps=DraftDeps(item=item, client=client_company)
    )
    assert isinstance(result.output, AgentDraft)


def test_draft_for_falls_back_to_template(monkeypatch, deadline, client_company) -> None:
    """No provider configured -> deterministic template, stamped as such."""
    monkeypatch.setattr(llm, "get_model", lambda purpose="draft": None)
    item = triage(deadline, date(2026, 11, 25))
    draft = draft_for(item, client_company)
    assert draft.model_used == "template"
    assert client_company.contact_name in draft.body
    assert draft.citations == []
