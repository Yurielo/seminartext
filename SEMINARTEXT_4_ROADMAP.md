# SeminarText 4.x Roadmap

Последнее обновление: 2026-08-26

## Главная цель

Развить SeminarText из системы транскрипции и обработки семинаров в систему построения, развития и обслуживания единой авторской базы знаний.

Архитектурный принцип: **Evidence-First Parallel Development**.

```text
Sources
  ↓
Canonical Evidence Layer
  ├── Track A: Semantic Automation
  │     Word Timeline → benchmark segments → Boundary Engine
  │     → Topic Draft → Seminar Structure
  │
  └── Track B: Knowledge Product
        Evidence → verified/manual/semi-auto Topics
        → Concepts → Relations → Obsidian Knowledge Prototype

Tracks converge into:
Verified Knowledge Layer
  ↓
Cross-Seminar Knowledge
  ↓
Learning / Marketing / Site / Media / Knowledge Assistant
```

`TOPIC SEGMENTATION STABLE` больше не блокирует Knowledge/Obsidian MVP. Track B
может использовать verified manual, Gold или semi-automatic topics, пока Track A
улучшает автоматизацию параллельно. Topic Engine остаётся критическим компонентом
масштабирования и не отменяется.

Accepted decision record:

`decisions/0002-evidence-first-parallel-development.md`

Roadmap/State consistency checkpoint: `evidence_first_parallel_v1`.

## ADOPT → ADAPT → BUILD

Перед существенной custom-разработкой выполняется bounded survey внешних решений.
Каждый жизнеспособный вариант классифицируется как `ADOPT`, `ADAPT`, `REJECT` или
`BUILD`. Правило особенно важно для alignment, diarization, semantic
segmentation/topic modeling, retrieval/RAG, Obsidian integration и graph
technology.

Enterprise-scale architecture не переносится в local-first SeminarText без
доказанной необходимости.

## Разделение ответственности слоёв

- **Boundary Detection** находит локальные semantic transitions.
- **Seminar Structure** строит hierarchy, merge и recurrence локальных topics на
  уровне полного семинара.
- **Knowledge Engine** выделяет concepts и relations внутри и между
  topics/seminars.

Эти задачи связаны provenance, но не являются одним алгоритмом или одним quality
gate.

---

# 0. Operating Model / Human Gates

Статус: ACTIVE

Принцип:

Do not minimize Yuri's participation. Minimize Yuri's participation in
operations where his expertise is not needed.

Роли, GitHub source-of-truth, стандартный execution loop и human-gate
classification описаны в `DEVELOPMENT_WORKFLOW.md`.

Human-gate classification for Issues:

- `AUTO` — Codex и automated QA могут работать без Yuri;
- `DOMAIN_REVIEW` — Yuri проверяет подготовленные evidence/options;
- `DOMAIN_AUTHORING` — Yuri должен предоставить authoritative semantic content;
- `LOCAL_ACTION` — Yuri выполняет local/UI/account action, недоступное tools.

Default: `AUTO`. Escalation только при явном обосновании.

Decision record:

`decisions/0001-operating-model-and-human-gates.md`

---

# 1. Canonical Evidence Layer / Evidence Foundation

Статус: DONE / IN PROGRESS

## Проектная структура

- [x] Структура SeminarText 4.0
- [x] Проектный формат
- [x] Поддержка нескольких источников
- [x] Видео
- [x] YouTube
- [x] Презентации
- [x] Раздаточные материалы
- [x] Прочие документы
- [x] sources.json
- [x] project-check
- [x] project-transcribe
- [x] --only
- [x] --dry-run

## Результаты транскрипции

- [x] transcript
- [x] transcript_clean
- [x] transcript_review
- [x] SRT
- [x] DOCX

Canonical machine-readable data является первичным representation. TXT, SRT,
DOCX и будущие Markdown views должны постепенно стать exports/views canonical
data, а не конкурирующими источниками истины.

## Evidence / Provenance

Все производные данные должны сохранять связь с исходником.

Необходимо поддерживать:

- [x] project_id
- [x] source_id для video/document и других source kinds
- [x] stable word/segment/topic/evidence IDs
- [x] source и transcript revision provenance
- [x] временной диапазон без fake timing
- [x] номер страницы документа
- [x] номер слайда
- [x] character/image locators
- [x] возможность перейти от canonical entity к исходному evidence

Canonical evidence schema должна быть speaker-ready: `speaker_id` включается как
optional/nullable field с первого schema contract. Реализация diarization сейчас
не требуется.

## Word Timeline / Alignment

Статус: CANONICAL EVIDENCE SCHEMA V1 ACCEPTED / WORD TIMELINE MVP NEXT

Canonical architecture:

