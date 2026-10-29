# Issue #131 acceptance evidence

## Scope

The optional `--structured-timing` path publishes JSON-full timing from the
same Whisper attempt selected by the existing SeminarText quality/retry flow.
It does not invoke WhisperX, forced alignment, or a second timing pass.

## Deterministic acceptance

Command:

```bash
python -m pytest -q -rs -p no:cacheprovider \
  tests/test_selected_whisper_timing.py \
  tests/test_transcribe_language.py \
  tests/test_asr_quality_gate.py
```

Result: `15 passed`.

Covered behavior:

- RU and EN request JSON-full in the existing Whisper execution;
- successful initial attempts publish matching TXT/SRT/JSON;
- a quality-rejected initial attempt is replaced by a matching retry trio;
- rejected JSON is absent from the durable package;
- multipart order and absolute offsets are stable;
- published artifact SHA-256 values validate;
- canonical timing survives `.parts` and `.chunks` cleanup;
- without the opt-in flag, no JSON-full output or timing package is created.

## Real English acceptance

Source:

`/Users/yurielokhin/Downloads/Telegram/AQPRra1CgRyBtarCwXqyLLEkhopDGQ4p0rIfQJR_GQaOzJ4gelwsj6bARp_UWbj1DrXrxGOmy7.mp4`

Source SHA-256:

`f53460e353437873e34f404b841134def1ffbbae6f719f3e618adb159ad84ecc`

Invocation used the normal SeminarText CLI with `--language en
--structured-timing`. The retained local evidence package is outside Git at:

`/Users/yurielokhin/Documents/Codex/seminartext-issue131-evidence/real-en-run-1/`

Observed result:

- one media part;
- selected attempt: `initial`;
- one JSON output event from the same Whisper execution;
- 10 JSON-full transcription segments;
- 170 token records;
- manifest and all selected artifact hashes validated;
- manifest passed `selected_whisper_timing_v1.schema.json`;
- `.parts` and `.chunks` were absent after completion;
- the JSON-full source text retained:
  `because they save a lot of energy. The LED`.

Real manifest SHA-256:

`9f3a27fb50785d6069eb9029cd0fff1e0e7d6785b3b1c629fa5974967a19f220`

The real run proves same-pass structured timing for the accepted English path.
Retry selection is proven deterministically because intentionally triggering a
real ASR failure would not be stable acceptance evidence.
