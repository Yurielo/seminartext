#!/usr/bin/env python3
"""Regression tests for prediction-independent Gold Expansion v2 preparation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis" / "gold_expansion_v2" / "prepare_gold_expansion_v2.py"
SPEC = importlib.util.spec_from_file_location("gold_expansion_v2", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture_inputs():
    cues = [
        {
            "id": index + 1,
            "start": float(index * 10),
            "end": float((index + 1) * 10),
            "text": f"слово{index:04d}",
        }
        for index in range(432)
    ]
    candidate = {
        "candidate_id": "G_TEST",
        "duration_seconds": 4320.0,
        "project_title": "Тестовый Gold candidate",
        "slug": "test_gold",
        "source_sha256": "a" * 64,
        "source_title": "Тестовый source",
    }
    text = "\n".join(cue["text"] for cue in cues) + "\n"
    alignment = {
        "alignment": {
            "aligner": "whisperx",
            "aligner_version": "3.8.6",
            "config_sha256": "b" * 64,
            "model": "test-model",
            "model_revision": "test-revision",
            "model_sha256": "c" * 64,
            "run_result_sha256": ["d" * 64, "d" * 64],
        },
        "transcript": {
            "text_sha256": MODULE.hashlib.sha256(text.encode("utf-8")).hexdigest()
        },
        "words": [
            {
                "end": round(index * 10 + 1.0, 3),
                "score": 0.9,
                "start": round(index * 10 + 0.1, 3),
                "word": cue["text"],
            }
            for index, cue in enumerate(cues)
        ],
    }
    return candidate, cues, alignment


def test_canonical_bundle_is_provisional_valid_and_deterministic():
    candidate, cues, alignment = fixture_inputs()
    first = MODULE.build_bundle(candidate, cues, alignment)
    second = MODULE.build_bundle(candidate, cues, alignment)

    assert MODULE.canonical_bytes(first) == MODULE.canonical_bytes(second)
    assert first["transcript_revisions"][0]["revision_kind"] == "asr"
    assert first["transcript_revisions"][0]["authority"] == "candidate"
    assert first["transcript_revisions"][0]["lifecycle_status"] == "draft"
    assert first["topics"] == []
    assert len(first["words"]) == 432
    assert all(word["speaker_id"] is None for word in first["words"])
    assert all(word["alignment_status"] == "aligned" for word in first["words"])


def test_packets_are_evenly_spaced_and_semantically_blank():
    candidate, cues, alignment = fixture_inputs()
    bundle = MODULE.build_bundle(candidate, cues, alignment)
    packets = MODULE.build_packets(candidate, cues, bundle)

    assert packets["selection_policy"]["selected_window_numbers"] == [1, 2, 3, 4, 5, 6]
    assert packets["contamination_policy"] == "prediction_independent_no_topic_engine_outputs_read"
    assert packets["packet_count"] == 6
    for packet in packets["packets"]:
        assert packet["annotation_status"] == "GOLD_ANNOTATION_REQUIRED"
        assert packet["annotation"] == {
            "boundaries": [],
            "notes": "",
            "summaries": [],
            "titles": [],
        }
        assert packet["word_id_range"][0]
        assert packet["word_id_range"][1]


def test_unmatched_alignment_semantics_are_rejected():
    candidate, cues, alignment = fixture_inputs()
    alignment["words"][10]["word"] = "подменённый-текст"
    with pytest.raises(ValueError, match="unmatched semantic token"):
        MODULE.build_bundle(candidate, cues, alignment)


def test_runner_has_no_topic_engine_dependency():
    text = SCRIPT.read_text(encoding="utf-8").lower()
    forbidden = ["treeseg", "local_peak", "ruptures", "chonkie", "ollama"]
    assert not any(name in text for name in forbidden)
