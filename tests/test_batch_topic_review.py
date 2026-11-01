"""Batch orchestration tests use synthetic sources and no semantic decisions."""
import json
from pathlib import Path

import pytest

from seminartext_modules import batch_topic_review as batch
from tests.test_automatic_topic_review import CASES, fixture


def manifest(path, argses):
    value = {
        "artifact_type": batch.MANIFEST_ARTIFACT,
        "schema_version": batch.VERSION,
        "entries": [
            {"id": f"synthetic-{index}", "project": str(args.project), "source": str(args.source),
             "source_id": args.source_id, "revision_id": args.revision_id, "run_directory": f"run-{index}"}
            for index, args in enumerate(argses, 1)
        ],
    }
    path.write_bytes(batch.review.canonical_bytes(value))
    return path


def fake_runtime(monkeypatch, calls, *, fail=None):
    def receipt(entry, root):
        run = Path(root) / entry["run_directory"]
        return {"run": str(run), "package": str(run / "review_package.json"), "receipt_sha256": "r" + entry["id"],
                "package_sha256": "p" + entry["id"], "topics": 2, "fallback_count": 0, "model_digest": "a" * 64}

    def execute(args):
        calls.append((args.command, args.source_id))
        if args.command == "generate" and args.source_id == fail:
            raise ValueError("synthetic producer failure")
        args.run.mkdir(parents=True, exist_ok=True)
        if args.command in {"generate", "replay"}:
            (args.run / "response.json").write_text("{}")
            (args.run / "receipt.json").write_text("{}")

    monkeypatch.setattr(batch.auto, "execute", execute)
    monkeypatch.setattr(batch, "_receipt", receipt)


def test_two_sources_prepare_run_reopen_resume_and_immutable_journal(tmp_path, monkeypatch):
    argses = [fixture(tmp_path / "astronomy", CASES[0]), fixture(tmp_path / "botany", CASES[1])]
    source_bytes = [args.source.read_bytes() for args in argses]
    path = manifest(tmp_path / "manifest.json", argses)
    root = tmp_path / "batch"
    prepared = batch.prepare(root, path)
    assert [entry["status"] for entry in prepared["entries"]] == ["PENDING", "PENDING"]
    calls = []; fake_runtime(monkeypatch, calls)
    result, changed = batch.run(root)
    assert changed and batch._summary(result) == {"status": "REVIEW_REQUIRED", "entries": 2, "pending": 0, "review_required": 2, "failed": 0}
    assert calls == [("generate", argses[0].source_id), ("generate", argses[1].source_id)]
    assert "решений: 0" in batch.inspect(root)
    reopened = batch.status(root)
    assert all(entry["status"] == "REVIEW_REQUIRED" for entry in reopened["entries"])
    resumed, changed = batch.run(root)
    assert not changed and resumed == reopened
    assert [args.source.read_bytes() for args in argses] == source_bytes
    paths, final = batch._snapshots(root)
    assert len(paths) == 3 and final == reopened
    assert all(json.loads(path.read_bytes())["state_sha256"] in path.name for path in paths)


def test_stale_preflight_prevents_every_model_call(tmp_path, monkeypatch):
    argses = [fixture(tmp_path / "astronomy", CASES[0]), fixture(tmp_path / "botany", CASES[1])]
    root = tmp_path / "batch"; batch.prepare(root, manifest(tmp_path / "manifest.json", argses))
    argses[1].source.write_bytes(b"changed")
    calls = []; fake_runtime(monkeypatch, calls)
    with pytest.raises(ValueError, match="stale or unavailable input"):
        batch.run(root)
    assert calls == []


def test_changed_manifest_never_reopens_old_batch_state(tmp_path):
    argses = [fixture(tmp_path / "astronomy", CASES[0]), fixture(tmp_path / "botany", CASES[1])]
    path = manifest(tmp_path / "manifest.json", argses)
    root = tmp_path / "batch"; batch.prepare(root, path)
    value = json.loads(path.read_bytes()); value["entries"][0]["id"] = "changed-selection"
    path.write_bytes(batch.review.canonical_bytes(value))
    with pytest.raises(ValueError, match="manifest changed"):
        batch.status(root)


def test_interrupted_response_replays_without_new_generation_and_failure_is_retained(tmp_path, monkeypatch):
    argses = [fixture(tmp_path / "astronomy", CASES[0]), fixture(tmp_path / "botany", CASES[1])]
    root = tmp_path / "batch"; batch.prepare(root, manifest(tmp_path / "manifest.json", argses))
    interrupted = root / "run-1"; interrupted.mkdir(); (interrupted / "response.json").write_text("{}")
    calls = []; fake_runtime(monkeypatch, calls, fail=argses[1].source_id)
    state, _ = batch.run(root)
    assert calls == [("replay", argses[0].source_id), ("generate", argses[1].source_id)]
    assert [entry["status"] for entry in state["entries"]] == ["REVIEW_REQUIRED", "FAILED"]
    calls.clear(); state, changed = batch.run(root)
    assert not changed and calls == [] and batch._summary(state)["status"] == "PARTIAL_FAILURE"


def test_manifest_contract_and_duplicate_sources_fail_before_preparation(tmp_path):
    args = fixture(tmp_path / "astronomy", CASES[0])
    path = manifest(tmp_path / "manifest.json", [args, args])
    with pytest.raises(ValueError, match="duplicate"):
        batch.prepare(tmp_path / "batch", path)
    value = json.loads(path.read_bytes()); value["schema_version"] = "9.0.0"
    path.write_bytes(batch.review.canonical_bytes(value))
    with pytest.raises(ValueError, match="unsupported manifest contract"):
        batch.prepare(tmp_path / "batch-other", path)
