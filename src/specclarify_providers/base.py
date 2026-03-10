"""Provider interface for SpecClarify LLM integration."""

from typing import Protocol

from specclarify_core.schema import SpecClarifyOutput


class ClarifyProvider(Protocol):
    """Protocol for requirement clarification providers."""

    def clarify(
        self,
        raw_requirement: str,
        rules_baseline: SpecClarifyOutput | None = None,
    ) -> SpecClarifyOutput:
        """Clarify a raw requirement, optionally refining a rules baseline."""
        ...
