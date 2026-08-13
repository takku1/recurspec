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
from .evaluation import ERROR, evaluate_change


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
        code, _ = evaluate_change(
            args.module,
            args.candidate_branch,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recurspec", description="Evidence-gated system design")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    evaluate = commands.add_parser("evaluate", help="evaluate a candidate branch")
    evaluate.add_argument("module")
    evaluate.add_argument("candidate_branch")
    evaluate.add_argument("--tolerance", type=float, default=20.0)
    evaluate.add_argument("--baseline-branch", default="main")
    evaluate.add_argument("--log-dir", default=".recurspec/evidence")
    evaluate.add_argument("--record-baseline", action="store_true")
    evaluate.add_argument("--stagnation-limit", type=int, default=5)
    evaluate.add_argument("--attempt-ceiling", type=int, default=8)
    evaluate.set_defaults(handler=_run_evaluate)

    skills = commands.add_parser("skills", help="install or verify the bundled agent skill")
    skills.add_argument("action", choices=("install", "check"), nargs="?", default="install")
    skills.add_argument("--target", choices=("claude", "codex", "all"), default="all")
    skills.set_defaults(handler=_run_skills)

    contract = commands.add_parser("contract", help="validate versioned Contract Nodes")
    contract_actions = contract.add_subparsers(dest="action", required=True)
    check = contract_actions.add_parser("check", help="validate one file or a directory tree")
    check.add_argument("path", type=Path)
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.set_defaults(handler=_run_contract_check)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
