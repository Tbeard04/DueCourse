"""The duecourse CLI — every pipeline stage, runnable on its own."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from .config import get_settings
from .models import ClientCompany
from .store import Store

app = typer.Typer(help="Filing-deadline triage and reviewed chasing-email drafts. Never sends.")


@app.command()
def sync(
    portfolio: Annotated[Path, typer.Option(help="Portfolio file")] = Path("portfolio.json"),
) -> None:
    """Load the client portfolio and pull fresh Companies House data for every company."""
    from .companies_house import CompaniesHouseClient

    store = Store(get_settings().db_path)
    clients = [ClientCompany(**entry) for entry in json.loads(portfolio.read_text("utf-8"))]
    for client in clients:
        store.upsert_client(client)
    removed = store.prune_clients([client.company_number for client in clients])
    if removed:
        typer.echo(f"Pruned {removed} clients no longer in the portfolio.")
    ch = CompaniesHouseClient()
    try:
        total = 0
        for client in clients:
            total += len(ch.deadlines_for(client.company_number))
        typer.echo(f"Synced {len(clients)} companies, {total} deadlines cached.")
    finally:
        ch.close()
        store.close()


@app.command()
def triage() -> None:
    """Triage every deadline in the portfolio and print the snapshot, most urgent first."""
    from .companies_house import CompaniesHouseClient
    from .triage import triage_portfolio

    today = date.today()
    store = Store(get_settings().db_path)
    ch = CompaniesHouseClient()
    try:
        deadlines = []
        for client in store.clients():
            deadlines.extend(ch.deadlines_for(client.company_number))
        run_id = store.start_run("triage", today)
        items = triage_portfolio(deadlines, today)
        store.save_triage(run_id, items)
        store.finish_run(run_id)
        for item in items:
            typer.echo(
                f"{item.status.value:>10}  {item.deadline.company_number}"
                f"  {item.deadline.kind.value:<24} due {item.deadline.due_date}"
                f" ({item.days_until_due:+d}d)"
            )
    finally:
        ch.close()
        store.close()


@app.command()
def draft() -> None:
    """Draft a chasing email for every overdue / due-soon item into the review queue."""
    from . import agent
    from .companies_house import CompaniesHouseClient
    from .models import TriageStatus

    store = Store(get_settings().db_path)
    try:
        ch = CompaniesHouseClient()
    except ValueError:
        ch = None  # drafting still works without filing-history context
    try:
        urgent = [
            item
            for item in store.latest_triage()
            if item.status in (TriageStatus.OVERDUE, TriageStatus.DUE_SOON)
        ]
        count = 0
        for item in urgent:
            client = store.client(item.deadline.company_number)
            if client is not None:
                store.save_draft(None, agent.draft_for(item, client, store=store, ch=ch))
                count += 1
        typer.echo(f"{count} drafts queued for review. Nothing has been sent.")
    finally:
        if ch is not None:
            ch.close()
        store.close()


@app.command()
def digest() -> None:
    """Build the Monday digest from the latest triage snapshot and print it."""
    from .digest import build_digest

    store = Store(get_settings().db_path)
    try:
        typer.echo(build_digest(store, date.today()).markdown)
    finally:
        store.close()


@app.command("run-weekly")
def run_weekly(now: bool = typer.Option(False, "--now", help="Run once, immediately")) -> None:
    """Run the weekly pipeline — scheduled (blocking) by default, once with --now."""
    from . import scheduler

    if now:
        typer.echo(f"Digest written to {scheduler.run_pipeline()}")
    else:
        typer.echo("Scheduling weekly run (Mon 07:30 Europe/London). Ctrl+C to stop.")
        scheduler.main()


@app.command("index-guidance")
def index_guidance() -> None:
    """(Re)build the LanceDB index over guidance/ (RAG stack installs with plain uv sync)."""
    from . import rag

    typer.echo(f"Indexed {rag.build_index()} chunks.")


@app.command("serve-api")
def serve_api(port: int = 8000) -> None:
    """Serve the FastAPI surface consumed by the n8n wrapper."""
    import uvicorn

    uvicorn.run("duecourse.api:app", port=port)


@app.command()
def review() -> None:
    """Open the Streamlit review queue."""
    import subprocess
    import sys

    app_path = Path(__file__).resolve().parents[2] / "review_app" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=True)


if __name__ == "__main__":
    app()
