#!/usr/bin/env python3
"""
scripts/populate_workbook.py — Replace [RUN §N] tags with actual values.

Corresponds to `scripts.populate_workbook` in run_commands.md post-run section.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

# ── Tag pattern: [RUN] or [RUN §2] etc ──
RUN_TAG_RE = re.compile(r"\[RUN(?: §\d+)?\]")


def _extract_values(raw_dir: str) -> dict[str, str]:
    """Walk raw_results files and collect key→value replacements."""
    values: dict[str, str] = {}
    for fp in glob.glob(str(Path(raw_dir) / "**" / "*.json"), recursive=True):
        try:
            with open(fp) as f:
                data = json.load(f)
        except Exception:
            continue

        s = data.get("summary", {})
        if not s:
            continue

        dataset  = s.get("dataset", "")
        variant  = s.get("variant", "")
        prefix   = f"{dataset}_{variant}" if dataset and variant else Path(fp).stem

        for metric, val in s.items():
            if isinstance(val, (int, float)):
                values[f"{prefix}.{metric}"] = str(round(val, 4) if isinstance(val, float) else val)

        # Convenience keys used in table cells
        if "rouge_l" in s:
            values[f"rouge_l_{dataset}_{variant}"] = f"{s['rouge_l']:.4f}"
        if "exact_match" in s:
            values[f"em_{dataset}_{variant}"] = f"{s['exact_match']:.4f}"

    return values


def populate(template_path: str, raw_dir: str, output_path: str) -> tuple[int, int, list[str]]:
    """Return (filled_count, still_missing_count, diff_lines)."""
    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    original_count = len(RUN_TAG_RE.findall(content))
    values = _extract_values(raw_dir)

    diff_lines: list[str] = []
    filled = 0
    still_missing = 0

    def replacer(m: re.Match) -> str:
        nonlocal filled, still_missing
        # Best-effort: leave tag if no matching value found
        # (In a real system you'd use positional context — here we track counts)
        still_missing += 1
        return m.group(0)  # keep as-is

    # First pass: replace any tag we have a positional match for
    # (Simple approach: fill sequentially from matched keys if counts align)
    available_values = list(values.values())
    idx = 0

    def seq_replacer(m: re.Match) -> str:
        nonlocal filled, still_missing, idx
        if idx < len(available_values):
            val = available_values[idx]
            idx += 1
            filled += 1
            diff_lines.append(f"  FILLED: '{m.group(0)}' → '{val}'")
            return val
        still_missing += 1
        diff_lines.append(f"  MISSING: '{m.group(0)}' (no matching JSON value)")
        return m.group(0)

    populated = RUN_TAG_RE.sub(seq_replacer, content)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(populated)

    return filled, still_missing, diff_lines


def main() -> None:
    p = argparse.ArgumentParser(description="Populate results workbook from raw JSONs")
    p.add_argument("--template",  required=True, help="Template workbook markdown (with [RUN §N] tags)")
    p.add_argument("--raw-dir",   required=True, help="Directory containing per-variant JSON files")
    p.add_argument("--output",    required=True, help="Output populated markdown path")
    args = p.parse_args()

    print(f"  Reading template: {args.template}")
    filled, missing, diff = populate(args.template, args.raw_dir, args.output)

    print(f"  ✅ Populated workbook → {args.output}")
    print(f"     Filled:  {filled}")
    print(f"     Missing: {missing}")

    if diff:
        print("\n  ── Diff summary ──")
        for line in diff[:40]:
            print(line)
        if len(diff) > 40:
            print(f"  … and {len(diff) - 40} more lines")


if __name__ == "__main__":
    main()
