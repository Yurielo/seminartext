from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/issue_68_vertical_slice"))
import batch_review as batch  # noqa: E402
import build_domain_review_qa as governed  # noqa: E402

OUTPUT = ROOT / "analysis/issue_68_vertical_slice/domain_review_v1"
SCHEMA = ROOT / "schemas/issue_68_batch_review_v1.schema.json"
SEMANTIC = ROOT / "analysis/issue_68_vertical_slice/semantic_authoring_v1/semantic_authoring_package.json"
PROJECT = Path("/Users/yurielokhin/Documents/seminartext_projects/Стресс код")
REVIEW = PROJECT / "review/issue_113_contract_v2/domain_review/topic_review_result_v2.json"
EVIDENCE = PROJECT / "evidence/canonical_bundle.json"
APPROVED_SUBMISSION = OUTPUT / "approved_batch_submission_2026-10-30.json"


def read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def historical_link_review_ledger() -> dict:
    # These tests remove past link decisions to replay their original admission.
    # Start from the retained pre-title-review revision, rather than deleting
    # history from a later ledger that explicitly binds that parent.
    current = read(OUTPUT / "domain_review_decisions.json")
    parent = current.get("title_review_revision")
    return (read(OUTPUT / "revisions" / f"{parent['parent_ledger_sha256']}.json")
            if parent else current)


def test_applied_batch_preserves_only_deferred_links() -> None:
    Draft202012Validator.check_schema(read(SCHEMA))
    qa = read(OUTPUT / "domain_review_qa.json")
    package = read(OUTPUT / "batch_review.json")
    batch.validate_schema(package)
    active = package["active"]
    deferred = package["deferred"]
    assert package["semantic_authority"] == "PROVISIONAL_UNREVIEWED"
    assert package["qa_sha256"] == hashlib.sha256((OUTPUT / "domain_review_qa.json").read_bytes()).hexdigest()
    assert active == []
    assert len(deferred) == 7
    assert len({item["link_id"] for item in active + deferred}) == 7
    assert {item["link_id"] for item in active + deferred} == {
        link["link_id"] for link in qa["link_results"] if link["classification"] == "LINK_EXCEPTION"
    }
    assert all(item["evidence_complete"] and item["source_revision_id"] and item["evidence_sha256"]
               and item["canonical_evidence_reference"] and item["mention_excerpt"] for item in active + deferred)
    assert all(set(indexed) == {item["link_id"] for item in active}
               for groups in package["groups"].values()
               for indexed in [{link_id for ids in groups.values() for link_id in ids}])
    assert all(item["deferred"] for item in deferred)


def test_applied_submission_is_complete_and_hash_bound() -> None:
    package = read(OUTPUT / "batch_review.json")
    submission = read(APPROVED_SUBMISSION)
    ledger = read(OUTPUT / "domain_review_decisions.json")
    assert submission["review_package_sha256"] == (
        "eeee4931ca286750ac56f57e034ea084ee12222b77f47468570266502debbd3a"
    )
    assert len(submission["decisions"]) == 52
    assert {item["action"] for item in submission["decisions"]} == {
        "ACCEPT", "REJECT", "DEFER"
    }
    assert sum(item["action"] == "ACCEPT" for item in submission["decisions"]) == 37
    assert sum(item["action"] == "REJECT" for item in submission["decisions"]) == 9
    assert sum(item["action"] == "DEFER" for item in submission["decisions"]) == 6
    persisted = {item["decision_id"]: item for item in ledger["link_decisions"]}
    assert all(persisted[item["governed_decision"]["decision_id"]] == item["governed_decision"]
               for item in submission["decisions"])
    assert package["active"] == []
    assert len(package["deferred"]) == 7
    if EVIDENCE.exists() and REVIEW.exists():
        rebuilt = governed.build_qa(
            ROOT,
            PROJECT,
            REVIEW,
            SEMANTIC,
            OUTPUT / "domain_review_decisions.json",
        )
        assert batch.encoded(rebuilt) == (OUTPUT / "domain_review_qa.json").read_bytes()
    rendered = batch.markdown(package)
    assert "Это один пакет рекомендаций, а не решение системы" in rendered
    assert "Постановка Целей Сессии» → «Коррекция» должна быть отклонена" in rendered
    assert "## PREVIOUSLY_DEFERRED" in rendered
    assert len({recommendation[1] for recommendation in batch.RECOMMENDATIONS.values()}) == 52
    assert package["semantic_authority"] == "PROVISIONAL_UNREVIEWED"


