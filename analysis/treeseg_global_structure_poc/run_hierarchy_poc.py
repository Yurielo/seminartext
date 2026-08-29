#!/usr/bin/env python3
"""Bounded TreeSeg temporal-hierarchy POC for GitHub Issue #52.

This is an isolated adapter around upstream TreeSeg. It does not implement a
segmentation or hierarchy algorithm. Existing local topic ranges are immutable
leaves; TreeSeg sees only transcript evidence text and creates parent groups.
Existing LLM titles are copied only to a separate display-label artifact.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import math
import statistics
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_PROJECT = REPO_ROOT.parent / "seminartext_projects" / "Стресс код"
CONFIG_PATH = HERE / "config.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def distribution(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "p90": 0.0, "max": 0.0}
    return {
        "min": round(min(values), 3),
        "median": round(statistics.median(values), 3),
        "p90": round(percentile(values, 0.9), 3),
        "max": round(max(values), 3),
    }


def load_locked_inputs(project_dir: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = config["input"]
    topics_path = project_dir / spec["topics_relative_path"]
    transcript_path = project_dir / spec["transcript_relative_path"]
    actual = {
        "topics_sha256": sha256_file(topics_path),
        "transcript_sha256": sha256_file(transcript_path),
    }
    expected = {
        "topics_sha256": spec["expected_topics_sha256"],
        "transcript_sha256": spec["expected_transcript_sha256"],
    }
    if actual != expected:
        raise SystemExit(f"Golden Seminar input hash mismatch: expected {expected}, got {actual}")
    topics = json.loads(topics_path.read_text(encoding="utf-8"))
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    if topics.get("topic_count") != spec["expected_topic_count"]:
        raise SystemExit("Unexpected local-topic count")
    if transcript.get("segment_count") != spec["expected_segment_count"]:
        raise SystemExit("Unexpected transcript-segment count")
    return topics, transcript


def verify_runtime_pins(config: dict[str, Any]) -> dict[str, Any]:
    distribution_meta = importlib.metadata.distribution("topic_treeseg")
    observed_version = distribution_meta.version
    if observed_version != config["treeseg"]["package_version"]:
        raise SystemExit(f"TreeSeg version mismatch: expected {config['treeseg']['package_version']}, got {observed_version}")
    direct_url = json.loads(distribution_meta.read_text("direct_url.json") or "{}")
    observed_commit = direct_url.get("vcs_info", {}).get("commit_id")
    if observed_commit != config["treeseg"]["upstream_commit"]:
        raise SystemExit(f"TreeSeg commit mismatch: expected {config['treeseg']['upstream_commit']}, got {observed_commit}")
    endpoint = config["embeddings"]["endpoint"].rstrip("/") + "/api/tags"
    with urllib.request.urlopen(endpoint, timeout=30) as response:
        models = json.load(response).get("models", [])
    requested = config["embeddings"]["model"]
    model = next((item for item in models if item.get("name") == requested or item.get("model") == requested), None)
    if model is None:
        raise SystemExit(f"Required Ollama model is unavailable: {requested}")
    observed_digest = model.get("digest")
    if observed_digest != config["embeddings"]["expected_model_digest"]:
        raise SystemExit(f"Embedding digest mismatch: expected {config['embeddings']['expected_model_digest']}, got {observed_digest}")
    return {"package_version": observed_version, "upstream_commit": observed_commit, "embedding_model_digest": observed_digest}


def build_entries(topics_doc: dict[str, Any], transcript_doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Build TreeSeg entries from evidence text, explicitly excluding titles/summaries."""
    segments = {int(item["id"]): item for item in transcript_doc["segments"]}
    entries = []
    previous_last = 0
    for index, topic in enumerate(topics_doc["topics"]):
        if topic["source_id"] != transcript_doc["source_id"]:
            raise ValueError("POC accepts only the locked video_001 topic sequence")
        first = int(topic["start_segment_id"])
        last = int(str(topic["evidence"]["last"]).rsplit(":", 1)[1])
        if first != previous_last + 1:
            raise ValueError(f"Non-contiguous topic evidence at {topic['topic_id']}")
        selected = [segments[segment_id] for segment_id in range(first, last + 1)]
        if len(selected) != int(topic["evidence"]["count"]):
            raise ValueError(f"Evidence count mismatch at {topic['topic_id']}")
        entries.append(
            {
                "local_index": index,
                "topic_id": topic["topic_id"],
                "composite": " ".join(str(item["text"]).strip() for item in selected),
                "start_seconds": float(topic["start_seconds"]),
                "end_seconds": float(topic["end_seconds"]),
                "first_segment_id": first,
                "last_segment_id": last,
            }
        )
        previous_last = last
    if previous_last != int(transcript_doc["segment_count"]):
        raise ValueError("Topic sequence does not cover the full locked transcript")
    return entries


