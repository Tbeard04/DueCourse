"""Guidance-corpus retrieval: LanceDB over ~30 pages of CH/HMRC filing guidance.

The corpus lives in guidance/*.md, each file with YAML frontmatter (title, source_url,
fetched_on). Embeddings are local (all-MiniLM-L6-v2), so indexing and search need no API key.
Install the extra first: uv sync --extra rag
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


def build_index() -> int:
    """(Re)build the LanceDB index from guidance/. Idempotent. Returns the chunk count.

    TODO(evening 4): implement — lancedb.connect(settings.lancedb_dir), register the
    sentence-transformers embedding function, create/overwrite a 'guidance' table from
    iter_corpus(), and return len(chunks).
    """
    _ = get_settings().lancedb_dir
    raise NotImplementedError("TODO(evening 4): index iter_corpus() into LanceDB")


def search(query: str, k: int = 4) -> list[GuidanceChunk]:
    """Vector search over the guidance corpus.

    TODO(evening 4): implement — open the 'guidance' table and return the top-k chunks.
    Powers the agent's search_guidance tool and the review queue's Q&A sidebar.
    """
    raise NotImplementedError("TODO(evening 4): LanceDB search")


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
