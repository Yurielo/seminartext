# Local Peak Raw Signal Failure Analysis

Дата: 2026-08-26

Статус: read-only diagnostic experiment на Dataset A/B. Dataset C не читался observer-ом и не запускался. Production-код, frozen Local Peak и Gold не изменялись.

Диагностические артефакты:

- Observer: `analysis/local_peak_raw_signal_observer.py`
- Полный per-position trace: `analysis/local_peak_raw_signal_failure_analysis.json`
- Frozen engine: `analysis/experiments/bge_m3_changepoint_topic_engine.py`

Observer импортирует функции frozen engine, повторяет только вычисление BGE-M3 signal для A/B и проверяет точное совпадение final predictions с ранее сохранёнными frozen result JSON. Все 12 окон воспроизведены без расхождений.

## 1. Frozen pipeline

Фактическая последовательность по коду:

1. Нормализация SRT-сегментов.
2. Группировка сегментов в 15-секундные semantic blocks; текст сегментов конкатенируется внутри блока.
3. Один BGE-M3 embedding на каждый block через Ollama `/api/embed`.
4. Для каждой границы блоков вычисляются средние embeddings двух блоков слева и двух справа.
5. Raw signal: `1 - cosine(mean(left_context), mean(right_context))`.
6. Smoothing: `[0.25, 0.5, 0.25]`.
7. Threshold: median smoothed score текущего окна `* 1.15`.
8. Кандидат должен одновременно пройти threshold и быть local maximum относительно соседних signal positions.
9. Кандидаты сортируются по убыванию score; greedy block-level NMS сохраняет расстояние не менее 3 blocks.
10. После каждого принятого кандидата проверяется limit; сохраняется максимум 11 change points.
11. Block boundary отображается в `start_id` первого сегмента правого блока.
12. Детерминированно добавляется первый `segment_id` окна.
13. Выполняется второй min-gap по segment ID, минимум 3 ID.
14. Формируются final predictions.

Отдельного этапа `contextual text` нет: context применяется к уже вычисленным block embeddings через left/right mean vectors.

Frozen parameters:

| Parameter | Value |
|---|---|
| Embeddings | `bge-m3:latest`, Ollama `/api/embed` |
| Block | 15 seconds |
| Context | 2 blocks left / 2 blocks right |
| Signal | cosine distance of contextual means |
| Smoothing | `[0.25, 0.5, 0.25]` |
| Threshold | window median `* 1.15` |
| Block min-gap/NMS | 3 blocks |
| Maximum selected change points | 11 |
| Segment-ID min-gap | 3 IDs |

Frozen script SHA-256: `83d7e0ec5e9e67be31aaf90260f3f8f8d0d8690cea4e06242b3f6d7807ee49a2`.

### Attribution rule

Для каждого FN берётся ближайшая mappable block-boundary и диагностическое окно +/-2 signal positions. Primary stage назначается по самому позднему этапу, которого достигает response:

1. final peak вне допуска -> `MAPPING/LOCALIZATION`;
2. selected/threshold candidate, удалённый gap -> `MIN_GAP`;
3. NMS survivor за limit -> `MAX_BOUNDARIES`;
4. local maximum ниже threshold -> `BELOW_THRESHOLD`;
5. response без local maximum -> `NOT_LOCAL_MAXIMUM`;
6. нет local maximum и above-median response -> `NO_SIGNAL`.

Аналитическое окно не является новым параметром engine и не используется для создания predictions.

## 2. Dataset A/B FN inventory

`Ratio` = smoothed score / frozen threshold данного окна. `Map` = segment ID позиции, представляющей самый поздний достигнутый stage.

### Dataset A: 33 FN

