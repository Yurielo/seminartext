# SeminarText 4.x Roadmap

Последнее обновление: 2026-08-25

## Главная цель

Развить SeminarText из системы транскрипции и обработки семинаров в систему построения, развития и обслуживания единой авторской базы знаний.

Архитектурный принцип:

Sources
→ Evidence Foundation
→ Topic Engine
→ Seminar Structure
→ Multi-source Alignment
→ Knowledge Engine
→ Human Review
→ Obsidian Knowledge Base
→ Cross-Seminar Knowledge Graph
→ Learning / Marketing / Site / Media / Knowledge Assistant

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

# 1. Evidence Foundation / Базовая инфраструктура

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

## Evidence / Provenance

Все производные данные должны сохранять связь с исходником.

Необходимо поддерживать:

- [ ] project_id
- [ ] video_id
- [ ] document_id
- [ ] source_id
- [ ] stable topic_id
- [ ] source provenance
- [ ] временной диапазон
- [ ] номер страницы документа
- [ ] номер слайда
- [ ] возможность перейти от знания к исходному evidence

Тестовый реальный проект:

Стресс код

Видео:
- video_001
- video_002
- video_003
- video_004

---

# 2. Hybrid Topic Engine / Topic Segmentation

Статус: CURRENT STAGE

Цель:

Автоматически определять естественные смысловые границы семинара и формировать устойчивые смысловые темы.

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

## 2.5 Dataset B — independent frozen validation

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

Dataset B:

Заблокированные эмоции
→ frozen unseen validation complete

Dataset C:

И Цзин
→ candidate windows prepared; manual Gold DOMAIN_AUTHORING next

---

## 2.6 Dataset C — next independent validation

Статус: CANDIDATES PREPARED / NEEDS MANUAL GOLD

Цель:

проверить переносимость Stage 2 Hybrid Topic Engine ещё на одном независимом
семинаре до architecture decision checkpoint.

План:

- [x] выбрать третий семинар: И Цзин / video_001;
- [x] подготовить независимые candidate windows: 6 cases, 24 available windows, 23 eligible windows;
- [ ] получить manual Gold только там, где требуется `DOMAIN_AUTHORING`;
- [ ] прогнать frozen A/B/C validation без tuning;
- [ ] принять architecture decision checkpoint перед Stage 3.

Artifact:

`analysis/dataset_c/topic_benchmark_dataset_c.json`

Review:

`analysis/DATASET_C_PREPARATION.md`

---

## 2.7 Будущая структура benchmark datasets

После Dataset C:

TRAIN
→ настройка параметров

VALIDATION
→ выбор block size / penalty / scoring

TEST
→ финальная независимая проверка

Желательная дальнейшая цель:

5 разных видео
× 6–8 окон

≈ 30–40 gold windows

≈ 200–300+ gold topics/boundaries

---

## 2.8 Автоматическое определение количества тем

Главная нерешённая задача Topic Engine.

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

## 2.9 Benchmark Runner

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

## 2.10 Критерий завершения Topic Engine

TOPIC SEGMENTATION STABLE

Критерии будут формально определены после frozen A/B/C validation и
architecture decision checkpoint.

---

# 3. Global Video Review / Seminar Structure

Статус: PENDING

После стабильного локального Topic Engine:

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

# 6. Knowledge Engine / Concept Engine

Статус: PENDING

Цель:

превращать структурированные материалы семинаров в связанную авторскую систему знаний.

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

# 9. MANDATORY GATE — OBSIDIAN

Статус: DO NOT SKIP

После:

TOPIC SEGMENTATION STABLE

и определения базовой Knowledge Schema

обязательный следующий крупный milestone:

OBSIDIAN MVP / KNOWLEDGE BASE INTEGRATION

Не откладывать Obsidian на конец SeminarText 4.x.

---

# 10. Knowledge Base / Obsidian Integration

Статус: PENDING

Цель:

Obsidian становится долговременным Knowledge Layer авторской системы.

SeminarText становится механизмом автоматического наполнения и обслуживания этой базы.

---

## 10.1 Obsidian Schema

Определить структуру Vault.

Типы заметок:

- Seminar
- Video / Source
- Topic
- Concept
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

Пример:

SeminarText
→ Topic Engine
→ Knowledge Engine
→ Review
→ Obsidian

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

Текущий этап:

HYBRID TOPIC ENGINE

Gold Dataset A:

Стресс код
GOLD COMPLETE: 6/6

Текущий архитектурный лидер:

BGE-M3
+
15-second semantic blocks
+
ruptures / change-point detection

Лучший эксперимент при известном количестве тем:

±2 ID F1 = 0.738
±5 ID F1 = 0.833

Следующая обязательная задача:

1. Разметить Dataset C Gold windows через `DOMAIN_AUTHORING`.
2. Не менять параметры Topic Engine до frozen A/B/C validation.
3. Прогнать текущие frozen engines по Dataset C.
4. Сравнить переносимость архитектуры на Dataset A/B/C.
5. Принять architecture decision checkpoint перед Stage 3.
6. После этого определить train / validation / test.
7. Решить задачу automatic topic count.
8. Реализовать следующий production Topic Engine шаг только после checkpoint.
9. Довести Topic Segmentation до STABLE.
10. Перейти к Obsidian Schema / Obsidian MVP.

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
