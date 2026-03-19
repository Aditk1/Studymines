"""
Unit tests for EduSum evaluation module.
Tests ROUGE, BERTScore, WER, CER, Educational Utility Score, and comparison utilities.
"""

import pytest
import json
import tempfile
import os

from app.evaluation import (
    RougeEvaluator,
    BERTScoreEvaluator,
    ExtractionAccuracyEvaluator,
    EducationalUtilityEvaluator,
    TesseractBaseline,
    EvaluationRunner,
)


class TestExtractionAccuracyEvaluator:
    """Test WER and CER computation (no external deps needed)."""

    def setup_method(self):
        self.evaluator = ExtractionAccuracyEvaluator()

    # --- WER ---

    def test_wer_identical(self):
        wer = self.evaluator.compute_wer("hello world", "hello world")
        assert wer == 0.0

    def test_wer_completely_wrong(self):
        wer = self.evaluator.compute_wer("foo bar", "hello world")
        assert wer == 1.0  # 2 substitutions / 2 words

    def test_wer_partial_match(self):
        wer = self.evaluator.compute_wer("hello there", "hello world")
        assert 0.0 < wer < 1.0

    def test_wer_empty_reference(self):
        wer = self.evaluator.compute_wer("hello", "")
        assert wer == 1.0

    def test_wer_both_empty(self):
        wer = self.evaluator.compute_wer("", "")
        assert wer == 0.0

    def test_wer_empty_prediction(self):
        wer = self.evaluator.compute_wer("", "hello world")
        assert wer == 1.0

    def test_wer_case_insensitive(self):
        wer = self.evaluator.compute_wer("HELLO WORLD", "hello world")
        assert wer == 0.0

    def test_wer_insertion(self):
        # Reference: "a b", Prediction: "a c b" → 1 insertion / 2 words = 0.5
        wer = self.evaluator.compute_wer("a c b", "a b")
        assert wer == 0.5

    # --- CER ---

    def test_cer_identical(self):
        cer = self.evaluator.compute_cer("hello", "hello")
        assert cer == 0.0

    def test_cer_one_char_diff(self):
        cer = self.evaluator.compute_cer("hallo", "hello")
        assert cer == pytest.approx(0.2, abs=0.01)  # 1/5

    def test_cer_empty_reference(self):
        cer = self.evaluator.compute_cer("hello", "")
        assert cer == 1.0

    def test_cer_both_empty(self):
        cer = self.evaluator.compute_cer("", "")
        assert cer == 0.0

    def test_cer_case_insensitive(self):
        cer = self.evaluator.compute_cer("HELLO", "hello")
        assert cer == 0.0

    # --- Batch ---

    def test_compute_batch(self):
        preds = ["hello world", "foo bar"]
        refs = ["hello world", "foo baz"]
        result = self.evaluator.compute_batch(preds, refs)
        assert "avg_wer" in result
        assert "avg_cer" in result
        assert result["samples"] == 2
        assert result["avg_wer"] >= 0.0

    def test_compute_batch_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            self.evaluator.compute_batch(["a"], ["a", "b"])


