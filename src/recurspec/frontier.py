"""Publish Research Frontiers to a local markdown tracker (R-303).

Incomplete product work stays in ROADMAP.md. This adapter writes claimable
Research Frontier tickets linked to a Contract Node. It does not invent a
second readiness list.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .contract import ContractInstrumentError, build_tree_index, decision_class

CONTRACT_FIELD = re.compile(r"\*\*Contract:\*\*\s+`([^`]+)`")
ROADMAP_RE = re.compile(r"\bR-\d+\b")
OPEN_QUESTIONS_RE = re.compile(
    r"-\s+\*\*Open questions:\*\*\s*(.+?)(?=^\s*-\s+\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)

RemotePublisher = Callable[[str, str], str]


class FrontierInstrumentError(RuntimeError):
    """Frontier publication or verification could not run without guessing."""


@dataclass(frozen=True)
class FrontierTicket:
    node_id: str
    title: str
    contract_path: str
    roadmap_ids: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class PublishReport:
    written: tuple[Path, ...]
    remote_ids: tuple[str, ...]


@dataclass(frozen=True)
class FrontierCheck:
    ticket_count: int
    broken: tuple[str, ...]

    @property
    def integrity(self) -> float:
        if self.ticket_count == 0:
            return 1.0
        return (self.ticket_count - len(self.broken)) / self.ticket_count


def _open_questions(section: str) -> str:
    match = OPEN_QUESTIONS_RE.search(section)
    return match.group(1).strip() if match else ""


def _slug(node_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", node_id).strip("-").lower() or "node"


def discover_frontiers(tree_root: str | Path) -> tuple[FrontierTicket, ...]:
    """Emit a Research Frontier for each DEFER leaf or leaf that cites a ROADMAP id."""
    try:
        index = build_tree_index(tree_root)
    except ContractInstrumentError as exc:
        raise FrontierInstrumentError(str(exc)) from exc
    tickets: list[FrontierTicket] = []
    for node in index.values():
        if not node["atomic_leaf"]:
            continue
        klass = decision_class(node["sections"]) or ""
        open_q = _open_questions(node["sections"].get("8", ""))
        refs = tuple(ROADMAP_RE.findall(open_q))
        if klass != "DEFER" and not refs:
            continue
        contract_path = Path(node["path"]).resolve()
        repo_relative = contract_path.as_posix()
        for parent in contract_path.parents:
            if (parent / "ROADMAP.md").is_file() or (parent / "pyproject.toml").is_file():
                repo_relative = contract_path.relative_to(parent).as_posix()
                break
        title = f"Research Frontier: {node['node_id']}"
        roadmap = ", ".join(refs) if refs else "none"
        body = (
            f"# {title}\n\n"
            f"- **Kind:** research\n"
            f"- **Contract:** `{repo_relative}`\n"
            f"- **Decision class:** {klass or 'unknown'}\n"
            f"- **Roadmap:** {roadmap}\n"
        )
        tickets.append(
            FrontierTicket(node["node_id"], title, repo_relative, refs, body)
        )
    return tuple(tickets)


def publish_frontiers(
    tree_root: str | Path,
    destination: str | Path,
    *,
    remote: RemotePublisher | None = None,
) -> PublishReport:
    tickets = discover_frontiers(tree_root)
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    remote_ids: list[str] = []
    for ticket in tickets:
        path = dest / f"{_slug(ticket.node_id)}.md"
        path.write_text(ticket.body, encoding="utf-8")
        written.append(path)
        if remote is not None:
            remote_ids.append(remote(ticket.title, ticket.body))
    index_lines = ["# Research Frontiers\n", ""]
    for ticket in tickets:
        index_lines.append(f"- [{ticket.title}]({_slug(ticket.node_id)}.md)")
    (dest / "MAP.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return PublishReport(tuple(written), tuple(remote_ids))


def check_frontiers(destination: str | Path, repository: str | Path) -> FrontierCheck:
    dest = Path(destination)
    repository = Path(repository)
    if not dest.is_dir():
        return FrontierCheck(0, ())
    broken: list[str] = []
    count = 0
    for ticket in sorted(dest.glob("*.md")):
        if ticket.name == "MAP.md":
            continue
        count += 1
        match = CONTRACT_FIELD.search(ticket.read_text(encoding="utf-8"))
        if match is None or not (repository / match.group(1)).is_file():
            broken.append(ticket.name)
    return FrontierCheck(count, tuple(broken))


def github_issue_publisher(runner: Callable[..., object] | None = None) -> RemotePublisher:
    """Publish via ``gh issue create``. Refuses if ``gh`` is missing or fails."""
    import shutil
    import subprocess

    def publish(title: str, body: str) -> str:
        execute = runner
        gh = "gh"
        if execute is None:
            resolved = shutil.which("gh")
            if resolved is None:
                raise FrontierInstrumentError("gh is not on PATH; cannot publish a remote issue")
            gh = resolved

            def execute(args: list[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.run(  # noqa: S603 - gh resolved to an absolute path above; no shell
                    args, capture_output=True, text=True, check=False
                )

        result = execute([gh, "issue", "create", "--title", title, "--body", body])
        if getattr(result, "returncode", 1) != 0:
            err = getattr(result, "stderr", "") or "gh issue create failed"
            raise FrontierInstrumentError(str(err).strip())
        url = (getattr(result, "stdout", "") or "").strip()
        if not url:
            raise FrontierInstrumentError("gh issue create returned no issue URL")
        return url

    return publish
