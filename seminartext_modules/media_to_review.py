"""Fail-closed intake for explicitly selected media-to-review work.

It records only selected local media and prerequisite state.  When the accepted
WhisperX alignment profile is available, a later adapter may advance a record;
this module never invents timing, transcripts, or semantic decisions.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from seminartext_modules import human_review_workflow as review
from seminartext_modules.reviewed_knowledge_admission import persist_revision

ARTIFACT = "seminartext.media_to_review_manifest"
STATE = "seminartext.media_to_review_state"
VERSION = "1.0.0"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*$")
MEDIA = {".wav", ".mp3", ".m4a", ".mp4", ".mov", ".mkv"}


def require(ok, message):
    if not ok: raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream: return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path): return json.loads(Path(path).read_bytes())


def manifest(path):
    path = Path(path).resolve(); require(path.is_file() and not path.is_symlink(), "manifest unavailable")
    data = load(path); require(set(data) == {"artifact_type", "schema_version", "entries"}, "unsupported manifest fields")
    require(data["artifact_type"] == ARTIFACT and data["schema_version"] == VERSION, "unsupported manifest contract")
    require(isinstance(data["entries"], list) and data["entries"], "manifest entries required")
    expected = {"id", "project", "source_id", "media"}; seen = set(); entries = []
    for row in data["entries"]:
        require(isinstance(row, dict) and set(row) == expected, "unsupported entry fields")
        require(all(isinstance(row[k], str) and row[k] for k in expected), "empty manifest field")
        require(NAME.fullmatch(row["id"]) and row["id"] not in seen, "invalid or duplicate entry id")
        project, media = Path(row["project"]), Path(row["media"])
        require(project.is_absolute() and project.is_dir() and not project.is_symlink(), "project unavailable")
        require(media.is_absolute() and media.is_file() and not media.is_symlink() and media.suffix.lower() in MEDIA, "unsupported or unavailable media")
        seen.add(row["id"]); entries.append({**row, "project": str(project.resolve()), "media": str(media.resolve()), "media_sha256": digest(media)})
    return path, entries


def prerequisites():
    return {"whisper_cli": shutil.which("whisper-cli") is not None,
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "whisperx_3_8_6": importlib.util.find_spec("whisperx") is not None,
            "accepted_alignment_producer": str(Path(__file__).resolve().parents[1] / "analysis/word_alignment_decision/run_whisperx_existing_text.py")}


def write_state(directory, state):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    payload = review.canonical_bytes(state); key = hashlib.sha256(payload).hexdigest()
    persist_revision(directory / f"state-{key}.json", state)


def latest(directory):
    files = sorted(Path(directory).glob("state-*.json")); require(files, "intake has not been prepared")
    state = load(files[-1]); require(state.get("artifact_type") == STATE and state.get("schema_version") == VERSION, "invalid intake state")
    return state


def prepare(directory, source_manifest):
    source_manifest, entries = manifest(source_manifest)
    state = {"artifact_type": STATE, "schema_version": VERSION, "manifest": str(source_manifest),
             "manifest_sha256": digest(source_manifest), "entries": [{**entry, "status": "PENDING"} for entry in entries]}
    write_state(directory, state); return state


def run(directory):
    state = latest(directory); current, entries = manifest(state["manifest"])
    require(digest(current) == state["manifest_sha256"], "manifest changed after preparation")
    require([{k:v for k,v in e.items() if k != "status"} for e in state["entries"]] == entries, "selected media changed")
    available = prerequisites()
    if not all(available[k] for k in ("whisper_cli", "ffmpeg", "whisperx_3_8_6")):
        state["prerequisites"] = available
        state["status"] = "ALIGNMENT_UNAVAILABLE"
        for entry in state["entries"]: entry["status"] = "ALIGNMENT_UNAVAILABLE"
        write_state(directory, state); return state
    raise ValueError("accepted alignment adapter integration is not yet implemented")


def execute(args):
    state = prepare(args.directory, args.manifest) if args.command == "prepare" else (run(args.directory) if args.command in {"run", "resume"} else latest(args.directory))
    if args.command == "inspect":
        print("# Обработка медиа\n\n" + "\n".join(f"- {e['id']}: {e['status']}" for e in state["entries"]))
    else: print(json.dumps({"status": state.get("status", "PENDING"), "entries": len(state["entries"])}, ensure_ascii=False))
    return 1 if state.get("status") == "ALIGNMENT_UNAVAILABLE" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__); subs = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "run", "resume", "status", "inspect"):
        sub = subs.add_parser(command); sub.add_argument("directory", type=Path)
        if command == "prepare": sub.add_argument("--manifest", required=True, type=Path)
    try: raise SystemExit(execute(parser.parse_args()))
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status":"INVALID_OR_UNAVAILABLE", "error":str(exc)}, ensure_ascii=False), file=sys.stderr); raise SystemExit(1)

if __name__ == "__main__": main()
