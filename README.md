# DueCourse — a one-person forward deployment

> **The number:** _TBD after measurement_ — manual filing-deadline chasing took **X hrs/week**;
> with DueCourse it takes **Y**, modelled at **£Z/year** saved for a 3-partner practice.
> (Baseline protocol and assumptions: [04-measurement](04-measurement/measurement.md).)

A small UK accountancy practice loses hours every week chasing Companies House filing deadlines
across ~60 client companies — and chasing the clients for records. DueCourse watches the client
list through the **live Companies House public API**, triages what's due, drafts the chasing
emails for a human to approve, and produces a Monday-morning workload digest.

**Live demo:** the [public weekly digest](https://tbeard04.github.io/DueCourse/) regenerates
itself every Monday from the live register via a scheduled GitHub Action — a statically
exported Next.js + TypeScript page ([02-solution/web](02-solution/web/)): no servers, no LLM,
read-only. The drafting and review queue run privately; to use those, clone the repo and bring
your own free Companies House key (plus an optional LLM key — see Quick start).

**The system never sends an email.** Every draft lands in a review queue; every decision is
logged. Deadlines and urgency are computed deterministically from Companies House data — the LLM
only drafts prose around injected, cited facts.

## The engagement pack

| Artefact | What it is |
| --- | --- |
| [01-discovery](01-discovery/) | The as-is workflow, who does it, where the hours go; agreed scope |
| [02-solution](02-solution/) | The DueCourse codebase: triage, drafting agent, review queue, digest |
| [03-evals](03-evals/) | Triage accuracy vs live API ground truth; draft rubric + LLM judge + hand-scores; model-selection memo |
| [04-measurement](04-measurement/) | Timed baseline vs after; hours/week and £/year with stated assumptions |
| [05-handover](05-handover/) | Runbook and risk register |
| [06-enablement](06-enablement/) | The 10-minute training session for the practice's staff |

## Where the engagement stands

The build is done; what remains is the consulting discipline — validating the evals with a
human, measuring the value, and enabling the client.

**Done and verified:**

- Triage: **120/120** deadlines exact-match against the live register's own answers
  ([results](03-evals/results/results.md))
- Cited drafting: **110/110** penalty citations machine-verified verbatim against the GOV.UK
  guidance corpus
- Model selection: four candidates compared under a constant judge; **claude-sonnet-5-5**
  shipped as the default — paying 2× for the top-tier model bought no measured quality gain,
  and the local 8B model failed the structured-output contract on 17/20 tasks
  ([memo](03-evals/model-selection.md))
- The never-sends guarantee is CI-enforced: a test walks the codebase proving no mail library
  exists anywhere
- Live public digest shipped: Next.js + TypeScript, statically exported, rebuilt from the
  register every Monday by a scheduled GitHub Action

**Next, in order:**

1. **Hand-score the 30-draft blind pack** ([scoring pack](03-evals/results/scoring_pack.md))
   and compute human–judge agreement (Cohen's kappa via
   [agreement.py](03-evals/agreement.py)). The LLM judge shares a model family with the
   shipped default, so its verdicts only become client-grade evidence once a human has
   calibrated them against blind scores.
2. **Run the timed before/after measurement** ([protocol](04-measurement/measurement.md)) and
   replace the X/Y/Z headline at the top of this page with measured numbers.
3. **Deliver enablement**: record the training session from
   [06-enablement](06-enablement/training-session.md) as the client-facing walkthrough.

## Quick start

```bash
cd 02-solution
uv sync                       # full install incl. local embeddings (CI runs slim: --no-group rag)
cp .env.example .env          # add your (free) Companies House API key
uv run duecourse sync
uv run duecourse triage
uv run duecourse review       # opens the Streamlit review queue
```

Runs with no LLM key at all: triage and the digest are deterministic, and drafts fall back to
templates. Set `ANTHROPIC_API_KEY` for model-drafted emails, or run Ollama locally.

## Deliberately not used

No agent-framework zoo, no hosted vector DB, no fine-tuning. An FDE who reaches for the minimum
stack that works is demonstrating client judgement — the public digest frontend shows the
production web stack (Next.js/TypeScript, statically exported); for the internal review queue,
Streamlit ships the workflow this engagement needs.

## What the second client would get

The pattern is **deadline-driven compliance workflow**, not accountancy: a deterministic
deadline source, triage thresholds, cited drafting against an official-guidance corpus, a
human review queue, and a weekly digest. VAT returns, payroll year-end, lettings gas
certificates, visa renewals — config swaps the data source and schema; the engagement
artefacts (discovery → measurement → runbook → enablement) template directly. That's what
makes this a repeatable client programme rather than a one-off build: the second engagement
starts from this pack, not from zero. Two things would change at production scale: the review
UI graduates from Streamlit to the same Next.js/TypeScript stack as the public digest, with
the practice's own sign-in, and the baseline comes from the client's staff and timesheets
instead of the author's stopwatch.

## Honest limitations

One simulated client; baseline timed on the author; draft-quality n=30. Stated plainly here and
in [03-evals/results](03-evals/results/results.md).
