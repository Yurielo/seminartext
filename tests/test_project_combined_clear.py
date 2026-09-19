#!/usr/bin/env python3
"""Regression coverage for Issue #122 combined clear project artifacts."""

import hashlib
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
        bin_dir / "ffprobe",
        """#!/usr/bin/env python3
import json, os, sys
value = json.loads(os.environ.get("SEMINARTEXT_TEST_EMBEDDED", "{}")).get(os.path.basename(sys.argv[-1]))
print(json.dumps({"format": {"tags": {"creation_time": value}}} if value else {"format": {"tags": {}}}))
""",
    )
    write_executable(
        bin_dir / "stat",
        """#!/usr/bin/env python3
import json, os, sys
print(json.loads(os.environ.get("SEMINARTEXT_TEST_BIRTHTIME", "{}")).get(os.path.basename(sys.argv[-1]), 0))
""",
    )
    for name in ("ffmpeg", "whisper-cli"):
        write_executable(bin_dir / name, "#!/bin/bash\nexit 0\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_project(root: Path, sources: list[dict]) -> Path:
    project = root / "project"
    project.mkdir()
    (project / "sources.json").write_text(
        json.dumps({"schema_version": 1, "videos": sources, "documents": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    return project


def ready_source(project: Path, source: dict, text: str) -> Path:
    media = project / source["file"]
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(("media:" + source["source_id"]).encode())
    out = project / "transcript" / source["source_id"]
    out.mkdir(parents=True)
    (out / "transcript_clean.txt").write_text(text, encoding="utf-8")
    (out / ".seminartext_complete").touch()
    (out / "transcript.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n" + text + "\n", encoding="utf-8"
    )
    return media


def env_for(root: Path, bin_dir: Path, embedded: dict | None = None, birthtime: dict | None = None) -> dict:
    model = root / "model.bin"
    vad = root / "vad.bin"
    model.write_text("model", encoding="utf-8")
    vad.write_text("vad", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env["PATH"],
            "SEMINARTEXT_MODEL": str(model),
            "SEMINARTEXT_VAD_MODEL": str(vad),
            "SEMINARTEXT_TEST_EMBEDDED": json.dumps(embedded or {}),
            "SEMINARTEXT_TEST_BIRTHTIME": json.dumps(birthtime or {}),
        }
    )
    return env


def run(project: Path, env: dict, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPT), "project-transcribe", str(project), *flags],
        text=True,
        capture_output=True,
        env=env,
    )


def source(source_id: str, file: str, order: int) -> dict:
    return {"source_id": source_id, "file": file, "order": order, "type": "local", "title": source_id}


def test_embedded_order_clean_output_manifest_and_repeatability():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_mocks(bin_dir)
        sources = [
            source("third", "часть В.mp4", 1),
            source("first", "часть А.mp4", 3),
            source("second", "часть Б.mp4", 2),
        ]
        project = make_project(root, sources)
        media = {entry["source_id"]: ready_source(project, entry, f"Текст {entry['source_id']}") for entry in sources}
        original_hashes = {
            key: sha256(project / "transcript" / key / "transcript_clean.txt") for key in media
        }
        env = env_for(
            root,
            bin_dir,
            embedded={"часть А.mp4": "2024-03-01T10:00:00Z", "часть Б.mp4": "2024-01-01T10:00:00Z"},
            birthtime={"часть А.mp4": 1, "часть Б.mp4": 1, "часть В.mp4": 1706745600},
        )
        result = run(project, env, "--combined-with-sources")
        assert result.returncode == 0, result.stdout + result.stderr
        transcript_root = project / "transcript"
        clean = transcript_root / "combined_clear.txt"
        with_sources = transcript_root / "combined_clear_with_sources.txt"
        manifest_path = transcript_root / "combined_clear_manifest.json"
        assert clean.read_text(encoding="utf-8") == "Текст second\n\nТекст third\n\nТекст first\n"
        assert "=====" not in clean.read_text(encoding="utf-8")
        assert ".mp4" not in clean.read_text(encoding="utf-8")
        readable = with_sources.read_text(encoding="utf-8")
        assert readable.index("часть Б.mp4") < readable.index("часть В.mp4") < readable.index("часть А.mp4")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["ordering_method"] == "creation_date"
        assert manifest["supported_ordering_methods"] == ["creation_date", "filename", "selection_order", "manual"]
        assert [entry["source_id"] for entry in manifest["sources"]] == ["second", "third", "first"]
        assert manifest["sources"][0]["ordering_date_source"] == "embedded"
        assert manifest["sources"][1]["ordering_date_source"] == "birthtime"
        assert manifest["sources"][0]["combined_clear_char_range"] == {"start": 0, "end": 12}
        assert manifest["sources"][0]["transcript_revision"]["artifact"] == "transcript/second/transcript_clean.txt"
        assert all(sha256(project / "transcript" / key / "transcript_clean.txt") == value for key, value in original_hashes.items())
        first_run = clean.read_bytes(), manifest_path.read_bytes()
        repeat = run(project, env, "--combined-with-sources")
        assert repeat.returncode == 0, repeat.stdout + repeat.stderr
        assert first_run == (clean.read_bytes(), manifest_path.read_bytes())


def test_birthtime_then_mtime_fallback_and_deterministic_ties():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_mocks(bin_dir)
        sources = [
            source("z-source", "zeta.mp4", 1),
            source("a-source", "альфа.mp4", 2),
            source("same-b", "one/same.mp4", 3),
            source("same-a", "two/same.mp4", 4),
        ]
        project = make_project(root, sources)
        for entry in sources:
            ready_source(project, entry, entry["source_id"])
        # Birthtime wins over intentionally opposite mtime values.
        for index, entry in enumerate(sources):
            path = project / entry["file"]
            os.utime(path, (1800000000 + index, 1800000000 + index))
        env = env_for(
            root,
            bin_dir,
            birthtime={"zeta.mp4": 1707000000, "альфа.mp4": 1706000000, "same.mp4": 1708000000},
        )
        result = run(project, env, "--combined-clear")
        assert result.returncode == 0, result.stdout + result.stderr
        manifest = json.loads((project / "transcript" / "combined_clear_manifest.json").read_text(encoding="utf-8"))
        assert [item["source_id"] for item in manifest["sources"]] == ["a-source", "z-source", "same-a", "same-b"]
        assert all(item["ordering_date_source"] == "birthtime" for item in manifest["sources"])

        # No embedded or birth date: mtime is the documented final fallback.
        env = env_for(root, bin_dir)
        result = run(project, env, "--combined-clear")
        assert result.returncode == 0, result.stdout + result.stderr
        manifest = json.loads((project / "transcript" / "combined_clear_manifest.json").read_text(encoding="utf-8"))
        assert all(item["ordering_date_source"] == "mtime" for item in manifest["sources"])
        assert [item["source_id"] for item in manifest["sources"]][:2] == ["z-source", "a-source"]


def test_incomplete_local_source_fails_closed_and_help_documents_mode():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_mocks(bin_dir)
        sources = [source("ready", "ready.mp4", 1), source("missing", "missing.mp4", 2)]
        project = make_project(root, sources)
        ready_source(project, sources[0], "Готовый текст")
        result = run(project, env_for(root, bin_dir), "--combined-clear")
        output = result.stdout + result.stderr
        assert result.returncode != 0
        assert "combined-clear" in output and "missing" in output
        assert not (project / "transcript" / "combined_clear.txt").exists()

        help_result = subprocess.run([str(SCRIPT), "project-transcribe", "--help"], text=True, capture_output=True)
        help_text = help_result.stdout + help_result.stderr
        assert help_result.returncode == 0
        for marker in ("--combined-clear", "--combined-with-sources", "embedded", "birth time", "mtime", "provenance"):
            assert marker in help_text


if __name__ == "__main__":
    test_embedded_order_clean_output_manifest_and_repeatability()
    test_birthtime_then_mtime_fallback_and_deterministic_ties()
    test_incomplete_local_source_fails_closed_and_help_documents_mode()
    print("project combined clear regression tests passed")
