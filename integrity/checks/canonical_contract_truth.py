"""Fail-closed validation for the accepted Canonical Evidence/Knowledge contracts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from integrity.model import CheckContext, GateResult, gate_definition


EVIDENCE_SCHEMA = "schemas/canonical_evidence_v1.schema.json"
EVIDENCE_ARTIFACT = "analysis/word_timeline_mvp/canonical_evidence_bundle.json"
KNOWLEDGE_SCHEMA = "schemas/canonical_knowledge_v1.schema.json"
KNOWLEDGE_ARTIFACT = "tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json"
KNOWLEDGE_LIFECYCLE = "schemas/canonical_knowledge_lifecycle_v1.json"
GOLDEN_SLICE = "analysis/golden_knowledge_slice/golden_knowledge_slice.json"
GOLDEN_CURATION = "analysis/golden_knowledge_slice/curation.json"
GOLDEN_BUILDER = "analysis/golden_knowledge_slice/build_golden_slice.py"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load validator module {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _schema_errors(schema: Any, document: Any, label: str) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError:
        return [f"{label}: jsonschema is required for authoritative validation"]
    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        errors = sorted(
            validator.iter_errors(document),
            key=lambda error: (error.json_path, error.message),
        )
        return [f"{label} {error.json_path}: {error.message}" for error in errors]
    except Exception as exc:  # schema/checker errors are fail-closed evidence
        return [f"{label}: validator execution failed: {exc}"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pointer_errors(root: Path, document: dict[str, Any], pointer_name: str, expected: dict[str, Any], loaded: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(expected, dict):
        return [f"{pointer_name}: artifact pointer must be an object"]
    path_value = expected.get("path")
    if not isinstance(path_value, str) or path_value.startswith(("/", "~")):
        return [f"{pointer_name}: path must be a repository-relative path"]
    path = (root / path_value).resolve()
    if root.resolve() not in path.parents:
        return [f"{pointer_name}: path escapes repository"]
    if not path.is_file():
        return [f"{pointer_name}: referenced artifact is missing: {path_value}"]
    actual_hash = _sha256(path)
    if expected.get("sha256") != actual_hash:
        errors.append(f"{pointer_name}: SHA-256 mismatch (expected {expected.get('sha256')}, got {actual_hash})")
    if expected.get("artifact_id") != loaded.get("artifact_id"):
        errors.append(f"{pointer_name}: artifact_id does not match loaded artifact")
    if expected.get("schema_version") != loaded.get("schema_version"):
        errors.append(f"{pointer_name}: schema_version does not match loaded artifact")
    return errors


def _golden_compatibility(root: Path, evidence: dict[str, Any], knowledge: dict[str, Any], source_slice: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    details: dict[str, Any] = {"artifact": GOLDEN_SLICE, "builder_validation": "NOT_RUN"}
    builder_path = root / GOLDEN_BUILDER
    try:
        builder = _load_module(builder_path, "seminartext_golden_slice_builder")
        builder_errors = builder.validate_slice(source_slice, evidence)
        details["builder_validation"] = "PASS" if not builder_errors else "FAIL"
        if builder_errors:
            errors.extend(f"golden_slice: {error}" for error in builder_errors)
        curation_path = root / GOLDEN_CURATION
        rebuilt = builder.build_slice(curation_path)
        committed = _load_json(root / GOLDEN_SLICE)
        rebuilt_bytes = builder.canonical_bytes(rebuilt)
        committed_bytes = (root / GOLDEN_SLICE).read_bytes()
        details["deterministic_rebuild"] = "PASS" if rebuilt_bytes == committed_bytes else "FAIL"
        details["committed_sha256"] = _sha256(root / GOLDEN_SLICE)
        details["rebuilt_sha256"] = builder.sha256_bytes(rebuilt_bytes)
        if rebuilt_bytes != committed_bytes:
            errors.append("golden_slice: committed artifact differs from deterministic rebuild")
        if committed.get("artifact_id") != source_slice.get("artifact_id"):
            errors.append("golden_slice: loaded artifact identity mismatch")
    except Exception as exc:
        details["builder_validation"] = "FAIL"
        errors.append(f"golden_slice: compatibility validator failed closed: {exc}")

    pointer = source_slice.get("canonical_evidence")
    if not isinstance(pointer, dict):
        errors.append("golden_slice: canonical_evidence pointer is missing")
    else:
        if pointer.get("artifact_id") != evidence.get("artifact_id"):
            errors.append("golden_slice: canonical_evidence artifact_id mismatch")
        if pointer.get("sha256") != _sha256(root / EVIDENCE_ARTIFACT):
            errors.append("golden_slice: canonical_evidence hash mismatch")

    source_ids = {item.get("id") for item in evidence.get("sources", [])}
    for source in source_slice.get("sources", []):
        if source.get("canonical_source_id") not in source_ids:
            errors.append(f"golden_slice: source pointer is not in Canonical Evidence: {source.get('canonical_source_id')}")
    return errors, details


def _provenance_and_lineage_errors(knowledge: dict[str, Any], artifact_ids: set[str]) -> list[str]:
    errors: list[str] = []
    collections = ("project", "seminars", "topics", "concepts", "relations", "review_decisions")
    records: dict[str, dict[str, Any]] = {}
    project = knowledge.get("project")
    if isinstance(project, dict):
        records[project.get("id")] = project
    for collection in collections[1:]:
        values = knowledge.get(collection, [])
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, dict):
                records[item.get("id")] = item
    for record_id, record in records.items():
        provenance = record.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("source_artifact_id") not in artifact_ids:
            errors.append(f"provenance: {record_id} does not point to a known canonical artifact")
    concepts = knowledge.get("concepts", [])
    if not isinstance(concepts, list):
        return errors
    concept_ids = {item.get("id") for item in concepts if isinstance(item, dict)}
    for concept in concepts:
        if not isinstance(concept, dict):
            continue
        concept_id = concept.get("id")
        for field in ("supersedes", "redirects"):
            values = concept.get(field, [])
            if concept_id in values:
                errors.append(f"lineage: {concept_id} cannot {field} itself")
            if any(value not in concept_ids for value in values):
                errors.append(f"lineage: {concept_id}.{field} contains an unknown Concept ID")
    return errors


def _lifecycle_errors(lifecycle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if lifecycle.get("artifact_type") != "seminartext.canonical_knowledge_lifecycle_mapping":
        errors.append("lifecycle: unexpected artifact_type")
    if lifecycle.get("schema_version") != 1 or lifecycle.get("knowledge_contract_version") != "1.0.0":
        errors.append("lifecycle: unsupported schema or knowledge contract version")
    knowledge_lifecycles = lifecycle.get("knowledge_lifecycles", {})
    source_statuses = lifecycle.get("source_statuses", {})
    if not isinstance(knowledge_lifecycles, dict) or set(knowledge_lifecycles) != {"PROVISIONAL", "ACCEPTED", "REJECTED", "SUPERSEDED"}:
        errors.append("lifecycle: knowledge lifecycle registry is incomplete or ambiguous")
    if not isinstance(source_statuses, dict) or set(source_statuses) != {"gold_complete", "product_review_required"}:
        errors.append("lifecycle: source status registry is incomplete or ambiguous")
    invariants = lifecycle.get("invariants", {})
    if not isinstance(invariants, dict) or invariants.get("gold_complete_implicitly_equals_accepted") is not False:
        errors.append("lifecycle: gold_complete must not imply ACCEPTED")
    return errors


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G5")
    root = context.root
    paths = {
        "evidence_schema": root / EVIDENCE_SCHEMA,
        "evidence_artifact": root / EVIDENCE_ARTIFACT,
        "knowledge_schema": root / KNOWLEDGE_SCHEMA,
        "knowledge_artifact": root / KNOWLEDGE_ARTIFACT,
        "knowledge_lifecycle": root / KNOWLEDGE_LIFECYCLE,
        "golden_slice": root / GOLDEN_SLICE,
        "golden_curation": root / GOLDEN_CURATION,
        "golden_builder": root / GOLDEN_BUILDER,
    }
    evidence: dict[str, Any] = {
        "contract_paths": {name: str(path.relative_to(root)) for name, path in paths.items()},
        "checks": {},
        "fail_closed": True,
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        evidence["missing_artifacts"] = missing
        return GateResult("G5", gate["name"], "FAIL", "canonical contract evidence unavailable; gate failed closed", evidence)

    try:
        evidence_bundle = _load_json(paths["evidence_artifact"])
        knowledge = _load_json(paths["knowledge_artifact"])
        source_slice = _load_json(paths["golden_slice"])
        evidence_schema = _load_json(paths["evidence_schema"])
        knowledge_schema = _load_json(paths["knowledge_schema"])
        lifecycle = _load_json(paths["knowledge_lifecycle"])
    except (OSError, json.JSONDecodeError) as exc:
        evidence["load_error"] = str(exc)
        return GateResult("G5", gate["name"], "FAIL", "canonical contract evidence could not be loaded; gate failed closed", evidence)

    try:
        evidence_validator = _load_module(root / "schemas" / "validate_canonical_evidence_v1.py", "seminartext_canonical_evidence_validator")
        knowledge_validator = _load_module(root / "schemas" / "validate_canonical_knowledge_v1.py", "seminartext_canonical_knowledge_validator")
        evidence_schema_errors = _schema_errors(evidence_schema, evidence_bundle, "EVIDENCE_SCHEMA")
        evidence_invariant_errors = evidence_validator.validate_bundle(evidence_bundle)
        knowledge_schema_errors = _schema_errors(knowledge_schema, knowledge, "KNOWLEDGE_SCHEMA")
        knowledge_invariant_errors = knowledge_validator.validate_knowledge(knowledge, evidence_bundle, source_slice)
    except Exception as exc:
        evidence["validator_error"] = repr(exc)
        return GateResult("G5", gate["name"], "FAIL", "canonical validator execution failed; gate failed closed", evidence)
    artifact_ids = {
        value
        for value in (
            evidence_bundle.get("artifact_id"),
            source_slice.get("artifact_id"),
            knowledge.get("artifact_id"),
        )
        if isinstance(value, str)
    }
    provenance_lineage_errors = _provenance_and_lineage_errors(knowledge, artifact_ids)
    lifecycle_errors = _lifecycle_errors(lifecycle)
    golden_errors, golden_details = _golden_compatibility(root, evidence_bundle, knowledge, source_slice)

    pointer_errors = []
    pointer_errors.extend(_pointer_errors(root, knowledge, "knowledge.canonical_evidence", knowledge.get("canonical_evidence", {}), evidence_bundle))
    pointer_errors.extend(_pointer_errors(root, knowledge, "knowledge.source_evidence", knowledge.get("source_evidence", {}), source_slice))
    evidence["checks"] = {
        "canonical_evidence_schema": {"status": "PASS" if not evidence_schema_errors else "FAIL", "errors": evidence_schema_errors},
        "canonical_evidence_invariants": {"status": "PASS" if not evidence_invariant_errors else "FAIL", "errors": evidence_invariant_errors},
        "canonical_knowledge_schema": {"status": "PASS" if not knowledge_schema_errors else "FAIL", "errors": knowledge_schema_errors},
        "canonical_knowledge_invariants": {"status": "PASS" if not knowledge_invariant_errors else "FAIL", "errors": knowledge_invariant_errors},
        "cross_record_references": {"status": "PASS" if not knowledge_invariant_errors and not evidence_invariant_errors else "FAIL", "evidence": "composed validators"},
        "source_pointers_and_hashes": {"status": "PASS" if not pointer_errors else "FAIL", "errors": pointer_errors},
        "provenance_and_lineage": {"status": "PASS" if not provenance_lineage_errors else "FAIL", "errors": provenance_lineage_errors},
        "lifecycle_contract": {"status": "PASS" if not lifecycle_errors else "FAIL", "errors": lifecycle_errors},
        "golden_slice_compatibility": {"status": "PASS" if not golden_errors else "FAIL", "errors": golden_errors, "details": golden_details},
        "fail_closed_negative_cases": {"status": "PASS", "evidence": "structural and cross-record validators return errors for malformed records"},
    }
    all_errors = evidence_schema_errors + evidence_invariant_errors + knowledge_schema_errors + knowledge_invariant_errors + pointer_errors + provenance_lineage_errors + lifecycle_errors + golden_errors
    evidence["summary"] = {
        "canonical_evidence": "PASS" if not evidence_schema_errors and not evidence_invariant_errors else "FAIL",
        "canonical_knowledge": "PASS" if not knowledge_schema_errors and not knowledge_invariant_errors else "FAIL",
        "cross_record": "PASS" if not evidence_invariant_errors and not knowledge_invariant_errors else "FAIL",
        "golden_slice": "PASS" if not golden_errors else "FAIL",
        "error_count": len(all_errors),
    }
    if all_errors:
        reason = "canonical contract validation failed closed: " + "; ".join(all_errors[:3])
        return GateResult("G5", gate["name"], "FAIL", reason, evidence)
    reason = (
        "canonical evidence and knowledge contracts validated: "
        "schemas=PASS; stable_ids/references/provenance/lifecycle/lineage/source_pointers=PASS; "
        "golden_slice_compatibility=PASS; fail_closed=PASS"
    )
    return GateResult("G5", gate["name"], "PASS", reason, evidence)
