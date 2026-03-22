"""
Configuration system using Pydantic v2.
Loads base YAML and merges with variant/dataset overrides.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class LLMConfig(BaseModel):
    provider: Literal["ollama", "openai", "anthropic"] = "ollama"
    model: str = "llama3.2:3b"
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout: int = 120
    ollama_base_url: str = "http://localhost:11434"
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-haiku-4-5-20251001"


class EmbeddingsConfig(BaseModel):
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cuda"
    batch_size: int = 32
    normalize: bool = True


class IngestionConfig(BaseModel):
    chunk_size: int = 512
    chunk_overlap: int = 64
    extractor: Literal["rebel", "spacy", "llm"] = "rebel"
    rebel_model: str = "Babelscape/rebel-large"
    rebel_device: str = "cuda"
    spacy_model: str = "en_core_web_lg"
    min_entity_length: int = 2
    max_triples_per_chunk: int = 50


class ConfidenceAxesConfig(BaseModel):
    factual_weight: float = 0.40
    specificity_weight: float = 0.35
    coherence_weight: float = 0.25


class ConfidenceConfig(BaseModel):
    enabled: bool = True
    axes: ConfidenceAxesConfig = Field(default_factory=ConfidenceAxesConfig)
    min_confidence_threshold: float = 0.15
    batch_size: int = 8


class LeidenConfig(BaseModel):
    resolution: float = 1.0
    n_iterations: int = 10
    seed: int = 42


class CWLeidenConfig(BaseModel):
    resolution: float = 1.0
    n_iterations: int = 10
    seed: int = 42
    weight_attribute: str = "confidence"


class RLMCommunityConfig(BaseModel):
    max_entities_per_call: int = 20
    similarity_threshold: float = 0.6


class CommunityConfig(BaseModel):
    strategy: Literal["leiden", "cw_leiden", "rlm_community"] = "cw_leiden"
    leiden: LeidenConfig = Field(default_factory=LeidenConfig)
    cw_leiden: CWLeidenConfig = Field(default_factory=CWLeidenConfig)
    rlm_community: RLMCommunityConfig = Field(default_factory=RLMCommunityConfig)


class FixedHopConfig(BaseModel):
    k: int = 3


class RLMTraversalConfig(BaseModel):
    max_depth: int = 5
    max_nodes_per_step: int = 10
    min_confidence_filter: float = 0.3
    repl_timeout: int = 30
    max_repl_steps: int = 15


class TraversalConfig(BaseModel):
    strategy: Literal["fixed_hop", "rlm"] = "rlm"
    fixed_hop: FixedHopConfig = Field(default_factory=FixedHopConfig)
    rlm: RLMTraversalConfig = Field(default_factory=RLMTraversalConfig)


class ParallelConfig(BaseModel):
    enabled: bool = True
    max_concurrent_entities: int = 5
    convergence_min_paths: int = 2
    convergence_weight_by_confidence: bool = True
    async_timeout: int = 60


class VectorStoreConfig(BaseModel):
    persist_directory: str = "outputs/chroma_db"
    collection_name: str = "entities"
    distance_metric: str = "cosine"
    top_k: int = 10


class RetrievalConfig(BaseModel):
    seed_entity_top_k: int = 5
    context_max_tokens: int = 3000
    dedup_similarity_threshold: float = 0.92


class AnswerGenerationConfig(BaseModel):
    system_prompt: str = (
        "You are a precise question-answering system. Answer based ONLY on the "
        "provided context. If the answer is not in the context, say 'Not found.' "
        "Be concise."
    )


class EvaluationConfig(BaseModel):
    metrics: list[str] = Field(default_factory=lambda: ["exact_match", "f1", "rouge_l"])
    track_cost: bool = True
    track_latency: bool = True
    track_nodes_visited: bool = True


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    output_dir: str = "outputs/logs"


class ProjectConfig(BaseModel):
    name: str = "rlm_graphrag"
    version: str = "1.0.0"
    seed: int = 42


# ---------------------------------------------------------------------------
# Root config
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    variant_name: str = "base"
    use_graph: bool = True

    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    confidence: ConfidenceConfig = Field(default_factory=ConfidenceConfig)
    community: CommunityConfig = Field(default_factory=CommunityConfig)
    traversal: TraversalConfig = Field(default_factory=TraversalConfig)
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    answer_generation: AnswerGenerationConfig = Field(default_factory=AnswerGenerationConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @model_validator(mode="after")
    def resolve_env_vars(self) -> "AppConfig":
        """Override with environment variable values if set."""
        if os.getenv("LLM_PROVIDER"):
            self.llm.provider = os.environ["LLM_PROVIDER"]  # type: ignore[assignment]
        if os.getenv("OLLAMA_BASE_URL"):
            self.llm.ollama_base_url = os.environ["OLLAMA_BASE_URL"]
        return self


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key.startswith("_"):
            continue  # skip directive keys like _base
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    base_path: str | Path = "config/base.yaml",
    variant_path: str | Path | None = None,
) -> AppConfig:
    """
    Load and merge configuration from YAML files.

    Args:
        base_path: Path to base.yaml
        variant_path: Optional path to variant YAML that overrides base.

    Returns:
        Validated AppConfig instance.
    """
    base_path = Path(base_path)
    with base_path.open() as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    if variant_path is not None:
        variant_path = Path(variant_path)
        with variant_path.open() as f:
            variant_raw: dict[str, Any] = yaml.safe_load(f) or {}
        raw = _deep_merge(raw, variant_raw)

    return AppConfig.model_validate(raw)


def load_config_for_variant(variant_name: str, config_dir: str | Path = "config") -> AppConfig:
    """Convenience loader: resolves variant path by name."""
    config_dir = Path(config_dir)
    base = config_dir / "base.yaml"
    variant = config_dir / "variants" / f"{variant_name}.yaml"
    if not variant.exists():
        raise FileNotFoundError(f"Variant config not found: {variant}")
    return load_config(base, variant)
