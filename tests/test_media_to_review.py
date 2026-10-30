import json
from pathlib import Path

import pytest

from seminartext_modules import media_to_review as intake


def write_manifest(tmp_path, media):
    project = tmp_path / "project"; project.mkdir()
    payload = {"artifact_type": intake.ARTIFACT, "schema_version": intake.VERSION,
               "entries": [{"id": "selected-source", "project": str(project), "source_id": "video_001", "media": str(media)}]}
    path = tmp_path / "manifest.json"; path.write_bytes(intake.review.canonical_bytes(payload)); return path


def test_explicit_media_is_bound_and_missing_alignment_stays_unavailable(tmp_path, monkeypatch):
    media = tmp_path / "sample.wav"; media.write_bytes(b"RIFF synthetic media")
    root = tmp_path / "intake"; path = write_manifest(tmp_path, media)
    prepared = intake.prepare(root, path)
    assert prepared["entries"][0]["status"] == "PENDING"
    monkeypatch.setattr(intake, "prerequisites", lambda: {"whisper_cli": True, "ffmpeg": True, "whisperx_3_8_6": False})
    result = intake.run(root)
    assert result["status"] == "ALIGNMENT_UNAVAILABLE"
    assert intake.latest(root)["entries"][0]["status"] == "ALIGNMENT_UNAVAILABLE"


def test_changed_media_or_invalid_manifest_fails_closed(tmp_path):
    media = tmp_path / "sample.wav"; media.write_bytes(b"first")
    root = tmp_path / "intake"; path = write_manifest(tmp_path, media); intake.prepare(root, path)
    media.write_bytes(b"changed")
    with pytest.raises(ValueError, match="selected media changed"):
        intake.run(root)
    bad = json.loads(path.read_bytes()); bad["entries"].append(bad["entries"][0])
    path.write_bytes(intake.review.canonical_bytes(bad))
    with pytest.raises(ValueError, match="duplicate"):
        intake.prepare(tmp_path / "other", path)
