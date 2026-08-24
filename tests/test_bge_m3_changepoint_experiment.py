#!/usr/bin/env python3
import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "analysis"
    / "experiments"
    / "bge_m3_changepoint_topic_engine.py"
)

spec = importlib.util.spec_from_file_location("bge_m3_experiment", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def segment(sid, start, end, text=None):
    return {
        "id": sid,
        "start": f"00:00:{start:02d},000",
        "end": f"00:00:{end:02d},000",
        "text": text or f"segment {sid}",
    }


def test_make_semantic_blocks():
    segments = [
        segment(1, 0, 5),
        segment(2, 5, 10),
        segment(3, 16, 20),
        segment(4, 21, 25),
    ]
    blocks = module.make_semantic_blocks(segments, block_seconds=15)
    assert len(blocks) == 2
    assert blocks[0]["start_id"] == 1
    assert blocks[0]["end_id"] == 2
    assert blocks[1]["start_id"] == 3
    assert blocks[1]["end_id"] == 4


def test_change_signal_detects_vector_shift():
    embeddings = [
        [1.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [0.0, 1.0],
    ]
    signal = module.change_signal(embeddings, context_blocks=1)
    best = max(signal, key=lambda item: item["score"])
    assert best["boundary_index"] == 2
    assert best["score"] == 1.0


def test_select_change_points_respects_gap_and_threshold():
    signal = [
        {"boundary_index": 1, "score": 0.10},
        {"boundary_index": 2, "score": 0.90},
        {"boundary_index": 3, "score": 0.80},
        {"boundary_index": 5, "score": 0.20},
        {"boundary_index": 6, "score": 0.70},
        {"boundary_index": 7, "score": 0.20},
    ]
    selected = module.select_change_points(
        signal,
        min_gap_blocks=3,
        median_multiplier=1.0,
        max_boundaries=4,
    )
    assert [item["boundary_index"] for item in selected] == [2, 6]


def test_boundaries_from_change_points_and_min_gap():
    segments = [segment(i, i * 2, i * 2 + 1) for i in range(1, 8)]
    blocks = [
        {"start_id": 1},
        {"start_id": 2},
        {"start_id": 3},
        {"start_id": 6},
    ]
    change_points = [
        {"boundary_index": 1, "score": 0.9},
        {"boundary_index": 2, "score": 0.8},
        {"boundary_index": 3, "score": 0.7},
    ]
    boundaries = module.boundaries_from_change_points(
        segments,
        blocks,
        change_points,
        min_gap_ids=3,
    )
    assert boundaries == [1, 6]


def test_metrics_for_tolerance():
    metrics = module.metrics_for([1, 5, 10], [1, 4, 12], tolerance=1)
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == [12]
    assert metrics["false_negatives"] == [10]


if __name__ == "__main__":
    test_make_semantic_blocks()
    test_change_signal_detects_vector_shift()
    test_select_change_points_respects_gap_and_threshold()
    test_boundaries_from_change_points_and_min_gap()
    test_metrics_for_tolerance()
    print("bge-m3 changepoint experiment tests passed")
