"""Explicit cross-repository fixture check using the real central publisher.

Run through seminartext-owned-run with --registry-root pointing to the verified
central checkout. The ordinary native suite is offline/self-contained; this
separate boundary check requires that checkout, not product deployment.
"""
import argparse
import importlib.util
from pathlib import Path
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
        paths += [ref["path"] for event in initial["history"] for ref in event["evidence"]]
        for relative in paths:
            target = checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
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
        print("BOUNDARY_FIXTURE: PASS; real publisher + atomic Git + idempotent retry; production untouched")


if __name__ == "__main__":
    main()
