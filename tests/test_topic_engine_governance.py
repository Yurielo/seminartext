#!/usr/bin/env python3
import copy
import hashlib
import json
from pathlib import Path

from seminartext_modules import dataset_governance
from seminartext_modules import topic_engine_governance as governance


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_lifecycle_is_complete_and_unambiguous():
    assert governance.validate_lifecycle() == []
    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    by_role = {item["role_id"]: item for item in lifecycle["engines"]}
    assert set(by_role) == governance.REQUIRED_ROLES
    assert by_role["production_legacy"]["engine_id"] == "legacy_ollama_gemma_runtime"
    assert by_role["production_legacy"]["production_runtime"] is True
    assert by_role["experimental_primary"]["engine_id"] == "bge_m3_local_peak_v1"
    assert by_role["comparator"]["engine_id"] == "bge_m3_pelt_v1"
    assert by_role["challenger"]["engine_id"] == "treeseg_external_adapt_v1"
    assert by_role["frozen_candidate"]["engine_id"] is None
    assert lifecycle["benchmark_segment_semantics"]["semantic_topic_output"] is False


def test_new_custom_family_is_rejected(tmp_path):
    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    lifecycle["engines"].append(
        {"engine_id": "unauthorized", "role_id": "new_family", "production_runtime": False}
    )
    path = tmp_path / "lifecycle.json"
    write_json(path, lifecycle)
    assert governance.validate_lifecycle(path)


def test_pending_freeze_blocks_dataset_d():
    gate = governance.freeze_gate()
    assert gate["status"] == "BLOCKED"
    assert gate["dataset_d_open_allowed"] is False
    assert not all(gate["checks"].values())


def approved_fixture(tmp_path: Path) -> tuple[Path, Path]:
    criteria = tmp_path / "criteria.md"
    plan = tmp_path / "plan.md"
    criteria.write_text("frozen criteria\n", encoding="utf-8")
    plan.write_text("frozen plan\n", encoding="utf-8")
    config = {"engine_id": "bge_m3_local_peak_v1", "threshold": 1.15}
    freeze = {
        "schema_version": 1,
        "status": "FROZEN_APPROVED",
        "product_owner_decision": "APPROVE_CANDIDATE_FREEZE",
        "candidate": {"engine_id": "bge_m3_local_peak_v1", "frozen": True},
        "configuration": {
            "value": config,
            "sha256": governance._canonical_sha256(config),
            "frozen": True,
        },
        "acceptance_criteria": {
            "artifact": str(criteria),
            "sha256": hashlib.sha256(criteria.read_bytes()).hexdigest(),
            "frozen": True,
        },
        "analysis_plan": {
            "artifact": str(plan),
            "sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
            "frozen": True,
        },
        "dataset_d": {"single_blind_run_authorized": True},
    }
    datasets = json.loads(governance.DEFAULT_DATASETS.read_text(encoding="utf-8"))
    dataset_d = next(item for item in datasets["datasets"] if item["id"] == "D")
    dataset_d["source_identity_recorded"] = True
    dataset_d["source_quality"] = "SUFFICIENT"
    freeze_path = tmp_path / "freeze.json"
    datasets_path = tmp_path / "datasets.json"
    write_json(freeze_path, freeze)
    write_json(datasets_path, datasets)
    return freeze_path, datasets_path


def test_gate_requires_every_frozen_input_and_dataset_d_authority(tmp_path):
    freeze_path, datasets_path = approved_fixture(tmp_path)
    passed = governance.freeze_gate(freeze_path, datasets_path)
    assert passed["status"] == "PASS"

    base = json.loads(freeze_path.read_text(encoding="utf-8"))
    mutations = [
        lambda x: x.update(product_owner_decision=None),
        lambda x: x["candidate"].update(frozen=False),
        lambda x: x["candidate"].update(engine_id="unknown_engine"),
        lambda x: x["configuration"].update(sha256="0" * 64),
        lambda x: x["acceptance_criteria"].update(frozen=False),
        lambda x: x["analysis_plan"].update(sha256="0" * 64),
        lambda x: x["dataset_d"].update(single_blind_run_authorized=False),
    ]
    for index, mutate in enumerate(mutations):
        candidate = copy.deepcopy(base)
        mutate(candidate)
        path = tmp_path / f"freeze-{index}.json"
        write_json(path, candidate)
        assert governance.freeze_gate(path, datasets_path)["status"] == "BLOCKED"


def test_dataset_c_and_e_remain_fail_closed():
    assert dataset_governance.evaluate("tuning", dataset_id="C").allowed is False
    assert dataset_governance.evaluate("experiment_run", dataset_id="E").allowed is False
    assert dataset_governance.evaluate("benchmark_run", dataset_id="D").allowed is False
