#!/usr/bin/env python3
import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "analysis"
    / "external_topic_baselines"
    / "run_baseline_challenge.py"
)
spec = importlib.util.spec_from_file_location("external_topic_baselines", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_match_boundaries_is_one_to_one_and_matches_runner_policy():
    matches, false_positives, false_negatives = module.match_boundaries(
        [10, 12], [11], tolerance=1
    )
    assert matches == [
        {"gold": 10, "predicted": 11, "distance": 1, "signed_offset": 1}
    ]
    assert false_positives == []
    assert false_negatives == [12]


def test_aggregate_metrics_reports_count_and_correction_proxies():
    cases = [
        module.metrics_for([1, 4, 8], [1, 5, 9], tolerance=1),
        module.metrics_for([20, 25], [20], tolerance=1),
    ]
    aggregate = module.aggregate_metrics(cases)
    assert aggregate["true_positives"] == 4
    assert aggregate["false_positives"] == 0
    assert aggregate["false_negatives"] == 1
    assert aggregate["oversegmentation_proxy_false_positives"] == 0
    assert aggregate["undersegmentation_proxy_false_negatives"] == 1
    assert aggregate["mean_absolute_topic_count_error"] == 0.5


def test_chunk_offsets_map_to_original_segment_ids():
    case = {
        "segments": [
            {"id": 10, "text": "one"},
            {"id": 11, "text": "two"},
            {"id": 12, "text": "three"},
        ]
    }
    text, offsets = module.joined_segment_text(case, "\n")
    assert text == "one\ntwo\nthree"
    assert offsets == [0, 4, 8]
    assert module.chunk_offsets_to_boundaries(case, offsets, [4, 9]) == [10, 11, 12]


def test_density_prior_duration_parser():
    case = {"start": "01:00:00,000", "end": "01:12:00,000"}
    assert module.window_duration_seconds(case) == 720.0


if __name__ == "__main__":
    test_match_boundaries_is_one_to_one_and_matches_runner_policy()
    test_aggregate_metrics_reports_count_and_correction_proxies()
    test_chunk_offsets_map_to_original_segment_ids()
    test_density_prior_duration_parser()
    print("external topic baseline challenge tests passed")
