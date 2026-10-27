#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "seminartext"


YTDLP_HELP = """\
Usage: yt-dlp [OPTIONS] URL
    --cookies-from-browser BROWSER[+KEYRING][:PROFILE][::CONTAINER]
    --extractor-args IE_KEY:ARGS
    --http-chunk-size SIZE
    -4, --force-ipv4
"""


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def make_project(root: Path) -> Path:
    project = root / "project"
    project.mkdir()
    (project / "sources.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "videos": [
                    {
                        "source_id": "video_001",
                        "order": 1,
                        "type": "youtube",
                        "url": "https://youtu.be/8rB2dbExVpk",
                        "title": "И Цзин",
                    }
                ],
                "documents": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return project


def base_env(root: Path, bin_dir: Path) -> dict:
    model = root / "model.bin"
    vad = root / "vad.bin"
    model.write_text("model", encoding="utf-8")
    vad.write_text("vad", encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env.get("PATH", ""),
            "SEMINARTEXT_MODEL": str(model),
            "SEMINARTEXT_VAD_MODEL": str(vad),
            "MOCK_WHISPER_LOG": str(root / "whisper.log"),
        }
    )
    return env


def install_common_mocks(bin_dir: Path) -> None:
    write_executable(
        bin_dir / "ffprobe",
        "#!/bin/bash\nexit 0\n",
    )
    write_executable(
        bin_dir / "ffmpeg",
        """#!/bin/bash
set -euo pipefail
out="${@: -1}"
if [[ "$out" == *chunk_%04d.wav ]]; then
  mkdir -p "$(dirname "$out")"
  : > "${out/chunk_%04d.wav/chunk_0000.wav}"
else
  mkdir -p "$(dirname "$out")"
  : > "$out"
fi
""",
    )
    write_executable(
        bin_dir / "whisper-cli",
        """#!/bin/bash
set -euo pipefail
if [[ -n "${MOCK_WHISPER_LOG:-}" ]]; then printf '%s\\n' "$*" >> "$MOCK_WHISPER_LOG"; fi
prefix=""
while (($#)); do
  if [[ "$1" == "-of" ]]; then
    prefix="$2"
    break
  fi
  shift
done
mkdir -p "$(dirname "$prefix")"
cat > "$prefix.txt" <<'TXT'
Это тестовая расшифровка успешного пути YouTube. Она достаточно длинная.
TXT
cat > "$prefix.srt" <<'SRT'
1
00:00:00,000 --> 00:00:01,000
Это тестовая расшифровка успешного пути YouTube.

SRT
""",
    )


def run_project_transcribe(project: Path, env: dict):
    return subprocess.run(
        [str(SCRIPT), "project-transcribe", str(project), "--only", "video_001"],
        text=True,
        capture_output=True,
        env=env,
    )


def test_failed_youtube_download_keeps_original_error_and_no_completion_marker():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_common_mocks(bin_dir)
        write_executable(
            bin_dir / "yt-dlp",
            f"""#!/bin/bash
set -euo pipefail
if [[ "${{1:-}}" == "--help" ]]; then
  cat <<'HELP'
{YTDLP_HELP}
HELP
  exit 0
fi
echo "ERROR: unable to download video data: HTTP Error 403: Forbidden" >&2
exit 1
""",
        )

        project = make_project(root)
        result = run_project_transcribe(project, base_env(root, bin_dir))
        output = result.stdout + result.stderr

        assert result.returncode != 0
        assert "HTTP Error 403: Forbidden" in output
        assert "yt-dlp не смог скачать" in output
        assert "unbound variable" not in output
        transcript_dir = project / "transcript" / "video_001"
        assert not (transcript_dir / ".seminartext_complete").exists()
        assert not (transcript_dir / "transcript.srt").exists()
        assert not (project / "transcript" / "video_001.json").exists()


def test_successful_youtube_project_transcribe_with_cookie_config():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        install_common_mocks(bin_dir)
        args_log = root / "yt_dlp_args.log"
        write_executable(
            bin_dir / "yt-dlp",
            f"""#!/bin/bash
set -euo pipefail
if [[ "${{1:-}}" == "--help" ]]; then
  cat <<'HELP'
{YTDLP_HELP}
HELP
  exit 0
fi
printf '%s\\n' "$*" >> "{args_log}"
out=""
while (($#)); do
  if [[ "$1" == "-o" ]]; then
    out="$2"
    break
  fi
  shift
done
out="${{out//%(ext)s/m4a}}"
mkdir -p "$(dirname "$out")"
printf 'audio' > "$out"
exit 0
""",
        )

        project = make_project(root)
        env = base_env(root, bin_dir)
        env["SEMINARTEXT_YTDLP_COOKIES_FROM_BROWSER"] = "chrome"
        result = run_project_transcribe(project, env)
        output = result.stdout + result.stderr

        if result.returncode != 0:
            raise AssertionError(output)

        transcript_dir = project / "transcript" / "video_001"
        assert (transcript_dir / ".seminartext_complete").exists()
        assert (transcript_dir / "transcript.srt").exists()
        assert not any(transcript_dir.glob(".youtube_source.*"))
        assert "--cookies-from-browser chrome" in args_log.read_text(encoding="utf-8")

        video_json = json.loads((project / "transcript" / "video_001.json").read_text(encoding="utf-8"))
        assert video_json["source_id"] == "video_001"
        assert video_json["segment_count"] == 1
        calls_before_reuse = len((root / "whisper.log").read_text(encoding="utf-8").splitlines())
        reused = run_project_transcribe(project, env)
        assert reused.returncode == 0, reused.stdout + reused.stderr
        assert "Переиспользую проверенную расшифровку" in reused.stdout
        assert len((root / "whisper.log").read_text(encoding="utf-8").splitlines()) == calls_before_reuse


if __name__ == "__main__":
    test_failed_youtube_download_keeps_original_error_and_no_completion_marker()
    test_successful_youtube_project_transcribe_with_cookie_config()
    print("project-transcribe YouTube regression tests passed")