`media → ASR transcript → word timeline → fine-grained benchmark segments → Gold topic boundaries → Topic Engine`

Не смешивать три разных уровня:

- **ASR words / speech-recognition units** — распознанные token/word units с
  текстом и timing;
- **benchmark segments** — детерминированные группы word units для размещения
  Gold boundaries;
- **topics** — смысловые интервалы, определяемые Gold или Topic Engine поверх
  benchmark segments.

SRT cue granularity остаётся полезным input/provenance, но не является
долгосрочной canonical coordinate system для Gold или Topic Engine.

Необходимо поддерживать:

- [x] source-grounded word timing contract;
- [x] stable word IDs;
- [x] original text/character span + nullable start/end для каждого word unit;
- [x] nullable confidence;
- [x] timing provenance (`source_exact`, `forced_alignment`,
  `derived_estimate` или equivalent);
- [x] source media mapping;
- [x] deterministic segment → word-range mapping;
- [x] topic → segment → word → source locator provenance;
- [x] сохранение original transcript text и revision provenance;
- [x] forced-alignment provenance contract для legacy transcripts;
- [x] явную маркировку estimated и unavailable timing.

Принятый canonical artifact:

`seminartext.canonical_evidence` JSON bundle schema v1.0.0

Schema зафиксирована в `schemas/canonical_evidence_v1.schema.json`, cross-record
invariants — в `schemas/validate_canonical_evidence_v1.py`, rationale — в
`analysis/CANONICAL_EVIDENCE_SCHEMA_V1.md`, решение — в ADR 0004. TXT, SRT, DOCX
и Markdown остаются только derived views.

### Word Alignment technology status

Final Controlled Word Alignment Decision завершён verdict
`WORD ALIGNMENT TECHNOLOGY SELECTED`.

Выбран `WhisperX 3.8.6` в alignment-only role:

`existing verified transcript + source audio -> native word intervals`

Reference configuration использует isolated Python 3.13 CPU worker и Russian
alignment model `jonatasgrosman/wav2vec2-large-xlsr-53-russian`. WhisperX ASR не
запускается; verified transcript остаётся semantic source of truth.

Canonical adapter обязан:

- сохранять original text/character spans и stable word IDs;
- сохранять source, transcript, aligner, model и configuration provenance;
- хранить native start/end/score только для успешно aligned words;
- явно помечать unsupported words как `unaligned` без synthetic timing;
- сохранять coarse cue bounds только как provenance, не word interval;
- выставлять QA flags для unaligned, long и low-confidence intervals.

Candidate classification:

- `WhisperX` — `ADOPT`;
- `stable-ts` — `REJECT`: 188 zero-duration words, встроенная bounded
  normalization не исправила их, upstream archived;
- `whisper.cpp large-v3 DTW` — `REJECT` для existing-transcript alignment:
  fresh ASR с WER 19.456%, experimental point anchors и zero durations;
- `MLX Whisper` — `NOT APPLICABLE`: релевантный existing-transcript alignment
  path отсутствует.

Evidence и ограничения зафиксированы в
`analysis/FINAL_CONTROLLED_WORD_ALIGNMENT_DECISION_2026-08-27.md` и ADR
`decisions/0003-whisperx-word-alignment.md`.

Canonical Evidence Schema v1 завершена verdict
`CANONICAL_EVIDENCE_SCHEMA_V1_ACCEPTED`. Немедленный следующий milestone:
**Word Timeline MVP on one controlled source**. Production integration в schema
milestone не выполнялась. Golden Seminar Knowledge Slice остаётся разрешённой
parallel preparation при auditable evidence и без выдачи estimated timing за
source-exact. Gold E не планируется: Dataset E исключён из Topic Engine evidence
решением Product Owner в Issue #34.

## 1.1 Минимальный Canonical Evidence contract для vertical slice

Минимальные entities:

- `Seminar`;
- `Source`;
- `Topic`;
- `Concept`;
- `Evidence`.

Минимальные свойства: stable ID, entity type, source link/provenance, lifecycle
status и typed source locator (time/page/slide/character/image range). Полная
canonical transcript schema v1 принята архитектурно; production population
начинается только в Word Timeline MVP.

Тестовый реальный проект:

Стресс код

Видео:
- video_001
- video_002
- video_003
- video_004

---

# 2. Track A — Semantic Automation / Boundary Detection

Статус: ACTIVE PARALLEL SCALABILITY TRACK

Цель:

Автоматически определять локальные смысловые границы и формировать Topic Draft,
который затем может использовать Seminar Structure. Этот Track отвечает за
масштабирование и продолжает Gold/benchmark работу, но не блокирует bounded
Knowledge Product prototype.

---

## 2.1 Gold Topic Benchmark — Dataset A

Проект:

