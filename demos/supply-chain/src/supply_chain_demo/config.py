"""Environment configuration and OpenAI-compatible ChatOpenAI factory."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class Settings(BaseModel):
    """Runtime settings for the LiteLLM/vLLM OpenAI endpoint and mock API server."""

    openai_base_url: str = "http://localhost:4000/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    mock_api_base_url: str = "http://127.0.0.1:8000"
    llm_temperature: float = 0.0


def load_settings(dotenv_path: str | Path | None = None) -> Settings:
    """Load settings from `.env` (if present) and process environment variables."""
    load_dotenv(dotenv_path=dotenv_path, override=False)
    temp_raw = os.getenv("LLM_TEMPERATURE", "0.0").strip()
    try:
        temperature = float(temp_raw)
    except ValueError:
        temperature = 0.0

    return Settings(
        openai_base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        mock_api_base_url=os.getenv("MOCK_API_BASE_URL", "http://127.0.0.1:8000").strip(),
        llm_temperature=temperature,
    )


def validate_llm_config(settings: Settings) -> None:
    """Validate that required OpenAI-compatible credentials and base URL are configured."""
    if not settings.openai_base_url:
        raise ValueError(
            "OPENAI_BASE_URL is empty. Copy `.env.example` to `.env` and set your LiteLLM/vLLM base URL."
        )
    if not settings.openai_api_key or settings.openai_api_key == "sk-replace-me":
        raise ValueError(
            "OPENAI_API_KEY is missing or still set to 'sk-replace-me'. "
            "Copy `.env.example` to `.env` and set your real API key."
        )
    if not settings.openai_model:
        raise ValueError("OPENAI_MODEL is empty. Set it in `.env` (e.g., gpt-4o-mini or your vLLM model).")


def build_chat_model(settings: Settings | None = None, *, validate: bool = True) -> ChatOpenAI:
    """Instantiate an official ChatOpenAI client pointing at the custom LiteLLM/vLLM gateway."""
    resolved = settings or load_settings()
    if validate:
        validate_llm_config(resolved)

    return ChatOpenAI(
        model=resolved.openai_model,
        base_url=resolved.openai_base_url,
        api_key=resolved.openai_api_key,
        temperature=resolved.llm_temperature,
        use_responses_api=False,
    )
