from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
FIXTURE = ROOT / "tests" / "fixtures" / "project_knowledge_bridge"
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(CLI), *args], cwd=ROOT, text=True, capture_output=True)


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "Project knowledge bridge"
    shutil.copytree(FIXTURE, project)
    for source_id in ("video_001", "video_002"):
        target = project / "transcript" / source_id
        target.mkdir(parents=True)
        shutil.copy2(project / f"transcript_{source_id}.txt", target / "transcript.txt")
    return project


def prepare_evidence(project: Path) -> tuple[str, str]:
    revisions = []
    for source_id in ("video_001", "video_002"):
        promoted = run_cli(
            "project-promote-transcript",
            str(project),
            "--source-id",
            source_id,
            "--text-file",
            str(project / f"transcript_{source_id}.txt"),
            "--state",
            "verified",
            "--reviewer",
            "fixture-reviewer",
        )
        assert promoted.returncode == 0, promoted.stderr
        revision_id = json.loads(promoted.stdout)["revision_id"]
        revisions.append(revision_id)
        aligned = run_cli(
            "project-align",
            str(project),
            "--source-id",
            source_id,
            "--revision-id",
            revision_id,
            "--alignment-json",
            str(project / f"alignment_{source_id}.json"),
            "--media",
            str(project / "source" / "video" / f"{source_id}.mp4"),
        )
        assert aligned.returncode == 0, aligned.stderr
    return revisions[0], revisions[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_input(project: Path, document: dict) -> Path:
    path = project / "changed_knowledge_input.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def rewrite_retained_source_bundle(project: Path, source_id: str, bundle: dict) -> None:
    """Keep a deliberately mutated source bundle internally hash-consistent."""
    source_root = project / "evidence" / "sources" / source_id
    current = source_root / "canonical_bundle.json"
    current.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path = source_root / "manifest.json"
    manifest = read_json(manifest_path)
    retained = source_root / "revisions" / manifest["transcript_revision_id"] / "canonical_bundle.json"
    shutil.copy2(current, retained)
    manifest["bundle_sha256"] = hashlib.sha256(current.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_second_source_is_retained_and_project_bundle_is_deterministic(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    first_promoted = run_cli(
        "project-promote-transcript",
        str(project),
        "--source-id",
        "video_001",
        "--text-file",
        str(project / "transcript_video_001.txt"),
        "--state",
        "verified",
        "--reviewer",
        "fixture-reviewer",
    )
    first_revision = json.loads(first_promoted.stdout)["revision_id"]
    first_aligned = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_001",
        "--revision-id",
        first_revision,
        "--alignment-json",
        str(project / "alignment_video_001.json"),
        "--media",
        str(project / "source/video/video_001.mp4"),
    )
    assert first_aligned.returncode == 0, first_aligned.stderr
    retained = project / "evidence/sources/source_video_001/canonical_bundle.json"
    first_hash = hashlib.sha256(retained.read_bytes()).hexdigest()

    second_promoted = run_cli(
        "project-promote-transcript",
        str(project),
        "--source-id",
        "video_002",
        "--text-file",
        str(project / "transcript_video_002.txt"),
        "--state",
        "verified",
        "--reviewer",
        "fixture-reviewer",
    )
    second_revision = json.loads(second_promoted.stdout)["revision_id"]
    second_aligned = run_cli(
        "project-align",
        str(project),
        "--source-id",
        "video_002",
        "--revision-id",
        second_revision,
        "--alignment-json",
        str(project / "alignment_video_002.json"),
        "--media",
        str(project / "source/video/video_002.mp4"),
    )
    assert second_aligned.returncode == 0, second_aligned.stderr
    assert hashlib.sha256(retained.read_bytes()).hexdigest() == first_hash
    assert (project / f"evidence/sources/source_video_001/revisions/{first_revision}/canonical_bundle.json").is_file()
    assert (project / f"evidence/sources/source_video_002/revisions/{second_revision}/canonical_bundle.json").is_file()

    bundle = read_json(project / "evidence/canonical_bundle.json")
    assert [item["id"] for item in bundle["sources"]] == ["source_video_001", "source_video_002"]
    assert len(bundle["transcript_revisions"]) == 2
    assert len(bundle["words"]) == 4
    assert {item["transcript_revision_id"] for item in bundle["words"]} == {first_revision, second_revision}
    manifest = read_json(project / "evidence/manifest.json")
    assert manifest["source_count"] == 2
    assert manifest["registered_source_count"] == 2
    assert manifest["all_registered_sources_composed"] is True
    assert {item["evidence_status"] for item in manifest["registry_coverage"]} == {"COMPOSED"}
    assert len(manifest["sources"]) == 2
    checked = run_cli("project-evidence-check", str(project), "--json")
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_dry_run_writes_nothing_and_export_is_byte_deterministic(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    destination = tmp_path / "vault"
    dry = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--destination",
        str(destination),
        "--dry-run",
    )
    assert dry.returncode == 0, dry.stderr
    report = json.loads(dry.stdout)
    assert report["status"] == "DRY_RUN"
    assert report["source_count"] == 2
    assert report["topic_count"] == 2
    assert report["concept_count"] == 1
    assert report["evidence_count"] == 2
    assert report["locator_types"] == ["time_interval"]
    assert not destination.exists()
    assert not (project / "knowledge").exists()

    first = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--destination",
        str(destination),
    )
    assert first.returncode == 0, first.stderr
    first_tree = tree_bytes(destination)
    first_knowledge = tree_bytes(project / "knowledge")
    second = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--destination",
        str(destination),
    )
    assert second.returncode == 0, second.stderr
    assert tree_bytes(destination) == first_tree
    assert tree_bytes(project / "knowledge") == first_knowledge

    canonical = read_json(project / "knowledge/canonical_evidence.json")
    knowledge = read_json(project / "knowledge/canonical_knowledge.json")
    source_evidence = read_json(project / "knowledge/source_evidence.json")
    supplied = read_json(project / "knowledge_input.json")
    assert len(canonical["sources"]) == 2
    assert [item["id"] for item in canonical["topics"]] == ["topic_source_one", "topic_source_two"]
    assert knowledge["topics"] == supplied["topics"]
    assert knowledge["concepts"] == supplied["concepts"]
    assert [item["claim"] for item in source_evidence["evidence"]] == [
        item["claim"] for item in supplied["evidence"]
    ]


