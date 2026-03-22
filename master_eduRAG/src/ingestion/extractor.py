"""
Entity and Relation Extraction.

Three extractors available (set via config.ingestion.extractor):
  1. "rebel"  — REBEL seq2seq model. Best for encyclopedic/Wikipedia-style text.
                 Struggles with technical ML papers.
  2. "llm"    — LLM-based extraction via Ollama. Best for technical documents,
                 academic papers, domain-specific content. Uses the same LLM
                 as the rest of the pipeline.
  3. "spacy"  — Dependency parsing fallback. Lightweight, no GPU needed.

Recommendation:
  - Academic ML papers    → use "llm"
  - News / Wikipedia text → use "rebel"
  - Quick testing         → use "spacy"
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from src.graph.knowledge_graph import Triple
from src.ingestion.loader import DocumentChunk
from src.utils.config import IngestionConfig
from src.utils.logger import get_logger

logger = get_logger("extractor")


# ── LLM Extraction Prompt ────────────────────────────────────────────────────

LLM_EXTRACTION_PROMPT = """Extract knowledge triples from the text below.
A triple is: (subject, relation, object)

Rules:
- Subject and object must be specific named concepts, not pronouns or generic words
- Never use "we", "they", "it", "this", "that" as subject or object
- Relation must describe a real relationship
- Include specific numerical facts: layer counts, scores, hyperparameters
- Examples of good triples:
    (transformer, uses, multi-head attention)
    (base model, has, 6 encoder layers)
    (adam optimizer, uses, beta1 = 0.9)
    (transformer big, achieves, bleu 41.0 on wmt2014 en-de)

Text:
{text}

Return JSON array only:
[
  {{"subject": "...", "relation": "...", "object": "..."}}
]

