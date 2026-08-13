from pathlib import Path

import pytest

from recurspec.technology_resolver import (
    ResolutionInstrumentError,
    audit_resolutions,
    load_dependency_inventory,
)


def _leaf(section_eight: str, implementation: str = "src/adapter.py") -> str:
    return f"""# Example (L1)

<!-- recurspec-contract: 1.0 -->

## 1. System Intent & Responsibility

Exercise resolution auditing.

## 2. Sub-System Decomposition

Atomic leaf.

## 3. Interface Contracts

- **Inputs:** Request.
- **Outputs:** Response.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** THE SYSTEM SHALL preserve its declared seam.
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Fixture.

## 6. Leaf Execution & Test Seam

- **Implementation:** `{implementation}`.
- **Tests:** `tests/test_adapter.py`.

## 7. Measurement Seams

- **Primary metric:** fixture result.

## 8. Technology Resolution

{section_eight}
"""


def _complete_resolution(decision_class: str = "ADOPT", pin: str = "1.0.0") -> str:
    return f"""- **Decision class:** {decision_class}
- **Selected:** Example SDK.
- **Dependency:** example-sdk
- **Pin:** {pin}
- **Standard / protocol:** none.
- **Alternatives considered:** Example alternative rejected for fit.
- **Fit gap:** Domain translation.
- **Seam:** `src/adapter.py`.
- **Adapter namespace:** `src`.
- **Exit cost:** LOW.
- **Cost model:** No service spend.
- **Liability transferred:** Parsing maintenance.
- **Operational owner:** us.
- **Failure mode:** Request fails closed.
- **Open questions:** none.
"""


def _write_tree(tmp_path: Path, section_eight: str, implementation: str = "src/adapter.py"):
    contract = tmp_path / "docs" / "architecture" / "SYSTEM.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(_leaf(section_eight, implementation), encoding="utf-8")
    for relative in ["src/adapter.py", "tests/test_adapter.py"]:
        path = tmp_path / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text("def seam():\n    pass\n", encoding="utf-8")
    return contract.parent


def test_resolution_audit_detects_pin_drift_against_authoritative_inventory(tmp_path: Path):
    tree = _write_tree(tmp_path, _complete_resolution(pin="1.0.0"))

    stale = audit_resolutions(tmp_path, contract_root=tree, inventory={"example-sdk": "2.0.0"})
    current = audit_resolutions(tmp_path, contract_root=tree, inventory={"example-sdk": "1.0.0"})

    assert [item.code for item in stale.diagnostics] == ["resolution.pin.stale"]
    assert current.valid


def test_resolution_audit_reports_incomplete_fields_and_refuses_vendor_on_defer(tmp_path: Path):
    incomplete = _complete_resolution().replace("- **Fit gap:** Domain translation.\n", "")
    incomplete = incomplete.replace("ADOPT", "DEFER").replace("Example SDK", "Real Vendor")
    tree = _write_tree(tmp_path, incomplete)

    result = audit_resolutions(tmp_path, contract_root=tree, inventory={})

    assert {item.code for item in result.diagnostics} == {
        "resolution.defer.vendor_selected",
        "resolution.defer.ticket_missing",
        "resolution.field.missing",
    }


def test_resolution_audit_is_indeterminate_without_inventory_for_an_external_pin(tmp_path: Path):
    tree = _write_tree(tmp_path, _complete_resolution())

    result = audit_resolutions(tmp_path, contract_root=tree)

    assert result.indeterminate
    assert result.diagnostics[0].code == "resolution.inventory.unavailable"


def test_resolution_audit_reopens_a_wrap_that_spreads_past_or_outgrows_its_seam(tmp_path: Path):
    resolution = _complete_resolution(decision_class="WRAP")
    tree = _write_tree(tmp_path, resolution, "src/adapter.py")
    (tmp_path / "src" / "workaround.py").write_text("def workaround():\n    pass\n")
    (tmp_path / "src" / "adapter.py").write_text("\n".join(["# adapter"] * 6))

    result = audit_resolutions(
        tmp_path,
        contract_root=tree,
        inventory={"example-sdk": "1.0.0"},
        wrap_line_limit=5,
    )

    assert {item.code for item in result.diagnostics} == {
        "resolution.wrap.bloat",
        "resolution.wrap.seam_spread",
    }


def test_dependency_inventory_normalizes_package_keys_without_altering_versions(tmp_path: Path):
    inventory = tmp_path / "inventory.json"
    inventory.write_text('{"Example_SDK":"1.0.0"}', encoding="utf-8")

    assert load_dependency_inventory(inventory) == {"example-sdk": "1.0.0"}


@pytest.mark.parametrize("floating", ["latest", ">=1.0", "*", "1.x", "^1.0.0"])
def test_dependency_inventory_rejects_a_floating_version(tmp_path: Path, floating):
    inventory = tmp_path / "inventory.json"
    inventory.write_text(f'{{"example-sdk":"{floating}"}}', encoding="utf-8")

    with pytest.raises(ResolutionInstrumentError, match="floating"):
        load_dependency_inventory(inventory)


def test_resolution_audit_flags_a_floating_pin_even_when_the_inventory_agrees(tmp_path: Path):
    # Reproduces the review's exact scenario: an inventory and §8 Pin that both say
    # "latest" pass plain string equality, but neither is an exact, reproducible pin.
    tree = _write_tree(tmp_path, _complete_resolution(pin="latest"))

    result = audit_resolutions(tmp_path, contract_root=tree, inventory={"example-sdk": "latest"})

    assert "resolution.pin.not_exact" in {item.code for item in result.diagnostics}
    assert "resolution.pin.stale" not in {item.code for item in result.diagnostics}


def test_resolution_audit_refuses_a_missing_wrap_namespace(tmp_path: Path):
    tree = _write_tree(tmp_path, _complete_resolution(decision_class="WRAP"))
    contract = tree / "SYSTEM.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(
            "- **Adapter namespace:** `src`.",
            "- **Adapter namespace:** `missing-adapters`.",
        ),
        encoding="utf-8",
    )

    result = audit_resolutions(
        tmp_path, contract_root=tree, inventory={"example-sdk": "1.0.0"}
    )

    assert "resolution.wrap.namespace_missing" in {item.code for item in result.diagnostics}
