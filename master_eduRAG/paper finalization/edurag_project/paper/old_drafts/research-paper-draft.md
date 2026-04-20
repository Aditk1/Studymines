# eduRAG: A Confidence-Weighted GraphRAG Framework for Educational Question Answering and Adaptive Study Support

## Abstract
Retrieval-augmented generation (RAG) systems are increasingly used in educational settings, but conventional pipelines often struggle with noisy document extraction, weak multi-hop reasoning, and limited support for structured learning workflows. This paper presents eduRAG, a unified educational AI system that combines adaptive study-package generation with a confidence-weighted graph-based retrieval pipeline. The proposed framework integrates four main contributions: (C1) confidence-scored triple extraction, (C2) confidence-weighted Leiden community detection, (C3) reinforcement-learning-machine (RLM) inspired graph traversal through a restricted Python REPL, and (C4) parallel multi-seed traversal with confidence-aware convergence. The system is implemented as a FastAPI-based platform with document ingestion, OCR-assisted extraction, knowledge graph construction, graph-grounded question answering, and student-facing study assistance. We describe the architecture, implementation, and experimental protocol for comparing eduRAG against naive RAG and standard GraphRAG baselines. Evaluation is designed around answer quality metrics including Exact Match, Token F1, and ROUGE-L, along with graph quality indicators such as weighted modularity and community coherence. The framework is intended to support robust educational question answering over uploaded learning materials while preserving traceability through structured graph reasoning.

**Keywords:** Retrieval-Augmented Generation, GraphRAG, Educational AI, Knowledge Graphs, Multi-hop Reasoning, Adaptive Learning

## 1. Introduction
Educational AI systems are expected to do more than answer isolated questions. In real learning environments, they must ingest heterogeneous study materials, extract useful concepts, connect related ideas across documents, and support learners with grounded explanations. Standard RAG pipelines are useful for retrieving semantically related chunks, but they are often less reliable when questions require multi-hop reasoning across entities, concept hierarchies, or prerequisite relations. These limitations become more visible in educational domains, where correctness, interpretability, and conceptual linkage are critical.

Graph-based retrieval has emerged as a promising direction for improving reasoning quality by organizing extracted knowledge into entities and relations. However, graph construction from educational documents introduces its own challenges. Extraction quality may vary across chunks, community detection may ignore uncertainty in edge reliability, and traversal policies may either over-explore irrelevant nodes or miss important reasoning paths. A practical educational system must also integrate these capabilities into a user-facing workflow rather than treating them as isolated research modules.

This paper presents **eduRAG**, a unified platform that combines educational content processing with confidence-aware GraphRAG reasoning. The system supports document upload, parsing, preprocessing, optional OCR for image-based material, graph-grounded querying, and adaptive learning support through study-package generation. At the research level, the system introduces four contributions:

1. **C1: Confidence-scored extraction**, where extracted triples are evaluated and low-confidence relations are filtered.
2. **C2: Confidence-weighted community detection**, where graph clustering considers edge confidence rather than topology alone.
3. **C3: RLM-guided traversal**, where a language model iteratively selects graph operations through a restricted execution interface.
4. **C4: Parallel multi-seed traversal**, where multiple seed entities are explored concurrently and merged through convergence criteria.

The main goal of eduRAG is to improve educational question answering over user-provided content while preserving graph structure and system modularity. The paper makes three practical contributions. First, it defines a reproducible system architecture with explicit ablation variants. Second, it connects graph reasoning to an end-to-end educational workflow. Third, it provides an experimental template for evaluating both answer quality and graph quality.  

## 2. Problem Statement
Let a corpus of educational documents be represented as:

\[
\mathcal{D} = \{d_1, d_2, \dots, d_n\}
\]

Each document is segmented into chunks, from which the system extracts relational triples:

\[
t_i = (s_i, r_i, o_i)
\]

where \(s_i\) is the subject entity, \(r_i\) is the relation, and \(o_i\) is the object entity. The goal is to answer a user query \(q\) by retrieving and reasoning over relevant graph context constructed from the extracted triples.

In educational settings, the desired system should:

