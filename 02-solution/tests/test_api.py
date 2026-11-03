"""The n8n-facing API: auth is required, and no approval route exists."""

from fastapi.testclient import TestClient

from duecourse.api import app

client = TestClient(app)


def test_auth_required(monkeypatch) -> None:
    monkeypatch.setenv("DUECOURSE_API_TOKEN", "secret")
    assert client.get("/triage").status_code == 401
    assert client.get("/triage", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_unconfigured_token_rejects_everything(monkeypatch) -> None:
    monkeypatch.delenv("DUECOURSE_API_TOKEN", raising=False)
    assert client.get("/triage", headers={"Authorization": "Bearer "}).status_code == 401


def test_no_approval_route() -> None:
    """Approval happens only in the review UI — the API must not offer a way around the human."""
    paths = {route.path for route in app.routes}
    assert not any("draft" in path or "approv" in path for path in paths)
