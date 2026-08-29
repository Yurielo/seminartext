#!/usr/bin/env python3
"""Read-only dependency/model profile diagnostics for SeminarText."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "dependencies" / "dependency_profiles.json"


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def version_tuple(value: str) -> tuple[int, int, int]:
    numbers = re.findall(r"\d+", value)
    return tuple((int(x) for x in (numbers + ["0", "0"])[:3]))  # type: ignore[return-value]


def satisfies(version: str, constraint: str) -> bool:
    current = version_tuple(version)
    bounds = re.fullmatch(r">=(\d+)\.(\d+),<(\d+)\.(\d+)", constraint)
    if not bounds:
        raise ValueError(f"Unsupported Python constraint: {constraint}")
    low = (int(bounds.group(1)), int(bounds.group(2)), 0)
    high = (int(bounds.group(3)), int(bounds.group(4)), 0)
    return current >= low and current < high


def profile_status(name: str, profile: dict[str, Any], python_version: str) -> dict[str, Any]:
    req = ROOT / profile["requirements"]
    lock = ROOT / profile["lock"]
    version_ok = satisfies(python_version, profile["supported_python"])
    files_ok = req.is_file() and lock.is_file()
    status = "PASS" if version_ok and files_ok else "FAIL"
    reasons = []
    if not version_ok:
        reasons.append(
            f"Python {python_version} is outside {profile['supported_python']} "
            f"(reconstruct with Python {profile['lock_python']})"
        )
    if not req.is_file():
        reasons.append(f"missing requirements file: {profile['requirements']}")
    if not lock.is_file():
        reasons.append(f"missing lock file: {profile['lock']}")
    return {
        "profile": name,
        "status": status,
        "python": python_version,
        "supported_python": profile["supported_python"],
        "lock_python": profile["lock_python"],
        "requirements": profile["requirements"],
        "lock": profile["lock"],
        "reasons": reasons,
    }


def check_model(path: str | None) -> dict[str, Any]:
    model = load_contract()["models"]["russian_alignment"]
    if not path:
        cache_root = os.environ.get(model["cache_root_env"])
        return {
            "model": model["model_id"],
            "revision": model["revision"],
            "status": "WARN",
            "message": (
                "No model file supplied; set --path to a cached artifact. "
                f"Use {model['cache_root_env']} for cache root and "
                f"{model['offline_env']}={model['offline_value']} for offline mode."
            ),
            "cache_root": cache_root,
        }
    candidate = Path(path)
    if not candidate.is_file():
        return {"model": model["model_id"], "status": "FAIL", "message": f"model file not found: {path}"}
    digest_context = hashlib.sha256()
    with candidate.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest_context.update(chunk)
    digest = digest_context.hexdigest()
    ok = digest == model["sha256"]
    return {
        "model": model["model_id"],
        "revision": model["revision"],
        "status": "PASS" if ok else "FAIL",
        "sha256": digest,
        "expected_sha256": model["sha256"],
        "message": "Pinned model digest verified" if ok else "Model digest mismatch; refusing substitution",
    }


def check_ollama(json_path: str | None) -> dict[str, Any]:
    model = load_contract()["models"]["ollama_bge_m3"]
    payload: Any
    if json_path:
        source = Path(json_path)
        if not source.is_file():
            return {"model": model["mutable_ref"], "status": "FAIL", "message": f"file not found: {json_path}"}
        payload = json.loads(source.read_text(encoding="utf-8"))
    else:
        executable = shutil.which("ollama")
        if not executable:
            return {"model": model["mutable_ref"], "status": "WARN", "message": "ollama CLI unavailable; install it in the optional profile or provide --json"}
        try:
            completed = subprocess.run(
                [executable, "show", model["mutable_ref"], "--json"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            payload = json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            return {"model": model["mutable_ref"], "status": "FAIL", "message": f"could not inspect Ollama model: {exc}"}
    serialized = json.dumps(payload, sort_keys=True)
    digest = payload.get("digest") if isinstance(payload, dict) else None
    if not digest and isinstance(payload, dict):
        digest = payload.get("details", {}).get("digest")
    if isinstance(digest, str):
        digest = digest.removeprefix("sha256:")
    ok = digest == model["expected_digest"]
    return {
        "model": model["mutable_ref"],
        "status": "PASS" if ok else "FAIL",
        "resolved_digest": digest,
        "expected_digest": model["expected_digest"],
        "message": "Resolved Ollama digest verified" if ok else "Digest missing or mismatched; mutable tag is not accepted",
        "payload_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
    }


def emit(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for row in payload:
            print(f"{row['status']}: {row.get('profile', row.get('model', 'check'))}")
            for reason in row.get("reasons", []):
                print(f"  - {reason}")
            if row.get("message"):
                print(f"  - {row['message']}")
    else:
        print(f"{payload['status']}: {payload.get('model', 'check')}")
        if payload.get("message"):
            print(f"  - {payload['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "model", "ollama"])
    parser.add_argument("--profile", choices=list(load_contract()["profiles"]), help="limit doctor to one profile")
    parser.add_argument("--path", help="alignment model artifact to hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--ollama-json", help="captured `ollama show MODEL --json` payload")
    args = parser.parse_args(argv)
    contract = load_contract()
    python_version = platform.python_version()
    if args.action == "doctor":
        names = [args.profile] if args.profile else list(contract["profiles"])
        rows = [profile_status(name, contract["profiles"][name], python_version) for name in names]
        emit(rows, args.as_json)
        # Optional profiles are allowed to be unavailable in an all-profile report;
        # an explicitly requested profile must fail closed so CI can gate on it.
        hard_failure = any(
            row["status"] == "FAIL"
            and (args.profile is not None or row["profile"] in {"core_product", "dev_test"})
            for row in rows
        )
        return 1 if hard_failure else 0
    result = check_model(args.path) if args.action == "model" else check_ollama(args.ollama_json)
    emit(result, args.as_json)
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
