# Eval results

<!-- TODO(evening 5): filled by triage_eval.py, judge.py, agreement.py, model_comparison.py -->

## Triage accuracy (vs live API ground truth)

- Exact-match accuracy: <!-- TODO --> across <!-- TODO --> deadlines
- Misses investigated: <!-- TODO: each one diagnosed, e.g. extended accounting periods -->

## Draft quality (5-criterion rubric)

- LLM-judge pass-rate: <!-- TODO -->
- Hand-scored (n=30) pass-rate: <!-- TODO -->
- Judge–human agreement: <!-- TODO: % + Cohen's kappa per criterion -->

## Citation validity

- Quoted rules found verbatim in the guidance corpus: <!-- TODO --> (target 100%)

## Model comparison

See [model-selection.md](model-selection.md) for the table and recommendation.

## Caveats, stated plainly

One simulated client; judge is an LLM (agreement measured, above); n=30 hand scores;
baseline timing in [04-measurement](../04-measurement/measurement.md) performed by the author.
