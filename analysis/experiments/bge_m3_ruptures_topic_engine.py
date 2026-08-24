#!/usr/bin/env python3
"""Read-only bge-m3 + ruptures Topic Engine experiment for Dataset A.

This helper runs a proper `ruptures` change-point detector on a bge-m3 semantic
change representation. It is experimental only and does not modify production
Topic Engine behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import ruptures as rpt


DEFAULT_BENCHMARK = (
    Path.home()
    / "Documents"
    / "seminartext_projects"
    / "Стресс код"
    / "analysis"
    / "benchmark"
    / "topic_benchmark.json"
)

BASELINE_TOL2 = {
    "precision": 0.500,
    "recall": 0.458,
    "f1": 0.478,
}

SLIDING_TOL2 = {
    "precision": 0.383,
    "recall": 0.479,
    "f1": 0.426,
}

LOCAL_PEAK_BGE_TOL2 = {
    "precision": 0.577,
    "recall": 0.312,
    "f1": 0.405,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    return [
        {
            "id": int(item["id"]),
            "start": str(item["start"]),
            "end": str(item["end"]),
            "text": str(item["text"]),
        }
        for item in case.get("segments", [])
    ]


def selected_cases(benchmark: dict) -> list[dict]:
    return [
        case
        for case in benchmark.get("cases", [])
        if case.get("review", {}).get("status") == "gold_complete"
    ]


def make_semantic_blocks(segments: list[dict], block_seconds: int) -> list[dict]:
    if not segments:
        return []
    blocks = []
    current = []
    block_start = srt_seconds(segments[0]["start"])
    block_end = block_start + block_seconds
    for segment in segments:
        segment_start = srt_seconds(segment["start"])
        if current and segment_start >= block_end:
            blocks.append(block_from_segments(current))
            current = []
            while segment_start >= block_end:
                block_start = block_end
                block_end = block_start + block_seconds
        current.append(segment)
    if current:
        blocks.append(block_from_segments(current))
    return blocks


def block_from_segments(segments: list[dict]) -> dict:
    return {
        "start_id": segments[0]["id"],
        "end_id": segments[-1]["id"],
        "start": segments[0]["start"],
        "end": segments[-1]["end"],
        "text": " ".join(item["text"].strip() for item in segments if item["text"].strip()),
    }


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def semantic_change_features(
    embeddings: np.ndarray,
    context_blocks: int,
) -> np.ndarray:
    """Build one feature row for each possible boundary between blocks."""
    features = []
    normalized = normalize_rows(embeddings)
    for boundary_index in range(1, len(normalized)):
        left = normalized[max(0, boundary_index - context_blocks):boundary_index]
        right = normalized[boundary_index:boundary_index + context_blocks]
        left_mean = left.mean(axis=0)
        right_mean = right.mean(axis=0)
        cosine = float(
            np.dot(left_mean, right_mean)
            / (np.linalg.norm(left_mean) * np.linalg.norm(right_mean))
        )
        change = 1.0 - cosine
        features.append([change])
    return np.asarray(features, dtype=float)


def smooth_features(features: np.ndarray) -> np.ndarray:
    if len(features) == 0:
        return features
    out = np.empty_like(features)
    for i in range(len(features)):
        prev_value = features[i - 1, 0] if i > 0 else features[i, 0]
        next_value = features[i + 1, 0] if i + 1 < len(features) else features[i, 0]
        out[i, 0] = 0.25 * prev_value + 0.5 * features[i, 0] + 0.25 * next_value
    return out


def run_pelt(features: np.ndarray, model: str, penalty: float, min_size: int, jump: int) -> list[int]:
    """Return feature-row breakpoints from ruptures PELT, excluding terminal n."""
    if len(features) < max(2, min_size * 2):
        return []
    algo = rpt.Pelt(model=model, min_size=min_size, jump=jump).fit(features)
    breakpoints = algo.predict(pen=penalty)
    return [int(item) for item in breakpoints if int(item) < len(features)]


def enforce_min_gap_segment_ids(boundaries: list[int], min_gap_ids: int) -> list[int]:
    if not boundaries:
        return []
    out = [boundaries[0]]
    for boundary in boundaries[1:]:
        if boundary - out[-1] >= min_gap_ids:
            out.append(boundary)
    return out


def boundaries_from_ruptures_breakpoints(
    segments: list[dict],
    blocks: list[dict],
    breakpoints: list[int],
    min_gap_ids: int,
) -> list[int]:
    boundaries = [segments[0]["id"]]
    for breakpoint in breakpoints:
        # Features are boundaries between blocks. Feature index 0 means before
        # block 1, so a ruptures breakpoint k maps to boundary before block k.
        if 0 < breakpoint < len(blocks):
            boundaries.append(blocks[breakpoint]["start_id"])
    return enforce_min_gap_segment_ids(sorted(set(boundaries)), min_gap_ids)


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
    matches, false_positives, false_negatives = match_boundaries(gold, predicted, tolerance)
    true_positives = len(matches)
    precision = true_positives / len(predicted) if predicted else 0.0
    recall = true_positives / len(gold) if gold else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "gold_boundaries": gold,
        "predicted_boundaries": predicted,
        "matched_boundaries": matches,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_positives": true_positives,
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
            case_metrics.append(metrics)
            by_case[case_id] = metrics
        result[str(tolerance)] = {
            "aggregate": aggregate_metrics(case_metrics),
            "cases": case_metrics,
            "recall_by_third": recall_by_third(cases, by_case),
        }
    return result


def embed_texts_ollama(
    texts: list[str],
    model: str,
    endpoint: str,
    batch_size: int,
    timeout: int,
) -> tuple[np.ndarray, dict]:
    embeddings = []
    prompt_eval_count = 0
    total_duration = 0
    for offset in range(0, len(texts), batch_size):
        batch = texts[offset:offset + batch_size]
        payload = {
            "model": model,
            "input": batch,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama embedding API failed: {exc}") from exc
        batch_embeddings = data.get("embeddings")
        if not isinstance(batch_embeddings, list) or len(batch_embeddings) != len(batch):
            raise RuntimeError("Ollama embedding API returned an unexpected shape")
        embeddings.extend(batch_embeddings)
        prompt_eval_count += int(data.get("prompt_eval_count") or 0)
        total_duration += int(data.get("total_duration") or 0)
    return np.asarray(embeddings, dtype=float), {
        "embedding_batches": math.ceil(len(texts) / batch_size) if texts else 0,
        "prompt_eval_count": prompt_eval_count,
        "ollama_total_duration_ns": total_duration,
    }


def run_experiment(
    cases: list[dict],
    embedding_model: str,
    endpoint: str,
    batch_size: int,
    timeout: int,
    block_seconds: int,
    context_blocks: int,
    smoothing: bool,
    ruptures_model: str,
    penalty: float,
    min_size: int,
    jump: int,
    min_gap_ids: int,
) -> dict:
    started = time.perf_counter()
    predictions = {}
    case_details = {}
    embedding_count = 0
    batch_count = 0
    prompt_eval_count = 0
    ollama_total_duration_ns = 0
    for case in cases:
        case_id = case["case_id"]
        segments = normalize_segments(case)
        blocks = make_semantic_blocks(segments, block_seconds)
        embeddings, stats = embed_texts_ollama(
            [block["text"] for block in blocks],
            model=embedding_model,
            endpoint=endpoint,
            batch_size=batch_size,
            timeout=timeout,
        )
        embedding_count += len(embeddings)
        batch_count += stats["embedding_batches"]
        prompt_eval_count += stats["prompt_eval_count"]
        ollama_total_duration_ns += stats["ollama_total_duration_ns"]
        features = semantic_change_features(embeddings, context_blocks)
        if smoothing:
            features = smooth_features(features)
        breakpoints = run_pelt(
            features,
            model=ruptures_model,
            penalty=penalty,
            min_size=min_size,
            jump=jump,
        )
        predicted = boundaries_from_ruptures_breakpoints(
            segments,
            blocks,
            breakpoints,
            min_gap_ids=min_gap_ids,
        )
        predictions[case_id] = predicted
        case_details[case_id] = {
            "block_count": len(blocks),
            "embedding_count": int(len(embeddings)),
            "feature_count": int(len(features)),
            "ruptures_breakpoints": breakpoints,
            "predicted_boundaries": predicted,
            "top_features": [
                {
                    "feature_index": int(index),
                    "score": float(features[index, 0]),
                }
                for index in np.argsort(features[:, 0])[::-1][:12]
            ] if len(features) else [],
        }
    return {
        "predictions": predictions,
        "cases": case_details,
        "runtime_seconds": time.perf_counter() - started,
        "embedding_count": embedding_count,
        "embedding_batches": batch_count,
        "prompt_eval_count": prompt_eval_count,
        "ollama_total_duration_ns": ollama_total_duration_ns,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--embedding-model", default="bge-m3:latest")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434/api/embed")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--block-seconds", type=int, default=15)
    parser.add_argument("--context-blocks", type=int, default=2)
    parser.add_argument("--no-smoothing", action="store_true")
    parser.add_argument("--ruptures-model", default="rbf")
    parser.add_argument("--penalty", type=float, default=0.5)
    parser.add_argument("--min-size", type=int, default=3)
    parser.add_argument("--jump", type=int, default=1)
    parser.add_argument("--min-gap-ids", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    benchmark = load_json(args.benchmark)
    cases = selected_cases(benchmark)
    if not cases:
        raise SystemExit("No gold_complete benchmark cases found")

    experiment = run_experiment(
        cases,
        embedding_model=args.embedding_model,
        endpoint=args.endpoint,
        batch_size=args.batch_size,
        timeout=args.timeout,
        block_seconds=args.block_seconds,
        context_blocks=args.context_blocks,
        smoothing=not args.no_smoothing,
        ruptures_model=args.ruptures_model,
        penalty=args.penalty,
        min_size=args.min_size,
        jump=args.jump,
        min_gap_ids=args.min_gap_ids,
    )
    tolerances = [0, 1, 2]
    experiment["metrics"] = evaluate_predictions(
        cases,
        experiment["predictions"],
        tolerances,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = {
        "schema_version": 1,
        "type": "seminartext_bge_m3_ruptures_topic_engine_experiment",
        "timestamp": timestamp,
        "parameters": {
            "embedding_model": args.embedding_model,
            "embedding_endpoint": args.endpoint,
            "block_seconds": args.block_seconds,
            "context_blocks": args.context_blocks,
            "signal": "1 - cosine(mean(left_context), mean(right_context))",
            "smoothing": None if args.no_smoothing else "fixed three-point kernel [0.25, 0.5, 0.25]",
            "change_point_library": "ruptures",
            "ruptures_version": rpt.__version__,
            "change_point_method": "PELT",
            "ruptures_model": args.ruptures_model,
            "penalty": args.penalty,
            "min_size_blocks": args.min_size,
            "jump": args.jump,
            "min_gap_segment_ids": args.min_gap_ids,
            "broad_parameter_search": False,
        },
        "dependencies": {
            "python": "see local venv",
            "numpy": np.__version__,
            "ruptures": rpt.__version__,
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
        "comparison_targets": {
            "current_ollama_semantic_baseline_tol2": BASELINE_TOL2,
            "issue_7_sliding_subwindow_tol2": SLIDING_TOL2,
            "issue_9_local_peak_bge_m3_tol2": LOCAL_PEAK_BGE_TOL2,
        },
        "bge_m3_ruptures": experiment,
    }

    output = args.output
    if output is None:
        output = (
            args.benchmark.parent
            / "results"
            / f"bge_m3_ruptures_experiment_{timestamp}.json"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"JSON: {output}")
    print(
        f"runtime_seconds: {experiment['runtime_seconds']:.1f}, "
        f"embeddings: {experiment['embedding_count']}, "
        f"batches: {experiment['embedding_batches']}"
    )
    for tolerance in tolerances:
        aggregate = experiment["metrics"][str(tolerance)]["aggregate"]
        print(
            f"tolerance {tolerance}: "
            f"P={aggregate['boundary_precision']:.3f} "
            f"R={aggregate['boundary_recall']:.3f} "
            f"F1={aggregate['boundary_f1']:.3f} "
            f"pred={aggregate['predicted_topic_count']}"
        )
    third = experiment["metrics"]["2"]["recall_by_third"]
    print(
        "recall_by_third tol2: "
        f"early={third['early']['recall']:.3f} "
        f"middle={third['middle']['recall']:.3f} "
        f"late={third['late']['recall']:.3f}"
    )
    print("EXPERIMENT COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
