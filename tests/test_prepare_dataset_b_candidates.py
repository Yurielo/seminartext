#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "analysis" / "prepare_dataset_b_candidates.py"
)

spec = importlib.util.spec_from_file_location("prepare_dataset_b", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_segment(sid):
    start = (sid - 1) * 60
    end = sid * 60
    return {
        "id": sid,
        "start": float(start),
        "end": float(end),
        "start_tc": f"00:{start // 60:02d}:00.000",
        "end_tc": f"00:{end // 60:02d}:00.000",
        "text": f"segment {sid}",
    }


def write_project(root):
    project = root / "Independent seminar"
    transcript_dir = project / "transcript" / "video_001"
    transcript_dir.mkdir(parents=True)
    (transcript_dir / ".seminartext_complete").write_text("", encoding="utf-8")
    (transcript_dir / "transcript.srt").write_text("1\n00:00:00,000 --> 00:01:00,000\nx\n", encoding="utf-8")
    (project / "transcript" / "video_001.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_id": "video_001",
                "title": "Independent video",
                "segments": [make_segment(i) for i in range(1, 121)],
            }
        ),
        encoding="utf-8",
    )
    (project / "sources.json").write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "source_id": "video_001",
                        "title": "Independent video",
                        "file": "source/video/video_001_source.mp4",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return project


def test_select_evenly_spaced_is_deterministic():
    assert module.select_evenly_spaced(26, 6) == [0, 5, 10, 15, 20, 25]
    assert module.eligible_window_indices(
        [
            [{"start": 0.0, "end": 601.0}],
            [{"start": 0.0, "end": 599.0}],
        ]
    ) == [0]


def test_build_benchmark_marks_candidates_without_gold(tmp_path):
    project = write_project(tmp_path)
    benchmark = module.build_benchmark(project, "video_001")

    assert benchmark["dataset_id"] == "dataset_b"
    assert benchmark["status"] == "candidate_needs_review"
    assert benchmark["window_count"] == 6
    assert benchmark["selection_policy"]["selected_window_numbers"] == [1, 3, 5, 6, 8, 10]
    assert benchmark["selection_policy"]["eligible_window_count"] == 10

    for case in benchmark["cases"]:
        assert case["review"]["status"] == "needs_review"
        assert case["gold"] == {"boundaries": [], "topics": []}
        assert case["provenance"]["project"] == "Independent seminar"
        assert case["provenance"]["segment_range"] == [
            case["first_segment_id"],
            case["last_segment_id"],
        ]


if __name__ == "__main__":
    test_select_evenly_spaced_is_deterministic()
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_build_benchmark_marks_candidates_without_gold(Path(td))
    print("prepare dataset b tests passed")
