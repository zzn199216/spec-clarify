"""SpecClarify rule-based engine with slot-based requirement model."""

import re
from enum import Enum
from typing import NamedTuple

from .schema import SpecClarifyOutput


class SlotStatus(Enum):
    """Status of a requirement slot."""

    CLEAR = "clear"
    PARTIAL = "partial"
    MISSING = "missing"


class RequirementSlot(NamedTuple):
    """A requirement slot with display name and question for clarification."""

    key: str
    label: str
    question: str


# Fixed slots for software/project clarification, in priority order for must_ask
SLOTS: list[RequirementSlot] = [
    RequirementSlot("goal", "goal", "What is the primary goal?"),
    RequirementSlot("target_users", "target users", "Who are the primary users or target audience?"),
    RequirementSlot("core_features", "core features", "What are the core features for the first version?"),
    RequirementSlot("scope_boundary", "scope / MVP boundary", "What is the minimum viable scope for the first release?"),
    RequirementSlot("auth_and_roles", "auth and roles", "What authentication and permission model is needed?"),
    RequirementSlot("data_persistence", "data persistence", "What data must be persisted and how?"),
    RequirementSlot("admin_ops", "admin / operations", "Are there admin, monitoring, or operational needs?"),
    RequirementSlot(
        "non_functional_constraints",
        "non-functional constraints",
        "Any performance, security, or scalability requirements?",
    ),
    RequirementSlot("timeline", "timeline", "What is the target timeline or launch date?"),
]


def _normalize(raw: str) -> str:
    """Return lowercase normalized text for analysis."""
    return (raw or "").strip().lower()


def _evaluate_slots(text: str) -> dict[str, SlotStatus]:
    """
    Evaluate each slot with realistic heuristics:
    - Explicit concrete details -> clear
    - Vague mentions (e.g. users, sign up, launch quickly) -> partial
    - No evidence -> missing
    """
    status: dict[str, SlotStatus] = {}

    # goal: clear if we extract a substantive goal; partial if vague
    goal_match = re.search(r"(?:i\s+)?(?:want|need|would like)\s+([^.?!]+)", text, re.IGNORECASE)
    if goal_match and len(goal_match.group(1).strip()) > 10:
        status["goal"] = SlotStatus.CLEAR
    elif "app" in text or "system" in text or "want" in text or "need" in text:
        status["goal"] = SlotStatus.PARTIAL
    else:
        status["goal"] = SlotStatus.MISSING

    # target_users: "users" / "user" / "friends" = partial (vague); specific roles = clear
    if any(x in text for x in ["b2b", "b2c", "developers", "admins", "providers", "enterprise", "consumer"]):
        status["target_users"] = SlotStatus.CLEAR
    elif any(x in text for x in ["user", "users", "friends", "people", "audience"]):
        status["target_users"] = SlotStatus.PARTIAL
    else:
        status["target_users"] = SlotStatus.MISSING

    # core_features: never clear if uncertainty markers; prefer partial when vague
    # Uncertainty: maybe, later, eventually, optional, could
    uncertainty_markers = ["maybe", "later", "eventually", "optional", "could"]
    has_uncertainty = any(m in text for m in uncertainty_markers)

    feature_mentions = sum(1 for x in ["sign up", "invite", "login", "points", "dashboard", "report"] if x in text)
    # Clear only when: multiple features, explicit scope, and NO uncertainty
    if has_uncertainty:
        status["core_features"] = SlotStatus.PARTIAL
    elif feature_mentions >= 2 and any(x in text for x in ["and", "plus", ",", "also"]):
        status["core_features"] = SlotStatus.PARTIAL  # Named features but behavior/priority vague -> partial
    elif feature_mentions >= 1:
        status["core_features"] = SlotStatus.PARTIAL
    else:
        status["core_features"] = SlotStatus.MISSING

    # scope_boundary: explicit mvp/phase = clear; "small"/"quickly" = partial
    if any(x in text for x in ["mvp", "phase 1", "first version:", "first release", "scope:"]):
        status["scope_boundary"] = SlotStatus.CLEAR
    elif any(x in text for x in ["small", "minimal", "quickly", "something quickly"]):
        status["scope_boundary"] = SlotStatus.PARTIAL
    else:
        status["scope_boundary"] = SlotStatus.MISSING

    # auth_and_roles: "sign up"/"login" = partial (vague); explicit model = clear
    if any(x in text for x in ["oauth", "saml", "jwt", "role-based", "rbac", "admin role", "permission"]):
        status["auth_and_roles"] = SlotStatus.CLEAR
    elif any(x in text for x in ["sign up", "login", "auth", "invite"]):
        status["auth_and_roles"] = SlotStatus.PARTIAL
    else:
        status["auth_and_roles"] = SlotStatus.MISSING

    # data_persistence: explicit = clear; vague "data"/"store" = partial
    if any(x in text for x in ["database", "postgres", "sql", "persist", "storage", "save to"]):
        status["data_persistence"] = SlotStatus.CLEAR
    elif any(x in text for x in ["data", "store", "save"]):
        status["data_persistence"] = SlotStatus.PARTIAL
    else:
        status["data_persistence"] = SlotStatus.MISSING

    # admin_ops: vague mentions = partial
    if any(x in text for x in ["admin dashboard", "ci/cd", "deployment pipeline"]):
        status["admin_ops"] = SlotStatus.CLEAR
    elif any(x in text for x in ["admin", "monitoring", "deploy", "operations"]):
        status["admin_ops"] = SlotStatus.PARTIAL
    else:
        status["admin_ops"] = SlotStatus.MISSING

    # non_functional_constraints: explicit = clear
    if any(x in text for x in ["10k", "latency", "uptime", "encryption", "gdpr", "performance", "security"]):
        status["non_functional_constraints"] = SlotStatus.CLEAR
    elif any(x in text for x in ["scale", "reliable", "fast"]):
        status["non_functional_constraints"] = SlotStatus.PARTIAL
    else:
        status["non_functional_constraints"] = SlotStatus.MISSING

    # timeline: "launch quickly" / "soon" = partial; specific date = clear
    if re.search(r"\b(q[1-4]\s*20\d{2}|20\d{2}|march|april|\d+\s*months?|by\s+\w+)\b", text):
        status["timeline"] = SlotStatus.CLEAR
    elif any(x in text for x in ["launch", "quickly", "soon", "deadline"]):
        status["timeline"] = SlotStatus.PARTIAL
    else:
        status["timeline"] = SlotStatus.MISSING

    return status