@pytest.mark.skipif(not EVIDENCE.exists() or not REVIEW.exists(), reason="local Issue #68 source project unavailable")
@pytest.mark.parametrize("problem", ["stale_revision", "unknown_link", "unsupported_action", "duplicate", "duplicate_historical_id", "stale_package", "stale_per_link_package", "stale_evidence", "missing_authority", "not_confirmed"])
def test_invalid_batch_never_changes_ledger(tmp_path: Path, problem: str) -> None:
    original = historical_link_review_ledger()
    applied = read(APPROVED_SUBMISSION)["decisions"][0]["governed_decision"]
    ledger_path = tmp_path / "domain_review_decisions.json"
    baseline = {**original, "link_decisions": [
        item for item in original["link_decisions"]
        if item["decision_id"] != applied["decision_id"]
    ]}
    ledger_path.write_bytes(batch.encoded(baseline))
    qa = governed.build_qa(ROOT, PROJECT, REVIEW, SEMANTIC, ledger_path)
    assert qa["errors"] == []
    governed.write_review_outputs(tmp_path, qa, ledger_path, EVIDENCE, SEMANTIC)
    package_path = tmp_path / "batch_review.json"
    package = read(package_path)
    item = package["active"][0]
    decision = {
        "decision_id": "synthetic_unapplied_decision", "authority": "PRODUCT_OWNER_DOMAIN_REVIEW",
        "outcome": "DEFER_LINK", "target_link_id": item["link_id"],
        "link_snapshot": item["governed_link_snapshot"],
    }
    entry = {"link_id": item["link_id"], "topic_id": item["topic_id"],
             "concept_id": item["concept_id"], "source_revision_id": item["source_revision_id"],
             "evidence_sha256": item["evidence_sha256"], "action": "DEFER",
             "review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
             "human_confirmed": True, "governed_decision": decision}
    submission = {"review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
                  "decision_ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
                  "decisions": [entry]}
    if problem == "stale_revision":
        entry["source_revision_id"] = "old-revision"
    elif problem == "unknown_link":
        entry["link_id"] = "unknown-link"
    elif problem == "unsupported_action":
        entry["action"] = "AUTO_ACCEPT"
    elif problem == "duplicate":
        submission["decisions"].append(deepcopy(entry))
    elif problem == "duplicate_historical_id":
        decision["decision_id"] = read(OUTPUT / "domain_review_decisions.json")["concept_identity_decisions"][0]["decision_id"]
    elif problem == "stale_package":
        submission["review_package_sha256"] = "0" * 64
    elif problem == "stale_per_link_package":
        entry["review_package_sha256"] = "0" * 64
    elif problem == "stale_evidence":
        entry["evidence_sha256"] = "0" * 64
    elif problem == "missing_authority":
        decision["authority"] = "MACHINE"
    elif problem == "not_confirmed":
        entry["human_confirmed"] = False
    batch_path = tmp_path / "batch.json"
    batch_path.write_bytes(batch.encoded(submission))
    before = ledger_path.read_bytes()
    with pytest.raises(ValueError):
        batch.apply_batch(package_path, batch_path, ledger_path, ROOT, PROJECT,
                          REVIEW, SEMANTIC, tmp_path)
    assert ledger_path.read_bytes() == before


