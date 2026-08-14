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