| Window | Gold | Topic | Stage | Map | Offset | Raw | Smooth | Ratio |
|---|---:|---|---|---:|---:|---:|---:|---:|
| 01 | 16 | Формат группы и правила присутствия | BELOW_THRESHOLD | 16 | +0 | 0.3541 | 0.3122 | 0.887 |
| 01 | 38 | Интерактивное обучение и активное мышление | BELOW_THRESHOLD | 40 | +2 | 0.2857 | 0.2727 | 0.775 |
| 01 | 54 | Знакомство и ожидания участников | NOT_LOCAL_MAXIMUM | 51 | -3 | 0.3795 | 0.3522 | 1.000 |
| 01 | 86 | Стресс как механизм адаптации и выживания | BELOW_THRESHOLD | 91 | +5 | 0.4056 | 0.3391 | 0.963 |
| 01 | 100 | Переход к следующему участнику | MAPPING/LOCALIZATION | 103 | +3 | 0.4214 | 0.4104 | 1.166 |
| 04 | 302 | Востребованность онлайн-работы | MAPPING/LOCALIZATION | 306 | +4 | 0.3993 | 0.3632 | 1.053 |
| 04 | 310 | Эффективность онлайн-работы | BELOW_THRESHOLD | 313 | +3 | 0.3633 | 0.3114 | 0.903 |
| 04 | 313 | План и структура семинара | BELOW_THRESHOLD | 313 | +0 | 0.3633 | 0.3114 | 0.903 |
| 04 | 321 | Как будет проходить обучение | BELOW_THRESHOLD | 321 | +0 | 0.3161 | 0.3069 | 0.890 |
| 04 | 331 | Восприятие большого объёма новой информации | MAPPING/LOCALIZATION | 337 | +6 | 0.3851 | 0.3804 | 1.103 |
| 04 | 351 | Благополучие, счастье и здоровье | BELOW_THRESHOLD | 347 | -4 | 0.2984 | 0.2939 | 0.852 |
| 08 | 666 | Передний и задний срединные меридианы | BELOW_THRESHOLD | 667 | +1 | 0.2965 | 0.2717 | 0.845 |
| 08 | 684 | Применение гимнастики для мозга | BELOW_THRESHOLD | 683 | -1 | 0.3165 | 0.3053 | 0.950 |
| 08 | 721 | Чакры, аура и энергетические потоки | BELOW_THRESHOLD | 721 | +0 | 0.3129 | 0.2635 | 0.820 |
| 08 | 733 | Структурный уровень и структуры мозга | BELOW_THRESHOLD | 732 | -1 | 0.3014 | 0.2858 | 0.889 |
| 08 | 739 | Первоэлементы и духовная кинезиология | BELOW_THRESHOLD | 738 | -1 | 0.3748 | 0.3049 | 0.948 |
| 08 | 752 | Тонкие планы, трансцендентальное и рефлексы | BELOW_THRESHOLD | 749 | -3 | 0.3703 | 0.3064 | 0.953 |
| 12 | 1084 | Этапы протокола коррекции | BELOW_THRESHOLD | 1084 | +0 | 0.2944 | 0.2775 | 0.880 |
| 12 | 1101 | Подготовка к демонстрационной коррекции | BELOW_THRESHOLD | 1103 | +2 | 0.3451 | 0.2922 | 0.927 |
| 12 | 1110 | Темы для учебных коррекций | BELOW_THRESHOLD | 1107 | -3 | 0.3441 | 0.2844 | 0.902 |
| 12 | 1128 | Доверие тестированию и онлайн-работе | NOT_LOCAL_MAXIMUM | 1132 | +4 | 0.2861 | 0.2975 | 0.944 |
| 12 | 1135 | Показательная коррекция перед дальнейшим обучением | BELOW_THRESHOLD | 1135 | +0 | 0.3453 | 0.3055 | 0.969 |
| 12 | 1145 | Обеденный перерыв | BELOW_THRESHOLD | 1145 | +0 | 0.3253 | 0.2597 | 0.823 |
| 12 | 1149 | Начало демонстрационной коррекции | BELOW_THRESHOLD | 1145 | -4 | 0.3253 | 0.2597 | 0.823 |
| 17 | 1640 | Возвращение в настоящее с закладкой позитива | BELOW_THRESHOLD | 1639 | -1 | 0.2923 | 0.2743 | 0.868 |
| 17 | 1653 | Ретест результатов коррекции | BELOW_THRESHOLD | 1655 | +2 | 0.3031 | 0.3032 | 0.959 |
| 17 | 1666 | Проекция в будущее и ретест темы | BELOW_THRESHOLD | 1667 | +1 | 0.2927 | 0.2980 | 0.943 |
| 17 | 1670 | Повторная субъективная оценка дискомфорта | BELOW_THRESHOLD | 1673 | +3 | 0.3235 | 0.3005 | 0.951 |
| 17 | 1675 | Домашнее задание и рекомендации | BELOW_THRESHOLD | 1673 | -2 | 0.3235 | 0.3005 | 0.951 |
| 22 | 2062 | Мышечный тест как ответ «да» или «нет» | BELOW_THRESHOLD | 2060 | -2 | 0.3503 | 0.3219 | 0.961 |
| 22 | 2068 | Проверка стресса через мысленное представление | BELOW_THRESHOLD | 2069 | +1 | 0.3656 | 0.2722 | 0.813 |
| 22 | 2075 | Стресс на работу и трудовую деятельность | BELOW_THRESHOLD | 2077 | +2 | 0.3770 | 0.3296 | 0.984 |
| 22 | 2130 | Итоги первого учебного дня | BELOW_THRESHOLD | 2134 | +4 | 0.3305 | 0.3201 | 0.956 |

