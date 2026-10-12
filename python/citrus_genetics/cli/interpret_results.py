"""Generate opinionated result interpretations using Claude CLI.

Reads analysis result JSONs from web/public/data/, constructs a structured
prompt, and calls `claude -p` to generate rich, opinionated interpretations.
Falls back to the deterministic interpret.py if Claude CLI is unavailable.

Requires:
    - `claude` CLI in PATH (Claude Code CLI)
    - ANTHROPIC_API_KEY in environment or .env file

Usage:
    uv run python -m citrus_genetics.cli.interpret_results
    make interpret
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
OUTPUT_PATH = DATA_DIR / "interpretations.json"

# Analysis keys and their source JSON files
ANALYSIS_SOURCES = {
    "models": "model_comparison.json",
    "anomalies": "anomaly_scores.json",
    "mi_matrix": "mi_matrix.json",
    "residuals": "residuals.json",
    "r_sweep": "r_sweep.json",
    "distribution_tests": "distribution_tests.json",
    "mixture": "mixture_weights.json",
}

# Supplementary data files
SUPPLEMENTARY = {
    "sibling_correlations": "sibling_correlations.json",
    "trait_cooccurrence": "trait_cooccurrence.json",
    "run_meta": "run_meta.json",
}

SYSTEM_PROMPT = """\
You are a research statistician analyzing results from a citrus tree breeding \
genetics study in A Tale in the Desert (ATITD). The study reverse-engineers \
hidden inheritance mechanics using maximum likelihood estimation across 30 \
competing models, with 692 observed offspring across 14 litters.

The CLAIM model posits: each child inherits one of two parent genes per trait \
(coin flip), plus a uniform mutation from one of 8 offsets in [-R, +R]. \
R = 150 is the fitted nudge range.

Your task: analyze the provided result data and produce opinionated, \
data-driven interpretation summaries. Be specific — cite actual numbers from \
the data. State what the results mean, not just what was measured.
"""


_PROMPT_HEADER = (
    "Analyze the following analysis results and produce interpretation "
    "summaries. For each of the 7 analyses below, generate a JSON object "
    'with this exact schema:\n\n```json\n{\n  "key": "<analysis_key>",\n'
    '  "title": "<display title>",\n  "findings": ["<finding 1>", ...],\n'
    '  "stats": { "<stat_name>": <value>, ... }\n}\n```\n\n'
    "Requirements:\n- findings: 3-6 bullet points per analysis, each a complete sentence\n"
    "- findings should be OPINIONATED — state conclusions, not just observations\n"
    "- Cite specific numbers (e.g., 'cv_ll = -5844.4', '12 of 56 pairs')\n"
    "- stats: include the key numeric values that the web dashboard needs\n"
    "- Be concise but precise\n\n"
    "Return ONLY valid JSON, no markdown fencing, no commentary.\n\n"
    "Required stats keys: models(n_models,best_model,best_cv_ll,worst_model,"
    "worst_cv_ll,better_than_claim,models_with_impossible) anomalies(n_children,"
    "mean_log_lik,std_log_lik,n_outliers_2std,worst_child,worst_log_lik) "
    "mi_matrix(n_pairs,diag_mean_z,offdiag_mean_z,n_high_offdiag) "
    "residuals(color/sweet/size/length_mean_abs_residual,n_sig_sibling_corr,"
    "mean_abs_sibling_r) r_sweep(best_R,best_cv_ll,r_range,total_cv_range) "
    "distribution_tests(n_pairs,n_ks_sig_fdr,pct_sig,n_ad_sig_5pct) "
    "mixture(n_litters,mean_pi_claim,min_pi_claim,min_pi_litter,n_indep_heavy)\n\n---\n\n"
)


def _serialize_data(data: object, max_len: int = 20000) -> str:
    """Serialize data to JSON, truncating large arrays."""
    json_str = json.dumps(data, indent=None)
    if len(json_str) > max_len and isinstance(data, list):
        sample = data[:20] + data[-5:] if len(data) > 25 else data
        json_str = json.dumps(sample, indent=None)
        json_str += f"\n(Showing {len(sample)} of {len(data)} records)"
    return json_str


def _build_prompt(data: dict[str, object]) -> str:
    """Build the interpretation prompt from loaded data."""
    parts = [_PROMPT_HEADER]

    for key, src in ANALYSIS_SOURCES.items():
        if key in data:
            parts.append(f"### {key} ({src})\n```json\n{_serialize_data(data[key])}\n```\n\n")

    for key, src in SUPPLEMENTARY.items():
        if key in data:
            s = json.dumps(data[key], indent=None)
            parts.append(f"### Supplementary: {key} ({src})\n```json\n{s[:10000]}\n```\n\n")

    return "".join(parts)


def _load_data() -> dict[str, object]:
    """Load all analysis result JSONs from the data directory."""
    data: dict[str, object] = {}

    for key, filename in {**ANALYSIS_SOURCES, **SUPPLEMENTARY}.items():
        path = DATA_DIR / filename
        if path.exists():
            with path.open(encoding="utf-8") as f:
                data[key] = json.load(f)
        else:
            print(f"  SKIP {filename} (not found)")

    return data


def _load_env() -> None:
    """Load .env file from project root if it exists."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    with env_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v


