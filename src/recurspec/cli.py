"""Command-line interface for evaluation and skill installation."""

from __future__ import annotations

import argparse
import filecmp
import json
import math
import os
import shutil
import sys
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path

from . import __version__
from .contract import ContractInstrumentError, validate_contract
from .evaluation import ERROR, evaluate_isolated_candidate
from .evidence import export_decision_corpus
from .fanout import FanoutInstrumentError, plan_fanout, render_fanout, write_fanout
from .frontier import (
    FrontierInstrumentError,
    check_frontiers,
    github_issue_publisher,
    publish_frontiers,
)
from .modules_gate import evaluate_changed_modules
from .project_status import StatusInstrumentError, inspect_project, render_status
from .reconcile import ReconciliationInstrumentError, plan_reconciliation
from .spec_runner.workers import load_merge_authorization
from .structure_gate import check_structure
from .study import StudyInstrumentError, assign_pair, init_pair, list_pairs
from .technology_resolver import (
    ResolutionInstrumentError,
    audit_resolutions,
    load_dependency_inventory,
)


def _finite_nonneg(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError(
            f"must be a finite, non-negative number: {value!r}"
        )
    return parsed


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
    if target in {"grok", "all"}:
        grok_home = Path(os.environ.get("GROK_HOME", home / ".grok"))
        targets.append(("Grok", grok_home / "skills"))
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
    try:
        result = check_structure(
            args.repository,
            source_root=args.source_root,
            contract_root=args.contract_root,
            test_root=args.test_root,
            changed_files=set(args.changed_file) if args.changed_file else None,
        )
    except (OSError, ValueError) as exc:
        print(f"[ERROR] structure instrument failed: {exc}", file=sys.stderr)
        return 2
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


def _run_modules_check(args: argparse.Namespace) -> int:
    code, reports = evaluate_changed_modules(
        args.repository,
        args.changed_file,
        all_modules=args.all,
        contract_root=args.contract_root,
    )
    if args.format == "json":
        payload = {
            "modules": [
                {
                    "module": report.module,
                    "checks_code": report.checks_code,
                    "measure_code": report.measure_code,
                }
                for report in reports
            ],
            "valid": code == 0,
        }
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    elif not reports:
        print("PASS: no measurable modules touched")
    elif code == 0:
        print(f"PASS: {len(reports)} module(s) checked")
    else:
        for report in reports:
            if report.checks_code != 0 or report.measure_code != 0:
                print(
                    f"{report.module}: checks={report.checks_code} "
                    f"measure={report.measure_code} {report.detail}".rstrip()
                )
    return code


def _run_frontier(args: argparse.Namespace) -> int:
    try:
        if args.action == "publish":
            remote = github_issue_publisher() if args.remote == "github" else None
            report = publish_frontiers(args.contract_root, args.output, remote=remote)
            print(f"published {len(report.written)} Research Frontier ticket(s)")
            return 0
        check = check_frontiers(args.output, args.repository)
        if args.format == "json":
            print(
                json.dumps(
                    {
                        "integrity": check.integrity,
                        "ticket_count": check.ticket_count,
                        "broken": list(check.broken),
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        elif check.broken:
            print(f"FAIL: {len(check.broken)} ticket(s) missing a Contract Node")
        else:
            print(f"PASS: ticket_to_leaf_link_integrity {check.integrity:.3f}")
        return int(bool(check.broken))
    except FrontierInstrumentError as exc:
        print(f"[ERROR] frontier instrument failed: {exc}", file=sys.stderr)
        return 2


def _run_status(args: argparse.Namespace) -> int:
    try:
        status = inspect_project(args.repository, contract_root=args.contract_root)
    except StatusInstrumentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(status.as_dict(), separators=(",", ":"), sort_keys=True))
    else:
        print(render_status(status), end="")
    return 0


def _run_fanout(args: argparse.Namespace) -> int:
    raw_items = list(args.item)
    if args.list_file is not None:
        try:
            raw_items.append(args.list_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            print(f"[ERROR] could not read list file: {exc}", file=sys.stderr)
            return 2
    try:
        plan = plan_fanout(raw_items, prefix=args.prefix, output_dir=args.output)
    except FanoutInstrumentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if args.write:
        try:
            write_fanout(plan, repository=args.repository)
        except FanoutInstrumentError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"[ERROR] could not write handoffs: {exc}", file=sys.stderr)
            return 2
    if args.format == "json":
        print(json.dumps(plan.as_dict(), separators=(",", ":"), sort_keys=True))
    else:
        print(render_fanout(plan), end="")
    return 0


def _run_corpus_export(args: argparse.Namespace) -> int:
    try:
        count = export_decision_corpus(args.log_dir, args.output, opt_in=args.i_opt_in)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    print(f"exported {count} redacted event(s)")
    return 0


def _run_study(args: argparse.Namespace) -> int:
    try:
        if args.action == "init":
            path = init_pair(
                args.repository,
                pair_id=args.pair_id,
                project=str(args.project),
                task_a=args.task_a,
                task_b=args.task_b,
                hours=args.hours,
                baseline=args.baseline,
            )
            print(f"initialized {path.as_posix()}")
            return 0
        if args.action == "assign":
            result = assign_pair(args.pair_log)
            print(result)
            return 0
        pairs = list_pairs(args.repository)
        if args.format == "json":
            print(
                json.dumps(
                    [item.as_dict() for item in pairs],
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        elif not pairs:
            print("no case-study pairs")
        else:
            for item in pairs:
                state = "assigned" if item.assigned else "unassigned"
                print(f"{item.pair_id}\t{state}\t{item.project}")
        return 0
    except StudyInstrumentError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


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
        type=_finite_nonneg,
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
        choices=("claude", "codex", "grok", "all"),
        default="all",
        help="which tool's skill directory to target",
    )
    skills.set_defaults(handler=_run_skills)

    status = commands.add_parser(
        "status",
        help="classify Recurspec readiness of a repository",
        formatter_class=defaults_formatter,
    )
    status.add_argument(
        "repository",
        type=Path,
        nargs="?",
        default=Path("."),
        help="repository root to inspect",
    )
    status.add_argument(
        "--contract-root",
        default="docs/architecture",
        help="repository-relative Contract Tree root",
    )
    status.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="text prints an orientation block; json prints a stable payload",
    )
    status.set_defaults(handler=_run_status)

    fanout = commands.add_parser(
        "fanout",
        help="split a work list into one strategy handoff per item",
        formatter_class=defaults_formatter,
    )
    fanout.add_argument(
        "--item",
        action="append",
        default=[],
        help="one work item; repeat for each independently failing item",
    )
    fanout.add_argument(
        "--list-file",
        type=Path,
        help="markdown file whose numbered or bulleted list expands into items",
    )
    fanout.add_argument(
        "--prefix",
        default="FAN",
        help="ticket stem, e.g. FAN-01 or R-631",
    )
    fanout.add_argument(
        "--output",
        type=Path,
        default=Path(".recurspec/handoffs"),
        help="directory for strategy-<ticket>.md files",
    )
    fanout.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="repository root used when --write is set",
    )
    fanout.add_argument(
        "--write",
        action="store_true",
        help="write one strategy handoff per item; default is print only",
    )
    fanout.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="text prints the split; json prints a stable payload",
    )
    fanout.set_defaults(handler=_run_fanout)

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

    modules = commands.add_parser(
        "modules",
        help="run checks and measurements for changed measurable modules",
        formatter_class=defaults_formatter,
    )
    modules_actions = modules.add_subparsers(dest="action", required=True)
    modules_check = modules_actions.add_parser(
        "check",
        help="run modules/*/checks.sh and measure.sh for touched modules",
        formatter_class=defaults_formatter,
    )
    modules_check.add_argument("repository", type=Path, help="repository root")
    modules_check.add_argument(
        "--contract-root",
        default="docs/architecture",
        help="repository-relative Contract Tree used to map §6 paths to modules",
    )
    modules_check.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="repository-relative path that changed; repeat as needed",
    )
    modules_check.add_argument(
        "--all",
        action="store_true",
        help="evaluate every module that has probes, ignoring --changed-file",
    )
    modules_check.add_argument(
        "--format", choices=("text", "json"), default="text", help="output format"
    )
    modules_check.set_defaults(handler=_run_modules_check)

    frontier = commands.add_parser(
        "frontier",
        help="publish or verify Research Frontier tickets",
        formatter_class=defaults_formatter,
    )
    frontier_actions = frontier.add_subparsers(dest="action", required=True)
    frontier_publish = frontier_actions.add_parser(
        "publish",
        help="write local Research Frontier tickets for DEFER leaves and R-nnn citations",
        formatter_class=defaults_formatter,
    )
    frontier_publish.add_argument(
        "contract_root", type=Path, help="Contract Tree to scan"
    )
    frontier_publish.add_argument(
        "--output",
        type=Path,
        default=Path(".recurspec/frontiers"),
        help="directory for local ticket markdown",
    )
    frontier_publish.add_argument(
        "--remote",
        choices=("github",),
        help="also create a remote issue; requires gh on PATH",
    )
    frontier_publish.set_defaults(handler=_run_frontier)
    frontier_check = frontier_actions.add_parser(
        "check",
        help="verify every ticket still points at an existing Contract Node",
        formatter_class=defaults_formatter,
    )
    frontier_check.add_argument("repository", type=Path, help="repository root")
    frontier_check.add_argument(
        "--output",
        type=Path,
        default=Path(".recurspec/frontiers"),
        help="directory that holds published tickets",
    )
    frontier_check.add_argument(
        "--format", choices=("text", "json"), default="text", help="output format"
    )
    frontier_check.set_defaults(handler=_run_frontier)

    corpus = commands.add_parser(
        "corpus",
        help="export a privacy-preserving decision corpus",
        formatter_class=defaults_formatter,
    )
    corpus_actions = corpus.add_subparsers(dest="action", required=True)
    corpus_export = corpus_actions.add_parser(
        "export",
        help="write redacted evidence events; refuses without --i-opt-in",
        formatter_class=defaults_formatter,
    )
    corpus_export.add_argument(
        "--log-dir",
        type=Path,
        default=Path(".recurspec/evidence"),
        help="evidence log directory",
    )
    corpus_export.add_argument(
        "--output",
        type=Path,
        required=True,
        help="destination JSONL path",
    )
    corpus_export.add_argument(
        "--i-opt-in",
        action="store_true",
        help="required explicit project-level opt-in (R-500)",
    )
    corpus_export.set_defaults(handler=_run_corpus_export)

    study = commands.add_parser(
        "study",
        help="register and assign R-400–R-403 matched-pair case studies",
        formatter_class=defaults_formatter,
    )
    study_actions = study.add_subparsers(dest="action", required=True)
    study_init = study_actions.add_parser(
        "init",
        help="write an unassigned pair log; refuses Recurspec as the subject project",
        formatter_class=defaults_formatter,
    )
    study_init.add_argument("pair_id", help="filename stem under docs/research/pairs/")
    study_init.add_argument(
        "--project",
        type=Path,
        required=True,
        help="subject repository (must not be Recurspec itself)",
    )
    study_init.add_argument("--task-a", required=True, help="first matched task name")
    study_init.add_argument("--task-b", required=True, help="second matched task name")
    study_init.add_argument(
        "--hours",
        required=True,
        help="a-priori time estimate applied to both tasks before either starts",
    )
    study_init.add_argument(
        "--baseline",
        required=True,
        help="the project's real existing workflow, not a strawman",
    )
    study_init.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Recurspec repository that holds the pair logs",
    )
    study_init.set_defaults(handler=_run_study)
    study_assign = study_actions.add_parser(
        "assign",
        help="coin-flip Recurspec vs baseline and refuse to re-flip",
        formatter_class=defaults_formatter,
    )
    study_assign.add_argument("pair_log", type=Path, help="pair markdown written by study init")
    study_assign.set_defaults(handler=_run_study)
    study_list = study_actions.add_parser(
        "list",
        help="list pair logs and whether they are assigned",
        formatter_class=defaults_formatter,
    )
    study_list.add_argument(
        "repository",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Recurspec repository that holds the pair logs",
    )
    study_list.add_argument("--format", choices=("text", "json"), default="text")
    study_list.set_defaults(handler=_run_study)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
