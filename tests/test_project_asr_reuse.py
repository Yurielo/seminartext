"""End-to-end project reuse checks with deterministic media/tool fixtures."""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"


def _executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _fixture(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _executable(bin_dir / "ffprobe", '''#!/bin/bash
if [[ "$*" == *"format=duration"* ]]; then echo 1.0; else echo '{"format":{"tags":{}}}'; fi
''')
    _executable(bin_dir / "ffmpeg", '''#!/bin/bash
set -euo pipefail
out="${@: -1}"
mkdir -p "$(dirname "$out")"
if [[ "$out" == *chunk_%04d.wav ]]; then : > "${out/chunk_%04d.wav/chunk_0000.wav}"; else : > "$out"; fi
''')
    log = tmp_path / "whisper_calls.log"
    _executable(bin_dir / "whisper-cli", '''#!/bin/bash
set -euo pipefail
printf '%s\\n' "$*" >> "$MOCK_WHISPER_LOG"
if [[ "${MOCK_CANCEL:-0}" == "1" ]]; then exit 130; fi
prefix=""
json=0
while (($#)); do
  [[ "$1" == "-ojf" ]] && json=1
  if [[ "$1" == "-of" ]]; then prefix="$2"; break; fi
  shift
done
printf '%s\\n' "$MOCK_TEXT" > "$prefix.txt"
cat > "$prefix.srt" <<SRT
1
00:00:00,000 --> 00:00:01,000
$MOCK_TEXT

SRT
if (( json == 1 )); then printf '{"offsets":{"from":0,"to":1000}}\\n' > "$prefix.json"; fi
''')
    model = tmp_path / "model.bin"
    model.write_bytes(b"model-v1")
    vad = tmp_path / "vad.bin"
    vad.write_bytes(b"vad-v1")
    project = tmp_path / "project"
    source_dir = project / "source" / "video"
    source_dir.mkdir(parents=True)
    source = source_dir / "lecture.mp4"
    source.write_bytes(b"AAAA")
    (project / "sources.json").write_text(json.dumps({
        "schema_version": 1,
        "videos": [{"source_id": "video_001", "order": 1, "type": "local",
                    "file": "source/video/lecture.mp4", "title": "Lecture"}],
        "documents": [],
    }), encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "PATH": str(bin_dir) + os.pathsep + env.get("PATH", ""),
        "SEMINARTEXT_MODEL": str(model),
        "SEMINARTEXT_VAD_MODEL": str(vad),
        "SEMINARTEXT_HEADLESS": "1",
        "SEMINARTEXT_OWNED_TMP_BASE": str(tmp_path),
        "MOCK_WHISPER_LOG": str(log),
        "MOCK_TEXT": "Recognized fixture transcript. More words for a stable result.",
    })
    return project, source, env, log


def _run(project: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(CLI), "project-transcribe", str(project), "--only", "video_001", *args],
        text=True,
        capture_output=True,
        env=env,
    )


def _calls(log: Path) -> int:
    return len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0


def test_unchanged_compatible_local_source_reuses_without_whisper(tmp_path):
    project, _, env, log = _fixture(tmp_path)
    first = _run(project, env)
    assert first.returncode == 0, first.stdout + first.stderr
    assert _calls(log) == 1

    second = _run(project, env)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "Переиспользую проверенную расшифровку" in second.stdout
    assert _calls(log) == 1


def test_same_path_same_size_and_mtime_with_changed_bytes_retranscribes(tmp_path):
    project, source, env, log = _fixture(tmp_path)
    first = _run(project, env)
    assert first.returncode == 0, first.stdout + first.stderr
    before = source.stat()
    source.write_bytes(b"BBBB")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    env["MOCK_TEXT"] = "Changed source transcript. More words for the fixture."

    second = _run(project, env)
    assert second.returncode == 0, second.stdout + second.stderr
    assert _calls(log) == 2
    assert "Changed source transcript" in (project / "transcript/video_001/transcript_clean.txt").read_text()


