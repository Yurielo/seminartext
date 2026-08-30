from __future__ import annotations

import hashlib
import os
import subprocess

from integrity.model import CheckContext, GateResult, gate_definition


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G2")
    components = []
    source_failures = []
    deployed_present = 0

    for declaration in context.contract["runtime_components"]:
        source = context.root / declaration["repository_path"]
        deployed = context.deploy_dir / declaration["deployed_name"]
        source_exists = source.is_file()
        deployed_exists = deployed.is_file()
        if deployed_exists:
            deployed_present += 1

        source_hash = _sha256(source) if source_exists else None
        deployed_hash = _sha256(deployed) if deployed_exists else None
        if not source_exists and declaration.get("required", False):
            source_failures.append(declaration["repository_path"])

        if not deployed_exists:
            deployment_status = "MISSING"
        elif not source_exists:
            deployment_status = "UNVERIFIED"
        elif source_hash == deployed_hash:
            deployment_status = "SYNC"
        else:
            deployment_status = "STALE"

        components.append(
            {
                "id": declaration["id"],
                "repository_path": declaration["repository_path"],
                "repository_sha256": source_hash,
                "deployed_path": str(deployed),
                "deployed_sha256": deployed_hash,
                "deployment_status": deployment_status,
            }
        )

    version_path = context.root / "SEMINARTEXT_VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else None
    evidence = {
        "repository_root": str(context.root),
        "repository_version": version,
        "deployment_dir": str(context.deploy_dir),
        "deployment_detected": deployed_present > 0,
        "components": components,
    }

    if source_failures:
        return GateResult(
            "G2",
            gate["name"],
            "FAIL",
            "repository runtime source missing: " + ", ".join(source_failures),
            evidence,
        )
    if deployed_present == 0:
        return GateResult(
            "G2",
            gate["name"],
            "WARN",
            "no installed runtime detected; repository source is verified but deployment is UNVERIFIED",
            evidence,
        )

    bad = [
        row
        for row in components
        if row["deployment_status"] in {"STALE", "MISSING", "UNVERIFIED"}
    ]
    if bad:
        summary = ", ".join(
            f"{row['id']}={row['deployment_status']}" for row in bad
        )
        return GateResult(
            "G2",
            gate["name"],
            "FAIL",
            f"detected installed runtime is not synchronized: {summary}",
            evidence,
        )

    # A synchronized file set is not sufficient: verify that the deployed
    # entrypoint can load and dispatch governed runtime paths.  These bounded
    # commands are read-only and do not touch project data, models, or external
    # dependencies.
    cli_path = context.deploy_dir / next(
        item["deployed_name"]
        for item in context.contract["runtime_components"]
        if item["id"] == "cli"
    )
    smoke_commands = [
        [str(cli_path), "project-evidence-check", "--help"],
        [str(cli_path), "project-obsidian-export", "--help"],
        [str(cli_path), "dataset-policy-check", "A", "gold_read", "--json"],
        [
            context.test_command[0],
            str(context.deploy_dir / "seminartext_modules" / "topic_engine_governance.py"),
            "validate",
            "--lifecycle",
            str(context.deploy_dir / "governance" / "topic_engine_lifecycle.json"),
            "--deployed",
            "--json",
        ],
        [
            context.test_command[0],
            str(context.deploy_dir / "seminartext_modules" / "topic_engine_governance.py"),
            "freeze-check",
            "--freeze",
            str(context.deploy_dir / "governance" / "topic_engine_freeze.json"),
            "--dataset-registry",
            str(context.deploy_dir / "governance" / "dataset_registry.json"),
            "--lifecycle",
            str(context.deploy_dir / "governance" / "topic_engine_lifecycle.json"),
            "--deployed",
            "--json",
        ],
    ]
    smoke_checks = []
    for smoke_command in smoke_commands:
        try:
            smoke = subprocess.run(
                smoke_command,
                cwd=context.deploy_dir,
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            smoke_checks.append(
                {
                    "status": "PASS" if smoke.returncode == 0 else "FAIL",
                    "command": smoke_command,
                    "returncode": smoke.returncode,
                    "stdout": smoke.stdout[-4000:],
                    "stderr": smoke.stderr[-4000:],
                }
            )
        except (OSError, subprocess.SubprocessError) as exc:
            smoke_checks.append(
                {"status": "FAIL", "command": smoke_command, "error": str(exc)}
            )
    smoke_evidence = {
        "status": "PASS" if all(item["status"] == "PASS" for item in smoke_checks) else "FAIL",
        "checks": smoke_checks,
    }
    evidence["functional_smoke"] = smoke_evidence
    if smoke_evidence["status"] != "PASS":
        return GateResult(
            "G2",
            gate["name"],
            "FAIL",
            "deployed governed runtime functional smoke failed",
            evidence,
        )
    return GateResult(
        "G2",
        gate["name"],
        "PASS",
        "detected installed runtime is byte-identical and governed dispatch smokes passed",
        evidence,
    )
