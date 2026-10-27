"""Deterministic identity and artifact-integrity regressions for Issue #147."""

import hashlib
import json
from pathlib import Path

import pytest

from seminartext_modules.asr_completion import (
    build_configuration,
    sha256_file,
    verify_completion,
    write_completion,
)


def _fixture(tmp_path: Path, *, structured_timing: bool = False):
    project = tmp_path / "project"
    transcript = project / "transcript" / "video_001"
    transcript.mkdir(parents=True)
    source_file = project / "source.mp4"
    source_file.write_bytes(b"AAAA")
    model = tmp_path / "model.bin"
    model.write_bytes(b"model-v1")
    vad = tmp_path / "vad.bin"
    vad.write_bytes(b"vad-v1")
    whisper = tmp_path / "whisper-cli"
    whisper.write_bytes(b"whisper-runtime-v1")
    producer = tmp_path / "seminartext"
    producer.write_bytes(b"producer-v1")
    for name, content in (
        ("transcript.txt", b"raw transcript\n"),
        ("transcript_clean.txt", b"clean transcript\n"),
        ("transcript_review.txt", b"review\n"),
        ("transcript.srt", b"1\n00:00:00,000 --> 00:00:01,000\ntext\n"),
    ):
        (transcript / name).write_bytes(content)
    (project / "transcript" / "video_001.json").write_text("{}\n", encoding="utf-8")
    source = {
        "source_id": "video_001",
        "type": "project-local",
        "reference": str(source_file.resolve()),
        "sha256": sha256_file(source_file),
        "source_manifest_identity_sha256": hashlib.sha256(b"source-record-v1").hexdigest(),
    }
    configuration = build_configuration(
        language="ru",
        mode="normal",
        chunk_seconds=300,
        model_path=model,
        vad_model_path=vad,
        whisper_path=whisper,
        producer_path=producer,
        producer_version="4.0.0",
        whisper_threads=4,
        structured_timing=structured_timing,
    )
    return project, transcript, source_file, source, configuration, model, vad, whisper, producer


