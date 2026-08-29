# Issue #62 — TreeSeg Product Review preparation

## Status and scope

This is an evidence packet for `DOMAIN_REVIEW`, not a Product Owner decision. It uses only the committed Issue #52/PR #55 artifacts:

- `analysis/treeseg_global_structure_poc/hierarchy.json`
- `analysis/treeseg_global_structure_poc/derived_labels.json`
- `analysis/treeseg_global_structure_poc/review_evidence_excerpts.json`
- `analysis/treeseg_global_structure_poc/structural_metrics.json`
- `analysis/treeseg_global_structure_poc/flat_topic_baseline.json`
- `analysis/treeseg_global_structure_poc/PRODUCT_OWNER_REVIEW_PACKET.md`

No TreeSeg run, algorithm change, Dataset D access, Gold authoring, prediction, or benchmark was performed. The structure is a temporal binary hierarchy over the existing 31 Day-1 local topics. Titles in `derived_labels.json` are a display layer and were not TreeSeg inputs.

Coverage is 31/31 local topics and 100% of `video_001`, but only 1/4 Golden Seminar source files (25%). Days 2–4 have no permitted local-topic sequence and are not represented.

## Evidence inventory

`hierarchy.json` reports 23 parent nodes, 31 leaves, 12 terminal parent groups, depth 7, zero singleton groups, valid temporal order, and identical structure hashes across two runs. The flat comparison has the same 31 chronological leaves and no parents. All intervals below are source intervals from the committed artifacts; segment ranges are from `review_evidence_excerpts.json`.

## Findings by review question

### 1–3. Relatedness, false joins, and fragmentation

| Finding | Node(s) and source interval | Evidence-based observation |
|---|---|---|
| `GOOD_GROUPING` | `group_RL`, topics `0026–0028`, 03:38:49.89–03:56:32.31; segments 1814–1850 | `topic_0026` introduces bringing client/self to normotonicity and the muscle test; `topic_0027` discusses test accuracy; `topic_0028` explains binary strong/weak response and starts the demonstration video. The sequence is a coherent “test introduction → rationale → demonstration” candidate. |
| `GOOD_GROUPING` | `group_LRRRLL`, topics `0019–0020`, 02:58:14.75–03:13:34.30; segments 1485–1605 | `topic_0019` selects the anger/correction state and trajectory; `topic_0020` explains eye-movement desensitisation and applies it to the correction. This is one contiguous correction workflow. |
| `GOOD_GROUPING` | `group_LRRRLR`, topics `0021–0022`, 03:13:34.30–03:33:26.46; segments 1606–1764 | `topic_0021` guides a concrete positive clinic image; `topic_0022` elicits the participant’s resulting awareness and closes the demonstration. The two leaves form a plausible “guided exercise → reflection” unit. |
| `QUESTIONABLE_GROUPING` | `group_LLR`, topics `0004–0006`, 00:12:11.31–00:48:19.64; segments 105–367 | `topic_0004` is a participant biography/motivation, `topic_0005` discusses awareness obstacles, and `topic_0006` is a recovery case. They are adjacent but not one stable section concept. |
| `QUESTIONABLE_GROUPING` | `group_LRLR`, topics `0011–0013`, 01:36:37.80–02:12:50.45; segments 758–1072 | `topic_0011` surveys techniques/programmes, `topic_0012` contains a generic personal story and transition, and `topic_0013` discusses emotional balancing. The middle leaf is weak semantic glue. |
| `QUESTIONABLE_GROUPING` | `group_LRRL`, topics `0014–0018`, 02:12:50.45–02:58:14.75; segments 1073–1484 | Protocol overview/setup (`0014–0015`), test instruction (`0016`), a physician/team/guardian-angel story (`0017`), and a “body level—calm” definition (`0018`) are joined into one five-topic parent. |
| `BAD_OR_MISLEADING_GROUPING` | `group_LLL`, topics `0001–0003`, 00:00:06.17–00:12:11.31; segments 1–104 | Lecturer greeting (`001`), participant introduction (`002`), and participant expectations/another introduction (`003`) are administrative opening material, not a single user-facing topic. The derived label “введение … → обзор спикера” should not be presented as a section title. |
| `BAD_OR_MISLEADING_GROUPING` | `group_LRRR`, topics `0019–0025`, 02:58:14.75–03:38:49.89; segments 1485–1813 | A specific correction, imagery, reflection, break/Q&A, and transition into testing are represented by one parent. The first/last label hides the internal change of activity. |
| `BAD_OR_MISLEADING_GROUPING` | `group_L`, topics `0001–0025`, 00:00:06.17–03:38:49.89; segments 1–1813 | A 3h39m container covers introductions, history, techniques, correction, and the hand-off to testing. It is useful as a structural ancestor but not as a seminar section. |
| `BAD_OR_MISLEADING_GROUPING` | `group_root`, topics `0001–0031`, 00:00:06.17–04:32:33.42; segments 1–2155 | The root label is formed from the first and last leaf (“введение … → Вы можете …”), so it is a tree container, not a meaningful seminar chapter. |

