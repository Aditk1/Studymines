# eduRAG: Complete Experimental Results

**Date**: 2026-04-13
**Experiment Version**: Full Paper Validation (v2)
**Status**: PARTIAL — Custom Educational QA complete; MuSiQue & 2WikiMultiHopQA pending

> Populated from `paper/final_paper_v2.pdf` (Tables II & III, §VI).
> Cells marked **[RUN]** have a command in `experiments/run_commands.md`.
> Cells marked **[MISSING FROM PAPER]** need data that was not reported in the final PDF.

---

## Executive Summary

This document tracks all experimental runs for the eduRAG paper validation across three datasets using six ablation variants. It validates:

- **RQ1**: Does C1 clean up the graph and improve answer quality?
- **RQ2**: Does C2 produce more coherent communities than vanilla Leiden?
- **RQ3**: Does C3 beat fixed-hop traversal on multi-hop educational questions?
- **RQ4**: Does C4 purchase insurance coverage or waste compute?

**Headline numbers (confirmed, from paper §VI):**
- Mean weighted modularity (CW-Leiden, 3 artifacts): **0.9248**
- Mean community coherence: **0.3173**
- Mean triple confidence after C1 filtering: **0.6479**
- Custom Educational QA: ROUGE-L **0.442** (+25.6%), BERTScore F1 **0.912** (+8.3%), METEOR **0.385** (+13.9%)
- SAEOCR v1.2 accuracy: **91.8%** vs Tesseract v5 at **57.5%** (+34.3 pp)

---

## Experimental Configuration

### Common Settings (All Variants)
```yaml
seed: 42
temperature: 0.0
ollama_model: llama3.2:3b
ollama_timeout: 120s
max_tokens: 1024
chunk_size: 200
chunk_overlap: 64
extraction_methods:
  - llm_prompt
  - rebel_large
  - spacy_en_core_web_lg
min_entity_length: 4
confidence_threshold: 0.15
traversal_confidence_threshold: 0.3
max_traversal_steps: 15
step_timeout: 30s
max_parallel_seeds: 5
context_token_limit: 3000
dedup_threshold: 0.92
entity_embedding_model: sentence-transformers/all-MiniLM-L6-v2  # 384-dim, CUDA
vector_store: chromadb
community_resolution: 1.0
community_iterations: 10
```

### Variant Definitions

| Variant | C1 | C2 | C3 | C4 | Description |
|---|---|---|---|---|---|
| **Naive RAG** | ✗ | ✗ | ✗ | ✗ | Dense chunk retrieval, no graph |
| **Standard GraphRAG** | ✗ | Leiden | Fixed-3 | ✗ | Standard graph, no confidence |
| **+C1** | ✓ | Leiden | Fixed-3 | ✗ | Confidence filtering only |
| **+C1+C2** | ✓ | CW-Leiden | Fixed-3 | k≤4 | Confidence in extraction + community |
| **+C1+C2+C3** | ✓ | CW-Leiden | RLM | ✗ | Full adaptive traversal |
| **Full eduRAG** | ✓ | CW-Leiden | RLM | k≤5 | All contributions enabled |

---

## Dataset Specifications

### Dataset 1: Custom Educational QA — STATUS: COMPLETE
- **Composition**: 45% papers, 32% lecture notes, 23% textbooks
- **Topics**: Machine learning, deep learning, NLP
- **Hop Complexity**: 1–3 hops
- **Documents**: 3 verified artifacts (HTML/CSS Guide + 2 image docs)
- **Questions**: [MISSING FROM PAPER — count not reported]

### Dataset 2: MuSiQue [16] — STATUS: PENDING
- **Source**: Wikipedia-based multi-hop QA
- **Questions**: 500
- **Hop Complexity**: 2–4 hops
- **Download**: https://github.com/StonyBrookNLP/musique
- **Run command**: see `experiments/run_commands.md` §2

### Dataset 3: 2WikiMultiHopQA [17] — STATUS: PENDING
- **Source**: Wikipedia paired articles
- **Questions**: 500
- **Hop Complexity**: 2–3 hops
- **Download**: https://github.com/Alab-NII/2wikimultihop
- **Run command**: see `experiments/run_commands.md` §3

---

## Section A: Graph Quality Metrics

### Graph Construction — Custom Educational QA (CONFIRMED, paper Table II)

| Artifact | Nodes | Edges | W. Modularity | Coherence |
|---|---:|---:|---:|---:|
| HTML/CSS Guide | 329 | 235 | 0.9715 | 0.2892 |
| Image Doc (1) | 30 | 16 | 0.9171 | 0.3388 |
| Image Doc (2) | 27 | 16 | 0.8858 | 0.3239 |
| **Mean** | — | — | **0.9248** | **0.3173** |

