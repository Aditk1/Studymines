"""
Evaluation Runner Script for EduSum Research Paper.

Runs the full evaluation pipeline:
1. Approach 1: ROUGE + BERTScore on summarization outputs
2. Approach 2: WER + CER on vision extraction outputs
3. Tesseract vs SAEOCR comparison
4. Baseline model comparisons (TextRank, BART, Pegasus, T5)
5. Exports results to JSON for paper figures

Usage:
    python -m app.evaluation.run_evaluation --approach 1
    python -m app.evaluation.run_evaluation --approach 2
    python -m app.evaluation.run_evaluation --all
"""

import json
import os
import time
import argparse
from typing import Dict, List, Optional
from pathlib import Path


def run_approach1_evaluation(
    documents_dir: Optional[str] = None,
    output_path: str = "evaluation_results/approach1_results.json"
):
    """
    Run Approach 1 evaluation: Multi-format summarization.

    Evaluates generated summaries against reference summaries using:
    - ROUGE-1, ROUGE-2, ROUGE-L
    - BERTScore F1
    """
    from app.evaluation import RougeEvaluator, BERTScoreEvaluator, MeteorEvaluator

    print("=" * 60)
    print("APPROACH 1 EVALUATION: Multi-Format Educational Summarization")
    print("=" * 60)

    rouge_eval = RougeEvaluator()
    bert_eval = BERTScoreEvaluator()
    meteor_eval = MeteorEvaluator()

    # Check if custom dataset exists
    dataset_path = documents_dir or "datasets/edusum_text"
    if os.path.exists(dataset_path):
        print(f"Loading EduSum-Text dataset from {dataset_path}...")
        predictions, references = _load_summarization_dataset(dataset_path)
    else:
        print(f"Dataset not found at {dataset_path}.")
        print("Using sample data for demonstration...")
        predictions, references = _get_sample_summarization_data()

    print(f"\nEvaluating {len(predictions)} samples...")

    results = {
        "approach": "approach_1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(predictions)
    }

    # ROUGE evaluation
    print("\n--- ROUGE Scores ---")
    rouge_results = rouge_eval.compute(predictions, references)
    results["rouge"] = rouge_results
    for metric, score in rouge_results.items():
        print(f"  {metric}: {score:.4f}")

    # BERTScore evaluation
    print("\n--- BERTScore ---")
    bert_results = bert_eval.compute(predictions, references)
    results["bertscore"] = bert_results
    for metric, score in bert_results.items():
        if isinstance(score, float):
            print(f"  {metric}: {score:.4f}")

    # METEOR evaluation
    print("\n--- METEOR Score ---")
    meteor_results = meteor_eval.compute(predictions, references)
    results["meteor"] = meteor_results
    print(f"  METEOR: {meteor_results.get('meteor', 0.0):.4f}")

    # PRD target comparison
    print("\n--- PRD Target Comparison ---")
    rouge1 = rouge_results.get("rouge1", 0)
    bert_f1 = bert_results.get("f1", 0)
    print(f"  ROUGE-1: {rouge1:.4f} (target: >= 0.46, {'✓ PASS' if rouge1 >= 0.46 else '✗ BELOW TARGET'})")
    print(f"  BERTScore F1: {bert_f1:.4f} (target: >= 0.80, {'✓ PASS' if bert_f1 >= 0.80 else '✗ BELOW TARGET'})")

    results["prd_targets"] = {
        "rouge1_target": 0.46,
        "rouge1_meets": rouge1 >= 0.46,
        "bertscore_f1_target": 0.80,
        "bertscore_f1_meets": bert_f1 >= 0.80
    }

    # Save results
    _save_results(results, output_path)
    return results


