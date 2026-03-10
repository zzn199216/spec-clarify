"""High-level service layer for SpecClarify."""

from .engine import clarify
from .schema import SpecClarifyOutput


def run_clarify(
    raw_requirement: str,
    mode: str = "rules",
    provider=None,
) -> SpecClarifyOutput:
    """
    Run clarification in the given mode.

    - rules: use deterministic engine only
    - llm: use provider only
    - hybrid: run rules first, then provider to refine
    """
    if mode == "rules":
        return clarify(raw_requirement)

    if provider is None:
        raise ValueError(
            "Provider required for llm or hybrid mode. "
            "Use --provider openai-compatible and configure model/base-url/api-key."
        )

    if mode == "llm":
        return provider.clarify(raw_requirement, rules_baseline=None)

    if mode == "hybrid":
        rules_out = clarify(raw_requirement)
        return provider.clarify(raw_requirement, rules_baseline=rules_out)

    raise ValueError(f"Unknown mode: {mode}. Use rules, llm, or hybrid.")
