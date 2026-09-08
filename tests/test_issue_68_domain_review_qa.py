from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/issue_68_vertical_slice/domain_review_v1"
QA_PATH = OUTPUT / "domain_review_qa.json"
REVIEW_PATH = OUTPUT / "DOMAIN_REVIEW.md"
MANIFEST_PATH = OUTPUT / "manifest.json"
DECISIONS_PATH = OUTPUT / "domain_review_decisions.json"


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_domain_review_qa_preserves_expected_input_inventory() -> None:
    qa = read_json(QA_PATH)

    assert qa["status"] == "READY_WITH_EXCEPTIONS"
    assert qa["semantic_authority"] == "PROVISIONAL_UNREVIEWED"
    assert qa["input_inventory"]["machine_topic_proposals"] == 262
    assert qa["input_inventory"]["authored_topic_results"] == 182
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

    assert len(topics) == 182
    assert len(concepts) == 19
    assert len(links) == 256
    assert len({item["candidate_concept_id"] for item in concepts}) == len(concepts)
    assert len({item["link_id"] for item in links}) == len(links)
    concept_ids = {item["candidate_concept_id"] for item in concepts}
    assert all(item["candidate_concept_reference"] in concept_ids for item in links)
    assert all(item["classification"] in {"REVIEW_CLEAR", "REVIEW_EXCEPTION"} for item in topics)
    assert all(item["semantic_status"] == "PROVISIONAL" for item in topics)
    decided = [item for item in topics if item["domain_review_status"] == "DECIDED"]
    assert [item["topic_id"] for item in decided] == [
        "issue_68_video_002_topic_proposal_020a",
        "issue_68_video_003_topic_proposal_051a",
        "issue_68_video_004_topic_proposal_001c",
        "issue_68_video_004_topic_proposal_024h",
        "issue_68_video_004_topic_proposal_024h2",
    ]
    assert all(
        item["domain_review_status"] == "REVIEW_REQUIRED"
        for item in topics
        if item not in decided
    )
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

    assert first["candidate_concept_id"] == "issue_68_candidate_concept_brain"
    assert first["classification"] == "IDENTITY_EXCEPTION"
    assert first["exception"]["human_decision_required"] is True
    assert "issue_68_video_002_topic_proposal_020a" not in review
    assert "issue_68_video_003_topic_proposal_051a" not in review
    assert "issue_68_video_004_topic_proposal_001c" not in review
    assert "issue_68_video_004_topic_proposal_024h" not in review
    assert "issue_68_candidate_concept_correction" not in review
    assert "issue_68_candidate_concept_nervous_system" not in review
    assert "issue_68_candidate_concept_brain" in review
    assert "REVIEW_CLEAR`\ndoes not mean `ACCEPTED" in review


def test_manifest_binds_deterministic_review_outputs() -> None:
    manifest = read_json(MANIFEST_PATH)

    assert manifest["qa_status"] == "READY_WITH_EXCEPTIONS"
    assert manifest["semantic_authority"] == "PROVISIONAL_UNREVIEWED"
    assert manifest["files"]["domain_review_qa.json"] == sha256(QA_PATH)
    assert manifest["files"]["DOMAIN_REVIEW.md"] == sha256(REVIEW_PATH)
    assert manifest["files"]["domain_review_decisions.json"] == sha256(DECISIONS_PATH)


def test_product_owner_topic_020a_decision_is_exact_and_neighbor_qa_passes() -> None:
    qa = read_json(QA_PATH)
    topic = next(
        item
        for item in qa["topic_results"]
        if item["topic_id"] == "issue_68_video_002_topic_proposal_020a"
    )
    resolution = topic["domain_review_resolution"]

    assert topic["classification"] == "REVIEW_CLEAR"
    assert topic["domain_review_status"] == "DECIDED"
    assert topic["semantic_status"] == "PROVISIONAL"
    assert topic["title"] == "Задание: классификация входящей, внутренней и производимой энергии"
    assert topic["start_word_id"].endswith(":word:007526")
    assert topic["end_word_id"].endswith(":word:007581")
    assert [item["disposition"] for item in resolution["results"]] == [
        "NON_SEMANTIC_EXCLUDED",
        "SEMANTIC_TOPIC",
        "NON_SEMANTIC_EXCLUDED",
    ]
    assert resolution["status"] == "DECIDED"
    assert resolution["package_semantic_promotion"] is False
    assert resolution["neighborhood_qa"] == {
        "previous_topic_id": "issue_68_video_002_topic_proposal_019",
        "previous_topic_ends_before_original_range": True,
        "decision_results_exactly_partition_original_range": True,
        "semantic_range_inside_original_range": True,
        "next_topic_id": "issue_68_video_002_topic_proposal_020b",
        "next_topic_starts_after_original_range": True,
        "neighboring_topic_overlap": False,
    }


