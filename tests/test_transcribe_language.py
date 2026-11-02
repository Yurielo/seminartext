#!/usr/bin/env python3
"""Acceptance coverage for explicit source language selection (Issue #129)."""

import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def install_tools(bin_dir: Path) -> None:
    write_executable(bin_dir / "ffprobe", "#!/bin/bash\nexit 0\n")
    write_executable(
        bin_dir / "ffmpeg",
        """#!/bin/bash
set -euo pipefail
out="${@: -1}"
mkdir -p "$(dirname "$out")"
if [[ "$out" == *chunk_%04d.wav ]]; then
  for ((i=0; i<${MOCK_CHUNKS:-1}; i++)); do
    printf -v chunk 'chunk_%04d.wav' "$i"
    : > "$(dirname "$out")/$chunk"
  done
else
  : > "$out"
fi
""",
    )
    write_executable(
        bin_dir / "whisper-cli",
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$*" >> "$MOCK_ARGS_LOG"
printf 'mock Whisper execution\n'
prefix=""
while (($#)); do
  if [[ "$1" == "-of" ]]; then prefix="$2"; break; fi
  shift
done
if [[ "${MOCK_FAIL_FIRST:-0}" == "1" && "$prefix" == *part_0000 && ! -e "$prefix.attempted" ]]; then
  : > "$prefix.attempted"
  exit 1
fi
printf '%s\n' "$MOCK_TEXT" > "$prefix.txt"
cat > "$prefix.srt" <<'SRT'
1
00:00:00,000 --> 00:00:05,000
because they save a lot of energy. The LED lights use less power.

SRT
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


def environment(tmp_path: Path, *, text: str, chunks: int = 1, fail_first: bool = False) -> dict:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    install_tools(bin_dir)
    model = tmp_path / "model.bin"
    vad = tmp_path / "vad.bin"
    model.write_bytes(b"model")
    vad.write_bytes(b"vad")
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
            "MOCK_TEXT": text,
            "MOCK_CHUNKS": str(chunks),
            "MOCK_FAIL_FIRST": "1" if fail_first else "0",
        }
    )
    return env


def run_transcribe(tmp_path: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    source = tmp_path / "lecture.mp4"
    source.write_bytes(b"media")
    return subprocess.run(
        [str(CLI), "transcribe", str(source), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("language_args", [(), ("--language", "ru")])
def test_default_and_explicit_russian_keep_language_and_prompt(tmp_path, language_args):
    env = environment(
        tmp_path,
        text="Это нормальная тестовая расшифровка русского семинара.",
    )
    result = run_transcribe(tmp_path, env, *language_args)
    assert result.returncode == 0, result.stdout + result.stderr
    call = (tmp_path / "whisper_args.log").read_text(encoding="utf-8")
    assert "-l ru" in call
    assert "--prompt Семинар на русском языке." in call
    info = (tmp_path / "output" / "lecture" / "info.txt").read_text(encoding="utf-8")
    assert "Язык источника: ru" in info


def test_english_uses_normal_chunk_retry_and_package_path_without_russian_prompt(tmp_path):
    critical = "because they save a lot of energy. The LED lights use less power."
    env = environment(
        tmp_path,
        text=f"Спасибо за внимание. {critical}",
        chunks=2,
        fail_first=True,
    )
    result = run_transcribe(tmp_path, env, "--language", "en")
    assert result.returncode == 0, result.stdout + result.stderr

    calls = (tmp_path / "whisper_args.log").read_text(encoding="utf-8").splitlines()
    assert len(calls) == 3
    assert all("-l en" in call for call in calls)
    assert all("--prompt" not in call for call in calls)
    assert all("--vad" in call and "-otxt" in call and "-osrt" in call for call in calls)
    assert "-vt 0.55" in calls[0]
    assert "-vt 0.68" in calls[1]

    package = tmp_path / "output" / "lecture"
    info = (package / "info.txt").read_text(encoding="utf-8")
    number = next(line.split(": ", 1)[1] for line in info.splitlines() if line.startswith("Номер расшифровки:"))
    expected = [
        package / f"transcript{number}.txt",
        package / f"transcript_clean{number}.txt",
        package / f"transcript_review{number}.txt",
        package / f"transcript{number}.srt",
        package / f"transcript{number}.docx",
        package / "info.txt",
        package / "transcription.log",
    ]
    assert all(path.is_file() for path in expected)
    assert "Язык источника: en" in info
    raw = expected[0].read_text(encoding="utf-8")
    clean = expected[1].read_text(encoding="utf-8")
    assert critical in raw and critical in clean
    assert "Спасибо за внимание" in clean


def test_unsupported_language_fails_before_transcription(tmp_path):
    env = environment(tmp_path, text="unused transcript text")
    result = run_transcribe(tmp_path, env, "--language", "fr")
    assert result.returncode == 2
    assert "неподдерживаемый язык 'fr'" in result.stderr
    assert not (tmp_path / "whisper_args.log").exists()


@pytest.mark.parametrize("language", ["ru", "en"])
def test_reuse_preserves_package_and_force_starts_new_log(tmp_path, language):
    env = environment(tmp_path, text="Это достаточно длинная проверочная расшифровка записи.")
    first = run_transcribe(tmp_path, env, "--language", language)
    assert first.returncode == 0, first.stdout + first.stderr
    package = tmp_path / "output" / "lecture"
    log = package / "transcription.log"
    assert b"mock Whisper execution" in log.read_bytes()
    log.write_bytes(log.read_bytes() + b"original diagnostic sentinel\n")
    before = {p.name: p.read_bytes() for p in package.iterdir() if p.is_file()}
    calls = (tmp_path / "whisper_args.log").read_bytes()
    reused = run_transcribe(tmp_path, env, "--language", language)
    assert reused.returncode == 0, reused.stdout + reused.stderr
    assert "Пропущено (уже готово)" in reused.stdout
    assert (tmp_path / "whisper_args.log").read_bytes() == calls
    assert {p.name: p.read_bytes() for p in package.iterdir() if p.is_file()} == before
    forced = run_transcribe(tmp_path, env, "--language", language, "--force")
    assert forced.returncode == 0, forced.stdout + forced.stderr
    assert len((tmp_path / "whisper_args.log").read_text().splitlines()) == 2
    assert b"mock Whisper execution" in log.read_bytes()
    assert b"original diagnostic sentinel" not in log.read_bytes()
