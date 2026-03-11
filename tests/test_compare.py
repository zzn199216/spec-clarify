"""Compare module tests."""

import tempfile
from pathlib import Path


def _write_jsonl(path: str, entries: list[dict]) -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def test_match_by_case_id() -> None:
    """Entries are matched by case_id."""
    from specclarify_eval.compare import compare, load_jsonl

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        _write_jsonl(f.name, [
            {"case_id": "c1", "mode": "baseline", "raw_input": "a", "transformed_input": "a", "downstream_output": "x"},
            {"case_id": "c2", "mode": "baseline", "raw_input": "b", "transformed_input": "b", "downstream_output": "y"},
        ])
        left_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        _write_jsonl(f.name, [
            {"case_id": "c1", "mode": "rules", "raw_input": "a", "transformed_input": "a'", "downstream_output": "x'"},
            {"case_id": "c2", "mode": "rules", "raw_input": "b", "transformed_input": "b'", "downstream_output": "y'"},
        ])
        right_path = f.name

    try:
        matched, left_only, right_only = compare(left_path, right_path)
        assert len(matched) == 2
        assert "c1" in matched and "c2" in matched
        assert matched["c1"][0]["downstream_output"] == "x"
        assert matched["c1"][1]["downstream_output"] == "x'"
        assert left_only == set()
        assert right_only == set()
    finally:
        Path(left_path).unlink(missing_ok=True)
        Path(right_path).unlink(missing_ok=True)


def test_markdown_report_generated() -> None:
    """Report contains case id, modes, transformed, downstream."""
    from specclarify_eval.compare import build_markdown_report, compare

    left = {"case_id": "c1", "mode": "baseline", "raw_input": "raw", "transformed_input": "t1", "downstream_output": "d1"}
    right = {"case_id": "c1", "mode": "rules", "raw_input": "raw", "transformed_input": "t2", "downstream_output": "d2"}
    matched = {"c1": (left, right)}

    report = build_markdown_report(matched, "left.jsonl", "right.jsonl")
    assert "## c1" in report
    assert "raw" in report
    assert "baseline" in report
    assert "rules" in report
    assert "t1" in report
    assert "t2" in report
    assert "d1" in report
    assert "d2" in report


def test_missing_case_ids_handled_gracefully() -> None:
    """Cases only in one file are reported, not crashed."""
    from specclarify_eval.compare import compare

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        _write_jsonl(f.name, [
            {"case_id": "c1", "mode": "a", "raw_input": "x", "transformed_input": "x", "downstream_output": ""},
            {"case_id": "c2", "mode": "a", "raw_input": "y", "transformed_input": "y", "downstream_output": ""},
        ])
        left_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        _write_jsonl(f.name, [
            {"case_id": "c1", "mode": "b", "raw_input": "x", "transformed_input": "x'", "downstream_output": ""},
            {"case_id": "c3", "mode": "b", "raw_input": "z", "transformed_input": "z'", "downstream_output": ""},
        ])
        right_path = f.name

    try:
        matched, left_only, right_only = compare(left_path, right_path)
        assert len(matched) == 1
        assert "c1" in matched
        assert left_only == {"c2"}
        assert right_only == {"c3"}
    finally:
        Path(left_path).unlink(missing_ok=True)
        Path(right_path).unlink(missing_ok=True)
