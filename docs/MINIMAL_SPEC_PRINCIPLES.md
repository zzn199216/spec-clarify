# Minimal Spec Principles

Internal design principles for SpecClarify. Guides implementation to avoid prompt bloat and drift.

## 1. Project Goal

SpecClarify is not trying to make prompts longer or prettier. It aims to **compress vague input into minimal sufficient, executable, and judgeable specification input**. Emphasize information density over more words.

## 2. Core Principles

- **Code over prose**: Prefer deterministic logic, schemas, and structured data over free-form prompt text. Move behavior into code when possible.

- **Schema over explanation**: Use fixed output schemas (e.g. confirmed, missing, must_ask, assumptions, risks, draft_spec) instead of long explanatory paragraphs. Structure enables comparison and evaluation.

- **Anchors over summaries**: Preserve semantic anchors from the raw input (invoice, dashboard, login, etc.) rather than collapsing into generic summaries. Retain what the user actually said.

- **Unresolved over fabricated**: Mark things as missing, partial, or "must ask" instead of inventing details. Do not fabricate requirements that should remain unresolved until clarified.

## 3. System Layering

- **Code layer**: Deterministic rules, slot evaluation, domain heuristics. No LLM. Fast, testable, interpretable.

- **Schema layer**: Fixed output format. Same fields for rules and LLM modes. Enables comparison and downstream consumption.

- **Prompt / LLM layer**: Minimal prompts. Use schema output format. Do not duplicate rules logic in prompt text. Hybrid mode uses rules output as context, not as boilerplate to repeat.

## 4. Design Questions

Before adding or changing behavior, ask:

- Does this increase decision power or only add words?
- Can this be moved into code/schema instead of prompt text?
- Does this preserve semantic anchors?
- Does this fabricate things that should remain unresolved?

## 5. Current Stage Guidance

Current priority:

- Semantic retention (domain nouns, task anchors)
- Better unresolved / explicit / derived separation
- Better domain-specific clarification (invoice, dashboard, invite, etc.)
- Avoiding prompt bloat

## 6. One-Sentence Principle

**SpecClarify aims for minimal sufficient specification, not more prompt text.**
