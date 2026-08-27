#!/usr/bin/env python3
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "canonical_evidence_v1.schema.json"
VALIDATOR = ROOT / "schemas" / "validate_canonical_evidence_v1.py"
FIXTURES = ROOT / "tests" / "fixtures" / "canonical_evidence_v1"
VALID = FIXTURES / "valid_bundle.json"
INVALID_CASES = FIXTURES / "invalid_cases.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("canonical_evidence_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VALIDATOR_MODULE = load_validator()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_local_ref(schema: dict, ref: str):
    assert ref.startswith("#/")
    value = schema
    for part in ref[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def apply_case(document: dict, case: dict) -> None:
    target = document
    for part in case["path"][:-1]:
        target = target[part]
    leaf = case["path"][-1]
    if case.get("operation") == "reverse":
        target[leaf].reverse()
    else:
        target[leaf] = case["value"]


def test_schema_is_draft_2020_12_and_all_local_refs_resolve():
    schema = load_json(SCHEMA)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"] == {"const": "1.0.0"}
    assert {
        "project",
        "source",
        "transcriptRevision",
        "cue",
        "word",
        "benchmarkSegment",
        "topic",
        "evidenceRef",
    } <= schema["$defs"].keys()
    for node in walk_json(schema):
        if "$ref" in node:
            assert resolve_local_ref(schema, node["$ref"])


def test_valid_fixture_passes_all_cross_record_invariants():
    document = load_json(VALID)
    assert VALIDATOR_MODULE.validate_bundle(document) == []


def test_valid_fixture_uses_deterministic_canonical_serialization():
    document = load_json(VALID)
    canonical = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert VALID.read_text(encoding="utf-8") == canonical


def test_invalid_fixtures_fail_for_the_expected_invariant():
    valid = load_json(VALID)
    cases = load_json(INVALID_CASES)
    assert len(cases) >= 5
    for case in cases:
        document = copy.deepcopy(valid)
        apply_case(document, case)
        errors = VALIDATOR_MODULE.validate_bundle(document)
        assert errors, case["name"]
        assert any(case["expected_error"] in error for error in errors), (
            case["name"],
            errors,
        )


def test_cli_accepts_valid_fixture():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(VALID)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.rstrip().endswith(": VALID")


if __name__ == "__main__":
    test_schema_is_draft_2020_12_and_all_local_refs_resolve()
    test_valid_fixture_passes_all_cross_record_invariants()
    test_valid_fixture_uses_deterministic_canonical_serialization()
    test_invalid_fixtures_fail_for_the_expected_invariant()
    test_cli_accepts_valid_fixture()
    print("Canonical Evidence Schema v1 tests passed")
