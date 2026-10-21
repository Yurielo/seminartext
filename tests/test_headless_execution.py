#!/usr/bin/env python3
"""Production-level GUI-side-effect coverage for Issue #138."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"

def executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)

def environment(root: Path, bin_dir: Path, *, headless: bool) -> dict:
    model, vad = root / "model.bin", root / "vad.bin"
    model.write_bytes(b"model")
    vad.write_bytes(b"vad")
    env = os.environ.copy()
    for key in ("CI", "PYTEST_CURRENT_TEST", "CODEX_HOME", "SEMINARTEXT_HEADLESS"):
        env.pop(key, None)
    env.update({
        "PATH": str(bin_dir) + os.pathsep + env["PATH"],
        "SEMINARTEXT_MODEL": str(model), "SEMINARTEXT_VAD_MODEL": str(vad),
        "SEMINARTEXT_OUTPUT": str(root / "output"),
        "SEMINARTEXT_OPEN_LOG": str(root / "open.log"),
    })
    if headless:
        env["SEMINARTEXT_HEADLESS"] = "1"
    return env

def install_tools(bin_dir: Path) -> None:
    executable(bin_dir / "open", "#!/bin/bash\nprintf '%s\\n' \"$*\" >> \"$SEMINARTEXT_OPEN_LOG\"\n")
    executable(bin_dir / "ffprobe", "#!/bin/bash\nexit 0\n")
    executable(bin_dir / "ffmpeg", """#!/bin/bash
set -euo pipefail
out="${@: -1}"
mkdir -p "$(dirname "$out")"
if [[ "$out" == *chunk_%04d.wav ]]; then
  : > "${out/chunk_%04d.wav/chunk_0000.wav}"
else
  : > "$out"
fi
""")
    executable(bin_dir / "whisper-cli", """#!/bin/bash
set -euo pipefail
while (($#)); do
  if [[ "$1" == "-of" ]]; then prefix="$2"; break; fi
  shift
done
mkdir -p "$(dirname "$prefix")"
printf 'Тестовая расшифровка без GUI.\\n' > "$prefix.txt"
printf '1\\n00:00:00,000 --> 00:00:01,000\\nТестовая расшифровка без GUI.\\n' > "$prefix.srt"
""")

def test_headless_normal_transcribe_never_calls_open_and_interactive_retains_open():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_tools(bin_dir)
        media = root / "lecture.mp4"
        media.write_bytes(b"media")
        headless = subprocess.run([str(CLI), "transcribe", str(media)], text=True, capture_output=True, env=environment(root, bin_dir, headless=True), cwd=ROOT)
        assert headless.returncode == 0, headless.stdout + headless.stderr
        assert not (root / "open.log").exists()
        interactive_root = root / "interactive"
        interactive_root.mkdir()
        interactive = subprocess.run([str(CLI), "transcribe", str(media)], text=True, capture_output=True, env=environment(interactive_root, bin_dir, headless=False), cwd=ROOT)
        assert interactive.returncode == 0, interactive.stdout + interactive.stderr
        assert (interactive_root / "open.log").read_text(encoding="utf-8").strip()

def test_ci_like_project_combined_clear_accepts_no_open_without_gui():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_tools(bin_dir)
        project = root / "project"
        project.mkdir()
        (project / "part.mp4").write_bytes(b"media")
        (project / "sources.json").write_text(json.dumps({"schema_version": 1, "videos": [{"source_id": "part", "type": "local", "file": "part.mp4", "order": 1}], "documents": []}), encoding="utf-8")
        transcript = project / "transcript" / "part"
        transcript.mkdir(parents=True)
        (transcript / ".seminartext_complete").touch()
        (transcript / "transcript_clean.txt").write_text("Готовый текст.", encoding="utf-8")
        (transcript / "transcript.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nГотовый текст.\n", encoding="utf-8")
        env = environment(root, bin_dir, headless=False)
        env["CI"] = "true"
        result = subprocess.run([str(CLI), "project-transcribe", str(project), "--combined-clear", "--no-open"], text=True, capture_output=True, env=env, cwd=ROOT)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (project / "transcript" / "combined_clear.txt").is_file()
        assert not (root / "open.log").exists()

if __name__ == "__main__":
    test_headless_normal_transcribe_never_calls_open_and_interactive_retains_open()
    test_ci_like_project_combined_clear_accepts_no_open_without_gui()
    print("headless execution regression tests passed")
