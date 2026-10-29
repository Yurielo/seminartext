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


def test_audit_r6_is_accepted_and_issue_68_is_the_only_active_product_work():
    state = _state()
    control = state["control_plane"]
    assert state["current_milestone"] == "issue_68_real_multi_source_vertical_slice"
    assert state["current_stage"] == "issue_68_real_multi_source_vertical_slice"
    assert state["next_actions"] == ["execute_issue_68_real_multi_source_vertical_slice"]
    assert control["current_milestone_id"] == "issue_68_real_multi_source_vertical_slice"
    assert control["last_completed_milestone_id"] == "autonomous_operating_model"
    assert control["next_eligible_milestone_id"] is None
    assert control["next_issue_allowed"] is False
    assert control["authorization_states"]["audit_r4"] == "NOT_AUTHORIZED"
    assert control["authorization_states"]["audit_r5"] == "NOT_AUTHORIZED"
    assert control["authorization_states"]["audit_r6"] == "NOT_AUTHORIZED"
    assert control["authorization_states"]["issue_68"] == "AUTHORIZED_IMPLEMENTATION"
    assert control["authorization_states"]["issue_113_cross_video_experiment"] == "NOT_AUTHORIZED"


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
    assert by_milestone["audit_r5_integrity_documentation_and_issue_template_sync"] == "complete_accepted"
    assert by_milestone["audit_r6_canonical_contract_truth"] == "complete_accepted"
    assert by_milestone["issue_104_product_bridge"] == "complete_accepted"
    assert by_milestone["issue_113_human_review_and_root_cause"] == "complete_accepted"
    assert by_milestone["autonomous_operating_model"] == "complete_accepted"
    assert by_milestone["issue_68_real_multi_source_vertical_slice"] == "in_progress"
    sequence = [item["milestone"] for item in state["near_term_execution_sequence"]]
    assert sequence.index("issue_68_real_multi_source_vertical_slice") < sequence.index("release_integration_readiness_audit")
    assert sequence.index("release_integration_readiness_audit") < sequence.index("s2_cross_seminar_knowledge_accumulation")
    assert sequence.index("s2_cross_seminar_knowledge_accumulation") < sequence.index("s3_integra_knowledge_navigation")
    assert sequence.index("s2_cross_seminar_knowledge_accumulation") < sequence.index("dataset_d_blind_evaluation")


def test_roadmap_mirrors_state_current_status_and_not_stale_review_labels():
    state = _state()
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    assert "AUDIT-R6" in roadmap
    assert '"current_milestone_id": "issue_68_real_multi_source_vertical_slice"' in roadmap
    assert '"last_completed_milestone_id": "autonomous_operating_model"' in roadmap
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
