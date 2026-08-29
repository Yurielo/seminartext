from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json"
SLICE = ROOT / "analysis/golden_knowledge_slice/golden_knowledge_slice.json"
EVIDENCE = ROOT / "analysis/word_timeline_mvp/canonical_evidence_bundle.json"
VALIDATOR = ROOT / "schemas/validate_canonical_knowledge_v1.py"
SCHEMA = ROOT / "schemas/canonical_knowledge_v1.schema.json"


def _load_validator():
    spec = importlib.util.spec_from_file_location("knowledge_validator", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _load_validator()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def document():
    return load(FIXTURE)


def errors(document):
    return V.validate_knowledge(document, load(EVIDENCE), load(SLICE))


def test_golden_slice_contract_is_valid_and_counts_are_preserved(document):
    assert errors(document) == []
    assert len(document["topics"]) == 3
    assert len(document["concepts"]) == 7
    assert len(load(SLICE)["evidence"]) == 10


def test_schema_is_draft_2020_12_with_resolvable_local_refs():
    schema = load(SCHEMA)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"] == {"const": "1.0.0"}
    assert {"project", "seminar", "topic", "concept", "relation", "review_decision"} <= set(schema["$defs"])

    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    for node in walk(schema):
        if "$ref" in node:
            ref = node["$ref"]
            assert ref.startswith("#/")
            target = schema
            for part in ref[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]


def test_fixture_is_deterministically_serialized():
    expected = json.dumps(load(FIXTURE), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert FIXTURE.read_text(encoding="utf-8") == expected


def test_project_and_seminar_have_distinct_stable_id_spaces(document):
    assert document["project"]["id"] != document["seminars"][0]["id"]
    assert document["seminars"][0]["project_id"] == document["project"]["id"]


def test_concepts_are_provisional_and_identity_is_not_label(document):
    assert all(c["status"] == "PROVISIONAL" for c in document["concepts"])
    document["concepts"][0]["preferred_label"] = "renamed label"
    assert document["concepts"][0]["id"] == "concept_adaptation_to_environment"
    assert errors(document) == []


def test_valid_provisional_relation(document):
    document["relations"].append({
        "id": "relation_supports_adaptation",
        "source_concept_id": "concept_adaptation_to_environment",
        "target_concept_id": "concept_survival_in_changing_environment",
        "relation_type": "supports", "status": "PROVISIONAL",
        "provenance": {"origin": "canonical_evidence", "source_artifact_id": document["canonical_evidence"]["artifact_id"]},
        "evidence_refs": ["evidence_adaptive_task"], "version": 1,
    })
    assert errors(document) == []


def test_controlled_relation_registry_rejects_unrestricted_type(document):
    document["relations"].append({
        "id": "relation_unrestricted", "source_concept_id": "concept_adaptation_to_environment",
        "target_concept_id": "concept_survival_in_changing_environment", "relation_type": "causes",
        "status": "PROVISIONAL", "provenance": {"origin": "canonical_evidence", "source_artifact_id": document["canonical_evidence"]["artifact_id"]},
        "evidence_refs": [], "version": 1,
    })
    assert any("not in controlled registry" in e for e in errors(document))


def test_dangling_reference_fails_closed(document):
    document["topics"][0]["concept_refs"].append("concept_missing")
    assert any("dangling reference" in e for e in errors(document))


def test_invalid_lifecycle_is_rejected(document):
    document["concepts"][0]["status"] = "AUTO_ACCEPTED"
    assert any("invalid lifecycle" in e for e in errors(document))


def test_review_decision_accept_mechanics(document):
    document["review_decisions"].append({
        "id": "decision_accept_concept", "action": "ACCEPT",
        "target_ids": ["concept_adaptation_to_environment"], "result_ids": ["concept_adaptation_to_environment"],
        "reason": "human decision placeholder", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z",
        "input_version": 1, "output_version": 1,
        "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]},
    })
    assert errors(document) == []


def test_rename_preserves_identity(document):
    document["review_decisions"].append({
        "id": "decision_rename_concept", "action": "RENAME", "target_ids": ["concept_adaptation_to_environment"],
        "result_ids": ["concept_adaptation_to_environment"], "reason": "placeholder mechanics", "actor_type": "system_validator",
        "timestamp": "2026-01-01T00:00:00Z", "input_version": 1, "output_version": 2,
        "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]},
    })
    assert errors(document) == []


def test_rename_changing_identity_is_rejected(document):
    d = {"id": "decision_bad_rename", "action": "RENAME", "target_ids": ["concept_adaptation_to_environment"], "result_ids": ["concept_survival_in_changing_environment"], "reason": "bad", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z", "input_version": 1, "output_version": 2, "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]}}
    document["review_decisions"].append(d)
    assert any("RENAME must preserve concept identity" in e for e in errors(document))


def test_merge_requires_two_targets_and_split_two_results(document):
    base = {"id": "decision_lineage", "reason": "mechanics only", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z", "input_version": 1, "output_version": 2, "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]}}
    document["review_decisions"] = [dict(base, action="MERGE", target_ids=["concept_adaptation_to_environment"], result_ids=["concept_survival_in_changing_environment"])]
    assert any("MERGE requires at least two" in e for e in errors(document))
    document["review_decisions"] = [dict(base, action="SPLIT", target_ids=["concept_adaptation_to_environment"], result_ids=["concept_survival_in_changing_environment"])]
    assert any("SPLIT requires at least two" in e for e in errors(document))


def test_rejected_and_superseded_lifecycles_are_supported(document):
    document["concepts"][0]["status"] = "REJECTED"
    document["concepts"][1]["status"] = "SUPERSEDED"
    assert errors(document) == []


def test_versioned_correction_requires_monotonic_versions(document):
    document["review_decisions"].append({"id": "decision_correction", "action": "DEFER", "target_ids": ["concept_adaptation_to_environment"], "result_ids": [], "reason": "correction pending", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z", "input_version": 2, "output_version": 1, "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]}})
    assert any("output_version cannot precede" in e for e in errors(document))


def test_conflicting_evidence_can_be_represented_without_collapsing(document):
    document["relations"].append({"id": "relation_conflict", "source_concept_id": "concept_adaptation_to_environment", "target_concept_id": "concept_survival_in_changing_environment", "relation_type": "contradicts", "status": "PROVISIONAL", "provenance": {"origin": "canonical_evidence", "source_artifact_id": document["canonical_evidence"]["artifact_id"]}, "evidence_refs": ["evidence_adaptive_task", "evidence_survival_environment"], "version": 1})
    assert errors(document) == []


def test_absolute_paths_are_rejected(document):
    document["source_evidence"]["path"] = "/Users/example/golden.json"
    assert any("absolute or machine-specific path" in e for e in errors(document))


def test_canonical_evidence_pointer_must_match_loaded_artifact(document):
    document["canonical_evidence"]["artifact_id"] = "artifact_other"
    assert any("does not match loaded Canonical Evidence" in e for e in errors(document))


def test_golden_slice_source_identities_are_not_rewritten(document):
    document["concepts"][0]["id"] = "concept_rewritten"
    assert any("source concepts identity missing" in e for e in errors(document))


def test_cli_accepts_fixture():
    import subprocess, sys
    result = subprocess.run([sys.executable, str(VALIDATOR), str(FIXTURE), "--canonical-evidence", str(EVIDENCE), "--source-slice", str(SLICE)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.rstrip().endswith(": VALID")
