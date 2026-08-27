#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SLICE_DIR = ROOT / "analysis" / "golden_knowledge_slice"
BUILDER = SLICE_DIR / "build_golden_slice.py"
CURATION = SLICE_DIR / "curation.json"
ARTIFACT = SLICE_DIR / "golden_knowledge_slice.json"
CANONICAL = ROOT / "analysis" / "word_timeline_mvp" / "canonical_evidence_bundle.json"
EXPECTED_SHA256 = "177d030a6ac3e3dc0a28d655db0f12321e09caba8eff494c078aeb828339d4d6"


def load_builder():
    spec = importlib.util.spec_from_file_location("golden_slice_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER_MODULE = load_builder()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_slice():
    return BUILDER_MODULE.build_slice(CURATION)


def test_golden_slice_is_byte_deterministic_and_matches_committed_artifact():
    first = BUILDER_MODULE.canonical_bytes(build_slice())
    second = BUILDER_MODULE.canonical_bytes(build_slice())
    assert first == second == ARTIFACT.read_bytes()
    assert BUILDER_MODULE.sha256_bytes(first) == EXPECTED_SHA256


def test_minimum_knowledge_model_and_reverse_navigation_exist():
    document = build_slice()
    assert document["artifact_type"] == "seminartext.golden_knowledge_slice"
    assert document["seminar"]["title"] == "Стресс код"
    assert len(document["sources"]) == 1
    assert len(document["topics"]) == 3
    assert len(document["concepts"]) == 7
    assert len(document["evidence"]) == 10

    topics = {item["id"]: item for item in document["topics"]}
    evidence = {item["id"]: item for item in document["evidence"]}
    for concept in document["concepts"]:
        assert concept["derivation_status"] == "provisional_manual_curation"
        assert concept["review_status"] == "product_review_required"
        assert concept["topic_ids"]
        assert concept["evidence_ids"]
        assert all(concept["id"] in topics[item]["concept_ids"] for item in concept["topic_ids"])
        assert all(item in evidence for item in concept["evidence_ids"])


def test_topic_inputs_are_gold_or_explicit_manual_and_gold_is_unchanged():
    document = build_slice()
    assert [topic["structure_origin"] for topic in document["topics"]] == [
        "gold_dataset_a",
        "manual_issue_44",
        "manual_issue_44",
    ]
    gold = document["topics"][0]
    assert gold["title"] == "Стресс как механизм адаптации и выживания"
    assert gold["coverage"] == "partial_start_clipped_to_canonical_bundle"
    assert gold["structure_provenance"] == {
        "benchmark_sha256": "3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803",
        "case_id": "video_001_window_01",
        "gold_start_segment_id": 86,
        "review_status": "gold_complete",
    }


def test_every_evidence_quote_and_locator_resolves_to_canonical_words():
    document = build_slice()
    canonical = load_json(CANONICAL)
    words = {item["id"]: item for item in canonical["words"]}
    transcript = canonical["transcript_revisions"][0]
    for item in document["evidence"]:
        first = words[item["canonical_word_start_id"]]
        last = words[item["canonical_word_end_id"]]
        selected = canonical["words"][first["sequence"] : last["sequence"] + 1]
        assert item["quote"] == transcript["canonical_text"][first["char_start"] : last["char_end"]]
        aligned = [word for word in selected if word["alignment_status"] == "aligned"]
        assert item["locator"] == {
            "end_seconds": aligned[-1]["end_seconds"],
            "start_seconds": aligned[0]["start_seconds"],
            "type": "time_interval",
        }
        assert item["canonical_source_id"] == "source_stress_code_video_001"


def test_unaligned_words_remain_explicit_inside_knowledge_evidence():
    document = build_slice()
    canonical = load_json(CANONICAL)
    evidence = next(
        item
        for item in document["evidence"]
        if item["id"] == "evidence_problem_resolution_with_unaligned_words"
    )
    expected_ids = [canonical["words"][970]["id"], canonical["words"][971]["id"]]
    assert evidence["unaligned_word_ids"] == expected_ids
    assert evidence["timing_status"] == "aligned_envelope_with_explicit_unaligned_words"
    for sequence in (970, 971):
        word = canonical["words"][sequence]
        assert word["start_seconds"] is None
        assert word["end_seconds"] is None


def test_repeated_concept_identity_is_conservative_and_auditable():
    document = build_slice()
    concept = next(
        item
        for item in document["concepts"]
        if item["id"] == "concept_survival_in_changing_environment"
    )
    assert concept["topic_ids"] == [
        "topic_stress_adaptation_survival",
        "topic_personal_professional_kinesiology",
    ]
    assert concept["evidence_ids"] == [
        "evidence_survival_environment",
        "evidence_modern_survival_and_practice",
    ]
    assert "не автоматический semantic merge" in concept["identity_rationale"]


def test_validator_rejects_orphan_concept_evidence():
    document = build_slice()
    canonical = load_json(CANONICAL)
    broken = copy.deepcopy(document)
    broken["concepts"][0]["evidence_ids"] = ["evidence_missing"]
    errors = BUILDER_MODULE.validate_slice(broken, canonical)
    assert any("orphan Evidence evidence_missing" in error for error in errors)


def test_builder_rejects_changed_canonical_bundle_hash(tmp_path):
    curation = load_json(CURATION)
    curation["canonical_bundle"]["sha256"] = "0" * 64
    changed = tmp_path / "curation.json"
    changed.write_text(json.dumps(curation, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="canonical bundle SHA-256 mismatch"):
        BUILDER_MODULE.build_slice(changed)


if __name__ == "__main__":
    test_golden_slice_is_byte_deterministic_and_matches_committed_artifact()
    test_minimum_knowledge_model_and_reverse_navigation_exist()
    test_topic_inputs_are_gold_or_explicit_manual_and_gold_is_unchanged()
    test_every_evidence_quote_and_locator_resolves_to_canonical_words()
    test_unaligned_words_remain_explicit_inside_knowledge_evidence()
    test_repeated_concept_identity_is_conservative_and_auditable()
    test_validator_rejects_orphan_concept_evidence()
    print("Golden Knowledge Slice tests passed")