def _extract_goal(raw: str) -> str:
    """Extract apparent goal from raw requirement text."""
    text = _normalize(raw)
    if not text:
        return "User has provided a requirement (details unclear)."
    match = re.search(r"(?:i\s+)?(?:want|need|would like)\s+([^.?!]+)", text, re.IGNORECASE)
    if match:
        return f"User wants: {match.group(1).strip()}."
    if "app" in text or "application" in text or "system" in text:
        return "User wants to build a software application."
    return "User has stated a software/project requirement."


def _build_output_from_slots(
    raw: str,
    slot_status: dict[str, SlotStatus],
    goal_text: str,
) -> SpecClarifyOutput:
    """Generate SpecClarifyOutput from slot states."""
    # confirmed: only CLEAR slots (goal always included if we extracted it)
    confirmed = [goal_text]
    for slot in SLOTS:
        if slot.key == "goal":
            continue
        if slot_status.get(slot.key) == SlotStatus.CLEAR:
            confirmed.append(f"Requirement area '{slot.label}' appears sufficiently specified.")

    # missing: PARTIAL or MISSING slots (blockers)
    missing = [
        slot.label
        for slot in SLOTS
        if slot.key != "goal" and slot_status.get(slot.key) in (SlotStatus.PARTIAL, SlotStatus.MISSING)
    ]
    if not missing:
        missing = ["general scope and constraints"]

    # must_ask: up to 3 from highest-priority partial/missing
    must_ask = []
    for slot in SLOTS:
        if len(must_ask) >= 3:
            break
        if slot.key == "goal":
            continue
        if slot_status.get(slot.key) in (SlotStatus.PARTIAL, SlotStatus.MISSING):
            must_ask.append(slot.question)
    must_ask = must_ask[:3]

    # assumptions: execution-oriented, derived from slot states where possible
    text = _normalize(raw)
    assumptions = ["Assume a web-based MVP unless otherwise specified."]

    if slot_status.get("auth_and_roles") in (SlotStatus.PARTIAL, SlotStatus.MISSING):
        assumptions.append("Assume a single end-user role unless multiple roles are explicitly mentioned.")
    if "maybe" in text or "later" in text or "eventually" in text:
        assumptions.append("Assume deferred features are out of MVP scope unless explicitly prioritized.")
    if slot_status.get("data_persistence") in (SlotStatus.PARTIAL, SlotStatus.MISSING):
        assumptions.append("Assume minimal persistence (e.g. user profiles) until data model is specified.")

    assumptions = assumptions[:4]

    # risks: tied to slot gaps
    risks = []
    if SlotStatus.PARTIAL in slot_status.values() or SlotStatus.MISSING in slot_status.values():
        risks.append("Scope creep if MVP boundary is not defined.")
        risks.append("Integration complexity if auth or external services are assumed but unspecified.")
    if slot_status.get("timeline") == SlotStatus.PARTIAL and ("quickly" in text or "launch" in text):
        risks.append("Time pressure may conflict with completeness of first release.")
    if "maybe" in text or "later" in text:
        risks.append("Deferred features ('maybe later') can create future rework.")
    if len(risks) < 2:
        risks.extend(["Key requirement areas need clarification.", "Assumptions may not match stakeholder intent."])
    risks = risks[:4]

    # draft_spec: actionable, with MVP and optional out-of-scope section
    has_deferred = any(x in text for x in ["maybe", "later", "eventually", "optional"])

    lines = [
        "## Goal",
        goal_text,
        "",
        "## MVP",
        "To be defined after clarifying: " + "; ".join(missing[:5]) + ".",
        "",
        "## Users",
        "Target users need clarification." if slot_status.get("target_users") != SlotStatus.CLEAR else "See confirmed.",
        "",
        "## Open Questions",
    ]
    for q in must_ask:
        lines.append(f"- {q}")
    if has_deferred:
        lines.extend(["", "## Out of Scope (tentative)", "Features marked 'maybe/later/eventually' until prioritized."])
    lines.extend(["", "## Assumptions"])
    for a in assumptions:
        lines.append(f"- {a}")
    draft_spec = "\n".join(lines)

    return SpecClarifyOutput(
        confirmed=confirmed,
        missing=missing,
        must_ask=must_ask,
        assumptions=assumptions,
        risks=risks,
        draft_spec=draft_spec,
    )


def clarify(raw_requirement: str) -> SpecClarifyOutput:
    """
    Rule-based requirement clarifier using a slot-based model.
    Deterministic: same input produces same output.
    """
    raw = raw_requirement or ""
    text = _normalize(raw)
    goal_text = _extract_goal(raw)
    slot_status = _evaluate_slots(text)
    return _build_output_from_slots(raw, slot_status, goal_text)
