from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_MILESTONE_FIELDS = {
    "milestone_id",
    "issue_id",
    "status",
    "decision",
    "disposition",
    "accepted",
    "implementation_state",
    "human_gate",
    "next_allowed_actions",
    "blocked_actions",
    "runtime_reconciliation_required",
    "runtime_reconciliation_complete",
    "evidence_refs",
    "historical",
    "prerequisite_milestones",
    "state_sequence_status",
}
ROADMAP_START = "<!-- SEMINARTEXT_CONTROL_PLANE_START -->"
ROADMAP_END = "<!-- SEMINARTEXT_CONTROL_PLANE_END -->"


@dataclass(frozen=True)
class ControlPlaneResult:
    contract_version: str | None
    current_milestone_id: str | None
    lifecycle_state: str | None
    human_gate: str
    github_lifecycle_check: str
    control_plane_reconciled: bool
    next_issue_allowed: bool
    g3_errors: tuple[str, ...]
    g8_errors: tuple[str, ...]

    def evidence(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "current_milestone_id": self.current_milestone_id,
            "lifecycle_state": self.lifecycle_state,
            "human_gate": self.human_gate,
            "github_lifecycle_check": self.github_lifecycle_check,
            "control_plane_reconciled": self.control_plane_reconciled,
            "next_issue_allowed": self.next_issue_allowed,
            "g3_errors": list(self.g3_errors),
            "g8_errors": list(self.g8_errors),
        }


def _error(bucket: list[str], code: str, message: str) -> None:
    bucket.append(f"{code}: {message}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _roadmap_snapshot(path: Path, start_marker: str, end_marker: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError("Roadmap must contain exactly one control-plane marker pair")
    payload = text.split(start_marker, 1)[1].split(end_marker, 1)[0].strip()
    if payload.startswith("```json") and payload.endswith("```"):
        payload = payload[len("```json") : -len("```")].strip()
    return json.loads(payload)


def _pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer!r}")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise KeyError(pointer)
    return value


def _projection(contract: dict[str, Any], milestones: dict[str, dict[str, Any]]) -> dict[str, Any]:
    current_id = contract["current_milestone_id"]
    current = milestones.get(current_id) if current_id is not None else None
    return {
        "contract_version": contract["contract_version"],
        "current_milestone_id": current_id,
        "last_completed_milestone_id": contract.get("last_completed_milestone_id"),
        "next_eligible_milestone_id": contract.get("next_eligible_milestone_id"),
        "lifecycle_state": (
            current["status"] if current is not None else contract["lifecycle_state"]
        ),
        "human_gate": (
            current["human_gate"] if current is not None else contract["human_gate"]
        ),
        "next_issue_allowed": contract["next_issue_allowed"],
        "active_actions": contract["active_actions"],
        "blocked_actions": contract["blocked_actions"],
        "authorization_states": contract.get("authorization_states", {}),
        "milestones": {
            milestone_id: {
                "status": milestone["status"],
                "accepted": milestone["accepted"],
                "implementation_state": milestone["implementation_state"],
                "human_gate": milestone["human_gate"],
                "runtime_reconciliation_required": milestone[
                    "runtime_reconciliation_required"
                ],
                "runtime_reconciliation_complete": milestone[
                    "runtime_reconciliation_complete"
                ],
            }
            for milestone_id, milestone in milestones.items()
        },
    }


