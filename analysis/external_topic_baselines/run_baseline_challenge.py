#!/usr/bin/env python3
"""Policy-locked external Topic Engine baseline challenge for Issue #45.

This experiment adapter calls external algorithms; it does not implement a new
segmentation algorithm. It accepts only the frozen hashes of development
Datasets A and B and deliberately has no option for C, D, or E.
"""

from __future__ import annotations

import argparse
import asyncio
import bisect
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from seminartext_modules.dataset_governance import enforce_benchmark_artifact


CONFIG_PATH = Path(__file__).with_name("challenge_config.json")
EXPECTED_HASHES = {
    "A": "3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803",
    "B": "a8a4817eea4ad8639eb4d5fa0801cd5f22fd9a5ccb8489b9868f38967b255fcb",
}
_TREESEG_EVENT_LOOP: asyncio.AbstractEventLoop | None = None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_allowed_benchmark(label: str, path: Path) -> dict[str, Any]:
    actual = sha256_file(path)
    expected = EXPECTED_HASHES[label]
    if actual != expected:
        raise SystemExit(
            f"Dataset {label} hash mismatch: expected {expected}, got {actual}. "
            "Issue #45 permits only the policy-locked A/B development artifacts."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if len(cases) != 6 or any(
        case.get("review", {}).get("status") != "gold_complete" for case in cases
    ):
        raise SystemExit(f"Dataset {label} is not the expected 6-case Gold-complete artifact")
    return payload


def parse_timestamp(value: str) -> float:
    hours, minutes, rest = value.replace(".", ",").split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def window_duration_seconds(case: dict[str, Any]) -> float:
    return parse_timestamp(case["end"]) - parse_timestamp(case["start"])


def match_boundaries(
    gold: list[int], predicted: list[int], tolerance: int
) -> tuple[list[dict[str, int]], list[int], list[int]]:
    remaining = set(range(len(predicted)))
    matches = []
    for gold_id in gold:
        candidates = [
            (abs(predicted[index] - gold_id), predicted[index], index)
            for index in remaining
            if abs(predicted[index] - gold_id) <= tolerance
        ]
        if not candidates:
            continue
        distance, predicted_id, index = min(candidates)
        remaining.remove(index)
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


def metrics_for(gold: list[int], predicted: list[int], tolerance: int) -> dict[str, Any]:
    matches, false_positives, false_negatives = match_boundaries(
        gold, predicted, tolerance
    )
    true_positives = len(matches)
    precision = true_positives / len(predicted) if predicted else 0.0
    recall = true_positives / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
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
        "absolute_topic_count_error": abs(len(predicted) - len(gold)),
    }


def aggregate_metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    gold_count = sum(item["gold_topic_count"] for item in cases)
    predicted_count = sum(item["predicted_topic_count"] for item in cases)
    true_positives = sum(item["true_positives"] for item in cases)
    false_positives = sum(len(item["false_positives"]) for item in cases)
    false_negatives = sum(len(item["false_negatives"]) for item in cases)
    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "case_count": len(cases),
        "gold_topic_count": gold_count,
        "predicted_topic_count": predicted_count,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "boundary_precision": precision,
        "boundary_recall": recall,
        "boundary_f1": f1,
        "oversegmentation_proxy_false_positives": false_positives,
        "undersegmentation_proxy_false_negatives": false_negatives,
        "mean_topic_count_error": sum(item["topic_count_error"] for item in cases)
        / len(cases),
        "mean_absolute_topic_count_error": sum(
            item["absolute_topic_count_error"] for item in cases
        )
        / len(cases),
    }


def evaluate(
    benchmark: dict[str, Any], predictions: dict[str, list[int]], tolerances: list[int]
) -> dict[str, Any]:
    by_tolerance = {}
    for tolerance in tolerances:
        case_metrics = []
        for case in benchmark["cases"]:
            case_id = case["case_id"]
            item = metrics_for(
                [int(value) for value in case["gold"]["boundaries"]],
                sorted(set(predictions[case_id])),
                tolerance,
            )
            item["case_id"] = case_id
            case_metrics.append(item)
        by_tolerance[str(tolerance)] = {
            "aggregate": aggregate_metrics(case_metrics),
            "cases": case_metrics,
        }
    return by_tolerance


def joined_segment_text(case: dict[str, Any], separator: str) -> tuple[str, list[int]]:
    pieces = []
    offsets = []
    cursor = 0
    for index, segment in enumerate(case["segments"]):
        if index:
            pieces.append(separator)
            cursor += len(separator)
        offsets.append(cursor)
        text = str(segment["text"]).strip()
        pieces.append(text)
        cursor += len(text)
    return "".join(pieces), offsets


