from pathlib import Path

from recurspec.modules_gate import evaluate_changed_modules, modules_touched


def test_modules_touched_maps_a_declared_implementation_path():
    repo = Path(__file__).resolve().parents[1]
    touched = modules_touched(repo, ["src/recurspec/contract.py"])

    assert "contract-engine" in touched
    assert "job-store" not in touched


def test_modules_touched_maps_a_probe_script():
    repo = Path(__file__).resolve().parents[1]
    touched = modules_touched(repo, ["modules/job-store/measure.sh"])

    assert touched == ("job-store",)


def test_evaluate_changed_modules_runs_only_touched_probes():
    repo = Path(__file__).resolve().parents[1]
    calls: list[str] = []

    def runner(script: str, module: str, cwd=None, timeout=300):
        calls.append(f"{module}:{Path(script).name}")
        return 0, "{}", ""

    code, reports = evaluate_changed_modules(
        repo,
        ["src/recurspec/contract.py"],
        runner=runner,
    )

    assert code == 0
    assert [report.module for report in reports] == ["contract-engine"]
    assert calls == ["contract-engine:checks.sh", "contract-engine:measure.sh"]


def test_evaluate_changed_modules_is_quiet_when_nothing_measurable_changed():
    repo = Path(__file__).resolve().parents[1]
    code, reports = evaluate_changed_modules(
        repo,
        ["README.md"],
        runner=lambda *_a, **_k: (1, "", "should not run"),
    )

    assert code == 0
    assert reports == ()


def test_evaluate_changed_modules_treats_a_missing_shell_as_instrument_failure():
    repo = Path(__file__).resolve().parents[1]

    def runner(script: str, module: str, cwd=None, timeout=300):
        return 127, "", "No bash"

    code, reports = evaluate_changed_modules(
        repo, ["src/recurspec/contract.py"], runner=runner
    )

    assert code == 2
    assert reports[0].checks_code == 127