Стресс код / video_001

Файл:

analysis/benchmark/topic_benchmark.json

Статус:

- [x] benchmark создан
- [x] video_001_window_01
- [x] video_001_window_04
- [x] video_001_window_08
- [x] video_001_window_12
- [x] video_001_window_17
- [x] video_001_window_22
- [x] integrity check
- [x] GOLD COMPLETE: 6/6

Gold topics:

- window_01 — 7
- window_04 — 8
- window_08 — 9
- window_12 — 9
- window_17 — 9
- window_22 — 6

Всего:

48 gold topics

Плотность gold:

- min: 30.2 тем/час
- max: 44.8 тем/час
- average: 39.8 тем/час

---

## 2.2 LLM Boundary Engine — baseline

Используется:

gemma3:4b

Вывод:

LLM-only boundary detection оказался нестабильным.

Обнаруженные проблемы:

- position bias к началу окна;
- выбор последовательных SRT ID;
- over-segmentation;
- under-segmentation после жёсткой фильтрации;
- refinement может создавать ложные соседние границы;
- prompt tuning не решает проблему устойчиво.

Решение:

- [x] оставить LLM boundary engine как baseline;
- [ ] не использовать его как основной production boundary engine без новых доказательств качества.

LLM планируется использовать преимущественно для:

- названий тем;
- summary;
- локальной semantic validation;
- Knowledge Engine.

---

## 2.3 Embedding Boundary Engine

Основной перспективный путь.

Компоненты:

- Ollama
- bge-m3
- embedding size: 1024
- ruptures 1.1.9
- semantic change-point detection

Установлено:

- [x] bge-m3
- [x] ruptures

---

## 2.4 Embedding experiments

### Простое left/right cosine comparison

Результат:

- часть gold boundaries хорошо видна;
- отдельных semantic-change peaks недостаточно;
- использовать только как дополнительный feature.

### BGE-M3 + Binseg

Лучший размер embedding-блока:

15 sec

При известном количестве тем:

- Exact F1: 0.143
- ±2 ID F1: 0.738
- ±5 ID F1: 0.833
- Mean nearest ΔID: 2.00

Вывод:

BGE-M3 + change-point detection существенно перспективнее LLM-only boundary detection.

### BGE-M3 + Pelt

Автоматическое количество тем.

Лучший найденный penalty:

0.5

Результат:

- mean ±2 F1: 0.657
- mean topic-count error: 1.67

### Candidate-count scorer

Использовано:

- candidate segmentation через Binseg;
- cohesion;
- separation;
- density prior.

Результат:

- mean ±2 F1: 0.694
- mean topic-count error: 1.67

Проблема:

scorer систематически предпочитает максимально разрешённое количество тем.

Причина:

cohesion и separation естественно растут при дополнительном дроблении.

Решение:

не продолжать подгонку коэффициентов на Dataset A.

---

## 2.5 Dataset B — historical frozen validation

Статус: DONE

Независимый Gold Dataset создан из другого семинара:

Заблокированные эмоции / video_001

Результат:

- [x] Dataset B candidate windows prepared;
- [x] manual Gold labels recorded;
- [x] GOLD COMPLETE: 6/6;
- [x] total Gold topics: 34;
- [x] frozen validation run for baseline, sliding, bge-m3 local peak, and bge-m3 + ruptures.Pelt.

Report:

`analysis/DATASET_B_FROZEN_VALIDATION.md`

Dataset A:

Стресс код
→ development / calibration

6/6 Gold complete, 48 Gold topics.

Dataset B:

Заблокированные эмоции
→ historical frozen validation; development / error-analysis source

6/6 Gold complete, 34 Gold topics.

Dataset C:

И Цзин
→ blind validation complete; closed for tuning / architecture selection

---

## 2.6 Dataset C — blind validation milestone

Статус: DONE / CLOSED FOR TUNING AND ARCHITECTURE SELECTION

Dataset C:

- И Цзин / video_001;
- 6/6 Gold complete;
- 24 Gold topics;
- blind validation completed.

Frozen results:

- Local Peak ±2 F1 = `0.583`;
- PELT ±2 F1 = `0.345`;
- Local Peak internal F1 excluding automatic window-start boundaries ≈ `0.444`.

Post-C diagnosis:

- Local Peak main bottleneck = boundary detection, not localization;
- 9/10 Dataset C FN were true detection misses;
- PELT rescued 6/10 Local Peak FN, but at severe over-segmentation cost;
- Local Peak = primary experimental candidate, not production baseline;
- PELT = recall-oriented comparator;
- production baseline is not declared.

Artifacts:

`analysis/DATASET_C_BLIND_VALIDATION.md`

Dataset C is frozen evidence and must not be reused for parameter tuning or
Topic Engine architecture selection.

