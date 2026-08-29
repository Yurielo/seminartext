#!/usr/bin/env python3
"""Validate Topic Engine lifecycle truth and the Dataset D freeze gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIFECYCLE = ROOT / "governance" / "topic_engine_lifecycle.json"
DEFAULT_FREEZE = ROOT / "governance" / "topic_engine_freeze.json"
DEFAULT_DATASETS = ROOT / "governance" / "dataset_registry.json"
REQUIRED_ROLES = {
    "production_legacy",
    "experimental_primary",
    "comparator",
    "challenger",
    "frozen_candidate",
}


def _path(explicit: str | Path | None, env_name: str, default: Path) -> Path:
    raw = explicit or os.environ.get(env_name)
    return Path(raw).expanduser().resolve() if raw else default


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _artifact_hash_matches(section: dict[str, Any], base: Path) -> bool:
    artifact = section.get("artifact")
    expected = section.get("sha256")
    if not artifact or not expected:
        return False
    path = Path(artifact)
    if not path.is_absolute():
        path = base / path
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected


def validate_lifecycle(path: str | Path | None = None) -> list[str]:
    lifecycle_path = _path(path, "SEMINARTEXT_TOPIC_LIFECYCLE", DEFAULT_LIFECYCLE)
    data = _load(lifecycle_path)
    errors = []
    roles = [item.get("role_id") for item in data.get("engines", [])]
    if set(roles) != REQUIRED_ROLES or len(roles) != len(REQUIRED_ROLES):
        errors.append(f"role inventory mismatch: {roles}")
    if data.get("new_custom_family_policy") != "DENY_UNLESS_EXPLICIT_PRODUCT_OWNER_ISSUE":
        errors.append("new custom Boundary family policy is not fail-closed")
    by_role = {item["role_id"]: item for item in data.get("engines", [])}
    legacy = by_role.get("production_legacy", {})
    if not legacy.get("production_runtime") or legacy.get("production_promoted"):
        errors.append("legacy runtime truth is ambiguous")
    for role in ("experimental_primary", "comparator", "challenger"):
        item = by_role.get(role, {})
        if item.get("production_runtime") or item.get("production_promoted"):
            errors.append(f"research role incorrectly promoted: {role}")
        implementation = item.get("implementation")
        if not implementation or not (ROOT / implementation).is_file():
            errors.append(f"missing implementation provenance for {role}")
    frozen = by_role.get("frozen_candidate", {})
    if frozen.get("lifecycle_status") == "PENDING_DOMAIN_REVIEW" and frozen.get("engine_id") is not None:
        errors.append("pending frozen_candidate must not select an engine")
    semantics = data.get("benchmark_segment_semantics", {})
    if semantics.get("semantic_topic_output") is not False:
        errors.append("canonical BenchmarkSegments must remain topic-neutral")
    for item in data.get("historical_implementations", []):
        if item.get("production_runtime") or item.get("production_promoted"):
            errors.append(f"historical implementation incorrectly promoted: {item.get('engine_id')}")
        implementation = item.get("implementation")
        if not implementation or not (ROOT / implementation).is_file():
            errors.append(f"missing historical implementation provenance: {item.get('engine_id')}")
    return errors


def freeze_gate(
    freeze_path: str | Path | None = None,
    dataset_path: str | Path | None = None,
) -> dict[str, Any]:
    resolved_freeze = _path(freeze_path, "SEMINARTEXT_TOPIC_FREEZE", DEFAULT_FREEZE)
    resolved_datasets = _path(dataset_path, "SEMINARTEXT_DATASET_REGISTRY", DEFAULT_DATASETS)
    freeze = _load(resolved_freeze)
    datasets = _load(resolved_datasets)
    lifecycle = _load(DEFAULT_LIFECYCLE)
    dataset_d = next((item for item in datasets.get("datasets", []) if item.get("id") == "D"), None)
    selected_engine = freeze.get("candidate", {}).get("engine_id")
    known_candidates = {
        item.get("engine_id")
        for item in lifecycle.get("engines", [])
        if item.get("role_id") in {"experimental_primary", "comparator", "challenger"}
    }
    configuration = freeze.get("configuration", {})
    criteria = freeze.get("acceptance_criteria", {})
    plan = freeze.get("analysis_plan", {})
    checks = {
        "product_owner_decision": freeze.get("product_owner_decision") == "APPROVE_CANDIDATE_FREEZE",
        "freeze_status": freeze.get("status") == "FROZEN_APPROVED",
        "candidate_frozen": freeze.get("candidate", {}).get("frozen") is True,
        "candidate_selected": selected_engine in known_candidates,
        "configuration_frozen": configuration.get("frozen") is True,
        "configuration_hash_bound": bool(configuration.get("value"))
        and configuration.get("sha256") == _canonical_sha256(configuration.get("value")),
        "acceptance_criteria_frozen": criteria.get("frozen") is True,
        "acceptance_criteria_hash_bound": _artifact_hash_matches(criteria, ROOT),
        "analysis_plan_frozen": plan.get("frozen") is True,
        "analysis_plan_hash_bound": _artifact_hash_matches(plan, ROOT),
        "dataset_d_locked_test": bool(dataset_d and dataset_d.get("role") == "LOCKED_TEST"),
        "dataset_d_prediction_access_denied": bool(dataset_d and dataset_d.get("topic_engine_access_allowed") is False),
        "dataset_d_source_identity_recorded": bool(dataset_d and dataset_d.get("source_identity_recorded") is True),
        "dataset_d_source_quality_accepted": bool(dataset_d and dataset_d.get("source_quality") == "SUFFICIENT"),
        "single_blind_run_authorized": freeze.get("dataset_d", {}).get("single_blind_run_authorized") is True,
    }
    ready = all(checks.values())
    return {
        "status": "PASS" if ready else "BLOCKED",
        "dataset_d_open_allowed": ready,
        "checks": checks,
        "freeze_path": str(resolved_freeze),
        "freeze_sha256": hashlib.sha256(resolved_freeze.read_bytes()).hexdigest(),
        "dataset_registry_path": str(resolved_datasets),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--lifecycle")
    validate.add_argument("--json", action="store_true")
    gate = subparsers.add_parser("freeze-check")
    gate.add_argument("--freeze")
    gate.add_argument("--dataset-registry")
    gate.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "validate":
        try:
            errors = validate_lifecycle(args.lifecycle)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors = [str(exc)]
        payload = {"status": "PASS" if not errors else "FAIL", "errors": errors}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["status"])
        return 0 if not errors else 2

    try:
        result = freeze_gate(args.freeze, args.dataset_registry)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "dataset_d_open_allowed": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["status"])
    return 0 if result["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
