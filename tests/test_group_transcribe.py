#!/usr/bin/env python3
"""Regression coverage for mixed file/directory group transcription."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "seminartext"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def install_mocks(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "ffmpeg",
        """#!/usr/bin/env python3
import sys
from pathlib import Path
args = sys.argv[1:]
target = Path(args[-1])
if "segment" in args:
    target.parent.mkdir(parents=True, exist_ok=True)
    Path(str(target).replace("%04d", "0000")).write_bytes(b"chunk")
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"audio")
""",
    )
    write_executable(
        bin_dir / "whisper-cli",
        """#!/usr/bin/env python3
import sys
from pathlib import Path
args = sys.argv[1:]
prefix = Path(args[args.index("-of") + 1])
print("mock Whisper execution")
prefix.parent.mkdir(parents=True, exist_ok=True)
text = "Это проверочная машинная расшифровка выбранной записи."
prefix.with_suffix(".txt").write_text(text + "\\n", encoding="utf-8")
prefix.with_suffix(".srt").write_text(
    "1\\n00:00:00,000 --> 00:00:01,000\\n" + text + "\\n", encoding="utf-8"
)
""",
    )
    write_executable(
        bin_dir / "ffprobe",
        "#!/usr/bin/env python3\nprint('{\"format\": {\"tags\": {}}}')\n",
    )
    write_executable(bin_dir / "stat", "#!/usr/bin/env python3\nprint(0)\n")


def environment(root: Path, bin_dir: Path) -> dict:
    model = root / "model.bin"
    vad = root / "vad.bin"
    model.write_bytes(b"model")
    vad.write_bytes(b"vad")
    env = os.environ.copy()
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env["PATH"],
            "SEMINARTEXT_MODEL": str(model),
            "SEMINARTEXT_VAD_MODEL": str(vad),
            "SEMINARTEXT_HEADLESS": "1",
        }
    )
    return env


def run(env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(SCRIPT), "group", *args], text=True, capture_output=True, env=env)


def test_group_accepts_directories_and_files_deduplicates_by_content_and_reuses_group():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_mocks(bin_dir)
        media_dir = root / "media"
        nested = media_dir / "nested"
        nested.mkdir(parents=True)
        first = media_dir / "first.ogg"
        same_content = nested / "copy.mp4"
        selected = root / "selected.m4a"
        first.write_bytes(b"same media")
        same_content.write_bytes(b"same media")
        selected.write_bytes(b"different media")
        group = root / "result group"
        env = environment(root, bin_dir)

        preview = run(env, str(media_dir), str(selected), "--output", str(group), "--list")
        assert preview.returncode == 0, preview.stdout + preview.stderr
        assert "Новых уникальных: 2" in preview.stdout
        assert "Повторов: 1" in preview.stdout
        assert not group.exists()

        first_run = run(env, str(media_dir), str(selected), "--output", str(group))
        assert first_run.returncode == 0, first_run.stdout + first_run.stderr
        sources = json.loads((group / "sources.json").read_text(encoding="utf-8"))
        assert len(sources["videos"]) == 2
        assert all((group / item["file"]).is_symlink() for item in sources["videos"])

        transcript = group / "transcript"
        clean = transcript / "combined_clear.txt"
        with_sources = transcript / "combined_clear_with_sources.txt"
        manifest = transcript / "combined_clear_manifest.json"
        assert clean.is_file() and with_sources.is_file() and manifest.is_file()
        assert clean.read_text(encoding="utf-8").count("Это проверочная") == 2
        assert with_sources.read_text(encoding="utf-8").count("=====") == 4
        assert len(json.loads(manifest.read_text(encoding="utf-8"))["sources"]) == 2

        logs = [transcript / item["source_id"] / "transcription.log" for item in sources["videos"]]
        logs_before = {p: p.read_bytes() for p in logs}
        assert all(b"mock Whisper execution" in value for value in logs_before.values())

        second_run = run(env, str(media_dir), str(selected), "--output", str(group))
        assert second_run.returncode == 0, second_run.stdout + second_run.stderr
        sources_after = json.loads((group / "sources.json").read_text(encoding="utf-8"))
        assert sources_after == sources
        assert {p: p.read_bytes() for p in logs} == logs_before
        assert second_run.stdout.count("Переиспользую проверенную расшифровку") == 2
        assert "mock Whisper execution" not in second_run.stdout
        for path in logs:
            path.write_bytes(path.read_bytes() + b"previous run sentinel\n")
        forced = run(env, str(media_dir), str(selected), "--output", str(group), "--force")
        assert forced.returncode == 0, forced.stdout + forced.stderr
        assert forced.stdout.count("mock Whisper execution") == 2
        assert all(b"previous run sentinel" not in path.read_bytes() for path in logs)


def test_group_defaults_to_sibling_group_for_selected_file():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        media = root / "chosen.ogg"
        media.write_bytes(b"chosen media")
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_mocks(bin_dir)

        preview = run(environment(root, bin_dir), str(media), "--list")
        assert preview.returncode == 0, preview.stdout + preview.stderr
        assert f"Группа: {(root / 'group').resolve()}" in preview.stdout
        assert not (root / "group").exists()


if __name__ == "__main__":
    test_group_accepts_directories_and_files_deduplicates_by_content_and_reuses_group()
    test_group_defaults_to_sibling_group_for_selected_file()
    print("group transcription regression tests passed")