**Not reported in paper** (need to extract from pipeline logs):
- Triples (Raw) per artifact — **[RUN §4]**
- Triples retained after C1 filter — **[RUN §4]**
- Per-artifact mean confidence — **[RUN §4]**

### Graph Construction — MuSiQue **[RUN §2]**

| Split | Nodes | Edges | Triples Raw | Triples after C1 | Avg Confidence |
|---|---|---|---|---|---|
| Full (500q) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |

### Graph Construction — 2WikiMultiHopQA **[RUN §3]**

| Split | Nodes | Edges | Triples Raw | Triples after C1 | Avg Confidence |
|---|---|---|---|---|---|
| Full (500q) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |

### Community Detection Quality (C2 Validation)

**Custom Educational QA** — paper reports the CW-Leiden row only. Vanilla-Leiden baseline not in final PDF; needed for RQ2.

| Variant | Algorithm | Num Communities | W. Mod. (Qw) | Mean Coher. | Median | Std |
|---|---|---|---|---|---|---|
| Standard GraphRAG | Leiden | [RUN §4] | [RUN §4] | [RUN §4] | [RUN §4] | [RUN §4] |
| +C1+C2 | CW-Leiden | [RUN §4] | 0.9248 | 0.3173 | [RUN §4] | [RUN §4] |
| Full eduRAG | CW-Leiden | [RUN §4] | 0.9248 | 0.3173 | [RUN §4] | [RUN §4] |

**MuSiQue** and **2WikiMultiHopQA**: all cells **[RUN §2, §3]**.

---

## Section B: Answer Quality Metrics

### RQ1 & RQ2 — Effect of C1 on Answer Quality

**Custom Educational QA** (paper Table III, only endpoints reported):

| Variant | ROUGE-L (F1) | BERTScore (F1) | METEOR | Exact Match |
|---|---:|---:|---:|---|
| Naive RAG (baseline) | 0.352 | 0.842 | 0.338 | [MISSING] |
| Standard GraphRAG | [RUN §4] | [RUN §4] | [RUN §4] | [RUN §4] |
| +C1 | [RUN §4] | [RUN §4] | [RUN §4] | [RUN §4] |
| +C1+C2 | [RUN §4] | [RUN §4] | [RUN §4] | [RUN §4] |
| +C1+C2+C3 | [RUN §4] | [RUN §4] | [RUN §4] | [RUN §4] |
| **Full eduRAG** | **0.442** (+25.6%) | **0.912** (+8.3%) | **0.385** (+13.9%) | [RUN §4] |

95% CI: ±0.012 on all three metrics (paper reports single CI for eduRAG row).

**MuSiQue** and **2WikiMultiHopQA**: all cells **[RUN §2, §3]**.

---

### RQ3 — LLM-Guided Traversal (C3) Performance on Multi-Hop

Paper §VII-A claims C3 helps more as hop count grows but does not publish a per-hop breakdown. All cells below require re-running the QA set with hop-labeled splits.

**Custom QA by Hop Complexity** — **[RUN §4 with `--bucket-by-hops`]**

| Hops | Variant | ROUGE-L | BERTScore | METEOR | Avg Depth | Latency (ms) |
|---|---|---|---|---|---|---|
| 1 | Standard GraphRAG (Fixed-3) | [RUN] | [RUN] | [RUN] | 3 | [RUN] |
| 1 | +C1+C2+C3 (RLM) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| 2 | Standard GraphRAG (Fixed-3) | [RUN] | [RUN] | [RUN] | 3 | [RUN] |
| 2 | +C1+C2+C3 (RLM) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| 3 | Standard GraphRAG (Fixed-3) | [RUN] | [RUN] | [RUN] | 3 | [RUN] |
| 3 | +C1+C2+C3 (RLM) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |

**MuSiQue (2/3/4-hop) & 2Wiki (2/3-hop)**: **[RUN §2, §3 with `--bucket-by-hops`]**.

---

### RQ4 — Parallel Multi-Seed Traversal (C4) Impact

Paper §VII-A: "C4 was not as noticeable. Its convergence rule turned out to be a good way to rank evidence almost by chance." Quantitative table not in PDF — reconstruct via ablation.

**Multi-entity questions only** — **[RUN §4 with `--multi-entity-only`]**

| Dataset | Variant | ROUGE-L | BERTScore | METEOR | Latency (ms) | Tokens | Nodes Visited |
|---|---|---|---|---|---|---|---|
| Custom QA | +C1+C2+C3 (C4=off) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| Custom QA | Full eduRAG (C4=on) | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| MuSiQue | +C1+C2+C3 (C4=off) | [RUN §2] | [RUN §2] | [RUN §2] | [RUN §2] | [RUN §2] | [RUN §2] |
| MuSiQue | Full eduRAG (C4=on) | [RUN §2] | [RUN §2] | [RUN §2] | [RUN §2] | [RUN §2] | [RUN §2] |

