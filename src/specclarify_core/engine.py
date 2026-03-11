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

    # target_users: explicit actors (team, customers, authors/readers) = partial; vague = partial; none = missing
    if any(x in text for x in ["b2b", "b2c", "developers", "admins", "providers", "enterprise", "consumer"]):
        status["target_users"] = SlotStatus.CLEAR
    elif any(x in text for x in ["team", "customers", "authors", "readers", "company", "small teams"]):
        status["target_users"] = SlotStatus.PARTIAL  # Explicit but roles need refinement
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


def _get_domain_specific_questions(text: str) -> list[str]:
    """Return domain-specific clarification questions when anchors are present."""
    questions = []
    if "invoice" in text or "invoic" in text:
        questions.append("What invoice lifecycle is needed (create, send, track, payment, reporting)?")
    if "dashboard" in text or "track progress" in text or "progress" in text:
        questions.append("What progress metrics or data sources should the dashboard show?")
    if "invite" in text or "points" in text or "referral" in text:
        questions.append("What invitation flow and reward scope apply for MVP?")
    if "appointment" in text or "booking" in text:
        questions.append("What booking workflow and availability model are needed?")
    if "wiki" in text or "blog" in text:
        questions.append("What editor/viewer roles and content model are needed?")
    if "feedback" in text:
        questions.append("What feedback mechanism and collection triggers are needed?")
    if "mobile" in text and ("food" in text or "order" in text):
        questions.append("What food ordering flow and restaurant/venue side are needed?")
    if "trello" in text or "like trello" in text:
        questions.append("Which Trello features to include vs simplify for small teams?")
    if "authors" in text and "readers" in text:
        questions.append("What can authors vs readers do (post, comment, moderate)?")
    return questions[:2]


def _extract_domain_anchor(text: str) -> str | None:
    """Extract a key domain/task noun from the text when present."""
    # Order matters: more specific first
    anchors = [
        ("invoice", "invoice"),
        ("invoic", "invoicing"),
        ("dashboard", "dashboard"),
        ("login", "login"),
        ("sign up", "sign-up"),
        ("invite", "invitation"),
        ("points", "points / rewards"),
        ("appointment", "appointment"),
        ("booking", "booking"),
        ("wiki", "wiki"),
        ("blog", "blog"),
        ("progress", "progress tracking"),
        ("track progress", "progress tracking"),
        ("feedback", "feedback"),
        ("project", "project management"),
        ("task", "task management"),
        ("analytics", "analytics"),
        ("report", "reporting"),
    ]
    for keyword, anchor in anchors:
        if keyword in text:
            return anchor
    return None


def _slot_question_for_context(slot: RequirementSlot, text: str, existing_questions: list[str]) -> str:
    """Return slot question, or a more targeted one when explicit signals exist. Skip if covered."""
    if slot.key == "target_users":
        if "authors" in text and "readers" in text:
            if any("author" in q.lower() and "reader" in q.lower() for q in existing_questions):
                return ""  # Domain question already covers this
            return "What can authors vs readers do?"
        if "team" in text:
            return "What defines the team and their access levels?"
        if "customers" in text:
            return "What customer segments or personas apply?"
    if slot.key == "scope_boundary" and "trello" in text:
        return "Which core features to include in the simplified version?"
    return slot.question


def _extract_phrase_anchors(text: str) -> list[str]:
    """Extract phrase-level semantic anchors from the text (preserve, do not collapse)."""
    anchors = []
    # Mobile app for X
    m = re.search(r"mobile\s+app\s+for\s+([^.?!,]+)", text, re.IGNORECASE)
    if m:
        anchors.append(f"mobile app for {m.group(1).strip()}")
    # Dashboard for X
    m = re.search(r"dashboard\s+for\s+(?:the\s+)?([^.?!,]+?)(?:\.|to\s|$)", text, re.IGNORECASE)
    if m:
        anchors.append(f"dashboard for {m.group(1).strip()}")
    # Tool that helps with X
    m = re.search(r"tool\s+that\s+helps\s+with\s+(\w+)", text, re.IGNORECASE)
    if m:
        anchors.append(f"tool that helps with {m.group(1)}")
    # Internal wiki for X
    m = re.search(r"internal\s+wiki\s+for\s+([^.?!,]+)", text, re.IGNORECASE)
    if m:
        anchors.append(f"internal wiki for {m.group(1).strip()}")
    # Like X but simpler
    m = re.search(r"like\s+(\w+)\s+but\s+(\w+)", text, re.IGNORECASE)
    if m:
        anchors.append(f"like {m.group(1)} but {m.group(2)}")
    # X where authors/readers ...
    m = re.search(r"(?:blog|wiki|app)\s+where\s+([^.?!]+)", text, re.IGNORECASE)
    if m:
        anchors.append(m.group(1).strip())
    return anchors


