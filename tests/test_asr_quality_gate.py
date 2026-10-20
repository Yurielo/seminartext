#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "seminartext"

FUZZY_LOOP = """\
В начале лекции мы обсудим исходные данные и порядок расчёта.
И с чего начать хотелось? С того, что самые большие ценности в нашей жизни не материальные.
И с чего же начать хотелось? С того, что самые большие ценности в нашей жизни вовсе не материальные.
И с чего начать мне хотелось? С того, что самые большие ценности в нашей жизни обычно не материальные.
И всё-таки с чего начать хотелось? С того, что самые большие ценности в нашей жизни не бывают материальными.
Затем лектор переходит к следующему разделу и показывает таблицу.
"""

GOOD_TRANSCRIPT = """\
В начале лекции мы посмотрим презентацию и уточним исходные данные.
Средняя продолжительность жизни мужчин составляет примерно семьдесят один год.
Для женщин тот же показатель ближе к семьдесят шести годам.
После этого мы сравним пульс и физическую нагрузку для разных групп.
"""

SHORT_PERIODIC_LOOP = "Вопросы и ответы на вопросы и ответы на вопросы"

MEANINGFUL_REPETITION = """\
Здоровье важнее материальных вещей, потому что оно определяет качество нашей жизни.
Повторю эту мысль иначе: без здоровья трудно пользоваться тем, что мы накопили.
Ещё один важный аспект — время жизни, которое нельзя вернуть или купить.
Итак, я снова говорю о здоровье, но теперь связываю его с нашими ежедневными привычками.
Финальное повторение нужно для вывода: здоровье даёт нам возможность использовать время осмысленно.
"""

# Minimal excerpt from production transcript SHA-256
# 35a0d2a0abf44f9e676c8892d8c4cb15657744e55fcf4e35b43dc3113ff148cf.
# The project owner verified against the source audio that this is an ASR loop.
ID06_CONFIRMED_LOOP = """\
И с чего начать хотелось? С того, что у нас самые большие ценности в нашей жизни, они, во-первых, не материальные, не деньги, не что-то, а здоровье, время жизни и время как таковое.
И с чего начать хотелось? С того, что у нас самые большие ценности в нашей жизни, они, во-первых, не материальные, не деньги, не здоровье, не карате, а здоровье, и с чего начать хотелось? С того, что у нас самые большие ценности в нашей жизни, они, во-первых, не материальные, не карате, а здоровье, время жизни и время как таковое.
И с чего начать хотелось? С того, что у нас самые большие ценности в нашей жизни, они, во-первых, не материальные, не карате, а здоровье, время жизни и время как таковое.
И решил я посчитать, произвести вот такие расчеты.
"""

# Minimal excerpt from production transcript SHA-256
# afdfa063aa00ddb8ab6145ae4b9981501566974d44e5835c372eb1b2788b7432.
# The project owner verified against the source audio that this is normal
# developing speech with an intentionally repeated enumerative structure.
ID22_CONFIRMED_STRUCTURED_SPEECH = """\
Третье по значимости степень моего существования. Первое – это проживать жизнь, познавать мир во всем его разнообразии, понимать чувство прекрасного и всего мироустройства, получать свои инсайты, свободу и всеобщую проявленность любви во всех аспектах.
Второе – это проживать жизнь, познавать мир во всем его разнообразии, понимать чувство прекрасного и всего мироустройства, получать свои инсайты, свободу и всеобщую проявленность любви во всех аспектах.
Третье по значимости степень моего существования. Первое – это проживать жизнь, познавать мир во всем его разнообразии, понимать чувство прекрасного и всего мироустройства, получать свои инсайты, свободу и всеобщую проявленность любви во всем его разнообразии.
Четвертое по значимости степень моего существования. Первое – это проживать жизнь, познавать мир во всем его разнообразии, понимать чувство прекрасного и всего мироустройства, получать свои инсайты, свободу и всеобщую проявленность любви во всем его разнообразии.
"""


def quality_check_program() -> str:
    source = CLI.read_text(encoding="utf-8")
    match = re.search(
        r"quality_check\(\) \{\n  python3 - \"\$1\" <<'PYCHECK'\n(.*?)\nPYCHECK\n\}",
        source,
        re.DOTALL,
    )
    assert match, "quality_check heredoc not found in production CLI"
    return match.group(1)