---

## Section C: Operational Metrics

Paper §VI-D: only qualitative claims ("C3 costs more per query than fixed-hop... worst case 15 steps × 30s"). No numeric table published. All cells **[RUN §4]**.

| Dataset | Variant | Queries | Avg Latency | p50 | p95 | Tokens/Query | Nodes Visited | Max Depth |
|---|---|---|---|---|---|---|---|---|
| Custom QA | Naive RAG | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | N/A |
| Custom QA | Standard GraphRAG | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | 3 |
| Custom QA | +C1 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | 3 |
| Custom QA | +C1+C2 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | 3 |
| Custom QA | +C1+C2+C3 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | ~5 avg |
| Custom QA | Full eduRAG | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] | ~5 avg |

Same table to populate for MuSiQue (500q) and 2Wiki (500q). See `experiments/run_commands.md`.

See `artifacts/plots/latency_scalability.png` for visual.

---

## Section D: Extraction Quality (C1 Impact)

### Confidence Weight Validation

Paper confirms only the aggregate mean (0.6479) and retention band (20–40% filtered). Distribution table = **[RUN §4 with `--dump-confidence-histogram`]**.

| Confidence Range | Raw Count | % Total | After C1 | % Retained | Avg ROUGE when used |
|---|---|---|---|---|---|
| 0.00 – 0.15 | [RUN] | [RUN] | 0 (filtered) | 0% | [RUN] |
| 0.15 – 0.30 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| 0.30 – 0.50 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| 0.50 – 0.70 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| 0.70 – 1.00 | [RUN] | [RUN] | [RUN] | [RUN] | [RUN] |
| **Total** | [RUN] | 100% | [RUN] | 60–80% | [RUN] |

### Extraction Method Comparison (Custom QA) — **[RUN §4]**

| Method | Triple Count | Raw Avg Conf | After C1 Avg | ROUGE-L when used |
|---|---|---|---|---|
| LLM Prompt | [RUN] | [RUN] | [RUN] | [RUN] |
| REBEL-large | [RUN] | [RUN] | [RUN] | [RUN] |
| spaCy en_core_web_lg | [RUN] | [RUN] | [RUN] | [RUN] |

### Confidence Weight Sensitivity — **[RUN §5]**

Paper §VII-B flags this explicitly: "The 0.40/0.35/0.25 weights are based on theory. Never tested against a correct labelled set."

| Config | Factuality | Specificity | Coherence | Retained | Avg Conf | ROUGE-L |
|---|---|---|---|---|---|---|
| Baseline | 0.40 | 0.35 | 0.25 | [RUN] | 0.6479 | 0.442 |
| Variant A | 0.50 | 0.30 | 0.20 | [RUN] | [RUN] | [RUN] |
| Variant B | 0.40 | 0.40 | 0.20 | [RUN] | [RUN] | [RUN] |
| Variant C | 0.30 | 0.35 | 0.35 | [RUN] | [RUN] | [RUN] |
| Variant D (equal) | 0.33 | 0.33 | 0.34 | [RUN] | [RUN] | [RUN] |

---

## Section E: Vision & OCR Performance

**SAEOCR v1.2 vs Tesseract v5** (paper §VI-C — aggregate only)

| Document Type | SAEOCR v1.2 | Tesseract v5 | Δ |
|---|---|---|---|
| Scanned textbooks | [RUN §6] | [RUN §6] | [RUN] |
| Handwritten notes | [RUN §6] | [RUN §6] | [RUN] |
| Annotated PDFs | [RUN §6] | [RUN §6] | [RUN] |
| **Average** | **91.8%** | **57.5%** | **+34.3 pp** |

---

## Section F: User Study Results

**N = 5** (paper §VI-E — flagged as small sample)

| Metric | Mean | Std Dev | 95% CI |
|---|---|---|---|
| Concept Extraction Quality | 4.8 | [MISSING] | [MISSING] |
| Flashcard Utility | 4.7 | [MISSING] | [MISSING] |
| Summarisation Quality | 4.6 | [MISSING] | [MISSING] |
| Exam Relevance | 4.5 | [MISSING] | [MISSING] |
| Graph Coherence | 4.4 | [MISSING] | [MISSING] |
| **Overall** | [MISSING] | [MISSING] | [MISSING] |

Std devs and CIs not in PDF — check original study sheet. Paper limitation §VII-B flags N=5 as under-powered (target N ≥ 20).

