# Issue #52 — bounded TreeSeg Global Seminar Structure POC

This directory is an isolated, reproducible TreeSeg adaptation for temporal hierarchy only. It does not evaluate boundary detection, alter Topic Engine roles, create a hierarchy Gold, or implement a custom segmentation algorithm.

## Locked input

- Golden Seminar: «Стресс код».
- Full existing topicized representation: all 31 chronological local topics and all 2,155 transcript segments in `video_001` (Day 1).
- Input hashes are locked in `config.json` and verified before every run.
- Days 2–4 have transcripts but no allowed existing local-topic sequence. They are not opened, synthesized, or counted as covered. The hierarchy therefore covers 100% of the available Day 1 representation and 1/4 source files in the Golden Seminar.
- Dataset C is not run; Dataset D Gold is not accessed; Dataset E and Gold Expansion G1/G2 are not used.

Each immutable local-topic range becomes a leaf. Its `composite` TreeSeg input is the concatenated text of the already-referenced transcript segments. `topic.title` and `topic.summary` are explicitly excluded. Existing titles are copied after structure generation into `derived_labels.json` for display only.

## Upstream and configuration

- Repository: <https://github.com/geraldthewes/topic-treeseg>
- Commit: `f18929a23693bdcb669aef1ab1a18fd035e50e57`
- Package version: `0.1.0`
- License: Apache-2.0
- Embeddings: local Ollama `bge-m3:latest`, digest `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`
- TreeSeg: `MIN_SEGMENT_SIZE=2`, `LAMBDA_BALANCE=0`, `UTTERANCE_EXPANSION_WIDTH=2`, `TEXT_KEY=composite`.
- Expansion is requested up to `K=31`; native TreeSeg stops earlier when no node can satisfy its minimum segment size. Native terminal groups are retained, and the existing local topics are attached below them as provenance-bearing leaves.

Local adaptation differences are limited to:

1. explicit event-loop creation for Python 3.14;
2. reset of upstream's process-global Ollama async client between determinism runs because it is bound to the closed prior loop;
3. serialization of the already-built native TreeSeg binary tree;
4. attachment of immutable input topics below native terminal groups;
5. objective metric and review-packet generation.

The adapter does not change TreeSeg loss, split search, split priority, or stopping behavior.

## Reproduction

From the repository root, with Ollama serving the pinned `bge-m3` model:

```bash
python3 -m venv /tmp/seminartext-issue52-venv
/tmp/seminartext-issue52-venv/bin/pip install -r analysis/treeseg_global_structure_poc/requirements.txt
/tmp/seminartext-issue52-venv/bin/python analysis/treeseg_global_structure_poc/run_hierarchy_poc.py
python3 tests/test_treeseg_global_structure_poc.py
```

The runner validates input hashes, installed TreeSeg version/commit, and embedding-model digest. It executes TreeSeg twice and fails rather than publishing output if the structure hashes differ or temporal integrity fails.

## Artifacts and metric definitions

- `hierarchy.json`: structure-only tree, time/order/children, and leaf-to-evidence provenance.
- `derived_labels.json`: display labels, explicitly excluded from structure.
- `review_evidence_excerpts.json`: deterministic transcript excerpts for bounded human review.
- `flat_topic_baseline.json`: unchanged 31-topic comparison sequence.
- `structural_metrics.json`: no F1; counts, depth, duration distributions, singleton, fragmentation, over-merge, coverage, ordering, runtime, and determinism.
- `PRODUCT_OWNER_REVIEW_PACKET.md`: full outline, beginning/middle/end examples, flat comparison, and review rubric.
- `source_snapshot.json`: locked hashes and observed runtime pins.

Fragmentation indicators count terminal groups with at most two leaves, terminal groups under 15 minutes, and 12-minute source-window transitions that remain/cross within terminal parents. Over-merge indicators count terminal parents longer than 60 minutes or broader than six leaves, non-root parents covering over 75% of leaves, and the largest root-child share. These are transparent review indicators, not accuracy scores or acceptance thresholds.
