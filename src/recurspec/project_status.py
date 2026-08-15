"""Classify whether a repository already has a Recurspec Contract Tree."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .contract import VERSION_RE, ContractInstrumentError, Diagnostic, validate_contract
from .structure_gate import declared_probe_paths

TreeState = Literal["missing", "not_recurspec", "invalid", "valid"]
Route = Literal["design", "repair", "ready"]

DEFAULT_CONTRACT_ROOT = "docs/architecture"
EXTRA_CONTRACT_ROOTS = (".recurspec/contracts",)
RIVAL_REGISTRY_PATHS = (
    "docs/open-work.md",
    "docs/FEATURE_GAPS.md",
    "docs/architecture/FEATURE_GAPS.md",
    "FEATURE_GAPS.md",
)


class StatusInstrumentError(RuntimeError):
    """The status command could not inspect the requested repository."""


@dataclass(frozen=True)
class ExtraTreeStatus:
    root: str
    tree: TreeState
    system_md: int
    versioned: int
    unversioned: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "system_md": self.system_md,
            "tree": self.tree,
            "unversioned": list(self.unversioned),
            "versioned": self.versioned,
        }


@dataclass(frozen=True)
class ProjectStatus:
    repository: str
    contract_root: str
    tree: TreeState
    route: Route
    system_md: int
    versioned: int
    unversioned: tuple[str, ...]
    roadmap: bool
    recurspec_dir: bool
    checker: bool
    rival_registries: tuple[str, ...]
    diagnostics: tuple[Diagnostic, ...]
    missing_probes: tuple[str, ...]
    extra_trees: tuple[ExtraTreeStatus, ...]
    next_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "checker": "present" if self.checker else "missing",
            "contract_root": self.contract_root,
            "diagnostics": [item.as_dict() for item in self.diagnostics],
            "extra_trees": [item.as_dict() for item in self.extra_trees],
            "missing_probes": list(self.missing_probes),
            "next": self.next_action,
            "recurspec_dir": self.recurspec_dir,
            "repository": self.repository,
            "rival_registries": list(self.rival_registries),
            "roadmap": self.roadmap,
            "route": self.route,
            "system_md": self.system_md,
            "tree": self.tree,
            "unversioned": list(self.unversioned),
            "versioned": self.versioned,
        }


def _resolve_repository(repository: Path) -> Path:
    try:
        resolved = repository.resolve()
    except OSError as exc:
        raise StatusInstrumentError(f"repository path could not be resolved: {exc}") from exc
    if not resolved.is_dir():
        raise StatusInstrumentError(f"repository does not exist: {repository}")
    return resolved


def _resolve_under(repository: Path, relative: str) -> Path:
    candidate = (repository / relative).resolve()
    if candidate != repository and repository not in candidate.parents:
        raise StatusInstrumentError(
            f"contract root {relative!r} escapes the repository"
        )
    return candidate


def _repo_relative(repository: Path, path: Path) -> str:
    return path.resolve().relative_to(repository).as_posix()


def _is_versioned(path: Path) -> bool:
    try:
        return VERSION_RE.search(path.read_text(encoding="utf-8")) is not None
    except (OSError, UnicodeError) as exc:
        raise StatusInstrumentError(f"could not read {path}: {exc}") from exc


def _classify_contract_dir(
    repo: Path, contract_dir: Path
) -> tuple[TreeState, int, int, tuple[str, ...], tuple[Diagnostic, ...]]:
    if contract_dir.is_dir():
        system_paths = sorted(contract_dir.rglob("SYSTEM.md"), key=lambda item: item.as_posix())
    else:
        system_paths = []
    unversioned = tuple(
        _repo_relative(repo, path) for path in system_paths if not _is_versioned(path)
    )
    versioned_count = len(system_paths) - len(unversioned)
    diagnostics: tuple[Diagnostic, ...] = ()
    if not system_paths:
        tree: TreeState = "missing"
    elif unversioned:
        tree = "not_recurspec"
    else:
        try:
            result = validate_contract(contract_dir)
        except ContractInstrumentError as exc:
            raise StatusInstrumentError(str(exc)) from exc
        diagnostics = result.diagnostics
        tree = "valid" if result.valid else "invalid"
    return tree, len(system_paths), versioned_count, unversioned, diagnostics


def _missing_probes(repo: Path, contract_dir: Path) -> tuple[str, ...]:
    if not contract_dir.is_dir():
        return ()
    missing: list[str] = []
    for contract in sorted(contract_dir.rglob("SYSTEM.md"), key=lambda item: item.as_posix()):
        if not _is_versioned(contract):
            continue
        probes, unsafe = declared_probe_paths(contract, repository=repo)
        for declared in sorted(probes):
            if not (repo / declared).is_file():
                missing.append(declared)
        missing.extend(sorted(unsafe))
    return tuple(missing)


def _next_action(
    tree: TreeState,
    *,
    roadmap: bool,
    rival_registries: tuple[str, ...],
    missing_probes: tuple[str, ...],
    extra_trees: tuple[ExtraTreeStatus, ...],
) -> str:
    if tree == "missing":
        message = (
            "No Contract Tree at the contract root. Follow references/design.md "
            "and create ROADMAP.md."
        )
    elif tree == "not_recurspec":
        message = (
            "Existing SYSTEM.md files are not Recurspec contracts. "
            "Follow references/design.md. Treat them as source material; "
            "do not stamp the version marker onto an incomplete file."
        )
        if not roadmap:
            message += " Create ROADMAP.md as the sole Recurspec incomplete-work surface."
    elif tree == "invalid":
        message = (
            "Opted-in Contract Nodes failed validation. Run recurspec contract check "
            "and repair diagnostics before product work."
        )
    else:
        message = "Recurspec Contract Tree is valid. Apply the request-based skill routes."
        if not roadmap:
            message += " Create ROADMAP.md as the sole incomplete-work surface."
        else:
            message += " Keep process debt in ROADMAP.md."
        message += " Maker and checker must differ."
    if rival_registries:
        listed = ", ".join(rival_registries)
        message += f" Rival incomplete-work files do not replace ROADMAP.md: {listed}."
    if missing_probes:
        listed = ", ".join(missing_probes)
        message += (
            " Declared §7 probes are missing; write the scripts or remove the claim: "
            f"{listed}."
        )
    for extra in extra_trees:
        message += (
            f" Extra Contract Tree {extra.root} is {extra.tree} "
            f"({extra.versioned}/{extra.system_md} versioned)."
        )
    return message


def inspect_project(
    repository: str | Path,
    *,
    contract_root: str = DEFAULT_CONTRACT_ROOT,
) -> ProjectStatus:
    """Classify Recurspec readiness of a repository without guessing a user request."""
    repo = _resolve_repository(Path(repository))
    contract_dir = _resolve_under(repo, contract_root)
    tree, system_md, versioned_count, unversioned, diagnostics = _classify_contract_dir(
        repo, contract_dir
    )
    rivals = tuple(path for path in RIVAL_REGISTRY_PATHS if (repo / path).is_file())
    roadmap = (repo / "ROADMAP.md").is_file()
    recurspec_dir = (repo / ".recurspec").is_dir()
    checker = (repo / ".recurspec" / "worker-authorizations.json").is_file()

    extra_trees: list[ExtraTreeStatus] = []
    extra_probe_roots = [contract_dir]
    for extra_root in EXTRA_CONTRACT_ROOTS:
        extra_dir = _resolve_under(repo, extra_root)
        if extra_dir == contract_dir or not extra_dir.is_dir():
            continue
        extra_tree, extra_count, extra_versioned, extra_unversioned, _extra_diag = (
            _classify_contract_dir(repo, extra_dir)
        )
        if extra_count == 0:
            continue
        extra_trees.append(
            ExtraTreeStatus(
                root=extra_root.replace("\\", "/"),
                tree=extra_tree,
                system_md=extra_count,
                versioned=extra_versioned,
                unversioned=extra_unversioned,
            )
        )
        extra_probe_roots.append(extra_dir)

    missing: list[str] = []
    seen: set[str] = set()
    for probe_root in extra_probe_roots:
        for declared in _missing_probes(repo, probe_root):
            if declared not in seen:
                seen.add(declared)
                missing.append(declared)
    missing_probes = tuple(missing)

    extras = tuple(extra_trees)
    route: Route = {
        "missing": "design",
        "not_recurspec": "design",
        "invalid": "repair",
        "valid": "ready",
    }[tree]
    if missing_probes or any(item.tree in {"invalid", "not_recurspec"} for item in extras):
        route = "repair"
    return ProjectStatus(
        repository=repo.as_posix(),
        contract_root=contract_root.replace("\\", "/"),
        tree=tree,
        route=route,
        system_md=system_md,
        versioned=versioned_count,
        unversioned=unversioned,
        roadmap=roadmap,
        recurspec_dir=recurspec_dir,
        checker=checker,
        rival_registries=rivals,
        diagnostics=diagnostics,
        missing_probes=missing_probes,
        extra_trees=extras,
        next_action=_next_action(
            tree,
            roadmap=roadmap,
            rival_registries=rivals,
            missing_probes=missing_probes,
            extra_trees=extras,
        ),
    )


def render_status(status: ProjectStatus) -> str:
    """Human-readable orientation block. JSON callers use ``ProjectStatus.as_dict``."""
    lines = [
        f"tree: {status.tree}",
        f"route: {status.route}",
        f"repository: {status.repository}",
        f"contract_root: {status.contract_root}",
        f"system_md: {status.system_md}",
        f"versioned: {status.versioned}",
        f"roadmap: {'present' if status.roadmap else 'missing'}",
        f"recurspec_dir: {'present' if status.recurspec_dir else 'missing'}",
        f"checker: {'present' if status.checker else 'missing'}",
    ]
    if status.unversioned:
        lines.append("unversioned:")
        lines.extend(f"  {path}" for path in status.unversioned)
    if status.rival_registries:
        lines.append("rival_registries:")
        lines.extend(f"  {path}" for path in status.rival_registries)
    if status.missing_probes:
        lines.append("missing_probes:")
        lines.extend(f"  {path}" for path in status.missing_probes)
    if status.extra_trees:
        lines.append("extra_trees:")
        lines.extend(
            f"  {item.root}: {item.tree} ({item.versioned}/{item.system_md} versioned)"
            for item in status.extra_trees
        )
    if status.diagnostics:
        lines.append("diagnostics:")
        lines.extend(
            f"  {item.path}: {item.rule_code}: {item.message}"
            for item in status.diagnostics
        )
    lines.append(f"next: {status.next_action}")
    return "\n".join(lines) + "\n"
