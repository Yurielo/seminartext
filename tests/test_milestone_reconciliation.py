import copy
import json
import shutil
import sys
from pathlib import Path

from integrity.checks import governance_truth, product_state
from integrity.checks.control_plane import (
    ROADMAP_END,
    ROADMAP_START,
    _projection,
    evaluate,
)
from integrity.runner import default_context, load_contract, render_human, run_integrity


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "integrity" / "milestone_reconciliation.json"


def _write_json(path: Path, document):
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_contract(root: Path):
    return json.loads((root / "integrity" / "milestone_reconciliation.json").read_text())


def _write_roadmap_projection(root: Path, projection):
    path = root / "SEMINARTEXT_4_ROADMAP.md"
    text = path.read_text(encoding="utf-8")
    prefix, tail = text.split(ROADMAP_START, 1)
    _, suffix = tail.split(ROADMAP_END, 1)
    payload = json.dumps(projection, ensure_ascii=False, indent=2)
    path.write_text(
        f"{prefix}{ROADMAP_START}\n```json\n{payload}\n```\n{ROADMAP_END}{suffix}",
        encoding="utf-8",
    )


def _synchronize_projections(root: Path, contract):
    milestones = {item["milestone_id"]: item for item in contract["milestones"]}
    projection = _projection(contract, milestones)
    state_path = root / "SEMINARTEXT_4_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["control_plane"] = copy.deepcopy(projection)
    state["current_milestone"] = contract["current_milestone_id"]
    state["current_stage"] = contract["state_current_stage"]
    state["next_actions"] = contract["active_actions"]
    sequence = {item["milestone"]: item for item in state["near_term_execution_sequence"]}
    for milestone_id, milestone in milestones.items():
        sequence[milestone_id]["status"] = milestone["state_sequence_status"]
    _write_json(state_path, state)
    _write_roadmap_projection(root, projection)


