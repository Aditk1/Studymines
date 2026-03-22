"""
Structured logging using structlog.
Outputs JSON for machine-parsing and JSONL experiment records.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import structlog


def setup_logging(level: str = "INFO", output_dir: str | Path | None = None) -> None:
    """
    Configure structlog for the entire application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        output_dir: If provided, also write JSON logs to this directory.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Standard library logging setup
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named structured logger."""
    return structlog.get_logger(name)


class ExperimentLogger:
    """
    Writes per-query experiment records to a JSONL file.
    Each line is one complete query result record.
    """

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = get_logger("experiment")

    def record(self, **fields: Any) -> None:
        """Write one record to the JSONL log."""
        with self.output_path.open("a") as f:
            f.write(json.dumps(fields) + "\n")
        self._log.info("query_recorded", **{k: v for k, v in fields.items() if k != "context"})

    def read_all(self) -> list[dict[str, Any]]:
        """Read all records from the JSONL file."""
        if not self.output_path.exists():
            return []
        records = []
        with self.output_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
