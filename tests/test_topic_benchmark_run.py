#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "seminartext"


def write_fake_engine(path):
    path.write_text(
        """DETAIL = {
    "auto": {
        "min_sec": 60,
        "hard_min_sec": 25,
        "target_per_hour": "test",
    }
}
WINDOW_SEC = 720


def analyze_window_boundaries(window, detail="auto", model="fake"):
    import json
    import os

    first_id = str(window[0]["id"])
    predictions = json.loads(os.environ["PREDICTIONS"])
    return predictions.get(first_id, [])
""",
        encoding="utf-8",
    )


def make_case(case_id, first, last, boundaries, status="gold_complete"):
    segments = [
        {
            "id": i,
            "start": f"00:00:{i:02d},000",
            "end": f"00:00:{i + 1:02d},000",
            "text": f"segment {i}",
        }
        for i in range(first, last + 1)
    ]
    return {
        "case_id": case_id,
        "source_id": "video_001",
        "window_number": 1,
        "start": segments[0]["start"],
        "end": segments[-1]["end"],
        "first_segment_id": first,
        "last_segment_id": last,
        "segments": segments,
        "gold": {
            "boundaries": boundaries,
            "topics": [
                {"start_id": sid, "title": f"Topic {sid}", "summary": ""}
                for sid in boundaries
            ],
        },
        "review": {"status": status, "notes": ""},
    }


def write_project(root, cases):
    project = root / "Bench"
    bench_dir = project / "analysis" / "benchmark"
    bench_dir.mkdir(parents=True)
    (bench_dir / "topic_benchmark.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "seminartext_topic_benchmark",
                "source_id": "video_001",
                "window_count": len(cases),
                "cases": cases,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return project


def run_benchmark(root, engine, predictions, *args, expect_ok=True):
    env = os.environ.copy()
    env.update(
        {
            "SEMINARTEXT_PROJECTS": str(root),
            "SEMINARTEXT_TOPICS_MODULE": str(engine),
            "SEMINARTEXT_PYTHON": sys.executable,
            "PREDICTIONS": json.dumps(predictions),
        }
    )
    proc = subprocess.run(
        [str(SCRIPT), "project-topic-benchmark-run", "Bench", *args],
        text=True,
        capture_output=True,
        env=env,
    )
    if expect_ok and proc.returncode != 0:
        raise AssertionError(proc.stderr + proc.stdout)
    if not expect_ok and proc.returncode == 0:
        raise AssertionError("expected failure")
    return proc


def latest_result(project):
    return json.loads(
        (project / "analysis" / "benchmark" / "results" / "topic_benchmark_run.json")
        .read_text(encoding="utf-8")
    )


def test_metrics_and_tolerance():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        engine = root / "fake_topics.py"
        write_fake_engine(engine)
        project = write_project(
            root,
            [
                make_case("case_a", 1, 10, [1, 4, 8]),
                make_case("case_b", 20, 30, [20, 25]),
            ],
        )

        run_benchmark(
            root,
            engine,
            {"1": [1, 3, 4, 9], "20": [20]},
            "--tolerance",
            "0",
        )
        data = latest_result(project)
        assert data["aggregate_metrics"]["true_positives"] == 3
        assert data["aggregate_metrics"]["false_positives"] == 2
        assert data["aggregate_metrics"]["false_negatives"] == 2

        run_benchmark(
            root,
            engine,
            {"1": [1, 3, 4, 9], "20": [20]},
            "--tolerance",
            "1",
        )
        data = latest_result(project)
        assert data["aggregate_metrics"]["true_positives"] == 4
        assert data["cases"][0]["false_positives"] == [3]
        assert data["cases"][0]["false_negatives"] == []


def test_only_and_empty_prediction_error():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        engine = root / "fake_topics.py"
        write_fake_engine(engine)
        write_project(
            root,
            [
                make_case("case_a", 1, 10, [1, 4]),
                make_case("case_b", 20, 30, [20, 25]),
            ],
        )

        run_benchmark(
            root,
            engine,
            {"20": [20, 25]},
            "--only",
            "case_b",
        )

        proc = run_benchmark(
            root,
            engine,
            {"1": []},
            "--only",
            "case_a",
            expect_ok=False,
        )
        assert "пустой prediction" in proc.stderr


def test_perfect_match():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        engine = root / "fake_topics.py"
        write_fake_engine(engine)
        project = write_project(
            root,
            [
                make_case("case_a", 1, 10, [1, 4, 8]),
                make_case("case_b", 20, 30, [20, 25]),
            ],
        )

        run_benchmark(
            root,
            engine,
            {"1": [1, 4, 8], "20": [20, 25]},
            "--tolerance",
            "0",
        )
        data = latest_result(project)
        aggregate = data["aggregate_metrics"]
        assert aggregate["true_positives"] == 5
        assert aggregate["false_positives"] == 0
        assert aggregate["false_negatives"] == 0
        assert aggregate["boundary_precision"] == 1.0
        assert aggregate["boundary_recall"] == 1.0
        assert aggregate["boundary_f1"] == 1.0
        assert all(case["f1"] == 1.0 for case in data["cases"])


def test_bad_benchmark_and_incomplete_case_errors():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        engine = root / "fake_topics.py"
        write_fake_engine(engine)
        project = root / "Bench"
        bench_dir = project / "analysis" / "benchmark"
        bench_dir.mkdir(parents=True)
        (bench_dir / "topic_benchmark.json").write_text("{bad", encoding="utf-8")

        proc = run_benchmark(root, engine, {}, expect_ok=False)
        assert "JSON повреждён" in proc.stderr

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        engine = root / "fake_topics.py"
        write_fake_engine(engine)
        case = make_case("case_a", 1, 5, [1])
        case["segments"] = []
        write_project(root, [case])

        proc = run_benchmark(root, engine, {"1": [1]}, expect_ok=False)
        assert "нет transcript segments" in proc.stderr


def test_missing_benchmark_file_error():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        engine = root / "fake_topics.py"
        write_fake_engine(engine)
        (root / "Bench" / "analysis" / "benchmark").mkdir(parents=True)

        proc = run_benchmark(root, engine, {}, expect_ok=False)
        assert "benchmark не найден" in proc.stderr


if __name__ == "__main__":
    test_metrics_and_tolerance()
    test_only_and_empty_prediction_error()
    test_perfect_match()
    test_bad_benchmark_and_incomplete_case_errors()
    test_missing_benchmark_file_error()
    print("topic benchmark runner tests passed")