Usage patterns (queries/session, session length, % using graph exploration, % reading reasoning paths): **[MISSING FROM PAPER]** — pull from backend logs via `experiments/run_commands.md` §7.

---

## Analysis & Discussion

### RQ1 — Does C1 clean up & improve quality?
**Paper answer (§VII-A):** Partial. C1 alone helps a little but not dramatically on community coherence. The real gain comes from C1+C2 together.
**Gap:** per-variant ROUGE-L delta not published — **[RUN §4]** to isolate C1's independent contribution.

### RQ2 — Does C2 produce more coherent communities?
**Paper answer:** Yes for weighted modularity (0.9248) and coherence (0.3173) on CW-Leiden.
**Gap:** Vanilla-Leiden baseline numbers missing — **[RUN §4]** to get the comparison pair.

### RQ3 — Does C3 beat fixed-hop on multi-hop?
**Paper answer:** Yes, especially on harder questions with layered sub-questions. Fixed-hop adequate for simple queries.
**Gap:** No per-hop breakdown published — **[RUN §4, §2, §3 with --bucket-by-hops]**.

### RQ4 — Does C4 buy coverage without wasting compute?
**Paper answer:** Marginal. Convergence rule useful for evidence ranking; latency cost is real but capped by parallel execution.
**Gap:** No numeric table — **[RUN §4 with --multi-entity-only]**.

### Ablation Summary Table — **[RUN §4]**

| Contribution | ROUGE-L Gain | Latency Add (ms) | Modularity Gain | Recommendation |
|---|---|---|---|---|
| C1 (Confidence Filter) | [RUN] | [RUN] | [RUN] | [RUN] |
| C2 (CW-Leiden) | [RUN] | [RUN] | [RUN] | [RUN] |
| C3 (RLM Traversal) | [RUN] | [RUN] | — | [RUN] |
| C4 (Multi-Seed) | [RUN] | [RUN] | — | [RUN] |

---

## Scaling Assessment

Paper §VII-B: "Our largest checked graph has 329 parts. Anything we say about scaling across the data set is just a guess."

| Metric | Best Observed | Projected to 10K Nodes | Notes |
|---|---|---|---|
| Modularity Stability | 0.9248 | [SPECULATIVE] | Need MuSiQue/2Wiki to validate |
| Community Count Growth | [RUN §4] | [RUN §2, §3] | — |
| Query Latency | [RUN §4] | [RUN §2, §3] | Bounded by 15-step × 30s cap |
| Nodes Visited per Query | [RUN §4] | [RUN §2, §3] | — |

---

## Limitations (from paper §VII-B + gaps we uncovered)

- [x] Confidence weights not empirically validated (0.40/0.35/0.25 theoretical)
- [x] Largest graph only 329 nodes — scaling claims are conjecture
- [x] User study N=5 — not statistically powered
- [x] Only llama3.2:3b tested — no GPT-4/Claude/Gemini A/B
- [x] No direct comparison to Microsoft GraphRAG or Tan et al. [7]
- [ ] Confidence rules may not transfer to legal/general domains
- [ ] Per-hop breakdowns absent from published results
- [ ] Vanilla-Leiden comparison rows missing (needed for RQ2 claim)
- [ ] C4 claims ("coverage without waste") lack numeric backing

---

## Reproducibility

**Paper run:**
- Date: (paper published 2026)
- Model: `ollama/llama3.2:3b`
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (CUDA)
- Community: `leidenalg`, resolution=1.0, seed=42, 10 iterations
- Store: ChromaDB

**This rerun:**
- Date: 2026-04-13
- System: Windows OS x64
- Python: 3.13.1
- Commit: c40614f2bb7863a512fcc2487e0b4f3f5c921bde
- Key Core Dependencies: networkx>=3.2.0, leidenalg>=0.10.0, chromadb>=0.4.24, ollama>=0.1.8
- Logs: `artifacts/logs/`
- Audits: `artifacts/audits/`
- Plots: `artifacts/plots/`

---

## Next Steps

- [ ] Run MuSiQue (§2) on autopilot
- [ ] Run 2WikiMultiHopQA (§3) on autopilot
- [ ] Run Custom QA full-ablation (§4) to fill intermediate variant rows
- [ ] Run confidence weight sensitivity (§5)
- [ ] Re-run OCR breakdown by doc type (§6)
- [ ] Pull user-study usage metrics from backend logs (§7)
- [ ] Expand user study to N ≥ 20
- [ ] Add GPT-4 / Claude Opus 4.6 / Gemini 2.5 LLM sweep
- [ ] Direct comparison to Microsoft GraphRAG and AdaptiveRAG [16]

---

**Last Updated**: 2026-04-13