### Dataset B: 18 FN

| Window | Gold | Topic | Stage | Map | Offset | Raw | Smooth | Ratio |
|---|---:|---|---|---:|---:|---:|---:|---:|
| 01 | 16 | Знакомство с участниками, ожидания от семинара | BELOW_THRESHOLD | 14 | -2 | 0.3630 | 0.3409 | 0.946 |
| 01 | 79 | Практическое применение Эмоционального кода: стресс, телесное напряжение и быстрое расслабление | BELOW_THRESHOLD | 82 | +3 | 0.3523 | 0.3151 | 0.875 |
| 06 | 525 | Перерыв и переход к практической кинезиологической гимнастике | BELOW_THRESHOLD | 522 | -3 | 0.3354 | 0.3187 | 0.914 |
| 06 | 556 | Восстановление заднесрединного и переднесрединного меридианов | BELOW_THRESHOLD | 554 | -2 | 0.3071 | 0.3450 | 0.990 |
| 06 | 569 | Неврологический смысл упражнений: латеральность, пространство и время | BELOW_THRESHOLD | 568 | -1 | 0.3737 | 0.3465 | 0.994 |
| 06 | 581 | Упражнение «перекрёст»: перекрёстные и гомолатеральные движения | BELOW_THRESHOLD | 580 | -1 | 0.3266 | 0.2994 | 0.858 |
| 11 | 977 | Виды заблокированных эмоций по времени и источнику образования | BELOW_THRESHOLD | 979 | +2 | 0.3767 | 0.3389 | 0.970 |
| 11 | 990 | Заблокированные эмоции личного жизненного опыта: сознание, подсознание и уровень тела | BELOW_THRESHOLD | 991 | +1 | 0.3066 | 0.2724 | 0.780 |
| 11 | 1007 | Перенятые заблокированные эмоции и резонанс со значимыми взрослыми | BELOW_THRESHOLD | 1005 | -2 | 0.3964 | 0.3353 | 0.960 |
| 11 | 1021 | Семилетние циклы в жизни человека | MAPPING/LOCALIZATION | 1018 | -3 | 0.4264 | 0.3630 | 1.039 |
| 15 | 1403 | Концепция Сердечной стены: защита от внешнего мира заблокированными эмоциями | BELOW_THRESHOLD | 1404 | +1 | 0.3599 | 0.3098 | 0.915 |
| 20 | 1787 | Тест запястья: мышечное тестирование лучевого разгибателя кисти | BELOW_THRESHOLD | 1787 | +0 | 0.3380 | 0.2903 | 0.917 |
| 20 | 1804 | Переход к продвинутым методам тестирования | BELOW_THRESHOLD | 1806 | +2 | 0.3173 | 0.3078 | 0.973 |
| 20 | 1806 | Перцепция в работе специалиста | BELOW_THRESHOLD | 1806 | +0 | 0.3173 | 0.3078 | 0.973 |
| 25 | 2315 | Тестирование чакральной системы с помощью мышечного теста | BELOW_THRESHOLD | 2316 | +1 | 0.2914 | 0.2593 | 0.875 |
| 25 | 2344 | Устранение неврологической дезорганизации и восстановление корректного мышечного ответа | BELOW_THRESHOLD | 2345 | +1 | 0.2909 | 0.2654 | 0.896 |
| 25 | 2351 | МЭТ: мануальная энергетическая техника, постизометрическая релаксация | BELOW_THRESHOLD | 2354 | +3 | 0.3209 | 0.2798 | 0.945 |
| 25 | 2377 | Тест поляризации и подготовка тела к тестированию | BELOW_THRESHOLD | 2376 | -1 | 0.2614 | 0.2499 | 0.844 |