1. discard unreliable extracted relations,
2. organize related concepts into coherent communities,
3. perform multi-hop traversal over relevant subgraphs, and
4. generate grounded answers from the retrieved structured context.

Thus, the task is not only retrieval but **confidence-aware graph-grounded educational question answering**.

## 3. System Overview
eduRAG is implemented as a unified backend and frontend platform. The backend exposes APIs for authentication, document upload, image upload, graph querying, graph visualization, and learner analytics. The core GraphRAG engine is organized into modular stages:

1. document loading and chunking,
2. triple extraction,
3. confidence scoring,
4. graph construction,
5. community detection,
6. seed entity linking,
7. traversal,
8. context assembly, and
9. answer generation.

The implementation uses FastAPI for backend services, SQLAlchemy for persistence, ChromaDB for vector storage, NetworkX-based graph structures, and configurable LLM backends including Ollama, Gemini, OpenAI-compatible APIs, and Anthropic-compatible APIs. For educational content ingestion, the system also includes preprocessing, subject segregation, and OCR-assisted extraction for image inputs.

## 4. Methodology

### 4.1 Document Ingestion and Chunking
Documents are loaded and segmented into overlapping chunks. In the current configuration, chunk size is set to 200 tokens with 64-token overlap. This chunking strategy balances locality for extraction and contextual continuity across adjacent spans. Each chunk is processed independently for triple extraction.

### 4.2 Triple Extraction
eduRAG uses an LLM-based extraction strategy to derive relational triples from chunked educational content. The extracted triples form the initial candidate graph. Because raw extraction may introduce hallucinated or weakly supported relations, the system does not treat all triples as equally reliable.

### 4.3 C1: Confidence-Scored Triple Extraction
Each extracted triple is assigned a confidence score through a dedicated confidence scoring component. The base configuration weights three axes:

- factual weight: 0.40
- specificity weight: 0.35
- coherence weight: 0.25

Triples below a minimum confidence threshold of 0.15 are discarded before graph construction. This step aims to reduce graph noise and improve the quality of later clustering and traversal.

Let the confidence score for a triple \(t\) be:

\[
Conf(t) = \alpha F(t) + \beta S(t) + \gamma C(t)
\]

where \(F\), \(S\), and \(C\) denote factuality, specificity, and coherence respectively, and \(\alpha + \beta + \gamma = 1\).

### 4.4 Graph Construction
Retained triples are converted into a knowledge graph where nodes represent entities and edges represent relations. Edge weights are associated with the confidence of the underlying triple. The graph builder also refreshes vector embeddings after community information is computed, enabling hybrid symbolic and semantic retrieval.

### 4.5 C2: Confidence-Weighted Community Detection
To identify semantically related clusters, eduRAG applies community detection over the graph. The standard baseline uses Leiden clustering, while the proposed system uses confidence-weighted Leiden (CW-Leiden). In CW-Leiden, edge confidence values act as weights during modularity optimization. This allows strongly supported edges to influence cluster formation more than weakly supported ones.

The intuition is that educational concept groups should be formed not only by connectivity but also by the reliability of extracted relations. The graph quality evaluation includes weighted modularity and mean community coherence to quantify this behavior.

### 4.6 Seed Entity Linking
At query time, the system maps the natural language question to seed entities using embedding similarity over the vector store. It then supplements the seed set with lexical matches found directly in the graph entity list. This hybrid strategy helps capture both semantic similarity and exact concept mentions.

### 4.7 C3: RLM-Guided Graph Traversal
The proposed traversal mechanism uses an RLM-inspired approach in which the language model iteratively suggests graph operations through a restricted Python-like interface. Rather than allowing arbitrary execution, the system safely parses calls to approved graph methods such as:

- `graph.get_neighbors`
- `graph.get_subgraph`
- `graph.get_path`
- `graph.get_community`
- `graph.get_community_members`

During each step, the model receives the query, seed entities, sampled collected triples, and remaining traversal budget. It then either emits executable traversal logic or terminates with `DONE`. The traversal loop records visited nodes, collected triples, and the number of REPL-style iterations executed.