---

## 2.7 Gold Expansion и состояния datasets

Authoritative Dataset E exclusion policy:
`analysis/DATASET_E_TOPIC_ENGINE_EVIDENCE_POLICY_2026-08-26.md`.

Policy:

- Dataset D = **LOCKED TEST**;
- Dataset E = **EXCLUDED FROM TOPIC ENGINE EVIDENCE**;
- Dataset F = potential **DEVELOPMENT** source после source/ASR quality repair;
- future Gold expansion intentionally diversifies seminar structure and subject
  matter внутри контролируемого целевого авторского корпуса.

Quality gate:

- Dataset D: `SOURCE QUALITY INSUFFICIENT`; repair/replace source is required
  before any locked-test evaluation;
- Dataset E: original source required resegmentation; historical topic-agnostic
  text segmentation prototype retained as transcript-segmentation engineering
  evidence only and is **not** `READY FOR GOLD` or benchmark evidence;
- Dataset F: `SOURCE QUALITY INSUFFICIENT`.

Historical Dataset E prototype facts (not Topic Engine evidence):

- 189 coarse cues → 704 derived segments;
- median duration 30.77s → 7.869s;
- median words 63 → 17;
- conservation and deterministic byte-identical generation: PASS;
- timestamps are derived estimates, not source-exact.

These facts preserve the architectural lesson that arbitrary SRT cue granularity
is unsuitable as the canonical coordinate system. Dataset E must not be used for
Gold creation, tuning, architecture/model/configuration comparison,
`TOPIC SEGMENTATION STABLE` acceptance, or conclusions about the Product Owner's
seminar corpus. Gold E is not planned.

## 2.8 Будущая структура benchmark datasets

Текущее разделение evidence:

DEVELOPMENT / CALIBRATION
→ Dataset A, Dataset B history/error analysis, and future controlled
target-corpus development sources; Dataset F is a potential source after repair

EXCLUDED FROM TOPIC ENGINE EVIDENCE
→ Dataset E; historical artifacts may be retained only as transcript-segmentation
engineering evidence

LOCKED TEST
→ Dataset D only after source repair and then without development tuning

Желательная дальнейшая цель:

5 разных видео
× 6–8 окон

≈ 30–40 gold windows

≈ 200–300+ gold topics/boundaries

---

## 2.9 Автоматическое определение количества тем

Будущая задача Topic Engine после Final Controlled Word Alignment Decision и
расширения development evidence. Она не является текущим architecture
checkpoint.

Кандидаты:

- [ ] Pelt + learned penalty
- [ ] Binseg + penalized cost
- [ ] elbow method
- [ ] BIC / AIC-подобный criterion
- [ ] semantic cohesion + boundary strength
- [ ] локальный boundary classifier
- [ ] supervised classifier на пользовательской gold-разметке

Важно:

не переобучать решение на одном семинаре.

---

## 2.10 Benchmark Runner

Планируемая команда:

project-topic-benchmark-run

Функции:

- [ ] запуск разных Topic Engines;
- [ ] LLM baseline;
- [ ] embedding engine;
- [ ] сравнение с gold;
- [ ] Boundary Precision;
- [ ] Boundary Recall;
- [ ] Boundary F1;
- [ ] tolerance ±ID / ±seconds;
- [ ] exact matches;
- [ ] over-segmentation;
- [ ] under-segmentation;
- [ ] topic-count error;
- [ ] mean nearest boundary distance;
- [ ] отчёт по каждому case;
- [ ] aggregate report;
- [ ] сохранение результатов эксперимента.

---

## 2.11 Критерий применимости Topic Automation

Будущий product gate: **TOPIC AUTOMATION USABLE**.

Boundary F1 остаётся важной диагностической метрикой, но не определяет production
readiness в одиночку. До открытия Dataset D необходимо заранее определить
eligible evidence и acceptance criteria, включая:

- Boundary Precision/Recall/F1 при заявленных tolerances;
- over-segmentation и under-segmentation;
- topic-count error;
- **Human Correction Time / Hour** исходного материала;
- semantic usefulness для Seminar Structure и Knowledge Product;
- cross-seminar generalization на контролируемом авторском корпусе;
- provenance completeness и отсутствие source/timing fabrication.

Оценка выполняется после freeze кандидата и topic-agnostic repair Dataset D.
Dataset D остаётся untouched `LOCKED TEST` до единственного разрешённого blind
evaluation.

## 2.12 External Topic / Semantic Segmentation Survey

Статус: REQUIRED BEFORE SUBSTANTIAL NEW CUSTOM ALGORITHMS

