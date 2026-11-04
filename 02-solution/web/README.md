# Digest frontend

The public face of DueCourse: a **Next.js + TypeScript** app, statically exported
(`output: "export"`) and published to GitHub Pages every Monday by
[publish-digest.yml](../../.github/workflows/publish-digest.yml). The deployed site is plain
files — no server, no runtime secrets, no data fetching in the browser.

Data flows one way: the Python pipeline triages the portfolio against the live Companies House
register, then `scripts/export_digest_data.py` writes [data/digest.json](data/digest.json),
which the page imports at build time. The checked-in JSON is a fixture so a fresh clone builds;
CI regenerates it from the live register before every deploy. Only public register data is
exported — no contacts, no drafts.

```bash
cd 02-solution
uv run python scripts/export_digest_data.py   # refresh data from the local triage snapshot
cd web
npm install
npm run dev                                   # http://localhost:3000
npm run build                                 # static export to out/
```

CI builds with `PAGES_BASE_PATH=/DueCourse` because GitHub Pages serves project sites under
`/<repo>`; local builds serve from the root.

Design: WCAG AA-verified colour pairs in light and dark mode, status conveyed by text labels
(tinted tags — colour never carries meaning alone), measure capped near 65 characters, the
long "on track" tail collapsed behind a native `<details>` disclosure, and table rows that
stack on narrow screens so the urgency column is never clipped.