Четыре пары Gold используют один representative weak peak: A `310/313`, A `1145/1149`, A `1670/1675`, B `1804/1806`. Поэтому 45 BELOW_THRESHOLD FN соответствуют 41 уникальному weak peak.

## 3. Dataset A/B FP inventory

Каждый FP является final, above-threshold local maximum. Семантическая категория определена по транскрипции вокруг mapped segment.

| Dataset | Window | FP | Nearest Gold | Delta | Raw | Smooth | Ratio | Semantic cause |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| A | 01 | 49 | 54 | -5 | 0.3792 | 0.3551 | 1.009 | Conceptual detail/instruction inside the introduction. |
| A | 01 | 103 | 100 | +3 | 0.4214 | 0.4104 | 1.166 | Speaker change; genuine transition localized one ID outside tolerance. |
| A | 04 | 337 | 331 | +6 | 0.3851 | 0.3804 | 1.103 | Philosophical elaboration inside the information-volume topic. |
| A | 08 | 659 | 656 | +3 | 0.3830 | 0.3332 | 1.036 | Transcript fragment/artifact (`кем-то.`). |
| A | 08 | 701 | 706 | -5 | 0.3774 | 0.3341 | 1.039 | Analogy/example inside the same system-level explanation. |
| A | 12 | 1159 | 1149 | +10 | 0.4384 | 0.3571 | 1.132 | Delayed theory-to-demonstration/procedural transition. |
| A | 12 | 1165 | 1149 | +16 | 0.4260 | 0.3366 | 1.067 | Speaker selection/Q&A inside the demonstration setup. |
| A | 17 | 1609 | 1606 | +3 | 0.3617 | 0.3458 | 1.094 | Sensory example/detail inside positive-image formation. |
| A | 22 | 2124 | 2130 | -6 | 0.3968 | 0.3530 | 1.054 | Organizational next-day instruction inside homework. |
| A | 22 | 2142 | 2130 | +12 | 0.3621 | 0.3413 | 1.019 | Summary subpoint inside the day-end summary. |
| A | 22 | 2154 | 2130 | +24 | 0.4546 | 0.4347 | 1.298 | Sign-off/window-end transition below Gold topic granularity. |
| B | 01 | 51 | 79 | -28 | 0.4555 | 0.3696 | 1.026 | New participant/speaker inside one broad introduction topic. |
| B | 01 | 70 | 79 | -9 | 0.4158 | 0.3904 | 1.084 | Another participant/speaker change inside the same topic. |
| B | 11 | 963 | 951 | +12 | 0.4161 | 0.3508 | Ethical instruction/elaboration inside the current topic. |
| B | 11 | 1018 | 1021 | -3 | 0.4264 | 0.3630 | 1.039 | Localization near the seven-year-cycle transition. |
| B | 15 | 1408 | 1403 | +5 | 0.4924 | 0.3932 | 1.162 | Heart-wall continuation adjacent to documented transcript glitch. |
| B | 20 | 1779 | 1776 | +3 | 0.3876 | 0.3784 | 1.196 | Example/localization near muscle-test interpretation. |
| B | 20 | 1851 | 1837 | +14 | 0.4004 | 0.3294 | 1.041 | Participant Q&A/example inside the perception topic. |
| B | 20 | 1876 | 1837 | +39 | 0.3861 | 0.3644 | 1.151 | Speaker/Q&A continuation inside the same broad topic. |
| B | 25 | 2333 | 2330 | +3 | 0.3096 | 0.3051 | 1.030 | Procedural demonstration substep/localization. |
| B | 25 | 2383 | 2377 | +6 | 0.2938 | 0.3012 | 1.017 | Body-preparation procedural substep. |

