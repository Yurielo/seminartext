#!/usr/bin/env python3
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "analysis" / "treeseg_global_structure_poc" / "run_hierarchy_poc.py"
spec = importlib.util.spec_from_file_location("treeseg_global_structure_poc", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FakeNode:
    def __init__(self, identifier, segment, left=None, right=None):
        self.identifier = identifier
        self.segment = segment
        self.left = left
        self.right = right


def sample_entries():
    return [
        {"topic_id": f"topic_{i + 1:04d}", "start_seconds": i * 10.0, "end_seconds": (i + 1) * 10.0, "first_segment_id": i + 1, "last_segment_id": i + 1}
        for i in range(4)
    ]


def sample_tree():
    return FakeNode("*", [0, 1, 2, 3], FakeNode("*L", [0, 1]), FakeNode("*R", [2, 3]))


def test_serializer_attaches_local_topics_below_native_terminal_groups():
    structure = module.tree_to_structure(sample_tree(), sample_entries())
    nodes = {item["node_id"]: item for item in structure["nodes"]}
    assert structure["root_node_id"] == "group_root"
    assert nodes["group_root"]["child_ids"] == ["group_L", "group_R"]
    assert nodes["group_L"]["child_ids"] == ["leaf_topic_0001", "leaf_topic_0002"]
    assert nodes["leaf_topic_0004"]["provenance"]["last_evidence_id"] == "video_001:segment:000004"


def test_temporal_integrity_detects_valid_and_broken_child_ranges():
    structure = module.tree_to_structure(sample_tree(), sample_entries())
    assert module.validate_temporal_integrity(structure)["valid"] is True
    nodes = {item["node_id"]: item for item in structure["nodes"]}
    nodes["group_root"]["child_ids"].reverse()
    result = module.validate_temporal_integrity(structure)
    assert result["valid"] is False
    assert any("order inversion" in item for item in result["violations"])


def test_metrics_are_structural_and_do_not_create_f1():
    structure = module.tree_to_structure(sample_tree(), sample_entries())
    config = {"metrics": {"source_window_seconds": 20.0, "fragment_short_duration_seconds": 15.0, "overmerge_long_duration_seconds": 35.0, "overmerge_broad_leaf_count": 3}}
    metrics = module.compute_metrics(structure, config, runtime_seconds=0.5)
    assert metrics["leaf_count"] == 4
    assert metrics["parent_count"] == 3
    assert metrics["hierarchy_depth"] == 2
    assert metrics["singleton_rate"] == 0.0
    assert metrics["temporal_order_integrity"]["valid"] is True
    assert all("f1" not in key.lower() for key in metrics)


def test_stable_hash_ignores_dictionary_key_order():
    assert module.stable_hash({"b": 2, "a": 1}) == module.stable_hash({"a": 1, "b": 2})


if __name__ == "__main__":
    test_serializer_attaches_local_topics_below_native_terminal_groups()
    test_temporal_integrity_detects_valid_and_broken_child_ranges()
    test_metrics_are_structural_and_do_not_create_f1()
    test_stable_hash_ignores_dictionary_key_order()
    print("TreeSeg Global Structure POC tests passed")
