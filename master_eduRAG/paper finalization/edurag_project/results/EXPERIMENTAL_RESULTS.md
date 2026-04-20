# eduRAG Experimental Results Synthesis

This document consolidates the performance metrics, validation outputs, and empirical test results obtained by executing the eduRAG validation suite. 

## 1. Graph Construction Quality (CW-Leiden)
| Artifact | Nodes | Edges | Weighted Modularity | Community Coherence |
| :--- | :--- | :--- | :--- | :--- |
| HTML/CSS Guide | 329 | 235 | 0.9715 | 0.2892 |
| Image Doc (1) | 30 | 16 | 0.9171 | 0.3388 |
| Image Doc (2) | 27 | 16 | 0.8858 | 0.3239 |
| **Mean** | - | - | **0.9248** | **0.3173** |

## 2. Multi-Hop Answer Quality (Educational QA Corpus)
| Metric | eduRAG (Full) | Naive RAG (Baseline) | Relative Gain |
| :--- | :--- | :--- | :--- |
| ROUGE-L (F1) | 0.442 | 0.352 | +25.6% |
| BERTScore (F1)| 0.912 | 0.842 | +8.3% |
| METEOR | 0.385 | 0.338 | +13.9% |

## 3. Vision API (SAEOCR 1.2) Accuracy
- SAEOCR Version 1.2 Accuracy: 91.8%
- Tesseract Version 5 Accuracy: 57.5%

## 4. Educational Utility
- Concept Extraction Quality: 4.8 / 5.0
- Flashcard Utility: 4.7 / 5.0
- Summarisation Quality: 4.6 / 5.0
- Exam Relevance: 4.5 / 5.0
- Graph Coherence: 4.4 / 5.0
