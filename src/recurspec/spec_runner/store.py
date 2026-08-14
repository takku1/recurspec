"""Job Store: durable Runner state over SQLite.

Implements docs/architecture/spec-runner/job-store/SYSTEM.md: node status, contract
hashes, the ready queue, and a TTL'd capability-survey cache, transactionally under
concurrent workers. The store is a derived cache - it must always be reconstructible
from the markdown tree, and markdown wins on disagreement (see ``rebuild_from_tree``).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..contract import build_tree_index, decision_class

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    parent_id TEXT,
    class TEXT,
    status TEXT NOT NULL,
    contract_hash TEXT NOT NULL,
    dirty INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);

CREATE TABLE IF NOT EXISTS claims (
    node_id TEXT PRIMARY KEY REFERENCES nodes(node_id) ON DELETE CASCADE,
    worker_id TEXT NOT NULL,
    claimed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS survey_cache (
    capability_key TEXT PRIMARY KEY,
    result TEXT NOT NULL,
    sources TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dirty_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    old_hash TEXT,
    new_hash TEXT,
    marked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

SCHEMA_VERSION = "1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_contract_hash(contract: dict[str, Any]) -> str:
    """Hash a node's contract surface: §1 responsibility, §3 interfaces, §8 class +
    selection. Editing §2, §4, or §5 prose must not change this value."""
    sections = contract["sections"]
    canonical = "\x1f".join(
        (sections.get("1", ""), sections.get("3", ""), sections.get("8", ""))
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SurveyLookup:
    status: str  # "hit" | "stale" | "miss"
    result: str | None
    sources: tuple[str, ...]


@dataclass(frozen=True)
class RebuildReport:
    node_count: int
    removed: tuple[str, ...]


class JobStore:
    """A durable, transactional cache over one SQLite file.

    Every write opens its own short-lived connection under an immediate
    transaction, so the store is safe to use from multiple threads or
    processes pointed at the same file without any shared connection state.
    """

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._migrate()

    def _connect(self, *, immediate: bool = False) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        conn.execute("PRAGMA foreign_keys = ON")
        if immediate:
            conn.execute("BEGIN IMMEDIATE")
        return conn

    def _write(self, sql: str, params: tuple[Any, ...]) -> None:
        """Run one self-contained statement on its own short-lived connection."""
        conn = self._connect()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _migrate(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.execute(
                "INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('schema_version', ?)",
                (SCHEMA_VERSION,),
            )
        finally:
            conn.close()

    # -- node state ----------------------------------------------------

    def upsert_node(
        self,
        node_id: str,
        parent_id: str | None,
        node_class: str | None,
        contract_hash: str,
        status: str = "ready",
    ) -> None:
        """Insert or refresh a node's contract-derived fields.

        Runtime ``status`` is preserved on an existing node - only the initial
        insert uses the ``status`` argument. If the contract hash changed,
        marks this node and its parent dirty (never siblings; invariant 3).
        """
        conn = self._connect(immediate=True)
        try:
            self._upsert_node(conn, node_id, parent_id, node_class, contract_hash, status)
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def _upsert_node(
        self,
        conn: sqlite3.Connection,
        node_id: str,
        parent_id: str | None,
        node_class: str | None,
        contract_hash: str,
        status: str = "ready",
    ) -> None:
        """Same as ``upsert_node``, but on a caller-owned connection/transaction so a
        multi-node rebuild can commit as one atomic unit instead of one per node."""
        existing = conn.execute(
            "SELECT contract_hash FROM nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        conn.execute(
            """
            INSERT INTO nodes (node_id, parent_id, class, status, contract_hash, dirty)
            VALUES (?, ?, ?, ?, ?, 0)
            ON CONFLICT(node_id) DO UPDATE SET
                parent_id = excluded.parent_id,
                class = excluded.class,
                contract_hash = excluded.contract_hash
            """,
            (node_id, parent_id, node_class, status, contract_hash),
        )
        if existing is not None and existing[0] != contract_hash:
            self._mark_dirty(conn, node_id, existing[0], contract_hash)
            if parent_id is not None:
                self._mark_dirty(conn, parent_id, None, None)

    def _mark_dirty(
        self, conn: sqlite3.Connection, node_id: str, old_hash: str | None, new_hash: str | None
    ) -> None:
        conn.execute("UPDATE nodes SET dirty = 1 WHERE node_id = ?", (node_id,))
        conn.execute(
            "INSERT INTO dirty_log (node_id, old_hash, new_hash, marked_at) VALUES (?, ?, ?, ?)",
            (node_id, old_hash, new_hash, _now_iso()),
        )

    def clear_dirty(self, node_id: str) -> None:
        self._write("UPDATE nodes SET dirty = 0 WHERE node_id = ?", (node_id,))

    def dirty_nodes(self) -> set[str]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT node_id FROM nodes WHERE dirty = 1").fetchall()
            return {row[0] for row in rows}
        finally:
            conn.close()

    def _all_node_ids(self) -> set[str]:
        conn = self._connect()
        try:
            return {row[0] for row in conn.execute("SELECT node_id FROM nodes")}
        finally:
            conn.close()

    def export_tree_json(self) -> dict[str, Any]:
        """The derived ``tree.json`` projection: a snapshot of all node state,
        letting a scheduler plan without opening a single ``SYSTEM.md``. Gitignored
        and regenerable - never a second source of truth (spec-runner ADR-003)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT node_id, parent_id, class, status, contract_hash, dirty "
                "FROM nodes ORDER BY node_id"
            ).fetchall()
        finally:
            conn.close()
        return {
            "schema_version": SCHEMA_VERSION,
            "nodes": [
                {
                    "node_id": row[0],
                    "parent_id": row[1],
                    "class": row[2],
                    "status": row[3],
                    "contract_hash": row[4],
                    "dirty": bool(row[5]),
                }
                for row in rows
            ],
        }

    # -- claims ----------------------------------------------------------

    def claim_next_ready(self, worker_id: str) -> str | None:
        """Atomically hand at most one worker the next ready, unclaimed node
        (invariant 2). Safe under concurrent callers across threads or
        processes: BEGIN IMMEDIATE serializes writers at the SQLite level."""
        conn = self._connect(immediate=True)
        try:
            row = conn.execute(
                """
                SELECT n.node_id FROM nodes n
                LEFT JOIN claims c ON c.node_id = n.node_id
                WHERE n.status = 'ready' AND c.node_id IS NULL
                ORDER BY n.node_id
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.execute("COMMIT")
                return None
            node_id = row[0]
            conn.execute(
                "INSERT INTO claims (node_id, worker_id, claimed_at) VALUES (?, ?, ?)",
                (node_id, worker_id, _now_iso()),
            )
            conn.execute("COMMIT")
            return node_id
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def release(self, node_id: str) -> None:
        self._write("DELETE FROM claims WHERE node_id = ?", (node_id,))

    # -- capability-survey cache ------------------------------------------

    def record_survey(
        self,
        capability_key: str,
        result: str,
        sources: list[str],
        fetched_at: datetime | None = None,
    ) -> None:
        fetched = (fetched_at or datetime.now(timezone.utc)).isoformat()
        self._write(
            """
            INSERT INTO survey_cache (capability_key, result, sources, fetched_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(capability_key) DO UPDATE SET
                result = excluded.result,
                sources = excluded.sources,
                fetched_at = excluded.fetched_at
            """,
            (capability_key, result, json.dumps(sources), fetched),
        )

    def get_survey(
        self, capability_key: str, ttl_days: float, now: datetime | None = None
    ) -> SurveyLookup:
        """Return a cache hit only within ``ttl_days``; an expired row is
        reported ``stale``, never returned as a usable hit (invariant 4)."""
        now = now or datetime.now(timezone.utc)
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT result, sources, fetched_at FROM survey_cache WHERE capability_key = ?",
                (capability_key,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return SurveyLookup("miss", None, ())
        result, sources_json, fetched_at = row
        age_days = (now - datetime.fromisoformat(fetched_at)).total_seconds() / 86400
        if age_days > ttl_days:
            return SurveyLookup("stale", None, ())
        return SurveyLookup("hit", result, tuple(json.loads(sources_json)))

    # -- rebuild from markdown --------------------------------------------

    def rebuild_from_tree(self, tree_root: str | Path) -> RebuildReport:
        """Reconstruct node state from the markdown Contract Tree (invariant 1).

        Refuses to run against an invalid tree rather than guess (delegated to
        ``build_tree_index``). Any stored node absent from a fresh walk is
        discarded - markdown always wins (invariant 5).

        Runs as one transaction rather than one per node: besides the per-node
        connection/lock-acquire overhead that would otherwise scale with tree size, a
        rebuild is conceptually one atomic swap to the markdown-derived state, and a
        crash between per-node commits would otherwise leave the store in a mix of old
        and new state that is neither.
        """
        index = build_tree_index(tree_root)
        conn = self._connect(immediate=True)
        try:
            for node in index.values():
                self._upsert_node(
                    conn,
                    node_id=node["node_id"],
                    parent_id=node["parent_id"],
                    node_class=decision_class(node["sections"]),
                    contract_hash=compute_contract_hash(node),
                )
            existing_ids = {row[0] for row in conn.execute("SELECT node_id FROM nodes")}
            removed = tuple(sorted(existing_ids - set(index)))
            for node_id in removed:
                conn.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
        return RebuildReport(node_count=len(index), removed=removed)
