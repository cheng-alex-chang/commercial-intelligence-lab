import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from ttd_lab.contracts import ContractError, load_files, read_document, validate_document, validate_state
from ttd_lab.fixtures import generate


@pytest.fixture(scope="module")
def fixture_inputs(tmp_path_factory):
    root = tmp_path_factory.mktemp("sources")
    generate(root)
    return root


@pytest.fixture
def state(fixture_inputs):
    return {(doc["source"], doc["partition"]): doc
            for _, _, doc in load_files(fixture_inputs / "baseline")}


def test_fixed_seed_reproduces_exact_bytes(fixture_inputs, tmp_path):
    generate(tmp_path)
    first = {str(p.relative_to(fixture_inputs)): p.read_bytes() for p in fixture_inputs.rglob("*.json")}
    second = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*.json")}
    assert first == second
    assert len(list((tmp_path / "baseline").rglob("*.json"))) == 170


def test_fixture_inputs_match_independent_business_expectations(state):
    validate_state(state)
    expected = json.loads(Path("tests/scenario_expectations.json").read_text())
    for account_id, case in expected["accounts"].items():
        for period in ("prior", "current"):
            start = expected["periods"][f"{period}_start"]
            end = expected["periods"][f"{period}_end"]
            missing = False
            total = Decimal("0")
            for coverage in state[("coverage", "all")]["rows"]:
                if start <= coverage["business_date"] <= end and any(
                        k["account_id"] == account_id for k in coverage["expected_keys"]):
                    delivery = state.get(("delivery", f"{coverage['business_date']}:{coverage['channel']}"))
                    if delivery is None:
                        missing = True
                    else:
                        total += sum((Decimal(r["spend_usd"]) for r in delivery["rows"]
                                      if r["account_id"] == account_id), Decimal("0"))
            assert (None if missing else str(total.quantize(Decimal("0.01")))) == case[f"{period}_spend"]


def test_absent_partition_allowed_but_omitted_expected_row_rejected(state):
    validate_state(state)  # Harbor's absent partition is explicitly unknown.
    state[("delivery", "2026-08-31:display")]["rows"].pop()
    with pytest.raises(ContractError, match="expected coverage"):
        validate_state(state)


@pytest.mark.parametrize("value", ["NaN", "-1.00", "1.234", "1e2", 1.00, "99999999999999999.00"])
def test_invalid_money_rejected(state, value):
    doc = state[("delivery", "2026-08-31:display")]
    doc["rows"][0]["spend_usd"] = value
    with pytest.raises(ContractError, match="USD"):
        validate_document(doc)


def test_overlapping_budget_versions_rejected(state):
    duplicate = deepcopy(state[("budgets", "all")]["rows"][0])
    duplicate["effective_from"] = "2026-08-01"
    state[("budgets", "all")]["rows"].append(duplicate)
    with pytest.raises(ContractError, match="Overlapping"):
        validate_state(state)


def test_manifest_calendar_gap_rejected(state):
    rows = state[("coverage", "all")]["rows"]
    rows[:] = [r for r in rows if r["business_date"] != "2026-08-15"]
    with pytest.raises(ContractError, match="calendar has a gap"):
        validate_state(state)


def test_retirement_requires_coordinated_budget_manifest_delivery(state, fixture_inputs):
    events = load_files(fixture_inputs / "events" / "retire_atlas")
    delivery = next(doc for _, _, doc in events if doc["source"] == "delivery")
    state[("delivery", delivery["partition"])] = delivery
    with pytest.raises(ContractError, match="expected coverage"):
        validate_state(state)
    for _, _, doc in events:
        state[(doc["source"], doc["partition"])] = doc
    validate_state(state)


def test_duplicate_json_fields_rejected(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"source":"accounts","source":"delivery"}')
    with pytest.raises(ContractError, match="Duplicate JSON"):
        read_document(path)
