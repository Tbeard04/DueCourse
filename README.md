# DueCourse — a one-person forward deployment

> **The number:** _TBD after measurement_ — manual filing-deadline chasing took **X hrs/week**;
> with DueCourse it takes **Y**, modelled at **£Z/year** saved for a 3-partner practice.
> (Baseline protocol and assumptions: [04-measurement](04-measurement/measurement.md).)

A small UK accountancy practice loses hours every week chasing Companies House filing deadlines
across ~60 client companies — and chasing the clients for records. DueCourse watches the client
list through the **live Companies House public API**, triages what's due, drafts the chasing
emails for a human to approve, and produces a Monday-morning workload digest.

**Live demo:** the [public weekly digest](https://tbeard04.github.io/DueCourse/) regenerates
itself every Monday from the live register via a scheduled GitHub Action — no servers, no LLM,
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
stack that works is demonstrating client judgement — the production path for the review UI would
be a proper web app (Next.js/TypeScript); for this engagement, Streamlit ships the workflow.

## What the second client would get

The pattern is **deadline-driven compliance workflow**, not accountancy: a deterministic
deadline source, triage thresholds, cited drafting against an official-guidance corpus, a
human review queue, and a weekly digest. VAT returns, payroll year-end, lettings gas
certificates, visa renewals — config swaps the data source and schema; the engagement
artefacts (discovery → measurement → runbook → enablement) template directly. That's what
makes this a repeatable client programme rather than a one-off build: the second engagement
starts from this pack, not from zero. Two things would change at production scale: the review
UI becomes a proper web app (Next.js/TypeScript) with the practice's own sign-in, and the
baseline comes from the client's staff and timesheets instead of the author's stopwatch.

## Honest limitations

One simulated client; baseline timed on the author; draft-quality n=30. Stated plainly here and
in [03-evals/results](03-evals/results/results.md).
