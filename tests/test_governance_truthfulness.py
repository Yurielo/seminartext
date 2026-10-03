import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
STATE = ROOT / "SEMINARTEXT_4_STATE.json"
ROADMAP = ROOT / "SEMINARTEXT_4_ROADMAP.md"
VERSION = ROOT / "SEMINARTEXT_VERSION"
WORKFLOW = ROOT / "DEVELOPMENT_WORKFLOW.md"
MVP = ROOT / "SEMINARTEXT_4_MVP_DEFINITION.md"
GOVERNANCE_CHECK = ROOT / "scripts" / "check_governance.py"
DEV_CLI = ROOT / "scripts" / "seminartext-dev"
DATASET_REGISTRY = ROOT / "governance" / "dataset_registry.json"


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cli(*args, env=None, cli=CLI, cwd=ROOT):
    command_env = os.environ.copy()
    if env:
        command_env.update({key: str(value) for key, value in env.items()})
    return subprocess.run(
        [str(cli), *args],
        cwd=cwd,
        env=command_env,
        text=True,
        capture_output=True,
        check=False,
    )


def write_benchmark(project: Path):
    cases = []
    for index in range(1, 7):
        first = index * 10
        cases.append(
            {
                "case_id": f"case_{index}",
                "segments": [
                    {
                        "id": first,
                        "start": "00:00:00,000",
                        "end": "00:00:01,000",
                        "text": "segment",
                    }
                ],
                "gold": {
                    "boundaries": [first],
                    "topics": [
                        {"start_id": first, "title": f"Topic {index}", "summary": ""}
                    ],
                },
                "review": {"status": "gold_complete"},
            }
        )
    target = project / "analysis" / "benchmark" / "topic_benchmark.json"
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps({"schema_version": 1, "cases": cases}, ensure_ascii=False),
        encoding="utf-8",
    )


def write_test_dataset_registry(path: Path, project_name: str, benchmark: Path) -> Path:
    registry = json.loads(DATASET_REGISTRY.read_text(encoding="utf-8"))
    dataset_a = next(item for item in registry["datasets"] if item["id"] == "A")
    dataset_a["project"] = project_name
    dataset_a["benchmark_sha256"] = sha256(benchmark)
    path.write_text(json.dumps(registry), encoding="utf-8")
    return path


def test_authoritative_version_is_used_by_cli_help_state_and_diagnostics():
    expected = VERSION.read_text(encoding="utf-8").strip()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    version = run_cli("--version")
    help_result = run_cli("help")
    identity = run_cli("runtime-identity")

    assert version.returncode == 0
    assert version.stdout.strip() == f"seminartext {expected}"
    assert help_result.stdout.startswith(f"SEMINARTEXT {expected}\n")
    assert f"version={expected}" in identity.stdout
    assert state["seminartext_version"] == expected


def test_every_dispatched_user_command_is_discoverable_in_main_help():
    source = CLI.read_text(encoding="utf-8")
    main_dispatch = source[source.index("main() {") :]
    commands = set(
        re.findall(r"^    ([a-z][a-z0-9-]*)\)$", main_dispatch, flags=re.MULTILINE)
    )
    help_text = run_cli("help").stdout
    assert commands
    assert commands == {
        "clean",
        "cut",
        "dataset-policy-check",
        "doctor",
        "help",
        "init",
            "project-add",
            "project-align",
            "project-check",
            "project-corpus",
            "project-documents",
            "project-evidence-check",
                "project-link-youtube",
                "project-obsidian-export",
                "project-promote-transcript",
                "project-review-apply",
                "project-review-boundary-prepare",
                "project-review-boundary-resolve",
                "project-review-boundary-status",
                "project-review-prepare",
                "project-review-status",
                "project-review-v2-apply",
                "project-review-v2-status",
        "project-topic-benchmark-check",
        "project-topic-benchmark-init",
        "project-topic-benchmark-label",
        "project-topic-benchmark-run",
        "project-topic-benchmark-show",
        "project-topics",
        "project-transcribe",
        "roadmap-status",
        "runtime-identity",
        "subtitles",
        "topics",
        "transcribe",
        "translate",
    }
    assert all(f"seminartext {command}" in help_text for command in commands)


def test_roadmap_status_renders_current_state_generically(tmp_path):
    result = run_cli("roadmap-status", env={"SEMINARTEXT_DEPLOY_DIR": tmp_path})
    assert result.returncode == 0, result.stderr
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert f"Stage: {state['current_stage']}" in result.stdout
    assert f"Milestone: {state['current_milestone']}" in result.stdout
    for action in state["next_actions"]:
        assert action in result.stdout
    for name, track in state["architecture"]["tracks"].items():
        assert name in result.stdout
        assert track["status"] in result.stdout
    assert "After TOPIC SEGMENTATION STABLE" not in result.stdout
    assert "DATASET B — NEXT CRITICAL STEP" not in result.stdout


