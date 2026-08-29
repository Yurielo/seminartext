#!/usr/bin/env python3
"""Prepare independent Dataset B candidate windows without Topic Engine output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from seminartext_modules.dataset_governance import enforce


DEFAULT_PROJECT_NAME = "Заблокированные эмоции"
DEFAULT_SOURCE_ID = "video_001"
WINDOW_SECONDS = 720
MIN_CANDIDATE_SECONDS = 600
CASE_COUNT = 6


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_project(project_arg: str) -> Path:
    project = Path(project_arg).expanduser()
    if project.exists():
        return project

    projects_root = Path.home() / "Documents" / "seminartext_projects"
    return projects_root / project_arg


def make_windows(segments: list[dict], window_seconds: int) -> list[list[dict]]:
    if not segments:
        return []

    windows: list[list[dict]] = []
    current: list[dict] = []
    window_start = float(segments[0]["start"])

    for segment in segments:
        start = float(segment["start"])
        if current and start >= window_start + window_seconds:
            windows.append(current)
            current = []
            window_start = start
        current.append(segment)

    if current:
        windows.append(current)

    return windows


def select_evenly_spaced(total: int, wanted: int) -> list[int]:
    if total < wanted:
        raise ValueError(f"need at least {wanted} windows, found {total}")

    selected: list[int] = []
    for i in range(wanted):
        index = int((i * (total - 1) / (wanted - 1)) + 0.5)
        selected.append(index)

    # The formula above is deterministic; this keeps it robust for small totals.
    selected = sorted(set(selected))
    cursor = 0
    while len(selected) < wanted:
        if cursor not in selected:
            selected.append(cursor)
        cursor += 1
    return sorted(selected)


def eligible_window_indices(windows: list[list[dict]]) -> list[int]:
    indices = []
    for index, window in enumerate(windows):
        duration = float(window[-1]["end"]) - float(window[0]["start"])
        if duration >= MIN_CANDIDATE_SECONDS:
            indices.append(index)
    return indices


def source_metadata(project_dir: Path, source_id: str) -> dict:
    sources_path = project_dir / "sources.json"
    if not sources_path.exists():
        return {}

    sources = load_json(sources_path)
    for video in sources.get("videos", []):
        if video.get("source_id") == source_id:
            return video
    return {}


def segment_payload(segment: dict) -> dict:
    return {
        "id": segment["id"],
        "start": srt_timecode(segment.get("start_tc") or segment["start"]),
        "end": srt_timecode(segment.get("end_tc") or segment["end"]),
        "text": segment["text"],
    }


def srt_timecode(value: object) -> str:
    text = str(value)
    if ":" in text and "." in text and "," not in text:
        return text.replace(".", ",")
    return text


def build_benchmark(project_dir: Path, source_id: str) -> dict:
    transcript_json = project_dir / "transcript" / f"{source_id}.json"
    transcript_srt = project_dir / "transcript" / source_id / "transcript.srt"
    complete_marker = project_dir / "transcript" / source_id / ".seminartext_complete"

    if not transcript_json.exists():
        raise FileNotFoundError(f"missing transcript JSON: {transcript_json}")
    if not transcript_srt.exists():
        raise FileNotFoundError(f"missing transcript SRT: {transcript_srt}")
    if not complete_marker.exists():
        raise FileNotFoundError(f"missing completion marker: {complete_marker}")

    transcript = load_json(transcript_json)
    segments = transcript.get("segments", [])
    windows = make_windows(segments, WINDOW_SECONDS)
    eligible_indices = eligible_window_indices(windows)
    selected_offsets = select_evenly_spaced(len(eligible_indices), CASE_COUNT)
    selected_indices = [eligible_indices[offset] for offset in selected_offsets]
    source = source_metadata(project_dir, source_id)

    cases = []
    for index in selected_indices:
        window_number = index + 1
        window = windows[index]
        first = window[0]
        last = window[-1]
        cases.append(
            {
                "case_id": f"dataset_b_{source_id}_window_{window_number:02d}",
                "dataset_id": "dataset_b",
                "source_id": source_id,
                "window_number": window_number,
                "selection_index": index,
                "start": srt_timecode(first.get("start_tc") or first["start"]),
                "end": srt_timecode(last.get("end_tc") or last["end"]),
                "first_segment_id": first["id"],
                "last_segment_id": last["id"],
                "segment_count": len(window),
                "provenance": {
                    "project": project_dir.name,
                    "project_path": str(project_dir),
                    "source_id": source_id,
                    "source_title": source.get("title", transcript.get("title")),
                    "source_file": source.get("file", transcript.get("source_file")),
                    "source_mirrors": source.get("mirrors", transcript.get("mirrors", [])),
                    "transcript_json": str(transcript_json),
                    "transcript_srt": str(transcript_srt),
                    "segment_range": [first["id"], last["id"]],
                    "timestamp_range": [
                        srt_timecode(first.get("start_tc") or first["start"]),
                        srt_timecode(last.get("end_tc") or last["end"]),
                    ],
                },
                "segments": [segment_payload(segment) for segment in window],
                "gold": {"boundaries": [], "topics": []},
                "review": {
                    "status": "needs_review",
                    "notes": (
                        "Dataset B candidate only. Manual Gold labels must be "
                        "created without using Topic Engine predictions."
                    ),
                },
            }
        )

    return {
        "schema_version": 1,
        "type": "seminartext_topic_benchmark",
        "dataset_id": "dataset_b",
        "dataset_name": "Dataset B",
        "status": "candidate_needs_review",
        "source_id": source_id,
        "window_count": len(cases),
        "selection_policy": {
            "name": "evenly_spaced_transcript_windows",
            "window_seconds": WINDOW_SECONDS,
            "min_candidate_seconds": MIN_CANDIDATE_SECONDS,
            "candidate_count": CASE_COUNT,
            "available_window_count": len(windows),
            "eligible_window_count": len(eligible_indices),
            "selected_window_numbers": [case["window_number"] for case in cases],
            "rule": (
                "Split the completed transcript into sequential 12-minute "
                "windows, keep windows that are at least 10 minutes long, "
                "then select six evenly spaced positions from first eligible "
                "to last eligible. Topic Engine predictions are not read."
            ),
        },
        "provenance": {
            "project": project_dir.name,
            "project_path": str(project_dir),
            "source_id": source_id,
            "transcript_json": str(transcript_json),
            "transcript_srt": str(transcript_srt),
        },
        "cases": cases,
    }


def write_report(benchmark: dict, output: Path) -> None:
    rows = [
        "| Case | Window | Segments | Timestamps | Status |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for case in benchmark["cases"]:
        rows.append(
            "| {case_id} | {window_number} | {first}-{last} | {start}-{end} | {status} |".format(
                case_id=case["case_id"],
                window_number=case["window_number"],
                first=case["first_segment_id"],
                last=case["last_segment_id"],
                start=case["start"],
                end=case["end"],
                status=case["review"]["status"],
            )
        )

    output.write_text(
        "\n".join(
            [
                "# Dataset B Candidate Benchmark Preparation",
                "",
                "Dataset B is prepared from `Заблокированные эмоции`, a seminar separate from Dataset A (`Стресс код`).",
                "",
                "The generated artifact is `analysis/dataset_b/topic_benchmark_dataset_b.json`.",
                "",
                "## Sampling Policy",
                "",
                benchmark["selection_policy"]["rule"],
                "",
                "No Topic Engine predictions, experiment outputs, or automatic boundaries are used to choose or adjust these windows.",
                "",
                "## Candidate Windows",
                "",
                *rows,
                "",
                "## Manual Gold Review Workflow",
                "",
                "1. Open each candidate case in the JSON artifact and read only its transcript segments.",
                "2. Mark true semantic topic starts as segment IDs in `gold.boundaries`.",
                "3. Add one `gold.topics` entry per boundary with `start_id`, `title`, and optional `summary`.",
                "4. Keep `review.status` as `needs_review` until both boundaries and topics are checked by a human reviewer.",
                "5. Change `review.status` to `gold_complete` only after the reviewer confirms the labels were created without viewing Topic Engine predictions.",
                "6. Confirm all six cases are `gold_complete`; only then run the frozen Dataset B validation configs.",
                "",
                "## Guardrails",
                "",
                "- Dataset A benchmark data is not modified.",
                "- Production Topic Engine logic is not modified.",
                "- Dataset B Gold labels are not fabricated or auto-generated.",
                "- No parameter tuning is performed on Dataset B before frozen validation.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare Dataset B candidate benchmark windows."
    )
    parser.add_argument("--project", default=DEFAULT_PROJECT_NAME)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/dataset_b/topic_benchmark_dataset_b.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("analysis/DATASET_B_PREPARATION.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    enforce("benchmark_init", dataset_id="B")
    project_dir = resolve_project(args.project)
    if not project_dir.exists():
        raise SystemExit(f"project not found: {project_dir}")

    benchmark = build_benchmark(project_dir, args.source_id)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(benchmark, args.report)

    print("DATASET B CANDIDATES PREPARED")
    print(f"Project: {benchmark['provenance']['project']}")
    print(f"Source: {benchmark['source_id']}")
    print(f"Windows: {benchmark['selection_policy']['selected_window_numbers']}")
    print(f"JSON: {args.output}")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
