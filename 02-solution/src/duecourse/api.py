"""Thin HTTP surface for the n8n wrapper. Bearer auth via DUECOURSE_API_TOKEN.

Deliberately NO draft-approval endpoint: approval happens only in the review UI, so the
wrapper cannot bypass the human.
"""

from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException

from .config import get_settings
from .digest import build_digest
from .store import Store

app = FastAPI(title="DueCourse", description="Read-only surface + pipeline trigger for n8n.")


def require_token(authorization: str = Header(default="")) -> None:
    expected = get_settings().duecourse_api_token
    if not expected or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="missing or invalid bearer token")


@app.get("/digest/latest", dependencies=[Depends(require_token)])
def latest_digest() -> dict:
    store = Store(get_settings().db_path)
    try:
        report = build_digest(store, date.today())
        return report.model_dump(mode="json")
    finally:
        store.close()


@app.get("/triage", dependencies=[Depends(require_token)])
def triage_snapshot(status: str | None = None) -> list[dict]:
    store = Store(get_settings().db_path)
    try:
        items = store.latest_triage()
        if status is not None:
            items = [item for item in items if item.status.value == status]
        return [item.model_dump(mode="json") for item in items]
    finally:
        store.close()


@app.post("/run", status_code=202, dependencies=[Depends(require_token)])
def trigger_run() -> dict:
    """Kick off the weekly pipeline. Runs synchronously for now.

    TODO(evening 6): move to a background task and return a poll-able run id.
    """
    from .scheduler import run_pipeline

    digest_path = run_pipeline()
    return {"status": "completed", "digest": digest_path}
