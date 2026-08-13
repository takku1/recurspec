"""Worker Pool: dispatch one node's loop turn to an isolated agent runtime.

Implements docs/architecture/spec-runner/worker-pool/SYSTEM.md. This module owns the
policy - budget enforcement, phase-to-tier routing, maker != checker, and the
concurrency cap - not a concrete agent-runtime integration. The node's own §8 names the
Claude Agent SDK as the selected runtime (ADOPT), but its package name and version must
be read from live documentation before pinning it, which this implementation cannot do
from here; asserting an unverified pin would violate the project's own evidence policy
(see docs/research/foundations.md). Callers inject a ``RuntimeCall`` instead - in
production, an SDK-backed callable; here, the pool's own policy is fully implemented and
tested against a fake runtime, matching how workers.py's fit gap is described in §8:
"the SDK does not know Recurspec's phases, tiering policy, or budget rule" - that gap,
and only that gap, is this module.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# FRAME and CHECK are mechanical/structural; RESOLVE and SPECIFY need the capable tier.
MECHANICAL_PHASES = {"frame", "check"}
CAPABLE_PHASES = {"resolve", "specify"}

# A worker "produces" a node in these phases; CHECK reviews what was produced.
PRODUCE_PHASES = {"frame", "resolve", "specify"}
CHECK_PHASES = {"check"}
_AUTHORIZATION_ISSUER = object()


@dataclass(frozen=True)
class MergeAuthorization:
    node_id: str
    candidate_branch: str
    candidate_oid: str
    maker_id: str
    checker_id: str
    _issuer: object

    def __post_init__(self) -> None:
        if self._issuer is not _AUTHORIZATION_ISSUER:
            raise ValueError("merge authorizations must be issued from Worker Pool state")


def load_merge_authorization(path: str | Path, node_id: str) -> MergeAuthorization:
    """Load a completed maker/checker record written by ``WorkerPool``."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    record = payload.get(node_id)
    if not isinstance(record, dict):
        raise ValueError(f"no Worker Pool authorization state for {node_id!r}")
    maker = record.get("maker_id")
    checker = record.get("checker_id")
    if not isinstance(maker, str) or not isinstance(checker, str) or not maker or not checker:
        raise ValueError(f"Worker Pool authorization for {node_id!r} is incomplete")
    if maker == checker:
        raise ValueError("maker and checker must differ")
    branch = record.get("candidate_branch")
    oid = record.get("candidate_oid")
    if not isinstance(branch, str) or not isinstance(oid, str) or not branch or not oid:
        raise ValueError(f"Worker Pool authorization for {node_id!r} lacks Candidate identity")
    return MergeAuthorization(node_id, branch, oid, maker, checker, _AUTHORIZATION_ISSUER)


def tier_for_phase(phase: str) -> str:
    """Route mechanical phases to the cheap tier, RESOLVE/SPECIFY to the capable one."""
    if phase in MECHANICAL_PHASES:
        return "cheap"
    if phase in CAPABLE_PHASES:
        return "capable"
    raise ValueError(f"unknown phase {phase!r}")


@dataclass(frozen=True)
class RuntimeResponse:
    """What a concrete agent-runtime adapter returns for one call."""

    body: Any
    tokens_in: int
    tokens_out: int
    ms: float


@dataclass(frozen=True)
class WorkerResult:
    outcome: str  # "ok" | "budget_exceeded" | "tool_error" | "refused"
    body: Any | None
    tokens_in: int
    tokens_out: int
    ms: float


# (packet, phase, tier) -> RuntimeResponse. The packet is the only thing a runtime call
# ever receives - never a tree_root or file path (invariant 1).
RuntimeCall = Callable[[Any, str, str], RuntimeResponse]


@dataclass(frozen=True)
class DispatchJob:
    node_id: str
    packet: Any
    phase: str
    worker_id: str
    max_tokens_per_node: int
    candidate_branch: str | None = None
    candidate_oid: str | None = None


