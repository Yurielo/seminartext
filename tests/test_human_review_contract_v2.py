from __future__ import annotations

import hashlib
import json
from pathlib import Path

from test_human_review_workflow import prepare, read_json, run_cli, write_json


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
    assert len(output["fragment_lineage"]) == 6
    assert output["source_topic_snapshots"] == read_json(package_path)["topics"]
    assert all(item["transcript_provenance"]["verification_state"] == "fully_human_verified" for item in output["fragment_lineage"])
    assert all(item["word_timeline_provenance"]["sha256"] == output["word_timeline"]["sha256"] for item in output["fragment_lineage"])
    assert all(item["provenance"]["canonical_evidence_sha256"] == output["canonical_evidence"]["sha256"] for item in output["semantic_knowledge"])


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
