"""Guidance-corpus retrieval: LanceDB over ~30 pages of CH/HMRC filing guidance.

The corpus lives in guidance/*.md, each file with YAML frontmatter (title, source_url,
fetched_on). Embeddings are local (all-MiniLM-L6-v2), so indexing and search need no API key.
The RAG stack installs with a plain `uv sync` (the "rag" default group).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import get_settings
from .models import Citation

GUIDANCE_DIR = Path(__file__).resolve().parents[2] / "guidance"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_CHUNK_CHARS = 1600  # ~400 tokens


@dataclass
class GuidanceChunk:
    text: str
    heading_path: str
    source_title: str
    source_url: str


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Minimal YAML frontmatter parser: `key: value` lines between --- fences."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, match.group(2)


def chunk_markdown(body: str) -> list[tuple[str, str]]:
    """Split a markdown body by heading; returns (heading_path, chunk_text) pairs.

    Oversized sections are split on paragraph boundaries at MAX_CHUNK_CHARS.
    """
    chunks: list[tuple[str, str]] = []
    heading = ""
    buffer: list[str] = []

    def flush() -> None:
        text = "\n".join(buffer).strip()
        buffer.clear()
        if not text:
            return
        while len(text) > MAX_CHUNK_CHARS:
            split_at = text.rfind("\n\n", 0, MAX_CHUNK_CHARS)
            if split_at <= 0:
                split_at = MAX_CHUNK_CHARS
            chunks.append((heading, text[:split_at].strip()))
            text = text[split_at:].strip()
        chunks.append((heading, text))

    for line in body.splitlines():
        if line.startswith("#"):
            flush()
            heading = line.lstrip("#").strip()
        else:
            buffer.append(line)
    flush()
    return chunks


def iter_corpus() -> list[GuidanceChunk]:
    out: list[GuidanceChunk] = []
    for path in sorted(GUIDANCE_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        for heading_path, text in chunk_markdown(body):
            out.append(
                GuidanceChunk(
                    text=text,
                    heading_path=heading_path,
                    source_title=meta.get("title", path.stem),
                    source_url=meta.get("source_url", ""),
                )
            )
    return out


class GuidanceUnavailable(RuntimeError):
    """Raised when the RAG stack is not installed or the index has not been built."""


def _embedding_fn():
    try:
        from lancedb.embeddings import get_registry
    except ImportError as exc:  # pragma: no cover
        raise GuidanceUnavailable("RAG stack not installed — run: uv sync") from exc
    return get_registry().get("sentence-transformers").create(name=EMBEDDING_MODEL)


def build_index() -> int:
    """(Re)build the LanceDB index from guidance/. Idempotent. Returns the chunk count."""
    import lancedb
    from lancedb.pydantic import LanceModel, Vector

    chunks = iter_corpus()
    if not chunks:
        raise GuidanceUnavailable(
            "guidance/ is empty — run: uv run python scripts/fetch_guidance.py"
        )
    func = _embedding_fn()

    class GuidanceRecord(LanceModel):
        text: str = func.SourceField()
        vector: Vector(func.ndims()) = func.VectorField()  # type: ignore[valid-type]
        heading_path: str
        source_title: str
        source_url: str

    db = lancedb.connect(str(get_settings().lancedb_dir))
    table = db.create_table("guidance", schema=GuidanceRecord, mode="overwrite")
    table.add(
        [
            {
                "text": c.text,
                "heading_path": c.heading_path,
                "source_title": c.source_title,
                "source_url": c.source_url,
            }
            for c in chunks
        ]
    )
    return len(chunks)


def search(query: str, k: int = 4) -> list[GuidanceChunk]:
    """Vector search over the guidance corpus — powers the agent's search_guidance tool
    and the review queue's Q&A sidebar."""
    try:
        import lancedb
    except ImportError as exc:  # pragma: no cover
        raise GuidanceUnavailable("RAG stack not installed — run: uv sync") from exc

    db = lancedb.connect(str(get_settings().lancedb_dir))
    try:
        table = db.open_table("guidance")
    except Exception as exc:
        raise GuidanceUnavailable("index not built — run: uv run duecourse index-guidance") from exc
    _embedding_fn()  # ensures the query-embedding function is registered
    rows = table.search(query).limit(k).to_list()
    return [
        GuidanceChunk(
            text=row["text"],
            heading_path=row["heading_path"],
            source_title=row["source_title"],
            source_url=row["source_url"],
        )
        for row in rows
    ]


QA_INSTRUCTIONS = """\
You answer a UK accountancy practice's questions about Companies House / HMRC filing rules.
Use ONLY the guidance extracts provided. Quote figures exactly as written. If the extracts do
not contain the answer, say so plainly. Under 150 words; name the source title(s) you used.
"""


def answer(question: str, k: int = 4) -> tuple[str | None, list[GuidanceChunk]]:
    """The review queue's "what if it's late?" Q&A. Returns (answer, sources).

    With no LLM configured the answer is None and the caller shows the raw extracts —
    retrieval alone still works (local embeddings, no key needed).
    """
    chunks = search(question, k)
    from . import llm  # local import: avoids a cycle at module load

    model = llm.get_model("draft")
    if model is None:
        return None, chunks
    from pydantic_ai import Agent

    qa = Agent(model, instructions=QA_INSTRUCTIONS)
    context = "\n\n".join(f"### {c.source_title} ({c.source_url})\n{c.text}" for c in chunks)
    result = qa.run_sync(f"Guidance extracts:\n\n{context}\n\nQuestion: {question}")
    return result.output, chunks


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_citation(citation: Citation) -> bool:
    """True when the quoted text exists (whitespace-normalised) in the guidance corpus.

    The citation eval's core check: every quoted rule must exist in a source, not model memory.
    """
    needle = _normalise(citation.quote)
    if not needle:
        return False
    for path in GUIDANCE_DIR.glob("*.md"):
        _, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if needle in _normalise(body):
            return True
    return False
