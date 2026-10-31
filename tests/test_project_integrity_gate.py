import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from integrity.checks import (
    git_truth,
    governance_truth,
    product_state,
    runtime_truth,
    tests_truth,
)
from integrity.model import CheckContext
from integrity.runner import run_integrity


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "integrity" / "integrity_contract.json"
ENTRYPOINT = ROOT / "scripts" / "seminartext-integrity"


def run(command, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def file_hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }


def make_fixture(tmp_path):
    root = tmp_path / "repo"
    deploy = tmp_path / "deploy"
    root.mkdir()
    deploy.mkdir()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    cli = """#!/bin/bash
main() {
  case "${1:-}" in
    project-topic-benchmark-run)
      exit 0
      ;;
    project-evidence-check)
      exit 0
      ;;
    project-obsidian-export)
      exit 0
      ;;
    dataset-policy-check)
      exit 0
      ;;
  esac
}
main "$@"
"""
    state = {
        "schema_version": 3,
        "seminartext_version": "4.0.0",
        "product_mvp": {"status": "defined_not_yet_product_integrated"},
        "status_semantics": {
            "technical_evidence": "separate",
            "architecture_acceptance": "separate",
            "product_integration": "separate",
            "product_review": "separate",
            "production_stability": "separate",
        },
        "stages": {
            "topic_benchmark_runner": {
                "status": "complete",
                "command": "project-topic-benchmark-run",
            },
            "word_alignment": {
                "status": "complete_technology_selected",
                "production_integration_complete": False,
            },
        },
    }
    state = json.loads((ROOT / "SEMINARTEXT_4_STATE.json").read_text(encoding="utf-8"))
    source_content = {
        "seminartext": cli,
        "seminartext_modules/seminartext_topics.py": "# topics\n",
        "seminartext_modules/seminartext_translate.py": "# translate\n",
        "SEMINARTEXT_VERSION": "4.0.0\n",
        "SEMINARTEXT_4_STATE.json": json.dumps(state, indent=2) + "\n",
        "SEMINARTEXT_4_ROADMAP.md": (ROOT / "SEMINARTEXT_4_ROADMAP.md").read_text(
            encoding="utf-8"
        ),
        "DEVELOPMENT_WORKFLOW.md": "# Workflow\n",
        "SEMINARTEXT_4_MVP_DEFINITION.md": "# MVP\n",
        "scripts/check_governance.py": "print('GOVERNANCE CHECK: PASS')\n",
        "integrity/integrity_contract.json": json.dumps(contract, indent=2) + "\n",
    }
    for relative, content in source_content.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    for relative in (
        "dependencies/dependency_profiles.json",
        "requirements-core.txt",
        "requirements-dev.txt",
        "requirements-alignment.txt",
        "requirements-treeseg.txt",
    ):
        source = ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for lock in (ROOT / "dependencies" / "locks").glob("*.lock"):
        destination = root / "dependencies" / "locks" / lock.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(lock, destination)

    for relative in (
        "seminartext_modules/evidence_foundation.py",
        "seminartext_modules/project_knowledge_bridge.py",
        "seminartext_modules/human_review_workflow.py",
        "seminartext_modules/owned_tmp.py",
        "seminartext_modules/group_sources.py",
        "seminartext_modules/asr_completion.py",
        "seminartext_modules/dataset_governance.py",
        "seminartext_modules/topic_engine_governance.py",
        "schemas/validate_canonical_evidence_v1.py",
        "schemas/canonical_evidence_v1.schema.json",
        "schemas/validate_canonical_knowledge_v1.py",
        "schemas/canonical_knowledge_v1.schema.json",
        "schemas/canonical_knowledge_lifecycle_v1.json",
        "schemas/project_knowledge_input_v1.schema.json",
        "schemas/topic_review_workflow_v1.schema.json",
        "schemas/topic_review_workflow_v2.schema.json",
        "analysis/word_timeline_mvp/canonical_evidence_bundle.json",
        "analysis/golden_knowledge_slice/golden_knowledge_slice.json",
        "analysis/golden_knowledge_slice/curation.json",
        "analysis/golden_knowledge_slice/build_golden_slice.py",
        "tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json",
        "governance/dataset_registry.json",
        "governance/topic_engine_lifecycle.json",
        "governance/topic_engine_freeze.json",
        "integrity/milestone_reconciliation.json",
        "analysis/treeseg_global_structure_poc/product_review_disposition.json",
        "analysis/obsidian_knowledge_prototype/product_review_disposition.json",
        "analysis/ROADMAP_STATE_CONSISTENCY_REVIEW_2026-08-26.md",
        "analysis/ROADMAP_STATE_POST_BASELINE_CONSISTENCY_REVIEW_2026-08-27.md",
        "analysis/TREESEG_GLOBAL_STRUCTURE_POC_ISSUE_52.md",
        "analysis/OBSIDIAN_KNOWLEDGE_PROTOTYPE_GOLDEN_SEMINAR.md",
    ):
        source = ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    # The fixture owns its stub engine; supply any newly declared closure file
    # without replacing deliberately synthetic sources above.
    for component in contract["runtime_components"]:
        source = root / component["repository_path"]
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / component["repository_path"], source)

    lifecycle_path = root / "governance" / "topic_engine_lifecycle.json"
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    fake_topics_hash = hashlib.sha256(
        (root / "seminartext_modules/seminartext_topics.py").read_bytes()
    ).hexdigest()
    lifecycle["engines"][0]["implementation"]["sha256"] = fake_topics_hash
    lifecycle_path.write_text(json.dumps(lifecycle, indent=2) + "\n", encoding="utf-8")

    for component in contract["runtime_components"]:
        destination = deploy / component["deployed_name"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / component["repository_path"], destination)
        if component["id"] == "cli":
            destination.chmod(0o755)

    run(["git", "init", "-q", "-b", "main"], root)
    run(["git", "config", "user.email", "integrity@example.invalid"], root)
    run(["git", "config", "user.name", "Integrity Fixture"], root)
    run(["git", "add", "."], root)
    run(["git", "commit", "-q", "-m", "healthy fixture"], root)
    run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"], root)

    context = CheckContext(
        root=root,
        deploy_dir=deploy,
        contract=contract,
        test_command=(sys.executable, "-c", "print('10 passed in 0.01s')"),
        governance_command=(
            sys.executable,
            str(root / "scripts" / "check_governance.py"),
        ),
    )
    return root, deploy, context


