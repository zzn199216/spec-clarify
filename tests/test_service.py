"""Service layer tests (rules, llm, hybrid with mock provider)."""

from specclarify_core.schema import SpecClarifyOutput


class MockProvider:
    """Mock provider for testing without network calls."""

    def clarify(
        self,
        raw_requirement: str,
        rules_baseline: SpecClarifyOutput | None = None,
    ) -> SpecClarifyOutput:
        return SpecClarifyOutput(
            confirmed=["[mock] confirmed"],
            missing=["[mock] missing"],
            must_ask=["[mock] must_ask"],
            assumptions=["[mock] assumption"],
            risks=["[mock] risk"],
            draft_spec="[mock] draft_spec",
        )


def test_run_clarify_rules_mode() -> None:
    """Rules mode uses deterministic engine, no provider."""
    from specclarify_core.service import run_clarify

    result = run_clarify("I want a login page.", mode="rules")
    assert isinstance(result, SpecClarifyOutput)
    assert "login" in result.confirmed[0].lower() or "want" in result.confirmed[0].lower()
    assert "## Goal" in result.draft_spec


def test_run_clarify_llm_mode_with_mock() -> None:
    """LLM mode uses provider when given."""
    from specclarify_core.service import run_clarify

    result = run_clarify("I want X.", mode="llm", provider=MockProvider())
    assert result.confirmed == ["[mock] confirmed"]
    assert result.draft_spec == "[mock] draft_spec"


def test_run_clarify_hybrid_mode_with_mock() -> None:
    """Hybrid mode runs rules then provider to refine."""
    from specclarify_core.service import run_clarify

    result = run_clarify("I want X.", mode="hybrid", provider=MockProvider())
    # Mock ignores baseline and returns fixed output
    assert result.confirmed == ["[mock] confirmed"]


def test_run_clarify_llm_mode_requires_provider() -> None:
    """LLM mode without provider raises."""
    from specclarify_core.service import run_clarify

    try:
        run_clarify("x", mode="llm", provider=None)
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert "Provider required" in str(e)


def test_run_clarify_hybrid_mode_requires_provider() -> None:
    """Hybrid mode without provider raises."""
    from specclarify_core.service import run_clarify

    try:
        run_clarify("x", mode="hybrid", provider=None)
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert "Provider required" in str(e)
