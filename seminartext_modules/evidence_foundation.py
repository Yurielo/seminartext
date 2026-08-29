#!/usr/bin/env python3
"""Project-level Evidence Foundation lifecycle and validation commands.

The service is deliberately alignment-only: it consumes a verified transcript
and native alignment evidence, never invokes ASR and never rewrites text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schemas.validate_canonical_evidence_v1 import validate_bundle  # noqa: E402


ID_RE = re.compile(r"[^a-z0-9]+")
ZERO_SHA256 = "0" * 64
ACCEPTED_MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-russian"
ACCEPTED_MODEL_REVISION = "2329100508896c6d9b157019803ab5601e6f3406"
ACCEPTED_MODEL_SHA256 = "d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def stable_id(value: str, prefix: str) -> str:
    slug = ID_RE.sub("_", value.lower()).strip("_") or "item"
    return f"{prefix}_{slug}"[:120]


def project_root(value: str | Path) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"project directory not found: {path}")
    return path


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} cannot be read: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def atomic_write_json(path: Path, value: Any, *, overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite immutable artifact: {path}")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def source_record(project: Path, source_id: str) -> tuple[dict[str, Any], str]:
    registry_path = project / "sources.json"
    registry = load_json(registry_path, "sources.json")
    for item in [*registry.get("videos", []), *registry.get("documents", [])]:
        if item.get("source_id") == source_id:
            return item, stable_id(source_id, "source")
    raise ValueError(f"source_id not found in sources.json: {source_id}")


def media_path(project: Path, source: dict[str, Any], override: str | None) -> Path:
    if override:
        path = Path(override).expanduser().resolve()
    else:
        relative = source.get("file")
        if not relative:
            raise ValueError("source has no local media file; pass --media explicitly (YouTube is not downloaded implicitly)")
        path = (project / relative).resolve()
    if not path.is_file():
        raise ValueError(f"source media not found: {path}")
    return path


def revisions_index(project: Path) -> Path:
    return project / "evidence" / "transcript_revisions" / "index.json"


def load_revision(project: Path, revision_id: str) -> dict[str, Any]:
    path = project / "evidence" / "transcript_revisions" / f"{revision_id}.json"
    revision = load_json(path, f"transcript revision {revision_id}")
    if revision.get("revision_id") != revision_id:
        raise ValueError("transcript revision id does not match its filename")
    return revision


def promote_transcript(args: argparse.Namespace) -> int:
    project = project_root(args.project)
    source, source_canonical_id = source_record(project, args.source_id)
    text_path = Path(args.text_file).expanduser().resolve()
    if not text_path.is_file():
        raise ValueError(f"transcript text not found: {text_path}")
    text = text_path.read_text(encoding="utf-8")
    text_hash = sha256_bytes(text.encode("utf-8"))
    index_path = revisions_index(project)
    index = load_json(index_path, "transcript revision index") if index_path.is_file() else {"schema_version": 1, "revisions": []}
    existing = [item for item in index.get("revisions", []) if item.get("source_id") == source_canonical_id]
    revision_number = max((int(item.get("revision_number", 0)) for item in existing), default=0) + 1
    parent = existing[-1] if existing else None
    if args.parent_revision_id:
        parent = next((item for item in existing if item.get("revision_id") == args.parent_revision_id), None)
        if parent is None:
            raise ValueError(f"parent revision not found for source: {args.parent_revision_id}")
        revision_number = int(parent["revision_number"]) + 1
    revision_id = f"transcript_revision_{source_canonical_id.removeprefix('source_')}_r{revision_number}"
    if any(item.get("revision_id") == revision_id for item in existing):
        raise ValueError(f"revision already exists: {revision_id}; use a new parent or inspect the existing immutable file")
    if args.state != "verified" and args.reviewer:
        raise ValueError("reviewer authority is only accepted for a verified promotion")
    if args.state == "verified" and not args.reviewer:
        raise ValueError("verified promotion requires --reviewer authority")
    authority = "authoritative" if args.state == "verified" else "candidate"
    lifecycle = "verified" if args.state == "verified" else ("active" if args.state == "review_required" else "draft")
    revision = {
        "revision_id": revision_id,
        "source_id": source_canonical_id,
        "revision_number": revision_number,
        "revision_kind": "verified" if args.state == "verified" else "asr",
        "parent_revision_id": parent.get("revision_id") if parent else None,
        "parent_text_sha256": parent.get("text_sha256") if parent else None,
        "canonical_text": text,
        "text_sha256": text_hash,
        "authority": authority,
        "reviewer_authority": args.reviewer,
        "state": args.state,
        "lifecycle_status": lifecycle,
        "source_registry_id": args.source_id,
        "source_title": source.get("title", ""),
    }
    atomic_write_json(project / "evidence" / "transcript_revisions" / f"{revision_id}.json", revision)
    index.setdefault("revisions", []).append({key: revision[key] for key in ("revision_id", "source_id", "revision_number", "text_sha256", "state", "authority")})
    index["revisions"] = sorted(index["revisions"], key=lambda item: (item.get("source_id", ""), item.get("revision_number", 0)))
    atomic_write_json(index_path, index, overwrite=True)
    print(json.dumps({"status": "verified" if args.state == "verified" else args.state, "revision_id": revision_id, "text_sha256": text_hash}, ensure_ascii=False, sort_keys=True))
    return 0


def read_alignment(path: Path) -> dict[str, Any]:
    payload = load_json(path, "alignment evidence")
    words = payload.get("words")
    if not isinstance(words, list):
        raise ValueError("alignment evidence must contain a words array")
    return payload


def map_words(text: str, evidence_words: list[dict[str, Any]]) -> list[dict[str, Any] | None]:
    tokens = list(re.finditer(r"\S+", text))
    mapped: list[dict[str, Any] | None] = []
    cursor = 0
    for token in tokens:
        item = evidence_words[cursor] if cursor < len(evidence_words) else None
        if isinstance(item, dict) and item.get("word") == token.group(0):
            mapped.append(item)
            cursor += 1
        else:
            mapped.append(None)
    if cursor != len(evidence_words):
        raise ValueError(f"alignment evidence is not an exact subsequence; first extra token: {evidence_words[cursor].get('word')!r}")
    return mapped


def build_bundle(project: Path, revision: dict[str, Any], source: dict[str, Any], source_id: str, media: Path, evidence: dict[str, Any], run_id: str, config_sha: str, model: str, model_revision: str, model_sha: str, aligner: str, aligner_version: str) -> tuple[dict[str, Any], dict[str, Any]]:
    project_id = stable_id(project.name, "project")
    source_canonical_id = revision["source_id"]
    revision_id = revision["revision_id"]
    text = revision["canonical_text"]
    tokens = list(re.finditer(r"\S+", text))
    mapped = map_words(text, evidence["words"])
    duration = source.get("duration_seconds")
    if duration is None:
        ends = [item.get("end") for item in mapped if item and isinstance(item.get("end"), (int, float))]
        duration = max(ends, default=0) + 1
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError("timed source requires --duration or sources.json duration_seconds")
    cue_id = f"{revision_id}:cue:000000"
    run = {
        "id": run_id,
        "source_id": source_canonical_id,
        "source_registry_id": source_id,
        "source_content_sha256": sha256_file(media),
        "transcript_revision_id": revision_id,
        "transcript_text_sha256": revision["text_sha256"],
        "aligner": aligner,
        "aligner_version": aligner_version,
        "model": model,
        "model_revision": model_revision,
        "model_sha256": model_sha,
        "config_sha256": config_sha,
        "status": "valid",
        "review_status": "review_required" if any(item is None for item in mapped) else "verified",
        "unaligned_sequences": [i for i, item in enumerate(mapped) if item is None],
        "input_policy": "verified_transcript_only_no_asr",
    }
    canonical_run = {key: run[key] for key in (
        "id", "source_id", "source_content_sha256", "transcript_revision_id",
        "transcript_text_sha256", "aligner", "aligner_version", "model",
        "model_revision", "model_sha256", "config_sha256", "status"
    )}
    words = []
    for sequence, (token, aligned) in enumerate(zip(tokens, mapped)):
        if aligned is None:
            start = end = confidence = None
            status = "unaligned"
            provenance = {"kind": "unavailable", "alignment_run_id": None, "method": None}
            flags = ["unaligned_review_required"]
        else:
            start, end = aligned.get("start"), aligned.get("end")
            confidence = aligned.get("score")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start or start < 0 or end > duration:
                raise ValueError(f"alignment interval invalid for token {sequence}")
            status = "aligned"
            provenance = {"kind": "forced_alignment", "alignment_run_id": run_id, "method": "native_word_intervals"}
            flags = []
        words.append({
            "id": f"{revision_id}:word:{sequence:06d}",
            "source_id": source_canonical_id,
            "transcript_revision_id": revision_id,
            "sequence": sequence,
            "char_start": token.start(),
            "char_end": token.end(),
            "text": token.group(0),
            "normalized_text": None,
            "source_cue_ids": [cue_id],
            "start_seconds": start,
            "end_seconds": end,
            "alignment_status": status,
            "confidence": confidence,
            "speaker_id": None,
            "timing_provenance": provenance,
            "qa_flags": flags,
            "lifecycle_status": "verified",
        })
    segments = []
    for sequence, offset in enumerate(range(0, len(words), 50)):
        group = words[offset : offset + 50]
        segments.append({"id": f"benchmark_segment_{revision_id.removeprefix('transcript_revision_')}_{sequence:06d}", "transcript_revision_id": revision_id, "sequence": sequence, "word_start_id": group[0]["id"], "word_end_id": group[-1]["id"], "word_count": len(group), "lifecycle_status": "verified"})
    bundle = {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.canonical_evidence",
        "artifact_id": stable_id(f"{project_id}_{revision_id}", "artifact"),
        "project": {"id": project_id, "title": project.name, "lifecycle_status": "active"},
        "sources": [{"id": source_canonical_id, "project_id": project_id, "sequence": 0, "kind": "video" if source.get("type") in {"youtube", "local"} or source.get("file", "").lower().endswith((".mp4", ".mov", ".mkv")) else "other", "title": source.get("title") or source_id, "content_sha256": run["source_content_sha256"], "duration_seconds": duration, "lifecycle_status": "active"}],
        "transcript_revisions": [{"id": revision_id} | {key: revision[key] for key in ("source_id", "revision_number", "revision_kind", "parent_revision_id", "canonical_text", "text_sha256", "authority", "lifecycle_status")}],
        "cues": [{"id": cue_id, "transcript_revision_id": revision_id, "sequence": 0, "char_start": 0, "char_end": len(text), "text": text, "source_locator": {"type": "time_interval", "start_seconds": 0, "end_seconds": duration}, "lifecycle_status": "verified"}],
        "alignment_runs": [canonical_run],
        "words": words,
        "benchmark_segments": segments,
        "topics": [],
        "evidence_refs": [],
    }
    errors = validate_bundle(bundle)
    if errors:
        raise ValueError("canonical cross-record validation failed:\n" + "\n".join(errors))
    return bundle, run


def align_project(args: argparse.Namespace) -> int:
    project = project_root(args.project)
    source, source_canonical_id = source_record(project, args.source_id)
    revision = load_revision(project, args.revision_id)
    if revision.get("state") != "verified" or revision.get("authority") != "authoritative":
        raise ValueError("alignment requires an authoritative verified TranscriptRevision; no provisional text may be aligned")
    media = media_path(project, source, args.media)
    evidence_path = Path(args.alignment_json).expanduser().resolve() if args.alignment_json else None
    if evidence_path is None or not evidence_path.is_file():
        raise ValueError("native alignment evidence is required; WhisperX ASR is never run as a semantic replacement")
    evidence = read_alignment(evidence_path)
    config = evidence.get("config", {"mode": "native_alignment_evidence"})
    config_sha = sha256_bytes(canonical_json(config))
    model = evidence.get("model", ACCEPTED_MODEL)
    model_revision = evidence.get("model_revision", ACCEPTED_MODEL_REVISION)
    model_sha = evidence.get("model_sha256", ACCEPTED_MODEL_SHA256)
    if not isinstance(model_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", model_sha):
        raise ValueError("alignment model_sha256 must be lowercase SHA-256")
    evidence_hash = sha256_file(evidence_path)
    run_id = f"alignment_{source_canonical_id.removeprefix('source_')}_{revision['revision_id'].removeprefix('transcript_revision_')}_{evidence_hash[:12]}"
    run_path = project / "evidence" / "alignment_runs" / f"{run_id}.json"
    bundle_path = project / "evidence" / "canonical_bundle.json"
    if run_path.is_file() and bundle_path.is_file():
        print(json.dumps({"status": "RESUMED", "alignment_run_id": run_id, "bundle": str(bundle_path)}, ensure_ascii=False, sort_keys=True))
        return 0
    bundle, run = build_bundle(project, revision, source, args.source_id, media, evidence, run_id, config_sha, model, model_revision, model_sha, evidence.get("aligner", "whisperx"), evidence.get("aligner_version", "3.8.6"))
    atomic_write_json(run_path, run)
    payload = json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(payload, encoding="utf-8")
    timeline = {"schema_version": "1.0.0", "source": "canonical_bundle.json", "transcript_revision_id": revision["revision_id"], "alignment_run_id": run_id, "words": bundle["words"]}
    atomic_write_json(project / "evidence" / "word_timeline.json", timeline, overwrite=True)
    manifest = {"schema_version": 1, "bundle_path": "evidence/canonical_bundle.json", "bundle_sha256": sha256_bytes(payload.encode("utf-8")), "transcript_revision_id": revision["revision_id"], "alignment_run_id": run_id, "source_content_sha256": run["source_content_sha256"], "review_status": run["review_status"]}
    atomic_write_json(project / "evidence" / "manifest.json", manifest, overwrite=True)
    output_bindings = []
    for candidate in (
        project / "transcript" / args.source_id / "transcript.txt",
        project / "transcript" / args.source_id / "transcript.srt",
        project / "transcript" / f"{args.source_id}.json",
        project / "transcript" / "combined.json",
    ):
        if candidate.is_file():
            output_bindings.append({"path": str(candidate.relative_to(project)), "sha256": sha256_file(candidate), "transcript_revision_id": revision["revision_id"], "canonical_bundle_sha256": manifest["bundle_sha256"]})
    atomic_write_json(project / "evidence" / "output_bindings.json", {"schema_version": 1, "bindings": output_bindings}, overwrite=True)
    print(json.dumps({"status": run["review_status"], "alignment_run_id": run_id, "bundle": str(bundle_path), "unaligned_words": run["unaligned_sequences"]}, ensure_ascii=False, sort_keys=True))
    return 0


def evidence_check(args: argparse.Namespace) -> int:
    project = project_root(args.project)
    bundle_path = Path(args.bundle).expanduser().resolve() if args.bundle else project / "evidence" / "canonical_bundle.json"
    try:
        bundle = load_json(bundle_path, "canonical bundle")
    except ValueError as exc:
        result = {"status": "FAIL", "errors": [str(exc)], "bundle": str(bundle_path)}
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) if args.json else "FAIL: " + str(exc))
        return 1
    errors = validate_bundle(bundle)
    manifest_path = project / "evidence" / "manifest.json"
    if manifest_path.is_file():
        manifest = load_json(manifest_path, "evidence manifest")
        actual_hash = sha256_file(bundle_path)
        if manifest.get("bundle_sha256") != actual_hash:
            errors.append("manifest bundle_sha256 does not match canonical bundle")
        if manifest.get("transcript_revision_id") not in {item.get("id") for item in bundle.get("transcript_revisions", [])}:
            errors.append("manifest transcript_revision_id is not present in canonical bundle")
    bindings_path = project / "evidence" / "output_bindings.json"
    if bindings_path.is_file():
        bindings = load_json(bindings_path, "output bindings")
        bundle_revision_ids = {item.get("id") for item in bundle.get("transcript_revisions", [])}
        for binding in bindings.get("bindings", []):
            output = project / binding.get("path", "")
            if not output.is_file():
                errors.append(f"bound output is missing: {binding.get('path')}")
                continue
            if binding.get("sha256") != sha256_file(output):
                errors.append(f"bound output hash mismatch: {binding.get('path')}")
            if binding.get("transcript_revision_id") not in bundle_revision_ids:
                errors.append(f"bound output references unknown revision: {binding.get('path')}")
            if binding.get("canonical_bundle_sha256") != sha256_file(bundle_path):
                errors.append(f"bound output canonical hash mismatch: {binding.get('path')}")
    schema_status = "SKIPPED_BY_OPTION"
    if not args.cross_record_only:
        try:
            from jsonschema import Draft202012Validator
            schema = json.loads((ROOT / "schemas" / "canonical_evidence_v1.schema.json").read_text(encoding="utf-8"))
            schema_errors = sorted(Draft202012Validator(schema).iter_errors(bundle), key=lambda item: list(item.path))
            errors.extend(f"JSON Schema: {error.message}" for error in schema_errors)
            schema_status = "PASS" if not schema_errors else "FAIL"
        except ImportError:
            errors.append("JSON Schema validator unavailable; install requirements-dev.txt in an isolated environment")
            schema_status = "UNAVAILABLE"
    result = {"status": "PASS" if not errors else "FAIL", "bundle": str(bundle_path), "cross_record": "PASS" if not validate_bundle(bundle) else "FAIL", "json_schema": schema_status, "errors": sorted(set(errors))}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{result['status']}: {bundle_path}")
        print(f"  cross-record={result['cross_record']} json-schema={schema_status}")
        for error in result["errors"]:
            print(f"  - {error}")
    return 0 if result["status"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    promote = sub.add_parser("promote-transcript")
    promote.add_argument("project")
    promote.add_argument("--source-id", required=True)
    promote.add_argument("--text-file", required=True)
    promote.add_argument("--state", choices=["provisional", "review_required", "verified", "superseded"], default="provisional")
    promote.add_argument("--reviewer")
    promote.add_argument("--parent-revision-id")
    align = sub.add_parser("align")
    align.add_argument("project")
    align.add_argument("--source-id", required=True)
    align.add_argument("--revision-id", required=True)
    align.add_argument("--media")
    align.add_argument("--alignment-json")
    check = sub.add_parser("evidence-check")
    check.add_argument("project")
    check.add_argument("--bundle")
    check.add_argument("--cross-record-only", action="store_true")
    check.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "promote-transcript":
            return promote_transcript(args)
        if args.command == "align":
            return align_project(args)
        return evidence_check(args)
    except (ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
