"""LLM provider selection: Anthropic -> local Ollama -> None (deterministic templates).

The chosen provider is stamped into every draft's model_used field — provenance in the audit
trail. With no provider at all, triage and the digest still work; only draft quality drops.
"""

from __future__ import annotations

from typing import Literal

import httpx

from .config import get_settings

OLLAMA_DRAFT_MODEL = "llama3.1:8b"


def _ollama_reachable(base_url: str) -> bool:
    try:
        return httpx.get(f"{base_url}/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def get_model(purpose: Literal["draft", "judge"] = "draft"):
    """Return a Pydantic AI model (or model name string), or None when no provider exists.

    Pydantic AI accepts 'anthropic:<model-id>' strings directly; the Ollama path goes through
    its OpenAI-compatible endpoint.
    """
    settings = get_settings()
    if settings.anthropic_api_key:
        model_id = settings.draft_model if purpose == "draft" else settings.judge_model
        return f"anthropic:{model_id}"
    if _ollama_reachable(settings.ollama_base_url):
        # TODO(evening 3): verify against the installed pydantic-ai version.
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.ollama import OllamaProvider

        return OpenAIChatModel(
            OLLAMA_DRAFT_MODEL,
            provider=OllamaProvider(base_url=f"{settings.ollama_base_url}/v1"),
        )
    return None


def describe_model(model) -> str:
    """Human-readable provenance string for model_used."""
    if model is None:
        return "template"
    if isinstance(model, str):
        return model
    return f"ollama:{OLLAMA_DRAFT_MODEL}"
