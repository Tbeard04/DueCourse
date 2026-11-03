# n8n wrapper — the client-ownable surface

One workflow a non-technical staff member can open and modify: schedule trigger (Mon 08:00) →
HTTP Request to `GET /digest/latest` (bearer token from `DUECOURSE_API_TOKEN`) → format →
post to the practice's Slack/Teams/webhook.

TODO(evening 6): build in n8n and export over `workflow.json`.
