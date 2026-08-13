from importlib.resources import files
from pathlib import Path

from recurspec.contract import validate_contract

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def test_validate_contract_accepts_a_complete_versioned_atomic_leaf():
    result = validate_contract(FIXTURES / "valid" / "SYSTEM.md")

    assert result.valid
    assert result.diagnostics == ()
    assert len(result.contracts) == 1
    assert result.contracts[0]["contract_version"] == "1.0"
    assert result.contracts[0]["atomic_leaf"] is True


def test_validate_contract_reports_explicit_stable_migration_diagnostics():
    result = validate_contract(FIXTURES)

    assert not result.valid
    assert [diagnostic.rule_code for diagnostic in result.diagnostics] == [
        "contract.heading.missing",
        "contract.invariant.ears",
        "contract.invariant.evidence-stage",
        "contract.version.missing",
    ]
    assert "section 8" in result.diagnostics[0].message
    assert "EARS" in result.diagnostics[1].message
    assert "Evidence Stage" in result.diagnostics[2].message
    assert "recurspec-contract: 1.0" in result.diagnostics[3].message


def test_contract_schema_is_a_bundled_package_resource():
    schema = files("recurspec").joinpath("schemas/contract-node-1.0.schema.json")

    assert schema.is_file()
    assert '"https://json-schema.org/draft/2020-12/schema"' in schema.read_text(encoding="utf-8")
