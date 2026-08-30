from __future__ import annotations

import hashlib

from integrity.checks.control_plane import evaluate as evaluate_control_plane
from integrity.model import CheckContext, GateResult, gate_definition
from integrity.process import run_process


GOVERNED_FILES = (
    "SEMINARTEXT_4_STATE.json",
    "SEMINARTEXT_4_ROADMAP.md",
    "DEVELOPMENT_WORKFLOW.md",
    "SEMINARTEXT_VERSION",
    "SEMINARTEXT_4_MVP_DEFINITION.md",
    "integrity/milestone_reconciliation.json",
)


def _hashes(context: CheckContext):
    result = {}
    for relative in GOVERNED_FILES:
        path = context.root / relative
        result[relative] = (
            hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        )
    return result


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G3")
    before = _hashes(context)
    control_plane = evaluate_control_plane(context.root)
    try:
        process = run_process(context.governance_command, context.root)
    except OSError as exc:
        return GateResult(
            "G3",
            gate["name"],
            "FAIL",
            "governance checker is unavailable",
            {"command": list(context.governance_command), "error": str(exc)},
        )
    after = _hashes(context)
    changed = [path for path in GOVERNED_FILES if before[path] != after[path]]
    evidence = {
        "command": list(context.governance_command),
        "exit_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
        "governed_hashes_before": before,
        "governed_hashes_after": after,
        "mutated_files": changed,
        "control_plane": control_plane.evidence(),
    }
    if changed:
        return GateResult(
            "G3",
            gate["name"],
            "FAIL",
            "governance check mutated governed files: " + ", ".join(changed),
            evidence,
        )
    if process.returncode != 0:
        return GateResult(
            "G3",
            gate["name"],
            "FAIL",
            "repository governance checker failed",
            evidence,
        )
    if control_plane.g3_errors:
        return GateResult(
            "G3",
            gate["name"],
            "FAIL",
            "; ".join(control_plane.g3_errors),
            evidence,
        )
    return GateResult(
        "G3",
        gate["name"],
        "PASS",
        "repository governance and accepted-decision reconciliation passed read-only",
        evidence,
    )
