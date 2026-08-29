#!/usr/bin/env python3
"""Dependency-free validator for Canonical Knowledge Contract v1.

The JSON schema defines record shape; this module closes the semantic gaps:
stable IDs, cross-record references, lifecycle/lineage mechanics, and links to
the existing Canonical Evidence and Golden Knowledge Slice artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{2,127}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
LIFECYCLES = {"PROVISIONAL", "ACCEPTED", "REJECTED", "SUPERSEDED"}
ACTIONS = {"ACCEPT", "RENAME", "SPLIT", "MERGE", "REJECT", "DEFER"}
RELATIONS = {"supports", "contradicts", "refines", "depends_on", "associated_with"}
ACTORS = {"human_domain_reviewer", "product_owner", "system_validator"}
COLLECTIONS = ("seminars", "topics", "concepts", "relations", "review_decisions")


def _id(value: Any) -> bool:
    return isinstance(value, str) and ID_RE.fullmatch(value) is not None


def _path_forbidden(value: str) -> bool:
    return value.startswith(("/", "~", "\\")) or bool(re.match(r"^[A-Za-z]:[\\/]", value)) or any(x in value for x in ("/Users/", "/home/", "file://", "vscode://"))


def _walk_strings(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{i}]")


def _required(errors: list[str], obj: Any, path: str, fields: set[str]) -> bool:
    if not isinstance(obj, dict):
        errors.append(f"{path}: expected object")
        return False
    missing = sorted(fields - obj.keys())
    if missing:
        errors.append(f"{path}: missing fields {missing}")
        return False
    return True


def _check_id(errors: list[str], value: Any, path: str) -> None:
    if not _id(value):
        errors.append(f"{path}: invalid stable id")


def _check_refs(errors: list[str], values: Any, path: str, available: set[str]) -> None:
    if not isinstance(values, list):
        errors.append(f"{path}: expected array")
        return
    for i, value in enumerate(values):
        _check_id(errors, value, f"{path}[{i}]")
        if _id(value) and value not in available:
            errors.append(f"{path}[{i}]: dangling reference {value}")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_knowledge(document: Any, evidence_bundle: dict[str, Any] | None = None, source_slice: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if not _required(errors, document, "$", {"schema_version", "artifact_type", "artifact_id", "version", "canonical_evidence", "source_evidence", "project", *COLLECTIONS, "relation_type_registry"}):
        return errors
    if document.get("schema_version") != "1.0.0":
        errors.append("$.schema_version: expected 1.0.0")
    if document.get("artifact_type") != "seminartext.canonical_knowledge":
        errors.append("$.artifact_type: unexpected artifact type")
    _check_id(errors, document.get("artifact_id"), "$.artifact_id")
    if document.get("version") != 1:
        errors.append("$.version: expected 1")

    for path, value in _walk_strings(document):
        if _path_forbidden(value):
            errors.append(f"{path}: absolute or machine-specific path is forbidden")

    pointers = ("canonical_evidence", "source_evidence")
    for name in pointers:
        ptr = document.get(name)
        if _required(errors, ptr, f"$.{name}", {"artifact_id", "schema_version", "sha256", "path"}):
            _check_id(errors, ptr.get("artifact_id"), f"$.{name}.artifact_id")
            if not isinstance(ptr.get("schema_version"), str) or not ptr["schema_version"]:
                errors.append(f"$.{name}.schema_version: expected non-empty string")
            if not SHA_RE.fullmatch(str(ptr.get("sha256", ""))):
                errors.append(f"$.{name}.sha256: expected lowercase SHA-256")
            if not isinstance(ptr.get("path"), str) or _path_forbidden(ptr.get("path", "")):
                errors.append(f"$.{name}.path: expected repository-relative path")

    project = document.get("project")
    if _required(errors, project, "$.project", {"id", "title", "status", "version", "provenance"}):
        _check_id(errors, project.get("id"), "$.project.id")
        if project.get("status") not in LIFECYCLES:
            errors.append("$.project.status: invalid lifecycle")
        if not isinstance(project.get("version"), int) or project["version"] < 1:
            errors.append("$.project.version: expected positive integer")

    records: dict[str, list[dict[str, Any]]] = {}
    all_ids: list[str] = [project.get("id")] if isinstance(project, dict) and _id(project.get("id")) else []
    for name in COLLECTIONS:
        value = document.get(name)
        if not isinstance(value, list):
            errors.append(f"$.{name}: expected array")
            records[name] = []
            continue
        records[name] = [x for x in value if isinstance(x, dict)]
        if len(records[name]) != len(value):
            errors.append(f"$.{name}: every item must be an object")
        for i, item in enumerate(value):
            path = f"$.{name}[{i}]"
            if isinstance(item, dict):
                _check_id(errors, item.get("id"), f"{path}.id")
                if _id(item.get("id")):
                    all_ids.append(item["id"])
    duplicates = sorted({x for x in all_ids if all_ids.count(x) > 1})
    for duplicate in duplicates:
        errors.append(f"$: duplicate stable id {duplicate}")

    project_id = project.get("id") if isinstance(project, dict) else None
    seminar_ids = {x.get("id") for x in records["seminars"] if _id(x.get("id"))}
    topic_ids = {x.get("id") for x in records["topics"] if _id(x.get("id"))}
    concept_ids = {x.get("id") for x in records["concepts"] if _id(x.get("id"))}
    relation_ids = {x.get("id") for x in records["relations"] if _id(x.get("id"))}
    decision_ids = {x.get("id") for x in records["review_decisions"] if _id(x.get("id"))}
    entity_ids = set(all_ids)

    for i, seminar in enumerate(records["seminars"]):
        path = f"$.seminars[{i}]"
        if _required(errors, seminar, path, {"id", "project_id", "title", "status", "version", "provenance", "topic_refs"}):
            if seminar.get("project_id") != project_id:
                errors.append(f"{path}.project_id: must reference project")
            if seminar.get("status") not in LIFECYCLES:
                errors.append(f"{path}.status: invalid lifecycle")
            _check_refs(errors, seminar.get("topic_refs"), f"{path}.topic_refs", topic_ids)
            _check_refs(errors, seminar.get("evidence_refs", []), f"{path}.evidence_refs", set(source_slice and [e.get("id") for e in source_slice.get("evidence", [])] or []))

    evidence_ids = set(e.get("id") for e in (source_slice or {}).get("evidence", []) if _id(e.get("id")))
    source_ids = set(s.get("id") for s in (evidence_bundle or {}).get("sources", []) if _id(s.get("id")))
    revision_ids = set(r.get("id") for r in (evidence_bundle or {}).get("transcript_revisions", []) if _id(r.get("id")))
    for i, topic in enumerate(records["topics"]):
        path = f"$.topics[{i}]"
        if _required(errors, topic, path, {"id", "seminar_id", "source_scope", "title", "summary", "evidence_refs", "concept_refs", "status", "provenance", "version"}):
            if topic.get("seminar_id") not in seminar_ids:
                errors.append(f"{path}.seminar_id: dangling reference")
            scope = topic.get("source_scope")
            if _required(errors, scope, f"{path}.source_scope", {"source_ids", "transcript_revision_ids"}):
                _check_refs(errors, scope.get("source_ids"), f"{path}.source_scope.source_ids", source_ids)
                _check_refs(errors, scope.get("transcript_revision_ids"), f"{path}.source_scope.transcript_revision_ids", revision_ids)
            _check_refs(errors, topic.get("evidence_refs"), f"{path}.evidence_refs", evidence_ids)
            _check_refs(errors, topic.get("concept_refs"), f"{path}.concept_refs", concept_ids)
            if topic.get("status") not in LIFECYCLES:
                errors.append(f"{path}.status: invalid lifecycle")

    for i, concept in enumerate(records["concepts"]):
        path = f"$.concepts[{i}]"
        required = {"id", "preferred_label", "aliases", "status", "scope", "description", "provenance", "evidence_refs", "topic_refs", "version", "created_from", "supersedes", "redirects"}
        if _required(errors, concept, path, required):
            _check_refs(errors, concept.get("evidence_refs"), f"{path}.evidence_refs", evidence_ids)
            _check_refs(errors, concept.get("topic_refs"), f"{path}.topic_refs", topic_ids)
            _check_refs(errors, concept.get("created_from"), f"{path}.created_from", evidence_ids | topic_ids | decision_ids)
            _check_refs(errors, concept.get("supersedes"), f"{path}.supersedes", concept_ids)
            _check_refs(errors, concept.get("redirects"), f"{path}.redirects", concept_ids)
            if concept.get("status") not in LIFECYCLES:
                errors.append(f"{path}.status: invalid lifecycle")
            if not isinstance(concept.get("aliases"), list):
                errors.append(f"{path}.aliases: expected array")

    registry = document.get("relation_type_registry")
    if not isinstance(registry, list) or {x.get("id") for x in registry if isinstance(x, dict)} != RELATIONS:
        errors.append("$.relation_type_registry: must contain exactly the controlled relation registry")
    for i, relation in enumerate(records["relations"]):
        path = f"$.relations[{i}]"
        required = {"id", "source_concept_id", "target_concept_id", "relation_type", "status", "provenance", "evidence_refs", "version"}
        if _required(errors, relation, path, required):
            if relation.get("source_concept_id") not in concept_ids or relation.get("target_concept_id") not in concept_ids:
                errors.append(f"{path}: relation endpoint must reference a Concept")
            if relation.get("relation_type") not in RELATIONS:
                errors.append(f"{path}.relation_type: not in controlled registry")
            _check_refs(errors, relation.get("evidence_refs"), f"{path}.evidence_refs", evidence_ids)
            if relation.get("status") not in LIFECYCLES:
                errors.append(f"{path}.status: invalid lifecycle")

    for i, decision in enumerate(records["review_decisions"]):
        path = f"$.review_decisions[{i}]"
        required = {"id", "action", "target_ids", "result_ids", "reason", "actor_type", "timestamp", "input_version", "output_version", "provenance"}
        if _required(errors, decision, path, required):
            action = decision.get("action")
            if action not in ACTIONS:
                errors.append(f"{path}.action: invalid action")
            _check_refs(errors, decision.get("target_ids"), f"{path}.target_ids", entity_ids)
            _check_refs(errors, decision.get("result_ids"), f"{path}.result_ids", entity_ids)
            if decision.get("actor_type") not in ACTORS:
                errors.append(f"{path}.actor_type: invalid actor type")
            if not isinstance(decision.get("input_version"), int) or not isinstance(decision.get("output_version"), int):
                errors.append(f"{path}: input/output versions must be integers")
            elif decision["output_version"] < decision["input_version"]:
                errors.append(f"{path}: output_version cannot precede input_version")
            # Mechanical lineage rules only; no semantic decision is inferred.
            if action == "RENAME" and decision.get("target_ids") != decision.get("result_ids"):
                errors.append(f"{path}: RENAME must preserve concept identity")
            if action == "SPLIT" and len(decision.get("result_ids", [])) < 2:
                errors.append(f"{path}: SPLIT requires at least two result IDs")
            if action == "MERGE" and len(decision.get("target_ids", [])) < 2:
                errors.append(f"{path}: MERGE requires at least two target IDs")
            if decision.get("source_revision") and decision["source_revision"] not in decision_ids:
                errors.append(f"{path}.source_revision: dangling decision reference")

    # Existing Canonical Evidence and Golden Slice are external, immutable inputs.
    if evidence_bundle is not None:
        if document["canonical_evidence"].get("artifact_id") != evidence_bundle.get("artifact_id"):
            errors.append("$.canonical_evidence.artifact_id: does not match loaded Canonical Evidence")
    if source_slice is not None:
        if document["source_evidence"].get("artifact_id") != source_slice.get("artifact_id"):
            errors.append("$.source_evidence.artifact_id: does not match loaded Golden Slice")
        for name in ("topics", "concepts"):
            for item in source_slice.get(name, []):
                if item.get("id") not in ({x.get("id") for x in records[name]}):
                    errors.append(f"$: source {name} identity missing from canonical knowledge: {item.get('id')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    parser.add_argument("--canonical-evidence", type=Path)
    parser.add_argument("--source-slice", type=Path)
    args = parser.parse_args()
    document = json.loads(args.document.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[1]
    evidence_path = args.canonical_evidence or (root / "analysis/word_timeline_mvp/canonical_evidence_bundle.json")
    source_path = args.source_slice or (root / "analysis/golden_knowledge_slice/golden_knowledge_slice.json")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.is_file() else None
    source = json.loads(source_path.read_text(encoding="utf-8")) if source_path.is_file() else None
    errors = validate_knowledge(document, evidence, source)
    if errors:
        print(f"{args.document}: INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"{args.document}: VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
