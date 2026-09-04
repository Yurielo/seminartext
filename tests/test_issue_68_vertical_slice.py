from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "analysis/issue_68_vertical_slice/build_readiness_manifest.py"
SPEC = importlib.util.spec_from_file_location("issue_68_readiness", BUILDER_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def word(source_number: int, sequence: int) -> dict:
    revision = f"transcript_revision_video_{source_number:03d}_r1"
    return {
        "id": f"{revision}:word:{sequence:06d}",
        "source_id": f"source_video_{source_number:03d}",
        "transcript_revision_id": revision,
        "sequence": sequence,
        "alignment_status": "aligned",
        "start_seconds": float(sequence),
        "end_seconds": float(sequence) + 0.5,
    }


def make_fixture(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "Stress code"
    sources = {
        "schema_version": 1,
        "videos": [
            {"source_id": f"video_{number:03d}", "title": f"Day {number}"}
            for number in range(1, 5)
        ],
        "documents": [
            {"source_id": "doc_001", "type": "presentation", "title": "Slides"}
        ],
    }
    write_json(project / "sources.json", sources)

    bundle = {
        "artifact_id": "artifact_stress_code",
        "project": {"id": "project_stress_code", "title": "Стресс код"},
        "sources": [
            {"id": f"source_video_{number:03d}"} for number in range(1, 5)
        ],
        "transcript_revisions": [
            {
                "id": f"transcript_revision_video_{number:03d}_r1",
                "source_id": f"source_video_{number:03d}",
                "transcript_provenance": {"verification_state": "machine_unverified"},
            }
            for number in range(1, 5)
        ],
        "alignment_runs": [
            {
                "id": f"alignment_{number}",
                "source_id": f"source_video_{number:03d}",
            }
            for number in range(1, 5)
        ],
        "words": [word(number, sequence) for number in range(1, 5) for sequence in range(3)],
    }
    bundle_path = project / "evidence/canonical_bundle.json"
    write_json(bundle_path, bundle)
    bundle_hash = MODULE.sha256(bundle_path)
    evidence_manifest = {
        "bundle_sha256": bundle_hash,
        "all_registered_sources_composed": False,
        "registry_coverage": [
            {
                "canonical_source_id": f"source_video_{number:03d}",
                "evidence_status": "COMPOSED",
            }
            for number in range(1, 5)
        ]
        + [{"canonical_source_id": "source_doc_001", "evidence_status": "EVIDENCE_UNAVAILABLE"}],
    }
    write_json(project / "evidence/manifest.json", evidence_manifest)

    first = word(1, 0)
    last = word(1, 2)
    review = {
        "artifact_id": "review_result_issue_113",
        "application_status": "APPLIED",
        "canonical_evidence": {"artifact_id": bundle["artifact_id"], "sha256": bundle_hash},
        "decision_artifact": {"artifact_id": "decisions", "sha256": "0" * 64},
        "source_topic_snapshots": [{"id": "snapshot_1"}],
        "semantic_knowledge": [
            {
                "id": "reviewed_topic_1",
                "source_id": "source_video_001",
                "word_start_id": first["id"],
                "word_end_id": last["id"],
                "word_start_sequence": 0,
                "word_end_sequence": 2,
            }
        ],
        "seminar_structure": [],
    }
    review_path = project / "review_result.json"
    write_json(review_path, review)
    return project, review_path


def test_real_slice_readiness_fails_closed_at_domain_authoring(tmp_path: Path) -> None:
    project, review = make_fixture(tmp_path)
    manifest = MODULE.build_manifest(project, review)

    assert manifest["status"] == "BLOCKED_AT_DOMAIN_AUTHORING"
    assert manifest["gates"]["canonical_evidence"] == "PASS"
    assert manifest["gates"]["all_video_sources_traced"] == "PASS"
    assert manifest["inventory"]["registered_video_count"] == 4
    assert manifest["inventory"]["word_count"] == 12
    assert manifest["inventory"]["reviewed_semantic_topic_unit_count"] == 1
    assert manifest["claims"]["full_video_evidence_coverage"] is True
    assert manifest["claims"]["full_video_semantic_coverage"] is False
    assert manifest["claims"]["multi_source_vertical_slice"] == "PARTIAL"
    assert manifest["human_gate"]["classification"] == "DOMAIN_AUTHORING"
    assert manifest["safety"]["topics_or_concepts_authored"] is False
    assert [item["canonical_source_id"] for item in manifest["coverage"][:4]] == [
        "source_video_001",
        "source_video_002",
        "source_video_003",
        "source_video_004",
    ]


def test_hash_or_word_binding_mismatch_is_invalid(tmp_path: Path) -> None:
    project, review_path = make_fixture(tmp_path)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["canonical_evidence"]["sha256"] = "f" * 64
    review["semantic_knowledge"][0]["word_end_id"] = "missing:word:000001"
    write_json(review_path, review)

    manifest = MODULE.build_manifest(project, review_path)

    assert manifest["status"] == "INVALID"
    assert manifest["gates"]["canonical_evidence"] == "FAIL"
    assert any("hash does not match" in error for error in manifest["errors"])
    assert any("unresolved Word range" in error for error in manifest["errors"])