Повторяющиеся FP mechanisms:

- Пример, пояснение или procedural substep без смены Gold-темы: 8.
- Speaker/Q&A change внутри широкой Gold-темы: 5.
- Localization-like FP около настоящей границы: 4.
- Organizational/sign-off: 2.
- Transcript artifact/glitch: 2.

Гипотеза подтверждается: Local Peak систематически реагирует на сильные semantic changes ниже Gold-гранулярности, особенно на смену говорящего, пример, организационную реплику и procedural beat.

## 4. Stage-loss accounting

| Failure stage | Dataset A | Dataset B | Total | Доля FN |
|---|---:|---:|---:|---:|
| NO_SIGNAL | 0 | 0 | 0 | 0.0% |
| WEAK_SIGNAL_BELOW_THRESHOLD | 28 | 17 | 45 | 88.2% |
| NOT_LOCAL_MAXIMUM | 2 | 0 | 2 | 3.9% |
| SUPPRESSED_BY_MIN_GAP | 0 | 0 | 0 | 0.0% |
| REMOVED_BY_MAX_BOUNDARIES | 0 | 0 | 0 | 0.0% |
| BLOCK_MAPPING / LOCALIZATION | 3 | 1 | 4 | 7.8% |
| OTHER | 0 | 0 | 0 | 0.0% |
| **Total** | **33** | **18** | **51** | **100%** |

`NO_SIGNAL=0` означает, что в operational neighborhood каждого FN найден хотя бы local maximum, above-median response или final neighboring peak. Это не означает, что все responses достаточно информативны: часть weak peaks имеет почти фоновую силу.

## 5. Signal-strength analysis

Technical window starts исключены из TP signal distribution, поскольку для них signal position отсутствует. Background содержит positions вне +/-2 от Gold и исключает уже учтённые FN representatives и final FP.

### Combined Dataset A/B

| Class | N | Raw mean | Raw median | Raw Q1-Q3 | Raw range |
|---|---:|---:|---:|---:|---:|
| TP internal | 19 | 0.3810 | 0.3823 | 0.3412-0.4101 | 0.2743-0.4816 |
| FN representative | 51 | 0.3378 | 0.3305 | 0.3068-0.3644 | 0.2614-0.4264 |
| FP | 21 | 0.3985 | 0.3968 | 0.3792-0.4260 | 0.2938-0.4924 |
| Background | 338 | 0.2714 | 0.2729 | 0.2382-0.3054 | 0.0452-0.4422 |

