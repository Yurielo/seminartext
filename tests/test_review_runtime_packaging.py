"""Governed review closure packaging; no installed runtime or models touched."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
DECLARATIONS = json.loads((ROOT / "integrity/integrity_contract.json").read_text())["runtime_components"]
REVIEW_IDS = {
    "automatic_topic_review", "batch_topic_review", "media_to_review", "media_alignment",
    "reviewed_knowledge_admission", "topic_review_engine", "existing_alignment_producer",
    "alignment_requirements", "dependency_profiles", "alignment_lock", "reviewed_knowledge_admission_schema",
}
REVIEW = [row for row in DECLARATIONS if row["id"] in REVIEW_IDS]


def shell(tmp_path, operations):
    # Source the existing governed functions without dispatching a command.
    prefix = (ROOT / "scripts/seminartext-dev").read_text().split('case "${1:-}" in')[0]
    script = tmp_path / "invoke.sh"
    script.write_text(prefix + "\n" + operations + "\n")
    return subprocess.run(["bash", str(script)], text=True, capture_output=True,
                          env={**os.environ, "SEMINARTEXT_DEV_REPO": str(ROOT),
                               "SEMINARTEXT_DEV_BIN": str(tmp_path / "bin")})


def test_review_closure_matches_inventory_and_dispatches_without_source_checkout(tmp_path):
    target = tmp_path / "bin"
    for row in DECLARATIONS:
        path = target / row["deployed_name"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / row["repository_path"], path)
    assert {row["id"] for row in REVIEW} == REVIEW_IDS
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)
    for command in ["project-topic-review", "project-topic-review-batch", "project-media-review"]:
        result = subprocess.run([str(target / "seminartext_4.0_work"), command, "--help"],
                                cwd=tmp_path, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    # The fixed historical producer is copied unchanged, not replaced.
    producer = next(row for row in REVIEW if row["id"] == "existing_alignment_producer")
    assert (target / producer["deployed_name"]).read_bytes() == (ROOT / producer["repository_path"]).read_bytes()


def test_backup_and_rollback_restore_existing_bytes_and_exact_absences(tmp_path):
    target = tmp_path / "bin"
    target.mkdir()
    existing = REVIEW[0]["deployed_name"]
    (target / existing).parent.mkdir(parents=True)
    (target / existing).write_bytes(b"previous governed implementation\n")
    result = shell(tmp_path, '''review_runtime_targets
review_runtime_backup "$BIN/../backup"
review_runtime_stage
review_runtime_install
review_runtime_restore "$BIN/../backup"''')
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / existing).read_bytes() == b"previous governed implementation\n"
    for row in REVIEW[1:]:
        assert not (target / row["deployed_name"]).exists()
    manifest = json.loads((tmp_path / "backup/review-runtime-manifest.json").read_text())
    assert manifest[existing] == hashlib.sha256(b"previous governed implementation\n").hexdigest()
    assert all(manifest[row["deployed_name"]] is None for row in REVIEW[1:])


def test_empty_cleanup_and_staging_collision_preserve_foreign_file(tmp_path):
    target = tmp_path / "bin"
    target.mkdir()
    result = shell(tmp_path, 'review_runtime_cleanup')
    assert result.returncode == 0, result.stderr
    result = shell(tmp_path, '''mkdir -p "$BIN/seminartext_modules"
printf foreign > "$BIN/seminartext_modules/automatic_topic_review.py.new.$$"
trap review_runtime_cleanup EXIT
review_runtime_stage''')
    assert result.returncode != 0
    assert "staging already exists" in result.stderr
    retained = list((target / "seminartext_modules").glob("*.new.*"))
    assert len(retained) == 1 and retained[0].read_bytes() == b"foreign"


def test_corrupt_or_symlinked_closure_is_rejected_before_replacement(tmp_path):
    (tmp_path / "bin").mkdir()
    result = shell(tmp_path, '''review_runtime_backup "$BIN/../backup"
review_runtime_stage
review_runtime_install
printf 'corrupt' > "$BIN/../backup/review-runtime-manifest.json"
review_runtime_restore "$BIN/../backup"''')
    assert result.returncode != 0
    assert "backup integrity failed" in result.stderr
    assert all((tmp_path / "bin" / row["deployed_name"]).read_bytes() ==
               (ROOT / row["repository_path"]).read_bytes() for row in REVIEW)
    other = tmp_path / "symlink"
    other.mkdir(); (other / "bin").mkdir()
    outside = other / "untouched"
    outside.mkdir()
    (other / "bin/seminartext_modules").symlink_to(outside, target_is_directory=True)
    result = shell(other, 'review_runtime_targets\nreview_runtime_stage')
    assert result.returncode != 0
    assert "unsafe review runtime parent" in result.stderr
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("damage", ["foreign-target", "rollback-stage-symlink"])
def test_rollback_preserves_foreign_changes_and_staging_paths(tmp_path, damage):
    (tmp_path / "bin").mkdir()
    first = REVIEW[0]["deployed_name"]
    outside = tmp_path / "foreign.txt"
    outside.write_bytes(b"foreign bytes must remain untouched")
    mutation = ('printf foreign > "$BIN/' + first + '"') if damage == "foreign-target" else (
        'ln -s "$BIN/../foreign.txt" "$BIN/' + first + '.rollback.$$"')
    result = shell(tmp_path, '''review_runtime_backup "$BIN/../backup"
review_runtime_stage
review_runtime_install
''' + mutation + '''
review_runtime_restore "$BIN/../backup"''')
    assert result.returncode != 0
    assert "changed since deploy" in result.stderr or "staging already exists" in result.stderr
    assert outside.read_bytes() == b"foreign bytes must remain untouched"
    # Preflight rejection must precede all restoration/removal.
    assert all((tmp_path / "bin" / row["deployed_name"]).exists() for row in REVIEW)
    if damage == "foreign-target":
        assert (tmp_path / "bin" / first).read_bytes() == b"foreign"
