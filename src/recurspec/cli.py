"""Command-line interface for evaluation and skill installation."""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path

from . import __version__
from .contract import ContractInstrumentError, validate_contract
from .evaluation import ERROR, evaluate_isolated_candidate
from .reconcile import ReconciliationInstrumentError, plan_reconciliation
from .spec_runner.workers import load_merge_authorization
from .structure_gate import check_structure
from .technology_resolver import (
    ResolutionInstrumentError,
    audit_resolutions,
    load_dependency_inventory,
)


def _skill_source() -> Path:
    return Path(str(files("recurspec").joinpath("skill")))


def _skill_targets(target: str) -> list[tuple[str, Path]]:
    home = Path.home()
    targets: list[tuple[str, Path]] = []
    if target in {"claude", "all"}:
        targets.append(
            ("Claude Code", Path(os.environ.get("CLAUDE_SKILLS_DIR", home / ".claude/skills")))
        )
    if target in {"codex", "all"}:
        codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
        targets.append(("Codex", Path(os.environ.get("CODEX_SKILLS_DIR", codex_home / "skills"))))
    return targets


def _same_tree(source: Path, destination: Path) -> bool:
    if not destination.is_dir():
        return False
    source_files = {path.relative_to(source) for path in source.rglob("*") if path.is_file()}
    destination_files = {
        path.relative_to(destination) for path in destination.rglob("*") if path.is_file()
    }
    return source_files == destination_files and all(
        filecmp.cmp(source / relative, destination / relative, shallow=False)
        for relative in source_files
    )


def sync_skill(destination_root: Path, *, check: bool = False) -> bool:
    """Install the bundled skill, returning whether it was already current."""
    source = _skill_source()
    destination = destination_root / "recurspec"
    current = _same_tree(source, destination)
    if current or check:
        return current
    destination_root.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return False


def _run_evaluate(args: argparse.Namespace) -> int:
    try:
        authorization = load_merge_authorization(args.worker_state, args.authorization_id)
        code, _ = evaluate_isolated_candidate(
            args.repo,
            args.module,
            args.candidate_branch,
            authorization=authorization,
            tolerance_pct=args.tolerance,
            baseline_branch=args.baseline_branch,
            log_dir=args.log_dir,
            record_baseline=args.record_baseline,
            stagnation_limit=args.stagnation_limit,
            attempt_ceiling=args.attempt_ceiling,
        )
        return code
    except Exception as exc:  # the evaluation instrument failed, not the candidate
        print(f"[ERROR] evaluation gate failed: {exc}")
        return ERROR


def _run_skills(args: argparse.Namespace) -> int:
    drift = False
    for label, root in _skill_targets(args.target):
        current = sync_skill(root, check=args.action == "check")
        status = "up to date" if current else ("differs" if args.action == "check" else "installed")
        print(f"{label}: {root / 'recurspec'} ({status})")
        drift = drift or not current
    return int(args.action == "check" and drift)


def _run_contract_check(args: argparse.Namespace) -> int:
    try:
        result = validate_contract(args.path)
    except ContractInstrumentError as exc:
        print(f"[ERROR] contract validation instrument failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        payload = {
            "contracts_checked": len(result.contracts),
            "diagnostics": [diagnostic.as_dict() for diagnostic in result.diagnostics],
            "valid": result.valid,
        }
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    elif result.valid:
        print(f"PASS: {len(result.contracts)} contract(s) valid")
    else:
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.path}: {diagnostic.rule_code}: {diagnostic.message}")
    return int(not result.valid)


def _run_structure_check(args: argparse.Namespace) -> int:
    result = check_structure(
        args.repository,
        source_root=args.source_root,
        contract_root=args.contract_root,
        test_root=args.test_root,
        changed_files=set(args.changed_file) if args.changed_file else None,
    )
    if args.format == "json":
        payload = {
            "diagnostics": [diagnostic.as_dict() for diagnostic in result.diagnostics],
            "instrument_error": result.instrument_error,
            "valid": result.valid,
        }
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    elif result.valid:
        print("PASS: source structure matches the Contract Tree")
    else:
        for diagnostic in result.diagnostics:
            location = f"::{diagnostic.symbol}" if diagnostic.symbol else ""
            print(f"{diagnostic.path}{location}: {diagnostic.code}: {diagnostic.message}")
    return 2 if result.instrument_error else int(not result.valid)


