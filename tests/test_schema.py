"""Schema tests."""

from specclarify_core.schema import SpecClarifyOutput


def test_schema_object_can_be_created() -> None:
    """Verify the schema object can be instantiated."""
    out = SpecClarifyOutput(
        confirmed=["a"],
        missing=["b"],
        must_ask=["c"],
        assumptions=["d"],
        risks=["e"],
        draft_spec="f",
    )
    assert out.confirmed == ["a"]
    assert out.draft_spec == "f"


def test_clarify_returns_valid_specclarify_output() -> None:
    """Verify clarify() returns a valid SpecClarifyOutput with all required fields."""
    from specclarify_core.engine import clarify

    result = clarify("I want a login page.")
    assert isinstance(result, SpecClarifyOutput)
    assert isinstance(result.confirmed, list)
    assert len(result.confirmed) >= 1
    assert isinstance(result.missing, list)
    assert isinstance(result.must_ask, list)
    assert isinstance(result.assumptions, list)
    assert len(result.assumptions) >= 2
    assert isinstance(result.risks, list)
    assert len(result.risks) >= 2
    assert isinstance(result.draft_spec, str)
    assert "## Goal" in result.draft_spec


def test_must_ask_contains_at_most_three_items() -> None:
    """Verify must_ask never exceeds 3 items."""
    from specclarify_core.engine import clarify

    result = clarify("vague request with no details")
    assert len(result.must_ask) <= 3
