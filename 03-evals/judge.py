"""LLM judge for draft quality: the 5-criterion rubric in draft_rubric.md.

Judge model: claude-sonnet-5-5 (constant across everything it scores — judge != drafter to
reduce self-preference bias). Each criterion is scored pass/fail with a one-line justification
via a Pydantic AI agent with structured output.

Output: results/judge_scores.json (one row per draft per criterion).

TODO(evening 5): implement. Run from 02-solution: uv run python ../03-evals/judge.py
"""

raise SystemExit("TODO(evening 5): not implemented yet — see module docstring")
