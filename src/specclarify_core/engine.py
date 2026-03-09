"""SpecClarify engine placeholder."""

from .schema import SpecClarifyOutput


def clarify(raw_requirement: str) -> SpecClarifyOutput:
    """
    Placeholder: takes a raw requirement string and returns a dummy output.
    No real intelligence yet.
    """
    return SpecClarifyOutput(
        confirmed=["[placeholder] confirmed"],
        missing=["[placeholder] missing"],
        must_ask=["[placeholder] must_ask"],
        assumptions=["[placeholder] assumption"],
        risks=["[placeholder] risk"],
        draft_spec="[placeholder] draft_spec",
    )