def run_quality_check(tmp_path: Path, text: str) -> subprocess.CompletedProcess:
    transcript = tmp_path / "transcript.txt"
    transcript.write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-", str(transcript)],
        input=quality_check_program(),
        text=True,
        capture_output=True,
        check=False,
    )


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def test_fuzzy_contextual_loop_is_rejected(tmp_path):
    result = run_quality_check(tmp_path, FUZZY_LOOP)
    assert result.returncode == 1
    assert "fuzzy_contextual_repetition" in result.stderr


def test_short_periodic_token_loop_is_rejected(tmp_path):
    result = run_quality_check(tmp_path, SHORT_PERIODIC_LOOP)
    assert result.returncode == 1
    assert "short_periodic_token_loop" in result.stderr


def test_confirmed_production_loop_is_rejected(tmp_path):
    result = run_quality_check(tmp_path, ID06_CONFIRMED_LOOP)
    assert result.returncode == 1
    assert "fuzzy_contextual_repetition" in result.stderr


def test_confirmed_enumerative_production_speech_passes(tmp_path):
    assert run_quality_check(tmp_path, ID22_CONFIRMED_STRUCTURED_SPEECH).returncode == 0


def test_normal_transcript_passes(tmp_path):
    assert run_quality_check(tmp_path, GOOD_TRANSCRIPT).returncode == 0


def test_meaningful_repetition_without_local_verbatim_context_passes(tmp_path):
    assert run_quality_check(tmp_path, MEANINGFUL_REPETITION).returncode == 0


def test_existing_exact_loop_is_still_rejected(tmp_path):
    exact_loop = " ".join(["Да, это так."] * 14)
    assert run_quality_check(tmp_path, exact_loop).returncode == 1


def test_normal_workflow_uses_existing_protective_retry_for_fuzzy_loop(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    args_log = tmp_path / "whisper_args.log"
    bad_text = tmp_path / "bad.txt"
    good_text = tmp_path / "good.txt"
    bad_text.write_text(FUZZY_LOOP, encoding="utf-8")
    good_text.write_text(GOOD_TRANSCRIPT, encoding="utf-8")

    write_executable(bin_dir / "ffprobe", "#!/bin/bash\nexit 0\n")
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
        f"""#!/bin/bash
set -euo pipefail
printf '%s\\n' "$*" >> "{args_log}"
prefix=""
has_prompt=0
while (($#)); do
  [[ "$1" == "--prompt" ]] && has_prompt=1
  if [[ "$1" == "-of" ]]; then
    prefix="$2"
    break
  fi
  shift
done
mkdir -p "$(dirname "$prefix")"
if ((has_prompt)); then
  cp "{bad_text}" "$prefix.txt"
else
  cp "{good_text}" "$prefix.txt"
fi
cat > "$prefix.srt" <<'SRT'
1
00:00:00,000 --> 00:00:10,000
Тестовый фрагмент.

SRT
""",
    )

    source = tmp_path / "lecture.mp4"
    source.write_bytes(b"video")
    model = tmp_path / "model.bin"
    vad = tmp_path / "vad.bin"
    model.write_bytes(b"model")
    vad.write_bytes(b"vad")
    output_root = tmp_path / "output"
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "SEMINARTEXT_MODEL": str(model),
            "SEMINARTEXT_VAD_MODEL": str(vad),
            "SEMINARTEXT_OUTPUT": str(output_root),
        }
    )

    result = subprocess.run(
        [str(CLI), "transcribe", str(source)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    result_dir = output_root / "lecture"
    log = (result_dir / "transcription.log").read_text(encoding="utf-8")
    calls = args_log.read_text(encoding="utf-8").splitlines()
    raw = next(result_dir.glob("transcript[0-9]*.txt")).read_text(encoding="utf-8")

    assert len(calls) == 2
    assert "--prompt" in calls[0]
    assert "--prompt" not in calls[1]
    assert "-vt 0.55" in calls[0] and "-vsd 550" in calls[0]
    assert "-vt 0.68" in calls[1] and "-vsd 350" in calls[1]
    assert "fuzzy_contextual_repetition" in log
    assert "Обнаружено возможное зацикливание" in log
    assert "Повторная расшифровка фрагмента успешна" in log
    assert "семьдесят один год" in raw
    assert "И с чего начать хотелось" not in raw