def test_product_owner_topic_051a_decision_is_exact_and_neighbor_qa_passes() -> None:
    qa = read_json(QA_PATH)
    topic = next(
        item
        for item in qa["topic_results"]
        if item["topic_id"] == "issue_68_video_003_topic_proposal_051a"
    )
    resolution = topic["domain_review_resolution"]

    assert topic["classification"] == "REVIEW_CLEAR"
    assert topic["domain_review_status"] == "DECIDED"
    assert topic["semantic_status"] == "PROVISIONAL"
    assert topic["title"] == "Выбор участника и темы демонстрационной сессии"
    assert topic["start_word_id"].endswith(":word:015220")
    assert topic["end_word_id"].endswith(":word:015449")
    assert [item["disposition"] for item in resolution["results"]] == [
        "NON_SEMANTIC_EXCLUDED",
        "SEMANTIC_TOPIC",
    ]
    assert resolution["action"] == "REALIGN_LEFT"
    assert resolution["status"] == "DECIDED"
    assert resolution["package_semantic_promotion"] is False
    assert resolution["neighborhood_qa"] == {
        "previous_topic_id": "issue_68_video_003_topic_proposal_045f",
        "previous_topic_ends_before_original_range": True,
        "decision_results_exactly_partition_original_range": True,
        "semantic_range_inside_original_range": True,
        "next_topic_id": "issue_68_video_003_topic_proposal_051b",
        "next_topic_starts_after_original_range": True,
        "neighboring_topic_overlap": False,
    }


def test_product_owner_topic_001c_audio_term_normalization_is_traceable() -> None:
    qa = read_json(QA_PATH)
    topic = next(
        item
        for item in qa["topic_results"]
        if item["topic_id"] == "issue_68_video_004_topic_proposal_001c"
    )
    resolution = topic["domain_review_resolution"]

    assert topic["classification"] == "REVIEW_CLEAR"
    assert topic["domain_review_status"] == "DECIDED"
    assert topic["semantic_status"] == "PROVISIONAL"
    assert topic["title"] == "Специфическая, генетическая и неспецифическая регрессия"
    assert topic["start_word_id"].endswith(":word:000615")
    assert topic["end_word_id"].endswith(":word:000754")
    assert topic["qa_dimensions"]["left_boundary"] == "PASS"
    assert topic["qa_dimensions"]["right_boundary"] == "PASS"
    assert topic["qa_dimensions"]["transcript_assurance"] == "SELECTIVE_AUDIO_TERM_VERIFIED"
    assert resolution["action"] == "CONFIRM_AUDIO_RECESSION_SEMANTIC_NORMALIZATION_TO_REGRESSION"
    assert resolution["status"] == "DECIDED"
    assert resolution["package_semantic_promotion"] is False
    assert resolution["terminology_normalization"] == {
        "semantic_term": "регрессия",
        "source_term": "рецессия",
        "source_term_verification": "HUMAN_CONFIRMED_FROM_SOURCE_AUDIO",
        "traceability": "PRESERVED",
        "transcript_revision_action": "PRESERVE_UNCHANGED",
    }
    transcript_exception = next(
        item
        for item in qa["selective_transcript_verification_exceptions"]
        if item["exception_id"] == "issue_68_transcript_exception_regression_term"
    )
    assert transcript_exception["partial_resolution"] == {
        "topic_id": "issue_68_video_004_topic_proposal_001c",
        "decision_id": "issue_68_domain_review_topic_001c",
        "status": "SOURCE_TERM_CONFIRMED_SEMANTIC_TERM_NORMALIZED",
        "source_term": "рецессия",
        "semantic_term": "регрессия",
        "transcript_revision_mutated": False,
    }


def test_product_owner_topic_024h_split_is_exact_and_neighbor_qa_passes() -> None:
    qa = read_json(QA_PATH)
    topics = {
        item["topic_id"]: item
        for item in qa["topic_results"]
        if item["topic_id"]
        in {
            "issue_68_video_004_topic_proposal_024h",
            "issue_68_video_004_topic_proposal_024h2",
        }
    }
    first = topics["issue_68_video_004_topic_proposal_024h"]
    second = topics["issue_68_video_004_topic_proposal_024h2"]
    resolution = first["domain_review_resolution"]

    assert first["classification"] == second["classification"] == "REVIEW_CLEAR"
    assert first["domain_review_status"] == second["domain_review_status"] == "DECIDED"
    assert first["semantic_status"] == second["semantic_status"] == "PROVISIONAL"
    assert first["title"] == (
        "Генетический опыт: предел глубины анализа и переход к ресурсному состоянию"
    )
    assert first["start_word_id"].endswith(":word:009738")
    assert first["end_word_id"].endswith(":word:010253")
    assert second["title"] == "Гимнастика для мозга и повторение претестов"
    assert second["start_word_id"].endswith(":word:010254")
    assert second["end_word_id"].endswith(":word:010431")
    assert resolution == second["domain_review_resolution"]
    assert resolution["action"] == "SPLIT_REALIGN"
    assert resolution["result_topic_ids"] == [
        "issue_68_video_004_topic_proposal_024h",
        "issue_68_video_004_topic_proposal_024h2",
    ]
    assert resolution["status"] == "DECIDED"
    assert resolution["package_semantic_promotion"] is False
    assert resolution["neighborhood_qa"] == {
        "previous_topic_id": "issue_68_video_004_topic_proposal_024g",
        "previous_topic_ends_before_original_range": True,
        "decision_results_exactly_partition_original_range": True,
        "semantic_range_inside_original_range": True,
        "next_topic_id": "issue_68_video_004_topic_proposal_024i",
        "next_topic_starts_after_original_range": True,
        "neighboring_topic_overlap": False,
    }
    assert qa["summary"]["topic_domain_review_decisions"] == 4


