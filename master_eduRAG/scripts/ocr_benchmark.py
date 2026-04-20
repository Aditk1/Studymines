#!/usr/bin/env python3
"""
scripts/ocr_benchmark.py — OCR accuracy benchmark by document type.

Corresponds to `scripts.ocr_benchmark` in run_commands.md §6.
Engines: saeocr_v1.2 (internal VisionExtractor), tesseract_v5 (pytesseract).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DOC_TYPE_EXT = {
    "scanned_textbooks": {".pdf"},
    "handwritten_notes": {".jpg", ".jpeg", ".png"},
    "annotated_pdfs":    {".pdf"},
}


def _run_saeocr(path: Path) -> str:
    """Use the internal vision extractor (Groq/Gemini) as SAEOCR surrogate."""
    try:
        from app.vision.vision_extractor import VisionExtractor
        extractor = VisionExtractor()
        result = extractor.extract_from_image(str(path))
        return result.get("text", "")
    except Exception as e:
        return f"[saeocr_error: {e}]"


def _run_tesseract(path: Path) -> str:
    """Call pytesseract if available."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except ImportError:
        return "[tesseract_unavailable: install pytesseract + Tesseract binary]"
    except Exception as e:
        return f"[tesseract_error: {e}]"


def _char_accuracy(pred: str, ref: str) -> float:
    """Simple character-level accuracy (1 - CER)."""
    if not ref:
        return 0.0
    matches = sum(a == b for a, b in zip(pred, ref))
    return matches / max(len(ref), len(pred))


def main() -> None:
    p = argparse.ArgumentParser(description="OCR benchmark by document type")
    p.add_argument("--input",     required=True,  help="Directory with OCR benchmark documents")
    p.add_argument("--engines",   required=True,  nargs="+", help="e.g. saeocr_v1.2 tesseract_v5")
    p.add_argument("--by-type",   required=True,  nargs="+", help="Document types to benchmark")
    p.add_argument("--output",    required=True,  help="Output JSON path")
    p.add_argument("--emit-markdown", default=None)
    args = p.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"⚠️  Input directory not found: {input_dir}")
        print("   Create data/ocr_bench/ with sub-folders per doc type and ground-truth .txt siblings.")
        # Emit placeholder output so downstream scripts don't break
        placeholder = {
            "note": "ocr_bench directory not found — populate data/ocr_bench/ and rerun",
            "results": {}
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(placeholder, f, indent=2)
        sys.exit(0)

    results: dict = {}
    for doc_type in args.by_type:
        type_dir = input_dir / doc_type
        if not type_dir.exists():
            print(f"  ⚠  Doc-type directory missing: {type_dir}")
            continue

        engine_scores: dict[str, list[float]] = {e: [] for e in args.engines}

        # For each document: look for a .txt ground-truth sibling
        for doc_file in sorted(type_dir.iterdir()):
            gt_file = doc_file.with_suffix(".txt")
            if not gt_file.exists():
                continue  # No ground truth, skip

            gt_text = gt_file.read_text(encoding="utf-8", errors="ignore")

            for engine in args.engines:
                if engine.startswith("saeocr"):
                    pred = _run_saeocr(doc_file)
                elif engine.startswith("tesseract"):
                    pred = _run_tesseract(doc_file)
                else:
                    pred = ""
                acc = _char_accuracy(pred, gt_text)
                engine_scores[engine].append(acc)
                print(f"    {engine} / {doc_type} / {doc_file.name}: {acc:.3f}")

        results[doc_type] = {
            engine: {
                "accuracy": round(sum(scores) / len(scores), 4) if scores else None,
                "n_docs":   len(scores),
            }
            for engine, scores in engine_scores.items()
        }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  ✅ OCR results → {args.output}")

    if args.emit_markdown:
        lines = [
            "# OCR Benchmark Results by Document Type", "",
            "| Document Type | " + " | ".join(args.engines) + " |",
            "|---|" + "---:|" * len(args.engines),
        ]
        for dt, eng_data in results.items():
            row = f"| {dt} |"
            for eng in args.engines:
                d = eng_data.get(eng, {})
                acc = d.get("accuracy")
                row += f" {acc*100:.1f}% |" if acc is not None else " — |"
            lines.append(row)
        Path(args.emit_markdown).parent.mkdir(parents=True, exist_ok=True)
        with open(args.emit_markdown, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"  📄 OCR markdown → {args.emit_markdown}")


if __name__ == "__main__":
    main()
