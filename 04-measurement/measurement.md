# Measurement — baseline vs after

> The measurement plan was written **before** the agent was finished (engagement method:
> baseline → intervention → remeasure). It's a model, not a claim: every assumption is stated,
> and at a real client the baseline would come from their staff and timesheets, not the author.

## What is measured

The weekly unit of work, as mapped in the [discovery memo](../01-discovery/discovery-memo.md):

- **Task A — deadline check:** confirm the live accounts + confirmation-statement due dates and
  urgency for the client book, against the Companies House register.
- **Task B — chasing emails:** write the week's chasing emails (modelled at 8/week) with
  correct dates, correct penalty consequences, and a clear ask.

## Baseline protocol (manual workflow)

Ten full manual runs of a 60-company check in one evening isn't realistic, so the baseline
samples each task and scales linearly — the scaling is itself an assumption, sanity-checked by
one full unscaled run:

1. **Task A sampling:** 10 timed runs, each checking a different random **12-company** slice of
   the portfolio on the Companies House website and recording due dates + urgency in the
   spreadsheet, exactly as the office manager would. Weekly estimate = median run × 5.
2. **Task B sampling:** 10 timed runs, each hand-writing **one** chasing email for a real
   urgent item (contact lookup, penalty check against GOV.UK, tone). Weekly estimate =
   median × 8.
3. **Sanity check:** one full 60-company Task A run, compared against the ×5 linear estimate;
   if it diverges badly, the scaling assumption is revised and the divergence reported.

Record every run in the tables below (raw times, not just medians).

## After protocol (with DueCourse)

The same weekly unit of work, 10 timed runs across different days:

- **Task A:** `duecourse sync` + `duecourse triage` wall-clock time plus reading the digest.
- **Task B:** reviewing the week's drafts in the queue (approve / edit / reject with reason),
  timed from opening the queue to emptying it.

## Results

| Run | Baseline A: 12-co check (mm:ss) | Baseline B: 1 email (mm:ss) | After A: sync+triage+digest | After B: review queue |
| --- | --- | --- | --- | --- |
| 1–10 | <!-- TODO: timed runs --> | | | |
| **Median** | | | | |

Full-run sanity check (60 companies, manual): <!-- TODO --> vs linear estimate: <!-- TODO -->

## The model

- **Hours/week saved** = (baseline weekly estimate) − (after weekly estimate).
- **£/year** = hours/week × 46 working weeks × **£35/hour**. Rate basis: a 2025 survey of 131
  UK bookkeepers found a **median £33.36/hour**
  ([6 Figure Bookkeeper pricing report, via Better Account](https://betteraccount.co.uk/p/what-is-hourly-rate-for-a-bookkeeper-in-uk/));
  small-practice qualified staff are charged out at £55–75/hour in practitioner accounts
  ([AccountingWEB](https://www.accountingweb.co.uk/node/210137)). £35 is deliberately at the
  cheap end — the saving is understated, not oversold.
- **Penalty-risk reduction**, reported separately and not priced into the headline: the
  portfolio's live overdue items (see the digest) each carry an automatic £150–£1,500 penalty
  exposure ([GOV.UK](https://www.gov.uk/annual-accounts/penalties-for-late-filing)); fewer
  missed deadlines is claimed directionally, not in £, since n=1 engagement.
- **Tool running cost**, netted off: ~$0.19/week in model spend at the selected drafting model
  ([model-selection memo](../03-evals/model-selection.md)) — immaterial but stated.

## Assumptions (stated)

1. Baseline timed on the author, not practice staff — a motivated operator; real staff with
   interruptions would likely be slower, so the baseline (and therefore the saving) is
   conservative.
2. Linear scaling from 12-company samples to 60 (sanity-checked once).
3. Weekly cadence and 8 chases/week, from the discovery memo's composite client — assumed.
4. £35/hour staff cost; 46 working weeks/year.
5. The after-measurement includes no training time; the 10-minute enablement session is the
   stated onboarding cost.
