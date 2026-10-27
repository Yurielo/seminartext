# Issue #147 — project ASR completion identity

Baseline `origin/main`: `f133cf2f615aa8afd4dfa1aaeebc5953cabc5884` (2026-10-27). Unified rules were read at Integra main `86e0801963e85e8d8b121c569fe624bb64ede5df`, SHA-256 `8b8e31c7620d45e1e14429e07e7b97b2adc118745ce781a55b932213c55b646b`.

## Reproduced cause

`process_record` returned immediately when `.seminartext_complete` existed. A deterministic one-source project with an unchanged path, size and mtime but changed media bytes, plus a deleted SRT, returned `Пропущено (уже готово)` and left the SRT missing. The marker held no source, configuration or selected artifact identity.

## Repair

A versioned `.seminartext_completion.json` is published only after project JSON and all required selected artifacts exist. Compatibility checks exact source bytes and source-manifest projection; language; effective model, VAD, Whisper runtime and producer hashes; mode, chunk size, threads and ASR parameters; selected timing manifest, ordered parts, attempt names and TXT/SRT/JSON hashes; and clear transcript, review and project JSON hashes. Unknown legacy identity is readable but never a compatible hit. Missing/tampered derived clear/review/JSON is rebuilt from authoritative raw/SRT evidence without Whisper. Missing/tampered recognized or timing evidence invokes ASR again. A source digest check prevents publication if media changes during ASR. Prior project artifacts are backed up before replacement and restored after a failed attempt. No global cache, ASR model, Topic Engine or translation change.

## Verification

Bounded deterministic fixture reproduced the baseline defect. Focused regression tests: 44 passed before the final rollback/source-integrity additions. A full pre-commit suite returned 417 passed and two deploy tests blocked by expected dirty Git state; they require rerun after commit. Existing selected timing tests cover RU/EN, initial/retry selections and truthful multi-part ranges. Grouped-input, combined-clear, native activation and rollback tests are in the full suite. No real media or inference was used; the Issue requires it only when necessary, and deterministic fixtures cover this defect.

Applicable active Product Rules: PR-008, PR-011, PR-012, PR-013, PR-014. No conflict identified. This change does not promote an Owner Candidate or deploy a runtime.