Bounded survey должен классифицировать внешние semantic segmentation,
topic-structure и related baseline решения как `ADOPT`, `ADAPT`, `REJECT` или
`BUILD`. Затем выбранные baselines проходят challenge на eligible development
evidence. Dataset C закрыт, Dataset D locked, Dataset E excluded.

---

# 3. Global Seminar Structure

Статус: POC PLANNED / PARALLEL

Первый POC разрешён на Golden Seminar (`Стресс код`) с verified manual, Gold или
semi-automatic topics до perfect automatic boundaries. POC проверяет отдельную
задачу hierarchy/merge/recurrence и не считается доказательством качества
Boundary Engine.

- [ ] собрать темы всех окон в структуру полного видео;
- [ ] убрать window-boundary artifacts;
- [ ] merge дублирующихся тем;
- [ ] убрать ложное дробление;
- [ ] восстановить естественную последовательность;
- [ ] поддержать многочасовые видео;
- [ ] поддержать многодневные семинары;
- [ ] построить иерархию:
  - seminar
  - day/video
  - chapter
  - topic
  - subtopic при необходимости.

---

# 4. Multi-source Alignment

Статус: PENDING

Цель:

связывать знания из разных источников одного семинара.

Источники:

- Video
- Audio
- TXT
- MD
- DOCX
- PPTX
- PDF
- handouts
- other

Необходимо:

- [ ] Video ↔ PPTX alignment
- [ ] Topic ↔ slide
- [ ] Topic ↔ PDF page
- [ ] Topic ↔ handout section
- [ ] Topic ↔ external document
- [ ] сохранение provenance
- [ ] поддержка нескольких источников одного знания

---

# 5. Document Pipeline

Статус: PENDING / PARTIALLY IMPLEMENTED

Поддерживаемые форматы:

- [ ] TXT
- [ ] MD
- [ ] DOCX
- [ ] PPTX
- [ ] PDF

Принцип:

оригинал
→ извлечение содержимого
→ нормализация
→ структурированное представление
→ Knowledge Layer

## TXT / MD

- кодировка
- очистка
- структура

## DOCX

- headings
- paragraphs
- lists
- tables
- images
- document structure

## PPTX

- slide number
- title
- text
- speaker notes
- tables
- images
- slide boundaries

## PDF

- native text extraction
- OCR fallback
- page ranges
- excluded pages
- image-heavy page detection
- не OCR-ить рисунки как обычный текст
- сохранение номера страницы

---

## 5.x Source Registry / External Sources

Статус: PENDING

SeminarText должен поддерживать регистрацию первичных источников знаний
без обязательного копирования оригинального файла в проект или Obsidian Vault.

Типы источников:

- book
- article
- research
- document
- presentation
- website
- external_author
- other

Для каждого источника необходим стабильный `source_id`.

Минимальные данные:

- source_id
- source_type
- title
- author
- year
- language
- local_file
- external_url
- project
- seminar
- status
- fingerprint
- provenance

### Локальные файлы

PDF/DOCX/PPTX и другие оригиналы могут храниться:

- на локальном диске;
- на внешнем диске;
- в Dropbox;
- в iCloud Drive;
- в другом локально доступном хранилище.

Оригинальный файл НЕ обязан копироваться в Obsidian Vault.

Требования:

- [ ] регистрация файла без копирования
- [ ] опциональное копирование
- [ ] сохранение исходного пути
- [ ] проверка доступности файла
- [ ] размер и тип файла
- [ ] fingerprint/checksum
- [ ] обнаружение замены файла
- [ ] изменение пути без изменения source_id
- [ ] поддержка внешних дисков
- [ ] поддержка локально доступных Dropbox/iCloud файлов

Планируемые команды:

    seminartext source-add "/path/to/book.pdf"

    seminartext project-source-add PROJECT "/path/to/book.pdf"

### PDF / Book Pipeline

    Original PDF
        ↓
    Source Registry
        ↓
    Page-aware extraction
        ↓
    Chapters / Sections
        ↓
    Knowledge Engine
        ↓
    Human Review
        ↓
    Obsidian

Любое производное знание должно сохранять:

    source_id
    page / page range
    chapter / section
    original file

Не смешивать:

- оригинальный источник;
- содержание семинара;
- авторскую интерпретацию;
- внешний научный источник;
- AI summary;
- AI hypothesis.


---

# 6. Track B — Knowledge Product / Knowledge Engine

Статус: BOUNDED GOLDEN SLICE PLANNED

Цель:

превращать структурированные материалы семинаров в связанную авторскую систему знаний.

Первый vertical slice использует только минимальные entities `Seminar`, `Source`,
`Topic`, `Concept`, `Evidence` и auditable provenance. Расширенные entity types
ниже остаются будущим направлением, а не prerequisite prototype.

Основные типы сущностей:

- concept
- term
- method
- practice
- artifact
- service
- case
- example
- question
- answer
- source
- seminar
- observation
- idea
- hypothesis

---

## 6.1 Concept / Entity Detection

- [ ] Concept Detection
- [ ] Term Detection
- [ ] Method Detection
- [ ] Practice Detection
- [ ] Artifact Detection
- [ ] Service Detection
- [ ] Case Detection
- [ ] Q&A Detection
- [ ] Source Detection
- [ ] Observation / Idea Detection
- [ ] Hypothesis Detection

AI не создаёт canonical author knowledge автоматически.

Новые сущности сначала:

CANDIDATE

---

## 6.2 Entity Resolution / Concept Resolution

Для каждого найденного объекта:

найденный термин
→ поиск Knowledge Base
→ existing / new / duplicate / ambiguous

Решения:

- ACCEPT
- REJECT
- MERGE
- LINK EXISTING
- CREATE CANDIDATE

Не терять авторскую терминологию.

---

## 6.3 Relationship Engine

Типы возможных связей:

- introduces
- continues
- develops
- deepens
- explains
- applies
- prerequisite
- related_to
- example_of
- uses_method
- uses_artifact
- contradicts
- revises

Связи должны иметь provenance.

---

## 6.4 Evolution / Contradiction Detection

- [ ] развитие определения;
- [ ] новые свойства концепции;
- [ ] новые связи;
- [ ] ранняя и поздняя версии концепции;
- [ ] потенциальные противоречия;
- [ ] пробелы в определениях;
- [ ] concepts без нормального определения.

---

# 7. Provenance Layer

Статус: MANDATORY

Каждое знание должно иметь происхождение.

Возможные origin types:

- author
- seminar
- consultation
- practice
- book
- article
- research
- external_author
- hypothesis
- AI_candidate

Не смешивать:

авторское утверждение
≠ внешний источник
≠ AI-гипотеза

Желательный provenance:

knowledge
→ seminar
→ video/document
→ time/page/slide
→ original evidence

---

# 8. Human Review

Статус: PENDING

Принцип:

AI анализирует
→ человек утверждает
→ SeminarText записывает canonical knowledge

Review queue:

- [ ] новые concepts
- [ ] новые methods
- [ ] новые practices
- [ ] новые links
- [ ] duplicates
- [ ] merge candidates
- [ ] contradictions
- [ ] definition changes
- [ ] source conflicts
- [ ] approve
- [ ] reject
- [ ] merge
- [ ] defer

---

# 9. Golden Seminar Vertical Slice / Obsidian Knowledge Prototype

Статус: UNBLOCKED AFTER MINIMUM CANONICAL EVIDENCE FOUNDATION

Первый bounded slice выполняется на controlled target-corpus seminar — по
умолчанию `Стресс код`. Разрешённый input topics: existing verified/Gold/manual
topics и явно помеченные semi-automatic drafts.

Минимальный результат использует entities:

- `Seminar`;
- `Source`;
- `Topic`;
- `Concept`;
- `Evidence`.

Prototype должен проверить evidence navigation, provenance, usefulness и human
review, но не требует:

- `TOPIC SEGMENTATION STABLE`;
- full bidirectional Obsidian sync;
- graph database;
- production RAG;
- site integration;
- Marketing Passport.

Topic Engine продолжает развиваться параллельно как путь автоматизации этого
ручного/verified workflow в масштабе.

---

# 10. Knowledge Base / Obsidian Integration

Статус: BOUNDED PROTOTYPE PLANNED

Цель:

Obsidian становится долговременным Knowledge Layer авторской системы.

SeminarText становится механизмом автоматического наполнения и обслуживания этой базы.

---

## 10.1 Obsidian Knowledge Prototype Schema

Определить структуру Vault.

Минимальные типы заметок prototype:

- Seminar
- Source
- Topic
- Concept
- Evidence

Возможные последующие типы:

- Term
- Method
- Practice
- Artifact
- Service
- Case
- Q&A
- Source / Reference
- Observation / Idea
- Hypothesis

Определить:

- [ ] folder structure
- [ ] Properties / YAML
- [ ] stable entity IDs
- [ ] Wikilinks
- [ ] relationship types
- [ ] aliases
- [ ] provenance fields
- [ ] timestamps
- [ ] page references
- [ ] slide references
- [ ] lifecycle/status
- [ ] canonical vs candidate entities

---

## 10.2 Obsidian Export MVP

Планируемая команда:

seminartext project-obsidian-export "<project>"

SeminarText напрямую создаёт Markdown-файлы внутри выбранного Obsidian Vault.

Автоматически разрешено экспортировать однозначные данные:

