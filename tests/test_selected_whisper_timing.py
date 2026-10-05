#!/usr/bin/env python3
"""Acceptance coverage for selected-attempt JSON-full timing (Issue #131)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
SCHEMA = ROOT / "schemas" / "selected_whisper_timing_v1.schema.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def install_tools(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "ffprobe",
        """#!/bin/bash
set -euo pipefail
input="${@: -1}"
case "$(basename "$input")" in
  chunk_0000.wav) printf '%s\n' "${MOCK_FIRST_DURATION:-300.000000}" ;;
  chunk_0001.wav) printf '42.500000\n' ;;
  *) printf '342.500000\n' ;;
esac
""",
    )
    write_executable(
        bin_dir / "ffmpeg",
        """#!/bin/bash
set -euo pipefail
out="${@: -1}"
mkdir -p "$(dirname "$out")"
if [[ "$out" == *chunk_%04d.wav ]]; then
  for ((i=0; i<${MOCK_CHUNKS:-1}; i++)); do
    printf -v chunk 'chunk_%04d.wav' "$i"
    printf 'chunk-%s\n' "$i" > "$(dirname "$out")/$chunk"
  done
else
  printf 'prepared-audio\n' > "$out"
fi
""",
    )
    write_executable(
        bin_dir / "whisper-cli",
        r"""#!/bin/bash
set -euo pipefail
printf '%s\n' "$*" >> "$MOCK_ARGS_LOG"
prefix=""
json_full=0
while (($#)); do
  case "$1" in
    -of) prefix="$2"; shift 2 ;;
    -ojf) json_full=1; shift ;;
    *) shift ;;
  esac
done
[[ -n "$prefix" ]]
count_file="$prefix.calls"
calls=0
[[ -f "$count_file" ]] && calls="$(cat "$count_file")"
calls=$((calls + 1))
printf '%s\n' "$calls" > "$count_file"
attempt="initial"
(( calls > 1 )) && attempt="retry"
part="$(basename "$prefix")"
json_end_ms="${MOCK_JSON_END_MS:-5000}"
srt_end="${MOCK_SRT_END:-00:00:05,000}"

if [[ "${MOCK_QUALITY_RETRY:-0}" == "1" && "$part" == "part_0000" && "$attempt" == "initial" ]]; then
  text="Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase. Loop phrase."
else
  text="$part accepted $attempt content with enough meaningful words for quality validation."
fi

printf '%s\n' "$text" > "$prefix.txt"
cat > "$prefix.srt" <<SRT
1
00:00:00,000 --> $srt_end
$text

SRT
if (( json_full == 1 )); then
  cat > "$prefix.json" <<JSON
{
  "attempt": "$attempt",
  "transcription": [
    {
      "text": "$text",
      "offsets": {"from": 0, "to": $json_end_ms},
      "tokens": [
        {"text": " $part", "offsets": {"from": 0, "to": $json_end_ms}, "p": 0.95}
      ]
    }
  ]
}
JSON
fi
""",
    )
    write_executable(
        bin_dir / "pandoc",
        """#!/bin/bash
