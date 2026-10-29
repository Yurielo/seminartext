"""Explicit cross-repository fixture check using the real central publisher.

Run through seminartext-owned-run with --registry-root pointing to the verified
central checkout. The ordinary native suite is offline/self-contained; this
separate boundary check requires that checkout, not product deployment.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import shutil
import tempfile

import pytest

from test_activation_receipt import a, native, complete, local_git


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.registry_root.resolve()
    spec = importlib.util.spec_from_file_location("real_central_registry", source / "registry.py")
    central = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(central)
    with tempfile.TemporaryDirectory(prefix="registry-adapter-boundary-") as tmp, pytest.MonkeyPatch.context() as patch:
        root = Path(tmp)
        fixture = native.__wrapped__(root, patch)
        bare = root / "remote.git"
        local_git(root, "init", "--bare", "-b", "main", str(bare))
        checkout = fixture["central"]
        local_git(root, "clone", str(bare), str(checkout))
        local_git(checkout, "config", "user.name", "Boundary Fixture")
        local_git(checkout, "config", "user.email", "fixture@example.invalid")
        paths = ["registry.json", "schemas/registry.schema.json"]
        initial = central.decode((source / "registry.json").read_bytes())
        initial["history"] = [e for e in initial["history"] if e["product"] != "seminartext"]
        initial["products"]["seminartext"]["current"] = None
        initial["products"]["seminartext"]["unregistered_reason"] = "isolated rollback fixture"
        paths += [ref["path"] for event in initial["history"] for ref in event["evidence"]]
        for relative in paths:
            target = checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(central.encode(initial) if relative == "registry.json"
                               else (source / relative).read_bytes())
        local_git(checkout, "add", "."); local_git(checkout, "commit", "-m", "Isolated central baseline")
        local_git(checkout, "push", "origin", "main")
        # Only this test factory bypasses production's exact-GitHub-origin
        # check. All subsequent publication is real Git to the local bare repo.
        patch.setattr(a, "central_module", lambda _: central)
        complete(fixture)
        first, code = a.publish(fixture["operation"], checkout)
        assert code == 0 and first["status"] == "PUBLISHED", first
        repeated, code = a.publish(fixture["operation"], checkout)
        assert code == 0 and repeated["status"] == "ALREADY_PUBLISHED", repeated
        head = local_git(bare, "rev-parse", "main")
        state = central.decode(central.at(bare, head, "registry.json"))
        central.validate(state, central.decode(central.at(bare, head, central.SCHEMA)),
                         lambda path: central.at(bare, head, path))
        assert state["history"][:-1] == initial["history"]
        assert state["history"][-1]["product"] == "seminartext"
        assert state["products"]["integra"] == initial["products"]["integra"]
        historical = deepcopy(state["history"][-1])
        backup = root / "old-runtime"
        backup.mkdir()
        for row in fixture["record"]["components"]:
            path = Path(row["deployed_path"])
            shutil.copy2(path, backup / path.name)
            path.write_text("next synthetic runtime " + row["id"])
        head = central.remote_head(checkout)
        next_release = deepcopy(historical["release"])
        next_release["native_ref"] = "file:///synthetic/second-activation"
        next_release["version"] = "5.0.0"
        next_release["source_commit"] = "f" * 40
        for artifact in next_release["artifacts"]:
            artifact["source_commit"] = "f" * 40
            artifact["digest"]["value"] = hashlib.sha256(Path(artifact["location"]).read_bytes()).hexdigest()
        next_event = {"product": "seminartext", "generation": historical["generation"] + 1,
                      "predecessor": historical["event_id"], "action": "activate", "rollback_of": None,
                      "target": historical["target"], "activated_at": historical["activated_at"],
                      "recorded_at": historical["recorded_at"], "dependencies": [], "release": next_release}
        next_proof = {"kind": "native_activation", "status": "SUCCEEDED",
                      "subject_sha256": central.subject_hash(next_event),
                      "native_reference": "file:///synthetic/second-activation",
                      "native_evidence": {"fixture": "second activation"}}
        payload = central.encode(next_proof)
        path = "evidence/seminartext-activation-" + hashlib.sha256(payload).hexdigest() + ".json"
        (checkout / path).write_bytes(payload)
        next_event["evidence"] = [{"path": path, "sha256": hashlib.sha256(payload).hexdigest()}]
        next_event["event_id"] = central.event_id(next_event)
        assert central.publish(checkout, next_event, head)["status"] == "PUBLISHED"
        local_git(checkout, "fetch", "origin", "main")
        rollback = fixture["operation"].parent / "rollback"
        rollback.mkdir()
        a.begin(fixture["root"], fixture["deployed"], rollback, checkout, "rollback", backup)
        for row in fixture["record"]["components"]:
            path = Path(row["deployed_path"])
            shutil.copy2(backup / path.name, path)
        (fixture["deployed"] / "SEMINARTEXT_4_STATE.json").write_text("{}")
        native_run = a.run
        def synthetic_smoke(command, **kwargs):
            if command[0] == "bash" or command[0] == str(fixture["deployed"] / "seminartext_4.0_work"):
                return 0, b"", b""
            return native_run(command, **kwargs)
        patch.setattr(a, "run", synthetic_smoke)
        receipt = a.rollback_complete(fixture["root"], fixture["deployed"], rollback)
        assert receipt["status"] == "SUCCEEDED"
        outcome, code = a.publish(rollback, checkout)
        assert code == 0 and outcome["status"] == "PUBLISHED", outcome
        final_head = central.remote_head(checkout)
        final = central.decode(central.at(checkout, final_head, "registry.json"))
        central.validate(final, central.decode(central.at(checkout, final_head, central.SCHEMA)),
                         lambda ref: central.at(checkout, final_head, ref))
        assert final["history"][:len(initial["history"])] == initial["history"]
        assert final["history"][-1]["rollback_of"] == historical["event_id"]
        assert final["history"][-1]["release"] == historical["release"]
        repeat, code = a.publish(rollback, checkout)
        assert code == 0 and repeat["status"] == "ALREADY_PUBLISHED"
        print("BOUNDARY_FIXTURE: PASS; real publisher, append-only rollback, read-back, retry; production untouched")


if __name__ == "__main__":
    main()
