# Roadmap update — Word Timeline / Alignment Foundation

Date: 2026-08-26

This decision record updates the intended SeminarText 4.x roadmap direction after Dataset C blind validation, Gold Expansion planning, Transcript Segmentation Quality Gate (#29), Dataset E resegmentation prototype (#30), and the architecture review of word-level alignment options.

## Product Owner decision

1. **Word Timeline becomes part of Evidence Foundation.**
2. The canonical architecture target is:

   `media → ASR transcript → word timeline → fine-grained benchmark segments → Gold topic boundaries → Topic Engine`

3. The following entities must remain distinct:
   - ASR words / speech-recognition units;
   - benchmark segments;
   - topics.
4. SRT cue granularity must not be treated as the canonical coordinate system for Topic Engine or Gold.
5. Dataset E resegmentation prototype is accepted at the **text segmentation** level. Its estimated timestamps remain non-source-exact and must be marked as such.
6. Dataset C is closed for parameter/architecture selection after blind validation.
7. Dataset D remains a future LOCKED TEST; current selected D source is `SOURCE QUALITY INSUFFICIENT` and must not be used until source/ASR quality is repaired.
8. Dataset E is DEVELOPMENT and may proceed after word-timestamp/alignment architecture is resolved.
9. Dataset F remains blocked by source-quality/ASR issues until repaired.
10. Local Peak remains the **primary experimental candidate**, not production baseline. PELT remains recall-oriented comparator.

## Evidence Foundation additions

Add a dedicated **Word Timeline / Alignment** subsection under Evidence Foundation.

Required capabilities:

- [ ] source-grounded word-level timestamps;
- [ ] stable word IDs;
- [ ] text + start/end per word/token unit;
- [ ] confidence when available;
- [ ] timing provenance (`source_exact`, `forced_alignment`, `derived_estimate`, or equivalent);
- [ ] source media reference;
- [ ] deterministic mapping from benchmark segments to word ranges;
- [ ] deterministic mapping topic → segments → words → source timestamps;
- [ ] preservation of original transcript text and provenance;
- [ ] support for legacy transcripts via forced alignment where possible;
- [ ] no silent timing fabrication: estimated timestamps must remain explicitly marked estimates.

Preferred canonical artifact direction:

`transcript_words.json`

Conceptual record:

```json
{
  "id": 1523,
  "text": "изменения",
  "start": 853.42,
  "end": 853.91,
  "confidence": 0.94,
  "timing_source": "forced_alignment",
  "source_id": "video_001"
}
```

Exact schema is not frozen yet.

## Alignment technology decision status

Do **not** freeze a production aligner yet.

Candidates for empirical POC/bake-off:

1. `stable-ts` — strongest candidate for aligning existing transcripts to audio and regrouping around existing coarse timestamps;
2. `WhisperX` — reference forced-alignment solution;
3. `whisper.cpp` DTW — minimal-stack candidate because SeminarText already uses whisper.cpp;
4. `MLX Whisper` — strong Apple-Silicon candidate for future ASR that emits word timestamps directly.

`faster-whisper` remains a possible future ASR backend but is not the first-choice solution for aligning already-existing transcripts.

## Immediate next experiment

**Word Alignment Bake-off** on one controlled Russian audio fragment (~10–20 minutes), using the same source and verified text.

Compare at least:

- stable-ts alignment;
- WhisperX forced alignment;
- whisper.cpp DTW;
- optionally MLX Whisper word timestamps as future-ASR comparator.

Do not involve Topic Engine or Gold in this comparison.

Evaluate:

- word/phrase alignment accuracy;
- start/end timing quality;
- unaligned/missing words;
- handling of Russian;
- repetitions/hallucination behavior;
- deterministic reproducibility;
- runtime;
- RAM usage;
- installation/maintenance complexity on Apple Silicon;
- ability to align an already-existing transcript;
- provenance quality.

## Topic Engine state update

Dataset A:
- 6/6 Gold complete;
- 48 Gold topics;
- development/calibration.

Dataset B:
- 6/6 Gold complete;
- 34 Gold topics;
- previous independent frozen validation; now part of development/error-analysis history.

Dataset C:
- 6/6 Gold complete;
- 24 Gold topics;
- blind validation completed;
- Local Peak ±2 F1 = 0.583;
- PELT ±2 F1 = 0.345;
- Local Peak internal F1 excluding automatic window-start boundaries ≈ 0.444;
- Dataset C is no longer available for tuning/architecture selection.

Post-C diagnosis:
- Local Peak main bottleneck = boundary detection, not localization;
- 9/10 Dataset C FN were true detection misses;
- PELT rescued 6/10 Local Peak FN but at severe over-segmentation cost;
- Local Peak = primary experimental candidate;
- PELT = recall-oriented comparator;
- no production baseline declared yet.

## Gold Expansion state update

Strategy:

- Dataset D = LOCKED TEST;
- Dataset E/F = DEVELOPMENT;
- future Gold expansion should intentionally diversify seminar structure and subject matter.

Quality-gate results:

- Dataset D: `SOURCE QUALITY INSUFFICIENT`;
- Dataset E: original source `RESEGMENTATION REQUIRED`, prototype derived segmentation now `READY FOR GOLD` at text-layer level;
- Dataset F: `SOURCE QUALITY INSUFFICIENT`.

Dataset E prototype:
- 189 coarse cues → 704 derived segments;
- median duration 30.77s → 7.869s;
- median words 63 → 17;
- text conservation PASS;
- deterministic byte-identical output PASS;
- timestamps currently derived estimates because source media / word-level timestamps are unavailable.

## Revised near-term sequence

1. Dataset C milestone — DONE / merged.
2. Gold Expansion Strategy — DONE.
3. Transcript Segmentation Quality Gate — DONE.
4. Dataset E topic-agnostic resegmentation prototype — DONE.
5. **Word Alignment Bake-off — NEXT.**
6. Freeze Word Timeline architecture and provenance schema.
7. Integrate selected alignment approach first as experimental Evidence Foundation component.
8. Rebuild/upgrade Dataset E timing from estimates to source-grounded word timing when media is available.
9. Create Gold E only after alignment/timing policy is accepted.
10. Repair/replace source for Dataset D while preserving locked-test firewall.
11. Prepare Dataset F only after ASR/source-quality repair.
12. Expand development Gold beyond A/B/E as needed.
13. Resume next Local Peak architecture experiment using development data only.
14. Freeze next Topic Engine candidate.
15. First blind evaluation on untouched Dataset D.
16. Define formal `TOPIC SEGMENTATION STABLE` acceptance criteria from cross-dataset evidence.
17. Proceed to Global Video Review / Seminar Structure.
18. Obsidian / Knowledge Layer follows after stable topic segmentation and provenance foundation.

## Roadmap wording to deprecate

The roadmap must no longer state:

- Dataset C `CANDIDATES PREPARED / NEEDS MANUAL GOLD`;
- Dataset C as the next independent validation;
- that frozen A/B/C validation is still pending;
- that SRT cue IDs are the implicit long-term canonical segmentation layer;
- that Topic Engine architecture choice should be made before resolving transcript/word-timeline provenance.

## Next action

Create and execute a dedicated **Word Alignment Bake-off** Issue before any further Gold E annotation or Topic Engine tuning.
