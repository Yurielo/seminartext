from __future__ import annotations

import hashlib
import json
from pathlib import Path

from test_human_review_workflow import prepare, read_json, run_cli, write_json


ROOT = Path(__file__).resolve().parents[1]


def canonical_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(value) -> str:
    return hashlib.sha256(value).hexdigest()


def make_v2_package(tmp_path: Path) -> tuple[Path, Path, list[dict]]:
    project, package_path, _ = prepare(tmp_path)
    package = read_json(package_path)
    bundle = read_json(project / "evidence" / "canonical_bundle.json")
    words = sorted(
        (item for item in bundle["words"] if item["transcript_revision_id"] == "transcript_revision_video_001_r1"),
        key=lambda item: item["sequence"],
    )
    ranges = [(0, 1), (0, 0), (1, 1), (0, 1)]
    for topic, (start, end) in zip(package["topics"], ranges):
        selected = words[start : end + 1]
        topic.update(
            {
                "word_start_id": selected[0]["id"],
                "word_end_id": selected[-1]["id"],
                "word_start_sequence": selected[0]["sequence"],
                "word_end_sequence": selected[-1]["sequence"],
                "quote": " ".join(item["text"] for item in selected),
                "locator": {
                    "type": "time_interval",
                    "start_seconds": selected[0]["start_seconds"],
                    "end_seconds": selected[-1]["end_seconds"],
                },
            }
        )
        core = dict(topic)
        core.pop("topic_sha256")
        topic["topic_sha256"] = sha256(canonical_bytes(core))
    write_json(package_path, package)
    return project, package_path, words


def fragment(fragment_id: str, topic: dict, start: dict, end: dict) -> dict:
    return {
        "id": fragment_id,
        "source_topic_id": topic["id"],
        "source_id": topic["source_id"],
        "transcript_revision_id": topic["transcript_revision_id"],
        "word_start_id": start["id"],
        "word_end_id": end["id"],
        "evidence_refs": [],
    }


def decision(document: dict, package: dict, targets: list[dict], fragments: list[dict], results: list[dict], operations: list[str]) -> None:
    document["decisions"].append(
        {
            "id": f"decision_v2_{len(document['decisions']) + 1}",
            "operations": operations,
            "target_ids": [item["id"] for item in targets],
            "expected_topics": [
                {"topic_id": item["id"], "topic_sha256": item["topic_sha256"]} for item in targets
            ],
            "source_fragments": fragments,
            "results": results,
            "reason": "Explicit Product Owner fixture decision.",
            "timestamp": "2026-09-02T00:00:00Z",
        }
    )


def result(result_id: str, disposition: str, sequence: int, refs: list[str]) -> dict:
    return {
        "id": result_id,
        "disposition": disposition,
        "title": result_id.replace("_", " "),
        "summary": "V2 lineage fixture.",
        "sequence": sequence,
        "fragment_refs": refs,
        "evidence_refs": [],
    }


def make_v2_decisions(package_path: Path, words: list[dict]) -> dict:
    package = read_json(package_path)
    topics = package["topics"]
    document = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.topic_review_decisions",
        "artifact_id": "review_decisions_v2_fixture",
        "review_package_id": package["artifact_id"],
        "review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "reviewer": {"actor_type": "product_owner", "actor_id": "product_owner_fixture"},
        "boundary_authority": "REVIEW_REQUIRED",
        "decisions": [],
    }
    f0 = fragment("fragment_0", topics[0], words[0], words[0])
    f1 = fragment("fragment_1", topics[0], words[1], words[1])
    decision(
        document,
        package,
        [topics[0]],
        [f0, f1],
        [
            result("result_semantic_0", "SEMANTIC_KNOWLEDGE", 0, [f0["id"]]),
            result("result_structure_0", "SEMINAR_STRUCTURE", 1, [f1["id"]]),
        ],
        ["SPLIT", "REALIGN", "CLASSIFY"],
    )
    f2 = fragment("fragment_2", topics[1], words[0], words[0])
    f3 = fragment("fragment_3", topics[2], words[1], words[1])
    decision(
        document,
        package,
        [topics[1], topics[2]],
        [f2, f3],
        [result("result_cross_draft", "SEMANTIC_KNOWLEDGE", 2, [f2["id"], f3["id"]])],
        ["SPLIT", "MERGE", "REALIGN"],
    )
    f4 = fragment("fragment_4", topics[3], words[0], words[0])
    f5 = fragment("fragment_5", topics[3], words[1], words[1])
    decision(
        document,
        package,
        [topics[3]],
        [f4, f5],
        [
            result("result_excluded", "NON_SEMANTIC_EXCLUDED", 3, [f4["id"]]),
            result("result_semantic_1", "SEMANTIC_KNOWLEDGE", 4, [f5["id"]]),
        ],
        ["TRIM", "EXCLUDE", "CLASSIFY"],
    )
    return document


