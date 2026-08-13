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
