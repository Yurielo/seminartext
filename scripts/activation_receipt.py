#!/usr/bin/env python3
"""Native deployment evidence and adapter to the existing central publisher.

No deployment, product registry or Git publication implementation lives here.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid


class Incomplete(ValueError):
    pass


class ReconciliationRequired(Incomplete):
    pass


def require(condition, message):
    if not condition:
        raise Incomplete(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def now():
    return datetime.now(timezone.utc).isoformat()


def retain(path, data):
    """Create immutable evidence; identical retries are harmless."""
    require(not path.is_symlink(), "evidence path is a symlink")
    if path.exists():
        require(path.read_bytes() == data, f"refusing to overwrite retained evidence: {path}")
        return
    temporary = path.with_name(path.name + ".staged-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            require(path.read_bytes() == data, "concurrent evidence differs")
    finally:
        temporary.unlink(missing_ok=True)  # Only our newly created staging file.


def run(command, *, cwd, timeout=120):
    # Only this owned subprocess group is terminated on timeout.
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_TERMINAL_PROMPT": "0"},
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        raise Incomplete("owned verification/publication subprocess timed out; receipt retained")
    return process.returncode, stdout, stderr


def git(root, *args):
    code, stdout, stderr = run(["git", "-C", str(root), *args], cwd=root, timeout=30)
    require(code == 0, stderr.decode(errors="replace"))
    return stdout.decode().strip()


@contextmanager
def mutation_lock(operation):
    # Serializes publication with native mutation-start only. This file has no
    # version/current pointer and is not a second registry.
    with (operation.parent / ".activation.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def contract(root):
    return read(root / "integrity/integrity_contract.json")


def source_inventory(root, deployed):
    rows = []
    for item in contract(root)["runtime_components"]:
        source = root / item["repository_path"]
        require(source.is_file() and not source.is_symlink(), "runtime source missing or symlinked")
        rows.append({"id": item["id"], "repository_path": item["repository_path"],
                     "deployed_path": str(deployed / item["deployed_name"]),
                     "sha256": digest(source.read_bytes())})
    return rows


def runtime_matches(rows):
    for row in rows:
        path = Path(row["deployed_path"])
        require(path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == row["sha256"],
                f"deployed component changed or missing: {row['id']}")


def begin(root, deployed, operation, registry_root, action, backup=None):
    """Called by the governed shell path before its first runtime replacement."""
    with mutation_lock(operation):
        epoch = uuid.uuid4().hex
        base = None
        observation = "UNAVAILABLE"
        if registry_root.is_dir():
            try:
                base = git(registry_root, "rev-parse", "--verify", "refs/remotes/origin/main")
                observation = "CACHED"
            except Incomplete:
                pass  # Standalone deployment never needs registry connectivity.
            try:
                origin = git(registry_root, "remote", "get-url", "origin").removesuffix(".git")
                require(origin in {"https://github.com/Yurielo/four-product-architecture",
                                   "git@github.com:Yurielo/four-product-architecture"}, "unknown registry origin")
                fresh = git(registry_root, "ls-remote", "--exit-code", "origin", "refs/heads/main").split()[0]
                git(registry_root, "fetch", "--quiet", "--no-tags", "--no-write-fetch-head", "origin", fresh)
                base, observation = fresh, "REMOTE_CONFIRMED_BEFORE_MUTATION"
            except (Incomplete, OSError, IndexError):
                pass  # Cached predecessor is conservative; a stale one is never rebased silently.
        data = {"schema_version": 1, "phase": "MUTATION_STARTED", "action": action,
                "mutation_id": epoch, "started_at": now(), "registry_base_head": base,
                "registry_base_observation": observation,
                "source_root": str(root), "source_commit": git(root, "rev-parse", "HEAD"),
                "deployment_dir": str(deployed),
                "contract_sha256": digest((root / "integrity/integrity_contract.json").read_bytes())}
        if action == "deploy":
            data.update(version=(root / "SEMINARTEXT_VERSION").read_text().strip(),
                        components=source_inventory(root, deployed))
        else:
            require(backup is not None and backup.is_dir(), "rollback source backup missing")
            data["restored_from_backup"] = str(backup)
        retain(operation / "activation-operation.json", encoded(data))
        temporary = operation.parent / (".activation-epoch-" + epoch)
        retain(temporary, epoch.encode())
        os.replace(temporary, operation.parent / ".activation-epoch")
        return data


def current_operation(operation, record):
    require((operation.parent / ".activation-epoch").read_text() == record["mutation_id"],
            "a later deployment or rollback superseded this operation")


def installed(root, deployed, operation):
    with mutation_lock(operation):
        start = read(operation / "activation-operation.json")
        current_operation(operation, start)
        require(start["action"] == "deploy", "not a deployment operation")
        require(start["source_commit"] == git(root, "rev-parse", "HEAD"), "source changed during deployment")
        require(start["deployment_dir"] == str(deployed), "wrong deployment target")
        require(source_inventory(root, deployed) == start["components"], "source changed during deployment")
        runtime_matches(start["components"])
        # This entry point is called only after all existing shell hashes and
        # functional smokes pass. It is not an activation receipt yet.
        result = {**start, "phase": "INSTALLATION_VERIFIED", "installation_verified_at": now(),
                  "native_deploy": "scripts/seminartext-dev deploy",
                  "native_hash_and_functional_smoke": "PASS",
                  "backup_manifest_sha256": digest((operation / "manifest.txt").read_bytes())}
        retain(operation / "installation-verified.json", encoded(result))
        return result


def validate_integrity(report, installed_record, source_contract):
    require(report.get("exit_code") == 0 and not report.get("internal_errors"), "Integrity failed")
    require(report.get("head_sha") == installed_record["source_commit"], "Integrity belongs to another source")
    require(report.get("deployment_dir") == installed_record["deployment_dir"], "Integrity belongs to another target")
    gates = {g["id"]: g for g in report["gates"]}
    require(len(gates) == len(report["gates"]), "duplicate Integrity gate")
    for declaration in source_contract["gates"]:
        if declaration["blocking_policy"] == "blocking":
            require(gates.get(declaration["id"], {}).get("status") == "PASS",
                    "incomplete native gate: " + declaration["id"])
    require(gates["G1"]["evidence"]["working_tree_clean"], "source is dirty")
    require(gates["G7"]["evidence"]["passed"] > 0 and gates["G7"]["evidence"]["skipped"] == 0,
            "required tests incomplete")
    runtime = gates["G2"]["evidence"]
    require(runtime.get("functional_smoke", {}).get("status") == "PASS", "functional smoke missing")
    expected = {row["id"]: row for row in installed_record["components"]}
    actual = runtime["components"]
    require(len(actual) == len(expected), "incomplete runtime inventory")
    require({row["id"] for row in actual} == set(expected), "wrong runtime inventory")
    for row in actual:
        declared = expected[row["id"]]
        require(row["deployment_status"] == "SYNC" and row["repository_sha256"] == declared["sha256"]
                and row["deployed_sha256"] == declared["sha256"]
                and row["deployed_path"] == declared["deployed_path"], "runtime identity differs from deployment")


def complete(root, deployed, operation):
    with mutation_lock(operation):
        record = read(operation / "installation-verified.json")
        current_operation(operation, record)
        require(record.get("phase") == "INSTALLATION_VERIFIED"
                and record.get("native_hash_and_functional_smoke") == "PASS", "installation evidence incomplete")
        require(record["deployment_dir"] == str(deployed), "wrong deployment target")
        require(record["source_commit"] == git(root, "rev-parse", "HEAD"), "source changed since deployment")
        require(record["contract_sha256"] == digest((root / "integrity/integrity_contract.json").read_bytes()),
                "Integrity contract changed since deployment")
        require(record["backup_manifest_sha256"] == digest((operation / "manifest.txt").read_bytes()),
                "backup manifest changed")
        runtime_matches(record["components"])
        receipt_path = operation / "activation-receipt.json"
        if receipt_path.exists():
            receipt = read(receipt_path)
            require(receipt["installation"] == record, "receipt belongs to another installation")
            validate_integrity(receipt["integrity"], record, contract(root))
            return receipt
        code, stdout, stderr = run([str(root / "scripts/seminartext-integrity"), "--json",
                                   "--deploy-dir", str(deployed)], cwd=root, timeout=1200)
        report_path = operation / ("post-deploy-integrity-" + uuid.uuid4().hex + ".json")
        retain(report_path, stdout)
        require(code == 0, "native post-deploy Integrity failed: " + stderr.decode(errors="replace")[-2000:])
        report = json.loads(stdout)
        validate_integrity(report, record, contract(root))
        runtime_matches(record["components"])
        require(record["source_commit"] == git(root, "rev-parse", "HEAD"), "source moved during post-checks")
        require(not git(root, "status", "--porcelain"), "source became dirty during post-checks")
        require(source_inventory(root, deployed) == record["components"], "source changed during post-checks")
        require(record["contract_sha256"] == digest((root / "integrity/integrity_contract.json").read_bytes()),
                "Integrity contract changed during post-checks")
        receipt = {"schema_version": 1, "product": "seminartext", "status": "SUCCEEDED",
                   "activated_at": now(), "target": deployed.as_uri(), "installation": record,
                   "integrity": report, "integrity_contract": contract(root),
                   "integrity_report_sha256": digest(stdout),
                   "scope": "Native technical activation; not semantic acceptance or full product MVP acceptance."}
        retain(receipt_path, encoded(receipt))
        return receipt


def rollback_complete(root, deployed, operation):
    """Record the restored bytes; never infer their source from a deploy manifest."""
    with mutation_lock(operation):
        start = read(operation / "activation-operation.json")
        current_operation(operation, start)
        require(start["action"] == "rollback" and start["deployment_dir"] == str(deployed),
                "wrong rollback operation or target")
        require(start["source_commit"] == git(root, "rev-parse", "HEAD") and
                start["contract_sha256"] == digest((root / "integrity/integrity_contract.json").read_bytes()),
                "rollback verifier or contract changed during restoration")
        backup = Path(start["restored_from_backup"])
        rows = []
        for item in contract(root)["runtime_components"]:
            old = backup / item["deployed_name"]
            live = deployed / item["deployed_name"]
            old_hash = digest(old.read_bytes()) if old.is_file() and not old.is_symlink() else None
            live_hash = digest(live.read_bytes()) if live.is_file() and not live.is_symlink() else None
            rows.append({"id": item["id"], "backup_path": str(old), "deployed_path": str(live),
                         "backup_sha256": old_hash, "sha256": live_hash,
                         "status": "MATCH" if old_hash is not None and old_hash == live_hash else "INCOMPLETE"})
        checks = []
        cli = next(Path(row["deployed_path"]) for row in rows if row["id"] == "cli")
        state = deployed / "SEMINARTEXT_4_STATE.json"
        for command in (["bash", "-n", str(cli)], [sys.executable, "-m", "json.tool", str(state)],
                        [str(cli), "project-evidence-check", "--help"],
                        [str(cli), "project-obsidian-export", "--help"]):
            try:
                code, _, stderr = run(command, cwd=deployed, timeout=15)
                checks.append({"command": command, "status": "PASS" if code == 0 else "FAIL",
                               "exit_code": code, "stderr_tail": stderr.decode(errors="replace")[-1000:]})
            except (OSError, Incomplete) as error:
                checks.append({"command": command, "status": "FAIL", "error": str(error)})
        verified = all(row["status"] == "MATCH" for row in rows) and all(
            check["status"] == "PASS" for check in checks)
        inspection = {"schema_version": 1, "action": "rollback", "operation": start,
                      "status": "VERIFIED" if verified else "INCOMPLETE", "inspected_at": now(),
                      "components": rows, "functional_checks": checks}
        receipt_path = operation / "rollback-receipt.json"
        if receipt_path.exists():
            receipt = read(receipt_path)
            require(receipt["operation"] == start, "rollback receipt belongs to another operation")
            require(verified and receipt["components"] == rows, "restored runtime changed since receipt")
            return receipt
        retain(operation / ("rollback-inspection-" + uuid.uuid4().hex + ".json"), encoded(inspection))
        require(verified, "restoration inventory or native functional verification incomplete")
        version = (deployed / "SEMINARTEXT_VERSION").read_text().strip()
        require(bool(version), "restored version missing")
        receipt = {"schema_version": 1, "product": "seminartext", "action": "rollback",
                   "status": "SUCCEEDED", "activated_at": now(), "target": deployed.as_uri(),
                   "operation": start, "restored_from_backup": str(backup), "version": version,
                   "components": rows, "functional_checks": checks,
                   "scope": "Verified native restoration; registration requires an exact historical target."}
        retain(receipt_path, encoded(receipt))
        return receipt


def central_module(registry_root):
    origin = git(registry_root, "remote", "get-url", "origin").removesuffix(".git")
    require(origin in {"https://github.com/Yurielo/four-product-architecture",
                       "git@github.com:Yurielo/four-product-architecture"}, "wrong central repository")
    require(not git(registry_root, "diff", "HEAD", "--", "registry.py", "schemas/registry.schema.json"),
            "central publisher/schema has local modifications")
    spec = importlib.util.spec_from_file_location("four_product_registry", registry_root / "registry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_publication(operation, registry_root, central):
    if (operation / "rollback-receipt.json").is_file():
        return prepare_rollback_publication(operation, registry_root, central)
    receipt = read(operation / "activation-receipt.json")
    record = receipt["installation"]
    require(receipt["product"] == "seminartext" and receipt["status"] == "SUCCEEDED", "native receipt incomplete")
    current_operation(operation, record)
    runtime_matches(record["components"])
    validate_integrity(receipt["integrity"], record, receipt["integrity_contract"])
    release = {"native_ref": (operation / "activation-receipt.json").as_uri(),
               "version": record["version"], "build": None, "source_commit": record["source_commit"],
               "artifacts": [{"role": row["id"], "location": row["deployed_path"],
                              "source_commit": record["source_commit"],
                              "digest": {"algorithm": "sha256-file", "value": row["sha256"]}}
                             for row in record["components"]]}
    event_path = operation / "publication-event.json"
    if event_path.exists():
        event = central.decode(event_path.read_bytes())
        proof = read(operation / "publication-evidence.json")
        require(event["product"] == "seminartext" and event["action"] == "activate"
                and event["rollback_of"] is None and event["release"] == release
                and event["target"] == receipt["target"] and event["dependencies"] == []
                and event["activated_at"] == receipt["activated_at"], "pending event differs from native receipt")
        require(proof["native_evidence"] == receipt and proof["subject_sha256"] == central.subject_hash(event),
                "pending evidence differs from native receipt")
        return event
    base = record["registry_base_head"]
    if base is None:
        base = central.remote_head(registry_root)
    state = central.decode(central.at(registry_root, base, "registry.json"))
    central.validate(state, central.decode(central.at(registry_root, base, central.SCHEMA)),
                     lambda path: central.at(registry_root, base, path))
    previous = state["products"]["seminartext"]["current"]
    require(record["registry_base_head"] is not None or previous is None,
            "no deployment-time predecessor; cannot replace an existing activation")
    predecessor = next((e for e in state["history"] if e["event_id"] == previous), None)
    event = {"product": "seminartext", "generation": predecessor["generation"] + 1 if predecessor else 1,
             "predecessor": previous, "action": "activate", "rollback_of": None,
             "target": receipt["target"], "activated_at": receipt["activated_at"],
             "recorded_at": receipt["activated_at"], "dependencies": [],
             "release": release}
    proof = {"kind": "native_activation", "status": "SUCCEEDED", "subject_sha256": central.subject_hash(event),
             "native_reference": event["release"]["native_ref"], "native_evidence": receipt}
    payload = central.encode(proof)
    path = "evidence/seminartext-activation-" + digest(payload) + ".json"
    # Keep the exact proof in the native outbox as well as staging it centrally.
    retain(operation / "publication-evidence.json", payload)
    event["evidence"] = [{"path": path, "sha256": digest(payload)}]
    event["event_id"] = central.event_id(event)
    retain(event_path, central.encode(event))
    return event


def prepare_rollback_publication(operation, registry_root, central):
    receipt = read(operation / "rollback-receipt.json")
    start = receipt["operation"]
    require(receipt["product"] == "seminartext" and receipt["action"] == "rollback"
            and receipt["status"] == "SUCCEEDED", "native rollback receipt incomplete")
    current_operation(operation, start)
    require(start["action"] == "rollback", "wrong rollback operation")
    require(receipt["target"] == Path(start["deployment_dir"]).as_uri(), "rollback target changed")
    declarations = contract(Path(start["source_root"]))["runtime_components"]
    require(start["contract_sha256"] == digest((Path(start["source_root"]) / "integrity/integrity_contract.json").read_bytes()),
            "rollback inventory contract changed")
    expected_paths = {(item["id"], str(Path(start["restored_from_backup"]) / item["deployed_name"]),
                       str(Path(start["deployment_dir"]) / item["deployed_name"])) for item in declarations}
    actual_paths = {(row["id"], row["backup_path"], row["deployed_path"]) for row in receipt["components"]}
    require(len(actual_paths) == len(receipt["components"]) == len(expected_paths) and
            actual_paths == expected_paths, "rollback inventory differs from native contract")
    for row in receipt["components"]:
        backup = Path(row["backup_path"])
        require(row["status"] == "MATCH" and row["backup_sha256"] == row["sha256"]
                and backup.is_file() and not backup.is_symlink()
                and digest(backup.read_bytes()) == row["sha256"], "rollback backup changed")
    runtime_matches(receipt["components"])
    base = start["registry_base_head"]
    require(base is not None, "no pre-rollback central baseline; verify reconciliation before publication")
    state = central.decode(central.at(registry_root, base, "registry.json"))
    central.validate(state, central.decode(central.at(registry_root, base, central.SCHEMA)),
                     lambda path: central.at(registry_root, base, path))
    previous = state["products"]["seminartext"]["current"]
    if previous is None:
        record = {"schema_version": 1, "status": "RECONCILIATION_REQUIRED",
                  "rollback_receipt_sha256": digest((operation / "rollback-receipt.json").read_bytes()),
                  "registry_base_head": base, "registered_predecessor": None,
                  "reason": "no registered predecessor at rollback start"}
        retain(operation / "rollback-reconciliation-required.json", encoded(record))
        raise ReconciliationRequired(record["reason"])
    historical = [e for e in state["history"] if e["product"] == "seminartext"]
    predecessor = next((e for e in historical if e["event_id"] == previous), None)
    require(predecessor is not None, "registered predecessor absent from baseline history")
    expected = {(row["id"], row["deployed_path"], row["sha256"]) for row in receipt["components"]}
    require(len(expected) == len(receipt["components"]), "duplicate rollback component identity")
    def matches(event):
        artifacts = event["release"]["artifacts"]
        actual = {(item["role"], item["location"], item["digest"]["value"])
                  for item in artifacts if item["digest"]["algorithm"] == "sha256-file"}
        return (event["target"] == receipt["target"] and event["release"]["version"] == receipt["version"]
                and len(actual) == len(artifacts) == len(expected) and actual == expected)
    if matches(predecessor):
        return None  # Restored bytes are already the registered current release.
    candidates = [e for e in historical if e["event_id"] != previous and matches(e)]
    releases = {central.encode(e["release"]) for e in candidates}
    if not candidates or len(releases) != 1:
        record = {"schema_version": 1, "status": "RECONCILIATION_REQUIRED",
                  "rollback_receipt_sha256": digest((operation / "rollback-receipt.json").read_bytes()),
                  "registry_base_head": base, "registered_predecessor": previous,
                  "reason": "no unique registered historical release matches all restored artifacts and target"}
        retain(operation / "rollback-reconciliation-required.json", encoded(record))
        raise ReconciliationRequired(record["reason"])
    target = candidates[-1]
    event_path = operation / "publication-event.json"
    if event_path.exists():
        event = central.decode(event_path.read_bytes())
        proof = read(operation / "publication-evidence.json")
        require(event["action"] == "rollback" and event["rollback_of"] == target["event_id"]
                and event["predecessor"] == previous and event["release"] == target["release"]
                and event["target"] == target["target"] and event["dependencies"] == target["dependencies"]
                and event["activated_at"] == receipt["activated_at"],
                "pending rollback event differs from native receipt or historical target")
        require(proof["native_evidence"] == receipt and proof["subject_sha256"] == central.subject_hash(event),
                "pending rollback evidence differs from native receipt")
        return event
    event = {"product": "seminartext", "generation": predecessor["generation"] + 1,
             "predecessor": previous, "action": "rollback", "rollback_of": target["event_id"],
             "target": target["target"], "activated_at": receipt["activated_at"],
             "recorded_at": receipt["activated_at"], "dependencies": target["dependencies"],
             "release": target["release"]}
    proof = {"kind": "native_activation", "status": "SUCCEEDED", "subject_sha256": central.subject_hash(event),
             "native_reference": (operation / "rollback-receipt.json").as_uri(), "native_evidence": receipt}
    payload = central.encode(proof)
    retain(operation / "publication-evidence.json", payload)
    event["evidence"] = [{"path": "evidence/seminartext-activation-" + digest(payload) + ".json",
                          "sha256": digest(payload)}]
    event["event_id"] = central.event_id(event)
    retain(event_path, central.encode(event))
    return event


def publish(operation, registry_root):
    """Publication failure is separate from successful native activation."""
    try:
        with mutation_lock(operation):
            central = central_module(registry_root)
            event = prepare_publication(operation, registry_root, central)
            if event is None:
                head = central.remote_head(registry_root)
                state = central.decode(central.at(registry_root, head, "registry.json"))
                central.validate(state, central.decode(central.at(registry_root, head, central.SCHEMA)),
                                 lambda path: central.at(registry_root, head, path))
                current = state["products"]["seminartext"]["current"]
                latest = next(e for e in state["history"] if e["event_id"] == current)
                receipt = read(operation / "rollback-receipt.json")
                expected = {(row["id"], row["deployed_path"], row["sha256"]) for row in receipt["components"]}
                actual = {(row["role"], row["location"], row["digest"]["value"])
                          for row in latest["release"]["artifacts"] if row["digest"]["algorithm"] == "sha256-file"}
                require(len(actual) == len(latest["release"]["artifacts"]) == len(expected)
                        and actual == expected and latest["target"] == receipt["target"]
                        and latest["release"]["version"] == receipt["version"],
                        "central current changed after rollback; reconcile before retry")
                return {"status": "ALREADY_CURRENT", "head": head, "current": current,
                        "operation": str(operation)}, 0
            proof = (operation / "publication-evidence.json").read_bytes()
            require(digest(proof) == event["evidence"][0]["sha256"], "pending proof changed")
            require(event["event_id"] == central.event_id(event), "pending event changed")
            retain(registry_root / event["evidence"][0]["path"], proof)
            head = central.remote_head(registry_root)
            result = central.publish(registry_root, event, head)
            require(result.get("event_id") == event["event_id"] and
                    result.get("status") in {"PUBLISHED", "ALREADY_PUBLISHED"}, "publication not confirmed")
            retain(operation / ("publication-confirmed-" + digest(encoded(result)) + ".json"), encoded(result))
            return result, 0
    except ReconciliationRequired as error:
        return {"status": "RECONCILIATION_REQUIRED", "native_rollback": "RECEIPT_RETAINED",
                "operation": str(operation), "event_prepared": False, "reason": str(error)}, 3
    except (OSError, ValueError, KeyError, ImportError, subprocess.SubprocessError) as error:
        kind = "native_rollback" if (operation / "rollback-receipt.json").is_file() else "native_activation"
        return {"status": "PUBLICATION_PENDING", kind: "RECEIPT_RETAINED",
                "operation": str(operation), "event_prepared": (operation / "publication-event.json").exists(),
                "reason": str(error)}, 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["begin", "installed", "complete", "rollback-complete", "retry", "publish"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--deploy-dir", type=Path, required=True)
    parser.add_argument("--operation", type=Path, required=True)
    parser.add_argument("--action", choices=["deploy", "rollback"], default="deploy")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--registry-root", type=Path,
                        default=Path(os.environ.get("SEMINARTEXT_REGISTRY_REPO", "~/Documents/four-product-architecture")))
    args = parser.parse_args()
    root, deployed, operation, registry_root = [p.expanduser().resolve() for p in
                                               (args.root, args.deploy_dir, args.operation, args.registry_root)]
    try:
        if args.command == "begin":
            backup = args.backup.expanduser().resolve() if args.backup else None
            result, code = begin(root, deployed, operation, registry_root, args.action, backup), 0
        elif args.command == "installed":
            result, code = installed(root, deployed, operation), 0
        else:
            if args.command == "complete":
                complete(root, deployed, operation)
            elif args.command == "rollback-complete":
                rollback_complete(root, deployed, operation)
            # Retry never reruns deployment or native tests.
            require((operation / "activation-receipt.json").is_file()
                    or (operation / "rollback-receipt.json").is_file(), "successful native receipt missing")
            if args.command == "publish":
                result, code = publish(operation, registry_root)
            else:
                # Registry packages remain optional delivery dependencies.
                candidate = registry_root / ".venv/bin/python"
                python = os.environ.get("SEMINARTEXT_REGISTRY_PYTHON",
                                        str(candidate) if candidate.is_file() else sys.executable)
                try:
                    code, stdout, stderr = run([python, str(Path(__file__).resolve()), "publish",
                                               "--root", str(root), "--deploy-dir", str(deployed),
                                               "--operation", str(operation), "--registry-root", str(registry_root)],
                                              cwd=root, timeout=120)
                    require(code in (0, 3), stderr.decode(errors="replace"))
                    result = json.loads(stdout)
                except (OSError, ValueError) as error:
                    result, code = {"status": "PUBLICATION_PENDING", "native_activation": "RECEIPT_RETAINED",
                                    "operation": str(operation), "reason": str(error)}, 3
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print("ACTIVATION_INCOMPLETE: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