- [ ] Seminar card
- [ ] Video / Source cards
- [ ] Topics
- [ ] topic hierarchy
- [ ] timecodes
- [ ] source references
- [ ] provenance
- [ ] существующие Wikilinks
- [ ] document/page/slide references

Первый пилот:

Стресс код

---

## 10.3 Automatic Knowledge Loading

После обработки SeminarText должен уметь автоматически наполнять соответствующие разделы Obsidian.

Допустимые prototype inputs:

SeminarText
→ verified/manual/Gold/semi-automatic Topics
→ Knowledge Engine
→ Review
→ Obsidian

После повышения автоматизации тот же contract принимает Topic Draft от Topic
Engine без изменения provenance requirements.

Автоматически:

- темы;
- таймкоды;
- карточки источников;
- Seminar cards;
- provenance;
- ссылки на существующие сущности.

Через Human Review:

- новые concepts;
- новые methods;
- новые practices;
- новые artifacts;
- изменение определений;
- merge дублей;
- contradictions;
- speculative relationships.

---

## 10.4 Safe Obsidian Sync

Планируемая команда:

seminartext project-obsidian-sync "<project>"

Требования:

- [ ] повторный запуск не создаёт дубли;
- [ ] idempotent sync;
- [ ] stable IDs;
- [ ] не уничтожать ручные правки пользователя;
- [ ] разделять machine-managed content и human-managed content;
- [ ] конфликт detection;
- [ ] change log;
- [ ] rollback strategy;
- [ ] safe re-export.

---

## 10.5 Obsidian ↔ Codex / ChatGPT

После стабилизации Knowledge Layer:

- [ ] Codex читает Vault;
- [ ] анализирует заметки;
- [ ] предлагает связи;
- [ ] ищет дубли;
- [ ] ищет contradictions;
- [ ] помогает поддерживать структуру;
- [ ] работает через human review;
- [ ] изменения должны быть проверяемыми.

На первом этапе прямой Markdown filesystem integration предпочтительнее сложного API.

В будущем возможно:

- Obsidian Local REST API;
- MCP;
- другие безопасные интеграции.

---

## 10.x Source Cards

Obsidian должен содержать самостоятельные карточки первичных источников.

Пример:

    Type: Source
    Source_type: Book
    Source_ID: book_bradley_nelson_emotion_code
    Title: The Emotion Code
    Author: Bradley Nelson
    Language: en
    Local_file: /Users/.../The Emotion Code.pdf
    External_URL:
    Project:
    Seminar:
    Status: registered

Требования:

- [ ] Source Card
- [ ] стабильный Source_ID
- [ ] Source ↔ Project
- [ ] Source ↔ Seminar
- [ ] Source ↔ Concept
- [ ] Source ↔ Method
- [ ] ссылка на локальный оригинал
- [ ] внешний URL
- [ ] PDF может находиться вне Vault
- [ ] page-level provenance
- [ ] chapter/section provenance

Рекомендуемая структура Vault:

    06 Исследования и источники/
        Книги/
        Статьи/
        Исследования/
        Внешние авторы/

Markdown-карточка является сущностью Knowledge Base.
Оригинальный PDF является evidence/source asset.


---

# 11. Knowledge Diff

Статус: PENDING

После обработки нового материала показывать:

- новые concepts;
- новые methods;
- новые practices;
- новые artifacts;
- новые connections;
- развитие существующих concepts;
- potential contradictions;
- definition changes;
- новые external sources.

---

# 12. Knowledge Graph Validator

Статус: PENDING

Планируемая команда:

knowledge-check

Проверять:

- broken Wikilinks
- duplicate concepts
- missing IDs
- notes without type
- objects without provenance
- inconsistent naming
- orphan concepts
- unresolved candidates
- suspicious duplicates
- invalid relationships
- missing source evidence

---

# 13. Cross-Seminar Knowledge System

Статус: PENDING

После появления нескольких обработанных семинаров:

- [ ] Cross-Seminar Dataset
- [ ] Concept Resolution benchmark
- [ ] Relationship benchmark
- [ ] Global Knowledge Graph
- [ ] cross-seminar provenance
- [ ] развитие concepts между курсами
- [ ] prerequisites
- [ ] основная последовательная цепь семинаров
- [ ] внецепочечные / встраиваемые семинары

Вопросы, на которые система должна уметь отвечать:

- где концепция впервые введена;
- где развивалась;
- где уточнялась;
- где применялась;
- как менялось определение;
- какие семинары требуют её как prerequisite;
- какие исходные фрагменты подтверждают утверждение.

---

# 14. Learning Architecture

Статус: PENDING

- prerequisites;
- рекомендуемая последовательность обучения;
- уровни сложности;
- knowledge dependencies;
- method dependencies;
- practice dependencies;
- персональные учебные маршруты.

---

# 15. Marketing Passport

Статус: PENDING

