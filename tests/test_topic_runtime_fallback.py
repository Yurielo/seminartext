from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "seminartext_modules/seminartext_topics.py"
SPEC = importlib.util.spec_from_file_location("seminartext_topics_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
TOPICS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOPICS)


def test_label_fallback_records_window_start_without_unbound_name(tmp_path, monkeypatch):
    source = tmp_path / "transcript.srt"
    source.write_text("fixture\n", encoding="utf-8")
    items = [
        {"id": 1, "start": "00:00:00,000", "end": "00:00:01,000", "text": "Первый блок"},
        {"id": 2, "start": "00:31:00,000", "end": "00:31:01,000", "text": "Второй блок"},
    ]

    monkeypatch.setattr(TOPICS, "find_transcript", lambda root, source: source)
    monkeypatch.setattr(TOPICS, "parse_srt", lambda path: items)
    monkeypatch.setattr(TOPICS, "make_windows", lambda parsed: [[items[0]], [items[1]]])
    monkeypatch.setattr(TOPICS, "analyze_window_boundaries", lambda window, **kwargs: [window[0]["id"]])

    def reject_label(*args, **kwargs):
        raise ValueError("плохой title")

    monkeypatch.setattr(TOPICS, "run_ollama_topic_label", reject_label)
    monkeypatch.setattr(TOPICS, "make_topics", lambda parsed, rows: rows)
    monkeypatch.setattr(
        TOPICS,
        "write_outputs",
        lambda *args, **kwargs: (tmp_path / "topics.txt", tmp_path / "topics.md", tmp_path / "topics.json"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["seminartext_topics.py", str(source), "--root", str(tmp_path)],
    )

    TOPICS.main()

    qa = json.loads((tmp_path / "topics_qa.json").read_text(encoding="utf-8"))
    assert [window["start_segment_id"] for window in qa["windows"]] == [1, 2]
    assert [window["status"] for window in qa["windows"]] == ["fallback", "fallback"]
    candidates = json.loads((tmp_path / "topics_candidates.json").read_text(encoding="utf-8"))
    assert [candidate["start_id"] for candidate in candidates] == [1, 2]