def run_approach2_evaluation(
    images_dir: Optional[str] = None,
    output_path: str = "evaluation_results/approach2_results.json"
):
    """
    Run Approach 2 evaluation: Vision extraction (SAEOCR).

    Evaluates extracted text against ground truth using:
    - WER (Word Error Rate)
    - CER (Character Error Rate)
    - Tesseract vs SAEOCR comparison
    """
    from app.evaluation import ExtractionAccuracyEvaluator, TesseractBaseline

    print("=" * 60)
    print("APPROACH 2 EVALUATION: Vision-Augmented Extraction (SAEOCR)")
    print("=" * 60)

    accuracy_eval = ExtractionAccuracyEvaluator()
    tesseract = TesseractBaseline()

    # Check if custom dataset exists
    dataset_path = images_dir or "datasets/edusum_vision"
    if os.path.exists(dataset_path):
        print(f"Loading EduSum-Vision dataset from {dataset_path}...")
        image_paths, ground_truths = _load_vision_dataset(dataset_path)
    else:
        print(f"Dataset not found at {dataset_path}.")
        print("Using sample data for demonstration...")
        image_paths, ground_truths = [], []

    results = {
        "approach": "approach_2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(image_paths)
    }

    if image_paths:
        # Run SAEOCR on all images
        print(f"\nExtracting text from {len(image_paths)} images...")
        from app.vision.vision_extractor import extract_from_image

        saeocr_extractions = []
        tesseract_extractions = []

        for i, img_path in enumerate(image_paths):
            print(f"  Processing image {i+1}/{len(image_paths)}: {os.path.basename(img_path)}")

            # SAEOCR extraction
            saeocr_result = extract_from_image(img_path)
            saeocr_extractions.append(saeocr_result.get("extracted_text", ""))

            # Tesseract extraction
            tess_result = tesseract.extract_text(img_path)
            tesseract_extractions.append(tess_result.get("extracted_text", ""))

        # Compute SAEOCR metrics
        print("\n--- SAEOCR (Gemini Vision) Metrics ---")
        saeocr_metrics = accuracy_eval.compute_batch(saeocr_extractions, ground_truths)
        results["saeocr"] = saeocr_metrics
        print(f"  Average WER: {saeocr_metrics['avg_wer']:.4f}")
        print(f"  Average CER: {saeocr_metrics['avg_cer']:.4f}")
        print(f"  Accuracy: {(1 - saeocr_metrics['avg_wer']) * 100:.1f}%")

        # Compute Tesseract metrics
        if tesseract.available:
            print("\n--- Tesseract OCR Baseline Metrics ---")
            tess_metrics = accuracy_eval.compute_batch(tesseract_extractions, ground_truths)
            results["tesseract"] = tess_metrics
            print(f"  Average WER: {tess_metrics['avg_wer']:.4f}")
            print(f"  Average CER: {tess_metrics['avg_cer']:.4f}")
            print(f"  Accuracy: {(1 - tess_metrics['avg_wer']) * 100:.1f}%")

            # Comparison
            print("\n--- SAEOCR vs Tesseract Comparison ---")
            wer_improvement = tess_metrics['avg_wer'] - saeocr_metrics['avg_wer']
            print(f"  WER improvement: {wer_improvement:+.4f}")
            print(f"  SAEOCR {'outperforms' if wer_improvement > 0 else 'underperforms'} Tesseract")
            results["comparison"] = {
                "wer_improvement": wer_improvement,
                "saeocr_better": wer_improvement > 0
            }

        # PRD target
        accuracy_pct = (1 - saeocr_metrics['avg_wer']) * 100
        print(f"\n  Extraction accuracy: {accuracy_pct:.1f}% (target: >= 85%, {'✓ PASS' if accuracy_pct >= 85 else '✗ BELOW TARGET'})")
        results["prd_targets"] = {
            "accuracy_target": 85.0,
            "accuracy_actual": accuracy_pct,
            "meets_target": accuracy_pct >= 85.0
        }
    else:
        print("\nNo images to evaluate. Create the dataset first:")
        print("  1. Create directory: datasets/edusum_vision/")
        print("  2. Add image files (.jpg, .png)")
        print("  3. Add ground truth text files with same name (.txt)")

    _save_results(results, output_path)
    return results


