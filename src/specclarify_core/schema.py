"""SpecClarify v0.1 output schema."""

from dataclasses import dataclass


@dataclass
class SpecClarifyOutput:
    """Output schema for SpecClarify v0.1."""

    confirmed: list[str]
    missing: list[str]
    must_ask: list[str]
    assumptions: list[str]
    risks: list[str]
    draft_spec: str
