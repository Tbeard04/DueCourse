"""The drafting agent: one Pydantic AI agent, four tools, structured output.

Hard rules, enforced by design (see 05-handover/risk-register.md):
- Drafts are proposals. Nothing in this codebase can send email.
- Dates, deadlines and urgency come from injected structured data; the agent reads urgency
  through a tool, it never computes it.
- Every penalty figure or rule must carry a citation; rag.verify_citation checks every quote
  against the corpus (one retry with feedback, then unverifiable citations are dropped).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from . import llm, rag
from .companies_house import CompaniesHouseClient
from .models import Citation, ClientCompany, DraftEmail, TriageItem, TriageStatus
from .store import Store

SYSTEM_PROMPT = """\
You draft chasing emails for a UK accountancy practice, reminding client companies of
Companies House filing deadlines.

Rules:
- You are drafting a PROPOSAL for a human to review. Never claim an email was or will be sent.
- Use ONLY the dates, deadlines and day counts given by your tools. Never compute, adjust or
  restate a date that is not present in tool results.
- Every penalty amount or filing rule you mention MUST be quoted verbatim from search_guidance
  output, returned in `citations`. If you cannot find a rule in the guidance, do not state it.
- One clear ask per email. Professional, warm, concise; urgency proportionate to the day count.
- Sign off as "[Practice signature]" — the reviewer replaces it.
"""


class AgentDraft(BaseModel):
    """Structured output of the drafting agent."""

    subject: str
    body: str
    citations: list[Citation] = Field(default_factory=list)


@dataclass
class DraftDeps:
    item: TriageItem
    client: ClientCompany
    store: Store | None = None  # for the reviewer-feedback loop
    ch: CompaniesHouseClient | None = None  # for filing history context


def build_agent(model) -> Agent[DraftDeps, AgentDraft]:
    agent = Agent(
        model,
        deps_type=DraftDeps,
        output_type=AgentDraft,
        instructions=SYSTEM_PROMPT,
        retries=2,
    )

    @agent.instructions
    def reviewer_feedback(ctx: RunContext[DraftDeps]) -> str:
        """The visible improvement loop: recent rejection reasons feed the prompt."""
        if ctx.deps.store is None:
            return ""
        reasons = ctx.deps.store.recent_rejections(5)
        if not reasons:
            return ""
        bullets = "\n".join(f"- {reason}" for reason in reasons)
        return f"Reviewers recently rejected drafts for these reasons — avoid them:\n{bullets}"

    @agent.tool
    def days_until_due(ctx: RunContext[DraftDeps]) -> dict:
        """The deadline facts, computed deterministically — the only source of truth for dates."""
        item = ctx.deps.item
        return {
            "filing_kind": item.deadline.kind.value,
            "due_date": item.deadline.due_date.isoformat(),
            "days_until_due": item.days_until_due,
            "status": item.status.value,
            "as_of": item.as_of.isoformat(),
        }

    @agent.tool
    def get_client_context(ctx: RunContext[DraftDeps]) -> dict:
        """Who to address and any practice notes about this client."""
        client = ctx.deps.client
        return {
            "company_name": client.name,
            "contact_name": client.contact_name,
            "practice_notes": client.notes or "none",
        }

    @agent.tool
    def get_filings(ctx: RunContext[DraftDeps]) -> list[dict]:
        """Recent filing history, e.g. to acknowledge that last year was filed on time."""
        if ctx.deps.ch is None:
            return []
        events = ctx.deps.ch.get_filing_history(ctx.deps.item.deadline.company_number, items=5)
        return [
            {
                "filed_on": e.filed_on.isoformat(),
                "category": e.category,
                "description": e.description,
            }
            for e in events
        ]

    @agent.tool
    def search_guidance(ctx: RunContext[DraftDeps], query: str) -> list[dict]:
        """Official CH/HMRC guidance chunks — the only permitted source for rules and penalties."""
        try:
            chunks = rag.search(query)
        except rag.GuidanceUnavailable:
            return [
                {
                    "note": "guidance corpus not available — do not state any penalty figure"
                    " or filing rule in this draft"
                }
            ]
        return [
            {"text": c.text, "source_title": c.source_title, "source_url": c.source_url}
            for c in chunks
        ]

    return agent


def template_draft(item: TriageItem, client: ClientCompany) -> DraftEmail:
    """Deterministic, LLM-free fallback: correct facts, generic prose, no citations."""
    kind_label = item.deadline.kind.value.replace("_", " ")
    due = item.deadline.due_date.strftime("%d %B %Y")
    if item.status == TriageStatus.OVERDUE:
        urgency = (
            f"our records show this was due on {due} and is now overdue. "
            "Please send the outstanding information as soon as possible"
        )
    else:
        urgency = (
            f"this is due on {due} ({item.days_until_due} days from now). "
            "Please could you send over the information we need in good time"
        )
    body = (
        f"Dear {client.contact_name},\n\n"
        f"A quick reminder about the {kind_label} for {client.name}: {urgency}.\n\n"
        "If you've already sent everything across, please ignore this note.\n\n"
        "Best regards,\n[Practice signature]"
    )
    return DraftEmail(
        company_number=item.deadline.company_number,
        triage_item=item,
        subject=f"Reminder: {kind_label} for {client.name} — due {due}",
        body=body,
        citations=[],
        model_used="template",
        created_at=datetime.now(UTC),
    )


def _validated_citations(
    agent: Agent[DraftDeps, AgentDraft], deps: DraftDeps, result
) -> AgentDraft:
    """Verify every citation against the corpus; one retry with feedback, then drop invalid."""
    output: AgentDraft = result.output
    invalid = [c for c in output.citations if not rag.verify_citation(c)]
    if not invalid:
        return output
    quotes = "\n".join(f"- {c.quote!r}" for c in invalid)
    retry = agent.run_sync(
        "These quotes do not appear verbatim in the guidance corpus:\n"
        f"{quotes}\n"
        "Rewrite the draft quoting ONLY verbatim text returned by search_guidance, or remove"
        " the claims that rely on them.",
        deps=deps,
        message_history=result.all_messages(),
    )
    output = retry.output
    still_invalid = {c.quote for c in output.citations if not rag.verify_citation(c)}
    if still_invalid:
        output = output.model_copy(
            update={"citations": [c for c in output.citations if c.quote not in still_invalid]}
        )
    return output


def draft_for(
    item: TriageItem,
    client: ClientCompany,
    store: Store | None = None,
    ch: CompaniesHouseClient | None = None,
) -> DraftEmail:
    """Draft one chasing email: agent when a model is available, template otherwise."""
    model = llm.get_model("draft")
    if model is None:
        return template_draft(item, client)

    agent = build_agent(model)
    deps = DraftDeps(item=item, client=client, store=store, ch=ch)
    kind_label = item.deadline.kind.value.replace("_", " ")
    result = agent.run_sync(
        f"Draft the chasing email for {client.name} (company {item.deadline.company_number})"
        f" about its {kind_label}. Use your tools for every fact.",
        deps=deps,
    )
    output = _validated_citations(agent, deps, result)
    return DraftEmail(
        company_number=item.deadline.company_number,
        triage_item=item,
        subject=output.subject,
        body=output.body,
        citations=output.citations,
        model_used=llm.describe_model(model),
        created_at=datetime.now(UTC),
    )