| Class | N | Smooth mean | Smooth median | Smooth Q1-Q3 | Smooth range | Median ratio |
|---|---:|---:|---:|---:|---:|---:|
| TP internal | 19 | 0.3591 | 0.3613 | 0.3442-0.3697 | 0.3010-0.4343 | 1.069 |
| FN representative | 51 | 0.3065 | 0.3053 | 0.2821-0.3210 | 0.2499-0.4104 | 0.943 |
| FP | 21 | 0.3584 | 0.3551 | 0.3366-0.3784 | 0.3012-0.4347 | 1.054 |
| Background | 338 | 0.2771 | 0.2785 | 0.2498-0.3059 | 0.1092-0.3712 | 0.837 |

### Dataset consistency

| Dataset | Class | N | Smooth median | Median threshold ratio |
|---|---|---:|---:|---:|
| A | TP | 9 | 0.3632 | 1.128 |
| A | FN | 33 | 0.3032 | 0.943 |
| A | FP | 11 | 0.3530 | 1.067 |
| A | Background | 157 | 0.2742 | 0.835 |
| B | TP | 10 | 0.3512 | 1.067 |
| B | FN | 18 | 0.3088 | 0.931 |
| B | FP | 10 | 0.3637 | 1.040 |
| B | Background | 181 | 0.2841 | 0.842 |

Descriptive pairwise ranking AUC по smoothed score:

- TP vs Background: `0.958`.
- FP vs Background: `0.947`.
- FN vs Background: `0.697`.
- TP vs FP: `0.514`.

Интерпретация:

- BGE-M3 cosine signal хорошо отличает сильное изменение от обычного background.
- Он почти не отличает Gold-valid TP от сильного внутритематического FP: TP и FP имеют практически одинаковые распределения, а FP raw mean даже выше.
- FN в среднем сильнее background, но слабее selected TP/FP. Это объясняет concentration сразу под threshold.
- Одномерный score измеряет semantic discontinuity, но не Gold-level topic transition.

## 6. Threshold analysis

### Фактические counts

- Всего FN: 51.
- Первый stage потери `BELOW_THRESHOLD`: 45 FN labels, или 88.2%.
- Эти labels соответствуют 41 уникальному local maximum из-за четырёх соседних пар Gold.
- 34 FN labels, представленные 33 уникальными peaks, одновременно:
  - находятся в +/-2 от Gold;
  - являются local maxima;
  - ниже frozen threshold;
  - индивидуально прошли бы неизменные block-gap, segment-gap и max-limit относительно frozen selected set.
- Для оставшихся 11 BELOW_THRESHOLD labels representative peak дополнительно отображается дальше +/-2, поэтому одного прохождения threshold недостаточно для benchmark TP.

Распределение 45 weak FN peaks по отношению к threshold:

| Ratio interval | FN labels |
|---|---:|
| 0.95-1.00 | 15 |
| 0.90-0.95 | 12 |
| 0.85-0.90 | 10 |
| <0.85 | 8 |

Во всех A/B signal traces найдено 76 local maxima ниже threshold:

- 35 находятся в +/-2 от пропущенного Gold.
- 41 не находятся в +/-2 ни от одной Gold-boundary.
- 23 из 76 имеют ratio >=0.95.
- 42 из 76 имеют ratio >=0.90.

Ответ на threshold hypothesis:

**Да, `median * 1.15` является главным непосредственным stage потери FN. Нет, это не доказывает, что tuning multiplier является правильным следующим направлением.** Порог отсекает много полезных weak peaks, но рядом с ними существует сопоставимый объём non-Gold local maxima. Простое снижение multiplier не решает TP-vs-FP separability и может резко увеличить over-segmentation.

Никакой альтернативный multiplier не вычислялся и не оценивался.

## 7. Local-maximum analysis

| Dataset | Signal positions | Local maxima | Above-threshold local maxima | Final internal predictions |
|---|---:|---:|---:|---:|
| A | 274 | 64 | 23 | 20 |
| B | 271 | 55 | 20 | 20 |
| Total | 545 | 119 | 43 | 40 |

Только 2/51 FN (`A:54`, `A:1128`) теряются на local-maximum requirement:

- `A:54` имеет response на уровне threshold, но соседняя позиция сильнее.
- `A:1128` имеет above-median response с ratio 0.944, но не формирует local maximum.

