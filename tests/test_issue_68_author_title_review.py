"""Explicit title review preserves historical authority and exact source ranges."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/issue_68_vertical_slice"))
import build_domain_review_qa as governed

OUTPUT = ROOT / "analysis/issue_68_vertical_slice/domain_review_v1"


def test_recorded_author_titles_preserve_prior_reviews_and_pending_semantics():
    ledger = json.loads((OUTPUT / "domain_review_decisions.json").read_bytes())
    parent_hash = ledger["title_review_revision"]["parent_ledger_sha256"]
    parent_bytes = (OUTPUT / "revisions" / f"{parent_hash}.json").read_bytes()
    assert hashlib.sha256(parent_bytes).hexdigest() == parent_hash
    parent = json.loads(parent_bytes)
    assert {k: v for k, v in ledger.items() if k not in {
        "topic_title_corrections", "title_review_revision"}} == parent
    assert [len(ledger[k]) for k in ("decisions", "concept_identity_decisions", "link_decisions")] == [4, 7, 62]
    assert hashlib.sha256((ROOT / "analysis/issue_68_vertical_slice/semantic_authoring_v1/domain_authoring_decisions.json").read_bytes()).hexdigest() == "334eb68f65ac9abdfd9f4ed04110b3dec43f832daebf34ab2643e58edf6b40ff"
    expected = {
        "issue_68_video_002_topic_proposal_004": "Разбор мышечного тестирования: различение сильного и слабого ответа",
        "issue_68_video_002_topic_proposal_012": "Коррекция Промахивание меридианов и завершение претестов",
        "issue_68_video_002_topic_proposal_077b": "Критерий завершения сессии по УНЭ / УПЭ и выбор дальнейших действий",
        "issue_68_video_002_topic_proposal_081": "Техническое определение УНЭ / УПЭ с помощью мышечного теста",
        "issue_68_video_002_topic_proposal_083a": "Практика в паре: разрешение на работу, гипертонус и оценка УНЭ / УПЭ",
        "issue_68_video_004_topic_proposal_011a": "Этапы специфической регрессии и два пути входа в генетическое прошлое",
        "issue_68_video_004_topic_proposal_011e": "Техника неспецифической регрессии и возврата в настоящее",
        "issue_68_video_004_topic_proposal_024a": "Преимущества и ограничения неспецифической регрессии",
    }
    assert {c["target_topic_id"]: c["new_title"] for c in ledger["topic_title_corrections"]} == expected
    qa = json.loads((OUTPUT / "domain_review_qa.json").read_bytes())
    assert len(qa["topic_title_review_resolutions"]) == 8
    for topic in qa["topic_results"]:
        if topic["topic_id"] not in expected:
            assert "title_review_resolution" not in topic
            continue
        assert topic["title"] == expected[topic["topic_id"]]
        assert topic["semantic_status"] == "PROVISIONAL"
        assert topic["domain_review_status"] == "REVIEW_REQUIRED"
        correction = topic["title_review_resolution"]
        assert correction["topic_semantic_acceptance"] is False
        assert correction["relationship_decision_changed"] is False
        assert correction["transcript_mutated"] is False
        assert (topic["start_word_id"], topic["end_word_id"]) == (
            correction["start_word_id"], correction["end_word_id"])
    assert [qa["summary"][k] for k in ("topic_results_total", "concept_candidates_total", "links_total", "link_deferred")] == [182, 22, 246, 7]
    assert all(t["semantic_status"] == "PROVISIONAL" for t in qa["topic_results"])


@pytest.fixture
def title_batch(tmp_path):
    parent = {"decisions": [{"decision_id": "old", "meaning": "unchanged"}],
              "concept_identity_decisions": [], "link_decisions": [
                  {"decision_id": "deferred", "outcome": "DEFER_LINK"}]}
    payload = json.dumps(parent).encode()
    parent_hash = hashlib.sha256(payload).hexdigest()
    archive = tmp_path / "revisions"
    archive.mkdir()
    (archive / f"{parent_hash}.json").write_bytes(payload)
    words = [{"id": f"revision:word:{n:06}", "text": text,
              "transcript_revision_id": "revision"} for n, text in enumerate(("alpha", "beta"))]
    units, corrections = [], []
    for n in range(2):
        word_id = words[n]["id"]
        units.append(dict(topic_id=f"topic{n}", source_id="source", title=f"old{n}",
                          start_word_id=word_id, end_word_id=word_id,
                          start_word_sequence=n, end_word_sequence=n))
        corrections.append(dict(decision_id=f"rename{n}", target_topic_id=f"topic{n}",
            authority="PRODUCT_OWNER_DOMAIN_REVIEW", action="RENAME", scope="TOPIC_TITLE_ONLY",
            boundary_action="PRESERVE", decision_date="2026-11-01", source_instruction="Explicit synthetic review",
            source_id="source", transcript_revision_id="revision", original_title=f"old{n}", new_title=f"new{n}",
            start_word_id=word_id, end_word_id=word_id, canonical_evidence_sha256="e" * 64,
            semantic_package_sha256="p" * 64, span_sha256=hashlib.sha256(words[n]["text"].encode()).hexdigest()))
    ledger = {**deepcopy(parent), "title_review_revision": dict(schema_version="1.0.0",
        scope="TOPIC_TITLE_ONLY", parent_ledger_sha256=parent_hash), "topic_title_corrections": corrections}
    return units, ledger, tmp_path / "ledger.json", {"source": words}


def apply(batch):
    units, ledger, path, words = batch
    errors = []
    result = governed.apply_topic_title_corrections(units, ledger, path, words, "e" * 64, "p" * 64, errors)
    return result, errors


@pytest.mark.parametrize("field,value", [
    ("original_title", "stale"), ("source_id", "wrong"), ("end_word_id", "wrong"),
    ("transcript_revision_id", "wrong"), ("span_sha256", "0" * 64),
    ("canonical_evidence_sha256", "0" * 64), ("semantic_package_sha256", "0" * 64),
    ("authority", "system_validator"), ("scope", "ACCEPT_PACKAGE"),
    ("boundary_action", "REALIGN"), ("new_title", None),
])
def test_invalid_last_correction_never_partially_applies(title_batch, field, value):
    units, ledger, _, _ = title_batch
    before = deepcopy(units)
    ledger["topic_title_corrections"][-1][field] = value
    result, errors = apply(title_batch)
    assert errors and result == [] and units == before


@pytest.mark.parametrize("damage", ["duplicate", "old_decision", "parent_bytes", "extra_field", "empty"])
def test_history_and_scope_fail_closed(title_batch, damage):
    units, ledger, path, _ = title_batch
    before = deepcopy(units)
    if damage == "duplicate":
        ledger["topic_title_corrections"].append(deepcopy(ledger["topic_title_corrections"][0]))
    elif damage == "old_decision":
        ledger["decisions"][0]["meaning"] = "overwritten"
    elif damage == "parent_bytes":
        next((path.parent / "revisions").iterdir()).write_text("{}")
    elif damage == "empty":
        ledger["topic_title_corrections"] = []
    else:
        ledger["topic_title_corrections"][0]["accept_relationships"] = True
    result, errors = apply(title_batch)
    assert errors and result == [] and units == before


def test_valid_batch_changes_only_titles_with_explicit_scope(title_batch):
    units, ledger, _, _ = title_batch
    before = deepcopy(units)
    result, errors = apply(title_batch)
    assert not errors and len(result) == 2
    for old, new in zip(before, units):
        assert new["title"] != old["title"]
        assert {k: v for k, v in new.items() if k not in {"title", "title_review_resolution"}} == {
            k: v for k, v in old.items() if k != "title"}
    assert ledger["link_decisions"] == [{"decision_id": "deferred", "outcome": "DEFER_LINK"}]


def test_later_governed_decisions_can_append_without_rewriting_parent(title_batch):
    _, ledger, _, _ = title_batch
    later = {"decision_id": "later_explicit_decision", "outcome": "DEFER_LINK"}
    ledger["link_decisions"].append(later)
    result, errors = apply(title_batch)
    assert not errors and len(result) == 2
    assert ledger["link_decisions"][-1] == later