def chunk_offsets_to_boundaries(
    case: dict[str, Any], offsets: list[int], chunk_starts: list[int]
) -> list[int]:
    segment_ids = [int(item["id"]) for item in case["segments"]]
    boundaries = [segment_ids[0]]
    for start in chunk_starts:
        index = max(0, bisect.bisect_right(offsets, start) - 1)
        boundaries.append(segment_ids[index])
    return sorted(set(boundaries))


def ollama_embed(endpoint: str, model: str, texts: list[str]) -> list[list[float]]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"model": model, "input": texts}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.load(response)
    return payload["embeddings"]


def run_chonkie(
    benchmark: dict[str, Any], config: dict[str, Any]
) -> tuple[dict[str, list[int]], dict[str, float]]:
    import numpy as np
    from chonkie import AutoTokenizer, SemanticChunker
    from chonkie.embeddings import BaseEmbeddings

    shared = config["shared"]
    candidate = config["chonkie_semantic"]

    class OllamaBgeM3Embeddings(BaseEmbeddings):
        def __init__(self) -> None:
            super().__init__()
            self.tokenizer = AutoTokenizer("character")
            self.cache: dict[str, Any] = {}

        def embed(self, text: str) -> Any:
            return self.embed_batch([text])[0]

        def embed_batch(self, texts: list[str]) -> list[Any]:
            missing = list(dict.fromkeys(text for text in texts if text not in self.cache))
            if missing:
                values = ollama_embed(
                    shared["embedding_endpoint"], shared["embedding_model"], missing
                )
                self.cache.update(
                    (text, np.asarray(value, dtype=np.float32))
                    for text, value in zip(missing, values)
                )
            return [self.cache[text] for text in texts]

        @property
        def dimension(self) -> int:
            return 1024

        def get_tokenizer(self) -> Any:
            return self.tokenizer

    embeddings = OllamaBgeM3Embeddings()
    chunker = SemanticChunker(
        embedding_model=embeddings,
        threshold=candidate["threshold"],
        chunk_size=candidate["chunk_size_characters"],
        similarity_window=candidate["similarity_window"],
        min_sentences_per_chunk=candidate["min_sentences_per_chunk"],
        min_characters_per_sentence=candidate["min_characters_per_sentence"],
        delim=[". ", "! ", "? ", "\n"],
        include_delim="prev",
        filter_window=candidate["filter_window"],
        filter_polyorder=candidate["filter_polyorder"],
        filter_tolerance=candidate["filter_tolerance"],
    )
    predictions = {}
    runtimes = {}
    for case in benchmark["cases"]:
        text, offsets = joined_segment_text(case, "\n")
        started = time.perf_counter()
        chunks = chunker(text)
        runtimes[case["case_id"]] = time.perf_counter() - started
        predictions[case["case_id"]] = chunk_offsets_to_boundaries(
            case, offsets, [chunk.start_index for chunk in chunks[1:]]
        )
    return predictions, runtimes


def run_treeseg(
    benchmark: dict[str, Any], config: dict[str, Any]
) -> tuple[dict[str, list[int]], dict[str, float]]:
    global _TREESEG_EVENT_LOOP
    temporary_mpl = tempfile.TemporaryDirectory(prefix="seminartext-issue45-mpl-")
    os.environ.setdefault("MPLCONFIGDIR", temporary_mpl.name)
    from treeseg import TreeSeg, ollama_embeddings
    from treeseg.embeddings import Embeddings

    shared = config["shared"]
    candidate = config["treeseg"]
    endpoint = shared["embedding_endpoint"].removesuffix("/api/embed")
    embedding_config = Embeddings(
        embeddings_func=ollama_embeddings,
        headers={},
        model=shared["embedding_model"],
        endpoint=endpoint,
    )
    treeseg_config = {
        "MIN_SEGMENT_SIZE": candidate["min_segment_size"],
        "LAMBDA_BALANCE": candidate["lambda_balance"],
        "UTTERANCE_EXPANSION_WIDTH": candidate["utterance_expansion_width"],
        "EMBEDDINGS": embedding_config,
        "TEXT_KEY": "composite",
    }
    predictions = {}
    runtimes = {}
    if _TREESEG_EVENT_LOOP is None:
        _TREESEG_EVENT_LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(_TREESEG_EVENT_LOOP)
    try:
        for case in benchmark["cases"]:
            entries = [
                {"composite": str(segment["text"]), "segment_id": int(segment["id"])}
                for segment in case["segments"]
            ]
            target_k = max(
                2,
                round(
                    window_duration_seconds(case)
                    * shared["topic_density_prior_per_hour"]
                    / 3600
                ),
            )
            started = time.perf_counter()
            segmenter = TreeSeg(configs=treeseg_config, entries=entries)
            if any("embedding" not in block for block in segmenter.blocks):
                raise RuntimeError("TreeSeg did not embed every transcript unit")
            transitions = segmenter.segment_meeting(K=target_k)
            runtimes[case["case_id"]] = time.perf_counter() - started
            boundaries = [int(case["segments"][0]["id"])]
            boundaries.extend(
                int(case["segments"][index]["id"])
                for index, transition in enumerate(transitions)
                if transition
            )
            predictions[case["case_id"]] = sorted(set(boundaries))
    finally:
        temporary_mpl.cleanup()
    return predictions, runtimes


