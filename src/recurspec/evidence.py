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
