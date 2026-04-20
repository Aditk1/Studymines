# Task 1 — Blueprint → Real Codebase Mapping

**Generated:** 2026-04-13  
**Commit:** c40614f2bb7863a512fcc2487e0b4f3f5c921bde  
**Repo root (`$EDURAG_HOME`):** `d:\projects\eduRAG\master_eduRAG`

---

## Mapping Table

| Blueprint (`run_commands.md`) | Real Codebase | Status | Action needed |
|---|---|---|---|
| `scripts.run_experiment` (singular) | `scripts/run_experiments.py` (plural) | **rename** | Invoke as `python scripts/run_experiment.py` (new thin wrapper — see §Patches below) |
| `configs/sanity.yaml` | `config/sanity.yaml` | **missing** — config dir is `config/`, not `configs/` | **Created** at `config/sanity.yaml` (see §Patches) |
| `configs/base.yaml` | `config/base.yaml` | **rename** | Invoke with `--config config/base.yaml` |
| `configs/${VARIANT}.yaml` | `config/variants/<mapped>.yaml` | **rename + remap** | See variant name table below |
| `configs/weights_*.yaml` | `config/variants/weights_*.yaml` | **missing** | **Created** 5 weight config files (see §Patches) |
| `--bucket-by-hops` flag | `scripts/run_experiment.py` | **absent** | **Implemented** — post-processes QA results by hop label (see §Patches) |
| `--multi-entity-only` flag | `scripts/run_experiment.py` | **absent** | **Implemented** — filters results to questions with >1 entity seed (see §Patches) |
| `--multi-entity-tag` flag | `scripts/run_experiment.py` | **absent** | **Implemented** — alias of `--multi-entity-only`; retained same semantics per blueprint §4 |
| `--dump-confidence-histogram` flag | `scripts/build_graph.py` | **absent** | **Implemented** in `scripts/build_graph.py` — emits histogram JSON after ingestion (see §Patches) |
| `--dump-per-method-stats` flag | `scripts/build_graph.py` | **absent** | **Implemented** in `scripts/build_graph.py` (see §Patches) |
| `--log-operational-metrics` flag | `scripts/run_experiment.py` | **absent** | **Implemented** — records latency, tokens, nodes-visited per query (see §Patches) |
| `--confidence-on` flag | `scripts/build_graph.py` | **absent** | **Implemented** — overrides `confidence.enabled=true` at runtime |
| `--emit-markdown` flag | `scripts/aggregate_results.py` | **absent** | **Implemented** (see §Patches) |
| `--emit-ablation-table` flag | `scripts/aggregate_results.py` | **absent** | **Implemented** (see §Patches) |
| `scripts.build_graph` | **missing** | **absent** | **Created** `scripts/build_graph.py` (see §Patches) |
| `scripts.community_ab` | **missing** | **absent** | **Created** `scripts/community_ab.py` (see §Patches) |
| `scripts.aggregate_results` | **missing** | **absent** | **Created** `scripts/aggregate_results.py` (see §Patches) |
| `scripts.aggregate_weights` | **missing** | **absent** | **Created** `scripts/aggregate_weights.py` (see §Patches) |
| `scripts.ocr_benchmark` | **missing** | **absent** | **Created** `scripts/ocr_benchmark.py` stub (see §Patches) |
| `scripts.parse_user_study` | **missing** | **absent** | **Created** `scripts/parse_user_study.py` stub (see §Patches) |
| `scripts.populate_workbook` | **missing** | **absent** | **Created** `scripts/populate_workbook.py` (see §Patches) |
| `scripts.download_dataset` | **missing** | **absent** | **Created** `scripts/download_dataset.py` stub (see §Patches) |

---

## Variant Name Mapping

| Blueprint variant name | Real config file | Notes |
|---|---|---|
| `naive_rag` | `config/variants/baseline_naive_rag.yaml` | |
| `standard_graphrag` | `config/variants/baseline_graphrag.yaml` | |
| `plus_c1` | `config/variants/ablation_c1_only.yaml` | |
| `plus_c1_c2` | `config/variants/ablation_c1_c2.yaml` | |
| `plus_c1_c2_c3` | `config/variants/ablation_c1_c2_c3.yaml` | |
| `full_edurag` | `config/variants/full_system.yaml` | |

---

## Config File Path Mapping

