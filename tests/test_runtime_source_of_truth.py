import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
MODULES = ROOT / "seminartext_modules"
TOPICS = MODULES / "seminartext_topics.py"
TRANSLATE = MODULES / "seminartext_translate.py"
DEV_CLI = ROOT / "scripts" / "seminartext-dev"
VERSION_FILE = ROOT / "SEMINARTEXT_VERSION"

ACCEPTED_HASHES = {
    TOPICS: "d8a14e83b877024c3e016a33e594af17d512741a77735ff3d8c7d1262628c8db",
    TRANSLATE: "1f8219e00f208c46a3dbf25586ebc6b1e2c82815f50bbfd7b0a8cc8bf0c6df02",
}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(*args, env=None, cli=CLI):
    command_env = os.environ.copy()
    if env:
        command_env.update({key: str(value) for key, value in env.items()})
    return subprocess.run(
        [str(cli), *args],
        cwd=ROOT,
        env=command_env,
        text=True,
        capture_output=True,
        check=False,
    )


def make_fake_ollama(bin_dir: Path):
    bin_dir.mkdir(parents=True, exist_ok=True)
    ollama = bin_dir / "ollama"
    ollama.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    ollama.chmod(0o755)


def make_runtime_stub(path: Path):
    path.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

Path(os.environ["SEMINARTEXT_STUB_RECORD"]).write_text(
    json.dumps(sys.argv[1:], ensure_ascii=False), encoding="utf-8"
)
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def parse_identity(output: str):
    return dict(
        line.split("=", 1)
        for line in output.splitlines()
        if "=" in line
    )


def test_tracked_runtime_modules_match_proven_live_hashes():
    for path, expected in ACCEPTED_HASHES.items():
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_topics_module_contract_without_ollama(tmp_path):
    topics = load_module(TOPICS)
    assert topics.clean_model_text("  Тема\x1b[31m  занятия  ") == "Тема занятия"
    assert topics.is_russian_topic_text("Практика мышечного тестирования")
    assert not topics.is_russian_topic_text("Muscle testing practice")

    srt = tmp_path / "sample.srt"
    srt.write_text(
        "1\n00:00:01,000 --> 00:00:03,000\nПервая тема\n\n"
        "2\n00:00:03,500 --> 00:00:05,000\nВторая тема\n",
        encoding="utf-8",
    )
    rows = topics.parse_srt(srt)
    assert [row["id"] for row in rows] == [1, 2]
    assert [row["text"] for row in rows] == ["Первая тема", "Вторая тема"]


def test_translate_module_contract_without_ollama():
    translate = load_module(TRANSLATE)
    assert translate.clean("a\x1b[31m b") == "a b"
    assert translate.is_english("This sentence contains enough English letters to translate.")
    assert not translate.is_english("Это достаточно длинное предложение на русском языке.")
    assert translate.json_array('prefix ["один", "два"] suffix') == ["один", "два"]


def test_runtime_identity_resolves_bundled_modules_and_hashes():
    result = run_cli("runtime-identity")
    assert result.returncode == 0, result.stderr
    identity = parse_identity(result.stdout)
    assert identity["version"] == VERSION_FILE.read_text(encoding="utf-8").strip()
    assert Path(identity["topics.path"]) == TOPICS
    assert Path(identity["translate.path"]) == TRANSLATE
    assert identity["topics.sha256"] == ACCEPTED_HASHES[TOPICS]
    assert identity["translate.sha256"] == ACCEPTED_HASHES[TRANSLATE]
    assert identity["cli.sha256"] == hashlib.sha256(CLI.read_bytes()).hexdigest()


def test_runtime_identity_supports_installed_sibling_layout(tmp_path):
    installed_cli = tmp_path / "seminartext"
    shutil.copy2(CLI, installed_cli)
    shutil.copy2(VERSION_FILE, tmp_path / VERSION_FILE.name)
    shutil.copy2(TOPICS, tmp_path / TOPICS.name)
    shutil.copy2(TRANSLATE, tmp_path / TRANSLATE.name)

    result = run_cli("runtime-identity", cli=installed_cli)
    assert result.returncode == 0, result.stderr
    identity = parse_identity(result.stdout)
    assert Path(identity["topics.path"]) == tmp_path / TOPICS.name
    assert Path(identity["translate.path"]) == tmp_path / TRANSLATE.name


def test_explicit_missing_override_fails_with_actionable_message(tmp_path):
    missing = tmp_path / "missing_topics.py"
    result = run_cli(
        "runtime-identity",
        env={"SEMINARTEXT_TOPICS_MODULE": missing},
    )
    assert result.returncode == 1
    assert "SEMINARTEXT_TOPICS_MODULE" in result.stderr
    assert str(missing) in result.stderr
    assert "удалите SEMINARTEXT_TOPICS_MODULE" in result.stderr


def test_topics_cli_smoke_uses_explicit_stub_without_real_ollama(tmp_path):
    fake_bin = tmp_path / "bin"
    make_fake_ollama(fake_bin)
    stub = tmp_path / "topics_stub.py"
    record = tmp_path / "topics_args.json"
    make_runtime_stub(stub)

    result = run_cli(
        "topics",
        "lecture.mp4",
        "--detail",
        "high",
        "--model",
        "fake:model",
        "--force",
        env={
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "SEMINARTEXT_TOPICS_MODULE": stub,
            "SEMINARTEXT_STUB_RECORD": record,
            "SEMINARTEXT_OUTPUT": tmp_path / "output",
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(record.read_text(encoding="utf-8")) == [
        "lecture.mp4",
        "--root",
        str(tmp_path / "output"),
        "--detail",
        "high",
        "--model",
        "fake:model",
        "--force",
    ]


def test_translate_cli_smoke_uses_explicit_stub_without_real_ollama(tmp_path):
    fake_bin = tmp_path / "bin"
    make_fake_ollama(fake_bin)
    stub = tmp_path / "translate_stub.py"
    record = tmp_path / "translate_args.json"
    make_runtime_stub(stub)

    result = run_cli(
        "translate",
        "lecture.mp4",
        "--force",
        env={
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "SEMINARTEXT_TRANSLATE_MODULE": stub,
            "SEMINARTEXT_STUB_RECORD": record,
            "SEMINARTEXT_OUTPUT": tmp_path / "output",
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(record.read_text(encoding="utf-8")) == [
        "lecture.mp4",
        "--root",
        str(tmp_path / "output"),
        "--force",
    ]


def test_dev_status_compares_both_runtime_modules(tmp_path):
    deploy_bin = tmp_path / "bin"
    deploy_bin.mkdir()
    shutil.copy2(TOPICS, deploy_bin / TOPICS.name)
    shutil.copy2(TRANSLATE, deploy_bin / TRANSLATE.name)

    result = subprocess.run(
        [str(DEV_CLI), "status"],
        cwd=ROOT,
        env={
            **os.environ,
            "SEMINARTEXT_DEV_REPO": str(ROOT),
            "SEMINARTEXT_DEV_BIN": str(deploy_bin),
            "SEMINARTEXT_DEV_BACKUP_ROOT": str(tmp_path / "backups"),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Topics:  SYNC" in result.stdout
    assert "Translate: SYNC" in result.stdout
    assert "DEPLOY STATUS: DIFFERENT (4/6)" in result.stdout
