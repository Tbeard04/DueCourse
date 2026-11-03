# Eval results

Run on 2026-11-03 against the live Companies House register (60-company portfolio).
Raw outputs: `triage_results.json`, `judge_scores.json`, `model_comparison.json`.

## Triage accuracy (vs live API ground truth)

- **Exact-match accuracy: 120/120 = 100%** across every deadline in the portfolio
  (status *and* day count both matching a fresh recomputation from the live register).
- Misses investigated: none on this run. The eval distinguishes genuine triage bugs from
  register changes (a company filing between snapshot and eval moves its due date) — neither
  occurred here.

## Draft quality (5-criterion rubric, judge: claude-sonnet-5-5)

Baseline run over the review queue's 12 **template** (LLM-free fallback) drafts:

| Criterion | Pass rate |
| --- | --- |
| correct_facts | 100% |
| correct_tone | 100% |
| one_clear_ask | 92% |
| no_invented_details | 100% |
| appropriate_urgency | **50%** |
| **All 5 (pass)** | **50%** |

**Finding:** the deterministic template is factually perfect but tonally flat — every failure
is `appropriate_urgency` on overdue items (the judge: *"64 days overdue, yet the subject line
says 'Reminder'"*). This is the measured case for the LLM drafting layer: facts were never
the LLM's job; register-appropriate urgency is.

- Hand-scored (n=30) pass rate: <!-- TODO: score 30 drafts in hand_scores.csv -->
- Judge–human agreement: <!-- TODO: run agreement.py after hand-scoring -->

## Citation validity

Template drafts carry no citations by design. Model-drafted citation validity is measured per
candidate in the model comparison below (every quote checked verbatim against the corpus).

## Model comparison

<!-- TODO: table from model_comparison.json once the run completes -->
See [model-selection.md](../model-selection.md) for the recommendation memo.

## Caveats, stated plainly

One simulated client; the judge is an LLM (agreement vs hand-scores to be reported above);
baseline timing in [04-measurement](../../04-measurement/measurement.md) performed by the
author. Prices and register state as of the run date.
