# eduRAG — Paper Project Files

Consolidated working folder for the eduRAG paper. All inputs from the 2026-04-13 data drop are organized here, with gaps flagged and autopilot commands ready to run.

## Layout

```
edurag_project/
├── README.md                         ← you are here
├── paper/
│   └── final_paper_v2.pdf            ← current draft (source of truth for claimed numbers)
├── outline/
│   ├── handwritten_outline_page1.jpeg
│   ├── handwritten_outline_page2.jpeg
│   └── paper_outline_transcribed.md  ← transcription + gap analysis vs published paper
├── results/
│   └── results_workbook.md           ← populated workbook; [RUN §N] tags mark gaps
├── experiments/
│   └── run_commands.md               ← autopilot commands to fill every [RUN §N] tag
└── artifacts/
    ├── plots/                        ← community_detection, graph_structure, latency, performance
    ├── logs/                         ← backend / frontend stdout & stderr
    ├── audits/                       ← api_smoke, browser_audit, inventory, responsive_audit
    └── review/                       ← file-list, function-inventory, repo tree
```

## What's confirmed (from paper)

- Mean weighted modularity **0.9248**, mean coherence **0.3173** (3 artifacts)
- Mean triple confidence after C1: **0.6479**
- Custom Educational QA: ROUGE-L **0.442** (+25.6%), BERTScore F1 **0.912** (+8.3%), METEOR **0.385** (+13.9%)
- OCR: SAEOCR v1.2 **91.8%** vs Tesseract v5 **57.5%**
- User study: N=5, scores 4.4–4.8 (paper flags as under-powered)

## What's missing

The published paper reports endpoint rows only. Intermediate ablation variants, per-hop breakdowns, MuSiQue, 2WikiMultiHopQA, confidence distributions, and the vanilla-Leiden baseline needed for RQ2 are all absent. Every gap is tagged `[RUN §N]` in `results/results_workbook.md` with a matching command in `experiments/run_commands.md`.

## Suggested next steps

1. Read `outline/paper_outline_transcribed.md` — there are 4 flagged mismatches between the original outline and the current draft that may need addressing before submission.
2. Run `experiments/run_commands.md` §1 (sanity check, 2 min) to confirm the environment.
3. Kick off §4 (Custom QA full ablation, ~1–2 h) first — this fills the holes in claims the paper already makes.
4. Queue §2 (MuSiQue) and §3 (2Wiki) overnight.
5. Regenerate the populated workbook via the command at the bottom of `experiments/run_commands.md`.

## Risks / review flags

- **RQ2 claim is under-supported.** The paper asserts CW-Leiden > vanilla Leiden, but the vanilla-Leiden row is not in the final PDF. §4c of the run commands fixes this — prioritise before submission.
- **Confidence weights are theoretical.** The 0.40/0.35/0.25 split is not empirically validated; §5 sensitivity sweep is the cheapest way to blunt reviewer pushback.
- **N=5 user study** is fragile. Paper already acknowledges this. If there is any time before submission, expand to N≥20.
- **Scaling claims at 329 nodes** are speculative. MuSiQue and 2Wiki runs will either substantiate or disprove this — either outcome is useful.
- **Outline mismatch** (see `outline/paper_outline_transcribed.md`): "Classification model" and "Model Training" appear in the original outline but not the paper. If an earlier version used classification, briefly explain the pivot in §III.