@pytest.mark.parametrize("relative", [
    "transcript/video_001/transcript.txt",
    "transcript/video_001/transcript_clean.txt",
    "transcript/video_001/transcript.srt",
    "transcript/video_001.json",
])
def test_missing_selected_project_artifact_invalidates_completion(tmp_path, relative):
    project, _, env, log = _fixture(tmp_path)
    assert _run(project, env).returncode == 0
    (project / relative).unlink()

    result = _run(project, env)
    assert result.returncode == 0, result.stdout + result.stderr
    rebuildable = relative.endswith("transcript_clean.txt") or relative.endswith("transcript_review.txt") or relative.endswith("video_001.json")
    assert _calls(log) == (1 if rebuildable else 2)
    assert (project / relative).is_file()


def test_partial_failed_and_cancelled_attempts_do_not_publish_completion(tmp_path):
    project, _, env, log = _fixture(tmp_path)
    env["MOCK_CANCEL"] = "1"

    result = _run(project, env)
    assert result.returncode != 0
    transcript = project / "transcript/video_001"
    assert not (transcript / ".seminartext_complete").exists()
    assert not (transcript / ".seminartext_completion.json").exists()
    assert _calls(log) >= 1


def test_selected_timing_artifact_tamper_invalidates_and_rebuilds(tmp_path):
    project, _, env, log = _fixture(tmp_path)
    first = _run(project, env, "--structured-timing")
    assert first.returncode == 0, first.stdout + first.stderr
    selected_json = project / "transcript/video_001/structured_timing/parts/part_0000.json"
    selected_json.write_text("tampered", encoding="utf-8")

    second = _run(project, env, "--structured-timing")
    assert second.returncode == 0, second.stdout + second.stderr
    assert _calls(log) == 2
    assert json.loads(selected_json.read_text(encoding="utf-8"))["offsets"]["to"] == 1000


def test_failed_retranscription_restores_previous_readable_artifacts(tmp_path):
    project, source, env, log = _fixture(tmp_path)
    assert _run(project, env).returncode == 0
    transcript = project / "transcript/video_001"
    old_text = (transcript / "transcript.txt").read_bytes()
    old_identity = (transcript / ".seminartext_completion.json").read_bytes()
    source.write_bytes(b"BBBB")
    env["MOCK_CANCEL"] = "1"

    failed = _run(project, env)
    assert failed.returncode != 0
    assert _calls(log) >= 2
    assert (transcript / "transcript.txt").read_bytes() == old_text
    assert (transcript / ".seminartext_completion.json").read_bytes() == old_identity
    # The restored marker describes the old bytes, so it cannot certify this source.
    env.pop("MOCK_CANCEL")
    rerun = _run(project, env)
    assert rerun.returncode == 0, rerun.stdout + rerun.stderr
    assert "Переиспользую проверенную расшифровку" not in rerun.stdout


def test_failed_retry_preserves_partial_project_without_marker(tmp_path):
    project, _, env, _ = _fixture(tmp_path)
    transcript = project / "transcript/video_001"
    transcript.mkdir(parents=True)
    prior = b"partial user transcript\n"
    (transcript / "transcript.txt").write_bytes(prior)
    env["MOCK_CANCEL"] = "1"

    failed = _run(project, env)
    assert failed.returncode != 0
    assert (transcript / "transcript.txt").read_bytes() == prior
    assert not (transcript / ".seminartext_complete").exists()


def test_source_change_between_verify_and_pending_cannot_certify_old_text(tmp_path):
    project, source, env, log = _fixture(tmp_path)
    assert _run(project, env).returncode == 0
    wrapper = tmp_path / "bin" / "python3"
    _executable(wrapper, "#!/bin/bash\n" +
        f"{shlex.quote(sys.executable)} \"$@\"\nstatus=$?\n" +
        'if [[ "${3:-}" == "verify" && "$status" == "0" ]]; then printf BBBB > "$MOCK_SOURCE_PATH"; fi\n' +
        'exit "$status"\n')
    env["MOCK_SOURCE_PATH"] = str(source)

    interrupted = _run(project, env)
    assert interrupted.returncode != 0
    assert source.read_bytes() == b"BBBB"
    assert _calls(log) == 1

    retry = _run(project, env)
    assert retry.returncode == 0, retry.stdout + retry.stderr
    assert "Переиспользую проверенную расшифровку" not in retry.stdout
    assert _calls(log) == 2