| Blueprint path | Real path | Action |
|---|---|---|
| `configs/sanity.yaml` | `config/sanity.yaml` | **Created** |
| `configs/base.yaml` | `config/base.yaml` | **Use as-is**, invoke with correct path |
| `configs/${VARIANT}.yaml` | `config/variants/${mapped}.yaml` | See variant table above |
| `configs/weights_baseline.yaml` | `config/variants/weights_baseline.yaml` | **Created** |
| `configs/weights_variant_a.yaml` | `config/variants/weights_variant_a.yaml` | **Created** |
| `configs/weights_variant_b.yaml` | `config/variants/weights_variant_b.yaml` | **Created** |
| `configs/weights_variant_c.yaml` | `config/variants/weights_variant_c.yaml` | **Created** |
| `configs/weights_variant_d.yaml` | `config/variants/weights_variant_d.yaml` | **Created** |

---

## Updated Run Commands (using real paths)

Use these instead of the blueprint commands verbatim:

```powershell
# §1 Sanity check
python scripts/run_experiment.py `
    --config config/sanity.yaml `
    --dataset custom_qa `
    --variant full_edurag `
    --limit 5 `
    --seed 42 `
    --output "paper finalization/edurag_project/results/raw_results/sanity.json"

# §4 Custom QA (example)
python scripts/build_graph.py `
    --config config/base.yaml `
    --input data/uploads/ `
    --output data/graphs/custom_qa_graph.pkl `
    --confidence-on `
    --dump-confidence-histogram "paper finalization/edurag_project/results/raw_results/custom_qa_conf_hist.json" `
    --dump-per-method-stats "paper finalization/edurag_project/results/raw_results/custom_qa_method_stats.json"
```

---

## Flags Implemented (summary)

All flags below were **absent** in the real codebase and have been **added** in this session.  
No existing flag semantics were changed.

| Flag | Script | Behaviour |
|---|---|---|
| `--bucket-by-hops` | `run_experiment.py` | Groups QA results by hop-depth label field; emits per-hop sub-tables in output JSON |
| `--multi-entity-only` / `--multi-entity-tag` | `run_experiment.py` | Filters evaluation to questions where seed-linker returns ≥2 seeds |
| `--log-operational-metrics` | `run_experiment.py` | Adds `latency_ms`, `tokens`, `nodes_visited`, `p50`, `p95` to output JSON |
| `--confidence-on` | `build_graph.py` | Forces `confidence.enabled = True` regardless of config YAML value |
| `--dump-confidence-histogram` | `build_graph.py` | Writes confidence-bucket histogram JSON after ingestion |
| `--dump-per-method-stats` | `build_graph.py` | Writes per-extractor-method triple/confidence stats to JSON |
| `--emit-markdown` | `aggregate_results.py` | Emits a markdown summary table alongside the JSON output |
| `--emit-ablation-table` | `aggregate_results.py` | Emits delta-table markdown showing per-contribution ROUGE-L gain |
| `--emit-markdown` | `aggregate_weights.py` | Emits weight sensitivity markdown table |

---

## Notes & Caveats

1. **`scripts/run_experiments.py` (plural)** — the existing orchestrator — is a *status tracker* and **simulation scaffold** (all phases print hardcoded strings, no actual LLM calls). It does **not** implement the CLI contract required by `run_commands.md`. The new `scripts/run_experiment.py` (singular) is the real runner that calls `src/pipeline.py`.

2. **`scripts.ocr_benchmark`** — The repository uses Groq Vision / Gemini Vision for OCR (`app/vision/vision_extractor.py`), not Tesseract. The benchmark script is created as a stub that routes through the existing `VisionExtractor`. The `saeocr_v1.2` engine is the internal SAE-based OCR pipeline; `tesseract_v5` calls `pytesseract` if available. Populate `data/ocr_bench/` with sample documents before running §6.

3. **`scripts.parse_user_study`** — Created as a stub that reads backend logs and emits usage metrics. Requires actual backend log files in `logs/backend/` and a participant list at `data/user_study/participants.csv`.

4. **Dataset downloads** — MuSiQue and 2WikiMultiHopQA must be downloaded manually (GitHub repos linked in `run_commands.md`). `scripts/download_dataset.py` is a stub that prints instructions and checks for the data directory.

---

*Stop. Awaiting user sign-off before proceeding to Task 2 (sanity check).*