def test_all_implemented_gates_pass_on_controlled_healthy_fixture(tmp_path):
    _, _, context = make_fixture(tmp_path)
    report, exit_code = run_integrity(context)
    by_id = {gate["id"]: gate for gate in report["gates"]}

    assert exit_code == 0
    assert report["bootstrap_implementation"] == "PASS"
    assert report["project_integrity"] == "PARTIAL"
    assert all(by_id[gate]["status"] == "PASS" for gate in ("G1", "G2", "G3", "G7", "G8"))
    assert by_id["G4"]["status"] == "PASS"
    assert by_id["G5"]["status"] == "PASS"
    assert by_id["G6"]["status"] == "NOT_IMPLEMENTED"


def test_git_dirty_state_is_detected_without_mutation(tmp_path):
    root, _, context = make_fixture(tmp_path)
    dirty = root / "local-note.txt"
    dirty.write_text("unique local work\n", encoding="utf-8")
    before = dirty.read_bytes()
    result = git_truth.run(context)

    assert result.status == "FAIL"
    assert "working tree is dirty" in result.reason
    assert dirty.read_bytes() == before


def test_git_origin_main_behind_condition_is_detected_locally(tmp_path):
    root, _, context = make_fixture(tmp_path)
    tree = run(["git", "rev-parse", "HEAD^{tree}"], root).stdout.strip()
    commit = subprocess.run(
        ["git", "commit-tree", tree, "-p", "HEAD", "-m", "origin ahead"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    run(["git", "update-ref", "refs/remotes/origin/main", commit], root)

    result = git_truth.run(context)
    assert result.status == "FAIL"
    assert result.evidence["behind"] == 1
    assert "behind origin/main" in result.reason


def test_required_runtime_source_missing_is_detected(tmp_path):
    root, _, context = make_fixture(tmp_path)
    missing = root / "seminartext_modules" / "seminartext_translate.py"
    missing.unlink()

    result = git_truth.run(context)
    assert result.status == "FAIL"
    assert "required runtime source missing" in result.reason


def test_runtime_sync_stale_missing_and_unverified_are_truthful(tmp_path):
    _, deploy, context = make_fixture(tmp_path)
    assert runtime_truth.run(context).status == "PASS"

    (deploy / "seminartext_4.0_work").write_text("stale\n", encoding="utf-8")
    stale = runtime_truth.run(context)
    assert stale.status == "FAIL"
    assert "cli=STALE" in stale.reason

    (deploy / "SEMINARTEXT_VERSION").unlink()
    missing = runtime_truth.run(context)
    assert missing.status == "FAIL"
    assert "version=MISSING" in missing.reason

    empty_deploy = deploy.parent / "empty"
    empty_deploy.mkdir()
    unverified = runtime_truth.run(replace(context, deploy_dir=empty_deploy))
    assert unverified.status == "WARN"
    assert "UNVERIFIED" in unverified.reason


def test_runtime_truth_requires_evidence_foundation_closure(tmp_path):
    _, deploy, context = make_fixture(tmp_path)
    missing = deploy / "seminartext_modules" / "evidence_foundation.py"
    missing.unlink()

    result = runtime_truth.run(context)

    assert result.status == "FAIL"
    assert "evidence_foundation=MISSING" in result.reason
    assert "functional_smoke" not in result.evidence


def test_runtime_truth_fails_when_dispatch_smoke_fails_even_with_matching_hashes(tmp_path):
    root, deploy, context = make_fixture(tmp_path)
    cli = root / "seminartext"
    cli.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
    cli.chmod(0o755)
    shutil.copy2(cli, deploy / "seminartext_4.0_work")
    (deploy / "seminartext_4.0_work").chmod(0o755)

    result = runtime_truth.run(context)

    assert result.status == "FAIL"
    assert "functional smoke failed" in result.reason
    assert result.evidence["functional_smoke"]["status"] == "FAIL"


def test_governance_failure_propagates_into_g3(tmp_path):
    root, _, context = make_fixture(tmp_path)
    failing = root / "governance-fail.py"
    failing.write_text("print('GOVERNANCE CHECK: FAIL'); raise SystemExit(1)\n")
    result = governance_truth.run(
        replace(context, governance_command=(sys.executable, str(failing)))
    )
    assert result.status == "FAIL"
    assert result.evidence["exit_code"] == 1


def test_governance_check_mutation_is_detected(tmp_path):
    root, _, context = make_fixture(tmp_path)
    mutating = root / "governance-mutate.py"
    mutating.write_text(
        "from pathlib import Path\n"
        "p=Path('SEMINARTEXT_4_STATE.json')\n"
        "p.write_text(p.read_text() + ' ')\n",
        encoding="utf-8",
    )
    result = governance_truth.run(
        replace(context, governance_command=(sys.executable, str(mutating)))
    )
    assert result.status == "FAIL"
    assert result.evidence["mutated_files"] == ["SEMINARTEXT_4_STATE.json"]


def test_test_failure_and_missing_capability_never_become_pass(tmp_path):
    _, _, context = make_fixture(tmp_path)
    failing = replace(
        context,
        test_command=(
            sys.executable,
            "-c",
            "print('4 passed, 1 failed in 0.1s'); raise SystemExit(1)",
        ),
    )
    failed = tests_truth.run(failing)
    assert failed.status == "FAIL"
    assert failed.evidence["failed"] == 1

    missing = tests_truth.run(
        replace(context, test_command=(str(context.root / "missing-pytest"),))
    )
    assert missing.status == "FAIL"
    assert "unavailable" in missing.reason


def test_visible_test_skip_is_warn_not_hidden_pass(tmp_path):
    _, _, context = make_fixture(tmp_path)
    skipping = replace(
        context,
        test_command=(
            sys.executable,
            "-c",
            "print('SKIPPED [1] fixture.py: dependency missing\\n9 passed, 1 skipped')",
        ),
    )
    result = tests_truth.run(skipping)
    assert result.status == "WARN"
    assert result.evidence["skipped"] == 1
    assert "G4" in result.reason


def test_obvious_product_state_contradiction_is_detected(tmp_path):
    root, _, context = make_fixture(tmp_path)
    state_path = root / "SEMINARTEXT_4_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["stages"]["word_alignment"]["status"] = "production_integrated"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = product_state.run(context)
    assert result.status == "FAIL"
    assert "claims production integration" in result.reason


def test_negative_mvp_maturity_wording_is_not_a_positive_claim(tmp_path):
    _, _, context = make_fixture(tmp_path)
    result = product_state.run(context)
    assert result.status == "PASS"
    assert result.evidence["product_mvp_status"] == "defined_not_yet_product_integrated"


def test_json_report_contract_and_exit_semantics(tmp_path):
    _, _, context = make_fixture(tmp_path)
    report, exit_code = run_integrity(context)

    encoded = json.dumps(report, sort_keys=True)
    decoded = json.loads(encoded)
    assert exit_code == 0
    assert decoded["report_schema_version"] == 2
    assert decoded["integrity_contract_version"] == "1.1.2"
    assert decoded["control_plane_reconciled"] is True
    assert decoded["next_issue_allowed"] is False
    assert decoded["human_gate"] == "AUTO_UNTIL_DOMAIN_REVIEW"
    assert decoded["github_lifecycle_check"] == "NOT_RUN"
    assert len(decoded["gates"]) == 8
    assert decoded["exit_code"] == exit_code
    assert {gate["status"] for gate in decoded["gates"]} <= {
        "PASS",
        "FAIL",
        "WARN",
        "NOT_IMPLEMENTED",
        "NOT_APPLICABLE",
    }

    failed_context = replace(
        context,
        test_command=(sys.executable, "-c", "print('1 failed'); raise SystemExit(1)"),
    )
    failed_report, failed_exit = run_integrity(failed_context)
    assert failed_exit == 1
    assert failed_report["project_integrity"] == "FAIL"

    schema = json.loads(
        (ROOT / "integrity" / "integrity_report.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(schema["required"]) == set(decoded)
    assert schema["properties"]["report_schema_version"]["const"] == 2
    assert set(schema["properties"]["gates"]["items"]["properties"]["status"]["enum"]) == {
        "PASS",
        "FAIL",
        "WARN",
        "NOT_IMPLEMENTED",
        "NOT_APPLICABLE",
    }


def test_checker_is_read_only_on_fixture(tmp_path):
    root, _, context = make_fixture(tmp_path)
    before = file_hashes(root)
    report, _ = run_integrity(context)
    after = file_hashes(root)
    assert report["bootstrap_implementation"] == "PASS"
    assert after == before


def test_canonical_entrypoint_emits_valid_json_without_fixture_mutation(tmp_path):
    root, deploy, _ = make_fixture(tmp_path)
    before = file_hashes(root)
    process = subprocess.run(
        [
            str(ENTRYPOINT),
            "--json",
            "--root",
            str(root),
            "--deploy-dir",
            str(deploy),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    report = json.loads(process.stdout)
    after = file_hashes(root)

    assert process.returncode == 1
    assert report["report_schema_version"] == 2
    assert report["bootstrap_implementation"] == "PASS"
    assert report["project_integrity"] == "FAIL"
    assert next(g for g in report["gates"] if g["id"] == "G7")["status"] == "FAIL"
    assert after == before


def test_internal_contract_error_uses_distinct_exit_code_two(tmp_path):
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    process = subprocess.run(
        [str(ENTRYPOINT), "--json", "--root", str(empty_root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    report = json.loads(process.stdout)
    assert process.returncode == 2
    assert report["exit_code"] == 2
    assert report["bootstrap_implementation"] == "FAIL"
    assert report["internal_errors"]


def test_fixture_paths_never_target_real_deploy_or_project_data(tmp_path):
    root, deploy, context = make_fixture(tmp_path)
    assert tmp_path in root.parents
    assert tmp_path in deploy.parents
    assert str(context.deploy_dir) != "/Users/yurielokhin/bin"
    assert "seminartext_projects" not in str(context.root)