Следовательно, форма пика является вторичным bottleneck, а не главным источником FN.

## 8. Min-gap/NMS analysis

### Block-level NMS

- Above-threshold candidates: 43.
- Candidates removed by block-level NMS: 0.
- FN, подавленные block-level NMS: 0.

### Segment-ID min-gap

Три selected change points Dataset A удалены после mapping:

| Window | Mapped ID | Ratio | Причина |
|---|---:|---:|---|
| A01 | 3 | 1.111 | Слишком близко к mandatory start 1. |
| A04 | 290 | 1.033 | Слишком близко к mandatory start 288. |
| A12 | 1075 | 1.125 | Слишком близко к mandatory start 1073. |

Ни один из трёх не находится в +/-2 от benchmark FN. Segment-ID gap удалил три потенциальных FP у начала окна и не вызвал наблюдаемых A/B FN.

Среди 45 weak FN representatives ни один не конфликтует с frozen selected peaks по block gap или с frozen final predictions по segment gap. Таким образом, min-gap/NMS hypothesis для текущих A/B FN опровергнута.

## 9. Max-boundaries analysis

- Frozen limit: 11 selected change points на окно.
- Фактический максимум before segment mapping: 5 в одном окне.
- Ни одно окно не достигло limit.
- Candidates removed by max-boundaries: 0.
- FN caused by max-boundaries: 0.

Ограничение `maximum boundaries = 11` не влияет на текущие A/B FN и исключается из основных bottleneck. Это утверждение относится только к frozen run; оно не предсказывает поведение при ином threshold.

## 10. Mapping/localization analysis

Primary mapping/localization category назначена четырём FN, где сильный final peak существует, но его mapped segment находится вне +/-2:

| Dataset | Window | Gold | Final peak | Offset | Ratio |
|---|---:|---:|---:|---:|---:|
| A | 01 | 100 | 103 | +3 | 1.166 |
| A | 04 | 302 | 306 | +4 | 1.053 |
| A | 04 | 331 | 337 | +6 | 1.103 |
| B | 11 | 1021 | 1018 | -3 | 1.039 |

Для всех 51 FN существует технически доступная block mapping position в +/-2 от Gold. Следовательно, 15-секундная block grid не делает ни одну Gold-boundary A/B принципиально непредставимой. Четыре primary localization errors возникают из-за положения выбранного semantic peak, а не из-за отсутствия допустимого mapped segment.

У 11 BELOW_THRESHOLD labels representative weak peak находится дальше +/-2. Для них threshold является первым stage потери, но mapping/localization остаётся дополнительной проблемой после гипотетического прохождения threshold.

## 11. Primary failure mechanism

Главный непосредственный pipeline loss: **WEAK_SIGNAL_BELOW_THRESHOLD**, 45/51 FN.

Корневая алгоритмическая проблема формулируется шире: **single BGE-M3 cosine-distance score недостаточно разделяет Gold-level transitions и сильные intra-topic changes**.

Доказательства:

- 34 FN labels имеют mapping-compatible weak local maxima, которые индивидуально остановлены только threshold.
- Одновременно ниже threshold находятся 41 local maxima вне +/-2 от Gold.
- Выбранные TP и FP почти неразделимы: smoothed AUC TP-vs-FP `0.514`.
- FP часто имеют такой же или более сильный signal, чем TP, потому что speaker change, example, artifact и sign-off являются реальными semantic discontinuities, но не Gold topics.

Поэтому bottleneck нельзя честно свести к «порог слишком высокий». Порог реализует precision/recall tradeoff на сигнале с granularity mismatch.

## 12. Secondary failure mechanisms