def run_baseline_comparison(
    output_path: str = "evaluation_results/baseline_comparison.json"
):
    """
    Compare EduSum against baseline summarization models.
    PRD Section 6.3: Baseline Models for Comparison.

    Baselines: TextRank, BART, Pegasus, T5-large
    """
    from app.evaluation import RougeEvaluator, BERTScoreEvaluator

    print("=" * 60)
    print("BASELINE MODEL COMPARISON")
    print("=" * 60)

    rouge_eval = RougeEvaluator()

    # Sample documents for comparison
    sample_texts = _get_sample_documents()

    results = {
        "comparison": "baseline_models",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {}
    }

    # 1. TextRank (extractive baseline)
    print("\n--- TextRank (Extractive Baseline) ---")
    try:
        textrank_summaries = _run_textrank(sample_texts)
        results["models"]["textrank"] = {
            "type": "extractive",
            "summaries": textrank_summaries,
            "available": True
        }
        print(f"  Generated {len(textrank_summaries)} summaries")
    except Exception as e:
        print(f"  Skipped: {e}")
        results["models"]["textrank"] = {"available": False, "error": str(e)}

    # 2. BART
    print("\n--- BART (facebook/bart-large-cnn) ---")
    try:
        bart_summaries = _run_huggingface_model(sample_texts, "facebook/bart-large-cnn")
        results["models"]["bart"] = {
            "type": "abstractive",
            "model": "facebook/bart-large-cnn",
            "summaries": bart_summaries,
            "available": True
        }
        print(f"  Generated {len(bart_summaries)} summaries")
    except Exception as e:
        print(f"  Skipped: {e}")
        results["models"]["bart"] = {"available": False, "error": str(e)}

    # 3. Pegasus
    print("\n--- Pegasus (google/pegasus-xsum) ---")
    try:
        pegasus_summaries = _run_huggingface_model(sample_texts, "google/pegasus-xsum")
        results["models"]["pegasus"] = {
            "type": "abstractive",
            "model": "google/pegasus-xsum",
            "summaries": pegasus_summaries,
            "available": True
        }
        print(f"  Generated {len(pegasus_summaries)} summaries")
    except Exception as e:
        print(f"  Skipped: {e}")
        results["models"]["pegasus"] = {"available": False, "error": str(e)}

    # 4. T5-large
    print("\n--- T5-large ---")
    try:
        t5_summaries = _run_huggingface_model(sample_texts, "t5-large", prefix="summarize: ")
        results["models"]["t5_large"] = {
            "type": "seq2seq",
            "model": "t5-large",
            "summaries": t5_summaries,
            "available": True
        }
        print(f"  Generated {len(t5_summaries)} summaries")
    except Exception as e:
        print(f"  Skipped: {e}")
        results["models"]["t5_large"] = {"available": False, "error": str(e)}

    # 5. EduSum (Gemini 1.5 Pro)
    print("\n--- EduSum (Gemini 1.5 Pro + EPF) ---")
    try:
        from app.llm.epf_generator import EPFGenerator
        generator = EPFGenerator()
        edusum_summaries = []
        for text in sample_texts:
            result = generator.generate_summary(text)
            summary = result.get("content", result.get("error", ""))
            edusum_summaries.append(summary)
        results["models"]["edusum"] = {
            "type": "llm_epf",
            "model": "gemini-1.5-pro",
            "summaries": edusum_summaries,
            "available": True
        }
        print(f"  Generated {len(edusum_summaries)} summaries")
    except Exception as e:
        print(f"  Skipped: {e}")
        results["models"]["edusum"] = {"available": False, "error": str(e)}

    _save_results(results, output_path)
    print(f"\nResults saved to {output_path}")
    return results


# ============================================================
# Helper functions
# ============================================================