def _find_claude_cmd() -> str | None:
    """Find the claude CLI command, handling Windows .CMD wrappers."""
    path = shutil.which("claude")
    return path


def _claude_cli_available() -> bool:
    """Check if claude CLI is available."""
    return _find_claude_cmd() is not None


def _run_claude(prompt: str) -> str | None:
    """Call claude CLI with the given prompt. Returns response text or None on failure."""
    claude_cmd = _find_claude_cmd()
    if claude_cmd is None:
        print("  Claude CLI not found")
        return None
    try:
        # Pass prompt via stdin to avoid command-line length limits (Windows: 8191 chars)
        # On Windows, .CMD files need shell=True
        use_shell = claude_cmd.lower().endswith((".cmd", ".bat"))
        result = subprocess.run(
            [claude_cmd, "-p", "--output-format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
            shell=use_shell,
        )
        if result.returncode != 0:
            print(f"  Claude CLI failed (exit {result.returncode}): {result.stderr[:500]}")
            return None
        # Parse the JSON output format — claude --output-format json wraps in {"result": ...}
        try:
            outer = json.loads(result.stdout)
            if isinstance(outer, dict) and "result" in outer:
                return str(outer["result"])
        except json.JSONDecodeError:
            pass
        return result.stdout
    except FileNotFoundError:
        print("  Claude CLI not found")
        return None
    except subprocess.TimeoutExpired:
        print("  Claude CLI timed out (300s)")
        return None


def _parse_response(response: str) -> dict | None:
    """Parse Claude's response into the interpretations dict."""
    # Strip markdown fencing if present
    text = response.strip()
    if text.startswith("```"):
        # Remove first and last ``` lines
        lines = text.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end])

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start:end])
            except json.JSONDecodeError:
                print("  Failed to parse Claude response as JSON")
                return None
        else:
            print("  No JSON object found in Claude response")
            return None

    if not isinstance(parsed, dict):
        print("  Claude response is not a dict")
        return None

    # Validate structure
    for key in ANALYSIS_SOURCES:
        if key in parsed:
            entry = parsed[key]
            if not isinstance(entry, dict):
                continue
            if "findings" not in entry or "stats" not in entry:
                print(f"  Warning: {key} missing findings or stats")
            # Ensure required fields
            entry.setdefault("key", key)
            entry.setdefault("title", key.replace("_", " ").title())

    return parsed


def run_interpretation() -> dict:
    """Run the full interpretation pipeline. Returns interpretations dict."""
    print("Generating result interpretations...")

    data = _load_data()
    if not data:
        print("  No data files found — skipping interpretation")
        return {}

    _load_env()

    # Try Claude CLI first
    if _claude_cli_available():
        print("  Using Claude CLI for interpretation...")
        prompt = _build_prompt(data)

        response = _run_claude(prompt)
        if response is not None:
            parsed = _parse_response(response)
            if parsed is not None:
                # Verify we got all expected keys
                missing = [k for k in ANALYSIS_SOURCES if k in data and k not in parsed]
                if missing:
                    print(f"  Warning: Claude response missing keys: {missing}")
                    # Fill in missing keys from deterministic fallback
                    from citrus_genetics.analysis.interpret import generate_interpretations

                    fallback = generate_interpretations()
                    for k in missing:
                        if k in fallback:
                            parsed[k] = fallback[k]

                print(f"  Claude CLI generated interpretations for {len(parsed)} analyses")
                return parsed
            print("  Claude response parsing failed — falling back to deterministic")
        else:
            print("  Claude CLI call failed — falling back to deterministic")
    else:
        print("  Claude CLI not available — using deterministic fallback")

    # Deterministic fallback
    from citrus_genetics.analysis.interpret import generate_interpretations

    result = generate_interpretations()
    print(f"  Deterministic fallback generated interpretations for {len(result)} analyses")
    return result


def main() -> None:
    """Run interpretation and write to output file."""
    interps = run_interpretation()

    if interps:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(interps, indent=None), encoding="utf-8")
        print(f"  Written to {OUTPUT_PATH}")
    else:
        print("  No interpretations generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
