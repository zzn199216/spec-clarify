# SpecClarify Evaluation Harness

Minimal harness to test whether SpecClarify improves downstream LLM performance on vague requirements.

## Benchmark Cases

- `benchmark_cases.jsonl`: 10 vague software/product requirement cases
- Each case: `id`, `raw_input`, `task`, `notes`

## Rubric

- `rubric.md`: 5 manual evaluation criteria (1–5 scale)
- Used for human scoring; no auto-scoring in this version

## Running Evals

```bash
# Smoke test: rules mode, skip downstream (no API key)
python -m specclarify_eval.runner evals/benchmark_cases.jsonl --mode rules --skip-downstream --output-dir evals/results

# Full runs (need API key or --base-url for Ollama)
python -m specclarify_eval.runner evals/benchmark_cases.jsonl --mode rules --output-dir evals/results --model gpt-4o-mini
python -m specclarify_eval.runner evals/benchmark_cases.jsonl --mode baseline --output-dir evals/results --model gpt-4o-mini
python -m specclarify_eval.runner evals/benchmark_cases.jsonl --mode llm --output-dir evals/results --model gpt-4o-mini
python -m specclarify_eval.runner evals/benchmark_cases.jsonl --mode hybrid --output-dir evals/results --model gpt-4o-mini
```

## Results

- Saved under `evals/results/`
- One JSON file per run (or per case depending on design)
- Each entry: `case_id`, `mode`, `raw_input`, `transformed_input`, `downstream_output`
