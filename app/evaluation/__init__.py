"""
Evaluation module for EduSum.
Implements all evaluation metrics specified in the PRD:

- ROUGE-1, ROUGE-2, ROUGE-L (Approach 1 baseline comparison)
- BERTScore F1 (Approach 1 quality measurement)
- WER - Word Error Rate (Approach 2 vs Tesseract comparison)
- CER - Character Error Rate (Approach 2 handwriting evaluation)
- Educational Utility Score (human evaluation framework)

PRD Section 6.2: Evaluation Metrics
"""

from typing import Dict, List, Optional, Tuple
import json


class RougeEvaluator:
    """
    ROUGE metric computation for summarization evaluation.
    Uses HuggingFace evaluate library.
    """

    def __init__(self):
        """Initialize ROUGE evaluator."""
        try:
            import evaluate
            self.rouge = evaluate.load("rouge")
            self.available = True
        except Exception as e:
            print(f"Warning: ROUGE evaluator not available: {e}")
            self.available = False

    def compute(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """
        Compute ROUGE-1, ROUGE-2, and ROUGE-L scores.

        Args:
            predictions: List of generated summaries.
            references: List of reference summaries.

        Returns:
            Dictionary with rouge1, rouge2, rougeL scores.
        """
        if not self.available:
            return {"error": "ROUGE evaluator not available. Install: pip install evaluate rouge-score"}

        if len(predictions) != len(references):
            raise ValueError("predictions and references must have the same length")

        results = self.rouge.compute(
            predictions=predictions,
            references=references,
            use_aggregator=True
        )

        return {
            "rouge1": round(results["rouge1"], 4),
            "rouge2": round(results["rouge2"], 4),
            "rougeL": round(results["rougeL"], 4),
        }

    def compute_single(self, prediction: str, reference: str) -> Dict[str, float]:
        """Compute ROUGE scores for a single prediction-reference pair."""
        return self.compute([prediction], [reference])


class BERTScoreEvaluator:
    """
    BERTScore F1 computation for semantic similarity evaluation.
    Uses HuggingFace evaluate library.
    """

    def __init__(self, model_type: str = "microsoft/deberta-xlarge-mnli"):
        """
        Initialize BERTScore evaluator.

        Args:
            model_type: Model to use for BERTScore. Default uses DeBERTa for accuracy.
        """
        self.model_type = model_type
        try:
            import evaluate
            self.bertscore = evaluate.load("bertscore")
            self.available = True
        except Exception as e:
            print(f"Warning: BERTScore evaluator not available: {e}")
            self.available = False

    def compute(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """
        Compute BERTScore (precision, recall, F1).

        Args:
            predictions: List of generated texts.
            references: List of reference texts.

        Returns:
            Dictionary with precision, recall, f1 (averaged).
        """
        if not self.available:
            return {"error": "BERTScore evaluator not available. Install: pip install evaluate bert-score"}

        results = self.bertscore.compute(
            predictions=predictions,
            references=references,
            model_type=self.model_type,
            lang="en"
        )

        # Average across all samples
        n = len(predictions)
        return {
            "precision": round(sum(results["precision"]) / n, 4),
            "recall": round(sum(results["recall"]) / n, 4),
            "f1": round(sum(results["f1"]) / n, 4),
        }

    def compute_single(self, prediction: str, reference: str) -> Dict[str, float]:
        """Compute BERTScore for a single pair."""
        return self.compute([prediction], [reference])


class MeteorEvaluator:
    """
    METEOR metric computation for summarization evaluation.
    Measures precision, recall, and synonym matching.
    PRD Section 6.2 requirement.
    """

    def __init__(self):
        """Initialize METEOR evaluator using NLTK."""
        try:
            import nltk
            from nltk.translate.meteor_score import meteor_score
            self.meteor_score = meteor_score
            # Ensure wordnet/punkt are available
            try:
                nltk.data.find('corpora/wordnet')
            except (LookupError, OSError):
                nltk.download('wordnet')
            try:
                nltk.data.find('tokenizers/punkt')
            except (LookupError, OSError):
                nltk.download('punkt')
            self.available = True
        except Exception as e:
            print(f"Warning: METEOR evaluator not available: {e}")
            self.available = False

    def compute(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        Compute METEOR score for a batch.

        Args:
            predictions: List of generated summaries.
            references: List of reference summaries.

        Returns:
            Dictionary with average meteor score.
        """
        if not self.available:
            return {"error": "METEOR evaluator not available. Install: pip install nltk"}

        import nltk
        scores = []
        for pred, ref in zip(predictions, references):
            # NLTK expects tokenized inputs
            pred_tokens = nltk.word_tokenize(pred)
            ref_tokens = nltk.word_tokenize(ref)
            score = self.meteor_score([ref_tokens], pred_tokens)
            scores.append(score)

        return {
            "meteor": round(sum(scores) / len(scores), 4) if scores else 0.0
        }


class ExtractionAccuracyEvaluator:
    """
    WER and CER computation for vision extraction evaluation.
    Compares extracted text against ground truth.
    Used for Approach 2 vs Tesseract comparison.
    """

    @staticmethod
    def compute_wer(prediction: str, reference: str) -> float:
        """
        Compute Word Error Rate (WER).
        WER = (Substitutions + Insertions + Deletions) / Words in Reference

        Args:
            prediction: Extracted text.
            reference: Ground truth text.

        Returns:
            WER as a float (0.0 = perfect, 1.0 = all wrong).
        """
        pred_words = prediction.strip().lower().split()
        ref_words = reference.strip().lower().split()

        if len(ref_words) == 0:
            return 0.0 if len(pred_words) == 0 else 1.0

        # Dynamic programming for edit distance at word level
        d = [[0] * (len(pred_words) + 1) for _ in range(len(ref_words) + 1)]

        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(pred_words) + 1):
            d[0][j] = j

        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(pred_words) + 1):
                if ref_words[i - 1] == pred_words[j - 1]:
                    d[i][j] = d[i - 1][j - 1]
                else:
                    d[i][j] = min(
                        d[i - 1][j] + 1,      # deletion
                        d[i][j - 1] + 1,      # insertion
                        d[i - 1][j - 1] + 1   # substitution
                    )

        wer = d[len(ref_words)][len(pred_words)] / len(ref_words)
        return round(wer, 4)

    @staticmethod
    def compute_cer(prediction: str, reference: str) -> float:
        """
        Compute Character Error Rate (CER).
        CER = (Substitutions + Insertions + Deletions) / Characters in Reference

        Args:
            prediction: Extracted text.
            reference: Ground truth text.

        Returns:
            CER as a float (0.0 = perfect).
        """
        pred_chars = list(prediction.strip().lower())
        ref_chars = list(reference.strip().lower())

        if len(ref_chars) == 0:
            return 0.0 if len(pred_chars) == 0 else 1.0

        # Dynamic programming for edit distance at character level
        d = [[0] * (len(pred_chars) + 1) for _ in range(len(ref_chars) + 1)]

        for i in range(len(ref_chars) + 1):
            d[i][0] = i
        for j in range(len(pred_chars) + 1):
            d[0][j] = j

        for i in range(1, len(ref_chars) + 1):
            for j in range(1, len(pred_chars) + 1):
                if ref_chars[i - 1] == pred_chars[j - 1]:
                    d[i][j] = d[i - 1][j - 1]
                else:
                    d[i][j] = min(
                        d[i - 1][j] + 1,
                        d[i][j - 1] + 1,
                        d[i - 1][j - 1] + 1
                    )

        cer = d[len(ref_chars)][len(pred_chars)] / len(ref_chars)
        return round(cer, 4)

    def compute_batch(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict[str, float]:
        """
        Compute average WER and CER for a batch of predictions.

        Args:
            predictions: List of extracted texts.
            references: List of ground truth texts.

        Returns:
            Dictionary with average wer and cer.
        """
        if len(predictions) != len(references):
            raise ValueError("predictions and references must have the same length")

        wers = [self.compute_wer(p, r) for p, r in zip(predictions, references)]
        cers = [self.compute_cer(p, r) for p, r in zip(predictions, references)]

        return {
            "avg_wer": round(sum(wers) / len(wers), 4),
            "avg_cer": round(sum(cers) / len(cers), 4),
            "individual_wer": wers,
            "individual_cer": cers,
            "samples": len(predictions)
        }


class EducationalUtilityEvaluator:
    """
    Framework for the Educational Utility Score — a novel human evaluation metric.
    PRD Section 6.4: Human Evaluation Protocol

    4 dimensions rated on a 5-point scale by 20 evaluators:
    - Accuracy: Does the summary faithfully represent the source?
    - Clarity: Is the language appropriate for the student level?
    - Completeness: Are all major concepts covered?
    - Educational Utility: Would this help you study for an exam?
    """

    DIMENSIONS = ["accuracy", "clarity", "completeness", "educational_utility"]

    def __init__(self):
        """Initialize with empty ratings storage."""
        self.ratings: List[Dict] = []

    def add_rating(
        self,
        evaluator_id: str,
        document_id: str,
        accuracy: int,
        clarity: int,
        completeness: int,
        educational_utility: int,
        comments: Optional[str] = None
    ) -> Dict:
        """
        Record a single evaluator rating.

        Args:
            evaluator_id: Unique evaluator identifier.
            document_id: Document being evaluated.
            accuracy: Score 1-5.
            clarity: Score 1-5.
            completeness: Score 1-5.
            educational_utility: Score 1-5.
            comments: Optional evaluator comments.

        Returns:
            The recorded rating.
        """
        # Validate scores
        for name, score in [
            ("accuracy", accuracy),
            ("clarity", clarity),
            ("completeness", completeness),
            ("educational_utility", educational_utility)
        ]:
            if not (1 <= score <= 5):
                raise ValueError(f"{name} must be between 1 and 5, got {score}")

        rating = {
            "evaluator_id": evaluator_id,
            "document_id": document_id,
            "accuracy": accuracy,
            "clarity": clarity,
            "completeness": completeness,
            "educational_utility": educational_utility,
            "comments": comments
        }
        self.ratings.append(rating)
        return rating

    def compute_aggregate(self) -> Dict:
        """
        Compute aggregate statistics across all ratings.

        Returns:
            Dictionary with per-dimension averages and overall score.
        """
        if not self.ratings:
            return {"error": "No ratings recorded"}

        n = len(self.ratings)
        averages = {}

        for dim in self.DIMENSIONS:
            scores = [r[dim] for r in self.ratings]
            averages[dim] = {
                "mean": round(sum(scores) / n, 2),
                "min": min(scores),
                "max": max(scores),
                "std": round(self._std(scores), 2)
            }

        # Overall educational utility score (PRD target: >= 4.2 / 5.0)
        overall = sum(
            averages[dim]["mean"] for dim in self.DIMENSIONS
        ) / len(self.DIMENSIONS)

        return {
            "dimensions": averages,
            "overall_score": round(overall, 2),
            "target_score": 4.2,
            "meets_target": overall >= 4.2,
            "total_ratings": n,
            "unique_evaluators": len(set(r["evaluator_id"] for r in self.ratings)),
            "unique_documents": len(set(r["document_id"] for r in self.ratings))
        }

    @staticmethod
    def _std(values: List[float]) -> float:
        """Compute standard deviation."""
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        return variance ** 0.5

    def export_ratings(self, filepath: str):
        """Export all ratings to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump({
                "ratings": self.ratings,
                "aggregate": self.compute_aggregate()
            }, f, indent=2)

    def load_ratings(self, filepath: str):
        """Load ratings from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.ratings = data.get("ratings", [])


class TesseractBaseline:
    """
    Tesseract OCR baseline for comparison against SAEOCR (Approach 2).
    PRD Section 5.4.3: Comparison with Traditional OCR
    """

    def __init__(self):
        """Initialize Tesseract baseline."""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            print("Warning: pytesseract not installed. Install: pip install pytesseract")
            print("Also requires Tesseract OCR v5 system installation.")
            self.available = False

    def extract_text(self, image_path: str) -> Dict[str, str]:
        """
        Extract text from image using Tesseract OCR.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary with extracted text and metadata.
        """
        if not self.available:
            return {
                "extracted_text": "",
                "error": "pytesseract not available",
                "method": "tesseract"
            }

        try:
            from PIL import Image
            image = Image.open(image_path)
            text = self.pytesseract.image_to_string(image)

            return {
                "extracted_text": text,
                "method": "tesseract",
                "confidence": "n/a"
            }
        except Exception as e:
            return {
                "extracted_text": "",
                "error": str(e),
                "method": "tesseract"
            }

    def compare_with_saeocr(
        self,
        image_path: str,
        ground_truth: str
    ) -> Dict:
        """
        Compare Tesseract extraction vs SAEOCR extraction against ground truth.

        Args:
            image_path: Path to image.
            ground_truth: Known correct text for the image.

        Returns:
            Comparison results with WER and CER for both methods.
        """
        from app.vision.vision_extractor import extract_from_image

        accuracy_eval = ExtractionAccuracyEvaluator()

        # Tesseract extraction
        tesseract_result = self.extract_text(image_path)
        tesseract_text = tesseract_result.get("extracted_text", "")

        # SAEOCR extraction (Gemini Vision)
        saeocr_result = extract_from_image(image_path)
        saeocr_text = saeocr_result.get("extracted_text", "")

        # Compute metrics
        tesseract_wer = accuracy_eval.compute_wer(tesseract_text, ground_truth)
        tesseract_cer = accuracy_eval.compute_cer(tesseract_text, ground_truth)
        saeocr_wer = accuracy_eval.compute_wer(saeocr_text, ground_truth)
        saeocr_cer = accuracy_eval.compute_cer(saeocr_text, ground_truth)

        return {
            "image": image_path,
            "ground_truth_length": len(ground_truth.split()),
            "tesseract": {
                "wer": tesseract_wer,
                "cer": tesseract_cer,
                "extracted_words": len(tesseract_text.split()),
                "accuracy_pct": round((1 - tesseract_wer) * 100, 1)
            },
            "saeocr": {
                "wer": saeocr_wer,
                "cer": saeocr_cer,
                "extracted_words": len(saeocr_text.split()),
                "accuracy_pct": round((1 - saeocr_wer) * 100, 1),
                "content_type": saeocr_result.get("content_type", "unknown"),
                "confidence": saeocr_result.get("confidence", "unknown")
            },
            "saeocr_improvement": {
                "wer_reduction": round(tesseract_wer - saeocr_wer, 4),
                "cer_reduction": round(tesseract_cer - saeocr_cer, 4),
                "saeocr_better": saeocr_wer < tesseract_wer
            }
        }


class EvaluationRunner:
    """
    Orchestrates full evaluation pipeline for research paper results.
    Runs all metrics and produces a comprehensive evaluation report.
    """

    def __init__(self):
        """Initialize all evaluators."""
        self.rouge_eval = RougeEvaluator()
        self.bert_eval = BERTScoreEvaluator()
        self.meteor_eval = MeteorEvaluator()
        self.extraction_eval = ExtractionAccuracyEvaluator()
        self.utility_eval = EducationalUtilityEvaluator()
        self.tesseract_baseline = TesseractBaseline()

    def evaluate_approach1(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict:
        """
        Full Approach 1 evaluation: ROUGE + BERTScore.

        Args:
            predictions: Generated summaries.
            references: Reference summaries.

        Returns:
            Combined evaluation results.
        """
        results = {
            "approach": "approach_1_summarization",
            "samples": len(predictions)
        }

        # ROUGE scores
        rouge_results = self.rouge_eval.compute(predictions, references)
        results["rouge"] = rouge_results

        # BERTScore
        bert_results = self.bert_eval.compute(predictions, references)
        results["bertscore"] = bert_results

        # METEOR
        meteor_results = self.meteor_eval.compute(predictions, references)
        results["meteor"] = meteor_results

        return results

    def evaluate_approach2(
        self,
        predictions: List[str],
        references: List[str]
    ) -> Dict:
        """
        Full Approach 2 evaluation: WER + CER.

        Args:
            predictions: Extracted texts from vision.
            references: Ground truth texts.

        Returns:
            Extraction accuracy results.
        """
        results = {
            "approach": "approach_2_vision_extraction",
            "samples": len(predictions)
        }

        accuracy = self.extraction_eval.compute_batch(predictions, references)
        results["extraction_accuracy"] = accuracy

        return results

    def full_evaluation_report(
        self,
        approach1_predictions: Optional[List[str]] = None,
        approach1_references: Optional[List[str]] = None,
        approach2_predictions: Optional[List[str]] = None,
        approach2_references: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate complete evaluation report for the research paper.

        Returns:
            Full evaluation results across all metrics and approaches.
        """
        report = {
            "evaluation_framework": "EduSum Research Evaluation",
            "metrics_used": ["ROUGE-1", "ROUGE-2", "ROUGE-L", "BERTScore F1", "METEOR", "WER", "CER"]
        }

        if approach1_predictions and approach1_references:
            report["approach_1"] = self.evaluate_approach1(
                approach1_predictions, approach1_references
            )

        if approach2_predictions and approach2_references:
            report["approach_2"] = self.evaluate_approach2(
                approach2_predictions, approach2_references
            )

        # Educational utility (human eval)
        utility = self.utility_eval.compute_aggregate()
        if "error" not in utility:
            report["educational_utility"] = utility

        return report
