from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json"
SLICE = ROOT / "analysis/golden_knowledge_slice/golden_knowledge_slice.json"
EVIDENCE = ROOT / "analysis/word_timeline_mvp/canonical_evidence_bundle.json"
VALIDATOR = ROOT / "schemas/validate_canonical_knowledge_v1.py"
SCHEMA = ROOT / "schemas/canonical_knowledge_v1.schema.json"
LIFECYCLE = ROOT / "schemas/canonical_knowledge_lifecycle_v1.json"


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


def assert_invalid(document, layer=None):
    result = errors(document)
    assert result
    if layer:
        assert any(error.startswith(layer) for error in result), result
    return result


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


def test_accepted_golden_slice_and_knowledge_fixture_hashes_are_unchanged():
    assert hashlib.sha256(SLICE.read_bytes()).hexdigest() == "177d030a6ac3e3dc0a28d655db0f12321e09caba8eff494c078aeb828339d4d6"
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == "21470fa1d903254aa51d2d5aed9666dfae6a48419cbaab755300ce71374892d0"


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
    assert_invalid(document, "L1_SCHEMA")


def test_dangling_reference_fails_closed(document):
    document["topics"][0]["concept_refs"].append("concept_missing")
    assert any("dangling reference" in e for e in errors(document))


def test_invalid_lifecycle_is_rejected(document):
    document["concepts"][0]["status"] = "AUTO_ACCEPTED"
    assert_invalid(document, "L1_SCHEMA")


def test_review_decision_accept_mechanics(document):
    document["concepts"][0]["status"] = "ACCEPTED"
    document["review_decisions"].append({
        "id": "decision_accept_concept", "action": "ACCEPT",
        "target_ids": ["concept_adaptation_to_environment"], "result_ids": ["concept_adaptation_to_environment"],
        "reason": "human decision placeholder", "actor_type": "human_domain_reviewer", "timestamp": "2026-01-01T00:00:00Z",
        "input_version": 1, "output_version": 1,
        "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]},
    })
    assert errors(document) == []


def test_rename_preserves_identity(document):
    document["review_decisions"].append({
        "id": "decision_rename_concept", "action": "RENAME", "target_ids": ["concept_adaptation_to_environment"],
        "result_ids": ["concept_adaptation_to_environment"], "reason": "placeholder mechanics", "actor_type": "human_domain_reviewer",
        "timestamp": "2026-01-01T00:00:00Z", "input_version": 1, "output_version": 2,
        "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]},
    })
    assert errors(document) == []


def test_rename_changing_identity_is_rejected(document):
    d = {"id": "decision_bad_rename", "action": "RENAME", "target_ids": ["concept_adaptation_to_environment"], "result_ids": ["concept_survival_in_changing_environment"], "reason": "bad", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z", "input_version": 1, "output_version": 2, "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]}}
    document["review_decisions"].append(d)
    assert any("RENAME must preserve identity" in e for e in errors(document))


def test_merge_requires_two_targets_and_split_two_results(document):
    base = {"id": "decision_lineage", "reason": "mechanics only", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z", "input_version": 1, "output_version": 2, "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]}}
    document["review_decisions"] = [dict(base, action="MERGE", target_ids=["concept_adaptation_to_environment"], result_ids=["concept_survival_in_changing_environment"])]
    assert any("MERGE requires at least two" in e for e in errors(document))
    document["review_decisions"] = [dict(base, action="SPLIT", target_ids=["concept_adaptation_to_environment"], result_ids=["concept_survival_in_changing_environment"])]
    assert any("SPLIT requires at least two" in e for e in errors(document))


def test_rejected_and_superseded_lifecycles_require_explicit_domain_review(document):
    document["concepts"][0]["status"] = "REJECTED"
    document["concepts"][1]["status"] = "SUPERSEDED"
    result = assert_invalid(document, "L4_LIFECYCLE")
    assert any("REJECTED requires explicit REJECT" in error for error in result)
    assert any("SUPERSEDED requires explicit MERGE/SPLIT" in error for error in result)


