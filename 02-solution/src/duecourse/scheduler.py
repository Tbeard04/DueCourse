"""The weekly pipeline and its APScheduler wrapper (Mon 07:30 Europe/London).

`duecourse run-weekly --now` runs the identical pipeline once, manually.
"""

from __future__ import annotations

from datetime import date

from . import agent
from .companies_house import CompaniesHouseClient
from .config import get_settings
from .models import TriageStatus
from .store import Store
from .triage import triage_portfolio


def run_pipeline(as_of: date | None = None) -> str:
    """sync -> triage -> draft urgent items -> digest. Returns the digest markdown path."""
    from .digest import build_digest

    as_of = as_of or date.today()
    settings = get_settings()
    store = Store(settings.db_path)
    ch = CompaniesHouseClient()
    try:
        run_id = store.start_run("triage", as_of)
        deadlines = []
        for client in store.clients():
            deadlines.extend(ch.deadlines_for(client.company_number))
        items = triage_portfolio(deadlines, as_of)
        store.save_triage(run_id, items)
        store.finish_run(run_id)

        urgent = [i for i in items if i.status in (TriageStatus.OVERDUE, TriageStatus.DUE_SOON)]
        for item in urgent:
            client = store.client(item.deadline.company_number)
            if client is not None:
                store.save_draft(run_id, agent.draft_for(item, client, store=store, ch=ch))

        report = build_digest(store, as_of)
        out_dir = settings.duecourse_data_dir / "digests"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{as_of.isoformat()}.md"
        out_path.write_text(report.markdown, encoding="utf-8")
        return str(out_path)
    finally:
        ch.close()
        store.close()


def main() -> None:
    """Block and run the pipeline every Monday 07:30 (Europe/London)."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler(timezone="Europe/London")
    scheduler.add_job(run_pipeline, "cron", day_of_week="mon", hour=7, minute=30)
    scheduler.start()
