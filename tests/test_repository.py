import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tracked_published_markdown() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
    )
    published: list[Path] = []
    for relative in result.stdout.split("\0"):
        if not relative.endswith(".md"):
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        if (
            path.parent == ROOT
            or ROOT.joinpath("docs") in path.parents
            or ROOT.joinpath("src", "recurspec", "skill") in path.parents
        ):
            published.append(path)
    return published


PUBLISHED_MARKDOWN = _tracked_published_markdown()


def test_relative_markdown_links_resolve():
    missing: list[str] = []
    link_pattern = re.compile(r"\[[^]]*]\(([^)]+)\)")
    for document in PUBLISHED_MARKDOWN:
        for raw_target in link_pattern.findall(document.read_text(encoding="utf-8")):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (document.parent / target).resolve().exists():
                missing.append(f"{document.relative_to(ROOT)} -> {raw_target}")

    assert missing == []


def test_legacy_public_names_do_not_return():
    banned = (
        "recursive-system-design",
        "/dual-loop",
        "/recursive-spec",
        "/resolve-stack",
        "/reconcile-spec",
        "harness/hypothesis_runner.py",
        "docs/open-work.md",
        "skills-lock.json",
    )
    # Case-study pair logs (docs/research/pairs/) narrate a *subject* project's own,
    # currently-real workflow verbatim -- a subject project's actual file (e.g. its own
    # docs/open-work.md) can legitimately share a name Recurspec retired for itself.
    # That is the external project's current state, not Recurspec vocabulary drift.
    pairs_dir = ROOT / "docs" / "research" / "pairs"
    offenders: list[str] = []
    for document in PUBLISHED_MARKDOWN:
        if pairs_dir in document.parents:
            continue
        text = document.read_text(encoding="utf-8")
        for term in banned:
            if term in text:
                offenders.append(f"{document.relative_to(ROOT)}: {term}")

    assert offenders == []


def test_current_docs_do_not_reintroduce_retired_workflow_surfaces():
    """Current documentation is one interface; history and subject-study logs are not."""
    retired = (
        ".scratch/wayfinder-map",
        "Type A/B",
        "Type B",
        "OW candidate",
        "docs/archive/",
        "None of the three exist yet",
    )
    excluded = {
        ROOT / "CHANGELOG.md",
        ROOT / "CONTEXT.md",  # Names retired terms in its explicit Avoid list.
    }
    pairs_dir = ROOT / "docs" / "research" / "pairs"
    offenders: list[str] = []
    for document in PUBLISHED_MARKDOWN:
        if document in excluded or pairs_dir in document.parents:
            continue
        text = document.read_text(encoding="utf-8")
        for term in retired:
            if term in text:
                offenders.append(f"{document.relative_to(ROOT)}: {term}")

    assert offenders == []


def test_top_level_docs_are_reachable_from_the_index():
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    unindexed = [
        path.name
        for path in sorted((ROOT / "docs").glob("*.md"))
        if path.name != "index.md" and f"./{path.name}" not in index
    ]

    assert unindexed == []


