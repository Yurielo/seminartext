from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/issue_68_vertical_slice/domain_review_v1"
QA_PATH = OUTPUT / "domain_review_qa.json"
REVIEW_PATH = OUTPUT / "DOMAIN_REVIEW.md"
MANIFEST_PATH = OUTPUT / "manifest.json"


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_domain_review_qa_preserves_expected_input_inventory() -> None:
    qa = read_json(QA_PATH)

    assert qa["status"] == "READY_WITH_EXCEPTIONS"
    assert qa["semantic_authority"] == "PROVISIONAL_UNREVIEWED"
    assert qa["input_inventory"]["machine_topic_proposals"] == 262
    assert qa["input_inventory"]["authored_topic_results"] == 181
    assert qa["input_inventory"]["concept_candidates"] == 18
    assert qa["input_inventory"]["topic_concept_link_proposals"] == 254
    assert qa["input_inventory"]["baseline_rebuilt_without_authoring_decisions"] is True
    assert qa["inventory_reconciliation"]["current_semantic_package_concept_projection"] == 15
    assert qa["inventory_reconciliation"]["current_semantic_package_link_projection"] == 179
    assert qa["inventory_reconciliation"]["semantic_change_inferred"] is False
    assert qa["summary"]["coverage_gaps"] == 0
    assert qa["summary"]["coverage_overlaps"] == 0
    assert qa["errors"] == []


def test_every_result_is_classified_without_semantic_promotion() -> None:
    qa = read_json(QA_PATH)
    topics = qa["topic_results"]
    concepts = qa["concept_results"]
    links = qa["link_results"]

    assert len(topics) == 181
    assert len(concepts) == 18
    assert len(links) == 254
    assert all(item["classification"] in {"REVIEW_CLEAR", "REVIEW_EXCEPTION"} for item in topics)
    assert all(item["semantic_status"] == "PROVISIONAL" for item in topics)
    assert all(item["domain_review_status"] == "REVIEW_REQUIRED" for item in topics)
    assert all(
        item["classification"]
        in {"CLEAR_FOR_HUMAN_BATCH_REVIEW", "IDENTITY_EXCEPTION"}
        for item in concepts
    )
    assert all(item["semantic_status"] == "PROVISIONAL" for item in concepts)
    assert all(item["classification"] in {"LINK_CLEAR", "LINK_EXCEPTION"} for item in links)
    assert all(item["semantic_status"] == "PROVISIONAL" for item in links)
    assert qa["review_policy"]["review_clear_is_accepted"] is False
    assert qa["review_policy"]["automatic_semantic_acceptance"] is False


def test_first_material_exception_is_bounded_and_human_facing() -> None:
    qa = read_json(QA_PATH)
    first = qa["first_material_exception"]
    review = REVIEW_PATH.read_text(encoding="utf-8")

    assert first["topic_id"] == "issue_68_video_002_topic_proposal_020a"
    assert first["classification"] == "REVIEW_EXCEPTION"
    assert first["exception"]["human_decision_required"] is True
    assert first["qa_dimensions"]["left_boundary"] == "REVIEW_REQUIRED"
    assert first["qa_dimensions"]["right_boundary"] == "REVIEW_REQUIRED"
    assert "issue_68_video_002_topic_proposal_020a" in review
    assert "issue_68_video_003_topic_proposal_051a" not in review
    assert "REVIEW_CLEAR`\ndoes not mean `ACCEPTED" in review


def test_manifest_binds_deterministic_review_outputs() -> None:
    manifest = read_json(MANIFEST_PATH)

    assert manifest["qa_status"] == "READY_WITH_EXCEPTIONS"
    assert manifest["semantic_authority"] == "PROVISIONAL_UNREVIEWED"
    assert manifest["files"]["domain_review_qa.json"] == sha256(QA_PATH)
    assert manifest["files"]["DOMAIN_REVIEW.md"] == sha256(REVIEW_PATH)