def _write_timing(project: Path, source: dict, configuration: dict, attempts: list[str]) -> None:
    timing = project / "transcript" / "video_001" / "structured_timing"
    parts_dir = timing / "parts"
    parts_dir.mkdir(parents=True)
    parts = []
    for index, attempt in enumerate(attempts):
        part_id = f"part_{index:04d}"
        artifacts = {}
        for kind, extension in (("txt", "txt"), ("srt", "srt"), ("json_full", "json")):
            relative = f"parts/{part_id}.{extension}"
            artifact = parts_dir / f"{part_id}.{extension}"
            artifact.write_text(f"{part_id} {kind}\n", encoding="utf-8")
            artifacts[kind] = {"path": relative, "sha256": sha256_file(artifact)}
        parts.append({
            "id": part_id,
            "order": index,
            "selected_attempt": attempt,
            "artifacts": artifacts,
        })
    reference = source["reference"]
    manifest = {
        "schema_version": 1,
        "artifact_type": "seminartext.selected_whisper_timing",
        "source": {
            "type": source["type"],
            "reference": reference,
            "reference_sha256": hashlib.sha256(reference.encode("utf-8")).hexdigest(),
            "media_sha256": source["sha256"],
        },
        "transcription": {
            "language": configuration["language"],
            "mode": configuration["mode"],
            "chunk_seconds": configuration["chunk_seconds"],
            "whisper_model": configuration["whisper_model"],
            "vad_model": configuration["vad_model"],
        },
        "parts": parts,
    }
    (timing / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_versioned_compatible_source_reuses_only_with_complete_artifact_hashes(tmp_path):
    project, _, _, source, config, *_ = _fixture(tmp_path)
    write_completion(project, source["source_id"], source, config)

    assert verify_completion(project, source["source_id"], source, config) == (
        True,
        "compatible validated completion",
    )


def test_changed_source_bytes_at_same_path_size_and_mtime_reject_completion(tmp_path):
    project, _, source_file, source, config, *_ = _fixture(tmp_path)
    write_completion(project, source["source_id"], source, config)
    previous_stat = source_file.stat()
    source_file.write_bytes(b"BBBB")
    source_file.touch()
    import os

    os.utime(source_file, ns=(previous_stat.st_atime_ns, previous_stat.st_mtime_ns))
    changed = {**source, "sha256": sha256_file(source_file)}

    assert source_file.stat().st_size == previous_stat.st_size
    assert source_file.stat().st_mtime_ns == previous_stat.st_mtime_ns
    assert verify_completion(project, source["source_id"], changed, config)[0] is False


@pytest.mark.parametrize("field,value", [("language", "en"), ("mode", "careful"), ("chunk_seconds", 120)])
def test_asr_language_and_effective_configuration_changes_reject_completion(tmp_path, field, value):
    project, _, _, source, config, *_ = _fixture(tmp_path)
    write_completion(project, source["source_id"], source, config)
    changed = {**config, field: value}

    assert verify_completion(project, source["source_id"], source, changed)[0] is False


@pytest.mark.parametrize("asset_index", [5, 6, 7, 8])
def test_model_vad_runtime_and_producer_byte_changes_reject_completion(tmp_path, asset_index):
    project, _, _, source, config, *assets = _fixture(tmp_path)
    write_completion(project, source["source_id"], source, config)
    assets[asset_index - 5].write_bytes(b"changed bytes")
    model, vad, whisper, producer = assets
    changed = build_configuration(
        language="ru", mode="normal", chunk_seconds=300,
        model_path=model, vad_model_path=vad, whisper_path=whisper,
        producer_path=producer, producer_version="4.0.0", whisper_threads=4,
        structured_timing=False,
    )

    assert verify_completion(project, source["source_id"], source, changed)[0] is False


@pytest.mark.parametrize(
    "relative",
    [
        "transcript/video_001/transcript.txt",
        "transcript/video_001/transcript_clean.txt",
        "transcript/video_001/transcript_review.txt",
        "transcript/video_001/transcript.srt",
    ],
)
def test_tampered_selected_artifact_rejects_or_requires_safe_rebuild(tmp_path, relative):
    project, _, _, source, config, *_ = _fixture(tmp_path)
    write_completion(project, source["source_id"], source, config)
    (project / relative).write_bytes(b"tampered")

    compatible, reason = verify_completion(project, source["source_id"], source, config)
    if relative.endswith(("transcript_clean.txt", "transcript_review.txt")):
        assert compatible is True and "deterministic rebuild" in reason
    else:
        assert compatible is False


def test_missing_or_tampered_derived_json_allows_safe_rebuild_from_selected_srt(tmp_path):
    project, _, _, source, config, *_ = _fixture(tmp_path)
    write_completion(project, source["source_id"], source, config)
    json_path = project / "transcript/video_001.json"
    json_path.write_text("tampered", encoding="utf-8")

    compatible, reason = verify_completion(project, source["source_id"], source, config)
    assert compatible is True
    assert "transcript/video_001.json" in reason
    json_path.unlink()
    compatible, reason = verify_completion(project, source["source_id"], source, config)
    assert compatible is True
    assert "transcript/video_001.json" in reason


def test_unknown_legacy_marker_is_not_trusted_but_project_files_remain_readable(tmp_path):
    project, transcript, _, source, config, *_ = _fixture(tmp_path)
    (transcript / ".seminartext_complete").touch()

    assert verify_completion(project, source["source_id"], source, config)[0] is False
    assert (transcript / "transcript_clean.txt").read_text(encoding="utf-8") == "clean transcript\n"


def test_failed_or_partial_artifact_bundle_cannot_be_published_complete(tmp_path):
    project, transcript, _, source, config, *_ = _fixture(tmp_path)
    (transcript / "transcript.srt").unlink()

    with pytest.raises(ValueError, match="required artifact is missing"):
        write_completion(project, source["source_id"], source, config)
    assert not (transcript / ".seminartext_complete").exists()


def test_selected_timing_manifest_binds_all_parts_and_selected_attempts(tmp_path):
    project, _, _, source, config, *_ = _fixture(tmp_path, structured_timing=True)
    _write_timing(project, source, config, ["initial", "retry"])
    write_completion(project, source["source_id"], source, config)

    assert verify_completion(project, source["source_id"], source, config)[0] is True
    identity = json.loads((project / "transcript/video_001/.seminartext_completion.json").read_text())
    assert identity["selected_attempts"] == [
        {"part_id": "part_0000", "order": 0, "selected_attempt": "initial"},
        {"part_id": "part_0001", "order": 1, "selected_attempt": "retry"},
    ]
    selected_json = project / "transcript/video_001/structured_timing/parts/part_0001.json"
    selected_json.write_text("tampered", encoding="utf-8")
    assert verify_completion(project, source["source_id"], source, config)[0] is False