def test_explicit_unavailable_semantic_input_remains_partial(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    destination = tmp_path / "partial-vault"
    result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input_partial.json"),
        "--destination",
        str(destination),
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["full_seminar_coverage"] is False
    coverage = read_json(project / "knowledge/coverage.json")
    by_source = {item["source_id"]: item for item in coverage["sources"]}
    assert by_source["source_video_001"]["status"] == "COVERED"
    assert by_source["source_video_002"]["status"] == "SEMANTIC_INPUT_UNAVAILABLE"
    assert by_source["source_video_002"]["topic_ids"] == []
    assert "SEMANTIC_INPUT_UNAVAILABLE" in (destination / "_meta/coverage.md").read_text(encoding="utf-8")


def test_generated_links_resolve_and_provisional_status_is_visible(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    destination = tmp_path / "vault"
    result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--destination",
        str(destination),
    )
    assert result.returncode == 0, result.stderr
    available = {
        path.relative_to(destination).with_suffix("").as_posix()
        for path in destination.rglob("*.md")
    }
    for path in destination.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert '"ownership_class": "MANAGED_GENERATED"' in text
        for target in WIKILINK_RE.findall(text):
            assert target.removesuffix(".md") in available, f"{path}: {target}"
    concept = (destination / "Concepts/concept_shared_sources.md").read_text(encoding="utf-8")
    assert "PROVISIONAL — DOMAIN_REVIEW has not accepted this Concept" in concept
    evidence = (destination / "Evidence/evidence_source_two.md").read_text(encoding="utf-8")
    assert "transcript_revision_video_002_r1:word:000000" in evidence
    assert "1.1`–`1.9" in evidence


def test_user_owned_notes_survive_and_managed_changes_or_collisions_fail(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    destination = tmp_path / "vault"
    args = (
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--destination",
        str(destination),
    )
    assert run_cli(*args).returncode == 0
    user_note = destination / "My notes.md"
    user_note.write_text("USER_OWNED\n", encoding="utf-8")
    assert run_cli(*args).returncode == 0
    assert user_note.read_text(encoding="utf-8") == "USER_OWNED\n"

    managed = destination / "Topics/topic_source_one.md"
    managed.write_text(managed.read_text(encoding="utf-8") + "manual edit\n", encoding="utf-8")
    changed = run_cli(*args)
    assert changed.returncode == 1
    assert "changed managed file" in changed.stderr

    other_destination = tmp_path / "collision"
    collision = other_destination / "Topics/topic_source_one.md"
    collision.parent.mkdir(parents=True)
    collision.write_text("USER_OWNED\n", encoding="utf-8")
    collision_result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--destination",
        str(other_destination),
    )
    assert collision_result.returncode == 1
    assert "USER_OWNED path collides" in collision_result.stderr

    symlink_destination = tmp_path / "symlink-collision"
    external = tmp_path / "external"
    symlink_destination.mkdir()
    external.mkdir()
    (symlink_destination / "Topics").symlink_to(external, target_is_directory=True)
    symlink_result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input", str(project / "knowledge_input.json"),
        "--destination", str(symlink_destination),
    )
    assert symlink_result.returncode == 1
    assert "managed output parent is a symlink" in symlink_result.stderr
    assert not list(external.iterdir())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["topic_sources"][0].__setitem__("origin", "automatic_draft"),
            "project knowledge input schema validation failed",
        ),
        (lambda value: value["topics"][0]["evidence_refs"].append("evidence_missing"), "references differ"),
        (
            lambda value: value["evidence"][0].__setitem__(
                "word_end_id", "transcript_revision_video_002_r1:word:000001"
            ),
            "cross-source or cross-revision",
        ),
        (lambda value: value["coverage"][1].__setitem__("status", "NOT_IN_SCOPE"), "hides supplied Topics"),
        (
            lambda value: value["concepts"][0].__setitem__("status", "ACCEPTED"),
            "requires explicit ACCEPT DOMAIN_REVIEW decision",
        ),
    ],
)
def test_invalid_semantic_inputs_fail_closed(tmp_path: Path, mutation, message: str) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    document = copy.deepcopy(read_json(project / "knowledge_input.json"))
    mutation(document)
    input_path = write_input(project, document)
    result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(input_path),
        "--destination",
        str(tmp_path / "vault"),
        "--dry-run",
    )
    assert result.returncode == 1
    assert message in result.stderr
    assert not (project / "knowledge").exists()


