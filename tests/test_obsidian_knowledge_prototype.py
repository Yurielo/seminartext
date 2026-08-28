#!/usr/bin/env python3
"""Focused validation for the bounded Obsidian Knowledge Prototype."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "analysis" / "obsidian_knowledge_prototype"
EXPORTER = PROTOTYPE / "export_obsidian_vault.py"
VAULT = PROTOTYPE / "vault"
MANIFEST = PROTOTYPE / "export_manifest.json"
SLICE = ROOT / "analysis" / "golden_knowledge_slice" / "golden_knowledge_slice.json"
CANONICAL = ROOT / "analysis" / "word_timeline_mvp" / "canonical_evidence_bundle.json"
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def load_exporter():
    spec = importlib.util.spec_from_file_location("obsidian_exporter", EXPORTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXPORTER_MODULE = load_exporter()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    marker = text.find("\n---\n", 4)
    assert marker > 4
    metadata = json.loads(text[4:marker])
    body = text[marker + 5 :]
    assert body.startswith("\n# ")
    assert text.endswith("\n")
    return metadata, body


def committed_files() -> dict[str, bytes]:
    return {
        path.relative_to(VAULT).as_posix(): path.read_bytes()
        for path in sorted(VAULT.rglob("*.md"))
    }


def test_export_is_byte_deterministic_and_matches_committed_fixture():
    first_files, first_manifest = EXPORTER_MODULE.build_vault(SLICE, CANONICAL)
    second_files, second_manifest = EXPORTER_MODULE.build_vault(SLICE, CANONICAL)
    assert first_files == second_files == committed_files()
    assert first_manifest == second_manifest == load_json(MANIFEST)
    assert first_manifest["generated_note_count"] == 25


def test_bounded_vault_structure_and_counts_are_exact():
    expected_counts = {
        ".": 2,
        "Seminars": 1,
        "Sources": 1,
        "Topics": 3,
        "Concepts": 7,
        "Evidence": 10,
        "_meta": 1,
    }
    observed = {name: 0 for name in expected_counts}
    for path in VAULT.rglob("*.md"):
        parent = path.parent.relative_to(VAULT).as_posix()
        observed[parent] += 1
    assert observed == expected_counts


def test_frontmatter_is_valid_json_yaml_subset_with_unique_stable_ids():
    stable_ids = []
    for path in VAULT.rglob("*.md"):
        metadata, _ = parse_note(path)
        # A JSON object is a strict YAML 1.2 mapping, while remaining dependency-free.
        assert metadata["export_schema_version"] == "1.0.0"
        assert metadata["lifecycle_status"] == "derived_view"
        assert metadata["generated_by"] == "seminartext_obsidian_bounded_exporter"
        assert metadata["derived_from_artifact_id"] == "golden_slice_stress_code_video_001_v1"
        assert metadata["derived_from_artifact_sha256"] == EXPORTER_MODULE.EXPECTED_SLICE_SHA256
        stable_ids.append(metadata["stable_id"])
    assert len(stable_ids) == len(set(stable_ids)) == 25


def test_every_wikilink_resolves_inside_portable_vault():
    available = {
        path.relative_to(VAULT).with_suffix("").as_posix()
        for path in VAULT.rglob("*.md")
    }
    referenced = set()
    for path in VAULT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in WIKILINK_RE.findall(text):
            target = target.removesuffix(".md")
            assert target in available, f"{path}: unresolved [[{target}]]"
            referenced.add(target)
    # Every entity note participates in navigation; only the start note is an entry point.
    entity_notes = {
        path.relative_to(VAULT).with_suffix("").as_posix()
        for folder in ("Seminars", "Sources", "Topics", "Concepts", "Evidence", "_meta")
        for path in (VAULT / folder).glob("*.md")
    }
    assert entity_notes <= referenced


def test_every_evidence_note_resolves_to_canonical_source_words_and_time():
    document = load_json(SLICE)
    canonical = load_json(CANONICAL)
    words = {item["id"]: item for item in canonical["words"]}
    source = canonical["sources"][0]
    evidence = {item["id"]: item for item in document["evidence"]}
    for evidence_id, item in evidence.items():
        metadata, body = parse_note(VAULT / "Evidence" / f"{evidence_id}.md")
        assert metadata["stable_id"] == evidence_id
        assert metadata["canonical_source_id"] == source["id"] == item["canonical_source_id"]
        assert metadata["canonical_word_start_id"] in words
        assert metadata["canonical_word_end_id"] in words
        assert metadata["start_seconds"] == item["locator"]["start_seconds"]
        assert metadata["end_seconds"] == item["locator"]["end_seconds"]
        assert metadata["timing_status"] == item["timing_status"]
        assert metadata["unaligned_word_ids"] == item["unaligned_word_ids"]
        assert item["quote"] in body.replace("> ", "").replace("\n>\n", "\n\n")
        assert "[[_meta/canonical_evidence_reference|Canonical Evidence]]" in body


def test_topic_and_provisional_concept_claims_have_evidence_links():
    document = load_json(SLICE)
    for item in document["topics"]:
        metadata, body = parse_note(VAULT / "Topics" / f"{item['id']}.md")
        assert metadata["evidence_ids"] == item["evidence_ids"]
        for evidence_id in item["evidence_ids"]:
            assert f"[[Evidence/{evidence_id}|" in body
    for item in document["concepts"]:
        metadata, body = parse_note(VAULT / "Concepts" / f"{item['id']}.md")
        assert metadata["derivation_status"] == "provisional_manual_curation"
        assert metadata["review_status"] == "product_review_required"
        assert "**PROVISIONAL — Product Review required.**" in body
        for evidence_id in item["evidence_ids"]:
            assert f"[[Evidence/{evidence_id}|" in body


def test_canonical_pointer_is_repo_relative_hash_locked_and_resolves():
    metadata, body = parse_note(VAULT / "_meta" / "canonical_evidence_reference.md")
    assert metadata["canonical_evidence_repo_path"] == CANONICAL.relative_to(ROOT).as_posix()
    assert metadata["canonical_artifact_sha256"] == EXPORTER_MODULE.sha256_file(CANONICAL)
    match = re.search(r"\[Open canonical JSON\]\(([^)]+)\)", body)
    assert match
    resolved = ((VAULT / "_meta") / match.group(1)).resolve()
    assert resolved == CANONICAL.resolve()
    assert resolved.is_file()


def test_portable_fixture_has_no_absolute_machine_paths():
    forbidden = ("/Users/", "/tmp/", "file://", "vscode://")
    for path in VAULT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden), path
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    assert not any(value in manifest_text for value in forbidden)


def test_rebuild_is_idempotent_and_refuses_unmanaged_markdown(tmp_path):
    files, manifest = EXPORTER_MODULE.build_vault(SLICE, CANONICAL)
    output = tmp_path / "vault"
    manifest_path = tmp_path / "manifest.json"
    EXPORTER_MODULE.export_vault(files, output, manifest, manifest_path)
    first = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*.md")
    }
    EXPORTER_MODULE.export_vault(files, output, manifest, manifest_path)
    second = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*.md")
    }
    assert first == second == files
    assert len(second) == 25

    unmanaged = output / "manual-note.md"
    unmanaged.write_text("manual", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing to delete unmanaged Markdown"):
        EXPORTER_MODULE.export_vault(files, output, manifest, manifest_path)


def test_exporter_rejects_changed_golden_slice_hash(tmp_path):
    changed = load_json(SLICE)
    changed["seminar"]["title"] = "Changed"
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="Golden Slice SHA-256 mismatch"):
        EXPORTER_MODULE.build_vault(path, CANONICAL)
