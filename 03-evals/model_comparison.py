"""Model-selection eval: the same drafts through every candidate model (SPEC §13a).

Takes the N most urgent items from the latest triage snapshot and drafts each one once per
candidate — identical agent, tools, prompt and citation validation (agent.draft_with_model);
only the model changes. Filing-history context is disabled (ch=None) so every candidate sees
byte-identical inputs. Drafts are NOT saved to the review queue.

Per candidate: rubric pass-rate (scored by judge.py's constant judge), citation validity,
measured token usage -> cost per draft and per modelled weekly run, and median latency.
Results feed model-selection.md; the recommendation becomes the shipped DRAFT_MODEL.

Run from 02-solution:  uv run python ../03-evals/model_comparison.py [N]
"""

from __future__ import annotations

import statistics
import sys
import time
from datetime import UTC, datetime

from _common import write_results
from judge import JUDGE_INSTRUCTIONS, RubricScore, judge_prompt
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from duecourse import llm, rag
from duecourse.agent import draft_with_model
from duecourse.config import get_settings
from duecourse.store import Store

DEFAULT_N = 20
WEEKLY_DRAFTS = 8  # assumption from the discovery memo: ~8 chasing emails per week

ANTHROPIC_CANDIDATES = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
# $/MTok (input, output), Anthropic API, as of 2026-11-03 — restate the date in the memo.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def candidates() -> list:
    settings = get_settings()
    models = []
    if settings.anthropic_api_key:
        provider = AnthropicProvider(api_key=settings.anthropic_api_key)
        models += [AnthropicModel(model_id, provider=provider) for model_id in ANTHROPIC_CANDIDATES]
    from duecourse.llm import OLLAMA_DRAFT_MODEL, _ollama_reachable

    if _ollama_reachable(settings.ollama_base_url):
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.ollama import OllamaProvider

        models.append(
            OpenAIChatModel(
                OLLAMA_DRAFT_MODEL,
                provider=OllamaProvider(base_url=f"{settings.ollama_base_url}/v1"),
            )
        )
    else:
        print("NOTE: Ollama not reachable — local candidate skipped")
    return models


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_N
    judge_model = llm.get_model("judge")
    if judge_model is None:
        sys.exit("The judge needs a configured LLM (ANTHROPIC_API_KEY or Ollama).")
    judge = Agent(judge_model, output_type=RubricScore, instructions=JUDGE_INSTRUCTIONS)

    store = Store(get_settings().db_path)
    items = store.latest_triage()[:n]  # most urgent first
    if not items:
        sys.exit("No triage snapshot — run: uv run duecourse triage")
    tasks = [(item, store.client(item.deadline.company_number)) for item in items]
    tasks = [(item, client) for item, client in tasks if client is not None]
    models = candidates()
    print(f"Comparing {len(models)} candidates on {len(tasks)} items (judge held constant)")

    results = []
    for model in models:
        name = llm.describe_model(model)
        latencies: list[float] = []
        costs: list[float] = []
        rows: list[dict] = []
        failures = 0
        for item, client in tasks:
            usage: dict = {}
            started = time.monotonic()
            try:
                draft = draft_with_model(model, item, client, store=None, ch=None, usage_out=usage)
            except Exception as exc:  # noqa: BLE001 — a failing candidate is a result, not a crash
                failures += 1
                print(f"  {name}: FAILED on {item.deadline.company_number}: {exc}")
                continue
            latencies.append(time.monotonic() - started)
            price_in, price_out = PRICES.get(name, (0.0, 0.0))
            costs.append(
                usage.get("input_tokens", 0) / 1e6 * price_in
                + usage.get("output_tokens", 0) / 1e6 * price_out
            )
            verdict = judge.run_sync(judge_prompt(draft))
            scores = verdict.output.model_dump()
            valid = sum(rag.verify_citation(c) for c in draft.citations)
            rows.append(
                {
                    "company_number": draft.company_number,
                    "passed_5_of_5": all(v["passed"] for v in scores.values()),
                    "criteria": {k: v["passed"] for k, v in scores.items()},
                    "citations_total": len(draft.citations),
                    "citations_valid": valid,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "subject": draft.subject,
                }
            )

        if not rows:
            results.append({"model": name, "failed": True, "failures": failures})
            continue
        cited = [r for r in rows if r["citations_total"]]
        mean_cost = statistics.mean(costs) if costs else 0.0
        summary = {
            "model": name,
            "drafts": len(rows),
            "failures": failures,
            "rubric_pass_rate": round(sum(r["passed_5_of_5"] for r in rows) / len(rows), 4),
            "citation_validity": (
                round(
                    sum(r["citations_valid"] for r in cited)
                    / sum(r["citations_total"] for r in cited),
                    4,
                )
                if cited
                else None
            ),
            "median_latency_s": round(statistics.median(latencies), 2),
            "mean_cost_per_draft_usd": round(mean_cost, 5),
            "cost_per_weekly_run_usd": round(mean_cost * WEEKLY_DRAFTS, 4),
            "rows": rows,
        }
        results.append(summary)
        print(
            f"  {name}: pass {summary['rubric_pass_rate']:.0%} | "
            f"${summary['cost_per_weekly_run_usd']}/weekly run | "
            f"median {summary['median_latency_s']}s | failures {failures}"
        )

    payload = {
        "ran_at": datetime.now(UTC).isoformat(),
        "n_items": len(tasks),
        "judge_model": llm.describe_model(judge_model),
        "weekly_drafts_assumption": WEEKLY_DRAFTS,
        "results": results,
    }
    path = write_results("model_comparison.json", payload)
    store.close()
    print(f"Full results -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
