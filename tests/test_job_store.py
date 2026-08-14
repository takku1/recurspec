import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from recurspec.spec_runner.store import JobStore

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def _store(tmp_path: Path) -> JobStore:
    return JobStore(tmp_path / "job-store.sqlite3")


def test_atomic_claim_hands_each_ready_node_to_exactly_one_worker(tmp_path: Path):
    store = _store(tmp_path)
    for index in range(8):
        store.upsert_node(f"node-{index}", None, "BUILD", contract_hash=f"hash-{index}")

    claims: list[str] = []
    lock = threading.Lock()

    def worker(worker_id: str) -> None:
        while True:
            node_id = store.claim_next_ready(worker_id)
            if node_id is None:
                return
            with lock:
                claims.append(node_id)

    threads = [threading.Thread(target=worker, args=(f"worker-{i}",)) for i in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert sorted(claims) == [f"node-{index}" for index in range(8)]
    assert len(claims) == len(set(claims))


def test_claim_returns_none_once_every_ready_node_is_claimed(tmp_path: Path):
    store = _store(tmp_path)
    store.upsert_node("only-node", None, "BUILD", contract_hash="hash-1")

    assert store.claim_next_ready("worker-a") == "only-node"
    assert store.claim_next_ready("worker-b") is None


def test_contract_hash_change_dirties_the_node_and_its_parent_but_not_siblings(
    tmp_path: Path,
):
    store = _store(tmp_path)
    store.upsert_node("parent", None, None, contract_hash="parent-hash")
    store.upsert_node("child-a", "parent", "BUILD", contract_hash="a-hash-1")
    store.upsert_node("child-b", "parent", "BUILD", contract_hash="b-hash-1")

    assert store.dirty_nodes() == set()

    store.upsert_node("child-a", "parent", "BUILD", contract_hash="a-hash-2")

    assert store.dirty_nodes() == {"child-a", "parent"}


def test_upserting_with_the_same_hash_does_not_dirty_anything(tmp_path: Path):
    store = _store(tmp_path)
    store.upsert_node("node", None, "BUILD", contract_hash="stable-hash")

    store.upsert_node("node", None, "BUILD", contract_hash="stable-hash")

    assert store.dirty_nodes() == set()


def test_survey_ttl_expiry_reports_stale_not_a_hit(tmp_path: Path):
    store = _store(tmp_path)
    fetched_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.record_survey("managed-oidc-idp", "Google Identity Platform", ["vendor docs"], fetched_at)

    fresh_lookup = store.get_survey(
        "managed-oidc-idp", ttl_days=30, now=fetched_at + timedelta(days=5)
    )
    stale_lookup = store.get_survey(
        "managed-oidc-idp", ttl_days=30, now=fetched_at + timedelta(days=45)
    )

    assert fresh_lookup.status == "hit"
    assert fresh_lookup.result == "Google Identity Platform"
    assert stale_lookup.status == "stale"
    assert stale_lookup.result is None


def test_survey_lookup_is_a_miss_when_never_recorded(tmp_path: Path):
    store = _store(tmp_path)

    assert store.get_survey("never-surveyed", ttl_days=30).status == "miss"


def test_export_tree_json_reflects_current_node_state(tmp_path: Path):
    store = _store(tmp_path)
    store.upsert_node("parent", None, None, contract_hash="parent-hash")
    store.upsert_node("child", "parent", "BUILD", contract_hash="child-hash-1")
    store.upsert_node("child", "parent", "BUILD", contract_hash="child-hash-2")

    projection = store.export_tree_json()

    nodes_by_id = {node["node_id"]: node for node in projection["nodes"]}
    assert nodes_by_id["child"]["parent_id"] == "parent"
    assert nodes_by_id["child"]["contract_hash"] == "child-hash-2"
    assert nodes_by_id["child"]["dirty"] is True
    assert nodes_by_id["parent"]["dirty"] is True


def test_full_rebuild_from_markdown_reproduces_the_store(tmp_path: Path):
    store = _store(tmp_path)

    first = store.rebuild_from_tree(FIXTURES / "valid-tree")
    lost_store = JobStore(tmp_path / "job-store-2.sqlite3")
    second = lost_store.rebuild_from_tree(FIXTURES / "valid-tree")

    assert first.node_count == second.node_count == 3
    assert store._all_node_ids() == lost_store._all_node_ids()
    assert store._all_node_ids() == {"SYSTEM.md", "publish/SYSTEM.md", "transform/SYSTEM.md"}


def test_rebuild_from_tree_commits_as_a_single_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A rebuild is one atomic swap to the markdown-derived state, not one commit per
    node: opening a fresh connection/transaction per node scales connection and lock
    overhead with tree size, and a crash between per-node commits would otherwise leave
    the store in a mix of old and new state that is neither."""
    store = _store(tmp_path)
    original_connect = store._connect
    connections: list[object] = []

    def counting_connect(*args, **kwargs):
        conn = original_connect(*args, **kwargs)
        connections.append(conn)
        return conn

    monkeypatch.setattr(store, "_connect", counting_connect)

    report = store.rebuild_from_tree(FIXTURES / "valid-tree")

    assert report.node_count == 3
    assert len(connections) == 1


def test_rebuild_from_tree_rolls_back_when_a_node_upsert_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A crash mid-rebuild must leave the prior store unchanged. Per-node commits
    would persist the first upserted tree node and leave stale rows that the
    interrupted rebuild never reached."""
    store = _store(tmp_path)
    store.upsert_node("stale-node", None, "BUILD", contract_hash="stale-hash")
    before = store.export_tree_json()

    original = store._upsert_node
    seen = {"count": 0}

    def fail_after_first(conn, *args, **kwargs):
        seen["count"] += 1
        if seen["count"] > 1:
            raise RuntimeError("injected mid-rebuild failure")
        return original(conn, *args, **kwargs)

    monkeypatch.setattr(store, "_upsert_node", fail_after_first)

    with pytest.raises(RuntimeError, match="injected mid-rebuild failure"):
        store.rebuild_from_tree(FIXTURES / "valid-tree")

    assert store.export_tree_json() == before
    assert store._all_node_ids() == {"stale-node"}


def test_nodes_table_is_indexed_by_status_for_claim_next_ready(tmp_path: Path):
    store = _store(tmp_path)
    conn = store._connect()
    try:
        table = conn.execute(
            "SELECT tbl_name FROM sqlite_master WHERE type = 'index' AND name = ?",
            ("idx_nodes_status",),
        ).fetchone()
        columns = [
            row[2] for row in conn.execute("PRAGMA index_info('idx_nodes_status')")
        ]
    finally:
        conn.close()
    assert table == ("nodes",)
    assert columns == ["status"]


def test_rebuild_refuses_an_invalid_tree_rather_than_guess(tmp_path: Path):
    store = _store(tmp_path)
    invalid_tree = tmp_path / "broken-tree"
    invalid_tree.mkdir()
    (invalid_tree / "SYSTEM.md").write_text("# Broken (L0)\nno contract marker\n", encoding="utf-8")

    with pytest.raises(Exception):
        store.rebuild_from_tree(invalid_tree)


def test_rebuild_discards_a_stored_row_that_disagrees_with_markdown(tmp_path: Path):
    store = _store(tmp_path)
    store.rebuild_from_tree(FIXTURES / "valid-tree")

    # Corrupt a stored row directly, simulating drift between the store and reality.
    store.upsert_node("transform/SYSTEM.md", "SYSTEM.md", "WRONG-CLASS", contract_hash="corrupted")

    store.rebuild_from_tree(FIXTURES / "valid-tree")

    conn = store._connect()
    try:
        row = conn.execute(
            "SELECT class, contract_hash FROM nodes WHERE node_id = ?", ("transform/SYSTEM.md",)
        ).fetchone()
    finally:
        conn.close()
    assert row[0] != "WRONG-CLASS"
    assert row[1] != "corrupted"


def test_rebuild_removes_nodes_no_longer_present_in_the_tree(tmp_path: Path):
    import shutil

    tree = tmp_path / "tree"
    shutil.copytree(FIXTURES / "valid-tree", tree)
    store = _store(tmp_path)
    store.rebuild_from_tree(tree)
    assert "publish/SYSTEM.md" in store._all_node_ids()

    shutil.rmtree(tree / "publish")
    root_system_md = tree / "SYSTEM.md"
    root_system_md.write_text(
        root_system_md.read_text(encoding="utf-8")
        .replace("- [Publish](publish/SYSTEM.md)\n", "")
        .replace("- **Outputs:** `artifact`", "- **Outputs:** `transformed`"),
        encoding="utf-8",
    )

    report = store.rebuild_from_tree(tree)

    assert report.removed == ("publish/SYSTEM.md",)
    assert "publish/SYSTEM.md" not in store._all_node_ids()
