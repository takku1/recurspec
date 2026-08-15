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

    assert skill.index("recurspec status") < skill.index("Raw goal or missing contract tree")
    assert "| `recurspec status REPO` |" in skill
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

    assert "skill install" in skill
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

    assert "## Work lists fan out" in skill
    assert "| `recurspec fanout --item ...` |" in skill
    assert "Do not implement 1–N" in skill or "Do not implement 1-N" in skill
    assert "not one FRAME" in design
    assert "fanout" in design


def test_skill_states_evidence_class_licensing():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )
    design = Path(str(files("recurspec").joinpath("skill/references/design.md"))).read_text(
        encoding="utf-8"
    )

    assert "Executed behavior" in skill
    assert "Does not license" in skill
    assert "research-informed" in skill
    assert "research-validated" in skill
    assert "oracles" in design
    assert "claim boundary" in design


def test_skill_states_escalate_is_the_wrong_space_path():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )

    assert "search space" in skill
    assert "fourth gate outcome" in skill
    assert "`ESCALATE`" in skill


def test_skill_cli_surface_names_the_current_commands():
    skill = Path(str(files("recurspec").joinpath("skill/SKILL.md"))).read_text(
        encoding="utf-8"
    )

    assert "| `recurspec contract evidence PATH` |" in skill
    assert "| `recurspec study accept` |" in skill
    assert "| `recurspec predict MODULE` |" in skill
    assert "| `recurspec recommend` |" in skill
    assert "--bks-metrics-only" in skill
    assert "recurspec[rust]" in skill
    assert "contaminated" in skill
