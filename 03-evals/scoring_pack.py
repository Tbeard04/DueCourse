"""Build the hand-scoring pack: 30 drafts, judged, ready for blind human scoring.

Takes every draft already in the store and tops up to 30 by drafting further triage items
with a mix of candidate models (not saved to the review queue — scoring material only). Then:

- results/judge_scores.json   — the LLM judge's scores for the same 30 (refreshed)
- results/scoring_pack.md     — the drafts in seeded-shuffled order WITHOUT model names or
                                judge verdicts: read each against draft_rubric.md and score
- hand_scores.csv             — pre-filled with one row per draft (model column left blank
                                to keep scoring blind; agreement.py joins on draft_id)

Workflow: fill the five criterion columns with 1/0 per draft (don't peek at judge_scores),
then run agreement.py.

Run from 02-solution:  uv run python ../03-evals/scoring_pack.py
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

from _common import CRITERIA, write_results
from judge import JUDGE_INSTRUCTIONS, RubricScore, score_draft
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from duecourse import llm
from duecourse.agent import draft_with_model
from duecourse.config import get_settings
from duecourse.store import Store

TARGET = 30
TOPUP_MODELS = ["claude-haiku-5-5", "claude-opus-5-5"]  # variety beyond the queue's drafts
HAND_SCORES = Path(__file__).resolve().parent / "hand_scores.csv"
PACK = Path(__file__).resolve().parent / "results" / "scoring_pack.md"


def main() -> int:
    settings = get_settings()
    if not settings.anthropic_api_key:
        sys.exit("Top-up drafting and the judge need ANTHROPIC_API_KEY.")
    judge = Agent(llm.get_model("judge"), output_type=RubricScore, instructions=JUDGE_INSTRUCTIONS)

    store = Store(settings.db_path)
    drafts = store.drafts()
    have = {(d.company_number, d.triage_item.deadline.kind, d.model_used) for d in drafts}

    items = store.latest_triage()
    provider = AnthropicProvider(api_key=settings.anthropic_api_key)
    model_cycle = [AnthropicModel(m, provider=provider) for m in TOPUP_MODELS]
    index = 0
    for item in items:
        if len(drafts) >= TARGET:
            break
        client = store.client(item.deadline.company_number)
        if client is None:
            continue
        model = model_cycle[index % len(model_cycle)]
        key = (item.deadline.company_number, item.deadline.kind, llm.describe_model(model))
        if key in have:
            continue
        print(f"  topping up: {item.deadline.company_number} via {llm.describe_model(model)}")
        drafts.append(draft_with_model(model, item, client, store=None, ch=None))
        have.add(key)
        index += 1
    store.close()
    drafts = drafts[:TARGET]

    print(f"Judging {len(drafts)} drafts…")
    rows = [score_draft(judge, draft) for draft in drafts]
    pass_rate = sum(r["rubric_passed_5_of_5"] for r in rows) / len(rows)
    write_results(
        "judge_scores.json",
        {
            "ran_at": datetime.now(UTC).isoformat(),
            "judge_model": llm.describe_model(llm.get_model("judge")),
            "drafts_judged": len(rows),
            "rubric_pass_rate_5_of_5": round(pass_rate, 4),
            "per_criterion_pass_rate": {
                criterion: round(sum(r[criterion] for r in rows) / len(rows), 4)
                for criterion in CRITERIA
            },
            "rows": rows,
        },
    )

    # The human-facing pack: seeded shuffle, no model names, no judge verdicts.
    shuffled = drafts[:]
    random.Random(7).shuffle(shuffled)
    lines = [
        "# Hand-scoring pack",
        "",
        f"{len(shuffled)} drafts in random order — models hidden. Score each against",
        "[draft_rubric.md](../draft_rubric.md): five criteria, 1 (pass) or 0 (fail) per row",
        "in hand_scores.csv, matched by draft id. Don't look at judge_scores.json until done.",
        "",
    ]
    for position, draft in enumerate(shuffled, 1):
        item = draft.triage_item
        citations = (
            "\n".join(f"> “{c.quote}” — {c.source_title}" for c in draft.citations)
            or "> (no citations)"
        )
        lines += [
            f"## Draft {position} · `{draft.id}`",
            "",
            (
                f"**Facts (ground truth):** {item.deadline.kind.value}"
                f" · due {item.deadline.due_date} · {item.days_until_due:+d} days"
                f" ({item.status.value}) as of {item.as_of} · company {draft.company_number}"
            ),
            "",
            f"**Subject:** {draft.subject}",
            "",
            "```text",
            draft.body,
            "```",
            "",
            "**Citations supplied:**",
            citations,
            "",
        ]
    PACK.write_text("\n".join(lines), encoding="utf-8")

    with HAND_SCORES.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["draft_id", "model", *CRITERIA, "notes"])
        for draft in shuffled:
            writer.writerow([draft.id, "", *[""] * len(CRITERIA), ""])

    print(f"Pack -> {PACK}")
    print(f"Pre-filled {HAND_SCORES.name} with {len(shuffled)} blind rows.")
    print("Score, then: uv run python ../03-evals/agreement.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
