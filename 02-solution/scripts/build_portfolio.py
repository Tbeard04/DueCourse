"""Build the 60-company demo portfolio (portfolio.json).

Picks real, active UK companies from the Companies House advanced-search endpoint so the
portfolio has a realistic staggered spread of due dates, then attaches FICTIONAL practice
contacts — never real people or addresses.

TODO(evening 2): implement —
  - GET /advanced-search/companies (company_status=active, varied incorporation months)
  - sample ~60 across SIC codes / incorporation dates for staggered deadlines
  - write portfolio.json: [{company_number, name, contact_name, contact_email, notes}, ...]
    with contacts from a fictional-name generator and @example.test addresses.

Run: uv run python scripts/build_portfolio.py
"""

raise SystemExit("TODO(evening 2): not implemented yet — see module docstring")
