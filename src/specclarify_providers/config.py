"""Provider configuration."""

from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    provider_name: str
    model: str
    base_url: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    timeout: float = 60.0