There is no singleton fragmentation (0%); however, the 12 terminal groups are mostly only 2–3 leaves (median 3), so the absence of singletons does not by itself establish semantic quality.

### 4–7. Parent usefulness, depth, and navigation

- `group_R` (topics `0026–0031`, 03:38:49.89–04:32:33.42) is a useful *candidate* parent for a “muscle testing” section, because all six leaves concern normality, test mechanics, demonstration, and application. It still requires a human title; the generated ending from `topic_0031` is not suitable.
- `group_LR` (topics `0007–0025`, 00:48:19.64–03:38:49.89) is a useful chronology container (“history/techniques → testing”) but too broad for a navigation section.
- The path is technically traversable through `child_ids` and leaf provenance: e.g. `group_R → group_RL → leaf_topic_0028` resolves to `video_001` segments 1838–1850. Human navigation is only partial because parent IDs are opaque and many labels are first/last transcript fragments.
- Depth is asymmetric: leaves `0026–0031` occur at depth 3, while leaves `0019–0022` occur at depth 7. A user reaching `topic_0019` would traverse seven parent/leaf levels for a 15-minute local sequence, whereas `topic_0026` is reached in three. This is complexity from the binary structure, not demonstrated product value.

### 8–9. Human naming and misleading nodes

High-priority `PARENT_REQUIRES_RENAME` candidates (11) are: `group_root`, `group_L`, `group_LL`, `group_LLL`, `group_LLR`, `group_LR`, `group_LRL`, `group_LRLR`, `group_LRR`, `group_LRRR`, and `group_RR`. Their labels either concatenate transcript fragments, span multiple activities, or end in a conversational utterance. `group_R` and `group_RL` are more plausible candidates but still need Product Owner naming approval.

### 10–11. TreeSeg versus Local Peak and recurring topics

TreeSeg adds 23 temporal parent candidates and preserves leaf-to-evidence links; the Local Peak comparison is a flat 31-topic sequence. This can make a contiguous seminar outline possible and joins 13 of 21 measured 12-minute transition edges inside terminal groups. It does not provide a semantic accuracy score (no hierarchy Gold exists), canonical names, cross-day coverage, or deduplication.

The recurring-topic problem is **not solved**. Testing is introduced in `topic_0015` (protocol/test setup), discussed in `topic_0016`, resumed at the transition `topic_0025`, and then occupies `topic_0026–0031` (02:24:53–04:32:33). Correction/anger material recurs across `topic_0013–0015` and `topic_0019–0022`. The tree keeps these chronological occurrences in separate contiguous branches; it does not create a cross-reference or merge non-adjacent occurrences.

### 12. Day-1 limitation

The evidence covers only `video_001` (`topic_0001–0031`, 00:00:06.17–04:32:33.42). The locked source snapshot records four Golden Seminar files but only 1/4 source-file coverage. Therefore no conclusion about hierarchy consistency across the seminar, repeated sections on Days 2–4, or cross-file navigation is warranted.

## Product disposition packet (options only; no Codex choice)

