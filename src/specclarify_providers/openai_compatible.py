"""OpenAI-compatible LLM provider (OpenAI, Ollama, LM Studio, etc.)."""

import json
import os

from specclarify_core.schema import SpecClarifyOutput

from .config import ProviderConfig

CLARIFY_PROMPT = """You are a requirement clarification assistant. Given a raw software requirement, produce a structured clarification.

Return ONLY valid JSON matching this schema (no markdown, no extra text):
{{
  "confirmed": ["string"],
  "missing": ["string"],
  "must_ask": ["string"],
  "assumptions": ["string"],
  "risks": ["string"],
  "draft_spec": "string"
}}

Raw requirement:
---
{raw}
---
"""

HYBRID_PROMPT = """You are a requirement clarification assistant. Refine the following rules-based clarification. Keep the same JSON schema.

Return ONLY valid JSON matching this schema (no markdown, no extra text):
{{
  "confirmed": ["string"],
  "missing": ["string"],
  "must_ask": ["string"],
  "assumptions": ["string"],
  "risks": ["string"],
  "draft_spec": "string"
}}

Raw requirement:
---
{raw}
---

Rules baseline:
---
{baseline}
---
"""


class OpenAICompatibleProvider:
    """Provider for OpenAI-compatible endpoints."""

    def __init__(self, config: ProviderConfig):
        self._config = config

    def clarify(
        self,
        raw_requirement: str,
        rules_baseline: SpecClarifyOutput | None = None,
    ) -> SpecClarifyOutput:
        from openai import OpenAI

        api_key = os.environ.get(self._config.api_key_env)
        if not api_key:
            raise ValueError(
                f"API key not found. Set {self._config.api_key_env} environment variable."
            )

        client = OpenAI(
            api_key=api_key,
            base_url=self._config.base_url,
        )

        if rules_baseline is not None:
            baseline_str = self._format_baseline(rules_baseline)
            prompt = HYBRID_PROMPT.format(raw=raw_requirement, baseline=baseline_str)
        else:
            prompt = CLARIFY_PROMPT.format(raw=raw_requirement)

        response = client.chat.completions.create(
            model=self._config.model,
            messages=[{"role": "user", "content": prompt}],
            timeout=self._config.timeout,
        )
        content = response.choices[0].message.content if response.choices else ""
        if not content:
            raise ValueError("Empty response from model")

        return self._parse_response(content)

    def _format_baseline(self, out: SpecClarifyOutput) -> str:
        return json.dumps(
            {
                "confirmed": out.confirmed,
                "missing": out.missing,
                "must_ask": out.must_ask,
                "assumptions": out.assumptions,
                "risks": out.risks,
                "draft_spec": out.draft_spec,
            },
            indent=2,
        )

    def _parse_response(self, content: str) -> SpecClarifyOutput:
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        data = json.loads(content)
        return SpecClarifyOutput(
            confirmed=list(data.get("confirmed", [])),
            missing=list(data.get("missing", [])),
            must_ask=list(data.get("must_ask", [])),
            assumptions=list(data.get("assumptions", [])),
            risks=list(data.get("risks", [])),
            draft_spec=str(data.get("draft_spec", "")),
        )
