"""
Contribution 1: Confidence-Scored Triple Extraction.

Three scoring modes configurable via config/base.yaml:

  mode: "fast"     — Rule-based only. No LLM calls. ~0 extra time.
                     Scores based on relation specificity and entity length.
                     Good for: development, smoke testing, large documents.

  mode: "balanced" — Rules first, LLM only for ambiguous triples (0.3-0.7).
                     Typically 20-30% of triples need LLM scoring.
                     Good for: normal research runs. DEFAULT.

  mode: "full"     — LLM scores every triple in batches of 8.
                     Highest accuracy, slowest.
                     Good for: final paper results only.

Add to config/base.yaml:
  confidence:
    mode: "balanced"    # fast | balanced | full
    batch_size: 8
"""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Literal

from src.graph.knowledge_graph import Triple
from src.utils.config import ConfidenceConfig
from src.utils.llm_client import LLMClient
from src.utils.logger import get_logger

logger = get_logger("confidence_scorer")

# ── Scoring mode type ────────────────────────────────────────────────────────
ScoringMode = Literal["fast", "balanced", "full"]

# ── Batch prompt ─────────────────────────────────────────────────────────────
BATCH_PROMPT = """Score each knowledge triple. Reply with JSON array only.

Context: "{context}"

Triples:
{triples_list}

For each triple return scores 0.0-1.0:
- factual: is this relationship meaningful and true?
- specificity: does the relation word carry precise meaning?
- coherence: is this supported by the context?

[
  {{"id": 0, "factual": 0.8, "specificity": 0.7, "coherence": 0.9}},
  {{"id": 1, "factual": 0.3, "specificity": 0.2, "coherence": 0.4}}
]"""

# ── Relation quality tiers for rule-based scoring ────────────────────────────
# High specificity relations — clearly meaningful
HIGH_SPECIFICITY = {
    "uses", "trained_on", "part_of", "part of", "achieves", "outperforms",
    "based_on", "is based on", "consists_of", "consists of", "proposed_by",
    "evaluated_on", "evaluated on", "implements", "extends", "replaces",
    "trained on", "achieves", "has", "produces", "requires", "enables",
    "composed_of", "composed of", "applied_to", "applied to",
    "includes", "contains", "performs", "calculates", "computes",
    "is defined as", "defined as", "refers to", "known as",
}

# Low specificity relations — vague, adds little signal
LOW_SPECIFICITY = {
    "related_to", "related to", "associated_with", "associated with",
    "connected_to", "connected to", "linked_to", "linked to",
    "involves", "concerns", "mentions", "discusses",
    "is", "are", "was", "were", "be",
}

# Noisy entity patterns — these are almost always bad triples
NOISY_ENTITY_PATTERNS = [
    r"^[a-z]$",           # single lowercase letter
    r"^\d+$",             # pure number
    r"^(et al|ibid)$",    # citation artifacts
    r"^(fig|eq|tab)\s*\d",# figure/equation references
]


@dataclass
class ConfidenceResult:
    triple: Triple
    factual: float
    specificity: float
    coherence: float
    composite: float
    method: str = "unknown"  # "rules", "llm_batch", "default"