def tree_to_structure(root: Any, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Serialize the native TreeSeg tree and attach immutable input topics as leaves."""
    nodes: list[dict[str, Any]] = []

    def visit(node: Any, depth: int) -> str:
        group_id = "group_root" if node.identifier == "*" else f"group_{node.identifier[1:]}"
        indexes = [int(value) for value in node.segment]
        child_ids: list[str] = []
        if node.left is not None and node.right is not None:
            child_ids = [visit(node.left, depth + 1), visit(node.right, depth + 1)]
        else:
            for local_index in indexes:
                entry = entries[local_index]
                topic_node_id = f"leaf_{entry['topic_id']}"
                child_ids.append(topic_node_id)
                nodes.append(
                    {
                        "node_id": topic_node_id,
                        "node_type": "local_topic_leaf",
                        "hierarchy_depth": depth + 1,
                        "temporal_order": local_index + 1,
                        "start_seconds": entry["start_seconds"],
                        "end_seconds": entry["end_seconds"],
                        "duration_seconds": round(entry["end_seconds"] - entry["start_seconds"], 3),
                        "child_ids": [],
                        "source_topic_ids": [entry["topic_id"]],
                        "provenance": {
                            "source_id": "video_001",
                            "first_segment_id": entry["first_segment_id"],
                            "last_segment_id": entry["last_segment_id"],
                            "first_evidence_id": f"video_001:segment:{entry['first_segment_id']:06d}",
                            "last_evidence_id": f"video_001:segment:{entry['last_segment_id']:06d}",
                        },
                    }
                )
        start = entries[indexes[0]]["start_seconds"]
        end = entries[indexes[-1]]["end_seconds"]
        nodes.append(
            {
                "node_id": group_id,
                "node_type": "treeseg_parent_group",
                "hierarchy_depth": depth,
                "temporal_order": indexes[0] + 1,
                "start_seconds": start,
                "end_seconds": end,
                "duration_seconds": round(end - start, 3),
                "child_ids": child_ids,
                "source_topic_ids": [entries[i]["topic_id"] for i in indexes],
                "provenance": {
                    "upstream_node_identifier": node.identifier,
                    "input_local_indexes_zero_based": indexes,
                },
            }
        )
        return group_id

    root_id = visit(root, 0)
    nodes.sort(key=lambda item: (item["temporal_order"], item["hierarchy_depth"], item["node_id"]))
    return {"root_node_id": root_id, "nodes": nodes}


def validate_temporal_integrity(structure: dict[str, Any]) -> dict[str, Any]:
    by_id = {item["node_id"]: item for item in structure["nodes"]}
    violations: list[str] = []
    parent_references = Counter()
    for node in structure["nodes"]:
        children = [by_id[child_id] for child_id in node["child_ids"]]
        for child in children:
            parent_references[child["node_id"]] += 1
        if children:
            ordered = sorted(children, key=lambda item: item["temporal_order"])
            if children != ordered:
                violations.append(f"{node['node_id']}: child order inversion")
            if ordered[0]["start_seconds"] != node["start_seconds"] or ordered[-1]["end_seconds"] != node["end_seconds"]:
                violations.append(f"{node['node_id']}: child coverage mismatch")
            for left, right in zip(ordered, ordered[1:]):
                if left["end_seconds"] != right["start_seconds"]:
                    violations.append(f"{node['node_id']}: child gap/overlap")
    for node in structure["nodes"]:
        expected = 0 if node["node_id"] == structure["root_node_id"] else 1
        if parent_references[node["node_id"]] != expected:
            violations.append(f"{node['node_id']}: parent reference count")
    return {
        "valid": not violations,
        "violation_count": len(violations),
        "violations": violations,
    }


def compute_metrics(structure: dict[str, Any], config: dict[str, Any], runtime_seconds: float) -> dict[str, Any]:
    nodes = structure["nodes"]
    leaves = [item for item in nodes if item["node_type"] == "local_topic_leaf"]
    parents = [item for item in nodes if item["node_type"] == "treeseg_parent_group"]
    by_id = {item["node_id"]: item for item in nodes}
    terminal = [item for item in parents if all(by_id[c]["node_type"] == "local_topic_leaf" for c in item["child_ids"])]
    parent_count_by_depth = Counter(str(item["hierarchy_depth"]) for item in parents)
    duration_by_depth = defaultdict(list)
    for item in parents:
        duration_by_depth[str(item["hierarchy_depth"])].append(item["duration_seconds"])
    thresholds = config["metrics"]
    source_start = leaves[0]["start_seconds"]
    window_index = {
        item["source_topic_ids"][0]: int((item["start_seconds"] - source_start) // thresholds["source_window_seconds"])
        for item in leaves
    }
    ordered_leaves = sorted(leaves, key=lambda item: item["temporal_order"])
    window_edges = [
        (left["source_topic_ids"][0], right["source_topic_ids"][0])
        for left, right in zip(ordered_leaves, ordered_leaves[1:])
        if window_index[left["source_topic_ids"][0]] != window_index[right["source_topic_ids"][0]]
    ]
    terminal_sets = [set(item["source_topic_ids"]) for item in terminal]
    crossed = sum(any(left in group and right in group for group in terminal_sets) for left, right in window_edges)
    nonroot = [item for item in parents if item["node_id"] != structure["root_node_id"]]
    top_children = [by_id[item] for item in by_id[structure["root_node_id"]]["child_ids"]]
    integrity = validate_temporal_integrity(structure)
    return {
        "evaluation_policy": "objective_structure_only_no_hierarchy_gold_no_f1",
        "leaf_count": len(leaves),
        "parent_count": len(parents),
        "parent_count_per_level": dict(sorted(parent_count_by_depth.items(), key=lambda pair: int(pair[0]))),
        "hierarchy_depth": max(item["hierarchy_depth"] for item in nodes),
        "parent_group_duration_seconds_by_level": {
            level: distribution(values)
            for level, values in sorted(duration_by_depth.items(), key=lambda pair: int(pair[0]))
        },
        "terminal_parent_count": len(terminal),
        "terminal_group_leaf_count_distribution": distribution([len(item["source_topic_ids"]) for item in terminal]),
        "terminal_group_duration_seconds_distribution": distribution([item["duration_seconds"] for item in terminal]),
        "singleton_rate": sum(len(item["source_topic_ids"]) == 1 for item in terminal) / len(terminal),
        "fragmentation_indicators": {
            "terminal_groups_with_two_or_fewer_leaves": sum(len(item["source_topic_ids"]) <= 2 for item in terminal),
            "terminal_groups_shorter_than_15_minutes": sum(item["duration_seconds"] < thresholds["fragment_short_duration_seconds"] for item in terminal),
            "source_window_transition_edges": len(window_edges),
            "source_window_transition_edges_joined_in_terminal_groups": crossed,
        },
        "over_merge_indicators": {
            "terminal_groups_longer_than_60_minutes": sum(item["duration_seconds"] > thresholds["overmerge_long_duration_seconds"] for item in terminal),
            "terminal_groups_broader_than_six_leaves": sum(len(item["source_topic_ids"]) > thresholds["overmerge_broad_leaf_count"] for item in terminal),
            "nonroot_parent_groups_covering_more_than_75_percent_of_leaves": sum(len(item["source_topic_ids"]) / len(leaves) > 0.75 for item in nonroot),
            "largest_top_level_child_leaf_share": round(max(len(item["source_topic_ids"]) for item in top_children) / len(leaves), 6),
        },
        "coverage": {
            "topicized_representation_leaf_coverage": 1.0,
            "topicized_representation_time_coverage": 1.0,
            "covered_source_ids": ["video_001"],
            "golden_seminar_source_files_total": 4,
            "golden_seminar_source_file_coverage": 0.25,
            "limitation": "Allowed existing local topics cover the full first-day representation only; no hierarchy input was invented for video_002..video_004.",
        },
        "temporal_order_integrity": integrity,
        "runtime_seconds": round(runtime_seconds, 6),
    }


def make_flat_baseline(topics_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "role": "comparison_only_existing_flat_local_topic_sequence",
        "structure_influence": "none",
        "topics": [
            {
                "temporal_order": index + 1,
                "topic_id": topic["topic_id"],
                "start_seconds": topic["start_seconds"],
                "end_seconds": topic["end_seconds"],
                "duration_seconds": round(topic["end_seconds"] - topic["start_seconds"], 3),
                "provenance": topic["evidence"],
            }
            for index, topic in enumerate(topics_doc["topics"])
        ],
    }


def make_derived_labels(topics_doc: dict[str, Any], structure: dict[str, Any]) -> dict[str, Any]:
    titles = {topic["topic_id"]: topic.get("title") or "(без названия)" for topic in topics_doc["topics"]}
    labels = {}
    for node in structure["nodes"]:
        topic_ids = node["source_topic_ids"]
        if node["node_type"] == "local_topic_leaf":
            labels[node["node_id"]] = titles[topic_ids[0]]
        else:
            labels[node["node_id"]] = f"Темы {node['temporal_order']}–{node['temporal_order'] + len(topic_ids) - 1}: {titles[topic_ids[0]]} → {titles[topic_ids[-1]]}"
    return {
        "schema_version": 1,
        "derived_layer_only": True,
        "used_by_treeseg_structure": False,
        "source": "existing seminar_topics.json titles; no new LLM call",
        "labels": labels,
    }


def make_review_evidence(entries: list[dict[str, Any]]) -> dict[str, Any]:
    excerpts = {}
    for entry in entries:
        text = " ".join(entry["composite"].split())
        excerpts[entry["topic_id"]] = {
            "first_segment_id": entry["first_segment_id"],
            "last_segment_id": entry["last_segment_id"],
            "opening_excerpt": text[:320],
            "closing_excerpt": text[-320:],
        }
    return {
        "schema_version": 1,
        "review_layer_only": True,
        "source": "locked transcript segments already referenced by each local topic",
        "excerpts": excerpts,
    }


def format_time(seconds: float) -> str:
    value = int(round(seconds))
    return f"{value // 3600:02d}:{(value % 3600) // 60:02d}:{value % 60:02d}"


def select_examples(structure: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    parents = [item for item in structure["nodes"] if item["node_type"] == "treeseg_parent_group" and 3 <= len(item["source_topic_ids"]) <= 8]
    leaf_count = sum(item["node_type"] == "local_topic_leaf" for item in structure["nodes"])
    choices = []
    for name, target in (("Beginning", 0.15), ("Middle", 0.5), ("End", 0.85)):
        selected = min(parents, key=lambda item: (abs((item["temporal_order"] - 1 + len(item["source_topic_ids"]) / 2) / leaf_count - target), len(item["source_topic_ids"]), item["node_id"]))
        choices.append((name, selected))
    return choices


def render_review_packet(structure: dict[str, Any], labels: dict[str, Any], review_evidence: dict[str, Any], metrics: dict[str, Any]) -> str:
    by_id = {item["node_id"]: item for item in structure["nodes"]}
    display = labels["labels"]
    lines = [
        "# TreeSeg Global Seminar Structure POC — Product Owner review packet",
        "",
        "## Decision requested",
        "",
        "Review the bounded TreeSeg hierarchy on the complete available Day 1 local-topic sequence for «Стресс код». This packet does not claim hierarchy accuracy: no hierarchy Gold exists, so no F1 is reported. Titles below are a separate display layer and did not influence TreeSeg.",
        "",
        "Technical handoff verdict: `TREESEG_HIERARCHY_POC_READY_FOR_PRODUCT_REVIEW`.",
        "",
        "Coverage limitation: 31/31 existing local topics and 100% of `video_001`, but only 1/4 source files in the Golden Seminar. No topics or hierarchy were invented for Days 2–4.",
        "",
        "## Full hierarchy overview",
        "",
    ]

    def outline(node_id: str, indent: int = 0) -> None:
        node = by_id[node_id]
        marker = "P" if node["node_type"] == "treeseg_parent_group" else "L"
        lines.append(f"{'  ' * indent}- `{marker}` `{node_id}` · {format_time(node['start_seconds'])}–{format_time(node['end_seconds'])} · {display[node_id]}")
        for child in node["child_ids"]:
            outline(child, indent + 1)

    outline(structure["root_node_id"])
    lines.extend(["", "## Bounded review examples", ""])
    for name, node in select_examples(structure):
        lines.extend([
            f"### {name}: `{node['node_id']}`",
            "",
            f"Range: {format_time(node['start_seconds'])}–{format_time(node['end_seconds'])}; local topics: {', '.join(node['source_topic_ids'])}.",
            "",
            f"Derived display label: {display[node['node_id']]}",
            "",
            "Direct children:",
            "",
        ])
        for child_id in node["child_ids"]:
            child = by_id[child_id]
            lines.append(f"- `{child_id}` · {format_time(child['start_seconds'])}–{format_time(child['end_seconds'])} · {display[child_id]}")
        lines.extend(["", "Leaf evidence excerpts (not generated labels):", ""])
        for topic_id in node["source_topic_ids"]:
            leaf = next(item for item in by_id.values() if item["node_type"] == "local_topic_leaf" and item["source_topic_ids"] == [topic_id])
            excerpt = review_evidence["excerpts"][topic_id]
            lines.append(f"- `{topic_id}` · {format_time(leaf['start_seconds'])}–{format_time(leaf['end_seconds'])} · segments {excerpt['first_segment_id']}–{excerpt['last_segment_id']}: “{excerpt['opening_excerpt']}…”")
        lines.append("")
    lines.extend([
        "## Flat topic baseline",
        "",
        "The comparison baseline is the unchanged 31-topic chronological sequence. It has no parent grouping.",
        "",
        "| # | Topic | Time | Existing derived title |",
        "|---:|---|---|---|",
    ])
    leaves = sorted((item for item in structure["nodes"] if item["node_type"] == "local_topic_leaf"), key=lambda item: item["temporal_order"])
    for leaf in leaves:
        lines.append(f"| {leaf['temporal_order']} | `{leaf['source_topic_ids'][0]}` | {format_time(leaf['start_seconds'])}–{format_time(leaf['end_seconds'])} | {display[leaf['node_id']]} |")
    lines.extend([
        "",
        "## Objective structural summary",
        "",
        f"- Leaves: {metrics['leaf_count']}; TreeSeg parents: {metrics['parent_count']}; hierarchy depth: {metrics['hierarchy_depth']}.",
        f"- Terminal parent groups: {metrics['terminal_parent_count']}; singleton rate: {metrics['singleton_rate']:.1%}.",
        f"- Window-transition edges joined inside terminal groups: {metrics['fragmentation_indicators']['source_window_transition_edges_joined_in_terminal_groups']}/{metrics['fragmentation_indicators']['source_window_transition_edges']}.",
        f"- Temporal order integrity: {'PASS' if metrics['temporal_order_integrity']['valid'] else 'FAIL'}.",
        f"- Determinism: {'PASS' if metrics['determinism']['identical_structure_across_two_runs'] else 'FAIL'} (`{metrics['determinism']['structure_sha256']}`).",
        "",
        "## Review rubric",
        "",
        "Score each question 0 (harmful), 1 (mixed), or 2 (useful), and cite node IDs/time ranges.",
        "",
        "1. Are the parent groups semantically logical?",
        "2. Are adjacent local topics grouped correctly?",
        "3. Do any parents merge clearly different seminar sections?",
        "4. Is the hierarchy depth useful rather than merely complex?",
        "5. Compared with the flat baseline, do parent groups reduce visible 12-minute window artifacts?",
        "6. Can the hierarchy serve as a useful seminar table of contents?",
        "7. Is there excessive fragmentation or over-merge?",
        "",
        "Required Product Owner disposition: `ACCEPT`, `REVISE`, or `REJECT`. Acceptance authorizes only the next evidence step; it does not promote TreeSeg to production or freeze a Topic Engine candidate.",
        "",
    ])
    return "\n".join(lines)


def run_treeseg(entries: list[dict[str, Any]], config: dict[str, Any]) -> tuple[dict[str, Any], float]:
    from treeseg import TreeSeg, ollama_embeddings
    from treeseg.embeddings import Embeddings
    from treeseg import ollama as treeseg_ollama

    embedding = config["embeddings"]
    candidate = config["treeseg"]
    treeseg_config = {
        "MIN_SEGMENT_SIZE": candidate["min_segment_size"],
        "LAMBDA_BALANCE": candidate["lambda_balance"],
        "UTTERANCE_EXPANSION_WIDTH": candidate["utterance_expansion_width"],
        "TEXT_KEY": candidate["text_key"],
        "EMBEDDINGS": Embeddings(
            embeddings_func=ollama_embeddings,
            headers={},
            model=embedding["model"],
            endpoint=embedding["endpoint"],
        ),
    }
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Upstream caches an AsyncClient globally. A second isolated run needs a
    # fresh client because the first run's event loop has been closed.
    treeseg_ollama._global_ollama_client = None
    started = time.perf_counter()
    try:
        segmenter = TreeSeg(configs=treeseg_config, entries=entries)
        if len(getattr(segmenter, "blocks", [])) != len(entries) or any("embedding" not in block for block in segmenter.blocks):
            raise RuntimeError("TreeSeg did not embed every local-topic evidence block")
        segmenter.segment_meeting(K=candidate["requested_max_terminal_groups"])
        structure = tree_to_structure(segmenter.root, entries)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)
    return structure, time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    runtime_pins = verify_runtime_pins(config)
    topics_doc, transcript_doc = load_locked_inputs(args.project_dir, config)
    entries = build_entries(topics_doc, transcript_doc)
    structure_1, runtime_1 = run_treeseg(entries, config)
    structure_2, runtime_2 = run_treeseg(entries, config)
    hash_1, hash_2 = stable_hash(structure_1), stable_hash(structure_2)
    if hash_1 != hash_2:
        raise SystemExit(f"TreeSeg structure is non-deterministic: {hash_1} != {hash_2}")
    metrics = compute_metrics(structure_1, config, runtime_1 + runtime_2)
    metrics["determinism"] = {
        "runs": 2,
        "identical_structure_across_two_runs": True,
        "structure_sha256": hash_1,
        "run_structure_sha256": [hash_1, hash_2],
        "run_runtime_seconds": [round(runtime_1, 6), round(runtime_2, 6)],
    }
    if not metrics["temporal_order_integrity"]["valid"]:
        raise SystemExit("Serialized hierarchy failed temporal integrity validation")
    now = datetime.now(timezone.utc).isoformat()
    structure_1.update(
        {
            "schema_version": 1,
            "artifact": "treeseg_global_seminar_structure_hierarchy",
            "issue": 52,
            "generated_at": now,
            "engine_identity": {
                "engine_id": "treeseg_external_adapt_v1",
                "role_id": "challenger",
                "lifecycle_registry": "governance/topic_engine_lifecycle.json",
                "production_runtime": False,
                "production_promoted": False,
            },
            "dataset_identity": {
                "dataset_id": "A",
                "dataset_role": "DEVELOPMENT_CALIBRATION",
                "input_kind": "accepted_golden_seminar_local_topic_sequence",
            },
            "role": "external_isolated_adapt_challenger_global_structure_only",
            "input_scope": "full_existing_topicized_representation_video_001_day_1",
            "titles_used_for_structure": False,
            "upstream": config["treeseg"],
            "embedding_model": config["embeddings"],
        }
    )
    labels = make_derived_labels(topics_doc, structure_1)
    review_evidence = make_review_evidence(entries)
    flat = make_flat_baseline(topics_doc)
    source_snapshot = {
        "schema_version": 1,
        "generated_at": now,
        "project": "Стресс код",
        "inputs": {
            "topics": {"path": config["input"]["topics_relative_path"], "sha256": config["input"]["expected_topics_sha256"]},
            "transcript": {"path": config["input"]["transcript_relative_path"], "sha256": config["input"]["expected_transcript_sha256"]},
        },
        "counts": {"local_topics": len(entries), "transcript_segments": transcript_doc["segment_count"]},
        "excluded_from_structure_input": ["topic.title", "topic.summary"],
        "runtime_pins_verified": runtime_pins,
    }
    verdict = "TREESEG_HIERARCHY_POC_READY_FOR_PRODUCT_REVIEW"
    metrics.update({"schema_version": 1, "generated_at": now, "issue": 52, "final_technical_verdict": verdict})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "hierarchy.json": structure_1,
        "flat_topic_baseline.json": flat,
        "derived_labels.json": labels,
        "review_evidence_excerpts.json": review_evidence,
        "structural_metrics.json": metrics,
        "source_snapshot.json": source_snapshot,
    }
    for filename, payload in outputs.items():
        (args.output_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "PRODUCT_OWNER_REVIEW_PACKET.md").write_text(render_review_packet(structure_1, labels, review_evidence, metrics), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "metrics": metrics, "outputs": sorted(outputs) + ["PRODUCT_OWNER_REVIEW_PACKET.md"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
