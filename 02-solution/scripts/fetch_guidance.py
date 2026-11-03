"""Fetch the RAG guidance corpus into guidance/*.md.

Sources: GOV.UK pages on confirmation statements, annual accounts, late-filing penalties,
strike-off and company tax deadlines, pulled through the GOV.UK Content API
(https://www.gov.uk/api/content/<path>) rather than HTML scraping. Multi-part "guide" pages
yield one markdown file per part, which is how ~15 entries become ~30 corpus pages.

Each file gets YAML frontmatter (title, source_url, fetched_on) that rag.py relies on.
Re-run any time to refresh the corpus; the URL list below keeps it reproducible.

Run from 02-solution:  uv run python scripts/fetch_guidance.py
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import httpx

try:
    import html2text
except ImportError:  # pragma: no cover
    sys.exit("html2text missing — install dev deps: uv sync --dev")

API = "https://www.gov.uk/api/content"
OUT_DIR = Path(__file__).resolve().parents[1] / "guidance"

# GOV.UK content paths. Simple pages give one file; guides give one file per part.
# Checked against the Content API on 2026-11-03 — slugs move, so re-verify on refresh.
PAGES = [
    "/annual-accounts",  # includes the penalties-for-late-filing part (the £150+ table)
    "/appeal-a-penalty-for-filing-your-company-accounts-late",
    "/government/publications/late-filing-penalties-from-companies-house",
    "/guidance/applying-for-more-time-to-file-your-companys-accounts",
    "/guidance/filing-your-companys-confirmation-statement",
    "/prepare-file-annual-accounts-for-limited-company",
    "/running-a-limited-company",
    "/company-tax-returns",
    "/dormant-company",
    "/first-company-accounts-and-return",
    "/pay-corporation-tax",
]


def to_markdown(html: str) -> str:
    converter = html2text.HTML2Text()
    converter.body_width = 0  # no hard wrapping — keeps quotes verbatim-matchable
    converter.ignore_images = True
    converter.ignore_emphasis = True
    return converter.handle(html).strip()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def write_page(slug: str, title: str, source_url: str, markdown: str) -> None:
    body = f"---\ntitle: {title}\nsource_url: {source_url}\nfetched_on: {date.today()}\n---\n\n{markdown}\n"
    (OUT_DIR / f"{slug}.md").write_text(body, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    written = 0
    with httpx.Client(timeout=30, follow_redirects=True) as http:
        for path in PAGES:
            response = http.get(f"{API}{path}")
            if response.status_code != 200:
                print(f"SKIP {path} -> HTTP {response.status_code}")
                continue
            content = response.json()
            title = content.get("title", path)
            base_url = f"https://www.gov.uk{path}"
            details = content.get("details", {})
            parts = details.get("parts")
            if parts:  # multi-part guide: one corpus page per part
                for part in parts:
                    part_title = f"{title} — {part['title']}"
                    part_url = f"{base_url}/{part['slug']}"
                    write_page(
                        f"{slugify(title)}--{slugify(part['title'])}",
                        part_title,
                        part_url,
                        to_markdown(part.get("body", "")),
                    )
                    written += 1
                print(f"OK   {path} ({len(parts)} parts)")
            else:
                body = details.get("body", "")
                if not body:
                    print(f"SKIP {path} -> no body in content API response")
                    continue
                write_page(slugify(title), title, base_url, to_markdown(body))
                written += 1
                print(f"OK   {path}")
    print(f"Wrote {written} corpus pages to {OUT_DIR}")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
