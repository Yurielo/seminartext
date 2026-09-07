# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **181**
- Topic `REVIEW_CLEAR`: **180**
- Topic `REVIEW_EXCEPTION`: **1**
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
- Topic: `issue_68_video_004_topic_proposal_024h`
- Time: `01:51:40.189` — `02:01:19.486`
- Words: `transcript_revision_video_004_r1:word:009738` — `transcript_revision_video_004_r1:word:010431`
- Current title: **Генетическая линия, предел глубины и ресурсный фокус работы**
- Classification: `REVIEW_EXCEPTION`
- Taxonomy: OVER-MERGE, TRANSITION_SPLIT, PROCEDURAL_CONTENT_MIX
- Confidence: `HIGH`

### Exact problem

The resource-focused discussion ends before a guided brain-gym sequence and pretest recap. The current range combines two distinct semantic functions under one title.

### Exact evidence preview

- Beginning: Мы здесь работаем, смотрите, мы с вами когда проговорили про первое поколение, здесь не очень верно на схеме написано, но вообще. У нас человек, с которым мы работаем, или мы сами, давайте
- Middle: тоже для вас такое замечание. Вот смотрите. Мы даже со своим личным опытом от зачатия до настоящего времени мы вряд ли сможем когда-либо разобраться. На то, чтобы с этими проблемами разобраться, нужно
- End: но сейчас запоминаем. Дальше мы дышим с вами, дальше мы промахиваем с вами меридианы, передний, средний меридиан, задний, средний меридиан. Делали гимнастику для мозга, восстановили свои когнитивные способности и переходим к вопросам.

### Recommended correction

```json
{
  "action": "SPLIT_REALIGN",
  "semantic_part": {
    "end_word_id": "transcript_revision_video_004_r1:word:010253",
    "preserve_title": true,
    "start_word_id": "transcript_revision_video_004_r1:word:009738"
  },
  "separate_semantic_part": {
    "end_word_id": "transcript_revision_video_004_r1:word:010431",
    "proposed_role": "SEMANTIC_TOPIC",
    "start_word_id": "transcript_revision_video_004_r1:word:010254",
    "title": "Гимнастика для мозга и повторение претестов перед вопросами"
  }
}
```

Alternative: Classify the second part as SEMINAR_STRUCTURE only if the guided exercise is intended as navigation rather than reusable content.

### Human decision required

Choose one bounded outcome for this exception. No other exception is presented
until this decision is persisted and the affected neighborhood is rebuilt and
re-QA'd.