class TestEducationalUtilityEvaluator:
    """Test the human evaluation framework."""

    def setup_method(self):
        self.evaluator = EducationalUtilityEvaluator()

    def test_add_valid_rating(self):
        rating = self.evaluator.add_rating(
            evaluator_id="eval_001",
            document_id="doc_001",
            accuracy=4,
            clarity=5,
            completeness=4,
            educational_utility=5
        )
        assert rating["accuracy"] == 4
        assert rating["clarity"] == 5
        assert len(self.evaluator.ratings) == 1

    def test_add_rating_invalid_score(self):
        with pytest.raises(ValueError, match="between 1 and 5"):
            self.evaluator.add_rating(
                evaluator_id="eval_001",
                document_id="doc_001",
                accuracy=0,  # Invalid
                clarity=5,
                completeness=4,
                educational_utility=5
            )

    def test_add_rating_too_high(self):
        with pytest.raises(ValueError, match="between 1 and 5"):
            self.evaluator.add_rating(
                evaluator_id="eval_001",
                document_id="doc_001",
                accuracy=6,  # Invalid
                clarity=5,
                completeness=4,
                educational_utility=5
            )

    def test_compute_aggregate_empty(self):
        result = self.evaluator.compute_aggregate()
        assert "error" in result

    def test_compute_aggregate_single_rating(self):
        self.evaluator.add_rating("e1", "d1", 4, 5, 4, 5)
        result = self.evaluator.compute_aggregate()
        assert result["total_ratings"] == 1
        assert result["overall_score"] == 4.5  # (4+5+4+5)/4

    def test_compute_aggregate_multiple_ratings(self):
        self.evaluator.add_rating("e1", "d1", 4, 4, 4, 4)
        self.evaluator.add_rating("e2", "d1", 5, 5, 5, 5)
        result = self.evaluator.compute_aggregate()
        assert result["total_ratings"] == 2
        assert result["unique_evaluators"] == 2
        assert result["overall_score"] == 4.5  # avg of (4,4,4,4) and (5,5,5,5)

    def test_meets_target(self):
        # All 5s should meet the 4.2 target
        self.evaluator.add_rating("e1", "d1", 5, 5, 5, 5)
        result = self.evaluator.compute_aggregate()
        assert result["meets_target"] is True

    def test_below_target(self):
        # All 3s should not meet 4.2 target
        self.evaluator.add_rating("e1", "d1", 3, 3, 3, 3)
        result = self.evaluator.compute_aggregate()
        assert result["meets_target"] is False

    def test_export_and_load_ratings(self):
        self.evaluator.add_rating("e1", "d1", 4, 5, 4, 5)
        self.evaluator.add_rating("e2", "d2", 3, 4, 3, 4)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            tmp_path = f.name

        try:
            self.evaluator.export_ratings(tmp_path)

            # Load into new evaluator
            new_eval = EducationalUtilityEvaluator()
            new_eval.load_ratings(tmp_path)
            assert len(new_eval.ratings) == 2
            assert new_eval.ratings[0]["accuracy"] == 4
        finally:
            os.unlink(tmp_path)


class TestRougeEvaluator:
    """Test ROUGE evaluator (requires 'evaluate' and 'rouge-score' packages)."""

    def setup_method(self):
        self.evaluator = RougeEvaluator()

    @pytest.mark.skipif(
        not RougeEvaluator().available,
        reason="ROUGE evaluator not available (install: pip install evaluate rouge-score)"
    )
    def test_rouge_identical_texts(self):
        result = self.evaluator.compute_single(
            "The cat sat on the mat",
            "The cat sat on the mat"
        )
        assert result["rouge1"] == 1.0
        assert result["rouge2"] == 1.0
        assert result["rougeL"] == 1.0

    @pytest.mark.skipif(
        not RougeEvaluator().available,
        reason="ROUGE evaluator not available"
    )
    def test_rouge_different_texts(self):
        result = self.evaluator.compute_single(
            "The dog ran in the park",
            "The cat sat on the mat"
        )
        assert result["rouge1"] < 1.0
        assert result["rouge1"] > 0.0  # "The" is shared

    @pytest.mark.skipif(
        not RougeEvaluator().available,
        reason="ROUGE evaluator not available"
    )
    def test_rouge_batch(self):
        result = self.evaluator.compute(
            ["Hello world", "Goodbye world"],
            ["Hello world", "Farewell world"]
        )
        assert "rouge1" in result
        assert "rouge2" in result
        assert "rougeL" in result


class TestEvaluationRunner:
    """Test the evaluation orchestrator."""

    def test_runner_initializes(self):
        runner = EvaluationRunner()
        assert runner.rouge_eval is not None
        assert runner.extraction_eval is not None
        assert runner.utility_eval is not None

    def test_evaluate_approach2(self):
        runner = EvaluationRunner()
        result = runner.evaluate_approach2(
            predictions=["hello world test", "foo bar baz"],
            references=["hello world test", "foo bar qux"]
        )
        assert result["approach"] == "approach_2_vision_extraction"
        assert result["samples"] == 2
        assert "extraction_accuracy" in result
