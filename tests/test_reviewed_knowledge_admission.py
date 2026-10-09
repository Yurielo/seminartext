"""Exact partial Word/cue admission, semantic firewall and legacy compatibility."""
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from seminartext_modules import reviewed_knowledge_admission as admission
from schemas.validate_canonical_knowledge_v1 import validate_knowledge

ROOT = Path(__file__).resolve().parents[1]


def inputs(cue=False):
    bundle = json.loads((ROOT / "tests/fixtures/canonical_evidence_v1/valid_bundle.json").read_bytes())
    first, last = bundle["words"][1:3]  # Partial BenchmarkSegment, deliberately.
    revision = bundle["transcript_revisions"][0]
    source = bundle["sources"][0]
    fragment = {"id": "fragment_exact", "source_id": source["id"], "transcript_revision_id": revision["id"],
        "word_start_id": first["id"], "word_end_id": last["id"],
        "quote": revision["canonical_text"][first["char_start"]:last["char_end"]],
        "locator": {"type": "time_interval", "start_seconds": first["start_seconds"], "end_seconds": last["end_seconds"]},
        "review_decision_provenance": {"actor_type": "human_domain_reviewer", "actor_id": "fixture_reviewer"}}
    if cue:
        fragment.pop("word_start_id")
        fragment.pop("word_end_id")
        fragment.update(cue_start_id=bundle["cues"][0]["id"], cue_end_id=bundle["cues"][0]["id"],
                        quote=bundle["cues"][0]["text"], locator=bundle["cues"][0]["source_locator"])
    bundle_payload = admission.canonical_bytes(bundle)
    reviewed = {"schema_version": "2.0.0", "artifact_type": "seminartext.human_review_result",
        "artifact_id": "review_result_exact", "application_status": "APPLIED",
        "review_package": {"artifact_id": "review_package_exact", "sha256": "a"*64},
        "decision_artifact": {"artifact_id": "review_decisions_exact", "sha256": "b"*64},
        "canonical_evidence": {"artifact_id": bundle["artifact_id"], "sha256": hashlib.sha256(bundle_payload).hexdigest()},
        "word_timeline": {"path": "evidence/word_timeline.json", "sha256": "c"*64},
        "source_topic_snapshots": [], "fragment_lineage": [fragment],
        "semantic_knowledge": [{"fragment_refs": [fragment["id"]], "provenance": {"boundary_authority": "PRODUCT_OWNER_DOMAIN_REVIEW"}}],
        "seminar_structure": [], "non_semantic_excluded": []}
    reviewed_payload = admission.canonical_bytes(reviewed)
    ev = admission._span(fragment, bundle)
    record = {"id": "concept_exact", "preferred_label": "Стресс", "aliases": [], "status": "PROVISIONAL",
        "scope": "source-bound", "description": "Source-bound proposed Concept", "version": 1,
        "evidence_refs": [ev["id"]], "topic_refs": [], "created_from": [ev["id"]], "supersedes": [], "redirects": [],
        "provenance": {"origin": "derived", "source_artifact_id": "proposals_exact"}}
    proposal = {"id": "proposal_exact", "entity_kind": "concepts", "operation": "CREATE", "record": record,
        "fragment_refs": [{"id": fragment["id"], "sha256": admission.digest(fragment)}], "before_sha256": None,
        "review_status": "REVIEW_REQUIRED", "generation_provenance": {"method": "fixture-proposal", "producer_sha256": "d"*64}}
    package = {"schema_version": "1.0.0", "artifact_type": "seminartext.reviewed_knowledge_proposals", "artifact_id": "proposals_exact",
        "contract": {"id": admission.CONTRACT_ID, "sha256": admission.CONTRACT_SHA256},
        "producer": {"component_id": "integra", "runtime_id": "integra_k2_v1", "runtime_sha256": "d"*64},
        "source_binding": {"project_id": bundle["project"]["id"], "source_id": source["id"],
            "source_revision_sha256": source["content_sha256"], "source_sha256": source["content_sha256"],
            "transcript_revision_id": revision["id"], "transcript_sha256": revision["text_sha256"],
            "evidence_sha256": hashlib.sha256(bundle_payload).hexdigest()},
        "k1_binding": {"artifact_id": reviewed["artifact_id"], "sha256": hashlib.sha256(reviewed_payload).hexdigest(),
            "notebook_id": "notebook_exact", "notebook_sha256": "e"*64, "review_state": "REVIEWED_FRAGMENTS_V2"},
        "parent_revision_sha256": None, "proposals": [proposal]}
    decisions = decide(package)
    return bundle_payload, reviewed_payload, package, decisions


def decide(package, action="ACCEPT", edits=None):
    return {"schema_version": "1.0.0", "package_id": package["artifact_id"], "package_sha256": admission.digest(package),
        "reviewer": {"actor_type": "human_domain_reviewer", "actor_id": "fixture_reviewer"}, "explicit_confirmation": True,
        "confirmed_proposal_ids": sorted(item["id"] for item in package["proposals"]),
        "decisions": [{"proposal_id": item["id"], "proposal_sha256": admission.digest(item), "action": action,
            "reason": "Explicit synthetic test decision", "timestamp": "2026-10-09T09:00:00Z",
            **({"edited_fields": edits} if edits else {})} for item in package["proposals"]]}


