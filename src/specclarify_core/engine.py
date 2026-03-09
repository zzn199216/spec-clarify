"""SpecClarify rule-based engine."""

import re

from .schema import SpecClarifyOutput

# Common missing requirement areas for software projects
MISSING_AREAS = [
    ("target users", ["user", "users", "audience", "who will use", "target", "end-user"]),
    ("scope / MVP boundary", ["mvp", "scope", "minimal", "small", "first version", "phase 1", "boundary"]),
    ("authentication / permissions", ["auth", "login", "sign up", "permission", "role", "access"]),
    ("data persistence", ["database", "data", "store", "persist", "save", "storage"]),
    ("admin / operations", ["admin", "operations", "monitoring", "deploy", "maintenance"]),
    ("timeline / deadline", ["deadline", "timeline", "launch", "quickly", "by when", "date"]),
    ("non-functional constraints", ["performance", "security", "scalability", "reliability", "latency"]),
]


def _extract_goal(raw: str) -> str:
    """Extract apparent goal from raw requirement text."""
    text = raw.strip().lower()
    if not text:
        return "User has provided a requirement (details unclear)."

    # Common goal indicators
    if "want" in text or "need" in text or "would like" in text:
        # Take first sentence or clause as goal hint
        match = re.search(r"(?:i\s+)?(?:want|need|would like)\s+([^.?!]+)", text, re.IGNORECASE)
        if match:
            hint = match.group(1).strip()
            return f"User wants: {hint}."

    if "app" in text or "application" in text or "system" in text:
        return "User wants to build a software application."

    return "User has stated a software/project requirement."


def _detect_missing(raw: str) -> list[str]:
    """Identify which common requirement areas are not clearly addressed."""
    text = raw.strip().lower()
    missing: list[str] = []

    for area_name, keywords in MISSING_AREAS:
        if not any(kw in text for kw in keywords):
            missing.append(area_name)

    return missing if missing else ["general scope and constraints"]


def _build_must_ask(missing: list[str], raw: str) -> list[str]:
    """Generate up to 3 high-priority clarification questions."""
    questions: list[str] = []

    priority_map = {
        "target users": "Who are the primary users or target audience?",
        "scope / MVP boundary": "What is the minimum viable scope for the first release?",
        "authentication / permissions": "What authentication and permission model is needed?",
        "data persistence": "What data must be persisted and how?",
        "admin / operations": "Are there admin, monitoring, or operational needs?",
        "timeline / deadline": "What is the target timeline or launch date?",
        "non-functional constraints": "Any performance, security, or scalability requirements?",
        "general scope and constraints": "What are the key scope boundaries and constraints?",
    }

    for area in missing[:3]:
        questions.append(priority_map.get(area, f"What are the requirements for: {area}?"))

    return questions[:3]


def _build_assumptions(raw: str) -> list[str]:
    """Generate 2-4 explicit default assumptions."""
    text = raw.strip().lower()
    assumptions = [
        "Single deployable unit unless distributed architecture is mentioned.",
        "Web or desktop context inferred from 'app' terminology.",
    ]

    if "user" in text or "users" in text:
        assumptions.append("Users are human end-users unless otherwise specified.")
    if "sign up" in text or "invite" in text:
        assumptions.append("User accounts and invitations imply email or similar contact flow.")

    return assumptions[:4]


def _build_risks(raw: str) -> list[str]:
    """Generate 2-4 concise risk statements."""
    text = raw.strip().lower()
    risks = [
        "Scope creep if MVP boundary is not defined.",
        "Integration complexity if auth or external services are assumed but unspecified.",
    ]

    if "quickly" in text or "launch" in text:
        risks.append("Time pressure may conflict with completeness of first release.")
    if "maybe" in text or "later" in text:
        risks.append("Deferred features ('maybe later') can create future rework.")

    return risks[:4]


def _build_draft_spec(
    goal: str,
    missing: list[str],
    must_ask: list[str],
    assumptions: list[str],
) -> str:
    """Build structured draft spec text."""
    lines = [
        "## Goal",
        goal,
        "",
        "## Scope",
        "To be refined. Key gaps: " + "; ".join(missing[:5]) + ".",
        "",
        "## Users",
        "Target users not yet specified.",
        "",
        "## Open Questions",
    ]
    for q in must_ask:
        lines.append(f"- {q}")
    lines.extend(["", "## Assumptions"])
    for a in assumptions:
        lines.append(f"- {a}")
    return "\n".join(lines)


def clarify(raw_requirement: str) -> SpecClarifyOutput:
    """
    Rule-based requirement clarifier for software/project requests.
    Deterministic: same input produces same output.
    """
    raw = raw_requirement or ""
    goal = _extract_goal(raw)
    missing = _detect_missing(raw)
    must_ask = _build_must_ask(missing, raw)
    assumptions = _build_assumptions(raw)
    risks = _build_risks(raw)
    draft_spec = _build_draft_spec(goal, missing, must_ask, assumptions)

    return SpecClarifyOutput(
        confirmed=[goal],
        missing=missing,
        must_ask=must_ask,
        assumptions=assumptions,
        risks=risks,
        draft_spec=draft_spec,
    )