def test_roadmap_references_and_blockers_name_open_items():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    open_ids = set(re.findall(r"^\| (R-\d{3}) \|", roadmap, flags=re.MULTILINE))
    stale: list[str] = []

    for document in PUBLISHED_MARKDOWN:
        if document.name == "CHANGELOG.md" or "pairs" in document.parts:
            continue
        for line_number, line in enumerate(
            document.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "ROADMAP" not in line:
                continue
            for ticket in re.findall(r"(?<!AD)R-\d{3}", line):
                if ticket not in open_ids:
                    stale.append(
                        f"{document.relative_to(ROOT)}:{line_number}: {ticket}"
                    )

    for line_number, line in enumerate(roadmap.splitlines(), start=1):
        if not line.startswith("| R-"):
            continue
        fields = [field.strip() for field in line.strip("|").split("|")]
        if len(fields) < 4 or fields[2] != "blocked":
            continue
        for blocker in re.findall(r"(?<!AD)R-\d{3}", fields[3]):
            if blocker not in open_ids:
                stale.append(f"ROADMAP.md:{line_number}: blocker {blocker}")

    assert stale == []


def test_local_scratch_state_is_never_committed():
    """.scratch/ is this repository's own scratchpad (ROADMAP.md is the sole
    incomplete-work surface, per AGENTS.md rule 1) - a file committed under it is
    exactly the kind of parallel, driftable readiness list that rule forbids. This
    reproduces the real regression: .scratch/wayfinder-map/ was committed pre-redesign
    and never removed, silently outliving the rename to recurspec's current
    architecture and vocabulary."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", ".scratch"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [line for line in result.stdout.splitlines() if line.strip()]

    assert tracked == []


def test_bundled_skill_has_one_public_identity():
    skill = ROOT / "src/recurspec/skill/SKILL.md"
    text = skill.read_text(encoding="utf-8")

    assert text.startswith("---\nname: recurspec\n")
    assert sorted(path.name for path in skill.parent.joinpath("references").glob("*.md")) == [
        "design.md",
        "reconcile.md",
        "resolve.md",
    ]


def _resolution_fields(path: Path) -> set[str]:
    """Field labels documented in a file's §8 Technology Resolution block."""
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r"^#+ 8\. Technology Resolution.*?$(.*?)(?=^#+ |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert blocks, f"{path.name} documents no §8 Technology Resolution block"
    return {
        label.strip()
        for block in blocks
        for label in re.findall(r"^\s*-\s+\*\*([^*]+):\*\*", block, re.MULTILINE)
    }


def test_skill_documents_exactly_the_enforced_resolution_fields():
    from recurspec.technology_resolver import _REQUIRED_FIELDS

    expected = set(_REQUIRED_FIELDS) | {"Justification"}
    references = ROOT / "src/recurspec/skill/references"
    for name in ("design.md", "resolve.md"):
        assert _resolution_fields(references / name) == expected, name


def test_ci_runs_every_deterministic_gate_the_project_ships():
    """Gates that only run when a maintainer remembers are not gates. A source-root
    default that broke every repository except this one survived precisely because
    structure, stack, and reconcile were never executed in CI (R-701)."""
    workflow = ROOT / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")

    for command in (
        "recurspec contract check docs/architecture",
        "recurspec structure check .",
        "recurspec stack check .",
        "recurspec reconcile plan .",
        "recurspec skills check --target claude",
        "recurspec modules check .",
        "recurspec contract evidence docs/architecture",
        "recurspec check .",
        "python -m pytest",
        "ruff check src tests",
    ):
        assert command in text, command

    assert "windows-latest" in text, "the development platform must be verified in CI"


def test_contributor_docs_name_the_gates_ci_runs():
    """AGENTS.md and CONTRIBUTING.md had drifted to a shorter gate than CI, which is how
    a source-root default that broke every other repository survived (R-701)."""
    commands = (
        "python -m pytest",
        "ruff check src tests",
        "recurspec contract check docs/architecture",
        "recurspec structure check .",
        "recurspec stack check .",
        "recurspec reconcile plan .",
        "recurspec check .",
        "python -m build",
    )
    for path in (ROOT / "AGENTS.md", ROOT / "CONTRIBUTING.md"):
        text = path.read_text(encoding="utf-8")
        for command in commands:
            assert command in text, f"{path.name} missing {command!r}"


def test_readme_names_the_evidence_boundary_and_foundations_ledger():
    """A front-door README that omits the claim boundary will be quoted as if Recurspec
    were already outcome-validated (R-400)."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/research/foundations.md" in text
    assert "research-informed" in text
    assert "research-validated" in text
    assert "ROADMAP.md" in text


def _bundled_system_md_template() -> str:
    text = (ROOT / "src/recurspec/skill/references/design.md").read_text(encoding="utf-8")
    after = text.split("## `SYSTEM.md` template", 1)[1]
    start = after.index("```markdown") + len("```markdown")
    return after[start : after.index("```", start)].strip() + "\n"


def test_skill_template_is_accepted_by_the_parser(tmp_path):
    """The bundled template said `(Level N)`, omitted the version marker, and used
    unbolded EARS tags — an agent following Recurspec's own instructions produced a
    tree Recurspec rejects. Recurspec's contracts were hand-written, so this stayed
    invisible (R-701)."""
    from recurspec.contract import validate_contract
    from recurspec.structure_gate import _IMPLEMENTATION_LABELS

    filled = _bundled_system_md_template().replace("<level>", "2")
    path = tmp_path / "SYSTEM.md"
    path.write_text(filled, encoding="utf-8")
    result = validate_contract(path)

    assert result.valid, [item.as_dict() for item in result.diagnostics]
    assert "<!-- recurspec-contract: 1.0 -->" in filled
    assert "**Implementation Files:**" in filled
    assert "Implementation Files" in _IMPLEMENTATION_LABELS
    assert "**Evaluation Gate Path:**" not in filled
