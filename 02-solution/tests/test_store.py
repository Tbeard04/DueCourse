"""The audit trail: drafts in, decisions appended, rejection reasons surfaced."""

from datetime import UTC, date, datetime

import pytest

from duecourse.agent import template_draft
from duecourse.models import ReviewDecision
from duecourse.store import Store
from duecourse.triage import triage


@pytest.fixture
def store(tmp_path) -> Store:
    return Store(tmp_path / "test.db")


def test_draft_review_roundtrip(store, deadline, client_company) -> None:
    item = triage(deadline, date(2026, 11, 25))
    store.upsert_client(client_company)
    draft = template_draft(item, client_company)
    store.save_draft(None, draft)

    pending = store.pending_drafts()
    assert [d.id for d in pending] == [draft.id]
    assert pending[0].triage_item.days_until_due == item.days_until_due
    assert pending[0].model_used == "template"

    store.record_decision(
        ReviewDecision(
            draft_id=draft.id,
            action="rejected",
            reason="tone too pushy for a long-standing client",
            decided_at=datetime.now(UTC),
        )
    )
    assert store.pending_drafts() == []
    assert store.recent_rejections() == ["tone too pushy for a long-standing client"]
    assert store.decision_stats() == {"rejected": 1}


def test_rejection_requires_reason(store, deadline, client_company) -> None:
    item = triage(deadline, date(2026, 11, 25))
    draft = template_draft(item, client_company)
    store.save_draft(None, draft)
    with pytest.raises(ValueError, match="reason"):
        store.record_decision(
            ReviewDecision(draft_id=draft.id, action="rejected", decided_at=datetime.now(UTC))
        )
