#!/usr/bin/env python3
"""Read-only sliding sub-window Topic Engine experiment for Dataset A.

This helper intentionally does not modify production Topic Engine behavior. It
imports the current Topic Engine module, runs the existing
analyze_window_boundaries() function on full windows and on smaller overlapping
sub-windows, and evaluates both paths against the same frozen benchmark data.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_BENCHMARK = (
    Path.home()
    / "Documents"
    / "seminartext_projects"
    / "Стресс код"
    / "analysis"
    / "benchmark"
    / "topic_benchmark.json"
)
DEFAULT_TOPICS_MODULE = Path("/Users/yurielokhin/bin/seminartext_topics.py")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def import_topic_engine(path: Path):
    spec = importlib.util.spec_from_file_location("seminartext_topics", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not import Topic Engine: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "analyze_window_boundaries"):
        raise SystemExit("Topic Engine lacks analyze_window_boundaries()")
    return module


def srt_seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(millis) / 1000
    )


def normalize_segments(case: dict) -> list[dict]:
    out = []
    for item in case.get("segments", []):
        out.append(
            {
                "id": int(item["id"]),
                "start": str(item["start"]),
                "end": str(item["end"]),
                "text": str(item["text"]),
            }
        )
    return out


def selected_cases(benchmark: dict) -> list[dict]:
    return [
        case
        for case in benchmark.get("cases", [])
        if case.get("review", {}).get("status") == "gold_complete"
    ]


def match_boundaries(gold: list[int], predicted: list[int], tolerance: int):
    remaining = set(range(len(predicted)))
    matches = []
    for gold_id in gold:
        candidates = [
            (abs(predicted[i] - gold_id), predicted[i], i)
            for i in remaining
            if abs(predicted[i] - gold_id) <= tolerance
        ]
        if not candidates:
            continue
        distance, predicted_id, idx = min(candidates)
        remaining.remove(idx)
        matches.append(
            {
                "gold": gold_id,
                "predicted": predicted_id,
                "distance": distance,
                "signed_offset": predicted_id - gold_id,
            }
        )
    matched_gold = {item["gold"] for item in matches}
    matched_predicted = {item["predicted"] for item in matches}
    return (
        matches,
        [item for item in predicted if item not in matched_predicted],
        [item for item in gold if item not in matched_gold],
    )


def metrics_for(gold: list[int], predicted: list[int], tolerance: int) -> dict:
    matches, fp, fn = match_boundaries(gold, predicted, tolerance)
    tp = len(matches)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "gold_boundaries": gold,
        "predicted_boundaries": predicted,
        "matched_boundaries": matches,
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "gold_topic_count": len(gold),
        "predicted_topic_count": len(predicted),
        "topic_count_error": len(predicted) - len(gold),
    }


def aggregate_metrics(case_metrics: list[dict]) -> dict:
    total_gold = sum(item["gold_topic_count"] for item in case_metrics)
    total_predicted = sum(item["predicted_topic_count"] for item in case_metrics)
    total_tp = sum(item["true_positives"] for item in case_metrics)
    total_fp = sum(len(item["false_positives"]) for item in case_metrics)
    total_fn = sum(len(item["false_negatives"]) for item in case_metrics)
    precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "case_count": len(case_metrics),
        "gold_topic_count": total_gold,
        "predicted_topic_count": total_predicted,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "boundary_precision": precision,
        "boundary_recall": recall,
        "boundary_f1": f1,
    }


def gold_third(gold_id: int, segments: list[dict]) -> str:
    first = segments[0]["id"]
    last = segments[-1]["id"]
    rel = (gold_id - first) / (last - first) if last > first else 0.0
    if rel < 1 / 3:
        return "early"
    if rel < 2 / 3:
        return "middle"
    return "late"


def recall_by_third(cases: list[dict], metrics_by_case: dict[str, dict]) -> dict:
    buckets = {
        "early": {"hit": 0, "total": 0},
        "middle": {"hit": 0, "total": 0},
        "late": {"hit": 0, "total": 0},
    }
    for case in cases:
        case_id = case["case_id"]
        segments = normalize_segments(case)
        matched = {
            item["gold"]
            for item in metrics_by_case[case_id]["matched_boundaries"]
        }
        for gold_id in metrics_by_case[case_id]["gold_boundaries"]:
            bucket = gold_third(gold_id, segments)
            buckets[bucket]["total"] += 1
            if gold_id in matched:
                buckets[bucket]["hit"] += 1
    for value in buckets.values():
        value["recall"] = value["hit"] / value["total"] if value["total"] else 0.0
    return buckets


def split_subwindows(
    segments: list[dict],
    subwindow_seconds: int,
    overlap_ratio: float,
) -> list[list[dict]]:
    first_start = srt_seconds(segments[0]["start"])
    last_end = srt_seconds(segments[-1]["end"])
    stride = subwindow_seconds * (1 - overlap_ratio)
    starts = []
    current = first_start
    while current < last_end:
        starts.append(current)
        current += stride
        if last_end - current < subwindow_seconds * 0.35:
            if current < last_end:
                starts.append(max(first_start, last_end - subwindow_seconds))
            break
    out = []
    seen = set()
    for start in starts:
        end = start + subwindow_seconds
        block = [
            item
            for item in segments
            if srt_seconds(item["start"]) < end
            and srt_seconds(item["end"]) > start
        ]
        if not block:
            continue
        key = (block[0]["id"], block[-1]["id"])
        if key not in seen:
            seen.add(key)
            out.append(block)
    return out


def merge_boundaries(boundaries: list[int], radius: int) -> tuple[list[int], int]:
    if not boundaries:
        return [], 0
    sorted_boundaries = sorted(boundaries)
    clusters = [[sorted_boundaries[0]]]
    for sid in sorted_boundaries[1:]:
        if sid - clusters[-1][-1] <= radius:
            clusters[-1].append(sid)
        else:
            clusters.append([sid])
    merged = []
    duplicates = 0
    for cluster in clusters:
        duplicates += len(cluster) - 1
        # Keep the earliest segment ID. This preserves a conservative transition
        # start and avoids tuning toward Gold labels.
        merged.append(cluster[0])
    return merged, duplicates


def run_full_window_engine(topic_engine, cases, detail: str, model: str) -> dict:
    output = {}
    calls = 0
    started = time.perf_counter()
    for case in cases:
        segments = normalize_segments(case)
        predicted = topic_engine.analyze_window_boundaries(
            segments,
            detail=detail,
            model=model,
        )
        calls += 1
        output[case["case_id"]] = sorted(set(int(item) for item in predicted))
    return {
        "predictions": output,
        "model_calls": calls,
        "runtime_seconds": time.perf_counter() - started,
    }


def run_sliding_engine(
    topic_engine,
    cases,
    detail: str,
    model: str,
    subwindow_seconds: int,
    overlap_ratio: float,
    merge_radius: int,
) -> dict:
    output = {}
    model_calls = 0
    started = time.perf_counter()
    for case in cases:
        segments = normalize_segments(case)
        original_first = segments[0]["id"]
        subwindows = split_subwindows(segments, subwindow_seconds, overlap_ratio)
        raw = []
        subwindow_runs = []
        synthetic_anchor_count = 0
        for block in subwindows:
            predicted = topic_engine.analyze_window_boundaries(
                block,
                detail=detail,
                model=model,
            )
            model_calls += 1
            predicted = sorted(set(int(item) for item in predicted))
            semantic = []
            for sid in predicted:
                if sid == block[0]["id"] and sid != original_first:
                    synthetic_anchor_count += 1
                    continue
                semantic.append(sid)
            raw.extend(semantic)
            subwindow_runs.append(
                {
                    "first_segment_id": block[0]["id"],
                    "last_segment_id": block[-1]["id"],
                    "raw_predictions": predicted,
                    "semantic_predictions": semantic,
                }
            )
        merged, duplicate_count = merge_boundaries(raw, merge_radius)
        if original_first not in merged:
            merged = [original_first] + merged
        merged = sorted(set(merged))
        output[case["case_id"]] = {
            "predicted_boundaries": merged,
            "raw_prediction_count": len(raw),
            "duplicate_predictions_before_merge": duplicate_count,
            "duplicate_predictions_after_merge": 0,
            "synthetic_anchor_count": synthetic_anchor_count,
            "subwindow_count": len(subwindows),
            "subwindow_runs": subwindow_runs,
        }
    return {
        "predictions": {
            case_id: data["predicted_boundaries"]
            for case_id, data in output.items()
        },
        "cases": output,
        "model_calls": model_calls,
        "runtime_seconds": time.perf_counter() - started,
    }


def evaluate_predictions(
    cases: list[dict],
    predictions: dict[str, list[int]],
    tolerances: list[int],
) -> dict:
    result = {}
    for tolerance in tolerances:
        case_metrics = []
        by_case = {}
        for case in cases:
            case_id = case["case_id"]
            gold = [int(item) for item in case["gold"]["boundaries"]]
            predicted = sorted(set(int(item) for item in predictions[case_id]))
            metrics = metrics_for(gold, predicted, tolerance)
            metrics["case_id"] = case_id
            metrics["window_number"] = case.get("window_number")
            case_metrics.append(metrics)
            by_case[case_id] = metrics
        result[str(tolerance)] = {
            "aggregate": aggregate_metrics(case_metrics),
            "cases": case_metrics,
            "recall_by_third": recall_by_third(cases, by_case),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--topics-module", type=Path, default=DEFAULT_TOPICS_MODULE)
    parser.add_argument("--detail", default="auto", choices=["low", "auto", "high"])
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--subwindow-seconds", type=int, default=300)
    parser.add_argument("--overlap-ratio", type=float, default=0.25)
    parser.add_argument("--merge-radius", type=int, default=2)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path. Defaults to benchmark results folder.",
    )
    args = parser.parse_args()

    benchmark = load_json(args.benchmark)
    cases = selected_cases(benchmark)
    if not cases:
        raise SystemExit("No gold_complete benchmark cases found")

    topic_engine = import_topic_engine(args.topics_module)

    baseline = run_full_window_engine(
        topic_engine,
        cases,
        detail=args.detail,
        model=args.model,
    )
    sliding = run_sliding_engine(
        topic_engine,
        cases,
        detail=args.detail,
        model=args.model,
        subwindow_seconds=args.subwindow_seconds,
        overlap_ratio=args.overlap_ratio,
        merge_radius=args.merge_radius,
    )

    tolerances = [0, 1, 2]
    baseline["metrics"] = evaluate_predictions(cases, baseline["predictions"], tolerances)
    sliding["metrics"] = evaluate_predictions(cases, sliding["predictions"], tolerances)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = {
        "schema_version": 1,
        "type": "seminartext_sliding_subwindow_topic_engine_experiment",
        "timestamp": timestamp,
        "parameters": {
            "detail": args.detail,
            "model": args.model,
            "subwindow_seconds": args.subwindow_seconds,
            "overlap_ratio": args.overlap_ratio,
            "merge_radius_segment_ids": args.merge_radius,
            "synthetic_subwindow_anchor_policy": (
                "drop sub-window first boundary unless it is the original "
                "benchmark window first segment"
            ),
        },
        "engine_version": {
            "source_path": str(args.topics_module),
            "source_sha256": hashlib.sha256(args.topics_module.read_bytes()).hexdigest(),
            "entrypoint": "analyze_window_boundaries",
        },
        "benchmark_version": {
            "source_path": str(args.benchmark),
            "source_sha256": hashlib.sha256(args.benchmark.read_bytes()).hexdigest(),
            "gold_complete_cases": len(cases),
            "gold_topic_count": sum(
                len(case["gold"]["boundaries"])
                for case in cases
            ),
        },
        "baseline_full_window": baseline,
        "sliding_subwindow": sliding,
    }

    output = args.output
    if output is None:
        output = (
            args.benchmark.parent
            / "results"
            / f"sliding_subwindow_experiment_{timestamp}.json"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"JSON: {output}")
    print()
    for name, section in (
        ("baseline", baseline),
        ("sliding", sliding),
    ):
        print(name)
        print(f"  model_calls: {section['model_calls']}")
        print(f"  runtime_seconds: {section['runtime_seconds']:.1f}")
        for tolerance in tolerances:
            aggregate = section["metrics"][str(tolerance)]["aggregate"]
            print(
                f"  tolerance {tolerance}: "
                f"P={aggregate['boundary_precision']:.3f} "
                f"R={aggregate['boundary_recall']:.3f} "
                f"F1={aggregate['boundary_f1']:.3f} "
                f"pred={aggregate['predicted_topic_count']}"
            )
        third = section["metrics"]["2"]["recall_by_third"]
        print(
            "  recall_by_third tol2: "
            f"early={third['early']['recall']:.3f} "
            f"middle={third['middle']['recall']:.3f} "
            f"late={third['late']['recall']:.3f}"
        )
    print()
    print("EXPERIMENT COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