def evaluate(root: Path) -> ControlPlaneResult:
    g3_errors: list[str] = []
    g8_errors: list[str] = []
    contract_path = root / "integrity" / "milestone_reconciliation.json"
    try:
        contract = _read_json(contract_path)
    except (OSError, json.JSONDecodeError) as exc:
        message = f"reconciliation contract cannot be read: {exc}"
        return ControlPlaneResult(
            None,
            None,
            None,
            "UNRESOLVED",
            "NOT_RUN",
            False,
            False,
            (f"CP_CONTRACT_UNREADABLE: {message}",),
            (f"CP_CONTRACT_UNREADABLE: {message}",),
        )

    contract_version = contract.get("contract_version")
    current_id = contract.get("current_milestone_id")
    github_check = contract.get("github_lifecycle_check", "NOT_RUN")
    lifecycle_state = None
    human_gate = "UNRESOLVED"

    if contract.get("schema_version") != 1:
        _error(g3_errors, "CP_SCHEMA", "schema_version must be 1")
    if not isinstance(contract_version, str) or not contract_version:
        _error(g3_errors, "CP_SCHEMA", "contract_version must be non-empty")
    if github_check not in {"NOT_RUN", "PASS", "FAIL"}:
        _error(g3_errors, "CP_SCHEMA", "github_lifecycle_check is invalid")

    authorization_states = contract.get("authorization_states")
    required_authorizations = {"audit_r5", "audit_r6", "issue_65", "issue_66"}
    if not isinstance(authorization_states, dict):
        _error(g8_errors, "CP_AUTHORIZATION_STATE", "authorization_states must be an object")
    else:
        for action in sorted(required_authorizations):
            if authorization_states.get(action) != "NOT_AUTHORIZED":
                _error(
                    g8_errors,
                    "CP_AUTHORIZATION_STATE",
                    f"{action} must remain NOT_AUTHORIZED",
                )
        expected_r4_authorization = (
            "AUTHORIZED_IMPLEMENTATION"
            if current_id == "audit_r4_mandatory_ci_and_main_protection"
            else "NOT_AUTHORIZED"
        )
        if authorization_states.get("audit_r4") != expected_r4_authorization:
            _error(
                g8_errors,
                "CP_AUTHORIZATION_STATE",
                f"audit_r4 must be {expected_r4_authorization}",
            )

    raw_milestones = contract.get("milestones")
    milestones: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_milestones, list) or not raw_milestones:
        _error(g3_errors, "CP_SCHEMA", "milestones must be a non-empty list")
    else:
        for index, milestone in enumerate(raw_milestones):
            if not isinstance(milestone, dict):
                _error(g3_errors, "CP_SCHEMA", f"milestone {index} must be an object")
                continue
            missing = sorted(REQUIRED_MILESTONE_FIELDS - milestone.keys())
            if missing:
                _error(
                    g3_errors,
                    "CP_SCHEMA",
                    f"milestone {index} missing fields: {', '.join(missing)}",
                )
                continue
            milestone_id = milestone["milestone_id"]
            if not isinstance(milestone_id, str) or not milestone_id:
                _error(g3_errors, "CP_SCHEMA", f"milestone {index} has invalid id")
                continue
            if milestone_id in milestones:
                _error(g3_errors, "CP_SCHEMA", f"duplicate milestone {milestone_id}")
                continue
            milestones[milestone_id] = milestone

    current = milestones.get(current_id) if current_id is not None else None
    if current_id is None:
        lifecycle_state = contract.get("lifecycle_state")
        human_gate = contract.get("human_gate", "UNRESOLVED")
        if not isinstance(lifecycle_state, str) or not lifecycle_state:
            _error(
                g8_errors,
                "CP_LIFECYCLE_UNRESOLVED",
                "inactive control plane lacks lifecycle_state",
            )
        if not isinstance(human_gate, str) or not human_gate:
            _error(
                g8_errors,
                "CP_HUMAN_GATE_UNRESOLVED",
                "inactive control plane lacks human_gate",
            )
    elif current is None:
        _error(g8_errors, "CP_CURRENT_UNKNOWN", f"current milestone {current_id!r} is not declared")
    else:
        lifecycle_state = current["status"]
        human_gate = current["human_gate"]
        if (
            current_id == "audit_r4_mandatory_ci_and_main_protection"
            and current.get("authorized") is not True
        ):
            _error(
                g8_errors,
                "CP_AUTHORIZATION_STATE",
                "active audit_r4 milestone must carry authorized=true",
            )

    for milestone_id, milestone in milestones.items():
        status = str(milestone["status"])
        if milestone["accepted"] and (
            "PENDING" in status or "PENDING" in str(milestone["human_gate"])
        ):
            _error(
                g3_errors,
                "CP_ACCEPTED_PENDING",
                f"accepted milestone {milestone_id} is still represented as pending",
            )
        if milestone["accepted"] and milestone["decision"] != "ACCEPT":
            _error(
                g3_errors,
                "CP_ACCEPTANCE_DECISION",
                f"accepted milestone {milestone_id} does not carry ACCEPT decision",
            )
        if milestone["historical"]:
            _error(
                g3_errors,
                "CP_ACTIVE_MARKED_HISTORICAL",
                f"active milestone inventory marks {milestone_id} historical",
            )
        for prerequisite in milestone["prerequisite_milestones"]:
            required = milestones.get(prerequisite)
            if required is None:
                _error(
                    g8_errors,
                    "CP_PREREQUISITE_UNKNOWN",
                    f"{milestone_id} references unknown prerequisite {prerequisite}",
                )
            elif (
                milestone["accepted"]
                or milestone_id in {
                    current_id,
                    contract.get("next_eligible_milestone_id"),
                }
            ) and not (
                required["accepted"] and required["implementation_state"] == "COMPLETE"
            ):
                _error(
                    g8_errors,
                    "CP_SEQUENCE_VIOLATION",
                    f"current milestone {milestone_id} precedes incomplete prerequisite {prerequisite}",
                )

    last_completed_id = contract.get("last_completed_milestone_id")
    last_completed = milestones.get(last_completed_id)
    if last_completed is None:
        _error(
            g8_errors,
            "CP_LAST_COMPLETED_UNKNOWN",
            "last completed milestone is not declared",
        )
    elif not (
        last_completed["accepted"]
        and last_completed["implementation_state"] == "COMPLETE"
        and str(last_completed["status"]).startswith("COMPLETE")
    ):
        _error(
            g8_errors,
            "CP_LAST_COMPLETED_INVALID",
            f"{last_completed_id} is not complete and accepted",
        )

    next_eligible_id = contract.get("next_eligible_milestone_id")
    next_eligible = (
        milestones.get(next_eligible_id) if next_eligible_id is not None else None
    )
    if next_eligible_id is None and current is None:
        _error(
            g8_errors,
            "CP_NEXT_ELIGIBLE_UNKNOWN",
            "next eligible milestone is not declared",
        )
    elif next_eligible_id is not None and next_eligible is None:
        _error(
            g8_errors,
            "CP_NEXT_ELIGIBLE_UNKNOWN",
            f"next eligible milestone {next_eligible_id!r} is not declared",
        )
    elif next_eligible is not None and not (
        next_eligible["status"] == "NOT_STARTED"
        and next_eligible["decision"] == "NOT_AUTHORIZED"
        and next_eligible["disposition"] == "NOT_AUTHORIZED"
        and next_eligible["accepted"] is False
        and next_eligible["implementation_state"] == "NOT_STARTED"
        and next_eligible.get("authorized") is False
    ):
        _error(
            g8_errors,
            "CP_NEXT_ELIGIBLE_AUTHORIZATION",
            f"{next_eligible_id} must remain not started and not authorized",
        )

    if contract.get("next_issue_allowed") is True:
        if current is not None:
            _error(
                g8_errors,
                "CP_NEXT_WHILE_ACTIVE",
                "next Issue is allowed while a milestone remains active",
            )
        if next_eligible is None:
            _error(
                g8_errors,
                "CP_NEXT_WITHOUT_ELIGIBLE",
                "next Issue is allowed without an eligible milestone",
            )
        if "PENDING" in str(human_gate):
            _error(
                g8_errors,
                "CP_HUMAN_GATE_BYPASS",
                "pending human gate permits the next Issue",
            )
        if last_completed is not None and (
            last_completed["runtime_reconciliation_required"]
            and not last_completed["runtime_reconciliation_complete"]
        ):
            _error(
                g8_errors,
                "CP_RUNTIME_RECONCILIATION_BYPASS",
                "incomplete required runtime reconciliation permits the next Issue",
            )

    active_blocked_overlap = sorted(
        set(contract.get("active_actions", []))
        & set(contract.get("blocked_actions", []))
    )
    if active_blocked_overlap:
        _error(
            g8_errors,
            "CP_BLOCKED_ACTION_EXECUTABLE",
            "blocked actions exposed as active actions: "
            + ", ".join(active_blocked_overlap),
        )

    if current is not None:
        if str(current["status"]).startswith("COMPLETE"):
            _error(
                g8_errors,
                "CP_COMPLETED_STILL_CURRENT",
                f"completed milestone {current_id} remains current",
            )
        if (
            "PENDING" in str(current["human_gate"])
            and contract.get("next_issue_allowed") is True
        ):
            _error(
                g8_errors,
                "CP_HUMAN_GATE_BYPASS",
                "pending human gate permits the next Issue",
            )
        if (
            current["runtime_reconciliation_required"]
            and not current["runtime_reconciliation_complete"]
            and contract.get("next_issue_allowed") is True
        ):
            _error(
                g8_errors,
                "CP_RUNTIME_RECONCILIATION_BYPASS",
                "incomplete required runtime reconciliation permits the next Issue",
            )
        overlap = sorted(
            set(current["next_allowed_actions"])
            & set(contract.get("blocked_actions", []))
        )
        if overlap:
            _error(
                g8_errors,
                "CP_BLOCKED_ACTION_EXECUTABLE",
                "blocked actions exposed as next actions: " + ", ".join(overlap),
            )

    sources: dict[str, Any] = {}
    source_specs = contract.get("authoritative_sources")
    if not isinstance(source_specs, dict):
        _error(g3_errors, "CP_SCHEMA", "authoritative_sources must be an object")
        source_specs = {}
    for source_id, spec in source_specs.items():
        try:
            path = root / spec["path"]
            if source_id == "roadmap":
                sources[source_id] = _roadmap_snapshot(
                    path,
                    spec.get("start_marker", ROADMAP_START),
                    spec.get("end_marker", ROADMAP_END),
                )
            else:
                sources[source_id] = _read_json(path)
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            bucket = g8_errors if source_id == "roadmap" else g3_errors
            _error(bucket, "CP_SOURCE_UNREADABLE", f"{source_id}: {exc}")

    expected_projection = _projection(contract, milestones)
    state = sources.get("state")
    if isinstance(state, dict):
        if state.get("control_plane") != expected_projection:
            _error(
                g3_errors,
                "CP_STALE_STATE",
                "State control_plane projection differs from reconciliation contract",
            )
        if state.get("current_milestone") != contract.get("state_current_milestone"):
            _error(
                g8_errors,
                "CP_STALE_STATE_CURRENT",
                "State current_milestone differs from reconciliation contract",
            )
        if state.get("current_stage") != contract.get("state_current_stage"):
            _error(
                g8_errors,
                "CP_STALE_STATE_STAGE",
                "State current_stage differs from reconciliation contract",
            )
        if state.get("next_actions") != contract.get("active_actions"):
            _error(
                g8_errors,
                "CP_STALE_STATE_ACTIONS",
                "State next_actions differ from reconciliation contract",
            )
        sequence = {
            item.get("milestone"): item.get("status")
            for item in state.get("near_term_execution_sequence", [])
            if isinstance(item, dict)
        }
        for milestone_id, milestone in milestones.items():
            if sequence.get(milestone_id) != milestone["state_sequence_status"]:
                _error(
                    g8_errors,
                    "CP_STALE_STATE_SEQUENCE",
                    f"State sequence status for {milestone_id} is stale",
                )

    roadmap = sources.get("roadmap")
    if isinstance(roadmap, dict) and roadmap != expected_projection:
        _error(
            g8_errors,
            "CP_STALE_ROADMAP",
            "Roadmap active snapshot differs from reconciliation contract",
        )

    assertions = contract.get("active_assertions")
    if not isinstance(assertions, list):
        _error(g3_errors, "CP_SCHEMA", "active_assertions must be a list")
    else:
        seen_assertions: set[str] = set()
        for assertion in assertions:
            try:
                assertion_id = assertion["id"]
                gate = assertion["gate"]
                source_id = assertion["source"]
                pointer = assertion["pointer"]
                expected = assertion["equals"]
                if assertion_id in seen_assertions:
                    raise ValueError(f"duplicate assertion id {assertion_id}")
                seen_assertions.add(assertion_id)
                actual = _pointer(sources[source_id], pointer)
                if actual != expected:
                    bucket = g3_errors if gate == "G3" else g8_errors
                    _error(
                        bucket,
                        "CP_ASSERTION_FAILED",
                        f"{assertion_id}: expected {expected!r}, got {actual!r}",
                    )
            except (KeyError, TypeError, ValueError, IndexError) as exc:
                gate = assertion.get("gate") if isinstance(assertion, dict) else None
                bucket = g8_errors if gate == "G8" else g3_errors
                _error(bucket, "CP_ASSERTION_INVALID", str(exc))

    historical = contract.get("historical_evidence")
    if not isinstance(historical, list):
        _error(g3_errors, "CP_SCHEMA", "historical_evidence must be a list")
    else:
        for relative in historical:
            if not isinstance(relative, str) or not (root / relative).is_file():
                _error(
                    g3_errors,
                    "CP_HISTORICAL_EVIDENCE_MISSING",
                    f"historical evidence missing: {relative!r}",
                )

    reconciled = not g3_errors and not g8_errors
    next_allowed = bool(contract.get("next_issue_allowed")) and reconciled
    return ControlPlaneResult(
        contract_version if isinstance(contract_version, str) else None,
        current_id if isinstance(current_id, str) else None,
        lifecycle_state,
        human_gate,
        github_check,
        reconciled,
        next_allowed,
        tuple(g3_errors),
        tuple(g8_errors),
    )
