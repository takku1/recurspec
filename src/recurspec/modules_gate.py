"""Map changed files to measurable modules and run their probes.

This is CI-side evaluation of already-merged or in-branch module probes. It is
not isolated Candidate evaluation and does not issue KEEP/REVERT.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from .evaluation import run_script
from .structure_gate import declared_paths, declared_probe_paths

ProbeRunner = Callable[..., tuple[int, str, str]]


@dataclass(frozen=True)
class ModuleProbeReport:
    module: str
    checks_code: int
    measure_code: int
    detail: str


def _posix(path: str | Path) -> str:
    return Path(path).as_posix().lstrip("./")


def measurable_owners(
    repository: Path, contract_root: str = "docs/architecture"
) -> dict[str, set[str]]:
    """Return ``{module_name: repo-relative owned paths}`` for modules that have probes."""
    repository = Path(repository)
    owners: dict[str, set[str]] = {}

    def _register(module_dir: Path) -> None:
        if not module_dir.is_dir():
            return
        if not (module_dir / "checks.sh").is_file() or not (module_dir / "measure.sh").is_file():
            return
        owners[module_dir.name] = {
            _posix(path.relative_to(repository))
            for path in module_dir.rglob("*")
            if path.is_file()
        }

    modules_root = repository / "modules"
    if modules_root.is_dir():
        for module_dir in modules_root.iterdir():
            _register(module_dir)

    tree = repository / contract_root
    # A project names its own probe root in §7; scanning only "modules/" made the gate
    # report a green PASS having measured nothing on any project that puts probes
    # elsewhere, while the Structure Gate validated those same declared paths (R-701).
    if tree.is_dir():
        for contract in tree.rglob("SYSTEM.md"):
            declared, _unsafe = declared_probe_paths(contract, repository=repository)
            for probe in declared:
                _register((repository / probe).parent)

    if tree.is_dir():
        for contract in tree.rglob("SYSTEM.md"):
            declared, _unsafe = declared_probe_paths(contract, repository=repository)
            # The module is the one this node declares a probe for; several nodes may
            # share one. Falling back to the contract's directory name only works where
            # that name happens to match the probe directory, as it does here (R-701).
            modules = {(repository / probe).parent.name for probe in declared}
            for module in modules or {contract.parent.name}:
                if module not in owners:
                    continue
                implementations, tests, _unsafe2 = declared_paths(contract, repository=repository)
                owners[module].update(_posix(item) for item in implementations)
                owners[module].update(_posix(item) for item in tests)
    return owners


def modules_touched(
    repository: Path,
    changed_files: Iterable[str],
    *,
    contract_root: str = "docs/architecture",
) -> tuple[str, ...]:
    owners = measurable_owners(repository, contract_root)
    changed = {_posix(item) for item in changed_files if item}
    touched: set[str] = set()
    for module, owned in owners.items():
        for path in changed:
            if any(path == item or path.startswith(f"{item.rstrip('/')}/") for item in owned):
                touched.add(module)
                break
    return tuple(sorted(touched))


def evaluate_changed_modules(
    repository: str | Path,
    changed_files: Iterable[str] | None = None,
    *,
    all_modules: bool = False,
    contract_root: str = "docs/architecture",
    runner: ProbeRunner = run_script,
) -> tuple[int, tuple[ModuleProbeReport, ...]]:
    """Run checks.sh and measure.sh for each touched module.

    Returns process-style exit ``0`` if every probe succeeds or no module was
    touched; ``1`` if a probe failed; ``2`` if the instrument could not run.
    """
    repository = Path(repository)
    if all_modules:
        selected = tuple(sorted(measurable_owners(repository, contract_root)))
    else:
        selected = modules_touched(
            repository, changed_files or (), contract_root=contract_root
        )
    reports: list[ModuleProbeReport] = []
    worst = 0
    for module in selected:
        checks = f"modules/{module}/checks.sh"
        measure = f"modules/{module}/measure.sh"
        checks_code, _out, checks_err = runner(checks, module, cwd=repository)
        measure_code, _mout, measure_err = runner(measure, module, cwd=repository)
        if checks_code == 127 or measure_code == 127:
            worst = 2
        elif checks_code != 0 or measure_code != 0:
            worst = max(worst, 1)
        detail = (checks_err or measure_err).strip()
        reports.append(
            ModuleProbeReport(module, checks_code, measure_code, detail)
        )
    return worst, tuple(reports)
