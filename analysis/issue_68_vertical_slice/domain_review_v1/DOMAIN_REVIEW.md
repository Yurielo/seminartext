# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **181**
- Topic `REVIEW_CLEAR`: **178**
- Topic `REVIEW_EXCEPTION`: **3**
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

- Source: `source_video_003`
- Topic: `issue_68_video_003_topic_proposal_051a`
- Time: `02:50:36.490` — `02:55:09.070`
- Words: `transcript_revision_video_003_r1:word:015212` — `transcript_revision_video_003_r1:word:015449`
- Current title: **Выбор участника и темы демонстрационной сессии**
- Classification: `REVIEW_EXCEPTION`
- Taxonomy: NON_SEMANTIC_CONTENT_CONTAMINATION, BOUNDARY_OFFSET
- Confidence: `HIGH`

### Exact problem

The unit opens with an unrelated lunch-break duration announcement before the participant and demonstration-topic selection begins.

### Exact evidence preview

- Beginning: Проведем обеденный перерыв. У нас будет на час. И у нас есть список желающих участвовать. Можно я? Мы тестируем по... То есть как бы не я решаю, а я по тесту проверяю.
- Middle: стресс на обучение. Это подумайте о том, что... Не нужно выбрать, да? Нет. Мы все по тесту. У нас забываем вообще выбрать. Забываем там, я хочу и так далее. У нас есть
- End: Вот. То есть вот это тема у нас будет. Я бы выбрала. Я доверяю своему тестированию. Продолжение следует... Это поменьше выбрали из всех, я понимаю. Это первый признак, что тема под стрессом.

### Recommended correction

```json
{
  "action": "REALIGN_LEFT",
  "exclude_as_nonsemantic": {
    "end_word_id": "transcript_revision_video_003_r1:word:015219",
    "start_word_id": "transcript_revision_video_003_r1:word:015212"
  },
  "preserve_end_word_id": "transcript_revision_video_003_r1:word:015449",
  "start_word_id": "transcript_revision_video_003_r1:word:015220"
}
```

Alternative: Preserve the current range as SEMINAR_STRUCTURE.

### Human decision required

Choose one bounded outcome for this exception. No other exception is presented
until this decision is persisted and the affected neighborhood is rebuilt and
re-QA'd.
