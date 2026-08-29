#!/usr/bin/env python3
import copy
import json
import shutil
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
    assert by_role["frozen_candidate"]["engine_id"] == "bge_m3_local_peak_v1"
    assert by_role["frozen_candidate"]["production_promoted"] is False
    assert lifecycle["benchmark_segment_semantics"]["semantic_topic_output"] is False


def test_new_custom_family_is_rejected(tmp_path):
    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    lifecycle["engines"].append(
        {"engine_id": "unauthorized", "role_id": "new_family", "production_runtime": False}
    )
    path = tmp_path / "lifecycle.json"
    write_json(path, lifecycle)
    assert governance.validate_lifecycle(path)


def test_approved_candidate_freeze_does_not_open_dataset_d():
    gate = governance.freeze_gate()
    assert gate["status"] == "PASS"
    assert gate["topic_candidate_freeze"] == "COMPLETE"
    assert gate["dataset_d_access"] == "BLOCKED"
    assert gate["dataset_d_open_allowed"] is False
    assert all(gate["checks"].values())
    assert gate["dataset_d_checks"]["dataset_d_prediction_access_denied"] is True
    assert gate["dataset_d_checks"]["single_blind_run_authorized"] is False


def approved_fixture(tmp_path: Path) -> tuple[Path, Path]:
    freeze = json.loads(governance.DEFAULT_FREEZE.read_text(encoding="utf-8"))
    datasets = json.loads(governance.DEFAULT_DATASETS.read_text(encoding="utf-8"))
    dataset_d = next(item for item in datasets["datasets"] if item["id"] == "D")
    dataset_d["source_identity_recorded"] = True
    dataset_d["source_quality"] = "SUFFICIENT"
    freeze_path = tmp_path / "freeze.json"
    datasets_path = tmp_path / "datasets.json"
    write_json(freeze_path, freeze)
    write_json(datasets_path, datasets)
    return freeze_path, datasets_path


def test_gate_requires_every_frozen_candidate_input(tmp_path):
    freeze_path, datasets_path = approved_fixture(tmp_path)
    passed = governance.freeze_gate(freeze_path, datasets_path)
    assert passed["status"] == "PASS"

    base = json.loads(freeze_path.read_text(encoding="utf-8"))
    mutations = [
        lambda x: x.update(product_owner_decision=None),
        lambda x: x.update(product_owner_disposition=None),
        lambda x: x["candidate"].update(frozen=False),
        lambda x: x["candidate"].update(engine_id="unknown_engine"),
        lambda x: x["configuration"]["value"].update(implementation_sha256="0" * 64),
        lambda x: x["configuration"].update(sha256="0" * 64),
        lambda x: x["acceptance_criteria"].update(frozen=False),
        lambda x: x["analysis_plan"].update(sha256="0" * 64),
    ]
    for index, mutate in enumerate(mutations):
        candidate = copy.deepcopy(base)
        mutate(candidate)
        path = tmp_path / f"freeze-{index}.json"
        write_json(path, candidate)
        assert governance.freeze_gate(path, datasets_path)["status"] == "BLOCKED"


def test_other_dataset_d_prerequisites_do_not_bypass_registry_denial(tmp_path):
    freeze_path, datasets_path = approved_fixture(tmp_path)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["dataset_d"]["single_blind_run_authorized"] = True
    freeze["dataset_d"]["open_allowed"] = True
    write_json(freeze_path, freeze)
    gate = governance.freeze_gate(freeze_path, datasets_path)
    assert gate["topic_candidate_freeze"] == "COMPLETE"
    assert gate["dataset_d_checks"]["dataset_d_source_identity_recorded"] is True
    assert gate["dataset_d_checks"]["dataset_d_source_quality_accepted"] is True
    assert gate["dataset_d_open_allowed"] is False


