# Runbook — operating DueCourse

*Written for the practice's office manager. No Python knowledge assumed beyond copying
commands. The 10-minute walkthrough is in [06-enablement](../06-enablement/training-session.md).*

## What this system does — and will never do

DueCourse watches your client list on the Companies House public register, flags what's due,
drafts the chasing emails, and builds your Monday digest. **It never sends anything.** Every
email is a draft waiting for your decision; sending is always done by you, from your own mail
client. (This is enforced in the software itself and checked by an automated test — there is
no "send" to switch on.)

## Weekly routine (Monday)

1. The weekly run fires automatically at 07:30 (`duecourse run-weekly`, scheduled), or run it
   by hand any time:
   ```
   cd 02-solution
   uv run duecourse run-weekly --now
   ```
2. Read the digest — posted to the practice channel by the n8n workflow at 08:00, or in
   `02-solution/data/digests/<date>.md`.
3. Open the review queue:
   ```
   uv run duecourse review
   ```
   For each draft: **Approve** (copy into your mail client and send), **edit then approve**,
   or **Reject with a reason**. Reasons matter: they are fed back into next week's drafting.
4. Partner escalation stays your call — the digest's overdue section is the escalation list.

## Adding or removing a client

Edit `02-solution/portfolio.json` (company number, name, contact, notes), then:
```
uv run duecourse sync
```
Removed companies disappear from tracking; their past drafts and decisions stay in the audit
log permanently.

## Keys, and rotating them

All keys live in `02-solution/.env` (never in the code, never in git):

| Key | What stops working without it | Rotation |
| --- | --- | --- |
| `CH_API_KEY` | Everything — no register data | Free, instant: create a new key in the [Companies House developer hub](https://developer.company-information.service.gov.uk/) (Live application, REST key), paste it in, delete the old one |
| `ANTHROPIC_API_KEY` | Personalised drafts (falls back to templates); guidance Q&A | Rotate in the Anthropic console; update `.env` |
| `DUECOURSE_API_TOKEN` | The n8n digest post | Change the value in `.env`, restart the API, update the n8n credential |

After changing `.env`, restart whatever is running (scheduler, API, review app).

## What "degraded" looks like

| Symptom | Meaning | What to do |
| --- | --- | --- |
| Drafts look generic/templated, `template` in the "drafted by" line | No LLM reachable | Deadlines and digest are still correct. Check `ANTHROPIC_API_KEY`, or that Ollama is running. Not urgent |
| Drafts cite no penalties/rules | Guidance index missing | `uv run duecourse index-guidance` |
| No digest on Monday | Scheduler or n8n not running | `uv run duecourse run-weekly --now`; check n8n execution log |
| Commands fail with "CH_API_KEY is not set" | Missing/empty `.env` | Copy `.env.example` to `.env` and fill it in |
| Repeated "rate limited, retrying" messages | Companies House limit (600 requests / 5 min) | It retries by itself; just let it finish |
| Errors mentioning 401 from Companies House | Key revoked, or a Test-environment key | Create a **Live** REST key (test keys only work against sandbox data) |
| A company's dates look wrong | Check the register first | Open the company on [find-and-update.company-information.service.gov.uk](https://find-and-update.company-information.service.gov.uk/) — DueCourse shows what the register says; if the register is right and DueCourse differs, report it and trust the register |

## Backups

Everything the practice would mind losing is two files/folders, copied like any other file:
- `02-solution/data/duecourse.db` — the audit trail (drafts, decisions) and triage history
- `02-solution/portfolio.json` — the client list

Everything else (caches, the guidance index) rebuilds itself from the register and GOV.UK.

## Data notes

Company data is public register data. Client contact details live only in `portfolio.json`
and the local database — nothing is uploaded anywhere except: company numbers to Companies
House (necessarily) and, when LLM drafting is on, the deadline facts + contact first name to
the model provider. For a strict no-data-leaves-the-building policy, run the local model
(Ollama) instead — drafts get plainer; nothing else changes. See the
[risk register](risk-register.md), GDPR row.