| Option | Benefits | Risks | Further work / POC expansion | 4.0 MVP and integration cost | Effect on frozen Local Peak |
|---|---|---|---|---|---|
| `ADOPT` | Immediate hierarchical outline and evidence drill-down for the reviewed Day-1 slice. | False joins and opaque labels could mislead users; depth is inconsistent. | Human naming, collapse rules, and review of all parent nodes; extend to Days 2–4 before broad claim. | Medium integration cost; MVP would gain a navigation layer but needs explicit UX safeguards. | None; Local Peak remains the frozen Dataset-D candidate. |
| `ADAPT FURTHER` | Addresses depth asymmetry, naming, and recurring-topic cross-links before adoption. | More design and validation effort; no acceptance yet. | Define depth/parent policy, human review rubric, cross-reference model, and run a bounded multi-day extension. | High cost; likely outside the current 4.0 MVP critical path. | None; TreeSeg remains a challenger. |
| `KEEP AS CHALLENGER` | Preserves a reproducible alternative with low product risk and useful research evidence. | No TreeSeg navigation benefit in MVP. | Retain artifacts and revisit after broader evidence or a hierarchy Gold. | Low integration cost; no MVP behavior change. | None. |
| `REJECT` | Avoids misleading hierarchy and maintenance burden. | Loses the parent-structure experiment and its potential navigation value. | Document rejection rationale; keep immutable artifacts for traceability. | Low implementation cost; flat/Local Peak path remains. | None; frozen Local Peak is unchanged. |

Product Owner must select one option. This packet does not select, promote, or reject TreeSeg.

## Product Owner decision recorded

`ISSUE_62_DECISION: KEEP_TREESEG_AS_CHALLENGER`.

The selected lifecycle record remains `treeseg_external_adapt_v1` with `role_id: challenger`. TreeSeg is not production-ready, not a frozen candidate, and is not authorized for expansion or a new experiment. The Product Owner rationale is the evidence summary above: 3 good groupings, 3 questionable groupings, 4 misleading groupings, 11 parent rename candidates, depth 7 with unnecessary levels, Day-1-only coverage, and unresolved recurring-topic handling. The frozen `bge_m3_local_peak_v1` candidate is unchanged.

## Requirement → evidence self-check matrix

| Issue #62 requirement | Evidence / result |
|---|---|
| Related, questionable, and misleading groupings | 3 `GOOD_GROUPING`, 3 `QUESTIONABLE_GROUPING`, and 4 `BAD_OR_MISLEADING_GROUPING` rows with node IDs, topic IDs, intervals, and excerpt segment ranges above. |
| Excessive or non-meaningful depth | Four explicit depth findings: `group_LRLLL`, `group_LRLLR`, `group_LRRRLL`, `group_LRRRLR`; structural metric depth is 7 and leaves are unevenly placed at depths 3–7. |
| Parent naming and navigation | 11 high-priority rename candidates are listed with rationale; provenance path example `group_R → group_RL → leaf_topic_0028` resolves to `video_001` segments 1838–1850. |
| TreeSeg vs Local Peak | Flat baseline has 31 leaves/no parents; TreeSeg adds 23 temporal parents but no accuracy Gold, deduplication, or cross-day coverage. |
| Recurring-topic handling | Explicit negative finding: testing spans `topic_0015`, `0016`, `0025`, `0026–0031`; correction/anger recurs in `0013–0015` and `0019–0022`; no cross-reference is created. |
| Day-1 limitation | `source_snapshot.json`/metrics: 31 topics, `video_001` only, 1/4 source files (25%); Days 2–4 not represented. |
| Product options without Codex selection | ADOPT, ADAPT FURTHER, KEEP AS CHALLENGER, and REJECT table; the recorded decision is the Product Owner decision, not a Codex choice. |
| Safety constraints | No new run, experiment, Gold, prediction, benchmark, Dataset D/C/E operation, model, dependency, or algorithm change. |

## Technical gate and restrictions

Baseline verification on `main` at `df972b2a02ac6b581d290b515725e3ede208cdf7` passed as expected: G1–G4/G8 PASS, G5/G6 NOT_IMPLEMENTED, G7 known WARN (`141 passed, 2 skipped`), and PROJECT_INTEGRITY PARTIAL. Dataset D remains BLOCKED and blind run authorization is NO. No Dataset D/C/E operation, Gold, prediction, benchmark, model, dependency, or algorithm mutation was performed.

`HUMAN_GATE: DOMAIN_REVIEW` is required. `SAFE_TO_COMPLETE_#62: NO`; `SAFE_TO_START_#63: NO`.
