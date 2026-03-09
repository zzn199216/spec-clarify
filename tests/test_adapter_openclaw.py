"""OpenClaw adapter tests."""

def test_adapter_returns_expected_top_level_fields() -> None:
    """Adapter returns a dict with the expected top-level keys."""
    from adapters.openclaw.adapter import clarify_requirement

    result = clarify_requirement("I want a login page.")

    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "missing" in result
    assert "must_ask" in result
    assert "assumptions" in result
    assert "risks" in result
    assert "draft_spec" in result
