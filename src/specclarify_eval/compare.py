"""Compare two eval result JSONL files."""

import argparse
import json
import sys


def load_jsonl(path: str) -> list[dict]:
    """Load JSONL file into list of dicts."""
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def index_by_case_id(entries: list[dict]) -> dict[str, dict]:
    """Index entries by case_id."""
    return {e.get("case_id", ""): e for e in entries}


def compare(left_path: str, right_path: str) -> tuple[dict[str, dict], set[str], set[str]]:
    """
    Load and match entries by case_id.
    Returns: (matched_pairs, left_only_ids, right_only_ids)
    """
    left_entries = load_jsonl(left_path)
    right_entries = load_jsonl(right_path)

    left_by_id = index_by_case_id(left_entries)
    right_by_id = index_by_case_id(right_entries)

    left_ids = set(left_by_id)
    right_ids = set(right_by_id)
    common = left_ids & right_ids
    left_only = left_ids - right_ids
    right_only = right_ids - common

    matched = {cid: (left_by_id[cid], right_by_id[cid]) for cid in sorted(common)}
    return matched, left_only, right_only


def build_markdown_report(matched: dict[str, tuple[dict, dict]], left_label: str, right_label: str) -> str:
    """Build markdown comparison report."""
    lines = ["# Eval Comparison Report", "", f"Left: {left_label}", f"Right: {right_label}", ""]

    for case_id, (left, right) in matched.items():
        lines.extend([
            f"## {case_id}",
            "",
            "### Raw Input",
            "```",
            left.get("raw_input", ""),
            "```",
            "",
            f"### Left ({left.get('mode', '?')})",
            "",
            "**Transformed:**",
            "```",
            left.get("transformed_input", ""),
            "```",
            "",
            "**Downstream output:**",
            "```",
            left.get("downstream_output", ""),
            "```",
            "",
            f"### Right ({right.get('mode', '?')})",
            "",
            "**Transformed:**",
            "```",
            right.get("transformed_input", ""),
            "```",
            "",
            "**Downstream output:**",
            "```",
            right.get("downstream_output", ""),
            "```",
            "",
        ])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two eval result JSONL files")
    parser.add_argument("left", help="Left JSONL path (e.g. baseline)")
    parser.add_argument("right", help="Right JSONL path (e.g. rules)")
    parser.add_argument("--output", "-o", help="Write markdown report to file")
    args = parser.parse_args()

    matched, left_only, right_only = compare(args.left, args.right)

    # Terminal summary
    left_label = args.left
    right_label = args.right
    print(f"Matched cases: {len(matched)}")
    if left_only:
        print(f"Only in left: {sorted(left_only)}")
    if right_only:
        print(f"Only in right: {sorted(right_only)}")

    if not matched:
        print("No matched cases to report.")
        sys.exit(1)

    report = build_markdown_report(matched, left_label, right_label)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print()
        print(report)


if __name__ == "__main__":
    main()