@pytest.mark.parametrize("cue", [False, True])
def test_exact_range_compiles_without_benchmark_substitution(cue):
    bundle, reviewed, package, decisions = inputs(cue)
    result = admission.compile_revision(bundle, reviewed, package, decisions)
    admission.validate_revision(result, bundle)
    evidence = result["source_evidence"]["evidence"][0]
    assert evidence["quote"] == json.loads(reviewed)["fragment_lineage"][0]["quote"]
    assert evidence["precision"] == ("CUE_RANGE" if cue else "WORD_RANGE")
    assert result["canonical_knowledge"]["concepts"][0]["status"] == "ACCEPTED"
    assert validate_knowledge(result["canonical_knowledge"], json.loads(bundle), result["source_evidence"]) == []
    assert admission.compile_revision(bundle, reviewed, package, decisions) == result


@pytest.mark.parametrize("action", ["REJECT", "DEFER"])
def test_rejected_and_deferred_do_not_enter_canonical_revision(action):
    bundle, reviewed, package, _ = inputs()
    result = admission.compile_revision(bundle, reviewed, package, decide(package, action))
    assert result["canonical_knowledge"]["concepts"] == []
    assert result["semantic_decisions"][0]["action"] == action


def test_edit_preserves_identity_and_parent_revision():
    bundle, reviewed, package, choices = inputs()
    parent = admission.compile_revision(bundle, reviewed, package, choices)
    saved_parent = copy.deepcopy(parent)
    package["parent_revision_sha256"] = parent["revision_sha256"]
    proposal = package["proposals"][0]
    proposal["operation"] = "UPDATE"
    proposal["before_sha256"] = admission.digest(parent["canonical_knowledge"]["concepts"][0])
    result = admission.compile_revision(bundle, reviewed, package, decide(package, "EDIT", {"preferred_label": "Стрессовая реакция"}), parent=parent)
    assert parent == saved_parent
    assert result["canonical_knowledge"]["concepts"][0]["id"] == "concept_exact"
    assert result["canonical_knowledge"]["concepts"][0]["version"] == 2
    assert result["parent_revision_sha256"] == parent["revision_sha256"]
    admission.validate_revision(result, bundle)


@pytest.mark.parametrize("case", ["source", "fragment", "evidence", "decision", "contract", "producer", "package", "merge", "unreviewed", "hidden", "timestamp"])
def test_negative_cases_fail_closed(case):
    bundle, reviewed, package, choices = inputs()
    if case == "source": package["source_binding"]["source_sha256"] = "f"*64
    elif case == "fragment": package["proposals"][0]["fragment_refs"][0]["sha256"] = "f"*64
    elif case == "evidence": package["proposals"][0]["record"]["evidence_refs"] = []
    elif case == "decision": choices["decisions"][0]["proposal_sha256"] = "f"*64
    elif case == "contract": package["contract"]["sha256"] = "f"*64
    elif case == "producer": package["producer"]["component_id"] = "machine_writer"
    elif case == "package": choices["package_sha256"] = "f"*64
    elif case == "merge": package["proposals"][0]["record"]["redirects"] = ["concept_other"]
    elif case == "unreviewed": choices["decisions"] = []
    elif case == "hidden": choices["confirmed_proposal_ids"] = []
    elif case == "timestamp": choices["decisions"][0]["timestamp"] = "not-a-date"
    if case in {"source", "fragment", "evidence", "contract", "producer", "merge"}:
        choices = decide(package)
    with pytest.raises(ValueError):
        admission.compile_revision(bundle, reviewed, package, choices)


def test_changed_exact_boundary_with_new_hash_still_rejects_old_quote():
    bundle, reviewed, package, _ = inputs()
    document = json.loads(reviewed)
    fragment = document["fragment_lineage"][0]
    fragment["word_end_id"] = json.loads(bundle)["words"][3]["id"]
    reviewed = admission.canonical_bytes(document)
    package["k1_binding"]["sha256"] = hashlib.sha256(reviewed).hexdigest()
    package["proposals"][0]["fragment_refs"][0]["sha256"] = admission.digest(fragment)
    with pytest.raises(ValueError, match="boundaries"):
        admission.compile_revision(bundle, reviewed, package, decide(package))


def test_immutable_write_failure_preserves_previous_revision(tmp_path):
    result = admission.compile_revision(*inputs())
    path = tmp_path / "revision.json"
    admission.persist_revision(path, result)
    original = path.read_bytes()
    with pytest.raises(ValueError):
        admission.persist_revision(path, {"different": True})
    assert path.read_bytes() == original
    with patch.object(admission.os, "link", side_effect=OSError("interrupted write")):
        with pytest.raises(OSError):
            admission.persist_revision(tmp_path / "new.json", result)
    assert path.read_bytes() == original
    assert not (tmp_path / "new.json").exists()


@pytest.mark.parametrize("case", ["text", "time", "zero_duration"])
def test_cue_order_and_positive_duration_fail_closed(case):
    payload, reviewed, _, _ = inputs(cue=True)
    bundle = json.loads(payload)
    fragment = json.loads(reviewed)["fragment_lineage"][0]
    first = bundle["cues"][0]
    second = copy.deepcopy(first)
    second.update(id="cue_reversed", sequence=first["sequence"] + 1)
    bundle["cues"].append(second)
    fragment["cue_end_id"] = second["id"]
    if case == "text":
        second["char_start"], second["char_end"] = 0, 1
    elif case == "time":
        second["char_start"], second["char_end"] = first["char_end"], first["char_end"] + 1
        second["source_locator"] = {"type": "time_interval", "start_seconds": 0, "end_seconds": 1}
    else:
        first["source_locator"]["end_seconds"] = first["source_locator"]["start_seconds"]
    with pytest.raises(ValueError, match="cue text/time"):
        admission._span(fragment, bundle)
