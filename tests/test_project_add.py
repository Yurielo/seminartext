#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "seminartext"


def write_pdf(path: Path, label: str) -> None:
    path.write_bytes(
        (
            "%PDF-1.4\n"
            f"% {label}\n"
            "1 0 obj << /Type /Catalog >> endobj\n"
            "trailer << /Root 1 0 R >>\n"
            "%%EOF\n"
        ).encode("utf-8")
    )


def run_project_add(project: Path, presentation: Path, handout: Path):
    return subprocess.run(
        [
            str(SCRIPT),
            "project-add",
            str(project),
            "--youtube",
            "https://youtu.be/8rB2dbExVpk",
            "--presentation",
            str(presentation),
            "--handout",
            str(handout),
        ],
        text=True,
        capture_output=True,
    )


def load_sources(project: Path) -> dict:
    return json.loads((project / "sources.json").read_text(encoding="utf-8"))


def test_project_add_youtube_presentation_handout_and_idempotency():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        project = root / "Проект И Цзин"
        source_dir = root / "Исходные материалы И Цзин"
        project.mkdir()
        source_dir.mkdir()
        (project / "seminar.yaml").write_text(
            'title: "И Цзин"\nlanguage: ru\n',
            encoding="utf-8",
        )

        presentation = source_dir / "Презентация И Цзин.pdf"
        handout = source_dir / "Протоколы И Цзин compressed.pdf"
        write_pdf(presentation, "presentation")
        write_pdf(handout, "handout")

        first = run_project_add(project, presentation, handout)
        if first.returncode != 0:
            raise AssertionError(first.stderr + first.stdout)

        data = load_sources(project)
        assert data["schema_version"] == 1
        assert len(data["videos"]) == 1
        assert len(data["documents"]) == 2

        assert data["videos"][0] == {
            "source_id": "video_001",
            "order": 1,
            "type": "youtube",
            "url": "https://youtu.be/8rB2dbExVpk",
            "title": "",
        }

        docs = {item["type"]: item for item in data["documents"]}
        assert set(docs) == {"presentation", "handout"}
        assert docs["presentation"]["source_id"] == "doc_001"
        assert docs["presentation"]["file"] == "source/presentations/Презентация И Цзин.pdf"
        assert docs["presentation"]["title"] == "Презентация И Цзин"
        assert docs["handout"]["source_id"] == "doc_002"
        assert docs["handout"]["file"] == "source/handouts/Протоколы И Цзин compressed.pdf"
        assert docs["handout"]["title"] == "Протоколы И Цзин compressed"

        assert (project / docs["presentation"]["file"]).read_bytes() == presentation.read_bytes()
        assert (project / docs["handout"]["file"]).read_bytes() == handout.read_bytes()

        second = run_project_add(project, presentation, handout)
        if second.returncode != 0:
            raise AssertionError(second.stderr + second.stdout)

        after = load_sources(project)
        assert after == data
        assert "[SKIP] YouTube уже зарегистрирован" in second.stdout
        assert "[SKIP] Уже зарегистрирован: source/presentations/Презентация И Цзин.pdf" in second.stdout
        assert "[SKIP] Уже зарегистрирован: source/handouts/Протоколы И Цзин compressed.pdf" in second.stdout


if __name__ == "__main__":
    test_project_add_youtube_presentation_handout_and_idempotency()
    print("project-add regression test passed")