def test_roadmap_status_detects_stale_deployed_snapshot(tmp_path):
    deployed = tmp_path / "deployed"
    deployed.mkdir()
    stale_state = json.loads(STATE.read_text(encoding="utf-8"))
    stale_state["updated"] = "stale-fixture"
    (deployed / STATE.name).write_text(
        json.dumps(stale_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(ROADMAP, deployed / ROADMAP.name)

    result = run_cli(
        "roadmap-status", env={"SEMINARTEXT_DEPLOY_DIR": deployed}
    )
    assert result.returncode == 0, result.stderr
    assert "State: STALE" in result.stdout
    assert "Roadmap: SYNC" in result.stdout


def test_installed_snapshot_is_resolved_but_never_claimed_current(tmp_path):
    installed_cli = tmp_path / "seminartext"
    shutil.copy2(CLI, installed_cli)
    (tmp_path / "seminartext_modules").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "seminartext_modules/owned_tmp.py", tmp_path / "seminartext_modules/owned_tmp.py")
    shutil.copy2(VERSION, tmp_path / VERSION.name)
    shutil.copy2(STATE, tmp_path / STATE.name)
    shutil.copy2(ROADMAP, tmp_path / ROADMAP.name)

    result = run_cli("roadmap-status", cli=installed_cli, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "STATE SOURCE CLASS: deployed_snapshot" in result.stdout
    assert "Repository freshness: UNVERIFIED" in result.stdout
    assert "SEMINARTEXT_REPO" in result.stdout


def test_benchmark_check_is_read_only_for_benchmark_and_governance(tmp_path):
    projects = tmp_path / "projects"
    project = projects / "Bench"
    write_benchmark(project)

    fake_home = tmp_path / "home"
    deployed_bin = fake_home / "bin"
    deployed_bin.mkdir(parents=True)
    shutil.copy2(STATE, deployed_bin / STATE.name)
    shutil.copy2(ROADMAP, deployed_bin / ROADMAP.name)
    test_registry = write_test_dataset_registry(
        tmp_path / "dataset_registry.json",
        "Bench",
        project / "analysis" / "benchmark" / "topic_benchmark.json",
    )

    guarded = [
        STATE,
        ROADMAP,
        project / "analysis" / "benchmark" / "topic_benchmark.json",
        deployed_bin / STATE.name,
        deployed_bin / ROADMAP.name,
    ]
    before = {path: sha256(path) for path in guarded}
    result = run_cli(
        "project-topic-benchmark-check",
        "Bench",
        env={
            "HOME": fake_home,
            "SEMINARTEXT_PROJECTS": projects,
            "SEMINARTEXT_PYTHON": sys.executable,
            "SEMINARTEXT_DATASET_REGISTRY": test_registry,
        },
    )
    after = {path: sha256(path) for path in guarded}

    assert result.returncode == 0, result.stderr
    assert "BENCHMARK INTEGRITY: OK" in result.stdout
    assert "READ-ONLY CHECK" in result.stdout
    assert "STATE UPDATED" not in result.stdout
    assert after == before


def test_governance_consistency_checker_and_maturity_contract_pass():
    result = subprocess.run(
        [sys.executable, str(GOVERNANCE_CHECK), "--root", str(ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "GOVERNANCE CHECK: PASS" in result.stdout

    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["product_mvp"]["definition"] == MVP.name
    assert state["product_mvp"]["status"] == "defined_not_yet_product_integrated"
    assert MVP.name in ROADMAP.read_text(encoding="utf-8")
    assert MVP.name in WORKFLOW.read_text(encoding="utf-8")


def test_documented_deploy_command_can_create_verified_isolated_snapshot(tmp_path):
    deploy_bin = tmp_path / "bin"
    backups = tmp_path / "backups"
    env = {
        **os.environ,
        "SEMINARTEXT_DEV_REPO": str(ROOT),
        "SEMINARTEXT_DEV_BIN": str(deploy_bin),
        "SEMINARTEXT_DEV_BACKUP_ROOT": str(backups),
    }
    deployed = subprocess.run(
        [str(DEV_CLI), "deploy"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert deployed.returncode == 0, deployed.stdout + deployed.stderr
    assert "DEPLOY: PASS" in deployed.stdout

    contract = json.loads(
        (ROOT / "integrity" / "integrity_contract.json").read_text(encoding="utf-8")
    )
    expected = {
        ROOT / item["repository_path"]: deploy_bin / item["deployed_name"]
        for item in contract["runtime_components"]
    }
    for source, snapshot in expected.items():
        assert snapshot.is_file()
        assert sha256(source) == sha256(snapshot)

    status = subprocess.run(
        [str(DEV_CLI), "status"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert status.returncode == 0, status.stderr
    assert "DEPLOY STATUS: SYNC" in status.stdout
