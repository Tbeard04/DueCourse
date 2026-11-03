"""LLM judge for draft quality: the 5-criterion rubric in draft_rubric.md.

Judges every draft in the store (pending and decided) with the constant judge model
(JUDGE_MODEL, default claude-sonnet-5-5 — judge != drafter to reduce self-preference bias).
Each criterion is pass/fail with a one-line justification, via structured output. Also
reports citation validity (every quote checked verbatim against the guidance corpus).

Output: results/judge_scores.json — one row per draft, joinable with hand_scores.csv on
draft_id by agreement.py.

Run from 02-solution:  uv run python ../03-evals/judge.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from _common import write_results
from pydantic import BaseModel
from pydantic_ai import Agent

from duecourse import llm, rag
from duecourse.config import get_settings
from duecourse.models import DraftEmail
from duecourse.store import Store

JUDGE_INSTRUCTIONS = """\
You are judging a chasing email drafted for a UK accountancy practice about a Companies House
filing deadline. Judge against the FACTS block (ground truth) and the CITATIONS block.

Score each criterion pass/fail with a one-line justification:
- correct_facts: every date, day count and company detail in the email matches the FACTS block
  exactly.
- correct_tone: professional and warm; appropriate for a practice writing to its own client.
- one_clear_ask: exactly one action is requested, unambiguously.
- no_invented_details: nothing is claimed that is not in FACTS or CITATIONS — no made-up
  penalties, dates, history or consequences.
- appropriate_urgency: the register of urgency is proportionate to the day count (overdue is
  urgent; 14 days out is firm but calm).
Judge only what is written. Do not reward length or extra caveats.
"""


class CriterionScore(BaseModel):
    passed: bool
    justification: str


class RubricScore(BaseModel):
    correct_facts: CriterionScore
    correct_tone: CriterionScore
    one_clear_ask: CriterionScore
    no_invented_details: CriterionScore
    appropriate_urgency: CriterionScore


def judge_prompt(draft: DraftEmail) -> str:
    item = draft.triage_item
    citations = "\n".join(f'- "{c.quote}" — {c.source_title}' for c in draft.citations) or "(none)"
    return f"""FACTS (deterministic, from Companies House):
- company_number: {draft.company_number}
- filing_kind: {item.deadline.kind.value}
- due_date: {item.deadline.due_date}
- days_until_due: {item.days_until_due} (as of {item.as_of})
- status: {item.status.value}

CITATIONS supplied with the draft (verified against the guidance corpus separately):
{citations}

DRAFT SUBJECT: {draft.subject}

DRAFT BODY:
{draft.body}
"""


def score_draft(judge: Agent, draft: DraftEmail) -> dict:
    result = judge.run_sync(judge_prompt(draft))
    scores: RubricScore = result.output
    row = {
        "draft_id": draft.id,
        "company_number": draft.company_number,
        "model_used": draft.model_used,
    }
    passed = 0
    for criterion, value in scores.model_dump().items():
        row[criterion] = value["passed"]
        row[f"{criterion}_why"] = value["justification"]
        passed += value["passed"]
    row["rubric_passed_5_of_5"] = passed == 5
    valid = sum(rag.verify_citation(c) for c in draft.citations)
    row["citations_total"] = len(draft.citations)
    row["citations_valid"] = valid
    return row


def main() -> int:
    judge_model = llm.get_model("judge")
    if judge_model is None:
        sys.exit("No LLM configured — the judge needs ANTHROPIC_API_KEY (or Ollama).")
    judge = Agent(judge_model, output_type=RubricScore, instructions=JUDGE_INSTRUCTIONS)

    store = Store(get_settings().db_path)
    drafts = store.drafts()
    store.close()
    if not drafts:
        sys.exit("No drafts in the store — run: uv run duecourse draft")

    rows = [score_draft(judge, draft) for draft in drafts]
    pass_rate = sum(r["rubric_passed_5_of_5"] for r in rows) / len(rows)
    cited = [r for r in rows if r["citations_total"]]
    citation_validity = (
        sum(r["citations_valid"] for r in cited) / sum(r["citations_total"] for r in cited)
        if cited
        else None
    )
    payload = {
        "ran_at": datetime.now(UTC).isoformat(),
        "judge_model": llm.describe_model(judge_model),
        "drafts_judged": len(rows),
        "rubric_pass_rate_5_of_5": round(pass_rate, 4),
        "citation_validity": round(citation_validity, 4) if citation_validity is not None else None,
        "per_criterion_pass_rate": {
            criterion: round(sum(r[criterion] for r in rows) / len(rows), 4)
            for criterion in RubricScore.model_fields
        },
        "rows": rows,
    }
    path = write_results("judge_scores.json", payload)
    print(f"Judged {len(rows)} drafts with {payload['judge_model']}")
    print(f"Rubric pass rate (5/5): {pass_rate:.0%}")
    for criterion, rate in payload["per_criterion_pass_rate"].items():
        print(f"  {criterion:<22} {rate:.0%}")
    if citation_validity is not None:
        print(f"Citation validity: {citation_validity:.0%}")
    print(f"Full results -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
