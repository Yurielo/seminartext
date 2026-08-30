from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"
BASE_FIXTURE = ROOT / "tests" / "fixtures" / "project_knowledge_bridge"
REVIEW_FIXTURE = ROOT / "tests" / "fixtures" / "human_review_workflow" / "topic_drafts.json"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(CLI), *args], cwd=ROOT, text=True, capture_output=True)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "Project knowledge bridge"
    shutil.copytree(BASE_FIXTURE, project)
    for source_id in ("video_001", "video_002"):
        target = project / "transcript" / source_id
        target.mkdir(parents=True)
        shutil.copy2(project / f"transcript_{source_id}.txt", target / "transcript.txt")
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
    return project


def prepare(tmp_path: Path) -> tuple[Path, Path, Path]:
    project = make_project(tmp_path)
    output = tmp_path / "review-package"
    result = run_cli(
        "project-review-prepare",
        str(project),
        "--drafts",
        str(REVIEW_FIXTURE),
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr
    return project, output / "review_package.json", output / "review_decisions.template.json"


def decision(
    package: dict,
    action: str,
    targets: list[str],
    *,
    decision_id: str | None = None,
    new_title: str | None = None,
    new_summary: str | None = None,
    result_topics: list[dict] | None = None,
) -> dict:
    topics = {item["id"]: item for item in package["topics"]}
    return {
        "id": decision_id or f"decision_{action.lower()}_{targets[0]}",
        "action": action,
        "target_ids": targets,
        "result_topics": result_topics or [],
        "reason": f"Explicit fixture {action} decision.",
        "timestamp": "2026-08-30T00:00:00Z",
        "expected_topics": [
            {"topic_id": topic_id, "topic_sha256": topics[topic_id]["topic_sha256"]}
            for topic_id in targets
        ],
        "new_title": new_title,
        "new_summary": new_summary,
    }


def complete_decisions(package_path: Path, template_path: Path) -> dict:
    package = read_json(package_path)
    document = read_json(template_path)
    document["reviewer"] = {"actor_type": "human_domain_reviewer", "actor_id": "reviewer_fixture"}
    document["decisions"] = [
        decision(package, "ACCEPT", ["topic_review_accept"]),
        decision(
            package,
            "RENAME",
            ["topic_review_rename"],
            new_title="Human-corrected stable Topic title",
            new_summary="The explicit rename revises the draft but does not silently accept it.",
        ),
        decision(package, "REJECT", ["topic_review_reject"]),
        decision(package, "DEFER", ["topic_review_defer"]),
    ]
    return document


def result_topic(item_id: str, sequence: int, title: str) -> dict:
    return {
        "id": item_id,
        "source_id": "source_video_001",
        "transcript_revision_id": "transcript_revision_video_001_r1",
        "topic_set_id": "topic_set_human_review_results",
        "sequence": sequence,
        "word_start_id": "transcript_revision_video_001_r1:word:000000",
        "word_end_id": "transcript_revision_video_001_r1:word:000001",
        "proposed_title": title,
        "proposed_summary": "Explicit human-authored lineage result fixture.",
        "evidence_refs": ["evidence_human_review_fixture"],
        "semantic_origin": "verified_manual",
    }


def test_prepare_is_human_readable_review_required_and_deterministic(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        result = run_cli(
            "project-review-prepare", str(project), "--drafts", str(REVIEW_FIXTURE), "--output", str(output)
        )
        assert result.returncode == 0, result.stderr
    assert (first / "review_package.json").read_bytes() == (second / "review_package.json").read_bytes()
    assert (first / "REVIEW.md").read_bytes() == (second / "REVIEW.md").read_bytes()
    package = read_json(first / "review_package.json")
    assert {item["lifecycle_status"] for item in package["topics"]} == {"REVIEW_REQUIRED"}
    assert package["review_policy"]["automatic_acceptance"] is False
    review = (first / "REVIEW.md").read_text(encoding="utf-8")
    assert "TranscriptRevision" in review
    assert "Evidence hash" in review
    assert "REVIEW_REQUIRED" in review


def test_status_and_apply_accept_rename_reject_defer(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    empty = run_cli("project-review-status", str(project), "--package", str(package_path))
    assert empty.returncode == 0, empty.stderr
    assert json.loads(empty.stdout)["UNREVIEWED"] == 4
    decisions_path = tmp_path / "decisions.json"
    write_json(decisions_path, complete_decisions(package_path, template_path))
    status = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(decisions_path)
    )
    assert status.returncode == 0, status.stderr
    counts = json.loads(status.stdout)
    assert counts == {
        "status": "PASS",
        "TOTAL": 4,
        "UNREVIEWED": 0,
        "ACCEPTED": 1,
        "RENAMED": 1,
        "SPLIT": 0,
        "MERGED": 0,
        "REJECTED": 1,
        "DEFERRED": 1,
    }
    first = tmp_path / "reviewed-first.json"
    second = tmp_path / "reviewed-second.json"
    for output in (first, second):
        applied = run_cli(
            "project-review-apply",
            str(project),
            "--package",
            str(package_path),
            "--decisions",
            str(decisions_path),
            "--output",
            str(output),
        )
        assert applied.returncode == 0, applied.stderr
        assert json.loads(applied.stdout)["canonical_knowledge_compatible"] is True
    assert first.read_bytes() == second.read_bytes()
    output = read_json(first)
    topics = {item["id"]: item for item in output["topics"]}
    assert topics["topic_review_accept"]["status"] == "ACCEPTED"
    assert topics["topic_review_rename"]["title"] == "Human-corrected stable Topic title"
    assert topics["topic_review_rename"]["status"] == "PROVISIONAL"
    assert topics["topic_review_reject"]["status"] == "REJECTED"
    assert topics["topic_review_defer"]["status"] == "PROVISIONAL"
    assert {item["action"] for item in output["review_decisions"]} == {"ACCEPT", "RENAME", "REJECT", "DEFER"}


def test_no_automatic_promotion_and_incomplete_apply_fails(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    output = tmp_path / "must-not-exist.json"
    applied = run_cli(
        "project-review-apply",
        str(project),
        "--package",
        str(package_path),
        "--decisions",
        str(template_path),
        "--output",
        str(output),
    )
    assert applied.returncode != 0
    assert "unreviewed Topic Drafts remain" in applied.stderr
    assert not output.exists()


def test_missing_evidence_and_invalid_revision_fail_closed(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    drafts = read_json(REVIEW_FIXTURE)
    drafts["topics"][0]["evidence_refs"] = ["evidence_missing"]
    path = tmp_path / "missing-evidence.json"
    write_json(path, drafts)
    result = run_cli("project-review-prepare", str(project), "--drafts", str(path), "--output", str(tmp_path / "out"))
    assert result.returncode != 0
    assert "missing evidence" in result.stderr

    drafts = read_json(REVIEW_FIXTURE)
    drafts["topics"][0]["transcript_revision_id"] = "transcript_revision_missing"
    path = tmp_path / "bad-revision.json"
    write_json(path, drafts)
    result = run_cli("project-review-prepare", str(project), "--drafts", str(path), "--output", str(tmp_path / "out2"))
    assert result.returncode != 0
    assert "invalid TranscriptRevision" in result.stderr


def test_stale_evidence_invalidates_review(tmp_path: Path) -> None:
    project, package_path, _ = prepare(tmp_path)
    canonical = project / "evidence" / "canonical_bundle.json"
    canonical.write_text(canonical.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = run_cli("project-review-status", str(project), "--package", str(package_path))
    assert result.returncode != 0
    assert "underlying evidence changed" in result.stderr


def test_tampered_review_package_fails_even_with_rebound_file_hash(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    package = read_json(package_path)
    package["topics"][0]["proposed_title"] = "Tampered title"
    write_json(package_path, package)
    decisions = complete_decisions(package_path, template_path)
    decisions["review_package_sha256"] = hashlib.sha256(package_path.read_bytes()).hexdigest()
    decisions_path = tmp_path / "rebound-decisions.json"
    write_json(decisions_path, decisions)
    result = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(decisions_path)
    )
    assert result.returncode != 0
    assert "Topic Draft changed" in result.stderr


def test_duplicate_or_orphan_decisions_fail_closed(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    package = read_json(package_path)
    document = complete_decisions(package_path, template_path)
    document["decisions"].append(copy.deepcopy(document["decisions"][0]))
    duplicate = tmp_path / "duplicate.json"
    write_json(duplicate, document)
    result = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(duplicate)
    )
    assert result.returncode != 0
    assert "duplicate ReviewDecision" in result.stderr

    document = complete_decisions(package_path, template_path)
    document["decisions"][0]["target_ids"] = ["topic_orphan"]
    document["decisions"][0]["expected_topics"] = [
        {"topic_id": "topic_orphan", "topic_sha256": "b" * 64}
    ]
    orphan = tmp_path / "orphan.json"
    write_json(orphan, document)
    result = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(orphan)
    )
    assert result.returncode != 0
    assert "orphan ReviewDecision" in result.stderr


def test_stale_topic_snapshot_and_unsupported_decision_fail_closed(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    document = complete_decisions(package_path, template_path)
    document["decisions"][0]["expected_topics"][0]["topic_sha256"] = "b" * 64
    stale = tmp_path / "stale.json"
    write_json(stale, document)
    result = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(stale)
    )
    assert result.returncode != 0
    assert "stale Topic Draft" in result.stderr

    document = complete_decisions(package_path, template_path)
    document["decisions"][0]["action"] = "AUTO_ACCEPT"
    unsupported = tmp_path / "unsupported.json"
    write_json(unsupported, document)
    result = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(unsupported)
    )
    assert result.returncode != 0
    assert "schema validation failed" in result.stderr


def test_explicit_split_and_merge_lineage_is_canonical_compatible(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    package = read_json(package_path)
    document = read_json(template_path)
    document["reviewer"] = {"actor_type": "human_domain_reviewer", "actor_id": "reviewer_lineage_fixture"}
    document["decisions"] = [
        decision(
            package,
            "MERGE",
            ["topic_review_accept", "topic_review_rename"],
            decision_id="decision_merge_review_topics",
            result_topics=[result_topic("topic_review_merged_result", 0, "Merged reviewed result")],
        ),
        decision(
            package,
            "SPLIT",
            ["topic_review_reject"],
            decision_id="decision_split_review_topic",
            result_topics=[
                result_topic("topic_review_split_result_a", 1, "First split result"),
                result_topic("topic_review_split_result_b", 2, "Second split result"),
            ],
        ),
        decision(package, "DEFER", ["topic_review_defer"]),
    ]
    decisions_path = tmp_path / "lineage-decisions.json"
    write_json(decisions_path, document)
    status = run_cli(
        "project-review-status", str(project), "--package", str(package_path), "--decisions", str(decisions_path)
    )
    assert status.returncode == 0, status.stderr
    counts = json.loads(status.stdout)
    assert counts["MERGED"] == 2
    assert counts["SPLIT"] == 1
    output = tmp_path / "lineage-reviewed.json"
    applied = run_cli(
        "project-review-apply",
        str(project),
        "--package",
        str(package_path),
        "--decisions",
        str(decisions_path),
        "--output",
        str(output),
    )
    assert applied.returncode == 0, applied.stderr
    topics = {item["id"]: item for item in read_json(output)["topics"]}
    assert topics["topic_review_accept"]["status"] == "SUPERSEDED"
    assert topics["topic_review_rename"]["status"] == "SUPERSEDED"
    assert topics["topic_review_reject"]["status"] == "SUPERSEDED"
    assert topics["topic_review_merged_result"]["status"] == "PROVISIONAL"
    assert topics["topic_review_split_result_a"]["status"] == "PROVISIONAL"


def test_package_hash_is_bound_and_machine_paths_are_not_canonical_identity(tmp_path: Path) -> None:
    project, package_path, template_path = prepare(tmp_path)
    template = read_json(template_path)
    assert template["review_package_sha256"] == hashlib.sha256(package_path.read_bytes()).hexdigest()
    package = read_json(package_path)
    assert str(tmp_path) not in json.dumps(package, ensure_ascii=False)
