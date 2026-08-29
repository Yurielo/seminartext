from __future__ import annotations

import json
import re

from integrity.model import CheckContext, GateResult, gate_definition


def _pinned_lines(path):
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G4")
    contract_path = context.root / "dependencies" / "dependency_profiles.json"
    try:
        profiles = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return GateResult("G4", gate["name"], "FAIL", "dependency profile contract cannot be read", {"error": str(exc)})

    failures = []
    profile_evidence = []
    for name, profile in profiles.get("profiles", {}).items():
        requirements = context.root / profile["requirements"]
        lock = context.root / profile["lock"]
        lock_lines = _pinned_lines(lock) if lock.is_file() else []
        valid_pins = all("==" in line or "@ git+" in line for line in lock_lines)
        row = {
            "profile": name,
            "requirements": profile["requirements"],
            "lock": profile["lock"],
            "requirements_exists": requirements.is_file(),
            "lock_exists": lock.is_file(),
            "lock_entries": len(lock_lines),
            "all_lock_entries_pinned": valid_pins,
            "supported_python": profile.get("supported_python"),
        }
        profile_evidence.append(row)
        if not requirements.is_file() or not lock.is_file() or not lock_lines or not valid_pins:
            failures.append(name)

    models = profiles.get("models", {})
    alignment = models.get("russian_alignment", {})
    required_alignment = {"model_id", "revision", "sha256", "cache_root_env", "offline_env"}
    if not required_alignment.issubset(alignment):
        failures.append("russian_alignment_model_metadata")
    if not re.fullmatch(r"[0-9a-f]{64}", str(alignment.get("sha256", ""))):
        failures.append("russian_alignment_model_sha256")
    ollama = models.get("ollama_bge_m3", {})
    if not re.fullmatch(r"[0-9a-f]{64}", str(ollama.get("expected_digest", ""))):
        failures.append("ollama_bge_m3_digest")

    evidence = {
        "contract": "dependencies/dependency_profiles.json",
        "profiles": profile_evidence,
        "model_metadata": {
            "alignment_model": alignment.get("model_id"),
            "alignment_revision": alignment.get("revision"),
            "ollama_expected_digest": ollama.get("expected_digest"),
        },
    }
    if failures:
        return GateResult("G4", gate["name"], "FAIL", "dependency profile contract is incomplete: " + ", ".join(failures), evidence)
    return GateResult(
        "G4",
        gate["name"],
        "PASS",
        "isolated dependency manifests, locks, and model drift metadata are present",
        evidence,
    )
