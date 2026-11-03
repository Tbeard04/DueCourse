"""Triage accuracy vs live Companies House ground truth.

Re-fetches the live profile for every portfolio company, recomputes ground-truth status from
the API's own due dates, and exact-matches against the stored triage snapshot. Target 100%;
every miss gets investigated and written up (extended accounting periods live here).

Output: results/triage_results.json + a section in results/results.md.

TODO(evening 5): implement using duecourse.companies_house + duecourse.triage + Store.
Run from 02-solution: uv run python ../03-evals/triage_eval.py
"""

raise SystemExit("TODO(evening 5): not implemented yet — see module docstring")
