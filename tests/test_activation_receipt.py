"""Isolated native lifecycle fixtures. No production deployment or GitHub write."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("activation_receipt", ROOT / "scripts/activation_receipt.py")
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def local_git(root, *arguments):
    return subprocess.check_output(["git", "-C", str(root), *arguments], stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def native(tmp_path, monkeypatch):
    root, deployed, operations = tmp_path / "source", tmp_path / "bin", tmp_path / "operations"
    root.mkdir(); deployed.mkdir(); operations.mkdir()
    (root / "integrity").mkdir()
    (root / "scripts").mkdir()
    (root / "SEMINARTEXT_VERSION").write_text("4.0.0\n")
    (root / "seminartext").write_text("synthetic installed fixture\n")
    (deployed / "seminartext_4.0_work").write_bytes((root / "seminartext").read_bytes())
    (deployed / "SEMINARTEXT_VERSION").write_bytes((root / "SEMINARTEXT_VERSION").read_bytes())
    contract = {"schema_version": 1, "runtime_components": [
        {"id": "cli", "repository_path": "seminartext", "deployed_name": "seminartext_4.0_work", "required": True},
        {"id": "version", "repository_path": "SEMINARTEXT_VERSION", "deployed_name": "SEMINARTEXT_VERSION", "required": True}],
        "gates": [{"id": f"G{i}", "blocking_policy": "future_blocking" if i == 6 else "blocking"} for i in range(1, 9)]}
    (root / "integrity/integrity_contract.json").write_bytes(a.encoded(contract))
    local_git(root, "init", "-b", "main")
    local_git(root, "config", "user.name", "Native Fixture")
    local_git(root, "config", "user.email", "fixture@example.invalid")
    local_git(root, "add", "."); local_git(root, "commit", "-m", "Synthetic native source")
    operation = operations / "deployment"
    operation.mkdir(); (operation / "manifest.txt").write_text("synthetic backup manifest\n")
    central = tmp_path / "central"
    a.begin(root, deployed, operation, central, "deploy")
    record = a.installed(root, deployed, operation)
    g2 = {"components": [{"id": row["id"], "deployed_path": row["deployed_path"],
                          "repository_sha256": row["sha256"], "deployed_sha256": row["sha256"],
                          "deployment_status": "SYNC"} for row in record["components"]],
          "functional_smoke": {"status": "PASS"}}
    report = {"exit_code": 0, "internal_errors": [], "head_sha": record["source_commit"],
              "deployment_dir": str(deployed), "project_integrity": "PARTIAL", "gates": [
                  {"id": f"G{i}", "status": "NOT_IMPLEMENTED" if i == 6 else "PASS", "evidence":
                   {"working_tree_clean": True} if i == 1 else g2 if i == 2 else
                   {"passed": 3, "skipped": 0} if i == 7 else {}} for i in range(1, 9)]}
    real_run = a.run
    calls = []
    def run(command, **kwargs):
        if command[0].endswith("scripts/seminartext-integrity"):
            calls.append(command)
            return 0, a.encoded(report), b""
        return real_run(command, **kwargs)
    monkeypatch.setattr(a, "run", run)
    return {"root": root, "deployed": deployed, "operation": operation, "central": central,
            "record": record, "report": report, "calls": calls}


def complete(native):
    return a.complete(native["root"], native["deployed"], native["operation"])


class PublisherFixture:
    """Test double for adapter calls; actual publisher is tested separately."""
    SCHEMA = "schema.json"
    def __init__(self):
        self.head = "a" * 40
        self.state = {"products": {"seminartext": {"current": None}}, "history": []}
        self.attempts = []
        self.fail = False
    def remote_head(self, root): return self.head
    def at(self, root, head, path): return a.encoded(self.state if path == "registry.json" else {})
    def validate(self, *args): return None
    def decode(self, data): return json.loads(data)
    def encode(self, value): return a.encoded(value)
    def subject_hash(self, event):
        return a.digest(a.encoded({k: v for k, v in event.items() if k not in {"event_id", "evidence"}}))
    def event_id(self, event):
        return "sha256:" + a.digest(a.encoded({k: v for k, v in event.items() if k != "event_id"}))
    def publish(self, root, event, expected):
        self.attempts.append(deepcopy(event))
        if self.fail: raise OSError("offline fixture")
        if event in self.state["history"]:
            return dict(status="ALREADY_PUBLISHED", head=self.head, event_id=event["event_id"],
                        current=self.state["products"]["seminartext"]["current"])
        if expected != self.head or event["predecessor"] != self.state["products"]["seminartext"]["current"]:
            raise ValueError("stale predecessor")
        self.state["history"].append(deepcopy(event))
        self.state["products"]["seminartext"]["current"] = event["event_id"]
        self.head = "b" * 40
        return dict(status="PUBLISHED", head=self.head, event_id=event["event_id"], current=event["event_id"])


@pytest.fixture
def publisher(native, monkeypatch):
    (native["central"] / "evidence").mkdir(parents=True)
    module = PublisherFixture()
    monkeypatch.setattr(a, "central_module", lambda root: module)
    return module


def test_receipt_only_after_existing_post_checks_and_idempotent_completion(native):
    assert not (native["operation"] / "activation-receipt.json").exists()
    receipt = complete(native)
    assert receipt["status"] == "SUCCEEDED"
    assert receipt["installation"]["source_commit"] == local_git(native["root"], "rev-parse", "HEAD")
    assert len(receipt["installation"]["components"]) == 2
    assert receipt["integrity"]["gates"][5]["status"] == "NOT_IMPLEMENTED"
    assert complete(native) == receipt
    assert len(native["calls"]) == 1


@pytest.mark.parametrize("gate", ["G1", "G2", "G3", "G4", "G5", "G7", "G8"])
def test_any_incomplete_required_gate_prevents_receipt(native, gate):
    next(g for g in native["report"]["gates"] if g["id"] == gate)["status"] = "WARN"
    with pytest.raises(a.Incomplete, match="native gate"):
        complete(native)
    assert not (native["operation"] / "activation-receipt.json").exists()


def test_smoke_inventory_and_test_proofs_are_required(native):
    record = native["record"]
    contract = a.contract(native["root"])
    for change in [lambda r: r.update(head_sha="0" * 40),
                   lambda r: r["gates"][1]["evidence"]["functional_smoke"].update(status="FAIL"),
                   lambda r: r["gates"][1]["evidence"]["components"].pop(),
                   lambda r: r["gates"][6]["evidence"].update(skipped=1)]:
        report = deepcopy(native["report"]); change(report)
        with pytest.raises(a.Incomplete): a.validate_integrity(report, record, contract)


def test_predeploy_manifest_and_matching_hashes_do_not_make_activation(native):
    (native["operation"] / "installation-verified.json").unlink()
    with pytest.raises(FileNotFoundError): complete(native)
    assert not (native["operation"] / "activation-receipt.json").exists()


def test_runtime_drift_prevents_receipt(native):
    (native["deployed"] / "seminartext_4.0_work").write_text("changed")
    with pytest.raises(a.Incomplete, match="component changed"): complete(native)


def test_publication_is_idempotent_and_does_not_rerun_checks(native, publisher):
    complete(native)
    first, code = a.publish(native["operation"], native["central"])
    assert code == 0 and first["status"] == "PUBLISHED"
    event_bytes = (native["operation"] / "publication-event.json").read_bytes()
    second, code = a.publish(native["operation"], native["central"])
    assert code == 0 and second["status"] == "ALREADY_PUBLISHED"
    assert (native["operation"] / "publication-event.json").read_bytes() == event_bytes
    assert len(publisher.state["history"]) == 1
    assert len(native["calls"]) == 1


def test_network_failure_preserves_exact_outbox_and_runtime(native, publisher):
    complete(native); publisher.fail = True
    first, code = a.publish(native["operation"], native["central"])
    assert code == 3 and first["status"] == "PUBLICATION_PENDING" and first["event_prepared"]
    event_bytes = (native["operation"] / "publication-event.json").read_bytes()
    publisher.fail = False
    result, code = a.publish(native["operation"], native["central"])
    assert code == 0 and result["status"] == "PUBLISHED"
    assert (native["operation"] / "publication-event.json").read_bytes() == event_bytes
    assert publisher.attempts[0] == publisher.attempts[1]
    a.runtime_matches(native["record"]["components"])


def test_newer_central_activation_rejects_pending_without_resealing(native, publisher):
    complete(native); publisher.fail = True
    a.publish(native["operation"], native["central"])
    event_bytes = (native["operation"] / "publication-event.json").read_bytes()
    publisher.fail = False
    publisher.state["products"]["seminartext"]["current"] = "sha256:" + "c" * 64
    result, code = a.publish(native["operation"], native["central"])
    assert code == 3 and "stale" in result["reason"]
    assert (native["operation"] / "publication-event.json").read_bytes() == event_bytes


def test_rollback_invalidates_retry_even_when_installed_bytes_equal(native, publisher):
    complete(native); publisher.fail = True
    a.publish(native["operation"], native["central"])
    rollback = native["operation"].parent / "rollback"
    rollback.mkdir()
    a.begin(native["root"], native["deployed"], rollback, native["central"], "rollback")
    before = len(publisher.attempts)
    result, code = a.publish(native["operation"], native["central"])
    assert code == 3 and "superseded" in result["reason"]
    assert len(publisher.attempts) == before
    a.runtime_matches(native["record"]["components"])


def test_no_predeployment_baseline_cannot_replace_registered_product(native, publisher):
    complete(native)
    publisher.state["products"]["seminartext"]["current"] = "sha256:" + "c" * 64
    result, code = a.publish(native["operation"], native["central"])
    assert code == 3 and "deployment-time predecessor" in result["reason"]
    assert not (native["operation"] / "publication-event.json").exists()


def test_unavailable_registry_does_not_invalidate_native_success(native, monkeypatch):
    receipt = complete(native)
    def missing(root): raise FileNotFoundError("central checkout unavailable")
    monkeypatch.setattr(a, "central_module", missing)
    result, code = a.publish(native["operation"], native["central"])
    assert code == 3 and result["status"] == "PUBLICATION_PENDING"
    assert a.read(native["operation"] / "activation-receipt.json") == receipt
    a.runtime_matches(native["record"]["components"])


def test_receipts_cannot_be_overwritten(native):
    complete(native)
    with pytest.raises(a.Incomplete, match="overwrite"):
        a.retain(native["operation"] / "activation-receipt.json", b"different")


def test_pending_event_cannot_switch_product_or_artifacts(native, publisher):
    complete(native); publisher.fail = True
    a.publish(native["operation"], native["central"])
    event_path = native["operation"] / "publication-event.json"
    event = a.read(event_path); event["product"] = "booktext"
    event_path.write_bytes(a.encoded(event))
    result, code = a.publish(native["operation"], native["central"])
    assert code == 3 and "differs from native" in result["reason"]


def test_governed_rollback_preserves_installed_bytes_and_invalidates_pending(tmp_path):
    deployed, backups = tmp_path / "bin", tmp_path / "backups"
    contract = a.contract(ROOT)
    for component in contract["runtime_components"]:
        target = deployed / component["deployed_name"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / component["repository_path"], target)
    before = {str(p.relative_to(deployed)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in deployed.rglob("*") if p.is_file()}
    env = {**os.environ, "SEMINARTEXT_DEV_REPO": str(ROOT), "SEMINARTEXT_DEV_BIN": str(deployed),
           "SEMINARTEXT_DEV_BACKUP_ROOT": str(backups), "SEMINARTEXT_REGISTRY_REPO": str(tmp_path / "absent")}
    result = subprocess.run([str(ROOT / "scripts/seminartext-dev"), "deploy"],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    operation = next(p for p in backups.iterdir() if p.is_dir())
    record = a.read(operation / "installation-verified.json")
    result = subprocess.run([str(ROOT / "scripts/seminartext-dev"), "rollback", str(operation)],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ROLLBACK: PASS" in result.stdout and "REGISTRY: RECONCILIATION_REQUIRED" in result.stdout
    assert before == {str(p.relative_to(deployed)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in deployed.rglob("*") if p.is_file()}
    with pytest.raises(a.Incomplete, match="superseded"): a.current_operation(operation, record)
    assert not (operation / "activation-receipt.json").exists()
