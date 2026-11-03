"""Fetch the RAG guidance corpus (~30 pages) into guidance/*.md.

Sources: GOV.UK pages on confirmation statements, annual accounts, late-filing penalties and
deadlines (Companies House + HMRC). Each page is converted to markdown with YAML frontmatter:

    ---
    title: Late filing penalties
    source_url: https://www.gov.uk/...
    fetched_on: 2026-11-10
    ---

TODO(evening 4): implement — fetch each URL (httpx), strip to main content, convert to
markdown, write guidance/<slug>.md. Keep the list of URLs in this file so the corpus is
reproducible.

Run: uv run python scripts/fetch_guidance.py
"""

GUIDANCE_URLS: list[str] = [
    # TODO(evening 4): the ~30 GOV.UK pages, e.g.
    # "https://www.gov.uk/guidance/late-filing-penalties",
    # "https://www.gov.uk/guidance/confirmation-statement-guidance",
]

raise SystemExit("TODO(evening 4): not implemented yet — see module docstring")
