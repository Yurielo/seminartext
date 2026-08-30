"""Regression checks for the accepted AUDIT-R1 governance outcome.

These checks intentionally validate only the accepted governance snapshot.  They
do not treat AUDIT-R1 as the active milestone after its acceptance.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "SEMINARTEXT_4_STATE.json"
ROADMAP_PATH = ROOT / "SEMINARTEXT_4_ROADMAP.md"


def _state():
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def test_topic_freeze_and_product_dispositions_are_accepted():
    state = _state()
    topic = state["stages"]["topic_engine"]
    treeseg = state["stages"]["global_seminar_structure"]
    obsidian = state["stages"]["obsidian_mvp"]

    assert topic["freeze_gate_status"] == "TOPIC_CANDIDATE_FREEZE_COMPLETE_DATASET_D_ACCESS_BLOCKED"
    assert topic["frozen_candidate_engine_id"] == "bge_m3_local_peak_v1"
    assert treeseg["product_review_complete"] is True
    assert treeseg["product_review_decision"] == "KEEP_TREESEG_AS_CHALLENGER"
    assert treeseg["role"] == "challenger"
    assert treeseg["production_promotion"] is False
    assert obsidian["product_review_complete"] is True
    assert obsidian["product_review_decision"] == "ADAPT_FURTHER"
    assert obsidian["production_ready"] is False


def test_canonical_knowledge_v1_is_present_in_state():
    state = _state()
    knowledge = state["stages"]["canonical_knowledge_v1"]
    assert knowledge["status"] == "complete_accepted"
    assert knowledge["verdict"] == "CANONICAL_KNOWLEDGE_CONTRACT_V1_ACCEPTED"
    assert knowledge["schema_version"] == "1.0.0"
    assert knowledge["issue"] == 64
    assert knowledge["pull_request"] == 86


def test_audit_r5_is_active_and_later_work_remains_blocked():
    state = _state()
    control = state["control_plane"]
    assert state["current_milestone"] == "audit_r5_integrity_documentation_and_issue_template_sync"
    assert state["current_stage"] == "audit_r5_integrity_docs_and_templates"
    assert state["next_actions"] == ["audit_r5_product_owner_review"]
    assert control["current_milestone_id"] == "audit_r5_integrity_documentation_and_issue_template_sync"
    assert control["last_completed_milestone_id"] == "audit_r4_mandatory_ci_and_main_protection"
    assert control["next_eligible_milestone_id"] is None
    assert control["next_issue_allowed"] is False
    assert control["authorization_states"]["audit_r4"] == "AUTHORIZED_IMPLEMENTATION"
    assert control["authorization_states"]["audit_r5"] == "AUTHORIZED_IMPLEMENTATION"


def test_near_term_sequence_has_no_completed_gate_marked_pending():
    state = _state()
    by_milestone = {item["milestone"]: item["status"] for item in state["near_term_execution_sequence"]}
    assert by_milestone["freeze_topic_engine_candidate"] == "complete"
    assert by_milestone["parallel_obsidian_product_review_and_treeseg_hierarchy_poc_product_review"] == "complete_product_reviewed"
    assert by_milestone["canonical_knowledge_contract_v1"] == "complete_accepted"
    assert by_milestone["audit_r1_governance_truth_reconciliation"] == "complete_accepted"
    assert by_milestone["audit_r2_canonical_knowledge_validation"] == "complete_accepted"
    assert by_milestone["audit_r3_control_plane_integrity_gate"] == "complete_accepted"
    assert by_milestone["audit_r4_mandatory_ci_and_main_protection"] == "complete_accepted"
    assert by_milestone["audit_r5_integrity_documentation_and_issue_template_sync"] == "implemented_pending_product_owner_review"


def test_roadmap_mirrors_state_current_status_and_not_stale_review_labels():
    state = _state()
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    assert "AUDIT-R5 IMPLEMENTED — PRODUCT OWNER REVIEW PENDING" in roadmap
    assert '"current_milestone_id": "audit_r5_integrity_documentation_and_issue_template_sync"' in roadmap
    assert '"last_completed_milestone_id": "audit_r4_mandatory_ci_and_main_protection"' in roadmap
    assert '"next_eligible_milestone_id": null' in roadmap
    assert "KEEP_TREESEG_AS_CHALLENGER" in roadmap
    assert "ADAPT_FURTHER" in roadmap
    assert "Canonical Knowledge Contract v1" in roadmap
    assert "SAFE_TO_CLOSE: YES" in roadmap
    assert "#69 — `SAFE_TO_CLOSE: NO`" in roadmap
    assert state["roadmap_state_consistency"]["checkpoint"] == "evidence_first_parallel_v1"
    assert "OBSIDIAN KNOWLEDGE PROTOTYPE READY FOR PRODUCT REVIEW" not in roadmap
    assert "TREESEG HIERARCHY POC READY FOR PRODUCT REVIEW / PARALLEL" not in roadmap


def test_integrity_document_describes_implemented_g4():
    text = (ROOT / "integrity" / "README.md").read_text(encoding="utf-8")
    assert "implemented G4 Dependency Truth" in text
    assert "G4, G5, and G6 are explicitly" not in text