def test_v2_fragment_composition_dispositions_and_assurance(tmp_path: Path) -> None:
    project, package_path, words = make_v2_package(tmp_path)
    decisions_path = tmp_path / "decisions-v2.json"
    document = make_v2_decisions(package_path, words)
    document["limitations"] = ["Known source limitation remains traceable."]
    write_json(decisions_path, document)

    status = run_cli(
        "project-review-v2-status", str(project), "--package", str(package_path), "--decisions", str(decisions_path)
    )
    assert status.returncode == 0, status.stderr
    report = json.loads(status.stdout)
    assert report["covered_topics"] == 4
    assert report["fragments"] == 6
    assert report["results"] == 5
    assert report["application_authorized"] is False

    blocked = run_cli(
        "project-review-v2-apply",
        str(project),
        "--package",
        str(package_path),
        "--decisions",
        str(decisions_path),
        "--output",
        str(tmp_path / "blocked.json"),
    )
    assert blocked.returncode == 2
    assert "exact boundaries remain REVIEW_REQUIRED" in blocked.stderr

    document["boundary_authority"] = "PRODUCT_OWNER_DOMAIN_REVIEW"
    write_json(decisions_path, document)
    first = tmp_path / "result-first.json"
    second = tmp_path / "result-second.json"
    for output in (first, second):
        applied = run_cli(
            "project-review-v2-apply",
            str(project),
            "--package",
            str(package_path),
            "--decisions",
            str(decisions_path),
            "--output",
            str(output),
        )
        assert applied.returncode == 0, applied.stderr
    assert first.read_bytes() == second.read_bytes()
    output = read_json(first)
    assert len(output["semantic_knowledge"]) == 3
    assert len(output["seminar_structure"]) == 1
    assert len(output["non_semantic_excluded"]) == 1
    assert output["limitations"] == document["limitations"]
    assert len(output["fragment_lineage"]) == 6
    assert output["source_topic_snapshots"] == read_json(package_path)["topics"]
    assert all(item["transcript_provenance"]["verification_state"] == "fully_human_verified" for item in output["fragment_lineage"])
    assert all(item["word_timeline_provenance"]["sha256"] == output["word_timeline"]["sha256"] for item in output["fragment_lineage"])
    assert all(item["provenance"]["canonical_evidence_sha256"] == output["canonical_evidence"]["sha256"] for item in output["semantic_knowledge"])


