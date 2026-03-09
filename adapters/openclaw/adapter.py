"""OpenClaw adapter: thin wrapper around SpecClarify core."""

from specclarify_core.engine import clarify


def clarify_requirement(raw: str) -> dict:
    """
    Call SpecClarify core and return a JSON-serializable dict.
    """
    out = clarify(raw)
    return {
        "confirmed": out.confirmed,
        "missing": out.missing,
        "must_ask": out.must_ask,
        "assumptions": out.assumptions,
        "risks": out.risks,
        "draft_spec": out.draft_spec,
    }