@pytest.mark.skipif(not EVIDENCE.exists() or not REVIEW.exists(), reason="local Issue #68 source project unavailable")
def test_mixed_historical_decisions_apply_atomically_and_retry(tmp_path: Path) -> None:
    original = historical_link_review_ledger()
    choices = {"ACCEPT_LINK": "ACCEPT", "REJECT_LINK": "REJECT",
               "REMAP_LINK": "REASSIGN", "DEFER_LINK": "DEFER"}
    selected = []
    for outcome in choices:
        selected.append(next(item for item in original["link_decisions"]
                             if item["outcome"] == outcome
                             and (outcome != "REMAP_LINK" or "day4" in item["decision_id"])))
    removed_ids = {item["decision_id"] for item in selected}
    baseline = {**original, "link_decisions": [item for item in original["link_decisions"]
                                                if item["decision_id"] not in removed_ids]}
    ledger = tmp_path / "domain_review_decisions.json"
    ledger.write_bytes(batch.encoded(baseline))
    qa = governed.build_qa(ROOT, PROJECT, REVIEW, SEMANTIC, ledger)
    assert qa["status"] != "INVALID"
    governed.write_review_outputs(tmp_path, qa, ledger, EVIDENCE, SEMANTIC)
    package_path = tmp_path / "batch_review.json"
    package = read(package_path)
    submitted_package_path = tmp_path / "submitted_batch_review.json"
    submitted_package_path.write_bytes(package_path.read_bytes())
    active = {item["link_id"]: item for item in package["active"]}
    entries = []
    for decision in selected:
        item = active[decision["target_link_id"]]
        entries.append({"link_id": item["link_id"], "topic_id": item["topic_id"],
                        "concept_id": item["concept_id"], "source_revision_id": item["source_revision_id"],
                        "evidence_sha256": item["evidence_sha256"],
                        "review_package_sha256": hashlib.sha256(submitted_package_path.read_bytes()).hexdigest(),
                        "action": choices[decision["outcome"]], "human_confirmed": True,
                        "governed_decision": decision})
    submission = {"review_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
                  "decision_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
                  "decisions": entries}
    submission_path = tmp_path / "submission.json"
    submission_path.write_bytes(batch.encoded(submission))
    invalid_submission = deepcopy(submission)
    remap_entry = next(item for item in invalid_submission["decisions"] if item["action"] == "REASSIGN")
    remap_entry["governed_decision"]["replacement_topic_reference"] = "unknown_topic"
    invalid_path = tmp_path / "invalid_submission.json"
    invalid_path.write_bytes(batch.encoded(invalid_submission))
    before = ledger.read_bytes()
    baseline_links = {item["link_id"]: item for item in qa["link_results"]}
    with pytest.raises(ValueError, match="governed validation failed"):
        batch.apply_batch(submitted_package_path, invalid_path, ledger, ROOT, PROJECT,
                          REVIEW, SEMANTIC, tmp_path)
    assert ledger.read_bytes() == before
    altered_package = deepcopy(package)
    altered_package["active"][0]["topic_title"] = "Changed outside governed QA"
    altered_package_path = tmp_path / "altered_package.json"
    altered_package_path.write_bytes(batch.encoded(altered_package))
    altered_submission = deepcopy(submission)
    altered_hash = hashlib.sha256(altered_package_path.read_bytes()).hexdigest()
    altered_submission["review_package_sha256"] = altered_hash
    for entry in altered_submission["decisions"]:
        entry["review_package_sha256"] = altered_hash
    altered_submission_path = tmp_path / "altered_submission.json"
    altered_submission_path.write_bytes(batch.encoded(altered_submission))
    with pytest.raises(ValueError, match="review package differs"):
        batch.apply_batch(altered_package_path, altered_submission_path, ledger,
                          ROOT, PROJECT, REVIEW, SEMANTIC, tmp_path)
    assert ledger.read_bytes() == before
    result_hash = batch.apply_batch(submitted_package_path, submission_path, ledger, ROOT, PROJECT,
                                    REVIEW, SEMANTIC, tmp_path)
    assert result_hash == hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert {item["decision_id"] for item in read(ledger)["link_decisions"]} == {
        item["decision_id"] for item in original["link_decisions"]}
    persisted = {item["decision_id"]: item for item in read(ledger)["link_decisions"]}
    assert all(persisted[item["decision_id"]] == item for item in original["link_decisions"])
    rebuilt_qa = read(tmp_path / "domain_review_qa.json")
    assert rebuilt_qa["errors"] == []
    after_links = {item["link_id"]: item for item in rebuilt_qa["link_results"]}
    selected_links = {item["target_link_id"] for item in selected}
    assert all(after_links[link_id] == link for link_id, link in baseline_links.items()
               if link_id not in selected_links)
    assert batch.encoded(governed.build_qa(ROOT, PROJECT, REVIEW, SEMANTIC, ledger)) == (
        tmp_path / "domain_review_qa.json").read_bytes()
    assert batch.apply_batch(submitted_package_path, submission_path, ledger, ROOT, PROJECT,
                             REVIEW, SEMANTIC, tmp_path) == result_hash


