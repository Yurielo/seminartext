from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from integrity import INTEGRITY_REPORT_SCHEMA_VERSION
from integrity.checks import (
    canonical_contract_truth,
    dependency_truth,
    git_truth,
    governance_truth,
    product_state,
    runtime_truth,
    tests_truth,
)
from integrity.model import CheckContext, GateResult, VALID_STATUSES


CHECKS: dict[str, Callable[[CheckContext], GateResult]] = {
    "G1": git_truth.run,
    "G2": runtime_truth.run,
    "G3": governance_truth.run,
    "G4": dependency_truth.run,
    "G5": canonical_contract_truth.run,
    "G7": tests_truth.run,
    "G8": product_state.run,
}


def load_contract(root: Path) -> dict:
    path = root / "integrity" / "integrity_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported integrity contract schema_version")
    if set(data.get("allowed_statuses", [])) != VALID_STATUSES:
        raise ValueError("integrity contract allowed_statuses drift")
    gates = data.get("gates")
    if not isinstance(gates, list) or [gate.get("id") for gate in gates] != [
        f"G{index}" for index in range(1, 9)
    ]:
        raise ValueError("integrity contract must declare ordered gates G1 through G8")
    for gate in gates:
        implemented = gate["id"] in CHECKS
        declared = str(gate.get("implementation", "")).startswith("IMPLEMENTED")
        if implemented != declared:
            raise ValueError(
                f"implementation declaration mismatch for {gate['id']}: "
                f"contract={gate.get('implementation')!r}"
            )
        if not gate.get("blocking_policy"):
            raise ValueError(f"blocking_policy missing for {gate['id']}")
    return data