def test_v2_complete_authority_provenance_is_total_and_fail_closed(tmp_path: Path) -> None:
    project, package_path, words = make_v2_package(tmp_path)
    package = read_json(package_path)
    document = make_v2_decisions(package_path, words)
    document["boundary_authority"] = "PRODUCT_OWNER_DOMAIN_REVIEW"
    document["authoritative_semantic_decisions"] = [
        {
            "id": f"semantic_decision_{number}",
            "review_item_number": number,
            "source_topic_id": topic["id"],
            "authoritative_outcome": f"Product Owner outcome {number}.",
        }
        for number, topic in enumerate(package["topics"], 1)
    ]
    source_sha = "a" * 64
    document["exact_boundary_provenance"] = {
        "authority": "PRODUCT_OWNER_DOMAIN_REVIEW",
        "sources": [
            {
                "artifact_id": "boundary_decisions_fixture",
                "sha256": source_sha,
                "authority": "PRODUCT_OWNER_DOMAIN_REVIEW",
                "decision_count": 1,
            }
        ],
        "resolved_boundaries": [
            {
                "boundary_proposal_id": "boundary_fixture",
                "canonical_word_id": words[1]["id"],
                "timestamp": words[1]["start_seconds"],
                "source_artifact_id": "boundary_decisions_fixture",
                "source_artifact_sha256": source_sha,
                "authority": "PRODUCT_OWNER_DOMAIN_REVIEW",
                "status": "DECIDED",
            }
        ],
    }
    document["decisions"][0].update(
        semantic_decision_refs=["semantic_decision_1"],
        boundary_decision_refs=["boundary_fixture"],
    )
    document["decisions"][1].update(
        semantic_decision_refs=["semantic_decision_2", "semantic_decision_3"],
        boundary_decision_refs=[],
    )
    document["decisions"][2].update(
        semantic_decision_refs=["semantic_decision_4"],
        boundary_decision_refs=[],
    )
    decisions_path = tmp_path / "complete-authority.json"
    write_json(decisions_path, document)

    status = run_cli(
        "project-review-v2-status",
        str(project),
        "--package",
        str(package_path),
        "--decisions",
        str(decisions_path),
    )
    assert status.returncode == 0, status.stderr
    report = json.loads(status.stdout)
    assert report["authoritative_semantic_decisions"] == 4
    assert report["resolved_boundary_decisions"] == 1

    broken = json.loads(json.dumps(document))
    broken["decisions"][0]["boundary_decision_refs"] = []
    write_json(decisions_path, broken)
    status = run_cli(
        "project-review-v2-status",
        str(project),
        "--package",
        str(package_path),
        "--decisions",
        str(decisions_path),
    )
    assert status.returncode == 2
    assert "exact-boundary decision provenance is incomplete" in status.stderr


def test_v2_fails_closed_on_gap_overlap_and_double_consumption(tmp_path: Path) -> None:
    project, package_path, words = make_v2_package(tmp_path)
    base = make_v2_decisions(package_path, words)
    for label, mutate, expected in (
        (
            "gap",
            lambda value: value["decisions"][0]["source_fragments"].pop(0),
            "gap or overlap",
        ),
        (
            "double",
            lambda value: value["decisions"][0]["results"][1]["fragment_refs"].append("fragment_0"),
            "consumed more than once",
        ),
    ):
        document = json.loads(json.dumps(base))
        mutate(document)
        path = tmp_path / f"{label}.json"
        write_json(path, document)
        status = run_cli(
            "project-review-v2-status", str(project), "--package", str(package_path), "--decisions", str(path)
        )
        assert status.returncode == 2
        assert expected in status.stderr


def test_boundary_proposals_are_deterministic_and_non_authoritative(tmp_path: Path) -> None:
    project, package_path, words = make_v2_package(tmp_path)
    package = read_json(package_path)
    requests = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.boundary_proposal_requests",
        "artifact_id": "boundary_requests_fixture",
        "review_package_id": package["artifact_id"],
        "review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "requests": [
            {
                "id": "boundary_single_fixture",
                "affected_original_drafts": [package["topics"][0]["id"]],
                "accepted_po_semantic_decision": "Split at the accepted semantic transition.",
                "boundary_role": "INTERNAL",
                "candidate_word_ids": [words[1]["id"]],
                "mechanical_rationales": ["First canonical word after the lexical transition."],
                "confidence": "HIGH",
            },
            {
                "id": "boundary_multiple_fixture",
                "affected_original_drafts": [package["topics"][3]["id"]],
                "accepted_po_semantic_decision": "Realign the left boundary.",
                "boundary_role": "LEFT",
                "candidate_word_ids": [words[0]["id"], words[1]["id"]],
                "mechanical_rationales": ["Sentence start.", "First content word."],
                "confidence": "MEDIUM",
            },
            {
                "id": "boundary_blocked_fixture",
                "affected_original_drafts": [package["topics"][2]["id"]],
                "accepted_po_semantic_decision": "Use the exact question start.",
                "boundary_role": "LEFT",
                "candidate_word_ids": [],
                "mechanical_rationales": [],
                "confidence": "LOW",
                "blocker_reason": "The existing canonical evidence contains no recoverable question marker.",
            },
        ],
    }
    requests_path = tmp_path / "requests.json"
    write_json(requests_path, requests)
    outputs = [tmp_path / "boundary-first", tmp_path / "boundary-second"]
    for output in outputs:
        prepared = run_cli(
            "project-review-boundary-prepare",
            str(project),
            "--package",
            str(package_path),
            "--requests",
            str(requests_path),
            "--output",
            str(output),
        )
        assert prepared.returncode == 0, prepared.stderr
        report = json.loads(prepared.stdout)
        assert (report["total"], report["unambiguous"], report["ambiguous"], report["blocked"]) == (3, 1, 1, 1)
    assert (outputs[0] / "boundary_proposals.json").read_bytes() == (outputs[1] / "boundary_proposals.json").read_bytes()
    assert (outputs[0] / "BOUNDARY_REVIEW.md").read_bytes() == (outputs[1] / "BOUNDARY_REVIEW.md").read_bytes()
    artifact = read_json(outputs[0] / "boundary_proposals.json")
    assert artifact["authority"] == "REVIEW_REQUIRED"
    assert {item["status"] for item in artifact["proposals"]} == {"REVIEW_REQUIRED"}
    assert artifact["word_timeline"]["sha256"]