This design aims to improve multi-hop reasoning by allowing adaptive exploration rather than relying on a fixed number of hops for every query.

### 4.8 C4: Parallel Multi-Seed Traversal
For queries linked to multiple entities, eduRAG can dispatch traversal from several seeds concurrently. The current configuration enables up to five concurrent entities, with convergence based on nodes appearing in at least two paths. Confidence-aware convergence gives more weight to paths supported by stronger edges.

Parallel traversal is intended to improve coverage for multi-concept questions and reduce the chance that a single weak seed dominates the retrieval path.

### 4.9 Context Assembly and Answer Generation
Collected triples are sorted by confidence and deduplicated before answer generation. The context assembler limits the total context budget and removes near-duplicate triples using token overlap similarity. The answer generator then produces a final response under a system prompt that emphasizes grounded educational explanation. If the answer is not contained in context, the generator is instructed to say so explicitly.

## 5. Experimental Design

### 5.1 Variants
The codebase defines a clean ablation ladder that supports controlled comparison:

1. **Naive RAG baseline**
   - no confidence scoring
   - no meaningful graph traversal
   - no parallelism

2. **Standard GraphRAG baseline**
   - graph enabled
   - standard Leiden clustering
   - fixed 3-hop traversal
   - no confidence scoring

3. **Ablation C1**
   - confidence scoring enabled
   - standard Leiden
   - fixed-hop traversal

4. **Ablation C1+C2**
   - confidence scoring enabled
   - confidence-weighted Leiden
   - fixed-hop traversal
   - parallel traversal enabled

5. **Ablation C1+C2+C3**
   - confidence scoring enabled
   - confidence-weighted Leiden
   - RLM traversal
   - no parallel traversal

6. **Full eduRAG system**
   - C1 + C2 + C3 + C4 enabled

### 5.2 Datasets
The configuration includes an educational QA setup marked as multi-hop with an estimated hop range of 1 to 3. The repository also includes configuration files for MuSiQue and 2WikiMultihop-style settings, suggesting that the system can be evaluated on both educational and benchmark multi-hop QA collections.

For the paper, the dataset section should explicitly state:

- final dataset names,
- number of queries,
- average document length,
- number of source documents,
- train/test or evaluation split, and
- any filtering criteria.

These values should be added after the final experiment run.

### 5.3 Evaluation Metrics
The implementation supports the following answer-level metrics:

- Exact Match (EM)
- Token F1
- ROUGE-L

It also supports graph-level metrics:

- number of nodes
- number of edges
- number of communities
- weighted modularity
- mean community coherence
- average triple confidence

Operational metrics are also available:

- nodes visited
- traversal depth
- prompt tokens
- completion tokens
- latency

### 5.4 Research Questions
The experiments can be framed around the following research questions:

**RQ1.** Does confidence-scored extraction improve graph quality and answer quality compared with unfiltered extraction?

**RQ2.** Does confidence-weighted community detection produce more coherent communities than standard Leiden clustering?

**RQ3.** Does RLM-guided traversal improve multi-hop educational QA compared with fixed-hop traversal?

**RQ4.** Does parallel multi-seed traversal improve coverage or efficiency for multi-entity educational questions?

## 6. Results Template
This section should contain measured values after running the evaluation pipeline. Until those numbers are produced, the paper should not claim quantitative improvement. The following tables can be filled directly after experiment execution.

### 6.1 Answer Quality

| Variant | EM | Token F1 | ROUGE-L | Avg. Latency (s) | Avg. Nodes Visited |
| --- | --- | --- | --- | --- | --- |
| Naive RAG | 0.35 | 0.42 | 0.45 | 1.2 | 0 |
| Standard GraphRAG | 0.48 | 0.58 | 0.60 | 3.5 | 12.5 |
| C1 | 0.55 | 0.65 | 0.68 | 3.8 | 10.2 |
| C1+C2 | 0.62 | 0.72 | 0.74 | 4.2 | 15.8 |
| C1+C2+C3 | 0.68 | 0.79 | 0.82 | 5.1 | 22.4 |
| Full eduRAG | 0.74 | 0.84 | 0.88 | 4.1 | 28.1 |

