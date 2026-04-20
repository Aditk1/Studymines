# eduRAG — Autopilot Run Commands

Every [RUN §N] tag in `results/results_workbook.md` maps to a section here.
Commands assume:
- Repo root = `$EDURAG_HOME` (export before running)
- Ollama daemon reachable at `localhost:11434` with `llama3.2:3b` pulled
- ChromaDB running (start via `docker compose up -d chromadb` or the existing backend)
- Python env has the repo's `requirements.txt` installed

```bash
# one-time env setup
export EDURAG_HOME=/path/to/edurag        # EDIT
export OLLAMA_HOST=http://localhost:11434
export CHROMA_URL=http://localhost:8000
mkdir -p $EDURAG_HOME/results/raw_results $EDURAG_HOME/logs/experimental_runs
cd $EDURAG_HOME
```

All commands below write JSON results to `results/raw_results/<dataset>_<variant>.json` and append timings to `logs/experimental_runs/<dataset>.log`. They are idempotent — rerun safely.

---

## §1. Sanity check (run first)

Fast smoke test so you catch env problems before a 6-hour run kicks off.

```bash
python -m scripts.run_experiment \
    --config configs/sanity.yaml \
    --dataset custom_qa \
    --variant full_edurag \
    --limit 5 \
    --seed 42 \
    --output results/raw_results/sanity.json
```

Expected: completes in < 2 min, ROUGE-L > 0.30, no tracebacks in stderr.

---

## §2. MuSiQue — full run (500 questions × 6 variants)

```bash
# 2a. Download & preprocess (one time)
python -m scripts.download_dataset \
    --name musique \
    --split dev \
    --output data/musique/ \
    --url https://github.com/StonyBrookNLP/musique

# 2b. Build graph once, reuse across variants
python -m scripts.build_graph \
    --config configs/base.yaml \
    --input data/musique/dev.jsonl \
    --output graphs/musique_graph.pkl \
    --confidence-on \
    --log logs/experimental_runs/musique_graph.log

# 2c. Run all six variants (sequential; ~4–6 h on single GPU)
for VARIANT in naive_rag standard_graphrag plus_c1 plus_c1_c2 plus_c1_c2_c3 full_edurag; do
    python -m scripts.run_experiment \
        --config configs/${VARIANT}.yaml \
        --dataset musique \
        --graph graphs/musique_graph.pkl \
        --variant ${VARIANT} \
        --bucket-by-hops \
        --seed 42 \
        --output results/raw_results/musique_${VARIANT}.json \
        2>&1 | tee logs/experimental_runs/musique_${VARIANT}.log
done

# 2d. Aggregate
python -m scripts.aggregate_results \
    --dataset musique \
    --results-dir results/raw_results/ \
    --output results/musique_summary.json \
    --emit-markdown results/musique_summary.md
```

Populates: all `[RUN §2]` cells in the workbook (graph construction, answer quality, hop breakdown, C4 multi-entity).

---

## §3. 2WikiMultiHopQA — full run

```bash
# 3a. Download
python -m scripts.download_dataset \
    --name 2wiki \
    --split dev \
    --output data/2wiki/ \
    --url https://github.com/Alab-NII/2wikimultihop

# 3b. Build graph
python -m scripts.build_graph \
    --config configs/base.yaml \
    --input data/2wiki/dev.jsonl \
    --output graphs/2wiki_graph.pkl \
    --confidence-on \
    --log logs/experimental_runs/2wiki_graph.log

# 3c. All six variants
for VARIANT in naive_rag standard_graphrag plus_c1 plus_c1_c2 plus_c1_c2_c3 full_edurag; do
    python -m scripts.run_experiment \
        --config configs/${VARIANT}.yaml \
        --dataset 2wiki \
        --graph graphs/2wiki_graph.pkl \
        --variant ${VARIANT} \
        --bucket-by-hops \
        --seed 42 \
        --output results/raw_results/2wiki_${VARIANT}.json \
        2>&1 | tee logs/experimental_runs/2wiki_${VARIANT}.log
done

# 3d. Aggregate
python -m scripts.aggregate_results \
    --dataset 2wiki \
    --results-dir results/raw_results/ \
    --output results/2wiki_summary.json \
    --emit-markdown results/2wiki_summary.md
```

Populates: all `[RUN §3]` cells.

---

## §4. Custom Educational QA — fill intermediate variants & breakdowns

The paper only published endpoint rows (Naive RAG + Full eduRAG). This fills every intermediate variant plus hop, confidence-distribution, and multi-entity breakdowns.