def test_product_owner_boundary_decisions_are_complete_traceable_and_deterministic(tmp_path: Path) -> None:
    project, package_path, words = make_v2_package(tmp_path)
    package = read_json(package_path)
    requests = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.boundary_proposal_requests",
        "artifact_id": "boundary_resolution_requests_fixture",
        "review_package_id": package["artifact_id"],
        "review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "requests": [
            {
                "id": "boundary_resolution_single",
                "affected_original_drafts": [package["topics"][0]["id"]],
                "accepted_po_semantic_decision": "Split at the accepted transition.",
                "boundary_role": "INTERNAL",
                "candidate_word_ids": [words[1]["id"]],
                "mechanical_rationales": ["First canonical word after the transition."],
                "confidence": "HIGH",
            },
            {
                "id": "boundary_resolution_multiple",
                "affected_original_drafts": [package["topics"][3]["id"]],
                "accepted_po_semantic_decision": "Realign the left boundary.",
                "boundary_role": "LEFT",
                "candidate_word_ids": [words[0]["id"], words[1]["id"]],
                "mechanical_rationales": ["Sentence start.", "First content word."],
                "confidence": "MEDIUM",
            },
        ],
    }
    requests_path = tmp_path / "resolution-requests.json"
    write_json(requests_path, requests)
    proposal_dir = tmp_path / "resolution-proposals"
    prepared = run_cli(
        "project-review-boundary-prepare",
        str(project),
        "--package",
        str(package_path),
        "--requests",
        str(requests_path),
        "--output",
        str(proposal_dir),
    )
    assert prepared.returncode == 0, prepared.stderr
    proposals_path = proposal_dir / "boundary_proposals.json"
    proposals = read_json(proposals_path)
    ledger = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.boundary_review_ledger",
        "artifact_id": "boundary_resolution_ledger_fixture",
        "boundary_proposals": {
            "artifact_id": proposals["artifact_id"],
            "sha256": hashlib.sha256(proposals_path.read_bytes()).hexdigest(),
        },
        "reviewer": {"actor_type": "product_owner", "actor_id": "product_owner_fixture"},
        "review_gate": "DOMAIN_REVIEW",
        "decisions": [
            {
                "boundary_proposal_id": proposals["proposals"][0]["boundary_proposal_id"],
                "outcome": "ACCEPT_BOUNDARY_PROPOSAL",
                "selected_candidate_number": 1,
                "canonical_word_id": proposals["proposals"][0]["candidates"][0]["word_id"],
                "timestamp": proposals["proposals"][0]["candidates"][0]["timestamp"],
            },
            {
                "boundary_proposal_id": proposals["proposals"][1]["boundary_proposal_id"],
                "outcome": "SELECT_ALTERNATIVE",
                "selected_candidate_number": 2,
                "canonical_word_id": proposals["proposals"][1]["candidates"][1]["word_id"],
                "timestamp": proposals["proposals"][1]["candidates"][1]["timestamp"],
            },
        ],
    }
    ledger_path = tmp_path / "boundary-ledger.json"
    write_json(ledger_path, ledger)
    outputs = [tmp_path / "resolved-first.json", tmp_path / "resolved-second.json"]
    for output in outputs:
        resolved = run_cli(
            "project-review-boundary-resolve",
            str(project),
            "--proposals",
            str(proposals_path),
            "--ledger",
            str(ledger_path),
            "--output",
            str(output),
        )
        assert resolved.returncode == 0, resolved.stderr
        assert json.loads(resolved.stdout)["unresolved_review_required"] == 0
    assert outputs[0].read_bytes() == outputs[1].read_bytes()

    status = run_cli(
        "project-review-boundary-status",
        str(project),
        "--proposals",
        str(proposals_path),
        "--decisions",
        str(outputs[0]),
    )
    assert status.returncode == 0, status.stderr
    report = json.loads(status.stdout)
    assert report["decisions_persisted"] == report["proposals"] == 2
    assert report["unresolved_review_required"] == 0
    artifact = read_json(outputs[0])
    assert artifact["authority"] == "PRODUCT_OWNER_DOMAIN_REVIEW"
    assert {item["status"] for item in artifact["decisions"]} == {"DECIDED"}
    assert artifact["transcript_assurance"] == proposals["transcript_assurance"]
    assert read_json(proposals_path)["authority"] == "REVIEW_REQUIRED"


