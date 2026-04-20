#!/usr/bin/env python3
"""
scripts/parse_user_study.py — Parse backend logs for user-study usage metrics.

Corresponds to `scripts.parse_user_study` in run_commands.md §7.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from collections import defaultdict


def _load_participants(csv_path: str) -> set[str]:
    participants: set[str] = set()
    p = Path(csv_path)
    if not p.exists():
        print(f"  ⚠  Participant list not found: {csv_path}")
        return participants
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("user_id", row.get("id", "")).strip()
            if uid:
                participants.add(uid)
    return participants


_JSON_LINE_RE = re.compile(r'^\{.*\}$')


def _parse_log_file(log_file: Path, participants: set[str]) -> list[dict]:
    events: list[dict] = []
    try:
        with open(log_file, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if _JSON_LINE_RE.match(line):
                    try:
                        ev = json.loads(line)
                        uid = ev.get("user_id", ev.get("uid", ""))
                        if not participants or uid in participants:
                            events.append(ev)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"  ⚠  Could not read {log_file}: {e}")
    return events


def _compute_metrics(events: list[dict]) -> dict:
    """Compute queries/session, session length, % using graph, % reading paths."""
    by_session: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        sid = ev.get("session_id", ev.get("user_id", "unknown"))
        by_session[sid].append(ev)

    sessions = list(by_session.values())
    if not sessions:
        return {"note": "No events found matching participant list"}

    queries_per_session = [
        sum(1 for e in sess if e.get("type") in {"query", "graph_query"})
        for sess in sessions
    ]
    session_lengths_min = [
        (max((e.get("ts", 0) for e in sess), default=0) - min((e.get("ts", 0) for e in sess), default=0)) / 60
        for sess in sessions
    ]
    used_graph = [
        any(e.get("type") == "graph_query" for e in sess)
        for sess in sessions
    ]
    read_paths = [
        any(e.get("type") == "read_path" for e in sess)
        for sess in sessions
    ]

    def safe_mean(lst: list) -> float:
        return round(sum(lst) / len(lst), 2) if lst else 0.0

    return {
        "n_sessions":             len(sessions),
        "n_events_total":         len(events),
        "avg_queries_per_session": safe_mean(queries_per_session),
        "avg_session_length_min": safe_mean(session_lengths_min),
        "pct_using_graph":        round(sum(used_graph) / len(used_graph) * 100, 1) if used_graph else 0.0,
        "pct_reading_paths":      round(sum(read_paths) / len(read_paths) * 100, 1) if read_paths else 0.0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Parse backend logs for user-study usage metrics")
    p.add_argument("--backend-logs", required=True, help="Directory of backend log files")
    p.add_argument("--user-ids",     required=True, help="CSV file with participant user_id column")
    p.add_argument("--output",       required=True, help="Output JSON")
    p.add_argument("--emit-markdown",default=None)
    args = p.parse_args()

    logs_dir = Path(args.backend_logs)
    if not logs_dir.exists():
        print(f"  ⚠  Backend logs directory not found: {logs_dir}")
        result = {"note": f"logs directory not found: {logs_dir}"}
    else:
        participants = _load_participants(args.user_ids)
        print(f"  Loaded {len(participants)} participant IDs")

        all_events: list[dict] = []
        for lf in sorted(logs_dir.glob("**/*.log")) or sorted(logs_dir.glob("**/*.jsonl")):
            evs = _parse_log_file(lf, participants)
            all_events.extend(evs)
            print(f"  Loaded {len(evs)} events from {lf.name}")

        result = _compute_metrics(all_events)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  ✅ User-study metrics → {args.output}")

    if args.emit_markdown:
        lines = ["# User Study Usage Metrics", ""]
        for k, v in result.items():
            lines.append(f"- **{k}**: {v}")
        Path(args.emit_markdown).parent.mkdir(parents=True, exist_ok=True)
        with open(args.emit_markdown, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"  📄 User-study markdown → {args.emit_markdown}")


if __name__ == "__main__":
    main()