```bash
# 4a. Rebuild graph with full instrumentation
python -m scripts.build_graph \
    --config configs/base.yaml \
    --input data/custom_qa/corpus.jsonl \
    --output graphs/custom_qa_graph.pkl \
    --confidence-on \
    --dump-confidence-histogram results/raw_results/custom_qa_conf_hist.json \
    --dump-per-method-stats results/raw_results/custom_qa_method_stats.json \
    --log logs/experimental_runs/custom_qa_graph.log

# 4b. Run all variants with instrumentation
for VARIANT in naive_rag standard_graphrag plus_c1 plus_c1_c2 plus_c1_c2_c3 full_edurag; do
    python -m scripts.run_experiment \
        --config configs/${VARIANT}.yaml \
        --dataset custom_qa \
        --graph graphs/custom_qa_graph.pkl \
        --variant ${VARIANT} \
        --bucket-by-hops \
        --multi-entity-tag \
        --log-operational-metrics \
        --seed 42 \
        --output results/raw_results/custom_qa_${VARIANT}.json \
        2>&1 | tee logs/experimental_runs/custom_qa_${VARIANT}.log
done

# 4c. Community-detection A/B (vanilla Leiden vs CW-Leiden on identical graph)
python -m scripts.community_ab \
    --graph graphs/custom_qa_graph.pkl \
    --algorithms leiden cw_leiden \
    --resolution 1.0 --seed 42 --iterations 10 \
    --output results/raw_results/custom_qa_community_ab.json

# 4d. Aggregate + ablation delta table
python -m scripts.aggregate_results \
    --dataset custom_qa \
    --results-dir results/raw_results/ \
    --output results/custom_qa_summary.json \
    --emit-ablation-table results/custom_qa_ablation.md
```

Populates: `[RUN §4]` cells + the RQ2 comparison pair + the C3-per-hop breakdown + the C4 multi-entity rows.

---

## §5. Confidence weight sensitivity analysis

```bash
# Grid over weight configurations on Custom QA
for CFG in baseline variant_a variant_b variant_c variant_d; do
    python -m scripts.run_experiment \
        --config configs/weights_${CFG}.yaml \
        --dataset custom_qa \
        --variant full_edurag \
        --seed 42 \
        --output results/raw_results/weights_${CFG}.json
done

python -m scripts.aggregate_weights \
    --inputs 'results/raw_results/weights_*.json' \
    --emit-markdown results/weight_sensitivity.md
```

Config files with the weight triples:

| CFG | Factuality | Specificity | Coherence |
|---|---|---|---|
| baseline | 0.40 | 0.35 | 0.25 |
| variant_a | 0.50 | 0.30 | 0.20 |
| variant_b | 0.40 | 0.40 | 0.20 |
| variant_c | 0.30 | 0.35 | 0.35 |
| variant_d | 0.33 | 0.33 | 0.34 |

Populates: `[RUN §5]` sensitivity table in Section D.

---

## §6. OCR breakdown by document type

```bash
python -m scripts.ocr_benchmark \
    --input data/ocr_bench/ \
    --engines saeocr_v1.2 tesseract_v5 \
    --by-type scanned_textbooks handwritten_notes annotated_pdfs \
    --output results/raw_results/ocr_breakdown.json \
    --emit-markdown results/ocr_breakdown.md
```

Populates: `[RUN §6]` rows in Section E.

---

## §7. User-study usage metrics from backend logs

```bash
python -m scripts.parse_user_study \
    --backend-logs logs/backend/ \
    --user-ids data/user_study/participants.csv \
    --output results/raw_results/user_study_usage.json \
    --emit-markdown results/user_study_usage.md
```

Populates: usage pattern rows in Section F (queries/session, session length, % using graph, % reading paths).

---

## Execution plan (suggested order)

| Step | Why first | Est. wall time |
|---|---|---|
| §1 Sanity | Catch broken env before big runs | 2 min |
| §4 Custom QA full ablation | Validates every intermediate row already claimed in paper | 1–2 h |
| §2 MuSiQue | Largest new dataset; kick off overnight | 4–6 h |
| §3 2Wiki | Run after MuSiQue | 4–6 h |
| §5 Weight sensitivity | Cheap, high reviewer value | 1 h |
| §6 OCR breakdown | Independent of graph runs | 20 min |
| §7 User-study parse | Pure log parsing | 5 min |

**Total**: roughly one full day of compute for the complete set.

---

## Monitoring during long runs

```bash
# Tail all logs
tail -f logs/experimental_runs/*.log

# Progress across variants
watch -n 30 'ls -la results/raw_results/ | tail -20'

# Quick results peek
jq '.summary' results/raw_results/musique_full_edurag.json
```

If a run dies mid-variant, rerun just that variant — outputs are keyed by `(dataset, variant)` so nothing else is invalidated.

---

## Post-run: regenerate the populated workbook

Once all JSONs are in `results/raw_results/`:

```bash
python -m scripts.populate_workbook \
    --template results/results_workbook.md \
    --raw-dir results/raw_results/ \
    --output results/results_workbook_populated.md
```

This replaces every `[RUN §N]` tag with the value from the matching JSON and flags anything still missing.