def test_composition_rejects_hash_project_and_duplicate_identity_corruption(tmp_path: Path) -> None:
    project = make_project(tmp_path / "invalid-hash")
    prepare_evidence(project)
    source_two = project / "evidence/sources/source_video_002/canonical_bundle.json"
    tampered = read_json(source_two)
    tampered["sources"][0]["title"] = "tampered without manifest update"
    source_two.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    invalid_hash = run_cli(
        "project-align", str(project), "--source-id", "video_002",
        "--revision-id", "transcript_revision_video_002_r1",
        "--alignment-json", str(project / "alignment_video_002.json"),
        "--media", str(project / "source/video/video_002.mp4"),
    )
    assert invalid_hash.returncode == 1
    assert "source manifest bundle hash mismatch" in invalid_hash.stderr

    project = make_project(tmp_path / "project-mismatch")
    prepare_evidence(project)
    bundle = read_json(project / "evidence/sources/source_video_002/canonical_bundle.json")
    bundle["project"]["id"] = "project_conflicting_identity"
    bundle["sources"][0]["project_id"] = "project_conflicting_identity"
    rewrite_retained_source_bundle(project, "source_video_002", bundle)
    mismatch = run_cli(
        "project-align", str(project), "--source-id", "video_002",
        "--revision-id", "transcript_revision_video_002_r1",
        "--alignment-json", str(project / "alignment_video_002.json"),
        "--media", str(project / "source/video/video_002.mp4"),
    )
    assert mismatch.returncode == 1
    assert "project identity mismatch" in mismatch.stderr

    project = make_project(tmp_path / "duplicate-id")
    prepare_evidence(project)
    first = read_json(project / "evidence/sources/source_video_001/canonical_bundle.json")
    bundle = read_json(project / "evidence/sources/source_video_002/canonical_bundle.json")
    duplicate_id = first["words"][0]["id"]
    old_id = bundle["words"][0]["id"]
    bundle["words"][0]["id"] = duplicate_id
    for segment in bundle["benchmark_segments"]:
        if segment["word_start_id"] == old_id:
            segment["word_start_id"] = duplicate_id
        if segment["word_end_id"] == old_id:
            segment["word_end_id"] = duplicate_id
    rewrite_retained_source_bundle(project, "source_video_002", bundle)
    duplicate = run_cli(
        "project-align", str(project), "--source-id", "video_002",
        "--revision-id", "transcript_revision_video_002_r1",
        "--alignment-json", str(project / "alignment_video_002.json"),
        "--media", str(project / "source/video/video_002.mp4"),
    )
    assert duplicate.returncode == 1
    assert "globally unique" in duplicate.stderr


