"""The drafting agent: one Pydantic AI agent, four tools, structured output.

Hard rules, enforced by design (see 05-handover/risk-register.md):
- Drafts are proposals. Nothing in this codebase can send email.
- Dates, deadlines and urgency come from injected structured data; the agent reads urgency
  through a tool, it never computes it.
- Every penalty figure or rule must carry a citation; rag.verify_citation rejects drafts whose
  quotes don't match the corpus (one retry, then flagged needs_attention).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel

from . import llm
from .models import Citation, ClientCompany, DraftEmail, TriageItem, TriageStatus

SYSTEM_PROMPT = """\
You draft chasing emails for a UK accountancy practice, reminding client companies of
Companies House filing deadlines.

Rules:
- You are drafting a PROPOSAL for a human to review. Never claim an email was or will be sent.
- Use ONLY the dates, deadlines and day counts given by your tools. Never compute, adjust or
  restate a date that is not present in tool results.
- Every penalty amount or filing rule you mention MUST be quoted verbatim from search_guidance
  output, with its source. If you cannot find a rule in the guidance, do not state it.
- One clear ask per email. Professional, warm, concise; urgency proportionate to the day count.
"""


class AgentDraft(BaseModel):
    """Structured output of the drafting agent."""

    subject: str
    body: str
    citations: list[Citation] = []


def build_agent(model):
    """Construct the Pydantic AI Agent with its four tools.

    TODO(evening 3): implement —
      Agent(model, output_type=AgentDraft, system_prompt=SYSTEM_PROMPT + feedback section)
      with tools: get_filings, days_until_due, get_client_context, search_guidance
      (backed by companies_house.get_filing_history, the precomputed TriageItem,
      store.client, and rag.search respectively). Append store.recent_rejections()
      summarised as a 'reviewer feedback' section.
    """
    raise NotImplementedError("TODO(evening 3): build the Pydantic AI agent")


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


def draft_for(item: TriageItem, client: ClientCompany) -> DraftEmail:
    """Draft one chasing email: agent when a model is available, template otherwise."""
    model = llm.get_model("draft")
    if model is None:
        return template_draft(item, client)
    # TODO(evening 3): run build_agent(model) with the item injected; validate citations via
    # rag.verify_citation (one retry, then flag). Until then, the template keeps the pipeline
    # runnable end to end.
    return template_draft(item, client)
