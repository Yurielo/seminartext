from __future__ import annotations

import hashlib

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
    return GateResult(
        "G2",
        gate["name"],
        "PASS",
        "detected installed runtime is byte-identical to repository source",
        evidence,
    )
