"""Corpus parsing and citation verification (no vector index needed for these)."""

from duecourse import rag
from duecourse.models import Citation


def test_parse_frontmatter() -> None:
    meta, body = rag.parse_frontmatter(
        "---\ntitle: Late filing penalties\nsource_url: https://example.test/x\n---\n# Heading\nBody."
    )
    assert meta == {"title": "Late filing penalties", "source_url": "https://example.test/x"}
    assert body.startswith("# Heading")


def test_chunk_markdown_by_heading() -> None:
    chunks = rag.chunk_markdown("# A\nfirst section\n\n## B\nsecond section\n")
    assert [(h, t) for h, t in chunks] == [("A", "first section"), ("B", "second section")]


def test_verify_citation_against_corpus(monkeypatch, tmp_path) -> None:
    (tmp_path / "penalties.md").write_text(
        "---\ntitle: Penalties\nsource_url: https://example.test\n---\n"
        "# Penalties\nThe penalty is £150 for accounts filed up to one month late.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(rag, "GUIDANCE_DIR", tmp_path)

    good = Citation(
        quote="The penalty is £150 for accounts   filed up to one month late.",
        source_title="Penalties",
        source_url="https://example.test",
    )
    bad = Citation(quote="The penalty is £5,000.", source_title="?", source_url="")
    assert rag.verify_citation(good) is True  # whitespace-normalised match
    assert rag.verify_citation(bad) is False
