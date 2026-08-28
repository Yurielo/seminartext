# TreeSeg Global Seminar Structure POC — Issue #52

Status: **READY FOR SEPARATE PRODUCT OWNER REVIEW**

Final technical verdict: `TREESEG_HIERARCHY_POC_READY_FOR_PRODUCT_REVIEW`

## Scope and separation

This bounded POC tests TreeSeg only as a temporal hierarchy component over the existing Golden Seminar local-topic sequence. It does not provide Boundary Detection evidence. Boundary roles remain unchanged:

- Local Peak — primary experimental Boundary candidate;
- PELT — recall-oriented comparator;
- TreeSeg — isolated external `ADAPT` challenger;
- no candidate is promoted or frozen.

No production Topic Engine code changed. Dataset C was not run and remains `CLOSED/FROZEN`; Dataset D remains unopened `LOCKED TEST`; Dataset E remains `EXCLUDED`; Gold A/B/C is unchanged; Gold Expansion G1/G2 was not used.

## Input and method

The only complete existing chronological local-topic representation available for «Стресс код» is Day 1 (`video_001`): 31 semi-automatic local topics covering all 2,155 transcript segments from `00:00:06.170` through `04:32:33.420`. The POC locks both source hashes. It does not invent topics for Days 2–4, so it covers 100% of the topicized Day 1 representation but 1/4 source files in the Golden Seminar.

Each existing local-topic range is an immutable leaf. TreeSeg embeds only the concatenated transcript evidence inside that range; existing LLM titles and summaries are excluded. TreeSeg's native recursive binary split and native `MIN_SEGMENT_SIZE=2` stopping rule create all parent groups. The adapter only serializes that tree and attaches evidence-bearing input leaves. Human-readable titles are copied into a separate derived layer after the structural result exists.

Upstream pin:

- source: <https://github.com/geraldthewes/topic-treeseg>;
- commit: `f18929a23693bdcb669aef1ab1a18fd035e50e57`;
- package: `topic_treeseg==0.1.0`;
- license: Apache-2.0;
- embeddings: Ollama `bge-m3:latest`, digest `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`;
- config: `MIN_SEGMENT_SIZE=2`, `LAMBDA_BALANCE=0`, `UTTERANCE_EXPANSION_WIDTH=2`, evidence text key `composite`.

The exact configuration, local compatibility differences, reproduction command, and artifact contract are documented in `analysis/treeseg_global_structure_poc/README.md`.

## Objective structural results

No hierarchy Gold exists. No hierarchy precision, recall, or F1 was created.

| Measure | Result |
|---|---:|
| Existing local-topic leaves | 31 |
| TreeSeg parent groups | 23 |
| Parent counts at depths 0–6 | 1 / 2 / 4 / 4 / 4 / 6 / 2 |
| Maximum hierarchy depth, including local leaves | 7 |
| Native terminal parent groups | 12 |
| Terminal leaves per group, min / median / max | 2 / 3 / 3 |
| Terminal duration, min / median / max | 323.43 / 1,348.89 / 2,172.65 s |
| Singleton rate | 0% |
| Terminal groups under 15 minutes | 2 / 12 |
| Terminal groups over 60 minutes | 0 / 12 |
| Terminal groups broader than 6 leaves | 0 / 12 |
| Source-window transitions joined inside terminal groups | 13 / 21 |
| Temporal order / coverage integrity | PASS, 0 violations |
| Determinism | PASS, identical structure in 2 runs |
| Stable structure SHA-256 | `edde504ac2f73e85e165c85e5a2fa223cc6a9cdcb28f2c3ab31d2aabf40f8f1f` |
| Two-run wall runtime | 27.890806 s |

## Structural findings

1. TreeSeg created a complete, ordered, provenance-preserving hierarchy without gaps, overlaps, inversions, or singleton terminal groups.
2. Terminal grouping crosses 13 of 21 inferred transitions between the original 12-minute source windows. This is an objective sign that the hierarchy is not simply repeating every window edge; whether those crossings are semantically better remains a human decision.
3. Terminal parents are bounded to 2–3 local topics and none exceeds 60 minutes or six leaves. Two very short terminal groups remain, including topics 23–25 at about 5.4 minutes, so fragmentation is still visible.
4. The upper hierarchy is strongly unbalanced: the root divides 25 versus 6 leaves (largest child share `0.806452`), and one non-root parent covers more than 75% of all leaves. Depth 7 may be useful navigation or unnecessary binary-tree complexity; structural metrics cannot decide that.
5. Only Day 1 has an allowed existing full local-topic sequence. The POC cannot support a claim about multi-day seminar structure until separately authorized topic inputs exist for Days 2–4.

These findings justify a Product Owner review packet, not a production decision.

## Product Owner decision required

Use `analysis/treeseg_global_structure_poc/PRODUCT_OWNER_REVIEW_PACKET.md`. It contains the full hierarchy, flat 31-topic baseline, bounded beginning/middle/end groups with transcript evidence excerpts, and a scored rubric.

The Product Owner must decide:

1. whether parent groups are semantically coherent;
2. whether adjacent topics are combined correctly;
3. whether distinct seminar sections are incorrectly merged;
4. whether depth 7 is useful rather than structural noise;
5. whether grouping across window transitions reduces visible window artifacts;
6. whether the result is a useful seminar table of contents;
7. whether the short groups or 25/6 top-level split show unacceptable fragmentation or over-merge.

Required disposition: `ACCEPT`, `REVISE`, or `REJECT`. Until that separate review, TreeSeg stays isolated/non-production and the Topic Engine candidate remains unfrozen.