def _extract_explicitly_stated(text: str) -> list[str]:
    """Extract information that is explicitly stated (actors, platform, permissions, scope hints)."""
    stated = []
    if any(x in text for x in ["customers", "customer"]):
        stated.append("Actors: customers")
    if any(x in text for x in ["authors", "readers"]):
        if "authors" in text and "readers" in text:
            stated.append("Actors: authors and readers")
        elif "authors" in text:
            stated.append("Actors: authors")
        elif "readers" in text:
            stated.append("Actors: readers")
    if any(x in text for x in ["team", "teams"]):
        stated.append("Actors: team")
    if "company" in text or "our company" in text:
        stated.append("Context: company / internal")
    if "small teams" in text:
        stated.append("Context: small teams")
    if "mobile" in text or "mobile app" in text:
        stated.append("Platform: mobile")
    if "online" in text:
        stated.append("Channel: online")
    if "internal" in text:
        stated.append("Scope: internal")
    if "everyone can edit" in text or "everyone can" in text:
        stated.append("Permission hint: everyone can edit")
    if "like trello" in text or "like trello but" in text:
        stated.append("Reference: Trello-like")
    if "quickly" in text or "launch" in text:
        stated.append("Timing hint: quick launch")
    if "maybe" in text or "later" in text:
        stated.append("Deferred: features marked maybe/later")
    return stated


def _extract_goal(raw: str) -> str:
    """Extract apparent goal from raw requirement text, preserving phrase-level anchors."""
    text = _normalize(raw)
    if not text:
        return "User has provided a requirement (details unclear)."

    # Prefer phrase anchors over single-noun collapse
    phrase_anchors = _extract_phrase_anchors(text)
    if phrase_anchors:
        return f"User wants: {phrase_anchors[0]}."

    # Pattern: want/need/would like + phrase
    match = re.search(r"(?:i\s+)?(?:want|need|would like)\s+([^.?!]+)", text, re.IGNORECASE)
    if match:
        phrase = match.group(1).strip()
        if len(phrase) > 8:
            return f"User wants: {phrase}."

    # Pattern: we need + phrase
    match = re.search(r"we\s+need\s+([^.?!]+)", text, re.IGNORECASE)
    if match:
        phrase = match.group(1).strip()
        if len(phrase) > 5:
            return f"User needs: {phrase}."

    # Pattern: X for Y (e.g. "Mobile app for ordering food")
    match = re.search(r"(?:mobile\s+)?app\s+for\s+([^.?!,]+)", text, re.IGNORECASE)
    if match:
        return f"User wants: app for {match.group(1).strip()}."

    # Pattern: tool/app that helps with X
    match = re.search(
        r"(?:tool|app|feature|system)\s+(?:that\s+)?(?:helps?\s+with|for)\s+(\w+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return f"User wants a tool/app for: {match.group(1)}."

    # Pattern: build/create + phrase
    match = re.search(
        r"(?:build|create|make|develop)\s+(?:a\s+)?([^.!?]+?)(?:\.|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        phrase = match.group(1).strip()
        if len(phrase) > 4:
            return f"User wants to build: {phrase}."

    # An internal wiki for our company
    match = re.search(r"(?:an?\s+)?internal\s+wiki\s+for\s+([^.?!]+)", text, re.IGNORECASE)
    if match:
        return f"User wants: internal wiki for {match.group(1).strip()}."

    # Something like X but Y
    match = re.search(r"something\s+like\s+([^.?!]+)", text, re.IGNORECASE)
    if match:
        return f"User wants: {match.group(1).strip()}."

    anchor = _extract_domain_anchor(text)
    if anchor:
        return f"User wants a solution for: {anchor}."

    if "app" in text or "application" in text:
        return "User wants to build a software application."
    return "User has stated a software/project requirement."


def _build_output_from_slots(
    raw: str,
    slot_status: dict[str, SlotStatus],
    goal_text: str,
) -> SpecClarifyOutput:
    """Generate SpecClarifyOutput from slot states."""
    text = _normalize(raw)
    stated = _extract_explicitly_stated(text)

    # confirmed: include goal and any explicit statements
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

    # must_ask: domain-specific first, then targeted slot questions (avoid generic when explicit)
    must_ask = []
    domain_questions = _get_domain_specific_questions(text)
    for q in domain_questions[:2]:
        must_ask.append(q)
    for slot in SLOTS:
        if len(must_ask) >= 3:
            break
        if slot.key == "goal":
            continue
        if slot_status.get(slot.key) in (SlotStatus.PARTIAL, SlotStatus.MISSING):
            q = _slot_question_for_context(slot, text, must_ask)
            if q and q not in must_ask:
                must_ask.append(q)
    must_ask = must_ask[:3]

    # assumptions: execution-oriented; do not assume web when mobile is explicit
    if "mobile" in text:
        assumptions = ["Assume mobile-first unless web is explicitly preferred."]
    else:
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

    # draft_spec: explicitly stated vs unresolved, concise
    has_deferred = any(x in text for x in ["maybe", "later", "eventually", "optional"])

    lines = [
        "## Goal",
        goal_text,
        "",
    ]
    if stated:
        lines.extend(["## Explicitly Stated", ""])
        for s in stated[:6]:
            lines.append(f"- {s}")
        lines.append("")
    lines.extend([
        "## Unresolved / Needs Clarification",
        "; ".join(missing[:5]) + ".",
        "",
        "## Open Questions",
    ])
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
