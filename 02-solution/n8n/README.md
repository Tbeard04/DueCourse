# n8n wrapper — the client-ownable surface

One small workflow a non-technical staff member can open, understand, and modify without
touching Python: every Monday at 08:00 it fetches the digest from the DueCourse API and posts
it to the practice's channel (Slack/Teams/anything with an incoming webhook).

**Why it exists:** the practice owns its own plumbing. Want the digest on Fridays too? At
07:00? Posted to two channels? Those are drag-and-drop changes in n8n, not code changes —
that's the handover story.

**What it deliberately cannot do:** approve drafts. The API has no approval endpoint, so no
workflow built on it can bypass the human review queue.

## Setup (once)

1. Start the API: `uv run duecourse serve-api` (from `02-solution/`).
2. Import `workflow.json` into n8n (*Workflows → Import from file*).
3. Create the **DueCourse API token** credential (type: *Header Auth*): name `Authorization`,
   value `Bearer <DUECOURSE_API_TOKEN from .env>`.
4. Set the `PRACTICE_WEBHOOK_URL` environment variable in n8n to your channel's incoming
   webhook, or replace the last node with a native Slack/Teams node.
5. Activate the workflow.

## The flow

`Monday 08:00 (schedule)` → `GET /digest/latest (bearer auth)` → `Format message (one-line
headline + full markdown)` → `POST to practice webhook`.

Note the API URL is `http://127.0.0.1:8000`, not `localhost`: n8n runs on Node, which resolves
`localhost` to IPv6 (`::1`) first, while uvicorn listens on IPv4 — `localhost` here fails with
"service refused the connection".

## Verified

The full loop was tested locally (2026-11-03): manual execution → authenticated digest fetch →
format → POST received by a second n8n workflow's webhook. Testing tip: "Listen for test
event" cancels when you switch workflows — instead, **activate** the receiver workflow and
post to its production URL (`/webhook/<path>`, not `/webhook-test/<path>`), then read the
arrivals in its Executions tab.
