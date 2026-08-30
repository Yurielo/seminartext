from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from schemas.validate_canonical_evidence_v1 import validate_bundle

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
FIXTURE = ROOT / "tests" / "fixtures" / "evidence_foundation"


def project(tmp_path: Path) -> Path:
    target = tmp_path / "Machine evidence fixture"
    shutil.copytree(FIXTURE, target)
    (target / "transcript" / "video_001").mkdir(parents=True)
    shutil.copy2(target / "transcript.txt", target / "transcript" / "video_001" / "transcript.txt")
    return target


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(CLI), *args], cwd=ROOT, text=True, capture_output=True)


def promote(p: Path, state: str = "review_required", text: Path | None = None, *extra: str) -> dict:
    result = run("project-promote-transcript", str(p), "--source-id", "video_001", "--text-file", str(text or p / "transcript.txt"), "--state", state, *extra)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_machine_revision_is_explicit_and_alignable_without_false_verification(tmp_path: Path) -> None:
    p = project(tmp_path)
    promoted = promote(p)
    provenance = promoted["transcript_provenance"]
    assert provenance == {
        "origin": "machine_generated",
        "method": "existing_machine_transcript_import",
        "verification_state": "machine_unverified",
        "verification_ranges": [],
        "reviewer": None,
    }
    aligned = run("project-align", str(p), "--source-id", "video_001", "--revision-id", promoted["revision_id"], "--alignment-json", str(p / "alignment.json"), "--media", str(p / "source/video/source.mp4"))
    assert aligned.returncode == 0, aligned.stderr
    bundle = json.loads((p / "evidence/canonical_bundle.json").read_text(encoding="utf-8"))
    revision = bundle["transcript_revisions"][0]
    assert revision["authority"] == "candidate"
    assert revision["lifecycle_status"] == "active"
    assert revision["transcript_provenance"]["verification_state"] == "machine_unverified"
    assert bundle["words"][0]["lifecycle_status"] == "active"
    assert json.loads(aligned.stdout)["status"] == "review_required"
    assert validate_bundle(bundle) == []
    drafts = {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.topic_drafts",
        "artifact_id": "topic_drafts_machine_fixture_v1",
        "project": {"id": bundle["project"]["id"], "title": bundle["project"]["title"]},
        "seminar": {"id": "seminar_machine_fixture", "title": "Machine fixture"},
        "generator": {"id": "generator_machine_fixture", "version": "1.0.0", "configuration_sha256": "a" * 64},
        "evidence": [{"id": "evidence_machine_fixture", "claim": "Machine evidence requires review.", "source_id": revision["source_id"], "transcript_revision_id": revision["id"], "word_start_id": bundle["words"][0]["id"], "word_end_id": bundle["words"][-1]["id"]}],
        "topics": [{"id": "topic_machine_fixture", "seminar_id": "seminar_machine_fixture", "source_id": revision["source_id"], "transcript_revision_id": revision["id"], "topic_set_id": "topic_set_machine_fixture", "sequence": 0, "word_start_id": bundle["words"][0]["id"], "word_end_id": bundle["words"][-1]["id"], "proposed_title": "Machine draft", "proposed_summary": "Must remain reviewable.", "evidence_refs": ["evidence_machine_fixture"], "semantic_origin": "machine_assisted", "lifecycle_status": "REVIEW_REQUIRED"}],
    }
    drafts_path = tmp_path / "machine_drafts.json"
    drafts_path.write_text(json.dumps(drafts, ensure_ascii=False), encoding="utf-8")
    prepared = run("project-review-prepare", str(p), "--drafts", str(drafts_path), "--output", str(tmp_path / "review"))
    assert prepared.returncode == 0, prepared.stderr
    assert json.loads((tmp_path / "review/review_package.json").read_text(encoding="utf-8"))["topics"][0]["lifecycle_status"] == "REVIEW_REQUIRED"
    assert "machine_unverified" in (tmp_path / "review/REVIEW.md").read_text(encoding="utf-8")


def test_selective_correction_preserves_parent_and_range(tmp_path: Path) -> None:
    p = project(tmp_path)
    parent = promote(p)
    corrected = tmp_path / "corrected.txt"
    corrected.write_text("Раз проверка!\n", encoding="utf-8")
    child = promote(p, "review_required", corrected, *(
        "--parent-revision-id", parent["revision_id"], "--reviewer", "human-reviewer",
        "--verification-state", "selectively_verified", "--verified-range", "0:12",
    ))
    assert child["transcript_provenance"]["origin"] == "human_corrected"
    assert child["transcript_provenance"]["verification_state"] == "selectively_verified"
    revision = json.loads((p / "evidence/transcript_revisions" / f"{child['revision_id']}.json").read_text(encoding="utf-8"))
    assert revision["parent_revision_id"] == parent["revision_id"]
    assert revision["authority"] == "candidate"
    assert revision["lifecycle_status"] == "active"


def test_selective_correction_outside_range_fails_closed(tmp_path: Path) -> None:
    p = project(tmp_path)
    parent = promote(p)
    corrected = tmp_path / "corrected.txt"
    corrected.write_text("Другая строка\n", encoding="utf-8")
    result = run("project-promote-transcript", str(p), "--source-id", "video_001", "--text-file", str(corrected), "--state", "review_required", "--parent-revision-id", parent["revision_id"], "--reviewer", "human-reviewer", "--verification-state", "selectively_verified", "--verified-range", "0:3")
    assert result.returncode == 1
    assert "outside" in result.stderr


def test_machine_revision_cannot_claim_full_human_verification_without_reviewer(tmp_path: Path) -> None:
    p = project(tmp_path)
    result = run("project-promote-transcript", str(p), "--source-id", "video_001", "--text-file", str(p / "transcript.txt"), "--state", "review_required", "--verification-state", "fully_human_verified")
    assert result.returncode == 1
    assert "reviewer" in result.stderr


def test_invalid_provenance_fails_validator(tmp_path: Path) -> None:
    p = project(tmp_path)
    promoted = promote(p)
    run("project-align", str(p), "--source-id", "video_001", "--revision-id", promoted["revision_id"], "--alignment-json", str(p / "alignment.json"), "--media", str(p / "source/video/source.mp4"))
    path = p / "evidence/canonical_bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["transcript_revisions"][0]["transcript_provenance"].pop("method")
    assert any("missing fields" in error for error in validate_bundle(bundle))


def test_legacy_schema_fixture_remains_valid() -> None:
    fixture = ROOT / "tests" / "fixtures" / "canonical_evidence_v1" / "valid_bundle.json"
    if fixture.is_file():
        assert validate_bundle(json.loads(fixture.read_text(encoding="utf-8"))) == []
