# Risk register

*The question each row answers: what could hurt the practice, how would we notice, and what
already stands in the way. Likelihood/impact: L/M/H.*

| # | Risk | L | I | Mitigation (built, not promised) | Early warning sign |
| --- | --- | --- | --- | --- | --- |
| 1 | **Wrong deadline shown** → client fined £150–£1,500 | L | H | Deadlines/urgency computed deterministically from Companies House data — never LLM-generated; `today` injected, boundary-tested; eval re-verifies the whole portfolio against the live API (last run: 120/120) | Any triage-eval miss diagnosed as "triage bug" (vs register change) |
| 2 | **Hallucinated email content** (invented penalty, wrong consequence) | M | H | Facts injected from structured data; penalties/rules must be quoted verbatim from the GOV.UK corpus and every quote is machine-verified (110/110 valid in the model eval); human approves every draft; rubric eval tracks `no_invented_details` | Citation-validity below 100% in an eval run; reviewer rejections citing wrong facts |
| 3 | **An email is sent by mistake** | Very L | H | Structural: no mail library exists in the codebase; a CI test fails the build if one is ever imported; the API has no approval endpoint, so no automation can bypass the queue | `test_never_sends` failing in CI |
| 4 | **Missed deadline because the system was quietly down** | M | M | Digest is a heartbeat — no Monday digest is itself the alarm; `run-weekly --now` manual fallback; last-sync visible; the old spreadsheet can be regenerated from `duecourse triage` output at any time | No digest in the channel on Monday 08:05 |
| 5 | **Companies House API downtime / rate limiting** | M | L | Retry with backoff (600 req/5 min respected); every response cached locally, so the last-known picture survives outages; weekly cadence tolerates hours of downtime | Repeated retry warnings in the run log |
| 6 | **GDPR / client data leaving the practice** | L | M | Register data is public; contacts stay in local files/DB; with LLM drafting on, only deadline facts + contact first name reach the provider; documented on-prem path (Ollama) for a no-egress policy — known cost: the local 8B model failed structured output 17/20, so budget for a larger local model | A client or partner raises a data-handling question the runbook's data note can't answer |
| 7 | **Key leakage** (`.env`) | L | M | `.env` gitignored; keys never printed in logs or drafts; rotation steps in the runbook for all three keys; CH key is free to rotate instantly | A key appears in any committed file or log |
| 8 | **Review app exposed beyond the practice** | L | M | Runs on localhost for a single operator by design; no auth is a *stated* limitation — production path is the practice's SSO in front of a proper web app (see README) | Anyone asks to use it from outside the office machine |
| 9 | **Model drift / provider price changes degrade drafts or economics** | M | L | Model choice is config, not code (`DRAFT_MODEL`); the model-comparison eval is re-runnable in minutes and the memo states when to revisit; provenance (`model_used`) logged per draft | Rising rejection rate in the decision log; judge pass-rate drop on a re-run |
| 10 | **Feedback loop poisons the prompt** (sarcastic/one-off rejection reasons steering all future drafts) | L | L | Only the last 5 reasons are injected, as guidance not rules; reviewer sees every draft anyway — the loop can't bypass the human | Drafts suddenly share an odd new habit traceable to one rejection reason |
| 11 | **Two sources of truth** (old spreadsheet kept alive alongside DueCourse) | M | M | Handover plan retires the spreadsheet after two clean parallel weeks; portfolio.json is the single client list, synced with one command | Spreadsheet edits reappearing after week 2 |
| 12 | **Bus factor: nobody at the practice can operate it** | M | M | Runbook written for the office manager; 10-minute recorded training session; everything driven by four commands; backups are two files | A question the runbook can't answer during the parallel-run fortnight |

**Residual risk accepted:** draft prose quality varies with the model (rubric pass-rates in
[03-evals/results](../03-evals/results/results.md)) — acceptable because every draft passes a
human; and the single-operator review app is not multi-user — acceptable at a 3-partner
practice, revisit at scale.
