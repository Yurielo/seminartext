#!/usr/bin/env python3
"""Read-only consistency checks for SeminarText governance surfaces."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EXPECTED_STATE_SCHEMA = 3
REQUIRED_STATE_KEYS = {
    "schema_version",
    "seminartext_version",
    "policy_checkpoint",
    "current_stage",
    "current_milestone",
    "architecture",
    "stages",
    "next_actions",
    "roadmap_state_consistency",
    "status_semantics",
    "product_mvp",
}
OBSOLETE_ACTIVE_PATTERNS = {
    "Dataset C is next": re.compile(
        r"next independent validation step is\s+Dataset C", re.IGNORECASE
    ),
    "Topic Stable blocks Obsidian": re.compile(
        r"After TOPIC SEGMENTATION STABLE", re.IGNORECASE
    ),
    "old CLI identity": re.compile(r"SEMINARTEXT 3\.0", re.IGNORECASE),
}


def fail(message: str) -> None:
    raise ValueError(message)


def check(root: Path) -> list[str]:
    version_path = root / "SEMINARTEXT_VERSION"
    state_path = root / "SEMINARTEXT_4_STATE.json"
    roadmap_path = root / "SEMINARTEXT_4_ROADMAP.md"
    workflow_path = root / "DEVELOPMENT_WORKFLOW.md"
    mvp_path = root / "SEMINARTEXT_4_MVP_DEFINITION.md"
    cli_path = root / "seminartext"
    dataset_registry_path = root / "governance" / "dataset_registry.json"

    required_files = (
        version_path,
        state_path,
        roadmap_path,
        workflow_path,
        mvp_path,
        cli_path,
        dataset_registry_path,
    )
    for path in required_files:
        if not path.is_file():
            fail(f"required governance file missing: {path}")

    version = version_path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"4\.\d+\.\d+", version):
        fail(f"SEMINARTEXT_VERSION is not a SeminarText 4.x SemVer: {version!r}")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    missing_keys = sorted(REQUIRED_STATE_KEYS - state.keys())
    if missing_keys:
        fail(f"State missing required keys: {', '.join(missing_keys)}")
    if state["schema_version"] != EXPECTED_STATE_SCHEMA:
        fail(
            "unsupported State schema_version: "
            f"{state['schema_version']!r}; expected {EXPECTED_STATE_SCHEMA}"
        )
    if state["seminartext_version"] != version:
        fail(
            "version drift: State has "
            f"{state['seminartext_version']!r}, version file has {version!r}"
        )

    for key in ("current_stage", "current_milestone", "policy_checkpoint"):
        if not isinstance(state[key], str) or not state[key].strip():
            fail(f"State {key} must be a non-empty string")
    if not isinstance(state["next_actions"], list) or not state["next_actions"]:
        fail("State next_actions must be a non-empty list")

    tracks = state.get("architecture", {}).get("tracks", {})
    for name in ("semantic_automation", "knowledge_product", "data_evaluation"):
        track = tracks.get(name)
        if not isinstance(track, dict):
            fail(f"State architecture.tracks.{name} missing")
        for field in ("status", "purpose"):
            if not str(track.get(field, "")).strip():
                fail(f"State architecture.tracks.{name}.{field} missing")

    semantics = state["status_semantics"]
    for key in (
        "technical_evidence",
        "architecture_acceptance",
        "product_integration",
        "product_review",
        "production_stability",
    ):
        if key not in semantics:
            fail(f"State status_semantics.{key} missing")

    mvp = state["product_mvp"]
    if mvp.get("definition") != mvp_path.name:
        fail("State product_mvp.definition does not name the authoritative MVP DoD")
    if mvp.get("status") != "defined_not_yet_product_integrated":
        fail("State product_mvp.status must not imply completed product integration")

    registry = json.loads(dataset_registry_path.read_text(encoding="utf-8"))
    if registry.get("default_policy") != "DENY_UNREGISTERED":
        fail("Dataset Registry must use DENY_UNREGISTERED")
    datasets = {entry.get("id"): entry for entry in registry.get("datasets", [])}
    if list(datasets) != ["A", "B", "C", "D", "E", "F", "G1", "G2"]:
        fail("Dataset Registry must contain the governed A/B/C/D/E/F/G1/G2 matrix")
    expected_roles = {
        "A": state["stages"]["topic_benchmark_dataset_a"]["role"],
        "B": state["stages"]["dataset_b"]["role"],
        "C": state["stages"]["dataset_c"]["role"],
        "D": state["stages"]["dataset_d"]["role"],
        "E": state["stages"]["dataset_e"]["status"],
        "F": state["stages"]["dataset_f"]["role"],
    }
    for dataset_id, expected_role in expected_roles.items():
        if datasets[dataset_id].get("role") != expected_role:
            fail(f"Dataset {dataset_id} role drift between Registry and State")
    if datasets["D"].get("topic_engine_access_allowed") is not False:
        fail("Dataset D LOCKED_TEST firewall must deny Topic Engine access")
    if datasets["E"].get("role") != "EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE":
        fail("Dataset E exclusion policy drift")
    for dataset_id in ("G1", "G2"):
        if datasets[dataset_id].get("role_status") != "PROPOSAL_PENDING_PRODUCT_OWNER_ACCEPTANCE":
            fail(f"Dataset {dataset_id} role must remain a pending proposal")

    roadmap = roadmap_path.read_text(encoding="utf-8")
    workflow = workflow_path.read_text(encoding="utf-8")
    cli = cli_path.read_text(encoding="utf-8")
    for value in (state["policy_checkpoint"], *state["next_actions"]):
        if value not in roadmap:
            fail(f"Roadmap does not contain State value: {value}")
    for surface_name, surface in (("Roadmap", roadmap), ("Workflow", workflow)):
        if mvp_path.name not in surface:
            fail(f"{surface_name} does not link the authoritative MVP DoD")

    for label, pattern in OBSOLETE_ACTIVE_PATTERNS.items():
        for surface_name, surface in (("CLI", cli), ("Workflow", workflow)):
            if pattern.search(surface):
                fail(f"obsolete active surface ({label}) remains in {surface_name}")

    return [
        f"version={version}",
        f"state_schema={state['schema_version']}",
        f"checkpoint={state['policy_checkpoint']}",
        f"next_actions={len(state['next_actions'])}",
        "maturity_semantics=present",
        "mvp_definition=linked",
        "obsolete_active_gates=absent",
        "dataset_registry=consistent_fail_closed",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    try:
        evidence = check(args.root.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"GOVERNANCE CHECK: FAIL\n{exc}")
        return 1
    print("GOVERNANCE CHECK: PASS")
    for item in evidence:
        print(f"  {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