@pytest.mark.skipif(not EVIDENCE.exists() or not REVIEW.exists(), reason="local Issue #68 source project unavailable")
def test_existing_batch_workflow_preserves_title_review_history(tmp_path: Path) -> None:
    current = read(OUTPUT / "domain_review_decisions.json")
    parent = historical_link_review_ledger()
    decision = read(APPROVED_SUBMISSION)["decisions"][0]["governed_decision"]
    parent["link_decisions"] = [d for d in parent["link_decisions"]
                                if d["decision_id"] != decision["decision_id"]]
    parent_bytes = batch.encoded(parent)
    parent_hash = hashlib.sha256(parent_bytes).hexdigest()
    (tmp_path / "revisions").mkdir()
    (tmp_path / "revisions" / f"{parent_hash}.json").write_bytes(parent_bytes)
    ledger_data = {**parent, "topic_title_corrections": current["topic_title_corrections"],
                   "title_review_revision": {**current["title_review_revision"],
                                             "parent_ledger_sha256": parent_hash}}
    ledger = tmp_path / "domain_review_decisions.json"
    ledger.write_bytes(batch.encoded(ledger_data))
    qa = governed.build_qa(ROOT, PROJECT, REVIEW, SEMANTIC, ledger)
    assert qa["errors"] == []
    governed.write_review_outputs(tmp_path, qa, ledger, EVIDENCE, SEMANTIC)
    package_path = tmp_path / "batch_review.json"
    saved_package = tmp_path / "submitted_package.json"
    saved_package.write_bytes(package_path.read_bytes())
    package = read(package_path)
    item = next(x for x in package["active"] if x["link_id"] == decision["target_link_id"])
    package_hash = hashlib.sha256(saved_package.read_bytes()).hexdigest()
    submission = {"review_package_sha256": package_hash,
                  "decision_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
                  "decisions": [{"link_id": item["link_id"], "topic_id": item["topic_id"],
                      "concept_id": item["concept_id"], "source_revision_id": item["source_revision_id"],
                      "evidence_sha256": item["evidence_sha256"], "review_package_sha256": package_hash,
                      "action": {v: k for k, v in batch.ACTIONS.items()}[decision["outcome"]],
                      "human_confirmed": True, "governed_decision": decision}]}
    submitted = tmp_path / "submission.json"
    submitted.write_bytes(batch.encoded(submission))
    result = batch.apply_batch(saved_package, submitted, ledger, ROOT, PROJECT, REVIEW, SEMANTIC, tmp_path)
    after = read(ledger)
    assert after["topic_title_corrections"] == current["topic_title_corrections"]
    assert after["link_decisions"][-1] == decision
    assert read(tmp_path / "domain_review_qa.json")["summary"]["topic_title_review_corrections"] == 8
    assert batch.apply_batch(saved_package, submitted, ledger, ROOT, PROJECT, REVIEW, SEMANTIC, tmp_path) == result