set -euo pipefail
while (($#)); do
  if [[ "$1" == "-o" ]]; then : > "$2"; exit 0; fi
  shift
done
exit 2
""",
    )


def environment(tmp_path: Path, *, chunks: int, quality_retry: bool = False) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    install_tools(bin_dir)
    model = tmp_path / "model.bin"
    vad = tmp_path / "vad.bin"
    model.write_bytes(b"whisper-model")
    vad.write_bytes(b"vad-model")
    env = os.environ.copy()
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env["PATH"],
            "SEMINARTEXT_MODEL": str(model),
            "SEMINARTEXT_VAD_MODEL": str(vad),
            "SEMINARTEXT_OUTPUT": str(tmp_path / "output"),
            "SEMINARTEXT_OWNED_TMP_BASE": str(tmp_path),
            "SEMINARTEXT_HEADLESS": "1",
            "MOCK_ARGS_LOG": str(tmp_path / "whisper_args.log"),
            "MOCK_CHUNKS": str(chunks),
            "MOCK_QUALITY_RETRY": "1" if quality_retry else "0",
        }
    )
    return env


def run_transcribe(
    tmp_path: Path,
    env: dict[str, str],
    *,
    language: str = "ru",
    structured: bool = True,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    source = tmp_path / "lecture.mp4"
    source.write_bytes(b"source-media")
    command = [str(CLI), "transcribe", str(source), "--language", language]
    if structured:
        command.append("--structured-timing")
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    package = tmp_path / "output" / "lecture"
    timing = next(iter(package.glob("structured_timing*")), package / "missing")
    return result, package, timing


def load_manifest(timing: Path) -> dict:
    manifest = json.loads((timing / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(manifest)
    return manifest


def assert_artifact_hashes(timing: Path, manifest: dict) -> None:
    for part in manifest["parts"]:
        for artifact in part["artifacts"].values():
            path = timing / artifact["path"]
            assert path.is_file()
            assert artifact["sha256"] == sha256(path)


def selected_local_timing_range(timing: Path, part: dict) -> tuple[float, float] | None:
    """The published evidence envelope must contain every JSON/SRT timestamp."""
    starts: list[float] = []
    ends: list[float] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            offsets = value.get("offsets")
            if isinstance(offsets, dict):
                if isinstance(offsets.get("from"), (int, float)):
                    starts.append(float(offsets["from"]) / 1000)
                if isinstance(offsets.get("to"), (int, float)):
                    ends.append(float(offsets["to"]) / 1000)
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    json_path = timing / part["artifacts"]["json_full"]["path"]
    collect(json.loads(json_path.read_text(encoding="utf-8")))
    srt_path = timing / part["artifacts"]["srt"]["path"]
    for start, end in re.findall(
        r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
        srt_path.read_text(encoding="utf-8"),
    ):
        def seconds(value: str) -> float:
            hours, minutes, remainder = value.split(":")
            whole, millis = remainder.split(",")
            return int(hours) * 3600 + int(minutes) * 60 + int(whole) + int(millis) / 1000

        starts.append(seconds(start))
        ends.append(seconds(end))
    return (min(starts), max(ends)) if starts and ends else None


def assert_selected_timing_ranges_are_truthful(timing: Path, manifest: dict) -> None:
    for part in manifest["parts"]:
        local_range = selected_local_timing_range(timing, part)
        published = part["selected_timing_absolute_range"]
        if local_range is None:
            assert published is None
        else:
            assert published is not None
            assert published["start_seconds"] == part["absolute_offset_seconds"] + local_range[0]
            assert published["end_seconds"] == part["absolute_offset_seconds"] + local_range[1]


@pytest.mark.parametrize("language", ["ru", "en"])
def test_same_pass_initial_selection_publishes_ordered_json_full(tmp_path, language):
    env = environment(tmp_path, chunks=2)
    result, package, timing = run_transcribe(tmp_path, env, language=language)
    assert result.returncode == 0, result.stdout + result.stderr

    calls = (tmp_path / "whisper_args.log").read_text(encoding="utf-8").splitlines()
    assert len(calls) == 2
    assert all("-ojf" in call and f"-l {language}" in call for call in calls)

    manifest = load_manifest(timing)
    assert manifest["artifact_type"] == "seminartext.selected_whisper_timing"
    assert manifest["schema_version"] == 1
    assert manifest["transcription"]["language"] == language
    assert manifest["transcription"]["mode"] == "normal"
    assert manifest["source"]["media_sha256"] == sha256(tmp_path / "lecture.mp4")
    assert [part["order"] for part in manifest["parts"]] == [0, 1]
    assert [part["selected_attempt"] for part in manifest["parts"]] == ["initial", "initial"]
    assert [part["absolute_offset_seconds"] for part in manifest["parts"]] == [0.0, 300.0]
    assert [part["absolute_range"] for part in manifest["parts"]] == [
        {"start_seconds": 0.0, "end_seconds": 300.0},
        {"start_seconds": 300.0, "end_seconds": 342.5},
    ]
    assert [part["selected_timing_absolute_range"] for part in manifest["parts"]] == [
        {"start_seconds": 0.0, "end_seconds": 5.0},
        {"start_seconds": 300.0, "end_seconds": 305.0},
    ]
    assert_artifact_hashes(timing, manifest)
    assert_selected_timing_ranges_are_truthful(timing, manifest)
    assert not (package / ".parts").exists()
    assert not (package / ".chunks").exists()


def test_quality_retry_selects_matching_retry_trio_and_hides_rejected_json(tmp_path):
    env = environment(tmp_path, chunks=1, quality_retry=True)
    result, package, timing = run_transcribe(tmp_path, env, language="en")
    assert result.returncode == 0, result.stdout + result.stderr

    calls = (tmp_path / "whisper_args.log").read_text(encoding="utf-8").splitlines()
    assert len(calls) == 2
    assert "-ojf" in calls[0] and "-ojf" in calls[1]
    assert "-vt 0.55" in calls[0]
    assert "-vt 0.68" in calls[1]

    manifest = load_manifest(timing)
    assert len(manifest["parts"]) == 1
    part = manifest["parts"][0]
    assert part["selected_attempt"] == "retry"
    published = [
        (timing / artifact["path"]).read_text(encoding="utf-8")
        for artifact in part["artifacts"].values()
    ]
    assert all("accepted retry" in value or '"attempt": "retry"' in value for value in published)
    assert all("Loop phrase" not in value and '"attempt": "initial"' not in value for value in published)
    assert "exact_short_sentence_loop" in (package / "transcription.log").read_text(encoding="utf-8")
    assert_artifact_hashes(timing, manifest)
    assert_selected_timing_ranges_are_truthful(timing, manifest)


def test_selected_evidence_range_preserves_whisper_padding_past_prepared_audio(tmp_path):
    env = environment(tmp_path, chunks=1)
    # This mirrors the LED evidence: WAV/chunk duration is shorter than native
    # Whisper's final selected timing. Both facts must be published unchanged.
    env.update(
        {
            "MOCK_FIRST_DURATION": "56.449125",
            "MOCK_JSON_END_MS": "60000",
            "MOCK_SRT_END": "00:00:56,580",
        }
    )
    result, _package, timing = run_transcribe(tmp_path, env, language="en")
    assert result.returncode == 0, result.stdout + result.stderr

    manifest = load_manifest(timing)
    part = manifest["parts"][0]
    assert part["absolute_range"] == {"start_seconds": 0.0, "end_seconds": 56.449125}
    assert part["selected_timing_absolute_range"] == {
        "start_seconds": 0.0,
        "end_seconds": 60.0,
    }
    assert "accepted initial" in (timing / "parts" / "part_0000.txt").read_text(encoding="utf-8")
    assert_selected_timing_ranges_are_truthful(timing, manifest)


def test_without_opt_in_keeps_legacy_package_and_does_not_request_json_full(tmp_path):
    env = environment(tmp_path, chunks=1)
    result, package, timing = run_transcribe(tmp_path, env, language="ru", structured=False)
    assert result.returncode == 0, result.stdout + result.stderr
    call = (tmp_path / "whisper_args.log").read_text(encoding="utf-8")
    assert "-ojf" not in call
    assert not timing.exists()
    assert not list(package.glob("structured_timing*"))
    assert list(package.glob("transcript*.txt"))
    assert list(package.glob("transcript*.srt"))
