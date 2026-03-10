"""CLI mode tests (rules default, llm/hybrid require provider)."""

import subprocess
from pathlib import Path


def test_cli_rules_mode_default() -> None:
    """Default mode is rules, works without provider."""
    result = subprocess.run(
        ["python", "-m", "specclarify_core.cli", "I want a login page"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    assert result.returncode == 0
    assert "confirmed" in result.stdout
    assert "login" in result.stdout.lower() or "want" in result.stdout.lower()


def test_cli_llm_mode_without_provider_errors() -> None:
    """LLM mode without --provider produces clear error."""
    result = subprocess.run(
        ["python", "-m", "specclarify_core.cli", "--mode", "llm", "I want X"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    assert result.returncode != 0
    assert "provider" in result.stderr.lower()
