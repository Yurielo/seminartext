#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def run_project(careful: bool) -> tuple[subprocess.CompletedProcess[str], str, str]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        project = root / "project"
        project.mkdir()
        source = project / "source.mp4"
        source.write_bytes(b"video")
        (project / "sources.json").write_text(json.dumps({"schema_version": 1, "videos": [{"source_id": "video_001", "order": 1, "type": "local", "file": "source.mp4"}], "documents": []}) + "\n", encoding="utf-8")
        model = root / "model.bin"
        vad = root / "vad.bin"
        model.write_bytes(b"model")
        vad.write_bytes(b"vad")
        args_log = root / "whisper_args.log"
        bin_dir = root / "bin"
        bin_dir.mkdir()
        write_executable(bin_dir / "ffprobe", "#!/bin/bash\nexit 0\n")
        write_executable(bin_dir / "ffmpeg", "#!/bin/bash\nset -euo pipefail\nout=\"${@: -1}\"\nmkdir -p \"$(dirname \"$out\")\"\nif [[ \"$out\" == *chunk_%04d.wav ]]; then : > \"${out/chunk_%04d.wav/chunk_0000.wav}\"; else : > \"$out\"; fi\n")
        write_executable(bin_dir / "whisper-cli", f"#!/bin/bash\nset -euo pipefail\nprintf '%s\\n' \"$*\" >> \"{args_log}\"\nprefix=\"\"\nwhile (($#)); do\n  if [[ \"$1\" == \"-of\" ]]; then prefix=\"$2\"; break; fi\n  shift\ndone\nmkdir -p \"$(dirname \"$prefix\")\"\nprintf '%s\\n' 'Достаточно длинная тестовая расшифровка для проверки параметров режима.' > \"$prefix.txt\"\nprintf '%s\\n' '1' '00:00:00,000 --> 00:00:01,000' 'Тестовая расшифровка.' > \"$prefix.srt\"\n")
        env = os.environ.copy()
        env.update({"PATH": str(bin_dir) + os.pathsep + env["PATH"], "SEMINARTEXT_MODEL": str(model), "SEMINARTEXT_VAD_MODEL": str(vad), "SEMINARTEXT_HEADLESS": "1"})
        command = [str(CLI), "project-transcribe", str(project), "--only", "video_001"]
        if careful:
            command.append("--careful")
        result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
        info = (project / "transcript" / "video_001" / "info.txt").read_text(encoding="utf-8")
        return result, args_log.read_text(encoding="utf-8"), info


def test_project_transcribe_accepts_careful_and_uses_existing_careful_parameters():
    result, call, info = run_project(careful=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "-bo 8" in call and "-bs 8" in call
    assert "-vt 0.45" in call and "-vsd 700" in call
    assert "Режим: careful" in info


def test_project_transcribe_normal_mode_is_unchanged():
    result, call, info = run_project(careful=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "-bo 5" in call and "-bs 5" in call
    assert "-vt 0.55" in call and "-vsd 550" in call
    assert "Режим: normal" in info


if __name__ == "__main__":
    test_project_transcribe_accepts_careful_and_uses_existing_careful_parameters()
    test_project_transcribe_normal_mode_is_unchanged()
    print("project-transcribe careful mode regression tests passed")
