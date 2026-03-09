# SpecClarify

Turn vague requirements into executable specs.

## Project Status

Deterministic v0.1 prototype. No LLM integration; rule-based clarification only.

## Quick Demo

```bash
# Direct input (JSON)
spec-clarify "I want a small app where users can sign up."

# From examples
spec-clarify --input-file examples/sample_requirement.txt --pretty

# Markdown output
spec-clarify --input-file examples/sample_requirement.txt --format markdown --output result.md
```

## Output Fields

| Field | Description |
|-------|-------------|
| **confirmed** | Items clearly identified from the requirement |
| **missing** | Requirement areas that still block execution |
| **must_ask** | Up to 3 high-priority clarification questions |
| **assumptions** | Explicit default assumptions for execution |
| **risks** | Concise risk statements |
| **draft_spec** | Structured draft spec (Goal, MVP, Users, Open Questions, Assumptions) |

## Usage

```bash
# Direct input (JSON)
spec-clarify "I want a small app where users can sign up."

# Direct input with pretty JSON
spec-clarify --pretty "I want a login page."

# Read from file
spec-clarify --input-file requirements.txt

# Write output to file
spec-clarify "User needs dashboard" --output result.json

# Markdown format
spec-clarify "Build an MVP for feedback" --format markdown

# Full example: file in, markdown out
spec-clarify --input-file req.txt --format markdown --output spec.md
```
