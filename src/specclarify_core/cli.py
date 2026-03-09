"""SpecClarify CLI entrypoint."""

import argparse
import json

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


def main() -> None:
    parser = argparse.ArgumentParser(description="SpecClarify: turn vague requirements into specs.")
    parser.add_argument("input", nargs="?", default="", help="Raw requirement text")
    args = parser.parse_args()

    result = clarify(args.input)
    print(json.dumps(to_dict(result), indent=2))


if __name__ == "__main__":
    main()
