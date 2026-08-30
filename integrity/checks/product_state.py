from __future__ import annotations

import json
import re

from integrity.checks.control_plane import evaluate as evaluate_control_plane
from integrity.model import CheckContext, GateResult, gate_definition


def _dispatched_commands(cli_source: str) -> set[str]:
    if "main() {" not in cli_source:
        return set()
    main = cli_source[cli_source.index("main() {") :]
    return set(re.findall(r"^    ([a-z][a-z0-9-]*)\)$", main, re.MULTILINE))


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G8")
    control_plane = evaluate_control_plane(context.root)
    state_path = context.root / "SEMINARTEXT_4_STATE.json"
    version_path = context.root / "SEMINARTEXT_VERSION"
    cli_path = context.root / "seminartext"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        version = version_path.read_text(encoding="utf-8").strip()
        commands = _dispatched_commands(cli_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return GateResult(
            "G8",
            gate["name"],
            "FAIL",
            "product-state inputs cannot be read",
            {"error": str(exc)},
        )

    contradictions = []
    declared_commands = []
    maturity_rows = []
    if state.get("seminartext_version") != version:
        contradictions.append(
            "State seminartext_version contradicts SEMINARTEXT_VERSION"
        )

    for stage_name, stage in state.get("stages", {}).items():
        if not isinstance(stage, dict):
            continue
        command = stage.get("command")
        if command:
            declared_commands.append(
                {
                    "stage": stage_name,
                    "command": command,
                    "dispatched": command in commands,
                }
            )
            if command not in commands:
                contradictions.append(
                    f"{stage_name} declares missing CLI command {command}"
                )

        status = str(stage.get("status", "")).lower()
        integration = stage.get("production_integration_complete")
        population = stage.get("production_population_complete")
        if integration is not None or population is not None:
            maturity_rows.append(
                {
                    "stage": stage_name,
                    "status": stage.get("status"),
                    "production_integration_complete": integration,
                    "production_population_complete": population,
                }
            )
        if "production_integrated" in status and integration is not True:
            contradictions.append(
                f"{stage_name} status claims production integration while flag is not true"
            )
        if "production_populated" in status and population is not True:
            contradictions.append(
                f"{stage_name} status claims production population while flag is not true"
            )
        if integration is True and any(
            marker in status for marker in ("incomplete", "pending", "not_production")
        ):
            contradictions.append(
                f"{stage_name} production integration flag contradicts status={status}"
            )

    product_mvp_status = str(state.get("product_mvp", {}).get("status", ""))
    normalized_mvp_status = product_mvp_status.lower()
    claims_product_integration = (
        "product_integrated" in normalized_mvp_status
        and "not_yet_product_integrated" not in normalized_mvp_status
        and "not_product_integrated" not in normalized_mvp_status
    )
    if claims_product_integration:
        incomplete = [
            row["stage"]
            for row in maturity_rows
            if row["production_integration_complete"] is False
            or row["production_population_complete"] is False
        ]
        if incomplete:
            contradictions.append(
                "product MVP claims integration while incomplete stages remain: "
                + ", ".join(incomplete)
            )

    evidence = {
        "version_file": version,
        "state_version": state.get("seminartext_version"),
        "product_mvp_status": product_mvp_status,
        "declared_commands": declared_commands,
        "maturity_fields": maturity_rows,
        "contradictions": contradictions,
        "control_plane": control_plane.evidence(),
    }
    contradictions.extend(control_plane.g8_errors)
    evidence["contradictions"] = contradictions
    if contradictions:
        return GateResult(
            "G8",
            gate["name"],
            "FAIL",
            "; ".join(contradictions),
            evidence,
        )
    return GateResult(
        "G8",
        gate["name"],
        "PASS",
        "product maturity and milestone progression reconciliation pass",
        evidence,
    )
