# Guidance corpus

The RAG source: ~30 pages of Companies House / HMRC filing guidance, fetched by
`scripts/fetch_guidance.py`. Every penalty figure or rule a draft quotes must exist verbatim in
one of these files (`rag.verify_citation` enforces it).

Each file is markdown with YAML frontmatter:

```markdown
---
title: Late filing penalties
source_url: https://www.gov.uk/guidance/late-filing-penalties
fetched_on: 2026-11-10
---

# Late filing penalties
...
```

The corpus is committed so the demo is reproducible; re-fetch to refresh.
