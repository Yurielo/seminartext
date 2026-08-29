import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from seminartext_modules import dataset_governance as governance


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
REGISTRY = ROOT / "governance" / "dataset_registry.json"


@pytest.mark.parametrize(
    ("dataset_id", "operation", "allowed"),
    [
        ("A", "tuning", True),
        ("B", "experiment_run", True),
        ("C", "gold_read", True),
        ("C", "tuning", False),
        ("C", "benchmark_run", False),
        ("D", "source_prepare", True),
        ("D", "prediction_read", False),
        ("D", "benchmark_run", False),
        ("E", "historical_artifact_read", True),
        ("E", "gold_author", False),
        ("E", "experiment_run", False),
        ("F", "source_prepare", True),
        ("F", "benchmark_run", False),
        ("G1", "source_prepare", True),
        ("G1", "gold_author", False),
        ("G2", "prediction_read", False),
    ],
)
def test_policy_matrix(dataset_id, operation, allowed):
    decision = governance.evaluate(operation, dataset_id=dataset_id)
    assert decision.allowed is allowed


def test_registry_has_complete_truthful_dataset_matrix():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in data["datasets"]}

    assert governance.validate_registry() == []
    assert list(by_id) == ["A", "B", "C", "D", "E", "F", "G1", "G2"]
    assert by_id["A"]["role"] == "DEVELOPMENT_CALIBRATION"
    assert by_id["B"]["role"] == "DEVELOPMENT_ERROR_ANALYSIS_HISTORY"
    assert by_id["C"]["lock_status"] == "CLOSED_FROZEN"
    assert by_id["D"]["role"] == "LOCKED_TEST"
    assert by_id["D"]["media_sha256"] is None
    assert by_id["D"]["identity_status"].startswith("INCOMPLETE_PENDING")
    assert by_id["E"]["role"] == "EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE"
    assert by_id["F"]["lock_status"] == "QUARANTINED"
    assert all(by_id[item]["role_status"].startswith("PROPOSAL_PENDING") for item in ("G1", "G2"))


def test_registry_matches_governing_state_roles_and_locks():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in registry["datasets"]}
    state = json.loads((ROOT / "SEMINARTEXT_4_STATE.json").read_text(encoding="utf-8"))
    stages = state["stages"]

    assert by_id["A"]["role"] == stages["topic_benchmark_dataset_a"]["role"]
    assert by_id["B"]["role"] == stages["dataset_b"]["role"]
    assert by_id["C"]["role"] == stages["dataset_c"]["role"]
    assert by_id["D"]["role"] == stages["dataset_d"]["role"]
    assert by_id["D"]["identity_status"] == stages["dataset_d"]["identity_status"]
    assert by_id["E"]["role"] == stages["dataset_e"]["status"]
    assert by_id["F"]["role"] == stages["dataset_f"]["role"]
    governance_state = stages["dataset_governance"]
    assert governance_state["registry"] == "governance/dataset_registry.json"
    assert governance_state["default_policy"] == "DENY_UNREGISTERED"


def test_unregistered_project_fails_closed():
    decision = governance.evaluate("benchmark_run", project="Unknown Seminar")
    assert not decision.allowed
    assert decision.dataset_id is None
    assert "unregistered" in decision.reason


def test_frozen_benchmark_hash_binds_experiment_entrypoint(tmp_path):
    fake = tmp_path / "topic_benchmark.json"
    fake.write_text('{"dataset_id": "A"}\n', encoding="utf-8")
    with pytest.raises(governance.DatasetPolicyError, match="identity mismatch"):
        governance.enforce_benchmark_artifact(
            "experiment_run", dataset_id="A", benchmark_path=fake
        )


def test_known_benchmark_and_experiment_entrypoints_use_central_guard():
    cli = CLI.read_text(encoding="utf-8")
    assert 'dataset_guard_benchmark "$project_dir" "$benchmark" benchmark_run' in cli
    assert cli.count('dataset_guard_benchmark "$project_dir" "$benchmark" gold_read') == 2
    for operation in ("gold_author", "benchmark_init"):
        assert f'dataset_guard_project "$project_dir" {operation}' in cli

    guarded_scripts = {
        "analysis/experiments/bge_m3_changepoint_topic_engine.py": "enforce_benchmark_artifact",
        "analysis/experiments/bge_m3_ruptures_topic_engine.py": "enforce_benchmark_artifact",
        "analysis/experiments/sliding_subwindow_topic_engine.py": "enforce_benchmark_artifact",
        "analysis/external_topic_baselines/run_baseline_challenge.py": "enforce_benchmark_artifact",
        "analysis/local_peak_raw_signal_observer.py": "enforce_benchmark_artifact",
        "analysis/prepare_dataset_b_candidates.py": 'enforce("benchmark_init", dataset_id="B")',
        "analysis/prepare_dataset_c_candidates.py": 'enforce("benchmark_init", dataset_id="C")',
    }
    for relative, marker in guarded_scripts.items():
        assert marker in (ROOT / relative).read_text(encoding="utf-8"), relative


def test_cli_denies_locked_or_excluded_project_before_benchmark_access(tmp_path):
    for project_name, expected_role in (
        ("Человек. Инструкция по применению", "LOCKED_TEST"),
        ("Нумеролог", "EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE"),
    ):
        project = tmp_path / project_name
        project.mkdir()
        result = subprocess.run(
            [str(CLI), "project-topic-benchmark-run", project_name],
            env={
                **os.environ,
                "SEMINARTEXT_PROJECTS": str(tmp_path),
                "SEMINARTEXT_PYTHON": sys.executable,
                "SEMINARTEXT_DATASET_REGISTRY": str(REGISTRY),
            },
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 3
        assert "DATASET GOVERNANCE: DENY" in result.stderr
        assert expected_role in result.stderr
        assert "benchmark не найден" not in result.stderr


def test_dataset_policy_cli_reports_pending_g2_denial():
    result = subprocess.run(
        [
            str(CLI),
            "dataset-policy-check",
            "G2",
            "prediction_read",
            "--json",
        ],
        env={**os.environ, "SEMINARTEXT_PYTHON": sys.executable},
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 3
    payload = json.loads(result.stdout)
    assert payload["dataset_id"] == "G2"
    assert payload["allowed"] is False
