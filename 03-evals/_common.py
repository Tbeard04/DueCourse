"""Shared helpers for the eval scripts. Run every script from 02-solution, e.g.:

cd 02-solution && uv run python ../03-evals/triage_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"

# The 5-criterion rubric (draft_rubric.md). Keys double as hand_scores.csv column names.
CRITERIA = [
    "correct_facts",
    "correct_tone",
    "one_clear_ask",
    "no_invented_details",
    "appropriate_urgency",
]


def write_results(name: str, payload: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def usage_tokens(result) -> tuple[int, int]:
    """(input_tokens, output_tokens) from a pydantic-ai run result, across API renames."""
    usage = result.usage  # a property since pydantic-ai 2.x; calling it is deprecated
    input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "request_tokens", 0) or 0
    output_tokens = (
        getattr(usage, "output_tokens", None) or getattr(usage, "response_tokens", 0) or 0
    )
    return int(input_tokens), int(output_tokens)