def _fixture(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    relative_paths = {
        "SEMINARTEXT_4_STATE.json",
        "SEMINARTEXT_4_ROADMAP.md",
        "SEMINARTEXT_VERSION",
        "SEMINARTEXT_4_MVP_DEFINITION.md",
        "DEVELOPMENT_WORKFLOW.md",
        "seminartext",
        "scripts/check_governance.py",
        "integrity/milestone_reconciliation.json",
    }
    relative_paths.update(
        spec["path"] for spec in contract["authoritative_sources"].values()
    )
    relative_paths.update(contract["historical_evidence"])
    for relative in sorted(relative_paths):
        source = ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return root


def _has(result, gate, code):
    errors = result.g3_errors if gate == "G3" else result.g8_errors
    return any(error.startswith(code + ":") for error in errors)


def test_current_real_seminartext_control_plane_is_truthful_and_offline():
    result = evaluate(ROOT)
    assert result.control_plane_reconciled is True
    assert result.next_issue_allowed is False
    assert result.github_lifecycle_check == "NOT_RUN"
    assert result.human_gate == "PRODUCT_OWNER_REVIEW_PENDING"


def test_accepted_decision_with_stale_state_fails_closed(tmp_path):
    root = _fixture(tmp_path)
    state_path = root / "SEMINARTEXT_4_STATE.json"
    state = json.loads(state_path.read_text())
    state["control_plane"]["milestones"]["audit_r1_governance_truth_reconciliation"][
        "status"
    ] = "READY_FOR_PRODUCT_REVIEW"
    _write_json(state_path, state)
    result = evaluate(root)
    assert _has(result, "G3", "CP_STALE_STATE")
    assert result.next_issue_allowed is False


def test_accepted_decision_cannot_remain_pending(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    r1 = next(
        item
        for item in contract["milestones"]
        if item["milestone_id"] == "audit_r1_governance_truth_reconciliation"
    )
    r1["status"] = "READY_FOR_PRODUCT_REVIEW"
    r1["human_gate"] = "PRODUCT_OWNER_REVIEW_PENDING"
    _write_json(path, contract)
    result = evaluate(root)
    assert _has(result, "G3", "CP_ACCEPTED_PENDING")
    assert result.next_issue_allowed is False


def test_stale_roadmap_snapshot_fails_closed(tmp_path):
    root = _fixture(tmp_path)
    contract = _read_contract(root)
    milestones = {item["milestone_id"]: item for item in contract["milestones"]}
    projection = _projection(contract, milestones)
    projection["current_milestone_id"] = "audit_r1_governance_truth_reconciliation"
    _write_roadmap_projection(root, projection)
    result = evaluate(root)
    assert _has(result, "G8", "CP_STALE_ROADMAP")


def test_completed_milestone_cannot_remain_current(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    contract["current_milestone_id"] = "audit_r2_canonical_knowledge_validation"
    _write_json(path, contract)
    result = evaluate(root)
    assert _has(result, "G8", "CP_COMPLETED_STILL_CURRENT")


def test_pending_human_gate_blocks_next_issue(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    contract["next_issue_allowed"] = True
    _write_json(path, contract)
    result = evaluate(root)
    assert _has(result, "G8", "CP_HUMAN_GATE_BYPASS")
    assert result.next_issue_allowed is False


def test_blocked_dataset_cannot_be_exposed_as_next_action(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    current = next(
        item
        for item in contract["milestones"]
        if item["milestone_id"] == contract["current_milestone_id"]
    )
    current["next_allowed_actions"] = ["dataset_d_blind_evaluation"]
    _write_json(path, contract)
    result = evaluate(root)
    assert _has(result, "G8", "CP_BLOCKED_ACTION_EXECUTABLE")


def test_runtime_reconciliation_pending_blocks_next_issue(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    current = next(
        item
        for item in contract["milestones"]
        if item["milestone_id"] == contract["current_milestone_id"]
    )
    current["human_gate"] = "SATISFIED"
    contract["next_issue_allowed"] = True
    _write_json(path, contract)
    result = evaluate(root)
    assert _has(result, "G8", "CP_RUNTIME_RECONCILIATION_BYPASS")


def test_runtime_reconciliation_not_required_is_valid(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    current = next(
        item
        for item in contract["milestones"]
        if item["milestone_id"] == contract["current_milestone_id"]
    )
    current["runtime_reconciliation_required"] = False
    current["runtime_reconciliation_complete"] = True
    _write_json(path, contract)
    _synchronize_projections(root, contract)
    assert evaluate(root).control_plane_reconciled is True


def test_runtime_reconciliation_completed_is_valid(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    current = next(
        item
        for item in contract["milestones"]
        if item["milestone_id"] == contract["current_milestone_id"]
    )
    current["runtime_reconciliation_complete"] = True
    _write_json(path, contract)
    _synchronize_projections(root, contract)
    assert evaluate(root).control_plane_reconciled is True


def test_contradictory_treeseg_disposition_fails(tmp_path):
    root = _fixture(tmp_path)
    path = root / "governance" / "topic_engine_lifecycle.json"
    lifecycle = json.loads(path.read_text())
    lifecycle["treeseg_product_review"]["production_ready"] = True
    _write_json(path, lifecycle)
    result = evaluate(root)
    assert any("treeseg_production_ready" in error for error in result.g3_errors)


def test_freeze_complete_but_marked_pending_fails(tmp_path):
    root = _fixture(tmp_path)
    path = root / "governance" / "topic_engine_freeze.json"
    freeze = json.loads(path.read_text())
    freeze["status"] = "PENDING"
    _write_json(path, freeze)
    result = evaluate(root)
    assert any("local_peak_freeze_complete" in error for error in result.g3_errors)


def test_canonical_knowledge_accepted_but_undefined_fails(tmp_path):
    root = _fixture(tmp_path)
    path = root / "SEMINARTEXT_4_STATE.json"
    state = json.loads(path.read_text())
    state["stages"]["canonical_knowledge_v1"]["status"] = "contract_not_defined"
    _write_json(path, state)
    result = evaluate(root)
    assert any(
        "canonical_knowledge_contract_accepted" in error for error in result.g3_errors
    )


def test_incomplete_prerequisite_blocks_current_milestone(tmp_path):
    root = _fixture(tmp_path)
    path = root / "integrity" / "milestone_reconciliation.json"
    contract = _read_contract(root)
    r2 = next(
        item
        for item in contract["milestones"]
        if item["milestone_id"] == "audit_r2_canonical_knowledge_validation"
    )
    r2["accepted"] = False
    r2["implementation_state"] = "IN_PROGRESS"
    _write_json(path, contract)
    result = evaluate(root)
    assert _has(result, "G8", "CP_SEQUENCE_VIOLATION")


def test_historical_stale_wording_is_not_active_truth(tmp_path):
    root = _fixture(tmp_path)
    path = root / "analysis" / "ROADMAP_STATE_CONSISTENCY_REVIEW_2026-08-26.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nready_for_product_review pending candidate_freeze_pending\n",
        encoding="utf-8",
    )
    assert evaluate(root).control_plane_reconciled is True


def test_g3_and_g8_use_same_reconciled_offline_verdict(tmp_path):
    contract = load_contract(ROOT)
    context = default_context(ROOT, tmp_path / "unused-deploy", contract)
    g3 = governance_truth.run(context)
    g8 = product_state.run(context)
    assert g3.status == "PASS"
    assert g8.status == "PASS"
    assert g3.evidence["control_plane"]["control_plane_reconciled"] is True
    assert g8.evidence["control_plane"]["next_issue_allowed"] is False


def test_json_and_human_reports_expose_progression_verdict(tmp_path):
    contract = load_contract(ROOT)
    context = default_context(ROOT, tmp_path / "missing-deploy", contract)
    context = type(context)(
        root=context.root,
        deploy_dir=context.deploy_dir,
        contract=context.contract,
        test_command=(sys.executable, "-c", "print('1 passed in 0.01s')"),
        governance_command=context.governance_command,
    )
    report, _ = run_integrity(context)
    human = render_human(report)
    assert report["control_plane_reconciled"] is True
    assert report["next_issue_allowed"] is False
    assert "CONTROL_PLANE_RECONCILED: YES" in human
    assert "NEXT_ISSUE_ALLOWED: NO" in human
    assert "HUMAN_GATE: PRODUCT_OWNER_REVIEW_PENDING" in human