def test_resolver_states_are_explicit_and_paths_do_not_leak(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    source_one = project / "source/video/video_001.mp4"
    resolver = {
        "schema_version": 1,
        "sources": {
            "source_video_001": {
                "state": "AVAILABLE",
                "path": "source/video/video_001.mp4",
                "content_sha256": hashlib.sha256(source_one.read_bytes()).hexdigest(),
            },
            "source_video_002": {"state": "MISSING"},
        },
    }
    resolver_path = project / "project_sources.json"
    resolver_path.write_text(json.dumps(resolver, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    destination = tmp_path / "vault"
    result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input",
        str(project / "knowledge_input.json"),
        "--source-resolver",
        str(resolver_path),
        "--destination",
        str(destination),
    )
    assert result.returncode == 0, result.stderr
    first = (destination / "Sources/source_video_001.md").read_text(encoding="utf-8")
    second = (destination / "Sources/source_video_002.md").read_text(encoding="utf-8")
    assert '"resolver_state": "AVAILABLE"' in first
    assert '"resolver_state": "MISSING"' in second
    for path in destination.rglob("*"):
        if path.is_file():
            assert str(project) not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("state", ["MOVED", "PROJECT_MOVED", "MISSING", "RESOLVER_UNAVAILABLE"])
def test_non_available_resolver_states_are_reported_without_retargeting(
    tmp_path: Path, state: str
) -> None:
    project = make_project(tmp_path)
    prepare_evidence(project)
    resolver_path = project / "resolver.json"
    resolver_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": {
                    "source_video_001": {"state": state},
                    "source_video_002": {"state": "RESOLVER_UNAVAILABLE"},
                },
            }
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "vault"
    result = run_cli(
        "project-obsidian-export",
        str(project),
        "--knowledge-input", str(project / "knowledge_input.json"),
        "--destination", str(destination),
        "--source-resolver", str(resolver_path),
    )
    assert result.returncode == 0, result.stderr
    note = (destination / "Sources/source_video_001.md").read_text(encoding="utf-8")
    assert f'"resolver_state": "{state}"' in note
    assert f"- Resolver state: `{state}`" in note
    assert str(project) not in note
