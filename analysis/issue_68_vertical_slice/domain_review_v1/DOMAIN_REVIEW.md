# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **181**
- Topic `REVIEW_CLEAR`: **177**
- Topic `REVIEW_EXCEPTION`: **4**
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

- Source: `source_video_002`
- Topic: `issue_68_video_002_topic_proposal_020a`
- Time: `01:20:18.736` — `01:21:11.830`
- Words: `transcript_revision_video_002_r1:word:007504` — `transcript_revision_video_002_r1:word:007588`
- Current title: **Перерыв и задание: классификация входящей, внутренней и производимой энергии**
- Classification: `REVIEW_EXCEPTION`
- Taxonomy: NON_SEMANTIC_CONTENT_CONTAMINATION, DISCOURSE_FUNCTION_BOUNDARY_MISSED
- Confidence: `HIGH`

### Exact problem

The semantic assignment is wrapped by two scheduling fragments: the break announcement at the left and the return-time announcement at the right. Treating the whole range as one knowledge Topic mixes seminar organization with the energy-classification task.

### Exact evidence preview

- Beginning: И давайте сделаем с вами небольшой перерыв на 10 минут, то есть у нас 10.20, 10.30 мы с вами встречаемся и продолжим. И пока подумайте на такие вопросы, я оставлю этот слайд
- Middle: такие вопросы, я оставлю этот слайд здесь, чтобы работал. Вот есть энергия, которая в нас входит, которую мы принимаем, энергия, которая внутри нас, которая существует, и энергия, которую мы производим. Подготовьте свои
- End: которую мы производим. Подготовьте свои варианты ответа на эти, даже не ответы, а варианты, что мы можем сделать. Мы можем в табличку вот эту вписать. Через 10 минут, 10.30 по Москве включаемся.

### Recommended correction

```json
{
  "action": "SPLIT_REALIGN",
  "exclude_as_nonsemantic": [
    {
      "end_word_id": "transcript_revision_video_002_r1:word:007525",
      "reason": "break scheduling",
      "start_word_id": "transcript_revision_video_002_r1:word:007504"
    },
    {
      "end_word_id": "transcript_revision_video_002_r1:word:007588",
      "reason": "return-time scheduling",
      "start_word_id": "transcript_revision_video_002_r1:word:007582"
    }
  ],
  "semantic_part": {
    "end_word_id": "transcript_revision_video_002_r1:word:007581",
    "start_word_id": "transcript_revision_video_002_r1:word:007526",
    "title": "Задание: классификация входящей, внутренней и производимой энергии"
  }
}
```

Alternative: Preserve the full range only as SEMINAR_STRUCTURE rather than as a knowledge Topic.

### Human decision required

Choose one bounded outcome for this exception. No other exception is presented
until this decision is persisted and the affected neighborhood is rebuilt and
re-QA'd.
