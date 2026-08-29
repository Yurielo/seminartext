from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
FIXTURE = ROOT / "tests" / "fixtures" / "evidence_foundation"


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "Evidence fixture"
    shutil.copytree(FIXTURE, project)
    return project


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(CLI), *args], cwd=ROOT, text=True, capture_output=True)


def test_project_evidence_foundation_end_to_end(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    (project / "transcript" / "video_001").mkdir(parents=True)
    shutil.copy2(project / "transcript.txt", project / "transcript" / "video_001" / "transcript.txt")
    promoted = run_cli(
        "project-promote-transcript",
        str(project),
        "--source-id",
        "video_001",
        "--text-file",
        str(project / "transcript.txt"),
        "--state",
        "verified",
        "--reviewer",
        "qa-user",
    )
    assert promoted.returncode == 0, promoted.stderr
    revision_id = json.loads(promoted.stdout)["revision_id"]

    aligned = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_001",
        "--revision-id",
        revision_id,
        "--alignment-json",
        str(project / "alignment.json"),
        "--media",
        str(project / "source/video/source.mp4"),
    )
    assert aligned.returncode == 0, aligned.stderr
    result = json.loads(aligned.stdout)
    assert result["status"] == "verified"

    checked = run_cli("project-evidence-check", str(project), "--cross-record-only", "--json")
    assert checked.returncode == 0, checked.stderr + checked.stdout
    report = json.loads(checked.stdout)
    assert report["status"] == "PASS"
    bundle = json.loads((project / "evidence/canonical_bundle.json").read_text(encoding="utf-8"))
    assert bundle["transcript_revisions"][0]["authority"] == "authoritative"
    assert bundle["words"][0]["timing_provenance"]["alignment_run_id"]
    assert (project / "evidence/word_timeline.json").is_file()
    bindings = json.loads((project / "evidence/output_bindings.json").read_text(encoding="utf-8"))
    assert bindings["bindings"][0]["transcript_revision_id"] == revision_id

    resumed = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_001",
        "--revision-id",
        revision_id,
        "--alignment-json",
        str(project / "alignment.json"),
        "--media",
        str(project / "source/video/source.mp4"),
    )
    assert resumed.returncode == 0
    assert json.loads(resumed.stdout)["status"] == "RESUMED"


def test_unverified_revision_and_missing_media_fail_closed(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    promoted = run_cli(
        "project-promote-transcript",
        str(project),
        "--source-id",
        "video_001",
        "--text-file",
        str(project / "transcript.txt"),
        "--state",
        "provisional",
    )
    assert promoted.returncode == 0
    revision_id = json.loads(promoted.stdout)["revision_id"]
    blocked = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_001",
        "--revision-id",
        revision_id,
        "--alignment-json",
        str(project / "alignment.json"),
    )
    assert blocked.returncode == 1
    assert "authoritative verified" in blocked.stderr

    verified = run_cli(
        "project-promote-transcript",
        str(project),
        "--source-id",
        "video_001",
        "--text-file",
        str(project / "transcript.txt"),
        "--state",
        "verified",
        "--reviewer",
        "qa-user",
        "--parent-revision-id",
        revision_id,
    )
    assert verified.returncode == 0
    verified_id = json.loads(verified.stdout)["revision_id"]
    missing_media = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_001",
        "--revision-id",
        verified_id,
        "--alignment-json",
        str(project / "alignment.json"),
        "--media",
        str(project / "missing.mp4"),
    )
    assert missing_media.returncode == 1
    assert "media not found" in missing_media.stderr


def test_unaligned_word_has_null_timing_and_review_status(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    (project / "alignment.json").write_text(
        json.dumps(
            {
                "aligner": "fixture-alignment-service",
                "aligner_version": "1.0.0",
                "config": {"mode": "fixture", "no_asr": True},
                "model": "fixture-model",
                "model_revision": "fixture-revision",
                "model_sha256": "0" * 64,
                "words": [{"word": "Раз", "start": 0.1, "end": 0.3, "score": 1.0}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    promoted = run_cli(
        "project-promote-transcript",
        str(project),
        "--source-id",
        "video_001",
        "--text-file",
        str(project / "transcript.txt"),
        "--state",
        "verified",
        "--reviewer",
        "qa-user",
    )
    revision_id = json.loads(promoted.stdout)["revision_id"]
    aligned = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_001",
        "--revision-id",
        revision_id,
        "--alignment-json",
        str(project / "alignment.json"),
        "--media",
        str(project / "source/video/source.mp4"),
    )
    assert aligned.returncode == 0
    assert json.loads(aligned.stdout)["status"] == "review_required"
    bundle = json.loads((project / "evidence/canonical_bundle.json").read_text(encoding="utf-8"))
    assert bundle["words"][1]["alignment_status"] == "unaligned"
    assert bundle["words"][1]["start_seconds"] is None
    assert bundle["words"][1]["end_seconds"] is None
