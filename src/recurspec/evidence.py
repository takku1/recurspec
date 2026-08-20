#!/usr/bin/env python3
"""Append Recurspec evidence events to ``.recurspec/evidence/<module>/log.jsonl``."""

import datetime
import json
import os
from typing import Any

EVIDENCE_STAGES = ["Unknown", "Observed", "Sampled", "Inferred", "Measured", "Proved", "Refuted"]


def log_event(
    module: str,
    event_type: str,
    metrics: dict[str, Any],
    evidence_stage: str = "Measured",
    branch: str = "main",
    verdict: str | None = None,
    reason: str | None = None,
    log_dir: str = ".recurspec/evidence",
) -> str:
    if evidence_stage not in EVIDENCE_STAGES:
        raise ValueError(
            f"Invalid EvidenceStage: {evidence_stage}. Must be one of {EVIDENCE_STAGES}"
        )

    comp_dir = os.path.join(log_dir, module)
    os.makedirs(comp_dir, exist_ok=True)
    log_file = os.path.join(comp_dir, "log.jsonl")

    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event_type": event_type,
        "module": module,
        "branch": branch,
        "evidence_stage": evidence_stage,
        "metrics": metrics,
    }
    if verdict:
        entry["verdict"] = verdict
    if reason:
        entry["reason"] = reason

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return log_file


_CORPUS_KEEP = ("event_type", "verdict", "evidence_stage", "ts")


class RecommendationError(RuntimeError):
    """A Decision Class recommendation would be invented from redacted or missing data."""


def recommend_decision_class(
    corpus_path: str | os.PathLike[str] | None = None,
) -> list[dict[str, Any]]:
    """Refuse to recommend a Decision Class without comparable outcome data.

    The redacted corpus omits reason, branch, metric values, and Decision Class.
    Comparable-outcome recommendations stay blocked until the roadmap studies
    produce a corpus that actually carries the required fields.
    """
    del corpus_path
    raise RecommendationError(
        "the corpus redacts Decision Class, reasons, and metric values; "
        "refusing to invent a recommendation"
    )


def export_decision_corpus(
    log_dir: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    opt_in: bool,
) -> int:
    """Write a redacted decision corpus. Refuses unless ``opt_in`` is true.

    Drops source, prompts, secrets, branch names, reasons, and metric values.
    Does not invent rows when a log is missing.
    """
    if not opt_in:
        raise ValueError("decision-corpus export requires explicit project-level opt-in")
    root = os.fspath(log_dir)
    dest = os.fspath(destination)
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    written = 0
    with open(dest, "w", encoding="utf-8") as out:
        if not os.path.isdir(root):
            return 0
        for dirpath, _dirs, files in os.walk(root):
            if "log.jsonl" not in files:
                continue
            log_path = os.path.join(dirpath, "log.jsonl")
            with open(log_path, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    redacted = {key: event[key] for key in _CORPUS_KEEP if key in event}
                    redacted["metrics_present"] = bool(event.get("metrics"))
                    out.write(json.dumps(redacted, sort_keys=True) + "\n")
                    written += 1
    return written