def close_treeseg_event_loop() -> None:
    global _TREESEG_EVENT_LOOP
    if _TREESEG_EVENT_LOOP is not None:
        _TREESEG_EVENT_LOOP.close()
        _TREESEG_EVENT_LOOP = None
        asyncio.set_event_loop(None)


def run_texttiling_compatibility(
    benchmark: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    from nltk.corpus import stopwords
    from nltk.tokenize.texttiling import TextTilingTokenizer

    candidate = config["nltk_texttiling"]
    tokenizer = TextTilingTokenizer(
        w=candidate["w"],
        k=candidate["k"],
        stopwords=stopwords.words("russian"),
    )
    cases = {}
    for case in benchmark["cases"]:
        text, _ = joined_segment_text(case, "\n\n")
        started = time.perf_counter()
        try:
            chunks = tokenizer.tokenize(text)
            cases[case["case_id"]] = {
                "status": "completed",
                "chunk_count": len(chunks),
                "runtime_seconds": time.perf_counter() - started,
            }
        except Exception as error:  # external compatibility evidence
            cases[case["case_id"]] = {
                "status": "incompatible",
                "error_type": type(error).__name__,
                "error": str(error),
                "runtime_seconds": time.perf_counter() - started,
            }
    statuses = {item["status"] for item in cases.values()}
    return {
        "status": "incompatible" if statuses == {"incompatible"} else "mixed",
        "cases": cases,
    }


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-a", type=Path, required=True)
    parser.add_argument("--dataset-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--candidates",
        nargs="+",
        choices=("chonkie", "treeseg", "texttiling"),
        default=("chonkie", "treeseg", "texttiling"),
    )
    args = parser.parse_args()

    enforce_benchmark_artifact(
        "experiment_run", dataset_id="A", benchmark_path=args.dataset_a
    )
    enforce_benchmark_artifact(
        "experiment_run", dataset_id="B", benchmark_path=args.dataset_b
    )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    benchmarks = {
        "A": load_allowed_benchmark("A", args.dataset_a),
        "B": load_allowed_benchmark("B", args.dataset_b),
    }
    tolerances = config["shared"]["boundary_tolerances_segment_ids"]
    result: dict[str, Any] = {
        "schema_version": 1,
        "type": "seminartext_external_topic_baseline_challenge",
        "issue": 45,
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "policy": {
            "datasets_used": ["A", "B"],
            "datasets_not_read_or_run": ["C", "D", "E"],
            "dataset_hashes": EXPECTED_HASHES,
            "config_sha256": sha256_file(CONFIG_PATH),
        },
        "environment": {
            "python": platform.python_version(),
            "machine": platform.machine(),
            "chonkie": package_version("chonkie"),
            "nltk": package_version("nltk"),
            "topic_treeseg": package_version("topic_treeseg"),
            "embedding_model": config["shared"]["embedding_model"],
        },
        "candidates": {},
    }

    runners = {"chonkie": run_chonkie, "treeseg": run_treeseg}
    for candidate_name in ("chonkie", "treeseg"):
        if candidate_name not in args.candidates:
            continue
        candidate_result = {"status": "completed", "datasets": {}}
        for label, benchmark in benchmarks.items():
            predictions, runtimes = runners[candidate_name](benchmark, config)
            candidate_result["datasets"][label] = {
                "predictions": predictions,
                "metrics": evaluate(benchmark, predictions, tolerances),
                "runtime_seconds": {
                    "total": sum(runtimes.values()),
                    "per_case": runtimes,
                },
            }
        if candidate_name == "treeseg":
            close_treeseg_event_loop()
        result["candidates"][candidate_name] = candidate_result

    if "texttiling" in args.candidates:
        result["candidates"]["texttiling"] = {
            "status": "compatibility_control",
            "datasets": {
                label: run_texttiling_compatibility(benchmark, config)
                for label, benchmark in benchmarks.items()
            },
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output)


if __name__ == "__main__":
    main()
