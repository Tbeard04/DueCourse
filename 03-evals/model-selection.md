# Model selection — recommendation memo

> One page, written for the practice (the "client"), after `model_comparison.py` runs.
> The recommended model becomes the shipped `DRAFT_MODEL` default — config follows evidence.

## The comparison

| Model | Rubric pass-rate | Citation validity | Cost / weekly run | Median latency |
| --- | --- | --- | --- | --- |
| claude-opus-5-5 | <!-- TODO --> | | | |
| claude-sonnet-5-5 | | | | |
| claude-haiku-5-5 | | | | |
| local (Ollama) | | | | |

## Recommendation

<!-- TODO(evening 5): "model X, because the quality delta above it isn't worth N× the cost." -->

## When to revisit

- Drafts get materially longer or more complex
- A data-residency requirement forces the on-prem (Ollama) path
- Prices or models change (prices above as of the run date)

## Honesty notes

n≈20 drafts per model; the judge is itself an LLM (kappa vs hand-scores reported in
`results/results.md`); total eval spend was under £1.
