#!/usr/bin/env python3
"""SeminarText-owned, additive exact-fragment semantic admission v1.

This produces the existing Canonical Knowledge v1 model, with a separate
content-addressed revision receipt. It never changes Canonical Evidence or
substitutes BenchmarkSegments for reviewed fragments.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator, FormatChecker
from schemas.validate_canonical_evidence_v1 import validate_bundle
from schemas.validate_canonical_knowledge_v1 import validate_knowledge, RELATIONS
from seminartext_modules.project_knowledge_bridge import canonical_bytes, require_id, _word_span
from seminartext_modules.human_review_workflow import validate_schema_v2

CONTRACT_ID = "seminartext.reviewed_knowledge_admission_v1"
SCHEMA_PATH = ROOT / "schemas/reviewed_knowledge_admission_v1.schema.json"
CONTRACT_SHA256 = hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _index(values, label):
    result = {}
    for item in values:
        require_id(item.get("id"), label)
        _require(item["id"] not in result, f"duplicate {label}")
        result[item["id"]] = item
    return result


def _span(fragment, bundle):
    """Validate exact available precision, without deriving missing Words."""
    sources = _index(bundle["sources"], "source")
    revisions = _index(bundle["transcript_revisions"], "revision")
    source = sources.get(fragment.get("source_id"))
    revision = revisions.get(fragment.get("transcript_revision_id"))
    _require(source and revision and revision["source_id"] == source["id"], "fragment source/revision mismatch")
    precision = "WORD_RANGE" if fragment.get("word_start_id") is not None else "CUE_RANGE"
    if precision == "WORD_RANGE":
        words = _index(bundle["words"], "word")
        selected, locator, timing, unaligned = _word_span({
            "id": fragment["id"], "claim": "Exact reviewed source fragment",
            "source_id": source["id"], "transcript_revision_id": revision["id"],
            "word_start_id": fragment["word_start_id"], "word_end_id": fragment["word_end_id"],
        }, words, revisions, sources)
        quote = revision["canonical_text"][selected[0]["char_start"]:selected[-1]["char_end"]]
        if "word_start_sequence" in fragment:
            _require(fragment["word_start_sequence"] == selected[0]["sequence"] and
                     fragment["word_end_sequence"] == selected[-1]["sequence"], "fragment sequence changed")
        anchors = {"canonical_word_start_id": selected[0]["id"], "canonical_word_end_id": selected[-1]["id"]}
    else:
        cues = _index(bundle["cues"], "cue")
        first, last = cues.get(fragment.get("cue_start_id")), cues.get(fragment.get("cue_end_id"))
        _require(first and last and first["transcript_revision_id"] == last["transcript_revision_id"] == revision["id"],
                 "fragment cue/revision mismatch")
        selected = sorted((cue for cue in cues.values() if cue["transcript_revision_id"] == revision["id"]
                           and first["sequence"] <= cue["sequence"] <= last["sequence"]), key=lambda cue: cue["sequence"])
        _require(selected and [cue["sequence"] for cue in selected] == list(range(first["sequence"], last["sequence"]+1)),
                 "non-contiguous cue range")
        _require(all(cue["char_start"] < cue["char_end"] and
                     cue["source_locator"]["type"] == "time_interval" and
                     cue["source_locator"]["start_seconds"] < cue["source_locator"]["end_seconds"]
                     for cue in selected), "invalid cue text/time range")
        _require(all(left["char_end"] <= right["char_start"] and
                     left["source_locator"]["start_seconds"] <= right["source_locator"]["start_seconds"] and
                     left["source_locator"]["end_seconds"] <= right["source_locator"]["end_seconds"]
                     for left, right in zip(selected, selected[1:])), "reversed cue text/time order")
        quote = revision["canonical_text"][first["char_start"]:last["char_end"]]
        start, end = first["source_locator"], last["source_locator"]
        _require(start["type"] == end["type"] == "time_interval", "unsupported cue locator")
        locator = {"type": "time_interval", "start_seconds": start["start_seconds"], "end_seconds": end["end_seconds"]}
        _require(quote.strip() and locator["start_seconds"] < locator["end_seconds"], "empty cue text/time range")
        timing, unaligned = "cue_range", []
        anchors = {"canonical_cue_start_id": first["id"], "canonical_cue_end_id": last["id"]}
    _require(fragment.get("quote") == quote and fragment.get("locator") == locator, "fragment quote/boundaries/timestamps changed")
    return {"id": "evidence_" + hashlib.sha256(fragment["id"].encode()).hexdigest(),
            "claim": "Exact reviewed source fragment", "canonical_source_id": source["id"],
            "canonical_transcript_revision_id": revision["id"], **anchors,
            "quote": quote, "locator": locator, "precision": precision,
            "timing_status": timing, "unaligned_word_ids": unaligned,
            "reviewed_fragment_id": fragment["id"], "reviewed_fragment_sha256": digest(fragment)}


def compile_revision(bundle_payload, reviewed_payload, package, decisions, *, parent=None):
    """Pure deterministic admission. Caller supplies current independently verified inputs."""
    package, decisions, parent = copy.deepcopy((package, decisions, parent))
    bundle, reviewed = json.loads(bundle_payload), json.loads(reviewed_payload)
    schema = json.loads(SCHEMA_PATH.read_bytes())
    for label, value, definition in (("package", package, "package"), ("decisions", decisions, "decisions")):
        errors = list(Draft202012Validator({**schema, "$ref": "#/$defs/" + definition}, format_checker=FormatChecker()).iter_errors(value))
        _require(not errors, f"{label} schema invalid: " + (errors[0].message if errors else ""))
    _require(not validate_bundle(bundle), "Canonical Evidence invalid")
    _require(package["contract"] == {"id": CONTRACT_ID, "sha256": CONTRACT_SHA256}, "wrong admission contract/version")
    _require(package["producer"]["component_id"] == "integra", "wrong producer")
    binding = package["source_binding"]
    _require(binding["project_id"] == bundle["project"]["id"], "source project mismatch")
    source = next((item for item in bundle["sources"] if item["id"] == binding["source_id"]), None)
    revision = next((item for item in bundle["transcript_revisions"] if item["id"] == binding["transcript_revision_id"]), None)
    _require(source and revision and revision["source_id"] == source["id"], "source/transcript revision unavailable")
    _require(source["content_sha256"] == binding["source_sha256"] == binding["source_revision_sha256"] and
             revision["text_sha256"] == binding["transcript_sha256"] and
             hashlib.sha256(bundle_payload).hexdigest() == binding["evidence_sha256"], "stale source/evidence hash")
    k1 = package["k1_binding"]
    validate_schema_v2(reviewed)
    _require(reviewed.get("artifact_type") == "seminartext.human_review_result" and reviewed.get("schema_version") == "2.0.0"
             and reviewed.get("application_status") == "APPLIED" and k1["review_state"] == "REVIEWED_FRAGMENTS_V2"
             and reviewed["artifact_id"] == k1["artifact_id"] and hashlib.sha256(reviewed_payload).hexdigest() == k1["sha256"],
             "K1 review/result hash mismatch")
    _require(reviewed["canonical_evidence"] == {"artifact_id": bundle["artifact_id"], "sha256": binding["evidence_sha256"]},
             "K1 Evidence binding mismatch")
    fragments = _index(reviewed["fragment_lineage"], "fragment")
    eligible = {ref for unit in reviewed["semantic_knowledge"] for ref in unit["fragment_refs"]}
    _require(all(unit.get("provenance", {}).get("boundary_authority") == "PRODUCT_OWNER_DOMAIN_REVIEW"
                 for unit in reviewed["semantic_knowledge"]), "K1 boundaries lack explicit review")
    proposals = _index(package["proposals"], "proposal")
    _require(decisions["package_id"] == package["artifact_id"] and decisions["package_sha256"] == digest(package), "stale proposal package")
    _require(decisions["confirmed_proposal_ids"] == sorted(proposals) and decisions["explicit_confirmation"] is True,
             "explicit enumerated package confirmation required")
    choices = {item["proposal_id"]: item for item in decisions["decisions"]}
    _require(len(choices) == len(decisions["decisions"]) and set(choices) == set(proposals), "missing/duplicate semantic ReviewDecision")
    for choice in choices.values():
        _require(datetime.fromisoformat(choice["timestamp"].replace("Z", "+00:00")).tzinfo is not None,
                 "semantic ReviewDecision timestamp requires timezone")
    previous = None
    if parent is not None:
        validate_revision(parent, bundle_payload)
        old_package = parent["source_evidence"]["admission"]["package"]
        _require(old_package["source_binding"] == binding and old_package["k1_binding"] == k1,
                 "parent belongs to another source/notebook revision")
        previous = parent["canonical_knowledge"]
    _require(package["parent_revision_sha256"] == (parent["revision_sha256"] if parent else None), "parent revision mismatch")
    records = {name: copy.deepcopy(previous[name]) if previous else [] for name in ("topics", "concepts", "relations")}
    prior_evidence = copy.deepcopy(parent["source_evidence"]["evidence"]) if parent else []
    ev_index = _index(prior_evidence, "Evidence")
    review_records = copy.deepcopy(previous["review_decisions"]) if previous else []
    semantic_decisions = []
    seen_targets = set()
    entity_schema = json.loads((ROOT / "schemas/canonical_knowledge_v1.schema.json").read_bytes())
    for proposal_id in sorted(proposals):
        proposal, choice = proposals[proposal_id], choices[proposal_id]
        _require(choice["proposal_sha256"] == digest(proposal), "semantic ReviewDecision proposal mismatch")
        _require(proposal["review_status"] == "REVIEW_REQUIRED" and proposal["record"]["status"] == "PROVISIONAL", "proposal already accepted")
        kind = proposal["entity_kind"]
        record = copy.deepcopy(proposal["record"])
        _require(record["id"] not in seen_targets, "ambiguous repeated entity identity")
        seen_targets.add(record["id"])
        old = next((item for item in records[kind] if item["id"] == record["id"]), None)
        _require(proposal["before_sha256"] == (digest(old) if old else None), "stale current canonical record")
        _require((old is None) == (proposal["operation"] == "CREATE"), "ambiguous Concept identity/operation")
        refs = []
        for ref in proposal["fragment_refs"]:
            _require(ref["id"] in eligible and ref["id"] in fragments, "missing or excluded reviewed fragment Evidence")
            fragment = fragments[ref["id"]]
            _require(digest(fragment) == ref["sha256"], "changed fragment boundaries/hash")
            _require(fragment["source_id"] == binding["source_id"] and fragment["transcript_revision_id"] == revision["id"],
                     "cross-source fragment unsupported")
            _require(fragment.get("review_decision_provenance", {}).get("actor_type") in {"human_domain_reviewer", "product_owner"},
                     "fragment lacks human K1 review provenance")
            evidence = _span(fragment, bundle)
            refs.append(evidence["id"])
            ev_index[evidence["id"]] = evidence
        _require(refs and record["evidence_refs"] == sorted(set(refs)), "proposal Evidence binding differs")
        _require(proposal["generation_provenance"]["producer_sha256"] == package["producer"]["runtime_sha256"],
                 "proposal producer identity differs")
        if kind == "topics":
            _require(record["source_scope"]["source_ids"] == [source["id"]] and
                     record["source_scope"]["transcript_revision_ids"] == [revision["id"]], "Topic source scope differs")
        if kind == "concepts":
            _require(not record["supersedes"] and not record["redirects"], "automatic Concept merge unsupported")
        if kind == "relations":
            _require(record["relation_type"] in RELATIONS, "unsupported Relation")
        editable = {"topics": {"title", "summary"}, "concepts": {"preferred_label", "description", "aliases"},
                    "relations": {"relation_type"}}[kind]
        edits = choice.get("edited_fields", {})
        _require(set(edits) <= editable and (not edits or choice["action"] == "EDIT"), "unsupported semantic edit")
        record.update(edits)
        _require(record["id"] == proposal["record"]["id"], "semantic edit changed identity")
        record["status"] = "ACCEPTED" if choice["action"] in {"ACCEPT", "EDIT"} else "PROVISIONAL"
        record["version"] = old["version"] + 1 if old and record["status"] == "ACCEPTED" else record["version"]
        errors = list(Draft202012Validator({"$schema": entity_schema["$schema"], "$defs": entity_schema["$defs"],
                                           "$ref": "#/$defs/" + kind[:-1]}).iter_errors(record))
        _require(not errors, "canonical entity schema invalid: " + (errors[0].message if errors else ""))
        semantic_decisions.append(copy.deepcopy(choice))
        if record["status"] != "ACCEPTED":
            continue  # REJECT/DEFER remain in the immutable receipt, never become canonical entities.
        record["provenance"] = {"origin": "human_review", "source_artifact_id": package["artifact_id"],
                                "notes": f"Semantic review of {proposal_id}; K1 review is separate."}
        records[kind] = [item for item in records[kind] if item["id"] != record["id"]] + [record]
        review_records.append({"id": "decision_" + digest({"package": digest(package), "choice": choice}),
            "action": "ACCEPT", "target_ids": [record["id"]], "result_ids": [record["id"]],
            "reason": choice["reason"], **decisions["reviewer"], "timestamp": choice["timestamp"],
            "input_version": old["version"] if old else 1, "output_version": record["version"],
            "provenance": {"origin": "human_review", "source_artifact_id": package["artifact_id"]}})
    used = {ref for name in records for item in records[name] for ref in item["evidence_refs"]}
    ev = [ev_index[key] for key in sorted(used)]
    request = {"package": package, "decisions": decisions, "reviewed_result": reviewed,
               "reviewed_payload_utf8": reviewed_payload.decode("utf-8"), "parent": parent}
    source_evidence = {"artifact_type": "seminartext.reviewed_fragment_knowledge_evidence", "schema_version": "1.0.0",
        "artifact_id": "admission_evidence_" + digest(request), "evidence": ev,
        "topics": [{"id": item["id"]} for item in records["topics"]],
        "concepts": [{"id": item["id"]} for item in records["concepts"]],
        "canonical_evidence": {"artifact_id": bundle["artifact_id"], "sha256": binding["evidence_sha256"]}, "admission": request}
    provenance = {"origin": "derived", "source_artifact_id": package["artifact_id"]}
    seminar_id = previous["seminars"][0]["id"] if previous else "seminar_" + hashlib.sha256(binding["project_id"].encode()).hexdigest()
    knowledge = {"schema_version": "1.0.0", "artifact_type": "seminartext.canonical_knowledge", "version": 1,
        "artifact_id": previous["artifact_id"] if previous else "knowledge_" + hashlib.sha256(k1["notebook_id"].encode()).hexdigest(),
        "canonical_evidence": {"artifact_id": bundle["artifact_id"], "schema_version": bundle["schema_version"],
            "sha256": binding["evidence_sha256"], "path": "knowledge/canonical_evidence.json"},
        "source_evidence": {"artifact_id": source_evidence["artifact_id"], "schema_version": "1.0.0",
            "sha256": digest(source_evidence), "path": "knowledge/source_evidence.json"},
        "project": copy.deepcopy(previous["project"]) if previous else {"id": binding["project_id"], "title": bundle["project"]["title"],
            "status": "PROVISIONAL", "version": 1, "provenance": provenance},
        "seminars": [{"id": seminar_id, "project_id": binding["project_id"], "title": bundle["project"]["title"],
            "status": "PROVISIONAL", "version": 1, "provenance": provenance, "topic_refs": sorted(item["id"] for item in records["topics"])}],
        **{name: sorted(values, key=lambda item: item["id"]) for name, values in records.items()},
        "review_decisions": sorted(review_records, key=lambda item: item["id"]),
        "relation_type_registry": [{"id": name, "description": name} for name in sorted(RELATIONS)]}
    errors = validate_knowledge(knowledge, bundle, source_evidence)
    _require(not errors, "canonical validation failed: " + "; ".join(errors))
    result = {"schema_version": "1.0.0", "artifact_type": "seminartext.canonical_knowledge_revision",
        "owner": "seminartext", "parent_revision_sha256": package["parent_revision_sha256"],
        "canonical_knowledge": knowledge, "canonical_knowledge_sha256": digest(knowledge),
        "source_evidence": source_evidence, "source_evidence_sha256": digest(source_evidence),
        "proposal_package_sha256": digest(package), "semantic_decisions": semantic_decisions}
    result["revision_sha256"] = digest(result)
    return result


def validate_revision(revision, bundle_payload):
    _require(revision.get("owner") == "seminartext" and revision.get("artifact_type") == "seminartext.canonical_knowledge_revision",
             "wrong canonical revision owner/type")
    _require(revision.get("revision_sha256") == digest({key: value for key, value in revision.items() if key != "revision_sha256"}),
             "canonical revision hash changed")
    request = revision["source_evidence"]["admission"]
    payload = request["reviewed_payload_utf8"].encode("utf-8")
    _require(json.loads(payload) == request["reviewed_result"], "reviewed result receipt changed")
    expected = compile_revision(bundle_payload, payload, request["package"], request["decisions"], parent=request["parent"])
    _require(revision == expected, "canonical admission output differs from bound inputs")


def persist_revision(destination, revision):
    """Atomic immutable write; the previous revision is never touched."""
    destination = Path(destination)
    if destination.is_symlink() or destination.parent.is_symlink():
        raise ValueError("unsafe canonical revision destination")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(revision)
    if destination.exists():
        _require(destination.read_bytes() == payload, "canonical revision already exists with different bytes")
        return
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".admission-", delete=True) as staged:
        staged.write(payload)
        staged.flush()
        os.fsync(staged.fileno())
        os.link(staged.name, destination)  # no overwrite, even with a concurrent writer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--reviewed", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = compile_revision(args.evidence.read_bytes(), args.reviewed.read_bytes(), json.loads(args.package.read_bytes()),
        json.loads(args.decisions.read_bytes()), parent=json.loads(args.parent.read_bytes()) if args.parent else None)
    persist_revision(args.output, result)
    print(json.dumps({"status": "PASS", "revision_sha256": result["revision_sha256"], "output": str(args.output)}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
