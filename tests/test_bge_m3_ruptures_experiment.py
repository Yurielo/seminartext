#!/usr/bin/env python3
import importlib.util
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "analysis"
    / "experiments"
    / "bge_m3_ruptures_topic_engine.py"
)

spec = importlib.util.spec_from_file_location("bge_m3_ruptures", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def segment(sid, start, end, text=None):
    return {
        "id": sid,
        "start": f"00:00:{start:02d},000",
        "end": f"00:00:{end:02d},000",
        "text": text or f"segment {sid}",
    }


def test_semantic_change_features_shape():
    embeddings = np.asarray(
        [
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ],
        dtype=float,
    )
    features = module.semantic_change_features(embeddings, context_blocks=1)
    assert features.shape == (3, 1)
    assert features[1, 0] > features[0, 0]
    assert features[1, 0] > features[2, 0]


def test_run_pelt_returns_nonterminal_breakpoint():
    features = np.asarray(
        [[0.05], [0.05], [0.05], [1.00], [1.00], [1.00]],
        dtype=float,
    )
    breakpoints = module.run_pelt(
        features,
        model="l2",
        penalty=0.01,
        min_size=2,
        jump=1,
    )
    assert breakpoints == [3]


def test_breakpoints_map_to_segment_boundaries():
    segments = [segment(i, i * 2, i * 2 + 1) for i in range(1, 9)]
    blocks = [
        {"start_id": 1},
        {"start_id": 3},
        {"start_id": 5},
        {"start_id": 7},
    ]
    boundaries = module.boundaries_from_ruptures_breakpoints(
        segments,
        blocks,
        breakpoints=[1, 2, 4],
        min_gap_ids=3,
    )
    assert boundaries == [1, 5]


def test_metrics_for_tolerance():
    metrics = module.metrics_for([1, 5, 10], [1, 4, 12], tolerance=1)
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == [12]
    assert metrics["false_negatives"] == [10]


if __name__ == "__main__":
    test_semantic_change_features_shape()
    test_run_pelt_returns_nonterminal_breakpoint()
    test_breakpoints_map_to_segment_boundaries()
    test_metrics_for_tolerance()
    print("bge-m3 ruptures experiment tests passed")
