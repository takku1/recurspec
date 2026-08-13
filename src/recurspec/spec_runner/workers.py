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

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

# FRAME and CHECK are mechanical/structural; RESOLVE and SPECIFY need the capable tier.
MECHANICAL_PHASES = {"frame", "check"}
CAPABLE_PHASES = {"resolve", "specify"}

# A worker "produces" a node in these phases; CHECK reviews what was produced.
PRODUCE_PHASES = {"frame", "resolve", "specify"}
CHECK_PHASES = {"check"}


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


class WorkerPool:
    """Dispatches node turns against an injected runtime, enforcing budget, tier
    routing, maker != checker, and a concurrency cap.

    Stateless between nodes except for the maker registry needed to enforce
    maker != checker - that registry is this pool's one piece of run state.
    """

    def __init__(self, runtime: RuntimeCall, concurrency: int):
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._runtime = runtime
        self._concurrency = concurrency
        self._semaphore = threading.Semaphore(concurrency)
        self._maker_lock = threading.Lock()
        self._maker_of: dict[str, str] = {}

    def dispatch(
        self,
        node_id: str,
        packet: Any,
        phase: str,
        worker_id: str,
        max_tokens_per_node: int,
    ) -> WorkerResult:
        """Run one node turn, or refuse without calling the runtime at all."""
        if phase in CHECK_PHASES:
            with self._maker_lock:
                maker = self._maker_of.get(node_id)
            if maker == worker_id:
                return WorkerResult(outcome="refused", body=None, tokens_in=0, tokens_out=0, ms=0.0)

        tier = tier_for_phase(phase)
        with self._semaphore:
            response = self._runtime(packet, phase, tier)

        if phase in PRODUCE_PHASES:
            with self._maker_lock:
                self._maker_of[node_id] = worker_id

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
                )
                for job in jobs
            ]
            return [future.result() for future in futures]
