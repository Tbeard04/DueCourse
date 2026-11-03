"""Render the latest triage snapshot as a static HTML digest page (site/index.html).

Published every Monday by .github/workflows/publish-digest.yml via GitHub Pages — the free,
public, read-only face of DueCourse. Deliberately shows only public register data (company
names, filing kinds, due dates, urgency): no contacts, no drafts, no LLM involved anywhere.

Run from 02-solution:  uv run python scripts/render_digest_page.py [out_dir]
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from duecourse.config import get_settings
from duecourse.models import TriageStatus
from duecourse.store import Store

SECTIONS = [
    (TriageStatus.OVERDUE, "Overdue", "overdue"),
    (TriageStatus.DUE_SOON, "Due within 14 days", "due-soon"),
    (TriageStatus.UPCOMING, "Due within 30 days", "upcoming"),
    (TriageStatus.OK, "On track", "ok"),
]

CSS = """
:root { color-scheme: light dark;
  --bg: #f6f7f9; --card: #ffffff; --text: #1a202c; --muted: #64748b; --line: #e2e8f0;
  --overdue: #dc2626; --due-soon: #d97706; --upcoming: #ca8a04; --ok: #16a34a; }
@media (prefers-color-scheme: dark) { :root {
  --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8; --line: #334155; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 880px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
.sub { color: var(--muted); margin: 0 0 24px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin-bottom: 28px; }
.tile { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px 16px; }
.tile b { display: block; font-size: 1.8rem; }
.tile span { color: var(--muted); font-size: .85rem; }
section { margin-bottom: 28px; }
h2 { font-size: 1.05rem; margin: 0 0 10px; }
table { width: 100%; border-collapse: collapse; background: var(--card);
  border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
th, td { text-align: left; padding: 9px 12px; border-top: 1px solid var(--line);
  font-size: .92rem; }
thead th { border-top: none; color: var(--muted); font-weight: 600; font-size: .8rem;
  text-transform: uppercase; letter-spacing: .04em; }
.days { white-space: nowrap; font-variant-numeric: tabular-nums; }
.badge { display: inline-block; padding: 1px 9px; border-radius: 99px; font-size: .78rem;
  font-weight: 600; color: #fff; }
.b-overdue { background: var(--overdue); } .b-due-soon { background: var(--due-soon); }
.b-upcoming { background: var(--upcoming); } .b-ok { background: var(--ok); }
footer { color: var(--muted); font-size: .85rem; border-top: 1px solid var(--line);
  padding-top: 16px; }
footer a { color: inherit; }
"""


def main() -> int:
    out_dir = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "site"
    )
    store = Store(get_settings().db_path)
    items = store.latest_triage()
    if not items:
        sys.exit("No triage snapshot — run: uv run duecourse triage")
    names = {}
    for item in items:
        number = item.deadline.company_number
        if number not in names:
            client = store.client(number)
            names[number] = client.name if client else number
    store.close()

    as_of = items[0].as_of
    counts = {status: sum(1 for i in items if i.status == status) for status, _, _ in SECTIONS}

    tiles = "".join(
        f'<div class="tile"><b>{counts[status]}</b><span>{label}</span></div>'
        for status, label, _ in SECTIONS
    )
    sections = []
    for status, label, slug in SECTIONS:
        rows = [i for i in items if i.status == status]
        if not rows:
            continue
        body = "".join(
            f"<tr><td>{escape(names[i.deadline.company_number])}"
            f'<br><span style="color:var(--muted);font-size:.8rem">'
            f"{escape(i.deadline.company_number)}</span></td>"
            f"<td>{escape(i.deadline.kind.value.replace('_', ' '))}</td>"
            f"<td>{i.deadline.due_date.isoformat()}</td>"
            f'<td class="days">{i.days_until_due:+d} days</td>'
            f'<td><span class="badge b-{slug}">{escape(label)}</span></td></tr>'
            for i in rows
        )
        sections.append(
            f"<section><h2>{escape(label)} ({len(rows)})</h2><table>"
            "<thead><tr><th>Company</th><th>Filing</th><th>Due</th><th>Days</th>"
            f"<th>Status</th></tr></thead><tbody>{body}</tbody></table></section>"
        )

    generated = datetime.now(UTC).strftime("%A %d %B %Y, %H:%M UTC")
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DueCourse digest</title>
<style>{CSS}</style>
</head>
<body><main>
<h1>DueCourse — weekly filing digest</h1>
<p class="sub">A demo accountancy portfolio of {len(names)} real UK companies, triaged against
the live Companies House register · snapshot as of {as_of.strftime("%d %B %Y")}</p>
<div class="tiles">{tiles}</div>
{"".join(sections)}
<footer>
<p>Regenerated every Monday by a scheduled GitHub Action — no servers, no manual steps.
Deadlines and urgency are computed deterministically from
<a href="https://developer.company-information.service.gov.uk/">Companies House public data</a>;
no AI touches this page. The human-in-the-loop drafting and review queue run privately inside
the practice — <a href="https://github.com/Tbeard04/DueCourse">source and engagement pack</a>.
Nothing is ever sent automatically. Generated {generated}.</p>
</footer>
</main></body></html>
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Wrote {out_dir / 'index.html'} ({len(items)} deadlines, as of {as_of})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