1. **Mapping/localization:** 4 primary FN и ещё 11 weak labels с representative offset >2.
2. **Not-local-maximum shape:** 2 FN.
3. **Semantic granularity over-segmentation:** 21 FP, особенно examples, speaker/Q&A и procedural substeps.
4. **Adjacent Gold sharing one peak:** четыре пары Gold описываются одним weak local maximum; один threshold decision не может создать две независимые boundaries.
5. **Transcript artifacts:** минимум два FP связаны с fragment/glitch text.

Min-gap/NMS и max-boundaries не являются secondary FN mechanisms в frozen A/B run.

## 13. Какие гипотезы опровергнуты

1. **FN в основном вызваны отсутствием любого semantic response:** опровергнуто. `NO_SIGNAL=0` по operational attribution; FN median ratio 0.943.
2. **Block-level NMS уничтожает много настоящих границ:** опровергнуто. Удалено 0 above-threshold candidates и вызвано 0 FN.
3. **Segment-ID min-gap является источником FN:** опровергнуто для A/B. Он удалил 3 near-start non-Gold candidates.
4. **Maximum 11 boundaries ограничивает recall:** опровергнуто. Максимум фактически выбранных change points равен 5.
5. **Основная проблема находится в block-to-segment representability:** опровергнуто. Для каждого FN существует mappable position в +/-2.
6. **Сильный cosine peak сам по себе означает Gold topic:** опровергнуто. TP-vs-FP AUC близок к случайному ранжированию.

## 14. Какие гипотезы подтверждены

1. **Большинство FN имеют weak local response ниже frozen threshold:** подтверждено, 45/51.
2. **Threshold является главным immediate loss stage:** подтверждено; для 34 FN labels он является единственным непосредственным препятствием к mapping-compatible candidate в текущем frozen окружении.
3. **Простое threshold tuning рискованно:** подтверждено overlap-ом 76 below-threshold local maxima, из которых 41 вне Gold tolerance.
4. **Local Peak реагирует на внутритематические semantic changes:** подтверждено всеми 21 FP и их текстовыми контекстами.
5. **TP и FP требуют дополнительного granularity/discourse signal:** подтверждено почти одинаковыми score distributions.
6. **Localization существует, но вторична:** подтверждено четырьмя primary cases против 45 below-threshold losses.

## 15. Рекомендация следующего эксперимента

Рекомендуется один **pre-registered candidate separability experiment на Dataset A/B**:

- Candidate pool: все существующие Local Peak local maxima, включая below-threshold; BGE-M3 embeddings, block size, context и smoothing остаются frozen.
- Hypothesis: Gold-valid и intra-topic peaks можно различить не magnitude-порогом, а небольшим набором inference-time discourse/structure features.
- Возможные заранее определённые признаки: speaker/Q&A change, пауза, explicit transition phrase, transcript-fragment indicator, window-edge/sign-off, persistence соседних smoothed positions.
- Design: source-level A->B и B->A; feature set, простой scoring rule и success metrics фиксируются до held-out evaluation.
- Primary metrics: candidate precision, Gold candidate recall, retained TP, rejected FP, internal-boundary F1 без mandatory starts, разрезы по speaker/example/organizational/protocol categories.
- Dataset C не используется. Dataset D остаётся untouched test после freeze архитектуры.
- Не выполнять threshold sweep: задача следующего эксперимента состоит в проверке separability, а не в поиске нового multiplier.

PRIMARY FAILURE MECHANISM: WEAK GOLD-BOUNDARY PEAKS ARE FIRST LOST AT THRESHOLD, BUT THE ROOT CAUSE IS POOR SEPARABILITY BETWEEN GOLD TRANSITIONS AND STRONG INTRA-TOPIC SEMANTIC CHANGES IN THE SINGLE COSINE-DISTANCE SIGNAL.

RECOMMENDED NEXT EXPERIMENT: A PRE-REGISTERED A/B-ONLY CANDIDATE SEPARABILITY STUDY THAT RE-RANKS FROZEN LOCAL MAXIMA WITH DISCOURSE/STRUCTURE FEATURES, WITHOUT THRESHOLD SWEEP OR DATASET C.
