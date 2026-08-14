import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_MARKDOWN = [
    *ROOT.glob("*.md"),
    *ROOT.joinpath("docs").rglob("*.md"),
    *ROOT.joinpath("src", "recurspec", "skill").rglob("*.md"),
]


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
    offenders: list[str] = []
    for document in PUBLISHED_MARKDOWN:
        text = document.read_text(encoding="utf-8")
        for term in banned:
            if term in text:
                offenders.append(f"{document.relative_to(ROOT)}: {term}")

    assert offenders == []


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