def _run_reconcile_plan(args: argparse.Namespace) -> int:
    try:
        events = []
        if args.evidence_log is not None:
            events = [
                json.loads(line)
                for line in args.evidence_log.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        plan = plan_reconciliation(
            args.repository,
            source_root=args.source_root,
            contract_root=args.contract_root,
            test_root=args.test_root,
            changed_files=set(args.changed_file) if args.changed_file else None,
            evidence_events=events,
            bloat_line_limit=args.bloat_line_limit,
        )
    except (OSError, ValueError, json.JSONDecodeError, ReconciliationInstrumentError) as exc:
        print(f"[ERROR] reconciliation instrument failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(plan.as_dict(), separators=(",", ":"), sort_keys=True))
    elif not plan.actions:
        print("PASS: no structural reconciliation drafts")
    else:
        for action in plan.actions:
            target = f" -> {action.contract_path}" if action.contract_path else ""
            print(f"{action.kind}: {action.source_path}{target}: {action.reason}")
    return int(bool(plan.actions))


def _run_stack_check(args: argparse.Namespace) -> int:
    try:
        inventory = (
            load_dependency_inventory(args.inventory) if args.inventory is not None else None
        )
        result = audit_resolutions(
            args.repository,
            contract_root=args.contract_root,
            inventory=inventory,
            wrap_line_limit=args.wrap_line_limit,
        )
    except (OSError, ValueError, ResolutionInstrumentError) as exc:
        print(f"[ERROR] stack audit instrument failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result.as_dict(), separators=(",", ":"), sort_keys=True))
    elif result.valid:
        print(f"PASS: Technology Resolution completeness {result.completeness:.3f}")
    else:
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.path}: {diagnostic.code}: {diagnostic.message}")
    return 2 if result.indeterminate else int(not result.valid)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recurspec", description="Evidence-gated system design")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    defaults_formatter = argparse.ArgumentDefaultsHelpFormatter

    evaluate = commands.add_parser(
        "evaluate",
        help="evaluate a candidate branch",
        formatter_class=defaults_formatter,
    )
    evaluate.add_argument(
        "module", help="module name under modules/<name>/ providing checks.sh and measure.sh"
    )
    evaluate.add_argument(
        "candidate_branch",
        help="existing local Candidate branch to isolate, evaluate, and fast-forward on KEEP",
    )
    evaluate.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="git repository whose checked-out baseline receives an accepted Candidate",
    )
    evaluate.add_argument(
        "--worker-state",
        type=Path,
        required=True,
        help="authorization state written by the Worker Pool",
    )
    evaluate.add_argument(
        "--authorization-id",
        required=True,
        help="completed Worker Pool node whose maker/checker state authorizes this merge",
    )
    evaluate.add_argument(
        "--tolerance",
        type=float,
        default=20.0,
        help="allowed percent regression on non-hard_gate metrics before reverting",
    )
    evaluate.add_argument(
        "--baseline-branch",
        default="main",
        help="branch whose promoted Best Known State this candidate is compared against",
    )
    evaluate.add_argument(
        "--log-dir",
        default=".recurspec/evidence",
        help="directory for the append-only evidence JSONL log",
    )
    evaluate.add_argument(
        "--record-baseline",
        action="store_true",
        help="after merge, re-evaluate trunk and promote its measurement as Best Known State",
    )
    evaluate.add_argument(
        "--stagnation-limit",
        type=int,
        default=5,
        help="consecutive reverts on this branch before returning ESCALATE",
    )
    evaluate.add_argument(
        "--attempt-ceiling",
        type=int,
        default=8,
        help="total reverts on this branch before returning ESCALATE",
    )
    evaluate.set_defaults(handler=_run_evaluate)

    skills = commands.add_parser(
        "skills",
        help="install or verify the bundled agent skill",
        formatter_class=defaults_formatter,
    )
    skills.add_argument(
        "action",
        choices=("install", "check"),
        nargs="?",
        default="install",
        help="install writes the bundled skill; check reports drift without writing",
    )
    skills.add_argument(
        "--target",
        choices=("claude", "codex", "all"),
        default="all",
        help="which tool's skill directory to target",
    )
    skills.set_defaults(handler=_run_skills)

    contract = commands.add_parser(
        "contract",
        help="validate versioned Contract Nodes",
        formatter_class=defaults_formatter,
    )
    contract_actions = contract.add_subparsers(dest="action", required=True)
    check = contract_actions.add_parser(
        "check",
        help="validate one file or a directory tree",
        formatter_class=defaults_formatter,
    )
    check.add_argument(
        "path", type=Path, help="a SYSTEM.md file, or a directory checked recursively for them"
    )
    check.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="text prints diagnostics; json prints a stable machine-readable payload",
    )
    check.set_defaults(handler=_run_contract_check)

    structure = commands.add_parser(
        "structure",
        help="check source ownership and test seams against the Contract Tree",
        formatter_class=defaults_formatter,
    )
    structure_actions = structure.add_subparsers(dest="action", required=True)
    structure_check = structure_actions.add_parser(
        "check",
        help="detect structural drift",
        formatter_class=defaults_formatter,
    )
    structure_check.add_argument(
        "repository", type=Path, help="repository root containing source and Contract Tree"
    )
    structure_check.add_argument(
        "--source-root", default="src/recurspec", help="repository-relative Python source root"
    )
    structure_check.add_argument(
        "--contract-root",
        default="docs/architecture",
        help="repository-relative Contract Tree root",
    )
    structure_check.add_argument(
        "--test-root", default="tests", help="repository-relative Python test root"
    )
    structure_check.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="repository-relative source path to inspect; repeat to provide a pre-commit set",
    )
    structure_check.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="diagnostic output format",
    )
    structure_check.set_defaults(handler=_run_structure_check)

    reconcile = commands.add_parser(
        "reconcile",
        help="turn structural feedback into reviewable contract drafts",
        formatter_class=defaults_formatter,
    )
    reconcile_actions = reconcile.add_subparsers(dest="action", required=True)
    reconcile_plan = reconcile_actions.add_parser(
        "plan",
        help="emit draft actions without changing files",
        formatter_class=defaults_formatter,
    )
    reconcile_plan.add_argument("repository", type=Path, help="repository root")
    reconcile_plan.add_argument("--source-root", default="src/recurspec")
    reconcile_plan.add_argument("--contract-root", default="docs/architecture")
    reconcile_plan.add_argument("--test-root", default="tests")
    reconcile_plan.add_argument("--changed-file", action="append", default=[])
    reconcile_plan.add_argument(
        "--evidence-log",
        type=Path,
        help="optional JSONL evidence log whose Signal D events remain deferred",
    )
    reconcile_plan.add_argument("--bloat-line-limit", type=int, default=150)
    reconcile_plan.add_argument(
        "--format", choices=("text", "json"), default="text"
    )
    reconcile_plan.set_defaults(handler=_run_reconcile_plan)

    stack = commands.add_parser(
        "stack",
        help="audit Technology Resolution completeness and staleness",
        formatter_class=defaults_formatter,
    )
    stack_actions = stack.add_subparsers(dest="action", required=True)
    stack_check = stack_actions.add_parser(
        "check", help="check §8 fields, pins, and WRAP seams", formatter_class=defaults_formatter
    )
    stack_check.add_argument("repository", type=Path, help="repository root")
    stack_check.add_argument("--contract-root", default="docs/architecture")
    stack_check.add_argument(
        "--inventory",
        type=Path,
        help="authoritative JSON object mapping normalized dependency names to exact versions",
    )
    stack_check.add_argument("--wrap-line-limit", type=int, default=150)
    stack_check.add_argument("--format", choices=("text", "json"), default="text")
    stack_check.set_defaults(handler=_run_stack_check)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
