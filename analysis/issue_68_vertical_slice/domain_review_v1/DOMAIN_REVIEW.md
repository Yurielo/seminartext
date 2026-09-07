# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **181**
- Topic `REVIEW_CLEAR`: **179**
- Topic `REVIEW_EXCEPTION`: **2**
- Concept candidates: **18**
- Concept identity exceptions: **7**
- Topic→Concept input links: **254**
- Link exceptions: **63**
- Selective transcript-verification exceptions: **2**
- Coverage gaps / overlaps: **0 / 0**

The full deterministic classification and Day 2–4 semantic maps are stored in
`domain_review_qa.json`. In accordance with the exception-only UX, this human
packet exposes only the first unresolved material exception.

## First material exception

- Source: `source_video_004`
- Topic: `issue_68_video_004_topic_proposal_001c`
- Time: `00:08:46.571` — `00:10:26.178`
- Words: `transcript_revision_video_004_r1:word:000615` — `transcript_revision_video_004_r1:word:000754`
- Current title: **Специфическая, генетическая и неспецифическая рецессия**
- Classification: `REVIEW_EXCEPTION`
- Taxonomy: MALFORMED_TITLE, TRANSCRIPT_UNCERTAINTY
- Confidence: `MEDIUM`

### Exact problem

The title and machine transcript use «рецессия» for a method whose surrounding explanation appears to describe temporal regression. The intended domain term cannot be authoritatively inferred from the machine TranscriptRevision alone.

### Exact evidence preview

- Beginning: И оно звучит так, как время, в которое коррекция пройдет наилучшим образом. То есть мы не знаем, что это за время. Какая же бывает вида специфической рецессии? Это текущее воплощение, то есть
- Middle: опыт, то есть от момента рождения до настоящего времени. Есть специфическая также рецессия, туда относится генетическое прошлое, то есть какой-то конкретный предок. Бабушка по материнской линии, либо дедушка по материнской линии в
- End: подробнее. Итого, мы можем уйти в какое-то конкретное время, либо в время, которое мы даже не знаем, куда мы попадем, которое называется неспецифическая рецессия, или время, в которое коррекция пройдет наилучшим образом.

### Recommended correction

```json
{
  "action": "SELECTIVE_TRANSCRIPT_VERIFICATION_THEN_RENAME_IF_CONFIRMED",
  "candidate_title": "Специфическая, генетическая и неспецифическая регрессия",
  "preserve_word_range": true
}
```

Alternative: Retain «рецессия» with an explicit source-term note if selective verification confirms that wording.

### Human decision required

Choose one bounded outcome for this exception. No other exception is presented
until this decision is persisted and the affected neighborhood is rebuilt and
re-QA'd.
