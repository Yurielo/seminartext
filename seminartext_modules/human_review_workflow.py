#!/usr/bin/env python3
"""Deterministic, fail-closed human review workflow for Topic Drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from schemas.validate_canonical_evidence_v1 import validate_bundle  # noqa: E402
from seminartext_modules.project_knowledge_bridge import compile_documents  # noqa: E402


VERSION = "1.0.0"
DRAFT_TYPE = "seminartext.topic_drafts"
PACKAGE_TYPE = "seminartext.topic_review_package"
DECISIONS_TYPE = "seminartext.topic_review_decisions"
INPUT_TYPE = "seminartext.project_knowledge_input"
SCHEMA = ROOT / "schemas" / "topic_review_workflow_v1.schema.json"
ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{2,127}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
ACTIONS = {"ACCEPT", "RENAME", "SPLIT", "MERGE", "REJECT", "DEFER"}
HUMAN_ACTORS = {"human_domain_reviewer", "product_owner"}
ORIGIN_MAP = {
    "machine_assisted": "semi_automatic",
    "semi_automatic": "semi_automatic",
    "verified_manual": "verified_manual",
    "gold": "gold",
}
RELATION_REGISTRY = [
    {"id": "supports", "description": "The source concept provides support for the target claim."},
    {"id": "contradicts", "description": "The source and target claims are explicitly competing or conflicting."},
    {"id": "refines", "description": "The source concept narrows or elaborates the target concept."},
    {"id": "depends_on", "description": "The target concept is a stated prerequisite of the source concept."},
    {"id": "associated_with", "description": "The source and target concepts are associated without an inferred ontology."},
]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} cannot be read: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def require_id(value: Any, path: str) -> str:
    if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
        raise ValueError(f"{path}: invalid stable ID")
    return value


def require_hash(value: Any, path: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise ValueError(f"{path}: expected SHA-256")
    return value


def require_exact(value: Any, required: set[str], optional: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    missing = sorted(required - value.keys())
    unexpected = sorted(value.keys() - required - optional)
    if missing or unexpected:
        raise ValueError(f"{path}: missing={missing} unexpected={unexpected}")
    return value


def validate_schema(document: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError as exc:
        raise ValueError("jsonschema is required; use the supported core/dev_test runtime") from exc
    schema = load_json(SCHEMA, "Topic review workflow schema")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (tuple(str(part) for part in error.path), error.message),
    )
    if errors:
        raise ValueError(
            "Topic review workflow schema validation failed:\n"
            + "\n".join(f"{error.json_path}: {error.message}" for error in errors)
        )


def stable_id(value: str, prefix: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "item"
    return f"{prefix}_{slug}"[:120]


def index(records: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for number, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"{label}[{number}]: expected object")
        item_id = require_id(record.get("id"), f"{label}[{number}].id")
        if item_id in result:
            raise ValueError(f"{label}: duplicate stable ID {item_id}")
        result[item_id] = record
    return result


def load_evidence(project: Path) -> tuple[dict[str, Any], str]:
    path = project / "evidence" / "canonical_bundle.json"
    bundle = load_json(path, "project Canonical Evidence")
    errors = validate_bundle(bundle)
    if errors:
        raise ValueError("project Canonical Evidence is invalid:\n" + "\n".join(errors))
    return bundle, sha256_file(path)


def resolve_word_range(
    item: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    revisions: dict[str, dict[str, Any]],
    words: dict[str, dict[str, Any]],
    path: str,
) -> dict[str, Any]:
    source = sources.get(item["source_id"])
    revision = revisions.get(item["transcript_revision_id"])
    first = words.get(item["word_start_id"])
    last = words.get(item["word_end_id"])
    if source is None:
        raise ValueError(f"{path}: invalid Source ID {item['source_id']}")
    if revision is None or revision.get("source_id") != source["id"]:
        raise ValueError(f"{path}: invalid TranscriptRevision {item['transcript_revision_id']}")
    if revision.get("authority") != "authoritative" or revision.get("lifecycle_status") != "verified":
        raise ValueError(f"{path}: TranscriptRevision must be authoritative and verified")
    if first is None or last is None:
        raise ValueError(f"{path}: missing canonical Word endpoint")
    if any(
        word.get("source_id") != source["id"]
        or word.get("transcript_revision_id") != revision["id"]
        for word in (first, last)
    ):
        raise ValueError(f"{path}: cross-source or cross-revision Word range")
    if last["sequence"] < first["sequence"]:
        raise ValueError(f"{path}: invalid inverted Word range")
    selected = sorted(
        (
            word
            for word in words.values()
            if word["transcript_revision_id"] == revision["id"]
            and first["sequence"] <= word["sequence"] <= last["sequence"]
        ),
        key=lambda word: word["sequence"],
    )
    if [word["sequence"] for word in selected] != list(range(first["sequence"], last["sequence"] + 1)):
        raise ValueError(f"{path}: non-contiguous Word range")
    aligned = [word for word in selected if word["alignment_status"] != "unaligned"]
    if not aligned or source["kind"] not in {"audio", "video"}:
        raise ValueError(f"{path}: exact time locator unavailable")
    quote = revision["canonical_text"][selected[0]["char_start"] : selected[-1]["char_end"]]
    return {
        "word_start_id": selected[0]["id"],
        "word_end_id": selected[-1]["id"],
        "word_start_sequence": selected[0]["sequence"],
        "word_end_sequence": selected[-1]["sequence"],
        "quote": quote,
        "locator": {
            "type": "time_interval",
            "start_seconds": aligned[0]["start_seconds"],
            "end_seconds": aligned[-1]["end_seconds"],
        },
    }


def validate_drafts(project: Path, drafts: dict[str, Any]) -> tuple[dict[str, Any], str, list[dict[str, Any]], list[dict[str, Any]]]:
    validate_schema(drafts)
    if drafts.get("artifact_type") != DRAFT_TYPE or drafts.get("schema_version") != VERSION:
        raise ValueError("Topic Draft input must use seminartext.topic_drafts v1.0.0")
    require_id(drafts["artifact_id"], "$.artifact_id")
    bundle, bundle_hash = load_evidence(project)
    if drafts["project"]["id"] != bundle["project"]["id"]:
        raise ValueError("Topic Draft project ID does not match Canonical Evidence")
    sources = index(bundle["sources"], "$.canonical.sources")
    revisions = index(bundle["transcript_revisions"], "$.canonical.transcript_revisions")
    words = index(bundle["words"], "$.canonical.words")
    evidence_input = index(drafts["evidence"], "$.evidence")
    resolved_evidence: list[dict[str, Any]] = []
    for number, evidence in enumerate(drafts["evidence"]):
        span = resolve_word_range(evidence, sources, revisions, words, f"$.evidence[{number}]")
        resolved_evidence.append({**evidence, **span})
    resolved_by_id = {item["id"]: item for item in resolved_evidence}

    topic_ids: set[str] = set()
    resolved_topics: list[dict[str, Any]] = []
    for number, topic in enumerate(drafts["topics"]):
        topic_id = require_id(topic["id"], f"$.topics[{number}].id")
        if topic_id in topic_ids:
            raise ValueError(f"$.topics: duplicate stable ID {topic_id}")
        topic_ids.add(topic_id)
        if topic["lifecycle_status"] != "REVIEW_REQUIRED":
            raise ValueError(f"{topic_id}: Topic Draft must start REVIEW_REQUIRED")
        if topic["seminar_id"] != drafts["seminar"]["id"]:
            raise ValueError(f"{topic_id}: Topic Draft belongs to another seminar")
        if topic["semantic_origin"] not in ORIGIN_MAP:
            raise ValueError(f"{topic_id}: unsupported semantic origin")
        span = resolve_word_range(topic, sources, revisions, words, f"$.topics[{number}]")
        evidence_items = []
        for evidence_id in topic["evidence_refs"]:
            evidence = resolved_by_id.get(evidence_id)
            if evidence is None:
                raise ValueError(f"{topic_id}: missing evidence {evidence_id}")
            if evidence["source_id"] != topic["source_id"] or evidence["transcript_revision_id"] != topic["transcript_revision_id"]:
                raise ValueError(f"{topic_id}: evidence belongs to another source or revision")
            if not (
                span["word_start_sequence"] <= evidence["word_start_sequence"]
                and evidence["word_end_sequence"] <= span["word_end_sequence"]
            ):
                raise ValueError(f"{topic_id}: evidence lies outside Topic Draft range")
            evidence_items.append(evidence)
        if not evidence_items:
            raise ValueError(f"{topic_id}: missing evidence")
        evidence_hash = sha256_bytes(canonical_bytes(evidence_items))
        core = {
            **topic,
            **span,
            "evidence_sha256": evidence_hash,
            "generator": drafts["generator"],
            "review_history": [],
        }
        core["topic_sha256"] = sha256_bytes(canonical_bytes(core))
        resolved_topics.append(core)
    return bundle, bundle_hash, resolved_evidence, resolved_topics


def render_review_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# SeminarText Topic Human Review",
        "",
        f"Project: {package['project']['title']} (`{package['project']['id']}`)",
        f"Seminar: {package['seminar']['title']} (`{package['seminar']['id']}`)",
        f"Package: `{package['artifact_id']}`",
        "",
        "Every draft remains REVIEW_REQUIRED until an explicit human ReviewDecision is applied.",
        "Edit the decision template, not Canonical Knowledge JSON.",
        "",
    ]
    for number, topic in enumerate(package["topics"], 1):
        lines.extend(
            [
                f"## {number}. {topic['proposed_title']}",
                "",
                f"- Draft ID: `{topic['id']}`",
                f"- Status: `{topic['lifecycle_status']}`",
                f"- Source: `{topic['source_id']}`",
                f"- TranscriptRevision: `{topic['transcript_revision_id']}`",
                f"- Words: `{topic['word_start_id']}` → `{topic['word_end_id']}`",
                f"- Time: {topic['locator']['start_seconds']} → {topic['locator']['end_seconds']} seconds",
                f"- Semantic origin: `{topic['semantic_origin']}`",
                f"- Generator: `{topic['generator']['id']}` `{topic['generator']['version']}`",
                f"- Evidence hash: `{topic['evidence_sha256']}`",
                f"- Draft hash: `{topic['topic_sha256']}`",
                "",
                topic["proposed_summary"] or "_No proposed summary supplied._",
                "",
                "Evidence:",
            ]
        )
        for evidence_id in topic["evidence_refs"]:
            evidence = next(item for item in package["evidence"] if item["id"] == evidence_id)
            lines.extend(["", f"- `{evidence_id}`: {evidence['claim']}", f"  > {evidence['quote']}"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def prepare(project: Path, drafts_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"review output already exists: {output}")
    drafts = load_json(drafts_path, "Topic Draft input")
    bundle, bundle_hash, evidence, topics = validate_drafts(project, drafts)
    package = {
        "schema_version": VERSION,
        "artifact_type": PACKAGE_TYPE,
        "artifact_id": stable_id(drafts["artifact_id"], "review_package"),
        "project": drafts["project"],
        "seminar": drafts["seminar"],
        "canonical_evidence": {"artifact_id": bundle["artifact_id"], "sha256": bundle_hash},
        "draft_input": {"artifact_id": drafts["artifact_id"], "sha256": sha256_file(drafts_path)},
        "review_policy": {
            "authoring_gate": "DOMAIN_AUTHORING",
            "review_gate": "DOMAIN_REVIEW",
            "machine_assisted_default": "REVIEW_REQUIRED",
            "automatic_acceptance": False,
        },
        "evidence": sorted(evidence, key=lambda item: item["id"]),
        "topics": sorted(topics, key=lambda item: (item["sequence"], item["id"])),
    }
    validate_schema(package)
    package_bytes = canonical_bytes(package)
    template = {
        "schema_version": VERSION,
        "artifact_type": DECISIONS_TYPE,
        "artifact_id": stable_id(package["artifact_id"], "review_decisions"),
        "review_package_id": package["artifact_id"],
        "review_package_sha256": sha256_bytes(package_bytes),
        "reviewer": {"actor_type": "human_domain_reviewer", "actor_id": "reviewer_id_required"},
        "decisions": [],
    }
    validate_schema(template)
    output.mkdir(parents=True)
    (output / "review_package.json").write_bytes(package_bytes)
    (output / "REVIEW.md").write_text(render_review_markdown(package), encoding="utf-8")
    (output / "review_decisions.template.json").write_bytes(canonical_bytes(template))
    return {
        "status": "REVIEW_REQUIRED",
        "package": str(output / "review_package.json"),
        "review_document": str(output / "REVIEW.md"),
        "decision_template": str(output / "review_decisions.template.json"),
        "total": len(package["topics"]),
        "unreviewed": len(package["topics"]),
    }


def load_package(project: Path, package_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package = load_json(package_path, "Topic review package")
    validate_schema(package)
    if package.get("artifact_type") != PACKAGE_TYPE or package.get("schema_version") != VERSION:
        raise ValueError("review package contract mismatch")
    bundle, bundle_hash = load_evidence(project)
    if package["canonical_evidence"]["artifact_id"] != bundle["artifact_id"]:
        raise ValueError("stale review package: Canonical Evidence artifact changed")
    if package["canonical_evidence"]["sha256"] != bundle_hash:
        raise ValueError("stale review package: underlying evidence changed")
    evidence_by_id = {item["id"]: item for item in package["evidence"]}
    for topic in package["topics"]:
        evidence_items = [evidence_by_id[item_id] for item_id in topic["evidence_refs"]]
        if topic["evidence_sha256"] != sha256_bytes(canonical_bytes(evidence_items)):
            raise ValueError(f"stale review package: evidence snapshot changed for {topic['id']}")
        core = dict(topic)
        supplied_hash = core.pop("topic_sha256")
        if supplied_hash != sha256_bytes(canonical_bytes(core)):
            raise ValueError(f"stale review package: Topic Draft changed for {topic['id']}")
    return package, bundle


def validate_result_topic(result: dict[str, Any], package: dict[str, Any], bundle: dict[str, Any], path: str) -> None:
    sources = index(bundle["sources"], "$.canonical.sources")
    revisions = index(bundle["transcript_revisions"], "$.canonical.transcript_revisions")
    words = index(bundle["words"], "$.canonical.words")
    span = resolve_word_range(result, sources, revisions, words, path)
    evidence_by_id = {item["id"]: item for item in package["evidence"]}
    if not result["evidence_refs"] or not set(result["evidence_refs"]).issubset(evidence_by_id):
        raise ValueError(f"{path}: result evidence must come from the reviewed package")
    for evidence_id in result["evidence_refs"]:
        evidence = evidence_by_id[evidence_id]
        if evidence["source_id"] != result["source_id"] or evidence["transcript_revision_id"] != result["transcript_revision_id"]:
            raise ValueError(f"{path}: result evidence belongs to another source or revision")
        if not (
            span["word_start_sequence"] <= evidence["word_start_sequence"]
            and evidence["word_end_sequence"] <= span["word_end_sequence"]
        ):
            raise ValueError(f"{path}: result evidence lies outside the result Topic range")


def validate_decisions(
    package_path: Path,
    package: dict[str, Any],
    bundle: dict[str, Any],
    decisions: dict[str, Any],
    *,
    require_complete: bool,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    validate_schema(decisions)
    if decisions.get("artifact_type") != DECISIONS_TYPE or decisions.get("schema_version") != VERSION:
        raise ValueError("review decisions contract mismatch")
    if decisions["review_package_id"] != package["artifact_id"]:
        raise ValueError("orphan ReviewDecision: package ID mismatch")
    if decisions["review_package_sha256"] != sha256_file(package_path):
        raise ValueError("stale review package: decision package hash mismatch")
    reviewer = decisions["reviewer"]
    if reviewer["actor_type"] not in HUMAN_ACTORS:
        raise ValueError("semantic ReviewDecision requires a human reviewer")
    require_id(reviewer["actor_id"], "$.reviewer.actor_id")
    package_topics = {item["id"]: item for item in package["topics"]}
    result_ids = set(package_topics)
    covered: dict[str, dict[str, Any]] = {}
    decision_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for number, decision in enumerate(decisions["decisions"]):
        path = f"$.decisions[{number}]"
        decision_id = require_id(decision["id"], f"{path}.id")
        if decision_id in decision_ids:
            raise ValueError(f"duplicate ReviewDecision {decision_id}")
        decision_ids.add(decision_id)
        action = decision["action"]
        if action not in ACTIONS:
            raise ValueError(f"{path}: unsupported decision {action}")
        targets = decision["target_ids"]
        if len(set(targets)) != len(targets):
            raise ValueError(f"{path}: duplicate target")
        for target_id in targets:
            if target_id not in package_topics:
                raise ValueError(f"orphan ReviewDecision target {target_id}")
            if target_id in covered:
                raise ValueError(f"duplicate decision for Topic Draft {target_id}")
            covered[target_id] = decision
        snapshots = {item["topic_id"]: item["topic_sha256"] for item in decision["expected_topics"]}
        if len(snapshots) != len(decision["expected_topics"]) or set(snapshots) != set(targets):
            raise ValueError(f"{path}: expected Topic snapshots must match targets")
        for target_id in targets:
            if snapshots[target_id] != package_topics[target_id]["topic_sha256"]:
                raise ValueError(f"{path}: stale Topic Draft {target_id}")
        results = decision["result_topics"]
        new_title = decision.get("new_title")
        new_summary = decision.get("new_summary")
        if action in {"ACCEPT", "REJECT", "DEFER"}:
            if len(targets) != 1 or results or new_title is not None or new_summary is not None:
                raise ValueError(f"{path}: invalid {action} shape")
        elif action == "RENAME":
            if len(targets) != 1 or results or not isinstance(new_title, str) or not new_title.strip():
                raise ValueError(f"{path}: RENAME requires one target and a non-empty new_title")
        elif action == "SPLIT":
            if len(targets) != 1 or len(results) < 2:
                raise ValueError(f"{path}: SPLIT requires one target and at least two explicit result Topics")
        elif action == "MERGE":
            if len(targets) < 2 or len(results) != 1:
                raise ValueError(f"{path}: MERGE requires at least two targets and one explicit result Topic")
        if action in {"SPLIT", "MERGE"}:
            source_keys = {
                (package_topics[target]["source_id"], package_topics[target]["transcript_revision_id"])
                for target in targets
            }
            if len(source_keys) != 1:
                raise ValueError(f"{path}: cross-source SPLIT/MERGE is unsupported")
            for result_number, result in enumerate(results):
                result_id = require_id(result["id"], f"{path}.result_topics[{result_number}].id")
                if result_id in result_ids:
                    raise ValueError(f"{path}: conflicting stable ID {result_id}")
                result_ids.add(result_id)
                validate_result_topic(result, package, bundle, f"{path}.result_topics[{result_number}]")
                if (result["source_id"], result["transcript_revision_id"]) not in source_keys:
                    raise ValueError(f"{path}: result Topic changes source or revision")
        normalized.append(decision)
    if require_complete and set(covered) != set(package_topics):
        raise ValueError(f"unreviewed Topic Drafts remain: {sorted(set(package_topics) - set(covered))}")
    return covered, normalized


def decision_status(package: dict[str, Any], covered: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {
        "TOTAL": len(package["topics"]),
        "UNREVIEWED": len(package["topics"]) - len(covered),
        "ACCEPTED": 0,
        "RENAMED": 0,
        "SPLIT": 0,
        "MERGED": 0,
        "REJECTED": 0,
        "DEFERRED": 0,
    }
    labels = {
        "ACCEPT": "ACCEPTED",
        "RENAME": "RENAMED",
        "SPLIT": "SPLIT",
        "MERGE": "MERGED",
        "REJECT": "REJECTED",
        "DEFER": "DEFERRED",
    }
    for decision in {item["id"]: item for item in covered.values()}.values():
        counts[labels[decision["action"]]] += len(decision["target_ids"])
    return counts


def status(project: Path, package_path: Path, decisions_path: Path | None) -> dict[str, Any]:
    package, bundle = load_package(project, package_path)
    covered: dict[str, dict[str, Any]] = {}
    if decisions_path is not None:
        decisions = load_json(decisions_path, "Topic review decisions")
        covered, _ = validate_decisions(package_path, package, bundle, decisions, require_complete=False)
    return {"status": "PASS", **decision_status(package, covered)}


def topic_from_review(topic: dict[str, Any], decision: dict[str, Any], decision_artifact_id: str) -> dict[str, Any]:
    action = decision["action"]
    title = decision["new_title"] if action == "RENAME" else topic["proposed_title"]
    summary = decision.get("new_summary") or topic["proposed_summary"] or "No summary supplied."
    lifecycle = {
        "ACCEPT": "ACCEPTED",
        "RENAME": "PROVISIONAL",
        "SPLIT": "SUPERSEDED",
        "MERGE": "SUPERSEDED",
        "REJECT": "REJECTED",
        "DEFER": "PROVISIONAL",
    }[action]
    return {
        "id": topic["id"],
        "seminar_id": topic["seminar_id"],
        "source_scope": {
            "source_ids": [topic["source_id"]],
            "transcript_revision_ids": [topic["transcript_revision_id"]],
            "order_start": topic["word_start_sequence"],
            "order_end": topic["word_end_sequence"],
        },
        "title": title,
        "summary": summary,
        "temporal_scope": {
            "start_seconds": topic["locator"]["start_seconds"],
            "end_seconds": topic["locator"]["end_seconds"],
        },
        "order_scope": {"sequence": topic["sequence"]},
        "evidence_refs": topic["evidence_refs"],
        "concept_refs": [],
        "status": lifecycle,
        "provenance": {
            "origin": "human_review",
            "source_artifact_id": decision_artifact_id,
            "source_status": "product_review_required",
        },
        "version": 2 if action in {"RENAME", "SPLIT", "MERGE"} else 1,
    }


def result_topic(result: dict[str, Any], seminar_id: str, decision_artifact_id: str, bundle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    sources = index(bundle["sources"], "$.canonical.sources")
    revisions = index(bundle["transcript_revisions"], "$.canonical.transcript_revisions")
    words = index(bundle["words"], "$.canonical.words")
    span = resolve_word_range(result, sources, revisions, words, "$.result_topic")
    topic = {
        "id": result["id"],
        "seminar_id": seminar_id,
        "source_scope": {
            "source_ids": [result["source_id"]],
            "transcript_revision_ids": [result["transcript_revision_id"]],
            "order_start": span["word_start_sequence"],
            "order_end": span["word_end_sequence"],
        },
        "title": result["proposed_title"],
        "summary": result["proposed_summary"] or "No summary supplied.",
        "temporal_scope": {
            "start_seconds": span["locator"]["start_seconds"],
            "end_seconds": span["locator"]["end_seconds"],
        },
        "order_scope": {"sequence": result["sequence"]},
        "evidence_refs": result["evidence_refs"],
        "concept_refs": [],
        "status": "PROVISIONAL",
        "provenance": {
            "origin": "human_review",
            "source_artifact_id": decision_artifact_id,
            "source_status": "product_review_required",
        },
        "version": 1,
    }
    source = {
        "topic_id": result["id"],
        "topic_set_id": result["topic_set_id"],
        "sequence": result["sequence"],
        "origin": ORIGIN_MAP[result["semantic_origin"]],
        "transcript_revision_id": result["transcript_revision_id"],
        "word_start_id": result["word_start_id"],
        "word_end_id": result["word_end_id"],
    }
    return topic, source


def apply(project: Path, package_path: Path, decisions_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"reviewed semantic output already exists: {output}")
    package, bundle = load_package(project, package_path)
    decisions = load_json(decisions_path, "Topic review decisions")
    covered, normalized = validate_decisions(package_path, package, bundle, decisions, require_complete=True)
    package_topics = {item["id"]: item for item in package["topics"]}
    knowledge_topics: list[dict[str, Any]] = []
    topic_sources: list[dict[str, Any]] = []
    review_decisions: list[dict[str, Any]] = []
    for topic in package["topics"]:
        decision = covered[topic["id"]]
        knowledge_topics.append(topic_from_review(topic, decision, decisions["artifact_id"]))
        topic_sources.append(
            {
                "topic_id": topic["id"],
                "topic_set_id": topic["topic_set_id"],
                "sequence": topic["sequence"],
                "origin": ORIGIN_MAP[topic["semantic_origin"]],
                "transcript_revision_id": topic["transcript_revision_id"],
                "word_start_id": topic["word_start_id"],
                "word_end_id": topic["word_end_id"],
            }
        )
    for decision in normalized:
        result_ids = []
        for result in decision["result_topics"]:
            new_topic, new_source = result_topic(result, package["seminar"]["id"], decisions["artifact_id"], bundle)
            knowledge_topics.append(new_topic)
            topic_sources.append(new_source)
            result_ids.append(result["id"])
        if decision["action"] in {"ACCEPT", "RENAME"}:
            result_ids = decision["target_ids"]
        review_decisions.append(
            {
                "id": decision["id"],
                "action": decision["action"],
                "target_ids": decision["target_ids"],
                "result_ids": result_ids,
                "reason": decision["reason"],
                "actor_type": decisions["reviewer"]["actor_type"],
                "actor_id": decisions["reviewer"]["actor_id"],
                "timestamp": decision["timestamp"],
                "input_version": 1,
                "output_version": 2 if decision["action"] in {"RENAME", "SPLIT", "MERGE"} else 1,
                "provenance": {"origin": "human_review", "source_artifact_id": decisions["artifact_id"]},
            }
        )
    knowledge_topics.sort(key=lambda item: (item["order_scope"]["sequence"], item["id"]))
    topic_sources.sort(key=lambda item: (item["sequence"], item["topic_id"]))
    artifact_id = stable_id(decisions["artifact_id"], "reviewed_topics")
    source_ids_with_topics = {item["source_scope"]["source_ids"][0] for item in knowledge_topics}
    result = {
        "schema_version": VERSION,
        "artifact_type": INPUT_TYPE,
        "artifact_id": artifact_id,
        "project": {
            "id": package["project"]["id"],
            "title": package["project"]["title"],
            "status": "PROVISIONAL",
            "version": 1,
            "provenance": {"origin": "human_review", "source_artifact_id": artifact_id},
        },
        "seminars": [
            {
                "id": package["seminar"]["id"],
                "project_id": package["project"]["id"],
                "title": package["seminar"]["title"],
                "status": "PROVISIONAL",
                "version": 1,
                "provenance": {"origin": "human_review", "source_artifact_id": artifact_id},
                "topic_refs": [item["id"] for item in knowledge_topics],
            }
        ],
        "topics": knowledge_topics,
        "concepts": [],
        "relations": [],
        "review_decisions": sorted(review_decisions, key=lambda item: item["id"]),
        "relation_type_registry": RELATION_REGISTRY,
        "topic_sources": topic_sources,
        "evidence": [
            {
                key: evidence[key]
                for key in ("id", "claim", "source_id", "transcript_revision_id", "word_start_id", "word_end_id")
            }
            for evidence in package["evidence"]
        ],
        "coverage": [
            {
                "source_id": source["id"],
                "status": "COVERED" if source["id"] in source_ids_with_topics else "SEMANTIC_INPUT_UNAVAILABLE",
                "reason": (
                    "Explicit reviewed Topic state is supplied."
                    if source["id"] in source_ids_with_topics
                    else "No reviewed Topic Draft was supplied for this source."
                ),
            }
            for source in bundle["sources"]
        ],
    }
    compile_documents(project, result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(result))
    return {
        "status": "PASS",
        **decision_status(package, covered),
        "output": str(output),
        "output_sha256": sha256_file(output),
        "canonical_knowledge_compatible": True,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("project")
    prepare_parser.add_argument("--drafts", required=True)
    prepare_parser.add_argument("--output", required=True)
    status_parser = commands.add_parser("status")
    status_parser.add_argument("project")
    status_parser.add_argument("--package", required=True)
    status_parser.add_argument("--decisions")
    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("project")
    apply_parser.add_argument("--package", required=True)
    apply_parser.add_argument("--decisions", required=True)
    apply_parser.add_argument("--output", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        project = Path(args.project).expanduser().resolve()
        if not project.is_dir():
            raise ValueError(f"project does not exist: {project}")
        if args.command == "prepare":
            report = prepare(project, Path(args.drafts).expanduser().resolve(), Path(args.output).expanduser().resolve())
        elif args.command == "status":
            decisions = Path(args.decisions).expanduser().resolve() if args.decisions else None
            report = status(project, Path(args.package).expanduser().resolve(), decisions)
        else:
            report = apply(
                project,
                Path(args.package).expanduser().resolve(),
                Path(args.decisions).expanduser().resolve(),
                Path(args.output).expanduser().resolve(),
            )
    except ValueError as exc:
        print(f"HUMAN REVIEW WORKFLOW: FAIL\n{exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