def select_test_python(root: Path) -> str:
    candidates = []
    override = os.environ.get("SEMINARTEXT_INTEGRITY_TEST_PYTHON")
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        (
            root / ".venv" / "bin" / "python",
            Path.home() / ".seminartext-venv" / "bin" / "python",
            Path(sys.executable),
        )
    )
    seen = set()
    for candidate in candidates:
        raw = str(candidate)
        if raw in seen or not candidate.is_file():
            continue
        seen.add(raw)
        probe = subprocess.run(
            [raw, "-c", "import pytest"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            return raw
    return str(Path(sys.executable))


def default_context(root: Path, deploy_dir: Path, contract: dict) -> CheckContext:
    test_python = select_test_python(root)
    test_command = tuple(
        test_python if item == "{test_python}" else item
        for item in contract["test_policy"]["command"]
    )
    governance_command = (
        str(Path(sys.executable)),
        str(root / "scripts" / "check_governance.py"),
        "--root",
        str(root),
    )
    return CheckContext(
        root=root,
        deploy_dir=deploy_dir,
        contract=contract,
        test_command=test_command,
        governance_command=governance_command,
    )


def run_integrity(context: CheckContext) -> tuple[dict, int]:
    results = []
    internal_errors = []
    definitions = {gate["id"]: gate for gate in context.contract["gates"]}

    for gate_id in (f"G{index}" for index in range(1, 9)):
        definition = definitions[gate_id]
        if gate_id not in CHECKS:
            results.append(
                GateResult(
                    gate_id,
                    definition["name"],
                    "NOT_IMPLEMENTED",
                    definition["reason"],
                    {
                        "contract_implementation": definition["implementation"],
                        "blocking_policy": definition["blocking_policy"],
                    },
                )
            )
            continue
        try:
            result = CHECKS[gate_id](context)
            if result.gate_id != gate_id:
                raise ValueError(
                    f"check returned {result.gate_id} while running {gate_id}"
                )
            results.append(result)
        except Exception as exc:  # checker errors are distinct from integrity FAIL
            internal_errors.append({"gate": gate_id, "error": repr(exc)})
            results.append(
                GateResult(
                    gate_id,
                    definition["name"],
                    "FAIL",
                    "internal checker error",
                    {"error": repr(exc)},
                )
            )

    head_sha = None
    for result in results:
        if result.gate_id == "G1":
            head_sha = result.evidence.get("head_sha")
            break

    bootstrap = "FAIL" if internal_errors else "PASS"
    implemented_blocking_failures = [
        result.gate_id
        for result in results
        if result.status == "FAIL"
        and definitions[result.gate_id]["implementation"].startswith("IMPLEMENTED")
        and definitions[result.gate_id]["blocking_policy"].startswith("blocking")
    ]
    if internal_errors:
        project_integrity = "FAIL"
        exit_code = 2
    elif implemented_blocking_failures:
        project_integrity = "FAIL"
        exit_code = 1
    elif any(result.status in {"WARN", "NOT_IMPLEMENTED"} for result in results):
        project_integrity = "PARTIAL"
        exit_code = 0
    else:
        project_integrity = "PASS"
        exit_code = 0

    report = {
        "report_schema_version": INTEGRITY_REPORT_SCHEMA_VERSION,
        "integrity_contract_version": context.contract["integrity_contract_version"],
        "head_sha": head_sha,
        "repository_root": str(context.root),
        "deployment_dir": str(context.deploy_dir),
        "gates": [result.as_dict() for result in results],
        "bootstrap_implementation": bootstrap,
        "project_integrity": project_integrity,
        "implemented_blocking_failures": implemented_blocking_failures,
        "internal_errors": internal_errors,
        "exit_code": exit_code,
    }
    control_plane = next(
        (
            result.evidence.get("control_plane")
            for result in results
            if result.gate_id == "G8" and result.evidence.get("control_plane")
        ),
        None,
    )
    report.update(
        {
            "control_plane_reconciled": bool(
                control_plane and control_plane.get("control_plane_reconciled")
            ),
            "next_issue_allowed": bool(
                control_plane and control_plane.get("next_issue_allowed")
            ),
            "human_gate": (
                control_plane.get("human_gate") if control_plane else "UNRESOLVED"
            ),
            "github_lifecycle_check": (
                control_plane.get("github_lifecycle_check")
                if control_plane
                else "NOT_RUN"
            ),
        }
    )
    return report, exit_code


def render_human(report: dict) -> str:
    lines = [
        "SEMINARTEXT PROJECT INTEGRITY",
        f"HEAD: {report['head_sha'] or 'UNRESOLVED'}",
        "",
    ]
    for gate in report["gates"]:
        lines.append(f"{gate['id']} {gate['name']:<25} {gate['status']}")
        lines.append(f"   {gate['reason']}")
    lines.extend(
        (
            "",
            f"BOOTSTRAP_IMPLEMENTATION: {report['bootstrap_implementation']}",
            "CONTROL_PLANE_RECONCILED: "
            + ("YES" if report["control_plane_reconciled"] else "NO"),
            "NEXT_ISSUE_ALLOWED: "
            + ("YES" if report["next_issue_allowed"] else "NO"),
            f"HUMAN_GATE: {report['human_gate']}",
            f"GITHUB_LIFECYCLE_CHECK: {report['github_lifecycle_check']}",
            f"PROJECT_INTEGRITY: {report['project_integrity']}",
        )
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only SeminarText integrity gate")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--deploy-dir",
        type=Path,
        default=Path(os.environ.get("SEMINARTEXT_DEPLOY_DIR", "~/bin")).expanduser(),
    )
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    deploy_dir = args.deploy_dir.expanduser().resolve()

    try:
        contract = load_contract(root)
        context = default_context(root, deploy_dir, contract)
        report, exit_code = run_integrity(context)
    except Exception as exc:
        report = {
            "report_schema_version": INTEGRITY_REPORT_SCHEMA_VERSION,
            "integrity_contract_version": None,
            "head_sha": None,
            "repository_root": str(root),
            "deployment_dir": str(deploy_dir),
            "gates": [],
            "bootstrap_implementation": "FAIL",
            "project_integrity": "FAIL",
            "implemented_blocking_failures": [],
            "internal_errors": [{"gate": None, "error": repr(exc)}],
            "exit_code": 2,
            "control_plane_reconciled": False,
            "next_issue_allowed": False,
            "human_gate": "UNRESOLVED",
            "github_lifecycle_check": "NOT_RUN",
        }
        exit_code = 2

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_human(report))
        if report["internal_errors"]:
            print("INTERNAL_ERRORS:")
            for item in report["internal_errors"]:
                print(f"  {item}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
