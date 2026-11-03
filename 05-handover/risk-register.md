# Risk register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Wrong deadline shown | Client misses a filing → £150+ penalty | Triage is **deterministic** from Companies House data — never LLM-generated. Eval: exact-match vs the API's own ground truth across the portfolio |
| Hallucinated email content | Client misinformed | Facts injected from structured data; penalty figures must carry citations verified verbatim against the guidance corpus; rubric eval; human approves every draft |
| Email sent by mistake | Reputational | Structurally impossible: no mail library exists in the codebase, enforced by a CI test (`test_never_sends.py`) |
| Companies House API downtime | Stale picture | Last-sync timestamp shown in queue and digest; cached responses; retry/backoff |
| GDPR / client data | Compliance | Company data is already public; client contacts in the demo are fictional; on-prem LLM path (Ollama) exists for data-residency requirements |
| <!-- TODO(evening 6): review-app access, key leakage, model drift --> | | |