def test_dataset_c_and_e_remain_fail_closed():
    assert dataset_governance.evaluate("tuning", dataset_id="C").allowed is False
    assert dataset_governance.evaluate("experiment_run", dataset_id="E").allowed is False
    assert dataset_governance.evaluate("benchmark_run", dataset_id="D").allowed is False


def test_active_missing_and_hash_mismatch_are_rejected(tmp_path):
    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    lifecycle["engines"][1]["implementation"]["path"] = "missing/authoritative.py"
    missing = tmp_path / "missing.json"
    write_json(missing, lifecycle)
    assert governance.validate_lifecycle(missing)

    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    lifecycle["engines"][1]["implementation"]["sha256"] = "0" * 64
    mismatch = tmp_path / "mismatch.json"
    write_json(mismatch, lifecycle)
    assert governance.validate_lifecycle(mismatch)


def test_candidate_binding_and_hash_are_required(tmp_path):
    freeze = json.loads(governance.DEFAULT_FREEZE.read_text(encoding="utf-8"))
    freeze["candidate"]["implementation_binding"]["path"] = "other.py"
    path = tmp_path / "candidate-path.json"
    write_json(path, freeze)
    assert governance.freeze_gate(path)["topic_candidate_freeze"] == "INCOMPLETE"

    freeze = json.loads(governance.DEFAULT_FREEZE.read_text(encoding="utf-8"))
    freeze["candidate"]["implementation_binding"]["sha256"] = None
    path = tmp_path / "candidate-hash.json"
    write_json(path, freeze)
    assert governance.freeze_gate(path)["topic_candidate_freeze"] == "INCOMPLETE"


def test_historical_and_external_pinned_provenance_are_valid(tmp_path):
    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    historical = {item["engine_id"]: item for item in lifecycle["historical_implementations"]}
    assert historical["external_chonkie_baseline"]["provenance_state"] == "NON_EXECUTABLE_HISTORICAL_RECORD"
    assert historical["external_texttiling_baseline"]["provenance_state"] == "NON_EXECUTABLE_HISTORICAL_RECORD"
    assert historical["external_chonkie_baseline"]["external"]["commit"]
    assert governance.validate_lifecycle() == []

    broken = copy.deepcopy(lifecycle)
    broken["historical_implementations"][1].pop("provenance_artifacts")
    path = Path(tmp_path) / "temporary_topic_lifecycle.json"
    write_json(path, broken)
    assert governance.validate_lifecycle(path)


def test_deployed_attestation_matches_repository_validation(tmp_path):
    deploy = tmp_path / "bin"
    (deploy / "governance").mkdir(parents=True)
    (deploy / "seminartext_modules").mkdir()
    lifecycle_path = deploy / "governance" / "topic_engine_lifecycle.json"
    freeze_path = deploy / "governance" / "topic_engine_freeze.json"
    shutil.copy2(governance.DEFAULT_LIFECYCLE, lifecycle_path)
    shutil.copy2(governance.DEFAULT_FREEZE, freeze_path)
    shutil.copy2(ROOT / "seminartext_modules" / "seminartext_topics.py", deploy / "seminartext_topics.py")
    datasets_path = deploy / "governance" / "dataset_registry.json"
    shutil.copy2(governance.DEFAULT_DATASETS, datasets_path)
    assert governance.validate_lifecycle(lifecycle_path, deployed=True) == []
    result = governance.freeze_gate(freeze_path, datasets_path, lifecycle_path, deployed=True)
    assert result["topic_candidate_freeze"] == "COMPLETE"
    assert result["dataset_d_access"] == "BLOCKED"


def test_personal_absolute_paths_are_rejected(tmp_path):
    lifecycle = json.loads(governance.DEFAULT_LIFECYCLE.read_text(encoding="utf-8"))
    lifecycle["engines"][1]["implementation"]["path"] = "/Users/example/private.py"
    path = tmp_path / "absolute.json"
    write_json(path, lifecycle)
    assert any("absolute personal path" in error for error in governance.validate_lifecycle(path))
