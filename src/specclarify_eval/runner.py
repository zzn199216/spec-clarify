"""Minimal evaluation runner for SpecClarify."""

import argparse
import json
import os
from pathlib import Path


def load_cases(path: str) -> list[dict]:
    """Load benchmark cases from JSONL."""
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def get_transformed_input(
    raw_input: str,
    mode: str,
    clarify_provider=None,
) -> str:
    """Get input to send to downstream model."""
    if mode == "baseline":
        return raw_input

    from specclarify_core.service import run_clarify

    out = run_clarify(raw_input, mode=mode, provider=clarify_provider)
    # Use draft_spec as the primary transformed input for downstream
    return out.draft_spec


def call_downstream(
    transformed_input: str,
    task: str,
    model: str,
    base_url: str | None,
    api_key_env: str,
    timeout: float,
) -> str:
    """Call downstream model with the (possibly clarified) input."""
    from openai import OpenAI

    api_key = os.environ.get(api_key_env)
    if not api_key and not base_url:
        raise ValueError(
            f"API key not found. Set {api_key_env} or use a local endpoint with --base-url."
        )
    # Ollama / local endpoints often work without a real key
    api_key = api_key or "not-needed"

    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt = f"Given the following requirement or spec, {task}\n\nInput:\n{transformed_input}"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )
    content = response.choices[0].message.content if response.choices else ""
    return content or ""


def build_clarify_provider(model: str, base_url: str | None, api_key_env: str, timeout: float):
    """Build clarify provider for llm/hybrid modes."""
    from specclarify_providers.config import ProviderConfig
    from specclarify_providers.openai_compatible import OpenAICompatibleProvider

    config = ProviderConfig(
        provider_name="openai-compatible",
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        timeout=timeout,
    )
    return OpenAICompatibleProvider(config)


def run_eval(
    cases_path: str,
    output_dir: str,
    mode: str,
    model: str,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    timeout: float = 60.0,
    skip_downstream: bool = False,
) -> list[dict]:
    """Run evaluation and save results."""
    cases = load_cases(cases_path)
    clarify_provider = None
    if mode in ("llm", "hybrid"):
        clarify_provider = build_clarify_provider(model, base_url, api_key_env, timeout)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results = []
    for case in cases:
        case_id = case.get("id", "unknown")
        raw_input = case.get("raw_input", "")
        task = case.get("task", "Produce a brief implementation plan.")

        try:
            transformed = get_transformed_input(raw_input, mode, clarify_provider)
        except Exception as e:
            transformed = f"[clarify error: {e}]"
            downstream_output = ""
        else:
            if skip_downstream:
                downstream_output = ""
            else:
                try:
                    downstream_output = call_downstream(
                        transformed, task, model, base_url, api_key_env, timeout
                    )
                except Exception as e:
                    downstream_output = f"[downstream error: {e}]"

        entry = {
            "case_id": case_id,
            "mode": mode,
            "raw_input": raw_input,
            "transformed_input": transformed,
            "downstream_output": downstream_output,
        }
        results.append(entry)

    # Save all results to one file per run
    run_file = out_path / f"run_{mode}.jsonl"
    with open(run_file, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="SpecClarify evaluation runner")
    parser.add_argument("cases", help="Path to benchmark_cases.jsonl")
    parser.add_argument("--output-dir", "-o", default="evals/results", help="Output directory")
    parser.add_argument(
        "--mode",
        choices=["baseline", "rules", "llm", "hybrid"],
        default="rules",
        help="Evaluation mode",
    )
    parser.add_argument("--model", default="gpt-4o-mini", help="Model for downstream (and llm/hybrid clarify)")
    parser.add_argument("--base-url", help="API base URL (e.g. http://localhost:11434/v1 for Ollama)")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Env var for API key")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds")
    parser.add_argument(
        "--skip-downstream",
        action="store_true",
        help="Skip downstream model call (smoke test)",
    )
    args = parser.parse_args()

    run_eval(
        cases_path=args.cases,
        output_dir=args.output_dir,
        mode=args.mode,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        timeout=args.timeout,
        skip_downstream=args.skip_downstream,
    )
    print(f"Saved results to {args.output_dir}/run_{args.mode}.jsonl")


if __name__ == "__main__":
    main()