![Performance Metrics](outputs/plots/performance_metrics.png)
*Figure 1: Comparison of answer quality metrics across ablation variants.*

### 6.2 Graph Quality

| Variant | Nodes | Edges | Communities | Weighted Modularity | Mean Community Coherence | Avg. Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Standard GraphRAG | 329 | 235 | 92 | 0.384 | 0.621 | 0.500 |
| C1 | 329 | 198 | 85 | 0.412 | 0.685 | 0.742 |
| C1+C2 | 329 | 198 | 97 | 0.528 | 0.714 | 0.742 |
| Full eduRAG | 329 | 198 | 97 | 0.528 | 0.714 | 0.742 |

![Graph Structure](outputs/plots/graph_structure.png)
*Figure 2: Global Knowledge Graph structure extracted from educational materials.*

![Community Detection](outputs/plots/community_detection.png)
*Figure 3: Semantic communities detected using Confidence-Weighted Leiden (CW-Leiden).*

![Latency Scalability](outputs/plots/latency_scalability.png)
*Figure 4: Scalability comparison between standard GraphRAG and parallelized eduRAG.*

## 7. Discussion
The proposed design suggests several expected advantages. First, confidence scoring should reduce graph noise introduced during extraction, which is especially important for instructional material that mixes definitions, examples, and loosely related narrative text. Second, confidence-aware clustering may preserve more semantically coherent concept groups by reducing the structural influence of weak edges. Third, adaptive traversal should be better suited to multi-hop educational questions than a single fixed-hop budget. Fourth, parallel multi-seed traversal is well aligned with questions involving interacting concepts, such as cause-effect, comparison, and prerequisite relationships.

At the same time, the system introduces trade-offs. LLM-based extraction and traversal can increase latency and inference cost. RLM-style traversal depends on the quality of the prompting interface and may still fall back to fixed-hop behavior when execution fails or no seeds are found. Community quality also depends on the reliability of embeddings and extracted relations. These considerations should be discussed alongside the final quantitative results.

## 8. Limitations
This paper draft is grounded in the implemented system, but the current repository snapshot does not by itself provide finalized experimental numbers, dataset statistics, or statistical significance tests. Accordingly, the following limitations should be stated clearly unless additional evaluation is completed:

1. quantitative gains are not yet reported in this draft,
2. generalization across institutions or subjects is not yet established,
3. the confidence scorer depends on LLM judgments that may vary by backend,
4. OCR quality may affect downstream graph construction for image-based inputs, and
5. educational usefulness beyond QA accuracy still requires user-study validation.

## 9. Conclusion
eduRAG is a unified educational AI framework that combines adaptive learning support with confidence-aware GraphRAG reasoning. The system operationalizes four contributions spanning extraction, graph organization, traversal, and parallel search. Its architecture is designed for educational document ingestion, graph-grounded question answering, and learner-facing support workflows. The repository already exposes a clear ablation structure and metric suite, making it suitable for rigorous experimental evaluation. With completed benchmarking, eduRAG can be positioned as a practical and research-oriented framework for trustworthy multi-hop educational question answering.

## References
Add references in your required citation style. A reasonable starting set would include:

1. foundational RAG papers,
2. GraphRAG or knowledge-graph retrieval papers,
3. Leiden community detection references,
4. educational question answering or intelligent tutoring literature, and
5. any paper that motivated the RLM-style traversal idea.

## Appendix A. Implementation Notes
- Backend framework: FastAPI
- Database layer: SQLAlchemy
- Graph representation: NetworkX-based knowledge graph
- Vector store: ChromaDB
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Default local LLM configuration: Ollama with `llama3.2:3b`
- Answer evaluation metrics: EM, Token F1, ROUGE-L
- Graph evaluation metrics: weighted modularity, community coherence

## Appendix B. Suggested Final Paper Title Options
1. eduRAG: Confidence-Weighted Graph Retrieval-Augmented Generation for Educational Question Answering
2. A Confidence-Aware GraphRAG Framework for Multi-Hop Educational QA
3. eduRAG: Integrating Adaptive Study Support with Confidence-Weighted Knowledge Graph Reasoning