def test_product_owner_correction_concept_is_a_bounded_umbrella() -> None:
    qa = read_json(QA_PATH)
    concept = next(
        item
        for item in qa["concept_results"]
        if item["candidate_concept_id"] == "issue_68_candidate_concept_correction"
    )
    resolution = concept["domain_review_resolution"]

    assert concept["classification"] == "CLEAR_FOR_HUMAN_BATCH_REVIEW"
    assert concept["domain_review_status"] == "DECIDED"
    assert concept["semantic_status"] == "PROVISIONAL"
    assert concept["proposed_canonical_label"] == "Коррекция"
    assert concept["evidence_reference_count"] == 45
    assert resolution["status"] == "DECIDED"
    assert resolution["outcome"] == "SAME_CONCEPT"
    assert resolution["canonical_role"] == "UMBRELLA_CONCEPT"
    assert resolution["identity_scope"] == "GENERAL_CORRECTION_PROCESS_ONLY"
    assert resolution["separate_method_identities_merged"] is False
    assert resolution["method_identity_policy"] == (
        "DISTINCT_UNLESS_SEPARATELY_HUMAN_REVIEWED"
    )
    assert resolution["package_semantic_promotion"] is False


def test_product_owner_nervous_system_related_concepts_are_not_merged() -> None:
    qa = read_json(QA_PATH)
    concepts = {
        item["candidate_concept_id"]: item
        for item in qa["concept_results"]
        if item["candidate_concept_id"]
        in {
            "issue_68_candidate_concept_nervous_system",
            "issue_68_candidate_concept_neural_connections_and_networks",
        }
    }
    nervous_system = concepts["issue_68_candidate_concept_nervous_system"]
    neural_networks = concepts[
        "issue_68_candidate_concept_neural_connections_and_networks"
    ]
    resolution = nervous_system["domain_review_resolution"]

    assert nervous_system["classification"] == "CLEAR_FOR_HUMAN_BATCH_REVIEW"
    assert neural_networks["classification"] == "CLEAR_FOR_HUMAN_BATCH_REVIEW"
    assert nervous_system["domain_review_status"] == "DECIDED"
    assert neural_networks["domain_review_status"] == "DECIDED"
    assert (
        nervous_system["semantic_status"]
        == neural_networks["semantic_status"]
        == "PROVISIONAL"
    )
    assert nervous_system["evidence_reference_count"] == 8
    assert neural_networks["evidence_reference_count"] == 4
    assert resolution == neural_networks["domain_review_resolution"]
    assert resolution["outcome"] == "RELATED"
    assert resolution["relation"] == "RELATED"
    assert resolution["identities_merged"] is False
    assert resolution["result_concept_ids"] == [
        "issue_68_candidate_concept_nervous_system",
        "issue_68_candidate_concept_neural_connections_and_networks",
    ]
    assert resolution["link_semantic_acceptance"] is False
    assert len(resolution["evidence_partition"]) == 10
    unresolved = [
        item
        for item in resolution["evidence_partition"]
        if item["unresolved_exact_term_signal"]
    ]
    assert [item["topic_reference"] for item in unresolved] == [
        "issue_68_video_004_topic_proposal_040"
    ]

    rewritten = [
        item
        for item in qa["link_results"]
        if "concept_identity_rebuild" in item
    ]
    by_topic = {}
    for item in rewritten:
        by_topic.setdefault(item["input_topic_reference"], set()).add(
            item["candidate_concept_reference"]
        )
        assert item["concept_identity_rebuild"]["semantic_acceptance"] is False
    assert by_topic["issue_68_video_003_topic_proposal_026"] == {
        "issue_68_candidate_concept_neural_connections_and_networks"
    }
    assert by_topic["issue_68_video_003_topic_proposal_086"] == {
        "issue_68_candidate_concept_nervous_system",
        "issue_68_candidate_concept_neural_connections_and_networks",
    }
    assert by_topic["issue_68_video_004_topic_proposal_014"] == {
        "issue_68_candidate_concept_nervous_system",
        "issue_68_candidate_concept_neural_connections_and_networks",
    }
    assert qa["summary"]["concept_domain_review_decisions"] == 2
    assert qa["summary"]["concept_candidates_total"] == 19
    assert qa["summary"]["concept_clear"] == 14
    assert qa["summary"]["concept_identity_exception"] == 5
    assert qa["summary"]["links_total"] == 256
