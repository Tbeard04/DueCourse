# Scope — agreed "with the client"

## In scope

- Confirmation-statement and annual-accounts deadlines for the ~60-company portfolio
- Triage (overdue / due ≤14 days / due ≤30 days / fine) from live Companies House data
- Drafted chasing emails — proposals only, approved by a human in the review queue
- Monday-morning workload digest

## Out of scope

- Sending email (by design, permanently — not a v2 feature)
- VAT, payroll, or HMRC deadlines (the "second client" generalisation — see README)
- Practice-management integration

## Success criteria (agreed "with the client")

1. **Triage correctness: 100%**, exact-match against the Companies House API's own due dates,
   re-verified across the whole portfolio by `03-evals/triage_eval.py`. Anything less fails the
   engagement — a wrong deadline is worse than no tool.
2. **Time on task: ≥50% reduction** in the measured weekly workflow (deadline check + chasing
   drafts), baseline vs with-tool, per the protocol in
   [04-measurement](../04-measurement/measurement.md).
3. **Nothing sends without a human**: every outgoing email is approved, edited or rejected in
   the review queue, with the decision logged. Verified structurally (no mail library in the
   codebase, enforced by a CI test).
4. **Every quoted rule is real**: 100% of penalty figures and filing rules in drafts verified
   verbatim against the GOV.UK guidance corpus (citation eval).
5. **Draft quality is reviewable, not perfect**: rubric pass-rate reported honestly (LLM judge
   + 30 hand-scores with agreement stats); the queue makes editing cheap, so the bar is
   "usually sendable with light edits", not "always perfect".
6. **The office manager can run it** after one 10-minute training session, using the runbook
   alone.