Extract up to {max_triples} triples:"""


class LLMExtractor:
    """
    LLM-based triple extraction.
    Works well for technical documents, academic papers, domain-specific text.
    Uses the same Ollama/OpenAI/Anthropic backend as the rest of the pipeline.
    """

    def __init__(self, config: IngestionConfig) -> None:
        self.config = config
        self._llm: Any = None

    def _get_llm(self) -> Any:
        """Lazy-load LLM client."""
        if self._llm is None:
            from src.utils.llm_client import LLMClient
            from src.utils.config import LLMConfig
            # Use default LLM config — extractor shares the same backend
            llm_config = LLMConfig()
            self._llm = LLMClient(llm_config)
        return self._llm

    async def extract_from_text(self, text: str) -> list[tuple[str, str, str]]:
        """Extract triples from text using LLM."""
        llm = self._get_llm()
        prompt = LLM_EXTRACTION_PROMPT.format(
            text=text[:1500],  # keep within context
            max_triples=self.config.max_triples_per_chunk,
        )
        try:
            response = await llm.generate(prompt, context_label="llm_extraction")
            return self._parse_triples(response.content)
        except Exception as e:
            logger.warning("llm_extraction_failed", error=str(e))
            return []

    @staticmethod
    def _parse_triples(response: str) -> list[tuple[str, str, str]]:
        """Parse JSON array of triples from LLM response."""
        clean = re.sub(r"```(?:json)?", "", response).strip().rstrip("`").strip()
        try:
            match = re.search(r"\[.*\]", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
                triples = []
                for item in data:
                    if isinstance(item, dict):
                        s = str(item.get("subject", "")).strip()
                        r = str(item.get("relation", "")).strip()
                        o = str(item.get("object", "")).strip()
                        if s and r and o and s.lower() != o.lower():
                            triples.append((s, r, o))
                return triples
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("llm_triple_parse_failed", error=str(e))

        # Fallback: look for (subject, relation, object) patterns
        pattern = r'\("?([^",]+)"?,\s*"?([^",]+)"?,\s*"?([^")]+)"?\)'
        matches = re.findall(pattern, clean)
        return [(s.strip(), r.strip(), o.strip()) for s, r, o in matches if s and r and o]


class REBELExtractor:
    """
    REBEL-based relation extraction.
    Best for encyclopedic/Wikipedia-style text with named real-world entities.
    Not recommended for technical ML papers.
    """

    def __init__(self, config: IngestionConfig) -> None:
        self.config = config
        self._tokenizer: Any = None
        self._model: Any = None
        self._device: str = self._resolve_device(config.rebel_device)

    @staticmethod
    def _resolve_device(device: str) -> str:
        try:
            import torch
            if device == "cuda" and torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _load(self) -> None:
        if self._model is None:
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(self.config.rebel_model)
                self._model = AutoModelForSeq2SeqLM.from_pretrained(self.config.rebel_model)
                self._model.to(self._device)
                self._model.eval()
                logger.info("rebel_loaded", model=self.config.rebel_model, device=self._device)
            except Exception as e:
                logger.error("rebel_load_failed", error=str(e))
                raise

    async def extract_from_text(self, text: str) -> list[tuple[str, str, str]]:
        self._load()
        try:
            import torch
            inputs = self._tokenizer(
                text, return_tensors="pt",
                max_length=512, truncation=True, padding=True,
            ).to(self._device)
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs, max_length=512, num_beams=3, early_stopping=True,
                )
            decoded = self._tokenizer.batch_decode(outputs, skip_special_tokens=False)
            triples = []
            for seq in decoded:
                triples.extend(self._parse_rebel_output(seq))
            return triples[: self.config.max_triples_per_chunk]
        except Exception as e:
            logger.warning("rebel_extraction_failed", error=str(e))
            return []

    @staticmethod
    def _parse_rebel_output(text: str) -> list[tuple[str, str, str]]:
        triples = []
        import re
        parts = text.split("<triplet>")
        for part in parts[1:]:
            try:
                subj_match = re.search(r"^(.*?)<subj>", part)
                rel_match  = re.search(r"<subj>(.*?)<obj>",  part)
                obj_match  = re.search(r"<obj>(.*?)(?:<|$)", part)
                if subj_match and rel_match and obj_match:
                    s = subj_match.group(1).strip()
                    r = rel_match.group(1).strip()
                    o = obj_match.group(1).strip()
                    if s and o:
                        triples.append((s, r or "related_to", o))
            except Exception:
                continue
        return triples


class SpaCyExtractor:
    """spaCy dependency parsing fallback."""

    def __init__(self, model_name: str = "en_core_web_lg") -> None:
        self.model_name = model_name
        self._nlp: Any = None

    def _load(self) -> None:
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load(self.model_name)
                logger.info("spacy_loaded", model=self.model_name)
            except OSError:
                import spacy
                self._nlp = spacy.blank("en")
                logger.warning("spacy_model_missing",
                               fix=f"python -m spacy download {self.model_name}")

    async def extract_from_text(self, text: str) -> list[tuple[str, str, str]]:
        self._load()
        doc = self._nlp(text)
        triples = []
        for sent in doc.sents:
            for token in sent:
                if token.dep_ == "ROOT" and token.pos_ == "VERB":
                    subjects = [c for c in token.children if c.dep_ in ("nsubj", "nsubjpass")]
                    objects  = [c for c in token.children if c.dep_ in ("dobj", "pobj", "attr")]
                    for subj in subjects:
                        for obj in objects:
                            triples.append((subj.text, token.lemma_, obj.text))
        return triples


class TripleExtractor:
    """
    Unified extractor. Selects backend based on config.ingestion.extractor.

    "llm"   → LLMExtractor   (best for technical/academic documents)
    "rebel" → REBELExtractor  (best for encyclopedic/Wikipedia text)
    "spacy" → SpaCyExtractor  (lightweight fallback)
    """

    def __init__(self, config: IngestionConfig) -> None:
        self.config = config
        extractor_type = config.extractor

        if extractor_type == "llm":
            self._extractor: Any = LLMExtractor(config)
            logger.info("extractor_selected", type="llm",
                        note="Good for technical/academic documents")
        elif extractor_type == "rebel":
            self._extractor = REBELExtractor(config)
            logger.info("extractor_selected", type="rebel",
                        note="Good for encyclopedic/Wikipedia text")
        else:
            self._extractor = SpaCyExtractor(config.spacy_model)
            logger.info("extractor_selected", type="spacy")

        # Always keep spaCy as fallback
        self._spacy_fallback = SpaCyExtractor(config.spacy_model)

    async def extract_from_chunk(self, chunk: DocumentChunk) -> list[Triple]:
        raw: list[tuple[str, str, str]] = []

        try:
            raw = await self._extractor.extract_from_text(chunk.text)
        except Exception as e:
            logger.warning("primary_extractor_failed", error=str(e),
                           falling_back="spacy")

        # Fallback to spaCy if primary returned nothing
        if not raw:
            raw = await self._spacy_fallback.extract_from_text(chunk.text)

        triples: list[Triple] = []
        for subj, rel, obj in raw:
            subj = subj.strip()
            obj  = obj.strip()
            if (
                len(subj) >= self.config.min_entity_length
                and len(obj)  >= self.config.min_entity_length
                and subj.lower() != obj.lower()
            ):
                triples.append(Triple(
                    subject=subj,
                    relation=rel.strip() or "related_to",
                    obj=obj,
                    confidence=1.0,
                    source_chunk=chunk.source,
                ))

        logger.debug("chunk_extracted",
                     source=chunk.source,
                     chunk_idx=chunk.chunk_idx,
                     num_triples=len(triples))
        return triples

    async def extract_from_chunks(self, chunks: list[DocumentChunk]) -> list[Triple]:
        all_triples: list[Triple] = []
        for chunk in chunks:
            all_triples.extend(await self.extract_from_chunk(chunk))
        logger.info("extraction_complete",
                    total_triples=len(all_triples),
                    num_chunks=len(chunks))
        return all_triples
