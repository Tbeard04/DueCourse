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
    """Return a Pydantic AI model, or None when no provider exists.

    The API key comes from .env via Settings (not ambient os.environ), so providers are
    constructed explicitly rather than through pydantic-ai's env-var discovery.
    """
    settings = get_settings()
    if settings.anthropic_api_key:
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        model_id = settings.draft_model if purpose == "draft" else settings.judge_model
        return AnthropicModel(
            model_id, provider=AnthropicProvider(api_key=settings.anthropic_api_key)
        )
    if _ollama_reachable(settings.ollama_base_url):
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
    return getattr(model, "model_name", None) or str(model)
