# Selected Whisper Timing v1

Issue #131 adds an optional output contract for consumers that need native
Whisper token timing from the exact attempt selected by SeminarText.

## Invocation

```bash
seminartext transcribe media.mp4 --language ru --structured-timing
seminartext transcribe media.mp4 --language en --structured-timing
```

The flag adds JSON-full output to each Whisper attempt already performed by the
normal reliability pipeline. It never starts a separate timing pass or forced
alignment.

## Package

Standalone transcripts publish `structured_timingN/`; project transcripts
publish `structured_timing/`. Each directory contains:

- `manifest.json`, validated by
  `schemas/selected_whisper_timing_v1.schema.json`;
- `parts/part_NNNN.txt`;
- `parts/part_NNNN.srt`;
- `parts/part_NNNN.json`.

The three files for a part are copied together only after the existing
quality/retry logic selects that attempt as canonical. A rejected initial JSON
is not published when a retry wins.

The manifest binds source and model hashes, language, mode, chunk order,
absolute media ranges, selected attempt kind, and SHA-256 identities of the
published TXT/SRT/JSON-full artifacts. Consumers shift local JSON-full timing by
`absolute_offset_seconds`; they do not infer token timing from SRT.

Without `--structured-timing`, the existing package and Whisper flags remain
unchanged.