def test_boundary_resolution_rejects_ledger_anchor_mismatch(tmp_path: Path) -> None:
    project, package_path, words = make_v2_package(tmp_path)
    package = read_json(package_path)
    requests = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.boundary_proposal_requests",
        "artifact_id": "boundary_mismatch_requests_fixture",
        "review_package_id": package["artifact_id"],
        "review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "requests": [
            {
                "id": "boundary_mismatch_fixture",
                "affected_original_drafts": [package["topics"][0]["id"]],
                "accepted_po_semantic_decision": "Split at the accepted transition.",
                "boundary_role": "INTERNAL",
                "candidate_word_ids": [words[1]["id"]],
                "mechanical_rationales": ["First canonical word after the transition."],
                "confidence": "HIGH",
            }
        ],
    }
    requests_path = tmp_path / "mismatch-requests.json"
    write_json(requests_path, requests)
    proposal_dir = tmp_path / "mismatch-proposals"
    prepared = run_cli(
        "project-review-boundary-prepare",
        str(project),
        "--package",
        str(package_path),
        "--requests",
        str(requests_path),
        "--output",
        str(proposal_dir),
    )
    assert prepared.returncode == 0, prepared.stderr
    proposals_path = proposal_dir / "boundary_proposals.json"
    proposals = read_json(proposals_path)
    ledger = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.boundary_review_ledger",
        "artifact_id": "boundary_mismatch_ledger_fixture",
        "boundary_proposals": {
            "artifact_id": proposals["artifact_id"],
            "sha256": hashlib.sha256(proposals_path.read_bytes()).hexdigest(),
        },
        "reviewer": {"actor_type": "product_owner", "actor_id": "product_owner_fixture"},
        "review_gate": "DOMAIN_REVIEW",
        "decisions": [
            {
                "boundary_proposal_id": "boundary_mismatch_fixture",
                "outcome": "ACCEPT_BOUNDARY_PROPOSAL",
                "selected_candidate_number": 1,
                "canonical_word_id": words[0]["id"],
                "timestamp": words[0]["start_seconds"],
            }
        ],
    }
    ledger_path = tmp_path / "mismatch-ledger.json"
    write_json(ledger_path, ledger)
    resolved = run_cli(
        "project-review-boundary-resolve",
        str(project),
        "--proposals",
        str(proposals_path),
        "--ledger",
        str(ledger_path),
        "--output",
        str(tmp_path / "mismatch-result.json"),
    )
    assert resolved.returncode == 2
    assert "selected canonical anchor does not match" in resolved.stderr


def test_issue_113_authoritative_boundary_ledger_is_complete() -> None:
    ledger = read_json(ROOT / "analysis" / "issue_113_boundary_review_ledger.json")
    decisions = ledger["decisions"]
    assert len(decisions) == 25
    assert len({item["boundary_proposal_id"] for item in decisions}) == 25
    assert {item["outcome"] for item in decisions} == {
        "ACCEPT_BOUNDARY_PROPOSAL",
        "SELECT_ALTERNATIVE",
    }
    candidate_two = [item for item in decisions if item["selected_candidate_number"] == 2]
    assert candidate_two == [
        {
            "boundary_proposal_id": "issue_113_boundary_09_left",
            "canonical_word_id": "transcript_revision_video_001_r1:word:006290",
            "outcome": "SELECT_ALTERNATIVE",
            "selected_candidate_number": 2,
            "timestamp": 4440.051,
        }
    ]