def _run_textrank(texts: List[str]) -> List[str]:
    """Run TextRank extractive summarization."""
    try:
        from gensim.summarization import summarize
        return [summarize(text, ratio=0.3) for text in texts]
    except ImportError:
        # Fallback: simple sentence scoring
        import re
        summaries = []
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            # Take top 30% of sentences by length (naive extractive)
            n = max(1, len(sentences) // 3)
            scored = sorted(sentences, key=len, reverse=True)[:n]
            summaries.append('. '.join(scored) + '.')
        return summaries


def _run_huggingface_model(
    texts: List[str],
    model_name: str,
    prefix: str = "",
    max_length: int = 150
) -> List[str]:
    """Run a HuggingFace summarization model."""
    from transformers import pipeline
    summarizer = pipeline("summarization", model=model_name, device=-1)  # CPU

    summaries = []
    for text in texts:
        input_text = prefix + text[:1024]  # Truncate for model limit
        result = summarizer(input_text, max_length=max_length, min_length=30, do_sample=False)
        summaries.append(result[0]["summary_text"])
    return summaries


def _load_summarization_dataset(dataset_dir: str):
    """
    Load summarization dataset from directory.
    Expects pairs: <name>.txt (source) and <name>.ref.txt (reference summary).
    """
    predictions = []
    references = []
    dataset_path = Path(dataset_dir)

    for ref_file in sorted(dataset_path.glob("*.ref.txt")):
        source_file = dataset_path / ref_file.name.replace(".ref.txt", ".txt")
        if source_file.exists():
            with open(ref_file, 'r', encoding='utf-8') as f:
                references.append(f.read().strip())
            # Generate summary using EduSum
            from app.llm.epf_generator import EPFGenerator
            generator = EPFGenerator()
            with open(source_file, 'r', encoding='utf-8') as f:
                source_text = f.read().strip()
            result = generator.generate_summary(source_text)
            predictions.append(result.get("content", ""))

    return predictions, references


def _load_vision_dataset(dataset_dir: str):
    """
    Load vision dataset from directory.
    Expects pairs: <name>.jpg/.png (image) and <name>.txt (ground truth text).
    """
    image_paths = []
    ground_truths = []
    dataset_path = Path(dataset_dir)

    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    for img_file in sorted(dataset_path.iterdir()):
        if img_file.suffix.lower() in image_extensions:
            gt_file = dataset_path / (img_file.stem + ".txt")
            if gt_file.exists():
                image_paths.append(str(img_file))
                with open(gt_file, 'r', encoding='utf-8') as f:
                    ground_truths.append(f.read().strip())

    return image_paths, ground_truths


def _get_sample_summarization_data():
    """Return sample prediction-reference pairs for demo evaluation."""
    predictions = [
        "Photosynthesis is the process by which plants convert light energy into chemical energy. "
        "It occurs in chloroplasts using chlorophyll to absorb sunlight. The process involves "
        "two stages: light-dependent reactions and the Calvin cycle.",

        "Machine learning is a subset of artificial intelligence that enables systems to learn "
        "from data. It includes supervised, unsupervised, and reinforcement learning approaches.",
    ]
    references = [
        "Photosynthesis is the biological process where green plants use sunlight to synthesize "
        "nutrients from carbon dioxide and water. It mainly takes place in plant leaves via "
        "chlorophyll. The light reactions capture energy and the Calvin cycle fixes carbon.",

        "Machine learning is an AI discipline where computers learn patterns from data without "
        "explicit programming. The three main paradigms are supervised learning, unsupervised "
        "learning, and reinforcement learning.",
    ]
    return predictions, references


def _get_sample_documents():
    """Return sample documents for baseline comparison."""
    return [
        """Photosynthesis is a process used by plants and other organisms to convert light energy
into chemical energy that can later be released to fuel the organism's activities. This chemical
energy is stored in carbohydrate molecules, such as sugars and starches, which are synthesized
from carbon dioxide and water. In most cases, oxygen is also released as a waste product that
sustains aerobic life. Most plants, algae, and cyanobacteria perform photosynthesis. Such
organisms are called photoautotrophs. Photosynthesis is largely responsible for producing and
maintaining the oxygen content of the Earth's atmosphere, and supplies most of the energy
necessary for life on Earth.""",

        """Machine learning is a method of data analysis that automates analytical model building.
It is a branch of artificial intelligence based on the idea that systems can learn from data,
identify patterns and make decisions with minimal human intervention. The process of learning
begins with observations or data, such as examples, direct experience, or instruction, in order
to look for patterns in data and make better decisions in the future based on the examples that
we provide. The primary aim is to allow the computers to learn automatically without human
intervention or assistance and adjust actions accordingly.""",
    ]


def _save_results(results: dict, output_path: str):
    """Save evaluation results to JSON file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n{'='*60}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="EduSum Evaluation Runner")
    parser.add_argument(
        "--approach", type=int, choices=[1, 2],
        help="Run evaluation for Approach 1 or 2"
    )
    parser.add_argument(
        "--baselines", action="store_true",
        help="Run baseline model comparison"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all evaluations"
    )
    parser.add_argument(
        "--documents-dir", type=str, default=None,
        help="Path to EduSum-Text dataset directory"
    )
    parser.add_argument(
        "--images-dir", type=str, default=None,
        help="Path to EduSum-Vision dataset directory"
    )

    args = parser.parse_args()

    os.makedirs("evaluation_results", exist_ok=True)

    if args.all or args.approach == 1:
        run_approach1_evaluation(documents_dir=args.documents_dir)

    if args.all or args.approach == 2:
        run_approach2_evaluation(images_dir=args.images_dir)

    if args.all or args.baselines:
        run_baseline_comparison()

    if not (args.all or args.approach or args.baselines):
        print("No evaluation selected. Use --approach 1, --approach 2, --baselines, or --all")
        parser.print_help()


if __name__ == "__main__":
    main()
