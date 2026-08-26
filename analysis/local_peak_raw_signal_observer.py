#!/usr/bin/env python3
"""Read-only stage observer for the frozen BGE-M3 Local Peak experiment.

The observer imports the frozen experiment helpers without modifying them,
recomputes Dataset A/B signals with the recorded parameters, and records the
state of every block boundary. Dataset C is intentionally unsupported.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
FROZEN_SCRIPT = ROOT / "analysis/experiments/bge_m3_changepoint_topic_engine.py"
DEFAULT_A_BENCHMARK = (
    Path.home()
    / "Documents/seminartext_projects/Стресс код/analysis/benchmark/topic_benchmark.json"
)
DEFAULT_A_RESULT = (
    Path.home()
    / "Documents/seminartext_projects/Стресс код/analysis/benchmark/results"
    / "bge_m3_changepoint_experiment_20260824T183855Z.json"
)
DEFAULT_B_BENCHMARK = ROOT / "analysis/dataset_b/topic_benchmark_dataset_b.json"
DEFAULT_B_RESULT = (
    ROOT / "analysis/dataset_b/results/dataset_b_bge_m3_changepoint_frozen.json"
)
DEFAULT_OUTPUT = ROOT / "analysis/local_peak_raw_signal_failure_analysis.json"

ANALYSIS_NEIGHBORHOOD_BLOCKS = 2


def load_frozen_module():
    spec = importlib.util.spec_from_file_location("frozen_local_peak", FROZEN_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import frozen script: {FROZEN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def descriptive(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": mean(values) if values else None,
        "median": median(values) if values else None,
        "q1": percentile(values, 0.25),
        "q3": percentile(values, 0.75),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def result_parameters(result: dict) -> dict:
    parameters = result["parameters"]
    return {
        "embedding_model": parameters["embedding_model"],
        "endpoint": parameters["embedding_endpoint"],
        "block_seconds": int(parameters["block_seconds"]),
        "context_blocks": int(parameters["context_blocks"]),
        "min_gap_blocks": int(parameters["min_gap_blocks"]),
        "median_multiplier": float(parameters["median_multiplier_threshold"]),
        "max_boundaries": int(parameters["max_boundaries_per_window"]),
        "min_gap_ids": int(parameters["min_gap_segment_ids"]),
    }


def local_maximum(signal: list[dict], index: int) -> bool:
    item = signal[index]
    left = signal[index - 1]["score"] if index > 0 else -1.0
    right = signal[index + 1]["score"] if index + 1 < len(signal) else -1.0
    return item["score"] >= left and item["score"] >= right


def annotate_stages(
    frozen,
    segments: list[dict],
    blocks: list[dict],
    smoothed: list[dict],
    parameters: dict,
) -> tuple[list[dict], list[int], dict]:
    threshold = frozen.robust_threshold(
        [item["score"] for item in smoothed],
        parameters["median_multiplier"],
    )
    signal_median = threshold / parameters["median_multiplier"]

    positions = []
    for index, item in enumerate(smoothed):
        boundary_index = int(item["boundary_index"])
        positions.append(
            {
                "boundary_index": boundary_index,
                "mapped_segment_id": int(blocks[boundary_index]["start_id"]),
                "mapped_start": str(blocks[boundary_index]["start"]),
                "raw_score": float(item["raw_score"]),
                "smoothed_score": float(item["score"]),
                "threshold": threshold,
                "threshold_ratio": float(item["score"] / threshold) if threshold else None,
                "is_local_maximum": local_maximum(smoothed, index),
                "passes_threshold": bool(item["score"] >= threshold),
                "threshold_candidate": False,
                "passes_block_min_gap": False,
                "passes_max_boundaries": False,
                "selected_change_point": False,
                "passes_segment_id_min_gap": False,
                "final_prediction": False,
            }
        )

    threshold_candidates = [
        item
        for item in positions
        if item["is_local_maximum"] and item["passes_threshold"]
    ]
    for item in threshold_candidates:
        item["threshold_candidate"] = True

    ranked = sorted(
        threshold_candidates,
        key=lambda item: (-item["smoothed_score"], item["boundary_index"]),
    )
    selected_unbounded = []
    for candidate in ranked:
        if all(
            abs(candidate["boundary_index"] - item["boundary_index"])
            >= parameters["min_gap_blocks"]
            for item in selected_unbounded
        ):
            candidate["passes_block_min_gap"] = True
            selected_unbounded.append(candidate)

    selected_change_points = selected_unbounded[: parameters["max_boundaries"]]
    for item in selected_change_points:
        item["passes_max_boundaries"] = True
        item["selected_change_point"] = True

    boundary_sources: dict[int, list[dict]] = {}
    for item in selected_change_points:
        boundary_sources.setdefault(item["mapped_segment_id"], []).append(item)

    candidate_boundaries = sorted(
        set([int(segments[0]["id"]), *boundary_sources.keys()])
    )
    final_boundaries = frozen.enforce_min_gap_segment_ids(
        candidate_boundaries,
        parameters["min_gap_ids"],
    )
    final_set = set(final_boundaries)
    for mapped_id, sources in boundary_sources.items():
        for item in sources:
            item["passes_segment_id_min_gap"] = mapped_id in final_set
            item["final_prediction"] = mapped_id in final_set

    for item in positions:
        item["would_pass_block_gap_against_frozen_selected"] = all(
            item is selected
            or abs(item["boundary_index"] - selected["boundary_index"])
            >= parameters["min_gap_blocks"]
            for selected in selected_change_points
        )
        counterfactual_boundaries = sorted(
            set([*final_boundaries, item["mapped_segment_id"]])
        )
        item["would_pass_segment_gap_against_frozen_final"] = (
            item["mapped_segment_id"]
            in frozen.enforce_min_gap_segment_ids(
                counterfactual_boundaries,
                parameters["min_gap_ids"],
            )
        )
        item["max_slot_available"] = (
            len(selected_change_points) < parameters["max_boundaries"]
            or item["selected_change_point"]
        )
        item["threshold_only_counterfactual"] = bool(
            item["is_local_maximum"]
            and not item["passes_threshold"]
            and item["would_pass_block_gap_against_frozen_selected"]
            and item["would_pass_segment_gap_against_frozen_final"]
            and item["max_slot_available"]
        )

    stats = {
        "signal_median": signal_median,
        "threshold": threshold,
        "position_count": len(positions),
        "local_maximum_count": sum(item["is_local_maximum"] for item in positions),
        "threshold_candidate_count": len(threshold_candidates),
        "block_nms_survivor_count": len(selected_unbounded),
        "max_boundary_survivor_count": len(selected_change_points),
        "segment_gap_survivor_count": len(final_boundaries) - 1,
        "max_boundary_removed_count": max(
            0, len(selected_unbounded) - parameters["max_boundaries"]
        ),
        "mandatory_window_start": int(segments[0]["id"]),
    }
    return positions, final_boundaries, stats


def segment_context(case: dict, segment_id: int, radius: int = 1) -> str:
    segments = case.get("segments", [])
    index = min(
        range(len(segments)),
        key=lambda i: abs(int(segments[i]["id"]) - segment_id),
    )
    start = max(0, index - radius)
    end = min(len(segments), index + radius + 1)
    return " ".join(str(item["text"]).strip() for item in segments[start:end])


def neighborhood(positions: list[dict], target_index: int) -> list[dict]:
    return [
        item
        for item in positions
        if abs(item["boundary_index"] - target_index) <= ANALYSIS_NEIGHBORHOOD_BLOCKS
    ]


def stage_rank(item: dict) -> int:
    if item["final_prediction"]:
        return 6
    if item["selected_change_point"]:
        return 5
    if item["passes_block_min_gap"]:
        return 4
    if item["threshold_candidate"]:
        return 3
    if item["is_local_maximum"]:
        return 2
    if item["passes_threshold"]:
        return 1
    return 0


def classify_fn(
    gold_id: int,
    positions: list[dict],
    signal_median: float,
) -> dict:
    nearest = min(
        positions,
        key=lambda item: (
            abs(item["mapped_segment_id"] - gold_id),
            -item["smoothed_score"],
        ),
    )
    nearby = neighborhood(positions, nearest["boundary_index"])
    representative = max(
        nearby,
        key=lambda item: (stage_rank(item), item["smoothed_score"]),
    )
    strongest = max(nearby, key=lambda item: item["smoothed_score"])

    if representative["final_prediction"]:
        category = "BLOCK_MAPPING / LOCALIZATION"
        reason = "A final selected peak exists in the diagnostic neighborhood but maps outside tolerance."
    elif representative["selected_change_point"]:
        category = "SUPPRESSED_BY_MIN_GAP"
        reason = "The block-level point was selected but removed by segment-ID minimum gap."
    elif representative["passes_block_min_gap"]:
        category = "REMOVED_BY_MAX_BOUNDARIES"
        reason = "The candidate survived block NMS but fell outside the maximum-boundary limit."
    elif representative["threshold_candidate"]:
        category = "SUPPRESSED_BY_MIN_GAP"
        reason = "The above-threshold local maximum was suppressed by block-level NMS."
    elif representative["is_local_maximum"]:
        category = "WEAK_SIGNAL_BELOW_THRESHOLD"
        reason = "A local maximum exists in the neighborhood but does not reach the frozen threshold."
    elif strongest["passes_threshold"]:
        representative = strongest
        category = "NOT_LOCAL_MAXIMUM"
        reason = "The response reaches threshold but is not a local maximum."
    elif strongest["smoothed_score"] >= signal_median:
        representative = strongest
        category = "NOT_LOCAL_MAXIMUM"
        reason = "An above-median response exists but never becomes a local maximum."
    else:
        representative = strongest
        category = "NO_SIGNAL"
        reason = "No local maximum or above-median response exists in the diagnostic neighborhood."

    return {
        "gold_id": gold_id,
        "category": category,
        "reason": reason,
        "nearest_mappable_position": nearest,
        "representative_position": representative,
        "strongest_position": strongest,
        "neighborhood_boundary_indices": [item["boundary_index"] for item in nearby],
    }


def topic_title(case: dict, gold_id: int) -> str:
    for topic in case.get("gold", {}).get("topics", []):
        if int(topic.get("start_id")) == gold_id:
            return str(topic.get("title", ""))
    return ""


def analyze_dataset(
    frozen,
    dataset_id: str,
    benchmark_path: Path,
    result_path: Path,
    parameters: dict,
) -> dict:
    benchmark = load_json(benchmark_path)
    saved_result = load_json(result_path)
    saved_engine = saved_result["bge_m3_changepoint"]
    cases = frozen.selected_cases(benchmark)
    saved_metrics = {
        item["case_id"]: item
        for item in saved_engine["metrics"]["2"]["cases"]
    }
    case_results = {}
    all_tp_scores = []
    all_fn_scores = []
    all_fp_scores = []
    all_non_boundary_scores = []
    all_tp_ratios = []
    all_fn_ratios = []
    all_fp_ratios = []
    all_non_boundary_ratios = []

    for case in cases:
        case_id = case["case_id"]
        segments = frozen.normalize_segments(case)
        blocks = frozen.make_semantic_blocks(segments, parameters["block_seconds"])
        embeddings, embedding_stats = frozen.embed_texts_ollama(
            [block["text"] for block in blocks],
            model=parameters["embedding_model"],
            endpoint=parameters["endpoint"],
            batch_size=32,
            timeout=300,
        )
        raw_signal = frozen.change_signal(embeddings, parameters["context_blocks"])
        smoothed = frozen.smooth_signal(raw_signal)
        positions, final_predictions, stage_stats = annotate_stages(
            frozen,
            segments,
            blocks,
            smoothed,
            parameters,
        )
        saved_predictions = [int(item) for item in saved_engine["predictions"][case_id]]
        if final_predictions != saved_predictions:
            raise RuntimeError(
                f"Frozen prediction mismatch for {case_id}: "
                f"computed={final_predictions}, saved={saved_predictions}"
            )

        metrics = saved_metrics[case_id]
        matches = metrics["matched_boundaries"]
        tp_inventory = []
        for match in matches:
            gold_id = int(match["gold"])
            predicted_id = int(match["predicted"])
            if predicted_id == int(segments[0]["id"]):
                tp_inventory.append(
                    {
                        "gold_id": gold_id,
                        "predicted_id": predicted_id,
                        "offset": int(match["signed_offset"]),
                        "technical_window_start": True,
                        "signal_position": None,
                    }
                )
                continue
            signal_position = next(
                item
                for item in positions
                if item["final_prediction"]
                and item["mapped_segment_id"] == predicted_id
            )
            tp_inventory.append(
                {
                    "gold_id": gold_id,
                    "predicted_id": predicted_id,
                    "offset": int(match["signed_offset"]),
                    "technical_window_start": False,
                    "signal_position": signal_position,
                }
            )
            all_tp_scores.append(signal_position["smoothed_score"])
            all_tp_ratios.append(signal_position["threshold_ratio"])

        fn_inventory = []
        for gold_id in metrics["false_negatives"]:
            diagnosis = classify_fn(
                int(gold_id),
                positions,
                stage_stats["signal_median"],
            )
            diagnosis["title"] = topic_title(case, int(gold_id))
            diagnosis["context"] = segment_context(case, int(gold_id))
            fn_inventory.append(diagnosis)
            representative = diagnosis["representative_position"]
            all_fn_scores.append(representative["smoothed_score"])
            all_fn_ratios.append(representative["threshold_ratio"])

        fp_inventory = []
        gold_boundaries = [int(item) for item in case["gold"]["boundaries"]]
        for predicted_id in metrics["false_positives"]:
            signal_position = next(
                item
                for item in positions
                if item["final_prediction"]
                and item["mapped_segment_id"] == int(predicted_id)
            )
            nearest_gold = min(
                gold_boundaries,
                key=lambda item: (abs(item - int(predicted_id)), item),
            )
            fp_inventory.append(
                {
                    "predicted_id": int(predicted_id),
                    "nearest_gold": nearest_gold,
                    "signed_distance": int(predicted_id) - nearest_gold,
                    "signal_position": signal_position,
                    "context": segment_context(case, int(predicted_id)),
                }
            )
            all_fp_scores.append(signal_position["smoothed_score"])
            all_fp_ratios.append(signal_position["threshold_ratio"])

        fn_representative_indices = {
            item["representative_position"]["boundary_index"]
            for item in fn_inventory
        }
        for item in positions:
            if all(
                abs(item["mapped_segment_id"] - gold_id) > 2
                for gold_id in gold_boundaries
            ) and not item["final_prediction"] and (
                item["boundary_index"] not in fn_representative_indices
            ):
                all_non_boundary_scores.append(item["smoothed_score"])
                all_non_boundary_ratios.append(item["threshold_ratio"])

        case_results[case_id] = {
            "block_count": len(blocks),
            "embedding_stats": embedding_stats,
            "stage_stats": stage_stats,
            "frozen_predictions_reproduced": True,
            "positions": positions,
            "true_positives": tp_inventory,
            "false_negatives": fn_inventory,
            "false_positives": fp_inventory,
        }

    return {
        "dataset_id": dataset_id,
        "benchmark_path": str(benchmark_path),
        "benchmark_sha256": sha256(benchmark_path),
        "frozen_result_path": str(result_path),
        "frozen_result_sha256": sha256(result_path),
        "case_count": len(cases),
        "cases": case_results,
        "signal_distributions": {
            "tp_internal": {
                "smoothed_score": descriptive(all_tp_scores),
                "threshold_ratio": descriptive(all_tp_ratios),
            },
            "fn_representative": {
                "smoothed_score": descriptive(all_fn_scores),
                "threshold_ratio": descriptive(all_fn_ratios),
            },
            "fp": {
                "smoothed_score": descriptive(all_fp_scores),
                "threshold_ratio": descriptive(all_fp_ratios),
            },
            "non_boundary_positions": {
                "smoothed_score": descriptive(all_non_boundary_scores),
                "threshold_ratio": descriptive(all_non_boundary_ratios),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-a-benchmark", type=Path, default=DEFAULT_A_BENCHMARK)
    parser.add_argument("--dataset-a-result", type=Path, default=DEFAULT_A_RESULT)
    parser.add_argument("--dataset-b-benchmark", type=Path, default=DEFAULT_B_BENCHMARK)
    parser.add_argument("--dataset-b-result", type=Path, default=DEFAULT_B_RESULT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    paths = [
        args.dataset_a_benchmark,
        args.dataset_a_result,
        args.dataset_b_benchmark,
        args.dataset_b_result,
    ]
    if any("dataset_c" in str(path).lower() for path in paths):
        raise SystemExit("Dataset C is forbidden in this diagnostic observer")

    frozen = load_frozen_module()
    result_a = load_json(args.dataset_a_result)
    result_b = load_json(args.dataset_b_result)
    parameters_a = result_parameters(result_a)
    parameters_b = result_parameters(result_b)
    if parameters_a != parameters_b:
        raise SystemExit(
            f"Frozen parameter mismatch between Dataset A and B: "
            f"A={parameters_a}, B={parameters_b}"
        )

    datasets = [
        analyze_dataset(
            frozen,
            "dataset_a",
            args.dataset_a_benchmark,
            args.dataset_a_result,
            parameters_a,
        ),
        analyze_dataset(
            frozen,
            "dataset_b",
            args.dataset_b_benchmark,
            args.dataset_b_result,
            parameters_a,
        ),
    ]

    stage_accounting = {}
    for dataset in datasets:
        counts = {}
        for case in dataset["cases"].values():
            for item in case["false_negatives"]:
                counts[item["category"]] = counts.get(item["category"], 0) + 1
        stage_accounting[dataset["dataset_id"]] = counts

    output = {
        "schema_version": 1,
        "type": "seminartext_local_peak_raw_signal_failure_analysis",
        "scope": "Dataset A/B only; Dataset C excluded",
        "analysis_neighborhood_blocks": ANALYSIS_NEIGHBORHOOD_BLOCKS,
        "frozen_script": str(FROZEN_SCRIPT),
        "frozen_script_sha256": sha256(FROZEN_SCRIPT),
        "parameters": parameters_a,
        "pipeline": [
            "normalize segments",
            "build fixed-time semantic blocks and concatenate segment text",
            "embed each block with Ollama BGE-M3",
            "compute left/right contextual mean cosine distance",
            "apply fixed three-point smoothing",
            "compute median * 1.15 threshold",
            "retain above-threshold local maxima",
            "rank by score and apply greedy block-level min-gap/NMS",
            "keep at most 11 selected change points",
            "map block boundaries to block start segment IDs",
            "prepend mandatory window start and apply segment-ID min-gap",
            "emit final predictions",
        ],
        "datasets": datasets,
        "stage_loss_accounting": stage_accounting,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"JSON: {args.output}")
    for dataset in datasets:
        counts = stage_accounting[dataset["dataset_id"]]
        total = sum(counts.values())
        print(f"{dataset['dataset_id']}: FN={total}, stages={counts}")
        print(f"{dataset['dataset_id']}: frozen predictions reproduced for all cases")
    print("RAW SIGNAL OBSERVATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
