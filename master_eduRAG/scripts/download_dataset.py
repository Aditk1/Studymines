#!/usr/bin/env python3
"""
scripts/download_dataset.py — Dataset download helper stub.

Corresponds to `scripts.download_dataset` in run_commands.md §2a, §3a.
Prints instructions and checks whether the dataset directory already exists.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

INSTRUCTIONS = {
    "musique": """
  MuSiQue Dataset Instructions:
  ─────────────────────────────
  1. Visit: https://github.com/StonyBrookNLP/musique
  2. Follow the download instructions in the README.
  3. Place the dev split at:  data/musique/data/musique_ans.json
  4. Optionally run their preprocessing script.
""",
    "2wiki": """
  2WikiMultiHopQA Dataset Instructions:
  ──────────────────────────────────────
  1. Visit: https://github.com/Alab-NII/2wikimultihop
  2. Download the dataset from the Releases page.
  3. Place the dev split at:  data/2WikiMultiHopQA/data/dev_ids.json
""",
}


def main() -> None:
    p = argparse.ArgumentParser(description="Dataset download helper")
    p.add_argument("--name",   required=True, help="Dataset name: musique | 2wiki")
    p.add_argument("--split",  default="dev")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--url",    default=None)
    args = p.parse_args()

    out = Path(args.output)
    if out.exists() and any(out.iterdir()):
        print(f"  ✓ Dataset '{args.name}' already present at {out}")
        sys.exit(0)

    print(f"  ⚠  Dataset '{args.name}' not found at {out}.")
    print(INSTRUCTIONS.get(args.name, f"  No instructions available for '{args.name}'."))
    print(f"  Expected URL: {args.url or 'see instructions above'}")
    sys.exit(1)


if __name__ == "__main__":
    main()