Параметры:

- целевая аудитория;
- боль;
- желаемый результат;
- осознаваемый запрос;
- скрытая потребность;
- триггер;
- страхи;
- возражения;
- предыдущие попытки;
- уровень осознания;
- язык аудитории;
- ценности;
- критерии доверия.

Marketing Passport должен опираться на фактический материал семинаров и Knowledge Graph.

---

# 16. Интеграция с проектом «Сайт Юра»

Knowledge Base должна обслуживать:

- школу семинаров;
- личные консультации;
- практики Новолуния и Полнолуния;
- практики на фазы Солнца;
- проект «Человек. Инструкция по применению»;
- лечебные и профессиональные артефакты;
- И Цзин прогностический сервис;
- сервисы по картам Чака Спеццано;
- будущие методы;
- будущие сервисы.

Сайт:

- каталог семинаров;
- связанные программы;
- карточки знаний;
- рекомендации следующего обучения;
- поиск по авторской системе;
- персональные маршруты обучения.

---

# 17. Educational Content

Статус: PENDING

На основе Knowledge Base:

- конспекты;
- методички;
- FAQ;
- статьи;
- книги;
- учебные маршруты;
- справочные материалы.

Любой производный материал должен сохранять provenance.

---

# 18. Media Engine

Статус: PENDING / PARTIALLY IMPLEMENTED

- subtitles
- automatic subtitles
- cut
- clips
- semantic clips
- chapter timecoding
- topic-based video cutting
- повторное использование фрагментов
- образовательные материалы
- маркетинговые материалы

---

# 19. Knowledge Assistant

Статус: FUTURE

Цель:

интерактивный помощник по всей авторской системе.

Возможности:

- semantic search;
- поиск по Knowledge Graph;
- retrieval исходного evidence;
- ответы со ссылками на seminar/video/timecode/page;
- сравнение концепций;
- развитие концепций во времени;
- обнаружение contradictions;
- помощь в создании новых программ;
- помощь в подготовке семинаров;
- помощь в работе с клиентскими запросами.

---

# CURRENT NEXT ACTION

Текущий этап: **CANONICAL EVIDENCE FOUNDATION / PARALLEL TRACK PREPARATION**.

Принята следующая обязательная последовательность без преждевременной реализации
поздних stages:

1. Architecture + State consistency repair — **DONE (Issue #36)**.
2. Final controlled Word Alignment decision — **DONE (Issue #38)**.
3. Canonical Evidence Schema v1 — **DONE (Issue #40)**.
4. **Word Timeline MVP on one controlled source — NEXT.**
5. Parallel split:
   - Golden Seminar Knowledge Slice → Obsidian Knowledge Prototype → Product
     Review;
   - External Topic/Semantic Segmentation Survey → Baseline Challenge → Topic
     Engine improvement.
6. Global Seminar Structure POC using verified/manual topics where needed.
7. Freeze Topic Engine candidate.
8. Repair/prepare Dataset D topic-agnostically while preserving LOCKED TEST.
9. Dataset D blind evaluation after candidate/config/criteria freeze.
10. Define and assess `TOPIC AUTOMATION USABLE`.
11. Expand Knowledge Engine.
12. Multi-seminar Knowledge MVP.
13. Later: Cross-Seminar Graph / Learning / Marketing / Site / Media / Knowledge
    Assistant.

Dataset guardrails apply throughout: A/B are development/history evidence; C is
closed/frozen; D is locked; E is excluded; F remains quarantined/potential
development until source/ASR repair.

## Roadmap ↔ State consistency requirement

`SEMINARTEXT_4_ROADMAP.md` is human-readable strategy.
`SEMINARTEXT_4_STATE.json` is machine-readable operational state. They must share
the checkpoint `evidence_first_parallel_v1` and must not disagree on dataset
roles, milestone completion, blockers, or next actions.

Every architecture/state milestone PR must:

1. update both files when shared facts change;
2. validate State as JSON;
3. review A/B/C/D/E/F roles and the ordered next-action sequence;
4. preserve historical experiment artifacts rather than rewriting them;
5. record accepted architectural changes in `decisions/`.

State should eventually be schema-validated or generated from one policy source.
A lightweight consistency check is preferred; a large governance subsystem is
not part of the current milestone.

Consistency review for this checkpoint:

`analysis/ROADMAP_STATE_CONSISTENCY_REVIEW_2026-08-26.md`.

---

# PRODUCT OWNER RULE

Product Owner является главным агентом проекта.

Product Owner:

- определяет цель;
- устанавливает требования;
- определяет приоритеты;
- задаёт критерии готовности;
- ставит задачи остальным ролям;
- принимает итоговый результат.

Нельзя менять критический путь проекта без Product Owner review.
