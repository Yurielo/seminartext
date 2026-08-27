#!/usr/bin/env python3
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MVP = ROOT / "analysis" / "word_timeline_mvp"
RUNNER = MVP / "build_canonical_evidence.py"
MANIFEST = MVP / "population_manifest.json"
BUNDLE = MVP / "canonical_evidence_bundle.json"
SCHEMA = ROOT / "schemas" / "canonical_evidence_v1.schema.json"
EXPECTED_BUNDLE_SHA256 = "8b1a5b1ffced298cd21a8ede3dbe61d82a00950f2de6da1ba186ffae4cd93d14"


def load_runner():
    spec = importlib.util.spec_from_file_location("word_timeline_mvp", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUNNER_MODULE = load_runner()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_bundle():
    return RUNNER_MODULE.build_bundle(MANIFEST)


def test_population_is_byte_deterministic_and_matches_committed_bundle():
    first = RUNNER_MODULE.canonical_bytes(build_bundle())
    second = RUNNER_MODULE.canonical_bytes(build_bundle())
    assert first == second == BUNDLE.read_bytes()
    assert RUNNER_MODULE.sha256_bytes(first) == EXPECTED_BUNDLE_SHA256


def test_bundle_passes_draft_2020_12_and_cross_record_validation():
    jsonschema = pytest.importorskip("jsonschema")
    bundle = build_bundle()
    schema = load_json(SCHEMA)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(bundle)
    assert RUNNER_MODULE.validate_bundle(bundle) == []


def test_real_population_counts_and_semantic_conservation():
    bundle = build_bundle()
    transcript = bundle["transcript_revisions"][0]
    words = bundle["words"]
    tokens = list(re.finditer(r"\S+", transcript["canonical_text"]))

    assert bundle["artifact_type"] == "seminartext.canonical_evidence"
    assert bundle["schema_version"] == "1.0.0"
    assert len(bundle["sources"]) == 1
    assert len(bundle["transcript_revisions"]) == 1
    assert len(bundle["alignment_runs"]) == 1
    assert len(bundle["cues"]) == 124
    assert len(words) == len(tokens) == 1434
    assert len(bundle["benchmark_segments"]) == 29
    assert len(bundle["topics"]) == 0
    assert len(bundle["evidence_refs"]) == 5
    assert transcript["authority"] == "authoritative"
    assert transcript["revision_kind"] == "verified"

    for sequence, (word, token) in enumerate(zip(words, tokens)):
        assert word["sequence"] == sequence
        assert word["text"] == token.group(0)
        assert word["char_start"] == token.start()
        assert word["char_end"] == token.end()
        assert transcript["canonical_text"][word["char_start"] : word["char_end"]] == word["text"]
        assert word["speaker_id"] is None


def test_timing_integrity_and_explicit_unaligned_words():
    bundle = build_bundle()
    words = bundle["words"]
    aligned = [word for word in words if word["alignment_status"] == "aligned"]
    unaligned = [word for word in words if word["alignment_status"] == "unaligned"]

    assert len(aligned) == 1432
    assert [(word["sequence"], word["text"]) for word in unaligned] == [
        (970, "думаешь,"),
        (971, "что"),
    ]
    for word in unaligned:
        assert word["start_seconds"] is None
        assert word["end_seconds"] is None
        assert word["confidence"] is None
        assert word["timing_provenance"] == {
            "alignment_run_id": None,
            "kind": "unavailable",
            "method": None,
        }
        assert "unaligned_review_required" in word["qa_flags"]

    previous_end = None
    source_duration = bundle["sources"][0]["duration_seconds"]
    for word in aligned:
        assert 0 <= word["start_seconds"] < word["end_seconds"] <= source_duration
        if previous_end is not None:
            assert word["start_seconds"] >= previous_end
        previous_end = word["end_seconds"]
        assert word["timing_provenance"]["kind"] == "forced_alignment"


def test_benchmark_ranges_cover_every_word_once():
    bundle = build_bundle()
    words = bundle["words"]
    by_id = {word["id"]: word for word in words}
    covered = []
    for segment in bundle["benchmark_segments"]:
        first = by_id[segment["word_start_id"]]["sequence"]
        last = by_id[segment["word_end_id"]]["sequence"]
        assert last - first + 1 == segment["word_count"]
        covered.extend(range(first, last + 1))
    assert covered == list(range(1434))


def test_navigation_refs_are_distributed_exact_source_intervals():
    bundle = build_bundle()
    words = {word["id"]: word for word in bundle["words"]}
    observed = []
    for evidence in bundle["evidence_refs"]:
        word = words[evidence["target"]["entity_id"]]
        assert evidence["source_id"] == "source_stress_code_video_001"
        assert evidence["locator"] == {
            "end_seconds": word["end_seconds"],
            "start_seconds": word["start_seconds"],
            "type": "time_interval",
        }
        observed.append((word["sequence"], word["text"], word["start_seconds"]))
    assert observed == [
        (3, "быть", 602.603),
        (299, "вопросом,", 822.531),
        (696, "есть", 1049.64),
        (1070, "И,", 1268.93),
        (1393, "Хорошо,", 1469.557),
    ]


def test_population_rejects_semantic_alignment_substitution():
    canonical = list(re.finditer(r"\S+", "один два три"))
    aligned = [
        {"word": "один"},
        {"word": "замена"},
        {"word": "три"},
    ]
    with pytest.raises(ValueError, match="not an exact subsequence"):
        RUNNER_MODULE.map_alignment(canonical, aligned, [])


def test_population_rejects_changed_verified_transcript_hash():
    spec = dict(load_json(MANIFEST)["transcript"])
    spec["text_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="verified transcript SHA-256 mismatch"):
        RUNNER_MODULE.load_verified_text(spec)


def test_cli_repeat_runs_are_byte_identical(tmp_path):
    pytest.importorskip("jsonschema")
    outputs = [tmp_path / "run_1.json", tmp_path / "run_2.json"]
    for output in outputs:
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--manifest",
                str(MANIFEST),
                "--schema",
                str(SCHEMA),
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert outputs[0].read_bytes() == outputs[1].read_bytes() == BUNDLE.read_bytes()


if __name__ == "__main__":
    test_population_is_byte_deterministic_and_matches_committed_bundle()
    test_real_population_counts_and_semantic_conservation()
    test_timing_integrity_and_explicit_unaligned_words()
    test_benchmark_ranges_cover_every_word_once()
    test_navigation_refs_are_distributed_exact_source_intervals()
    test_population_rejects_semantic_alignment_substitution()
    test_population_rejects_changed_verified_transcript_hash()
    print("Word Timeline MVP tests passed")
