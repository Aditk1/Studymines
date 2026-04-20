# Paper Outline (Transcribed from Handwritten Notes)

Source: `outline/handwritten_outline_page1.jpeg` and `handwritten_outline_page2.jpeg`

---

## Top-level sections (page 1)

1. Abstract
2. Introduction
3. Existing technology
4. Emerging opportunities
5. Methodology
6. System Architecture
7. Result and discussion
8. Future
9. Conclusion
10. References

---

## Detailed structure (page 2)

- **I) Project idea discussion** → linked to Introduction
- **II) Literature review** → linked to Related Work
- **III) Methodology**
  - i) Dataset discussion
  - ii) Text cleaning and preparation
  - iii) Classification model
  - iv) Model Training
  - v) Evaluation
- **IV) System design and Architecture**
  - i) System design / Architecture
  - ii) Text preprocessing
  - iii) Drawback
  - iv) Output & usage
  - v) Workflow
- **V) Result & Discussion** — "discuss every test"
- **VI) Conclusion**
- **References**

---

## Mapping — handwritten outline → published paper v2

| Outline Section | Published Paper §  | Status |
|---|---|---|
| Abstract | Abstract | ✓ matches |
| Introduction → Project idea | §I Introduction | ✓ expanded (A. why it matters, B. contributions, C. scope) |
| Existing technology | §II Related Work | ✓ matches (RAG, graphs, confidence, Leiden) |
| Emerging opportunities | — | Folded into §I-A and §II-C |
| Methodology → Dataset, cleaning, classification, training, evaluation | §III Problem Formulation + §V Experimental Methodology | Partial — "classification model" and "model training" do not appear (the paper is a retrieval/graph system, not a classifier). **Possible mismatch — confirm whether outline was from an earlier project direction.** |
| System Architecture → design, preprocessing, drawback, output, workflow | §IV System Architecture | ✓ covers pipeline, chunking, C1–C4, context assembly |
| Result & Discussion → "discuss every test" | §VI Results and Analysis + §VII Discussion | Partial — many "every test" rows are **[RUN]** gaps flagged in `results/results_workbook.md` |
| Future | §VII-C "What comes next" | ✓ matches |
| Conclusion | §VIII Conclusion | ✓ matches |
| References | References [1]–[25] | ✓ matches |

---

## Gaps between outline and paper worth flagging

1. **"Classification model" and "Model Training" (III-iii, III-iv)** — absent from the published paper. Either (a) these were dropped when the project pivoted to GraphRAG or (b) they map onto the extraction/traversal components and just need renaming. Worth a sentence in §III to explain.
2. **"Drawback" subsection (IV-iii)** — paper has no dedicated drawback section in the architecture chapter. Paper §VII-B covers limitations but from a results angle, not an architectural one. Consider adding an "Architectural trade-offs" paragraph.
3. **"Output & usage" (IV-iv)** — the frontend/React side gets one sentence in §I-C but no screenshots or usage walk-through. A half-page with one UI figure would help reviewers judge real-world utility.
4. **"Discuss every test" (V)** — currently under-delivered. The workbook tracks what needs filling.
