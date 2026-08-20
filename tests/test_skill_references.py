import re
from importlib.resources import files
from pathlib import Path

BANNED_TERMS = (
    "graphgraph",
    "code-review-graph",
    "Sherloc",
    "Type B",
    ".scratch/wayfinder-map",
)


def test_skill_references_do_not_name_unavailable_tools_or_banned_vocabulary():
    skill_root = Path(str(files("recurspec").joinpath("skill")))
    offenders: list[str] = []
    for document in sorted(skill_root.rglob("*.md")):
        text = document.read_text(encoding="utf-8")
        for term in BANNED_TERMS:
            if term in text:
                offenders.append(f"{document.relative_to(skill_root)}: {term!r}")

    assert offenders == []


def test_skill_references_never_link_outside_the_installed_skill(tmp_path):
    """pyproject.toml bundles only ``skill/**/*`` into the installed package (R-605):
    a relative link that climbs out of the skill's own directory (e.g. into
    docs/research/, which is repository-only) is a dead link for every consumer that
    installs the skill standalone."""
    skill_root = Path(str(files("recurspec").joinpath("skill")))
    link_pattern = re.compile(r"\[[^]]*]\(([^)]+)\)")
    offenders: list[str] = []
    for document in sorted(skill_root.rglob("*.md")):
        for raw_target in link_pattern.findall(document.read_text(encoding="utf-8")):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (document.parent / target).resolve()
            if skill_root not in resolved.parents and resolved != skill_root:
                offenders.append(f"{document.relative_to(skill_root)} -> {raw_target}")

    assert offenders == []


def test_skill_design_reference_carries_a_self_contained_ears_citation():
    design = Path(str(files("recurspec").joinpath("skill/references/design.md")))
    text = design.read_text(encoding="utf-8")

    assert "docs/research/foundations.md" not in text
    assert "10.1109/RE.2009.9" in text
    assert "Mavin" in text


def test_skill_requires_status_before_design_and_names_not_recurspec():
    skill_root = Path(str(files("recurspec").joinpath("skill")))
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    design = (skill_root / "references" / "design.md").read_text(encoding="utf-8")

    assert skill.index("recurspec status") < skill.index("design")
    assert "`not_recurspec`" in skill
    assert "NEED_CHECKER" in skill
    assert "source material" in design
    assert "Existing architecture documents" in design
    assert "FEATURE_GAPS.md" in design


def test_skill_requires_status_on_paper_and_research_asks():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )
    design = Path(str(files("recurspec").joinpath("skill/references/design.md"))).read_text(
        encoding="utf-8"
    )

    assert "*subject* repository" in skill
    assert "missing_probes" in skill
    assert ".recurspec/contracts" in skill
    assert "prose-only preprint" in skill
    assert "until those files exist" in design


def test_skill_requires_work_lists_to_fan_out():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )
    design = Path(str(files("recurspec").joinpath("skill/references/design.md"))).read_text(
        encoding="utf-8"
    )

    assert "recurspec fanout" in skill
    assert "one Candidate" in skill
    assert "not one FRAME" in design
    assert "fanout" in design


def test_skill_states_evidence_class_licensing():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )
    design = Path(str(files("recurspec").joinpath("skill/references/design.md"))).read_text(
        encoding="utf-8"
    )

    assert "Tests license" in skill
    assert "measurements license" in skill
    assert "research-informed" in skill
    assert "research-validated" in skill
    assert "oracles" in design
    assert "claim boundary" in design


def test_skill_states_escalate_is_the_wrong_space_path():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )

    assert "Contract Node or search space" in skill
    assert "KEEP`, `REVERT`, or `ESCALATE" in skill
    assert "`ESCALATE`" in skill


def test_skill_is_a_compact_controller_not_a_duplicate_cli_manual():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )

    assert "DISCOVER -> RESOLVE -> EXECUTE -> CHECK -> RECONCILE" in skill
    assert "references/design.md" in skill
    assert "references/resolve.md" in skill
    assert "references/reconcile.md" in skill
    assert len(skill.splitlines()) <= 90


def test_design_reference_defines_bounded_coverage_review():
    design = Path(str(files("recurspec").joinpath("skill/references/design.md"))).read_text(
        encoding="utf-8"
    )

    assert "Coverage Review" in design
    assert "vertically" in design
    assert "horizontally" in design
    assert "sibling pairs" in design
    assert "Unknown" in design
    assert "automatic Contract Tree" in design
