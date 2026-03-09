"""CLI tests."""

import tempfile
from pathlib import Path

# Use subprocess for real CLI invocation
# Simpler: call the CLI module and capture. Use subprocess for real CLI invocation.


def test_markdown_format_renders_all_sections() -> None:
    """Markdown output includes Confirmed, Missing, Must Ask, Assumptions, Risks, Draft Spec."""
    from specclarify_core.cli import to_markdown
    from specclarify_core.schema import SpecClarifyOutput

    out = SpecClarifyOutput(
        confirmed=["Goal: login"],
        missing=["scope"],
        must_ask=["Who are users?"],
        assumptions=["Web MVP"],
        risks=["Scope creep"],
        draft_spec="## Goal\nLogin page.",
    )
    md = to_markdown(out)
    assert "## Confirmed" in md
    assert "## Missing" in md
    assert "## Must Ask" in md
    assert "## Assumptions" in md
    assert "## Risks" in md
    assert "## Draft Spec" in md
    assert "Goal: login" in md
    assert "## Goal" in md and "Login page." in md


def test_input_file_reads_content() -> None:
    """--input-file reads requirement text from file."""
    import subprocess

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("I need a dashboard for admins.")
        path = f.name

    try:
        result = subprocess.run(
            ["python", "-m", "specclarify_core.cli", "--input-file", path],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={**__import__("os").environ, "PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        assert "dashboard" in result.stdout or "admin" in result.stdout.lower()
    finally:
        Path(path).unlink(missing_ok=True)


def test_no_input_returns_error() -> None:
    """CLI exits with error when no input is provided."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "specclarify_core.cli"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    assert result.returncode != 0
    assert "No input" in result.stderr or "input" in result.stderr.lower()