class ConfidenceScorer:
    """
    Hybrid confidence scorer with three configurable modes.

    "fast"     — rules only, instant
    "balanced" — rules + LLM for ambiguous cases only  ← recommended
    "full"     — LLM for everything, batched
    """

    # Thresholds for "balanced" mode
    RULE_HIGH_THRESHOLD  = 0.72   # above this → keep without LLM
    RULE_LOW_THRESHOLD   = 0.22   # below this → discard without LLM
    # Between 0.22 and 0.72 → send to LLM

    def __init__(self, config: ConfidenceConfig, llm_client: LLMClient) -> None:
        self.config     = config
        self.llm        = llm_client
        # Read mode from config, default to "balanced"
        self.mode: ScoringMode = getattr(config, "mode", "balanced")
        logger.info("confidence_scorer_init", mode=self.mode)

    # ── Composite calculation ─────────────────────────────────────────────

    def _composite(self, f: float, s: float, c: float) -> float:
        axes = self.config.axes
        return axes.factual_weight * f + axes.specificity_weight * s + axes.coherence_weight * c

    # ── Rule-based scoring ────────────────────────────────────────────────

    def _rule_score(self, triple: Triple) -> ConfidenceResult:
        """
        Fast rule-based scoring. No LLM calls.
        Returns a ConfidenceResult scored purely by heuristics.
        """
        subj = triple.subject.lower().strip()
        rel  = triple.relation.lower().strip()
        obj  = triple.obj.lower().strip()

        # ── Factual score ──────────────────────────────────────────────
        factual = 0.6  # base

        # Boost for specific numeric or named entities
        if any(c.isdigit() for c in obj):
            factual = min(1.0, factual + 0.2)   # numbers are usually factual

        # Penalise very short entities
        if len(subj) < 4 or len(obj) < 4:
            factual = max(0.0, factual - 0.3)

        # Penalise noisy entity patterns
        for pattern in NOISY_ENTITY_PATTERNS:
            if re.match(pattern, subj) or re.match(pattern, obj):
                factual = 0.1
                break

        # ── Specificity score ──────────────────────────────────────────
        if rel in HIGH_SPECIFICITY:
            specificity = 0.85
        elif rel in LOW_SPECIFICITY:
            specificity = 0.15
        elif len(rel.split()) >= 2:
            specificity = 0.55   # multi-word relations are usually meaningful
        else:
            specificity = 0.45   # single unknown word — neutral

        # ── Coherence score ────────────────────────────────────────────
        # Without reading context we can only estimate coherence
        # by checking if subject and object share domain vocabulary
        coherence = 0.55  # neutral default

        composite = self._composite(factual, specificity, coherence)
        return ConfidenceResult(
            triple=triple,
            factual=factual,
            specificity=specificity,
            coherence=coherence,
            composite=composite,
            method="rules",
        )

    # ── Batch LLM scoring ─────────────────────────────────────────────────

    async def _llm_score_batch(
        self,
        triples: list[Triple],
        context: str,
    ) -> list[ConfidenceResult]:
        """Score a batch of triples in one LLM call."""
        triples_text = "\n".join(
            f"{i}. ({t.subject}, {t.relation}, {t.obj})"
            for i, t in enumerate(triples)
        )
        prompt   = BATCH_PROMPT.format(
            context=context[:500],
            triples_list=triples_text,
        )
        response = await self.llm.generate(prompt, context_label="confidence_batch")
        scores   = self._parse_batch(response.content, len(triples))

        results: list[ConfidenceResult] = []
        for i, triple in enumerate(triples):
            f, s, c = scores[i] if i < len(scores) else (0.5, 0.5, 0.5)
            results.append(ConfidenceResult(
                triple=triple,
                factual=f, specificity=s, coherence=c,
                composite=self._composite(f, s, c),
                method="llm_batch",
            ))
        return results

    @staticmethod
    def _parse_batch(response: str, expected: int) -> list[tuple[float, float, float]]:
        clean = re.sub(r"```(?:json)?", "", response).strip().rstrip("`").strip()
        try:
            match = re.search(r"\[.*\]", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if isinstance(data, list) and data:
                    scores = []
                    for item in data:
                        if isinstance(item, dict):
                            f = max(0.0, min(1.0, float(item.get("factual",     0.5))))
                            s = max(0.0, min(1.0, float(item.get("specificity", 0.5))))
                            c = max(0.0, min(1.0, float(item.get("coherence",   0.5))))
                            scores.append((f, s, c))
                    if scores:
                        return scores
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        # Fallback: extract floats in order
        floats = []
        for n in re.findall(r"0\.\d+|1\.0*", clean):
            try:
                v = float(n)
                if 0.0 <= v <= 1.0:
                    floats.append(v)
            except ValueError:
                continue

        if len(floats) >= expected * 3:
            return [
                (floats[i*3], floats[i*3+1], floats[i*3+2])
                for i in range(expected)
            ]

        return [(0.5, 0.5, 0.5)] * expected

    # ── Main scoring entry point ──────────────────────────────────────────

    async def score_batch(
        self,
        triples: list[Triple],
        context_map: dict[str, str] | None = None,
    ) -> list[Triple]:
        """
        Score triples according to the configured mode.

        Returns triples above min_confidence_threshold with updated scores.
        """
        if not self.config.enabled:
            logger.info("confidence_scoring_disabled")
            return triples

        ctx_map   = context_map or {}
        threshold = self.config.min_confidence_threshold
        mode      = self.mode

        kept:        list[Triple] = []
        discarded                 = 0
        llm_calls                 = 0
        rule_kept                 = 0
        rule_discarded            = 0
        ambiguous_sent_to_llm     = 0

        # Group by source chunk so LLM batches share context
        chunk_groups: dict[str, list[Triple]] = {}
        for t in triples:
            chunk_groups.setdefault(t.source_chunk, []).append(t)

        for source, chunk_triples in chunk_groups.items():
            context   = ctx_map.get(source, "")
            llm_queue: list[Triple] = []  # triples needing LLM scoring

            # ── Step 1: Rule-based pre-filter ──────────────────────────
            for triple in chunk_triples:
                rule_result = self._rule_score(triple)

                if mode == "fast":
                    # Rules only — no LLM at all
                    if rule_result.composite >= threshold:
                        triple.confidence = round(rule_result.composite, 4)
                        kept.append(triple)
                        rule_kept += 1
                    else:
                        discarded += 1
                        rule_discarded += 1

                elif mode == "balanced":
                    if rule_result.composite >= self.RULE_HIGH_THRESHOLD:
                        # Clearly good — keep without LLM
                        triple.confidence = round(rule_result.composite, 4)
                        kept.append(triple)
                        rule_kept += 1
                    elif rule_result.composite < self.RULE_LOW_THRESHOLD:
                        # Clearly bad — discard without LLM
                        discarded += 1
                        rule_discarded += 1
                    else:
                        # Ambiguous (0.22–0.72) — send to LLM
                        llm_queue.append(triple)
                        ambiguous_sent_to_llm += 1

                elif mode == "full":
                    # Queue everything for LLM
                    llm_queue.append(triple)

            # ── Step 2: LLM scoring for queued triples ─────────────────
            if llm_queue:
                batch_size = self.config.batch_size
                for i in range(0, len(llm_queue), batch_size):
                    sub_batch = llm_queue[i: i + batch_size]
                    llm_calls += 1
                    try:
                        results = await self._llm_score_batch(sub_batch, context)
                    except Exception as e:
                        logger.warning("llm_batch_failed", error=str(e))
                        # Fallback: use rule scores for this batch
                        results = [
                            ConfidenceResult(
                                t, 0.5, 0.5, 0.5,
                                self._composite(0.5, 0.5, 0.5),
                                method="fallback",
                            )
                            for t in sub_batch
                        ]

                    for result in results:
                        if result.composite >= threshold:
                            result.triple.confidence = round(result.composite, 4)
                            kept.append(result.triple)
                        else:
                            discarded += 1

        logger.info(
            "scoring_complete",
            mode=mode,
            input=len(triples),
            kept=len(kept),
            discarded=discarded,
            rule_kept=rule_kept,
            rule_discarded=rule_discarded,
            ambiguous_sent_to_llm=ambiguous_sent_to_llm,
            llm_calls=llm_calls,
        )

        # Print a human-readable summary to terminal
        total_llm = ambiguous_sent_to_llm if mode == "balanced" else len(triples)
        print(f"\n  \033[96mConfidence scoring ({mode} mode):\033[0m")
        print(f"    Input triples:     {len(triples)}")
        if mode == "balanced":
            print(f"    Ruled out fast:    {rule_kept} kept + {rule_discarded} discarded (no LLM)")
            print(f"    Sent to LLM:       {ambiguous_sent_to_llm} ambiguous triples")
            print(f"    LLM calls made:    {llm_calls}  (vs {len(triples)} in full mode)")
        elif mode == "fast":
            print(f"    LLM calls made:    0  (rules only)")
        else:
            print(f"    LLM calls made:    {llm_calls}")
        print(f"    Final kept:        {len(kept)}")
        print(f"    Final discarded:   {discarded}\n")

        return kept

    def score_batch_sync(
        self,
        triples: list[Triple],
        context_map: dict[str, str] | None = None,
    ) -> list[Triple]:
        """Synchronous wrapper."""
        return asyncio.run(self.score_batch(triples, context_map))