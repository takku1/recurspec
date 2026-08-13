import threading
import time
from dataclasses import dataclass

import pytest

from recurspec.spec_runner.workers import (
    DispatchJob,
    RuntimeResponse,
    WorkerPool,
    load_merge_authorization,
    tier_for_phase,
)


@dataclass(frozen=True)
class FakePacket:
    """Deliberately has no path/tree_root field - only what context-packer really
    produces (all strings). If a worker could reach the filesystem, this fixture
    would have to carry a path for it to leak."""

    contract_card: str
    own_draft: str


def test_tier_for_phase_routes_mechanical_cheap_and_resolve_capable():
    assert tier_for_phase("frame") == "cheap"
    assert tier_for_phase("check") == "cheap"
    assert tier_for_phase("resolve") == "capable"
    assert tier_for_phase("specify") == "capable"


def test_tier_for_phase_rejects_an_unknown_phase():
    with pytest.raises(ValueError):
        tier_for_phase("not-a-real-phase")


def test_completed_independent_check_persists_merge_authorization(tmp_path):
    state = tmp_path / "worker-authorizations.json"
    pool = WorkerPool(
        lambda *_args: RuntimeResponse({}, 1, 1, 1.0),
        concurrency=1,
        authorization_state=state,
    )
    pool.dispatch("node-1", {}, "frame", "maker", 100)
    pool.dispatch("node-1", {}, "check", "checker", 100, "candidate/node-1", "abc123")

    issued = pool.merge_authorization("node-1")
    authorization = load_merge_authorization(state, "node-1")

    assert authorization.maker_id == "maker"
    assert authorization.checker_id == "checker"
    assert authorization.candidate_branch == "candidate/node-1"
    assert authorization.candidate_oid == "abc123"
    assert authorization == issued


def test_budget_rejected_producer_cannot_establish_merge_authorization():
    pool = WorkerPool(
        lambda *_args: RuntimeResponse({}, 50, 50, 1.0),
        concurrency=1,
    )

    assert pool.dispatch("node-1", {}, "frame", "maker", 100).outcome == "budget_exceeded"
    pool.dispatch("node-1", {}, "check", "checker", 101, "candidate/node-1", "abc123")

    with pytest.raises(ValueError, match="no completed maker/checker authorization"):
        pool.merge_authorization("node-1")


def test_worker_only_ever_receives_the_packet_never_a_filesystem_path():
    received: list[tuple] = []

    def runtime(packet, phase, tier):
        received.append((packet, phase, tier))
        return RuntimeResponse(body="ok-body", tokens_in=10, tokens_out=10, ms=5.0)

    pool = WorkerPool(runtime=runtime, concurrency=1)
    packet = FakePacket(contract_card="CARD", own_draft="DRAFT")

    pool.dispatch("node-a", packet, "frame", "worker-1", max_tokens_per_node=1000)

    assert len(received) == 1
    received_packet, phase, tier = received[0]
    assert received_packet is packet
    assert phase == "frame"
    assert tier == "cheap"
    # The runtime call signature is (packet, phase, tier) - structurally incapable of
    # forwarding a tree_root or path even if one existed upstream.
    assert not hasattr(received_packet, "path")
    assert not hasattr(received_packet, "tree_root")


def test_budget_exceeded_discards_the_body_rather_than_return_a_partial_node():
    def runtime(packet, phase, tier):
        return RuntimeResponse(body="a-partial-spec", tokens_in=900, tokens_out=200, ms=5.0)

    pool = WorkerPool(runtime=runtime, concurrency=1)

    result = pool.dispatch(
        "node-a", FakePacket("CARD", "DRAFT"), "resolve", "worker-1", max_tokens_per_node=1000
    )

    assert result.outcome == "budget_exceeded"
    assert result.body is None


def test_within_budget_returns_ok_with_the_body():
    def runtime(packet, phase, tier):
        return RuntimeResponse(body="a-complete-spec", tokens_in=10, tokens_out=10, ms=5.0)

    pool = WorkerPool(runtime=runtime, concurrency=1)

    result = pool.dispatch(
        "node-a", FakePacket("CARD", "DRAFT"), "resolve", "worker-1", max_tokens_per_node=1000
    )

    assert result.outcome == "ok"
    assert result.body == "a-complete-spec"


def test_maker_cannot_check_the_node_it_produced():
    def runtime(packet, phase, tier):
        return RuntimeResponse(body="body", tokens_in=1, tokens_out=1, ms=1.0)

    pool = WorkerPool(runtime=runtime, concurrency=1)

    produced = pool.dispatch(
        "node-a", FakePacket("CARD", "DRAFT"), "resolve", "worker-1", max_tokens_per_node=1000
    )
    same_worker_check = pool.dispatch(
        "node-a", FakePacket("CARD", "DRAFT"), "check", "worker-1", 1000,
        "candidate/node-a", "abc123"
    )
    different_worker_check = pool.dispatch(
        "node-a", FakePacket("CARD", "DRAFT"), "check", "worker-2", 1000,
        "candidate/node-a", "abc123"
    )

    assert produced.outcome == "ok"
    assert same_worker_check.outcome == "refused"
    assert different_worker_check.outcome == "ok"


def test_concurrency_cap_is_never_exceeded():
    active = 0
    max_active = 0
    lock = threading.Lock()

    def runtime(packet, phase, tier):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return RuntimeResponse(body="ok", tokens_in=1, tokens_out=1, ms=1.0)

    pool = WorkerPool(runtime=runtime, concurrency=3)
    jobs = [
        DispatchJob(
            node_id=f"node-{i}",
            packet=FakePacket("CARD", "DRAFT"),
            phase="frame",
            worker_id=f"worker-{i}",
            max_tokens_per_node=1000,
        )
        for i in range(9)
    ]

    results = pool.dispatch_many(jobs)

    assert len(results) == 9
    assert all(result.outcome == "ok" for result in results)
    assert max_active <= 3


def test_concurrency_must_be_at_least_one():
    with pytest.raises(ValueError):
        WorkerPool(runtime=lambda packet, phase, tier: None, concurrency=0)
