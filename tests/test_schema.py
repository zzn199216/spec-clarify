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


def test_vague_mentions_not_treated_as_clear() -> None:
    """Vague mentions like 'users can sign up' and 'launch quickly' must NOT cause
    target_users, auth_and_roles, or timeline to be treated as fully clear."""
    from specclarify_core.engine import SlotStatus, _evaluate_slots

    text = "i want a small app where users can sign up, invite friends, and maybe get points later. we should launch something quickly."
    status = _evaluate_slots(text)

    # These must remain partial or missing, not clear
    assert status["target_users"] != SlotStatus.CLEAR
    assert status["auth_and_roles"] != SlotStatus.CLEAR
    assert status["timeline"] != SlotStatus.CLEAR


def test_vague_sample_output_includes_clarifications() -> None:
    """Sample input should produce missing/must_ask for target_users, auth, timeline."""
    from specclarify_core.engine import clarify

    result = clarify(
        "I want a small app where users can sign up, invite friends, and maybe get points later. We should launch something quickly."
    )
    # Should need clarification on these areas
    missing_labels = {m.lower() for m in result.missing}
    assert "target users" in missing_labels or "auth" in " ".join(missing_labels).lower()
    assert len(result.must_ask) <= 3


DEMO_INPUT = (
    "I want a small app where users can sign up, invite friends, and maybe get points later. "
    "We should launch something quickly."
)


def test_golden_sample_demo_input() -> None:
    """Golden sample: demo input produces stable expected structure."""
    from specclarify_core.engine import clarify

    result = clarify(DEMO_INPUT)
    assert "target users" in [m.lower() for m in result.missing]
    assert len(result.must_ask) <= 3
    assert "## MVP" in result.draft_spec


def test_invoice_input_preserves_semantic_anchor() -> None:
    """Invoice-related input should preserve 'invoice' in goal or draft spec."""
    from specclarify_core.engine import clarify

    result = clarify("Build a tool that helps with invoices.")
    combined = (result.confirmed[0] + " " + result.draft_spec).lower()
    assert "invoice" in combined


def test_dashboard_input_produces_domain_specific_question() -> None:
    """Dashboard-related input should produce at least one dashboard/progress-specific question."""
    from specclarify_core.engine import clarify

    result = clarify("We need a dashboard for the team to track progress.")
    must_ask_lower = " ".join(q.lower() for q in result.must_ask)
    assert "dashboard" in must_ask_lower or "progress" in must_ask_lower or "metric" in must_ask_lower


def test_maybe_later_does_not_make_core_features_clear() -> None:
    """Phrases like 'invite friends, and maybe get points later' must NOT cause
    core_features to be treated as fully clear."""
    from specclarify_core.engine import SlotStatus, _evaluate_slots

    status = _evaluate_slots("invite friends, and maybe get points later")
    assert status["core_features"] != SlotStatus.CLEAR