def test_versioned_correction_requires_monotonic_versions(document):
    document["review_decisions"].append({"id": "decision_correction", "action": "DEFER", "target_ids": ["concept_adaptation_to_environment"], "result_ids": [], "reason": "correction pending", "actor_type": "system_validator", "timestamp": "2026-01-01T00:00:00Z", "input_version": 2, "output_version": 1, "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]}})
    assert any("output_version cannot precede" in e for e in errors(document))


def test_conflicting_evidence_can_be_represented_without_collapsing(document):
    document["relations"].append({"id": "relation_conflict", "source_concept_id": "concept_adaptation_to_environment", "target_concept_id": "concept_survival_in_changing_environment", "relation_type": "contradicts", "status": "PROVISIONAL", "provenance": {"origin": "canonical_evidence", "source_artifact_id": document["canonical_evidence"]["artifact_id"]}, "evidence_refs": ["evidence_adaptive_task", "evidence_survival_environment"], "version": 1})
    assert errors(document) == []


def test_absolute_paths_are_rejected(document):
    document["source_evidence"]["path"] = "/Users/example/golden.json"
    assert_invalid(document, "L1_SCHEMA")


def test_canonical_evidence_pointer_must_match_loaded_artifact(document):
    document["canonical_evidence"]["artifact_id"] = "artifact_other"
    assert any("does not match loaded Canonical Evidence" in e for e in errors(document))


def test_golden_slice_source_identities_are_not_rewritten(document):
    document["concepts"][0]["id"] = "concept_rewritten"
    assert any("source concepts identity missing" in e for e in errors(document))


def test_cli_accepts_fixture():
    result = subprocess.run([sys.executable, str(VALIDATOR), str(FIXTURE), "--canonical-evidence", str(EVIDENCE), "--source-slice", str(SLICE)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.rstrip().endswith(": VALID")


def test_cli_rejects_schema_invalid_document(tmp_path, document):
    document["unexpected_top_level"] = True
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(invalid), "--canonical-evidence", str(EVIDENCE), "--source-slice", str(SLICE)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "INVALID" in result.stdout
    assert "L1_SCHEMA" in result.stdout


def test_jsonschema_is_the_authoritative_structural_validator():
    validator = V._schema_validator()
    assert validator is not None
    assert validator.__class__.__name__ == "Draft202012Validator"


def test_missing_jsonschema_dependency_fails_clearly(monkeypatch, document):
    V._schema_validator.cache_clear()
    monkeypatch.setattr(V, "Draft202012Validator", None)
    result = errors(document)
    assert result == [
        "L1_SCHEMA $.dependency: jsonschema is required for authoritative "
        "Canonical Knowledge structural validation; install the supported dev_test profile"
    ]
    V._schema_validator.cache_clear()


@pytest.mark.parametrize(
    ("mutation", "description"),
    [
        (lambda value: value.pop("artifact_type"), "missing required top-level field"),
        (lambda value: value.__setitem__("unexpected", True), "unknown top-level field"),
        (lambda value: value["concepts"][0].__setitem__("unexpected", True), "unknown Concept field"),
        (lambda value: value.__setitem__("version", "1"), "wrong primitive type"),
        (lambda value: value["concepts"][0].__setitem__("status", "AUTO_ACCEPTED"), "invalid enum"),
        (lambda value: value["concepts"][0].__setitem__("id", "Bad ID"), "invalid stable ID form"),
        (lambda value: value["topics"][0]["provenance"].pop("origin"), "malformed provenance"),
        (lambda value: value["topics"][0]["source_scope"].pop("source_ids"), "malformed source scope"),
        (lambda value: value["topics"][0].__setitem__("temporal_scope", {"start_seconds": "zero"}), "malformed temporal evidence"),
        (
            lambda value: value["review_decisions"].append(
                {
                    "id": "decision_missing_reason",
                    "action": "DEFER",
                    "target_ids": ["concept_adaptation_to_environment"],
                    "result_ids": [],
                    "actor_type": "system_validator",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "input_version": 1,
                    "output_version": 1,
                    "provenance": {"origin": "derived", "source_artifact_id": value["artifact_id"]},
                }
            ),
            "malformed ReviewDecision",
        ),
        (
            lambda value: value["relations"].append(
                {
                    "id": "relation_missing_target",
                    "source_concept_id": "concept_adaptation_to_environment",
                    "relation_type": "supports",
                    "status": "PROVISIONAL",
                    "provenance": {"origin": "derived", "source_artifact_id": value["artifact_id"]},
                    "evidence_refs": [],
                    "version": 1,
                }
            ),
            "malformed Relation",
        ),
        (lambda value: value["source_evidence"].__setitem__("path", "/Users/example/golden.json"), "forbidden absolute path"),
        (lambda value: value.__setitem__("schema_version", "2.0.0"), "unsupported contract version"),
    ],
)
def test_structural_negative_cases_fail_closed(document, mutation, description):
    mutation(document)
    assert_invalid(document, "L1_SCHEMA")


def test_malformed_relation_registry_entry_fails_closed(document):
    document["relation_type_registry"][0]["description"] = 42
    assert_invalid(document, "L1_SCHEMA")


def test_inverted_source_and_temporal_scopes_fail_at_field_layer(document):
    document["topics"][0]["source_scope"].update(order_start=9, order_end=2)
    document["topics"][0]["temporal_scope"] = {"start_seconds": 20.0, "end_seconds": 10.0}
    result = assert_invalid(document, "L2_FIELD")
    assert any("order_end precedes order_start" in error for error in result)
    assert any("end_seconds must follow start_seconds" in error for error in result)


def test_machine_specific_string_outside_pointer_fails_portability_layer(document):
    document["concepts"][0]["provenance"]["notes"] = "/Users/example/private/source.json"
    assert_invalid(document, "L2_FIELD")


def test_lifecycle_contract_keeps_source_and_knowledge_dimensions_separate():
    contract = load(LIFECYCLE)
    assert contract["dimensions"]["source_status"] != contract["dimensions"]["knowledge_lifecycle"]
    assert set(contract["source_statuses"]) == {"gold_complete", "product_review_required"}
    assert set(contract["knowledge_lifecycles"]) == {"PROVISIONAL", "ACCEPTED", "REJECTED", "SUPERSEDED"}
    assert contract["invariants"]["gold_complete_implicitly_equals_accepted"] is False
    assert contract["domain_authoring"]["required_for_existing_mapping"] is False


def test_active_canonical_artifacts_have_no_absolute_local_paths(document):
    active = [document, load(LIFECYCLE)]
    forbidden = [
        (path, value)
        for artifact in active
        for path, value in V._walk_strings(artifact)
        if V._path_forbidden(value)
    ]
    assert forbidden == []


def test_gold_complete_is_auto_safe_only_as_provisional_without_review(document):
    topic = document["topics"][0]
    assert topic["provenance"]["source_status"] == "gold_complete"
    assert topic["status"] == "PROVISIONAL"
    assert errors(document) == []
    topic["status"] = "ACCEPTED"
    assert any("ACCEPTED requires explicit ACCEPT DOMAIN_REVIEW" in error for error in errors(document))


def test_explicit_human_review_can_accept_without_rewriting_source_status(document):
    topic = document["topics"][0]
    topic["status"] = "ACCEPTED"
    document["review_decisions"].append(
        {
            "id": "decision_accept_gold_source_topic",
            "action": "ACCEPT",
            "target_ids": [topic["id"]],
            "result_ids": [topic["id"]],
            "reason": "explicit domain review fixture",
            "actor_type": "human_domain_reviewer",
            "timestamp": "2026-01-01T00:00:00Z",
            "input_version": 1,
            "output_version": 1,
            "provenance": {"origin": "human_review", "source_artifact_id": document["artifact_id"]},
        }
    )
    assert errors(document) == []
    assert topic["provenance"]["source_status"] == "gold_complete"


def test_system_validator_cannot_semantically_accept(document):
    concept = document["concepts"][0]
    concept["status"] = "ACCEPTED"
    document["review_decisions"].append(
        {
            "id": "decision_invalid_auto_accept",
            "action": "ACCEPT",
            "target_ids": [concept["id"]],
            "result_ids": [concept["id"]],
            "reason": "invalid automatic semantic decision",
            "actor_type": "system_validator",
            "timestamp": "2026-01-01T00:00:00Z",
            "input_version": 1,
            "output_version": 1,
            "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]},
        }
    )
    assert any("system_validator cannot perform semantic action ACCEPT" in error for error in errors(document))


def test_auto_defer_is_mechanical_and_preserves_provisional_state(document):
    concept = document["concepts"][0]
    document["review_decisions"].append(
        {
            "id": "decision_auto_defer",
            "action": "DEFER",
            "target_ids": [concept["id"]],
            "result_ids": [],
            "reason": "semantic review remains required",
            "actor_type": "system_validator",
            "timestamp": "2026-01-01T00:00:00Z",
            "input_version": 1,
            "output_version": 1,
            "provenance": {"origin": "derived", "source_artifact_id": document["artifact_id"]},
        }
    )
    assert concept["status"] == "PROVISIONAL"
    assert errors(document) == []


def test_superseded_lineage_requires_and_accepts_explicit_merge_decision(document):
    source = document["concepts"][0]
    duplicate = document["concepts"][1]
    result = document["concepts"][2]
    source["status"] = "SUPERSEDED"
    duplicate["status"] = "SUPERSEDED"
    source["redirects"] = [result["id"]]
    duplicate["redirects"] = [result["id"]]
    document["review_decisions"].append(
        {
            "id": "decision_merge_lineage",
            "action": "MERGE",
            "target_ids": [source["id"], duplicate["id"]],
            "result_ids": [result["id"]],
            "reason": "explicit lineage mechanics fixture",
            "actor_type": "human_domain_reviewer",
            "timestamp": "2026-01-01T00:00:00Z",
            "input_version": 1,
            "output_version": 2,
            "provenance": {"origin": "human_review", "source_artifact_id": document["artifact_id"]},
        }
    )
    assert errors(document) == []


def test_unknown_source_status_fails_lifecycle_layer(document):
    document["topics"][0]["provenance"]["source_status"] = "invented_status"
    assert any("unsupported source status" in error for error in assert_invalid(document, "L4_LIFECYCLE"))
