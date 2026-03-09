"""SpecClarify CLI entrypoint."""

import argparse
import json
import sys

from .engine import clarify
from .schema import SpecClarifyOutput


def to_dict(out: SpecClarifyOutput) -> dict:
    """Convert SpecClarifyOutput to JSON-serializable dict."""
    return {
        "confirmed": out.confirmed,
        "missing": out.missing,
        "must_ask": out.must_ask,
        "assumptions": out.assumptions,
        "risks": out.risks,
        "draft_spec": out.draft_spec,
    }


def to_markdown(out: SpecClarifyOutput) -> str:
    """Convert SpecClarifyOutput to a readable markdown document."""
    lines = ["# SpecClarify Result", ""]

    lines.extend(["## Confirmed", ""])
    for item in out.confirmed:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## Missing", ""])
    for item in out.missing:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## Must Ask", ""])
    for item in out.must_ask:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## Assumptions", ""])
    for item in out.assumptions:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## Risks", ""])
    for item in out.risks:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## Draft Spec", "", out.draft_spec])
    return "\n".join(lines)


def get_input_text(args: argparse.Namespace) -> str:
    """
    Resolve input text from args.
    When both direct input and --input-file are provided, prefer direct input.
    """
    if args.input and args.input.strip():
        return args.input.strip()
    if args.input_file:
        with open(args.input_file, encoding="utf-8") as f:
            return f.read()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SpecClarify: turn vague requirements into specs.",
        epilog="When both direct input and --input-file are provided, direct input is used.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="",
        help="Raw requirement text (overrides --input-file when both given)",
    )
    parser.add_argument("--input-file", "-i", help="Read requirement text from file")
    parser.add_argument("--output", "-o", help="Write result to file instead of stdout")
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indentation")
    args = parser.parse_args()

    text = get_input_text(args)
    if not text:
        parser.error("No input provided. Give requirement text as argument or use --input-file.")

    result = clarify(text)

    if args.format == "markdown":
        output = to_markdown(result)
    else:
        kwargs = {"indent": 2} if args.pretty else {}
        output = json.dumps(to_dict(result), **kwargs)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
