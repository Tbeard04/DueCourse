# Runbook — operating DueCourse

<!-- TODO(evening 6): written for a practice manager, not an engineer. -->

## Normal operation

- Monday 07:30: the weekly run executes (`duecourse run-weekly`, scheduled) — or run it manually
  with `duecourse run-weekly --now`.
- Open the review queue (`duecourse review`); approve, edit, or reject each draft. Rejections
  need a reason — they feed the next week's drafting.
- **The system never sends email.** Approved drafts are copied into your mail client by you.

## Keys and rotation

<!-- TODO: Companies House API key rotation; LLM key optional. -->

## What "degraded" looks like

| Symptom | Meaning | Action |
| --- | --- | --- |
| Drafts are templated, not personalised | No LLM configured/reachable | Triage and digest are unaffected; fix the key or Ollama |
| Digest missing on Monday | Scheduler not running | `duecourse run-weekly --now` |
| <!-- TODO --> | | |
