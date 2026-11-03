"""The review queue: approve / edit / reject every draft. The human-in-the-loop surface.

Run with: duecourse review   (or: streamlit run review_app/app.py)
"""

from datetime import UTC, datetime

import streamlit as st

from duecourse.config import get_settings
from duecourse.models import ReviewDecision, TriageStatus
from duecourse.store import Store

st.set_page_config(page_title="DueCourse — review queue", layout="wide")


@st.cache_resource
def get_store() -> Store:
    return Store(get_settings().db_path)


store = get_store()

# --- header: the practice dashboard -----------------------------------------
items = store.latest_triage()
overdue = sum(1 for i in items if i.status == TriageStatus.OVERDUE)
due_soon = sum(1 for i in items if i.status == TriageStatus.DUE_SOON)
pending = store.pending_drafts()

st.title("DueCourse review queue")
col1, col2, col3 = st.columns(3)
col1.metric("Overdue", overdue)
col2.metric("Due ≤14 days", due_soon)
col3.metric("Drafts awaiting review", len(pending))
st.caption("Nothing is ever sent by this system. Approved drafts are yours to copy and send.")

# --- sidebar: guidance Q&A ---------------------------------------------------
with st.sidebar:
    st.header("Ask about a deadline")
    question = st.text_input("e.g. what happens if accounts are a month late?")
    if question:
        # TODO(evening 4): rag.search(question) + LLM answer restricted to retrieved chunks,
        # citations rendered as links.
        st.info("Guidance Q&A arrives with the RAG index (evening 4).")

# --- the queue ---------------------------------------------------------------
if not pending:
    st.success("Queue is empty — nothing waiting for review.")

for draft in pending:
    item = draft.triage_item
    with st.container(border=True):
        st.subheader(draft.subject)
        st.markdown(
            f"**Deterministic facts** (from Companies House, not the LLM): "
            f"`{item.deadline.kind.value}` due `{item.deadline.due_date}` "
            f"(`{item.days_until_due:+d}` days) — status `{item.status.value}` · "
            f"drafted by `{draft.model_used}`"
        )
        body = st.text_area("Draft", draft.body, height=220, key=f"body-{draft.id}")
        if draft.citations:
            st.markdown("**Citations:**")
            for citation in draft.citations:
                st.markdown(
                    f"- “{citation.quote}” — [{citation.source_title}]({citation.source_url})"
                )

        approve, reject = st.columns(2)
        edited = body != draft.body
        if approve.button("Approve (as edited)" if edited else "Approve", key=f"a-{draft.id}"):
            store.record_decision(
                ReviewDecision(
                    draft_id=draft.id,
                    action="edited" if edited else "approved",
                    edited_body=body if edited else None,
                    decided_at=datetime.now(UTC),
                )
            )
            st.rerun()
        reason = reject.text_input("Rejection reason (required)", key=f"r-{draft.id}")
        if reject.button("Reject", key=f"x-{draft.id}"):
            if not reason:
                st.error("A rejection needs a reason — it feeds next week's drafting.")
            else:
                store.record_decision(
                    ReviewDecision(
                        draft_id=draft.id,
                        action="rejected",
                        reason=reason,
                        decided_at=datetime.now(UTC),
                    )
                )
                st.rerun()
