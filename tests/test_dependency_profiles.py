"""Contract tests for the isolated dependency/model profiles."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from dependencies.check_profiles import check_model, check_ollama, load_contract, satisfies


ROOT = Path(__file__).resolve().parents[1]


def test_all_required_profiles_have_pinned_manifests_and_locks() -> None:
    contract = load_contract()
    assert set(contract["profiles"]) == {
        "core_product",
        "dev_test",
        "alignment_whisperx",
        "treeseg_topic_external",
    }
    for profile in contract["profiles"].values():
        requirements = ROOT / profile["requirements"]
        lock = ROOT / profile["lock"]
        assert requirements.is_file()
        assert lock.is_file()
        lines = [line.strip() for line in lock.read_text().splitlines() if line.strip() and not line.startswith("#")]
        assert lines
        assert all("==" in line or "@ git+" in line for line in lines)


def test_python_profile_boundaries_fail_safely() -> None:
    assert satisfies("3.13.15", ">=3.13,<3.14")
    assert not satisfies("3.14.6", ">=3.13,<3.14")
    assert not satisfies("3.13.15", ">=3.14,<3.15")


def test_alignment_model_mismatch_is_rejected(tmp_path: Path) -> None:
    candidate = tmp_path / "model.bin"
    candidate.write_bytes(b"not-the-pinned-model")
    result = check_model(str(candidate))
    assert result["status"] == "FAIL"
    assert "mismatch" in result["message"]


def test_ollama_digest_is_required(tmp_path: Path) -> None:
    payload = tmp_path / "ollama.json"
    payload.write_text(json.dumps({"digest": "sha256:wrong"}), encoding="utf-8")
    result = check_ollama(str(payload))
    assert result["status"] == "FAIL"
    assert "mismatched" in result["message"]


def test_jsonschema_is_declared_in_dev_profile() -> None:
    text = (ROOT / "requirements-dev.txt").read_text()
    assert "jsonschema==4.25.1" in text
    # This host's existing venv is intentionally not modified by the profile change.
    if importlib.util.find_spec("jsonschema") is None:
        assert "jsonschema" in text
