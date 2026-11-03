"""Model-selection eval: the same drafts through every candidate model (SPEC §13a).

Drafts an identical fixed set of ~20 urgent items once per candidate — claude-opus-5-5,
claude-sonnet-5-5, claude-haiku-5-5, and the Ollama local model — same agent, same tools,
same prompt; only the model changes (via llm.get_model overrides).

Per candidate: rubric pass-rate (scored by judge.py's constant judge), citation-validity rate,
cost per full 60-company weekly run (extrapolated from usage token counts x published per-MTok
prices), median latency per draft.

Output: results/model_comparison.json + the table in results/results.md; the recommendation is
written up in model-selection.md and becomes the shipped DRAFT_MODEL default.

TODO(evening 5): implement.
"""

CANDIDATES = [
    "claude-opus-5-5",
    "claude-sonnet-5-5",
    "claude-haiku-5-5",
    "ollama:llama3.1:8b",
]

# $/MTok (input, output) as of 2026-11 — restate the as-of date in the memo.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "ollama:llama3.1:8b": (0.0, 0.0),
}

raise SystemExit("TODO(evening 5): not implemented yet — see module docstring")
