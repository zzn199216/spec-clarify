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
