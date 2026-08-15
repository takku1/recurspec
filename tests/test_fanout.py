import json
from pathlib import Path

from recurspec.cli import main
from recurspec.fanout import expand_items, plan_fanout


def test_expand_items_accepts_plus_bullets():
    assert expand_items(["+ first seam\n+ second seam\n"]) == [
        "first seam",
        "second seam",
    ]


def test_expand_items_splits_a_numbered_list_in_one_string():
    goals = expand_items(
        [
            "1. missing probes\n2. extra trees\n3. paper still runs status\n"
        ]
    )

    assert goals == [
        "missing probes",
        "extra trees",
        "paper still runs status",
    ]


def test_plan_fanout_refuses_a_single_item():
    try:
        plan_fanout(["only one thing"])
    except Exception as exc:
        assert "at least two items" in str(exc)
    else:
        raise AssertionError("expected FanoutInstrumentError")


def test_fanout_cli_prints_one_row_per_item_without_writing(tmp_path: Path, capsys):
    code = main(
        [
            "fanout",
            "--item",
            "missing probes",
            "--item",
            "extra trees",
            "--repository",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["ticket_id"] for item in payload["items"]] == ["FAN-01", "FAN-02"]
    assert "do not keep siblings" in payload["rule"]
    assert not (tmp_path / ".recurspec" / "handoffs").exists()


def test_fanout_cli_writes_one_handoff_per_item(tmp_path: Path):
    code = main(
        [
            "fanout",
            "--item",
            "missing probes",
            "--item",
            "extra trees",
            "--prefix",
            "R-631",
            "--repository",
            str(tmp_path),
            "--write",
        ]
    )

    assert code == 0
    first = tmp_path / ".recurspec" / "handoffs" / "strategy-R-631-01.md"
    second = tmp_path / ".recurspec" / "handoffs" / "strategy-R-631-02.md"
    assert first.is_file()
    assert second.is_file()
    text = first.read_text(encoding="utf-8")
    assert "missing probes" in text
    assert "Sibling items" in text
    assert "Do not keep sibling items" in text
    assert "extra trees" not in text


def test_fanout_cli_refuses_an_escaping_output_directory(tmp_path: Path, capsys):
    code = main(
        [
            "fanout",
            "--item",
            "first",
            "--item",
            "second",
            "--output",
            "../outside",
            "--repository",
            str(tmp_path),
            "--write",
        ]
    )

    assert code == 1
    assert "escapes" in capsys.readouterr().err
    assert not (tmp_path.parent / "outside").exists()


def test_fanout_cli_maps_a_missing_repository_to_instrument_error(
    tmp_path: Path, capsys
):
    code = main(
        [
            "fanout",
            "--item",
            "first",
            "--item",
            "second",
            "--repository",
            str(tmp_path / "absent"),
            "--write",
        ]
    )

    assert code == 2
    assert "does not exist" in capsys.readouterr().err


def test_fanout_cli_expands_a_list_file(tmp_path: Path, capsys):
    listing = tmp_path / "work.md"
    listing.write_text("- first seam\n- second seam\n", encoding="utf-8")

    code = main(["fanout", "--list-file", str(listing), "--format", "json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["goal"] for item in payload["items"]] == ["first seam", "second seam"]
