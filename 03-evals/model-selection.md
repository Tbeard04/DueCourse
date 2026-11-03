# Model selection — recommendation memo

*For the practice ("the client"). Run 2026-11-03: 20 identical drafting tasks per candidate —
same agent, tools, prompt and citation checks; only the model swapped. Judged pass/fail on the
5-criterion rubric by a constant judge (claude-sonnet-5-5). Raw data:
`results/model_comparison.json`. Prices are Anthropic API rates as of the run date.*

## The comparison

| Model | Rubric 5/5 | Citation validity | Cost / weekly run* | Median latency |
| --- | --- | --- | --- | --- |
| claude-opus-5-5 | 35% | 100% (47/47) | $0.32 | 11.6s |
| **claude-sonnet-5-5** | **50%** | **100% (43/43)** | **$0.19** | **9.5s** |
| claude-haiku-5-5 | 45% | 100% (20/20) | $0.01 | 9.8s |
| llama3.1:8b (local, Ollama) | 0% — completed 3/20 | n/a (no citations) | £0 (local) | 7.7s |

*\*modelled at 8 drafts/week, measured token usage × published $/MTok.*

**Dominant failure modes differ by model:** opus fails almost entirely on `no_invented_details`
(12/20 — richer contextual prose the judge reads as going beyond the supplied facts), while
sonnet and haiku mostly fail `one_clear_ask` (6–7/20). Every penalty figure any Anthropic model
quoted was verified verbatim against the guidance corpus — **110/110 citations valid**.

## Recommendation

**`claude-sonnet-5-5` as the shipped `DRAFT_MODEL` default.** Best pass-rate point estimate,
fastest of the three, and 100% citation validity. Cost does **not** decide this: at practice
scale all three cost under £15/year, which is immaterial next to one £150 late-filing penalty —
so the decision rests on quality, where paying 2× sonnet's rate for opus bought no measured
improvement on this task. If budget ever mattered, haiku at ~$0.50/year is statistically
indistinguishable from sonnet here and would be the value pick.

**The local-model finding matters for a different conversation:** llama3.1:8b failed the
structured-output contract on 17 of 20 tasks. The zero-key/on-prem path exists and degrades
gracefully (triage and digest are unaffected; templates still produced), but a data-residency
deployment would need a substantially larger local model, costed separately.

## When to revisit

- Drafts get materially longer or more complex (cost gaps widen with output length)
- A data-residency requirement forces the local path (re-run with larger local models)
- Prices or models change

## Honesty notes

- **n=20 per model: the sonnet–haiku–opus differences are within sampling noise** (±~11pp);
  this run ranks them but cannot separate them definitively. The direction of the finding —
  "no measured gain from the most expensive model" — is the decision-relevant part.
- **The judge shares a family with one candidate** (judge = claude-sonnet-5-5). Mitigation
  planned: hand-scores + agreement stats (agreement.py), and a sensitivity re-run with a
  different judge model.
- The 20-item set is the top of the triage snapshot, so it includes upcoming/ok items beyond
  the 7 genuinely urgent ones; production only drafts overdue/due-soon items.
- The judge's criterion justifications were not persisted per draft in this run — the
  `no_invented_details` characterisation above comes from the failure counts; hand-scoring
  will test it qualitatively.
- Total eval spend: well under £1.