class WorkerPool:
    """Dispatches node turns against an injected runtime, enforcing budget, tier
    routing, maker != checker, and a concurrency cap.

    Stateless between nodes except for the maker registry needed to enforce
    maker != checker - that registry is this pool's one piece of run state.
    """

    def __init__(
        self, runtime: RuntimeCall, concurrency: int, authorization_state: str | Path | None = None
    ):
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._runtime = runtime
        self._concurrency = concurrency
        self._semaphore = threading.Semaphore(concurrency)
        self._maker_lock = threading.Lock()
        self._maker_of: dict[str, str] = {}
        self._checker_of: dict[str, str] = {}
        self._checked_candidate: dict[str, tuple[str, str]] = {}
        self._authorization_state = Path(authorization_state) if authorization_state else None

    def _persist_authorizations(self) -> None:
        if self._authorization_state is None:
            return
        payload = {
            node_id: {"maker_id": maker, "checker_id": self._checker_of.get(node_id)}
            for node_id, maker in sorted(self._maker_of.items())
        }
        self._authorization_state.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._authorization_state.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        temporary.replace(self._authorization_state)

    def merge_authorization(self, node_id: str) -> MergeAuthorization:
        with self._maker_lock:
            maker = self._maker_of.get(node_id)
            checker = self._checker_of.get(node_id)
            candidate = self._checked_candidate.get(node_id)
        if maker is None or checker is None or candidate is None:
            raise ValueError(f"node {node_id!r} has no completed maker/checker authorization")
        candidate_branch, candidate_oid = candidate
        authorization = MergeAuthorization(
            node_id,
            candidate_branch,
            candidate_oid,
            maker,
            checker,
            _AUTHORIZATION_ISSUER,
        )
        if self._authorization_state is not None:
            payload = json.loads(self._authorization_state.read_text(encoding="utf-8"))
            payload[node_id].update(
                candidate_branch=candidate_branch, candidate_oid=candidate_oid
            )
            self._authorization_state.write_text(
                json.dumps(payload, sort_keys=True), encoding="utf-8"
            )
        return authorization

    def dispatch(
        self,
        node_id: str,
        packet: Any,
        phase: str,
        worker_id: str,
        max_tokens_per_node: int,
        candidate_branch: str | None = None,
        candidate_oid: str | None = None,
    ) -> WorkerResult:
        """Run one node turn, or refuse without calling the runtime at all."""
        if phase in CHECK_PHASES:
            if not candidate_branch or not candidate_oid:
                return WorkerResult(
                    outcome="refused", body=None, tokens_in=0, tokens_out=0, ms=0.0
                )
            with self._maker_lock:
                maker = self._maker_of.get(node_id)
            if maker == worker_id:
                return WorkerResult(outcome="refused", body=None, tokens_in=0, tokens_out=0, ms=0.0)

        tier = tier_for_phase(phase)
        with self._semaphore:
            response = self._runtime(packet, phase, tier)

        spend = response.tokens_in + response.tokens_out
        if spend >= max_tokens_per_node:
            # Refuse rather than guess: discard the body so a partial spec can never
            # surface as if it were complete (invariant 3).
            return WorkerResult(
                outcome="budget_exceeded",
                body=None,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                ms=response.ms,
            )
        with self._maker_lock:
            if phase in PRODUCE_PHASES:
                self._maker_of[node_id] = worker_id
            if phase in CHECK_PHASES:
                self._checker_of[node_id] = worker_id
                self._checked_candidate[node_id] = (candidate_branch, candidate_oid)
            self._persist_authorizations()
        return WorkerResult(
            outcome="ok",
            body=response.body,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            ms=response.ms,
        )

    def dispatch_many(self, jobs: list[DispatchJob]) -> list[WorkerResult]:
        """Run independent jobs concurrently, never exceeding the configured cap
        (invariant 5). ``dispatch``'s own semaphore is the authoritative cap - this
        is a convenience for the common "many siblings at once" case."""
        with ThreadPoolExecutor(max_workers=self._concurrency) as executor:
            futures = [
                executor.submit(
                    self.dispatch,
                    job.node_id,
                    job.packet,
                    job.phase,
                    job.worker_id,
                    job.max_tokens_per_node,
                    job.candidate_branch,
                    job.candidate_oid,
                )
                for job in jobs
            ]
            return [future.result() for future in futures]
