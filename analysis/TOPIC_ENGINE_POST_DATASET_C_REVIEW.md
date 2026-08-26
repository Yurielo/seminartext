# Topic Engine Product/Algorithm Review после Dataset C

Дата: 2026-08-26

Статус: анализ существующих результатов. Новые запуски Topic Engine, parameter sweeps и изменения алгоритма не выполнялись.

Источники:

- `analysis/DATASET_C_BLIND_VALIDATION.md`
- `analysis/dataset_c/results/dataset_c_bge_m3_local_peak_blind.json`
- `analysis/dataset_c/results/dataset_c_bge_m3_pelt_blind.json`
- `analysis/BGE_M3_CHANGEPOINT_EXPERIMENT_DATASET_A.md`
- `analysis/BGE_M3_RUPTURES_EXPERIMENT_DATASET_A.md`
- `analysis/DATASET_B_FROZEN_VALIDATION.md`
- raw results и Gold benchmark Dataset A, B и C

## 1. Executive Summary

1. **Главный bottleneck Local Peak: boundary detection.** На Dataset C при допуске +/-2 есть 10 FN. Только один из них является убедительной ошибкой локализации (`66 -> 69`); остальные девять являются пропущенными переходами. По A/B/C вместе Local Peak имеет 61 FN против 31 FP.
2. **Локализация уже сравнительно сильна.** На C 14/24 Gold-boundary находятся в +/-2: 7 exact, 4 в +/-1 и 3 в +/-2. На A и B все засчитанные TP также расположены не дальше +/-2.
3. **Технические начала окон завышают видимое качество тематического детектора.** Local Peak всегда добавляет первый `segment_id` программно. На C это 6 из 14 TP. Без шести технических стартов метрики внутренних границ составляют P/R/F1 `0.444/0.444/0.444`, а не `0.583/0.583/0.583`.
4. **PELT эмпирически дополняет Local Peak, но слишком шумен.** Он спасает 6 из 10 FN Local Peak, то есть 60%, но относительно Local Peak создаёт 38 дополнительных FP, теряет 5 Local-Peak-only TP и даёт только +1 aggregate TP.
5. **Рост Local Peak F1 A -> B -> C частично смешан с изменением Gold-гранулярности.** Среднее число Gold-тем на примерно 12-минутное окно падает с `8.0` на A до `5.7` на B и `4.0` на C. Предсказаний при этом в среднем `4.3`, `4.3` и `4.0`. Поэтому C подтверждает жизнеспособность Local Peak, но не доказывает независимый от плотности тем рост качества.
6. **Архитектурный статус:** Local Peak можно назначить primary experimental candidate, но не production baseline. PELT следует сохранить как recall comparator/research branch. Данных достаточно для исследования gated hybrid, но недостаточно для реализации или продвижения простого объединения predictions.
7. **Следующий эксперимент с максимальной информационной ценностью:** read-only boundary-signal attribution audit на A/B. Он должен проверить, отсутствует ли сигнал у FN или сигнал есть, но его отбрасывают threshold/NMS/min-gap. Dataset C в выборе параметров больше не участвует.

Формальный PASS/FAIL не вводится: acceptance criteria до blind evaluation Dataset C не были установлены.

## 2. Local Peak error anatomy

### 2.1 Aggregate Dataset C

| Допуск | TP | FP | FN | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 7 | 17 | 17 | 0.292 | 0.292 | 0.292 |
| 1 | 11 | 13 | 13 | 0.458 | 0.458 | 0.458 |
| 2 | 14 | 10 | 10 | 0.583 | 0.583 | 0.583 |

### 2.2 True Positives при +/-2

| Окно | Gold | Prediction | Offset | Тип | Интерпретация |
|---|---:|---:|---:|---|---|
| 01 | 1 | 1 | 0 | technical window start | Добавляется алгоритмом детерминированно; не является доказательством semantic detection. |
| 01 | 83 | 85 | +2 | organizational return / explicit transition | Возврат после просьбы включить камеры локализован в допустимой области. |
| 05 | 373 | 373 | 0 | technical window start | Детерминированное начало окна. |
| 05 | 399 | 397 | -2 | gradual conceptual transition | Переход к рефреймингу найден немного раньше Gold. |
| 10 | 867 | 867 | 0 | technical window start | Детерминированное начало окна. |
| 10 | 940 | 940 | 0 | explicit verbal transition | Сильное «Перейдём к такой теме» найдено точно. |
| 10 | 966 | 968 | +2 | Q&A / interpretation transition | Переход от притчи к обсуждению её смысла найден рядом. |
| 14 | 1276 | 1276 | 0 | technical window start | Детерминированное начало окна. |
| 14 | 1336 | 1335 | -1 | explicit domain transition | Переход к структуре гексаграммы найден точно по смысловой области. |
| 14 | 1361 | 1360 | -1 | explicit conceptual transition | Переход к сильным и слабым позициям найден рядом. |
| 19 | 1738 | 1738 | 0 | technical window start | Детерминированное начало окна. |
| 19 | 1761 | 1762 | +1 | explicit topic transition | Переход к переводу Щуцкого локализован рядом. |
| 23 | 2156 | 2156 | 0 | technical window start | Детерминированное начало окна. |
| 23 | 2234 | 2235 | +1 | Q&A / work-plan transition | Заключительный практический блок и вопросы найдены рядом. |

Шесть технических стартов входят в benchmark корректно, но не измеряют способность Local Peak обнаруживать переход. После их исключения:

| Срез C | Gold | Pred | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Все границы | 24 | 24 | 14 | 10 | 10 | 0.583 | 0.583 | 0.583 |
| Только внутренние границы | 18 | 18 | 8 | 10 | 10 | 0.444 | 0.444 | 0.444 |

### 2.3 False Negatives при +/-2

| Окно | Gold | Ближайший LP | Distance | Тип причины | Объяснение |
|---|---:|---:|---:|---|---|
| 01 | 24 | 1 | 23 | explicit verbal transition / detection | Переход от введения к жизни в эпоху перемен не вызвал выбранного пика. |
| 01 | 66 | 69 | 3 | localization | Правильная смысловая область обнаружена, но пик на один ID вышел за допуск. |
| 01 | 79 | 85 | 6 | organizational transition / short topic | Короткая просьба включить камеры пропущена; prediction 85 уже относится к возврату в 83. |
| 05 | 431 | 416 | 15 | organizational transition / short topic | Короткий перерыв не получил кандидата поблизости. |
| 05 | 433 | 416 | 17 | explicit transition / adjacent short topic | Новая тема сразу после перерыва пропущена; пара 431/433 также конфликтует с `min_gap_segment_ids=3`. |
| 10 | 906 | 940 | 34 | Q&A transition | Вопрос о науке и нравственности не распознан как новая тема. |
| 14 | 1303 | 1327 | 24 | gradual semantic transition / long topic | Переход к целям жизни и самоценности развивается без резкого lexical shift. |
| 19 | 1808 | 1770 | 38 | strong explicit transition | Явный переход к практическим протоколам, мудрам и мышечному тестированию полностью пропущен. |
| 23 | 2181 | 2194 | 13 | gradual semantic transition / long topic | Полная коррекция использует лексику предыдущего практического блока и обнаруживается поздно. |
| 23 | 2214 | 2194 | 20 | Q&A transition / short topic | Практический вопрос о критерии завершения не создаёт выбранного локального пика. |

Распределение FN по механизму:

- Boundary localization: 1/10.
- Explicit/strong transition detection: 3/10 (`24`, `433`, `1808`).
- Organizational short topic: 2/10 (`79`, `431`).
- Q&A transition: 2/10 (`906`, `2214`).
- Gradual semantic transition: 2/10 (`1303`, `2181`).
- Technical window starts: 0 пропусков, поскольку они вставляются детерминированно.

### 2.4 False Positives при +/-2

| Окно | Prediction | Ближайший Gold | Distance | Тип причины | Объяснение |
|---|---:|---:|---:|---|---|
| 01 | 69 | 66 | 3 | localization counterpart | Это вторая сторона near-miss `66 -> 69`, а не самостоятельная ложная тема. |
| 05 | 416 | 431 | 15 | смена примера без смены темы | Пример внутри рефрейминга создаёт локальный semantic peak. |
| 05 | 465 | 433 | 32 | локальный пик внутри длинной темы | Частный пример дуальности и конец окна ошибочно выделены отдельно. |
| 10 | 981 | 966 | 15 | window-end / long-topic split | Продолжение обсуждения притчи в конце окна разделено повторно. |
| 14 | 1327 | 1336 | 9 | organizational artifact | Техническая реплика о микрофоне даёт резкий сигнал, но Gold не считает её темой. |
| 14 | 1345 | 1336 | 9 | смена примера без смены темы | Деталь структуры гексаграммы отделена от родительской темы. |
| 14 | 1371 | 1361 | 10 | локальный пик внутри длинной темы | Пример 64-й гексаграммы остаётся частью темы сильных и слабых позиций. |
| 19 | 1770 | 1761 | 9 | смена примера без смены темы | Деталь интерпретации древнекитайских образов ошибочно выделена отдельно. |
| 23 | 2194 | 2181 | 13 | procedural substep | Один шаг коррекции принят за новую тему. |
| 23 | 2257 | 2234 | 23 | Q&A subturn / window end | Отдельный ответ внутри общего Q&A ошибочно становится темой. |

Распределение FP по механизму:

- Локальные примеры и procedural substeps внутри темы: 6/10.
- Localization counterpart: 1/10.
- Organizational artifact: 1/10.
- Window-end split: 1/10.
- Q&A subturn: 1/10.

Итого на C Local Peak одновременно недодетектирует настоящие переходы и реагирует на внутритематические пики. Однако cross-dataset баланс ошибок показывает, что under-detection является более устойчивой и более крупной проблемой.

## 3. Boundary-distance analysis

Distance ниже является абсолютным расстоянием от каждого Gold до ближайшего Local Peak prediction. Один prediction может быть ближайшим к нескольким Gold, поэтому эта таблица диагностирует геометрию кандидатов, а не заменяет one-to-one benchmark matching.

| Окно | Gold | Ближайший prediction | Signed offset | Bin |
|---|---:|---:|---:|---|
| 01 | 1 | 1 | 0 | exact |
| 01 | 24 | 1 | -23 | >10 / нет prediction поблизости |
| 01 | 66 | 69 | +3 | +/-3-5 |
| 01 | 79 | 85 | +6 | +/-6-10 |
| 01 | 83 | 85 | +2 | +/-2 |
| 05 | 373 | 373 | 0 | exact |
| 05 | 399 | 397 | -2 | +/-2 |
| 05 | 431 | 416 | -15 | >10 / нет prediction поблизости |
| 05 | 433 | 416 | -17 | >10 / нет prediction поблизости |
| 10 | 867 | 867 | 0 | exact |
| 10 | 906 | 940 | +34 | >10 / нет prediction поблизости |
| 10 | 940 | 940 | 0 | exact |
| 10 | 966 | 968 | +2 | +/-2 |
| 14 | 1276 | 1276 | 0 | exact |
| 14 | 1303 | 1327 | +24 | >10 / нет prediction поблизости |
| 14 | 1336 | 1335 | -1 | +/-1 |
| 14 | 1361 | 1360 | -1 | +/-1 |
| 19 | 1738 | 1738 | 0 | exact |
| 19 | 1761 | 1762 | +1 | +/-1 |
| 19 | 1808 | 1770 | -38 | >10 / нет prediction поблизости |
| 23 | 2156 | 2156 | 0 | exact |
| 23 | 2181 | 2194 | +13 | >10 / нет prediction поблизости |
| 23 | 2214 | 2194 | -20 | >10 / нет prediction поблизости |
| 23 | 2234 | 2235 | +1 | +/-1 |

Распределение:

| Bin | Count | Доля Gold |
|---|---:|---:|
| exact | 7 | 29.2% |
| +/-1 | 4 | 16.7% |
| +/-2 | 3 | 12.5% |
| +/-3-5 | 1 | 4.2% |
| +/-6-10 | 1 | 4.2% |
| >10 | 8 | 33.3% |
| Нет prediction в окне вообще | 0 | 0.0% |

При operational definition «нет prediction поблизости» = нет кандидата в +/-10 таких Gold 8/24. Cumulative coverage составляет 58.3% в +/-2, 62.5% в +/-5 и 66.7% в +/-10.

Сравнение nearest-distance distributions:

| Dataset | Gold | exact | +/-1 | +/-2 | +/-3-5 | +/-6-10 | >10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 48 | 9 | 6 | 0 | 6 | 5 | 22 |
| B | 34 | 10 | 5 | 1 | 2 | 4 | 12 |
| C | 24 | 7 | 4 | 3 | 1 | 1 | 8 |

Ключевой вывод: когда Local Peak выбирает правильный переход, его точность позиции обычно достаточна. Проблема заключается не в постоянном сдвиге на несколько cue, а в отсутствии выбранного кандидата для целых типов переходов. На C один-to-one анализ даёт 1 localization error и 9 detection errors среди 10 FN.

## 4. PELT rescue analysis

Для каждого FN Local Peak проверен ближайший PELT prediction и one-to-one match при +/-2.

| Окно | LP FN | Тип | Ближайший PELT | Offset | Rescued в +/-2 |
|---|---:|---|---:|---:|---|
| 01 | 24 | explicit transition | 26 | +2 | да |
| 01 | 66 | LP localization miss | 64 | -2 | да |
| 01 | 79 | organizational short topic | 78 | -1 | да |
| 05 | 431 | organizational short topic | 430 | -1 | да |
| 05 | 433 | adjacent explicit transition | 430 | -3 | нет |
| 10 | 906 | Q&A transition | 908 | +2 | да |
| 14 | 1303 | gradual transition | 1301 | -2 | да |
| 19 | 1808 | strong explicit transition | 1811 | +3 | нет |
| 23 | 2181 | gradual transition | 2189 | +8 | нет |
| 23 | 2214 | Q&A transition | 2217 | +3 | нет |

Результат:

- Local Peak FN rescued by PELT: `6/10 = 60%`.
- Не спасены: `4/10 = 40%`.
- PELT-only Gold TP: 6.
- Local-Peak-only Gold TP: 5.
- Aggregate TP: Local Peak 14, PELT 15, разница всего +1.
- FP: Local Peak 10, PELT 48, разница +38.
- Цена полного перехода с Local Peak на PELT: 38 дополнительных FP ради одного дополнительного net TP.
- Если считать все шесть rescued FN как потенциальную ценность candidate channel, приходится отфильтровать 38 incremental FP, то есть `6.33` дополнительных FP на один rescued FN до применения gate.

Вывод: есть эмпирическое основание исследовать **gated rescue architecture**, потому что PELT покрывает разные типы пропусков Local Peak. Нет основания объединять outputs напрямую: raw PELT candidate stream имеет слишком низкую селективность и одновременно теряет пять TP Local Peak.

## 5. Cross-dataset patterns

### 5.1 Aggregate Local Peak A/B/C

| Dataset | Gold | Pred | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 48 | 26 | 15 | 11 | 33 | 0.577 | 0.312 | 0.405 |
| B | 34 | 26 | 16 | 10 | 18 | 0.615 | 0.471 | 0.533 |
| C | 24 | 24 | 14 | 10 | 10 | 0.583 | 0.583 | 0.583 |
| Pooled diagnostic | 106 | 76 | 45 | 31 | 61 | 0.592 | 0.425 | 0.495 |

Без обязательных первых границ каждого из 18 окон:

| Dataset | Internal Gold | Internal Pred | Internal TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 42 | 20 | 9 | 11 | 33 | 0.450 | 0.214 | 0.290 |
| B | 28 | 20 | 10 | 10 | 18 | 0.500 | 0.357 | 0.417 |
| C | 18 | 18 | 8 | 10 | 10 | 0.444 | 0.444 | 0.444 |

Pooled строка не является новой benchmark-оценкой: datasets имеют разную Gold-плотность и представлены всего тремя видео. Она нужна только для сравнения масштаба механизмов ошибок.

### 5.2 Engine-specific повторяющиеся ошибки

1. **Compression семантически похожих последовательных тем.** На A пропускаются каталоги уровней (`window_08`) и шаги протокола (`window_17`); на B похожая проблема возникает в практических упражнениях и типах эмоций (`window_06`, `11`, `20`, `25`); на C она видна в коррекционном протоколе (`2181`, `2214`). Повторяемая лексика снижает локальный cosine-discontinuity.
2. **Организационные и Q&A-переходы.** A пропускает передачи слова, обед и итоги дня; B пропускает знакомство, перерыв и переходы в практику; C пропускает `79`, `431`, `906`, `2214`. Это устойчивый cross-dataset класс.
3. **Внутритематические примеры дают FP.** На A narrative/protocol beats создают пики, на B участники и практические детали дробятся внутри Gold-тем, на C аналогичны `416`, `1345`, `1371`, `1770`, `2194`. Это вторичный, но повторяемый over-segmentation mechanism.
4. **Сильные verbal transitions не гарантируют пик.** Пропуски A/B включают явно объявленные этапы и переходы; на C особенно показательны `24`, `433`, `1808`. Embedding distance не заменяет discourse signal.
5. **Успешная локализация при наличии detection.** Exact/near matches преобладают среди TP на всех трёх datasets; большие систематические signed offsets не наблюдаются.

### 5.3 Dataset-specific ошибки и confounders

- **Dataset A:** самая высокая плотность Gold (`8.0` темы/окно), каталоги уровней, нумерованные protocol steps и сильное late under-detection. FN 33 при 26 predictions.
- **Dataset B:** повторяющаяся лексика эмоциональных состояний, длинные практические последовательности и отдельный документированный transcript glitch. Late recall Local Peak остаётся 0.125.
- **Dataset C:** философские gradual transitions, близкая пара коротких тем `431/433` и практический Q&A. При этом Gold-плотность заметно ниже, что уменьшает under-count pressure.
- **Position effect:** Local Peak recall early/middle/late равен A `0.450/0.250/0.167`, B `0.600/0.545/0.125`, C `0.727/0.333/0.571`. Поздняя слабость повторяется на A/B, но не на C, поэтому чистая гипотеза «алгоритм всегда ухудшается к концу окна» не подтверждается. Более вероятно взаимодействие позиции, плотности и семантической однородности.

## 6. Topic-density analysis

Все окна имеют продолжительность около 12 минут. `Gold/min` показывает плотность Gold-гранулярности, а не объективную сложность исходного видео.

| Dataset | Window | Минут | Gold | Pred | FP | FN | F1 | Gold/min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 01 | 12.09 | 7 | 4 | 2 | 5 | 0.364 | 0.579 |
| A | 04 | 12.13 | 8 | 3 | 1 | 6 | 0.364 | 0.660 |
| A | 08 | 12.09 | 9 | 5 | 2 | 6 | 0.429 | 0.744 |
| A | 12 | 12.04 | 9 | 4 | 2 | 7 | 0.308 | 0.747 |
| A | 17 | 12.11 | 9 | 5 | 1 | 5 | 0.571 | 0.743 |
| A | 22 | 11.92 | 6 | 5 | 3 | 4 | 0.364 | 0.503 |
| B | 01 | 12.03 | 4 | 4 | 2 | 2 | 0.500 | 0.333 |
| B | 06 | 12.39 | 6 | 2 | 0 | 4 | 0.500 | 0.484 |
| B | 11 | 12.10 | 6 | 4 | 2 | 4 | 0.400 | 0.496 |
| B | 15 | 12.02 | 5 | 5 | 1 | 1 | 0.800 | 0.416 |
| B | 20 | 12.07 | 5 | 5 | 3 | 3 | 0.400 | 0.414 |
| B | 25 | 12.08 | 8 | 6 | 2 | 4 | 0.571 | 0.662 |
| C | 01 | 12.04 | 5 | 3 | 1 | 3 | 0.500 | 0.415 |
| C | 05 | 12.01 | 4 | 4 | 2 | 2 | 0.500 | 0.333 |
| C | 10 | 12.01 | 4 | 4 | 1 | 1 | 0.750 | 0.333 |
| C | 14 | 12.11 | 4 | 6 | 3 | 1 | 0.600 | 0.330 |
| C | 19 | 12.06 | 3 | 3 | 1 | 1 | 0.667 | 0.249 |
| C | 23 | 12.07 | 4 | 4 | 2 | 2 | 0.500 | 0.331 |

Dataset-level summary:

| Dataset | Mean Gold/window | Mean Pred/window | Mean count error | Mean F1 |
|---|---:|---:|---:|---:|
| A | 8.00 | 4.33 | -3.67 | 0.400 |
| B | 5.67 | 4.33 | -1.33 | 0.529 |
| C | 4.00 | 4.00 | 0.00 | 0.586 |

Exploratory observations:

- По всем 18 окнам Pearson `r(F1, Gold count) = -0.481`, а `r(F1, Gold/min) = -0.483`.
- Корреляция `Gold count` и `Pred count` слаба: `r = 0.179`. Число выбранных peaks почти не растёт вслед за Gold-плотностью.
- Окна с 3-5 Gold-темами имеют mean F1 `0.580` (`n=9`); с 6-7 темами `0.407` (`n=4`); с 8-9 темами `0.449` (`n=5`).
- Внутри отдельных datasets знак density-correlation нестабилен: A `+0.364`, B `+0.011`, C `-0.495`. Это показывает сильный dataset confounding и не позволяет объявлять универсальную статистическую зависимость.
- Более устойчивый факт: с ростом Gold count растёт абсолютное число FN, тогда как predictions остаются в диапазоне 2-6. Local Peak ведёт себя как консервативный selector с недостаточной адаптацией количества тем.

Вывод является exploratory: `N=18`, только три исходных видео, а Gold-гранулярность могла различаться между разметками. Тем не менее плотность тем должна стать обязательным stratification factor в следующем эксперименте.

## 7. Primary bottleneck

Выбор: **B. Boundary detection**.

Подтверждение:

- На C среди 10 FN только 1 является genuine localization error; 9 переходов не детектированы корректным кандидатом.
- 8/24 Gold не имеют Local Peak prediction даже в +/-10.
- По A/B/C вместе: 61 FN против 31 FP.
- После исключения детерминированных стартов Local Peak находит только 27 из 88 внутренних Gold-boundary, pooled internal recall `0.307`.
- На A и B особенно заметен under-count: `-3.67` и `-1.33` темы на окно в среднем.
- Организационные, Q&A, gradual и repeated-vocabulary transitions повторно пропускаются в разных семинарах.

**Secondary bottleneck: C. Over-segmentation.** На C шесть FP возникают из-за примеров и procedural substeps внутри темы. Это объясняет, почему простое снижение threshold не является безопасным решением: оно может повысить recall ценой ещё большего granularity mismatch.

Boundary localization не является приоритетом следующей итерации. Улучшение привязки к cue не решит девять detection FN на C и большинство FN на A/B.

## 8. Next experiments

Ни один из экспериментов ниже в рамках этого review не выполняется. Dataset C исключается из parameter selection и model selection.

### Priority 1. Boundary-signal attribution audit

**Hypothesis:** большинство FN возникают либо потому, что в Gold-области нет выраженного bge-m3 change signal, либо потому, что существующий сигнал отбрасывают threshold, local-maximum selection или min-gap. Эти механизмы требуют разных архитектурных решений.

**Проверяется:** raw smoothed score и rank каждого Gold-boundary до selection; наличие кандидата до/после threshold; причина удаления NMS/min-gap; разрезы по типу перехода, позиции и Gold-density.

**Данные:** Dataset A и B. Использовать существующие Gold и frozen embeddings/signals. C только как уже опубликованный descriptive reference, без вычисления критериев по нему.

**Разрешено:** добавить read-only instrumentation/analysis script; вручную или независимо разметить boundary types A/B; вычислить ranks, coverage и effect sizes.

**Запрещено:** менять embeddings, block size, context, smoothing, threshold, min-gap, maximum boundaries или production code.

**Метрика успеха:** получить однозначное разложение FN на `no signal`, `below threshold`, `not local maximum`, `suppressed by min-gap/NMS`, повторяемое на A и B; отдельно report top-k candidate recall и AUC/rank по типам переходов.

**Риск overfitting:** низкий, потому что алгоритм и predictions не меняются. Риск остаётся в субъективной классификации типов, поэтому annotator не должен видеть scores.

**Информационная ценность:** максимальная. Эксперимент определит, нужен ли новый semantic/discourse feature или достаточно менять selector.

### Priority 2. PELT rescue separability study

**Hypothesis:** PELT-only true candidates отличаются от PELT FP по заранее доступным признакам: signal rank/persistence, поддержка Local Peak в соседстве, explicit discourse cue, пауза, speaker/Q&A change или устойчивость на соседнем масштабе.

**Проверяется:** можно ли gate-ом спасать часть FN Local Peak без переноса полного PELT over-segmentation.

**Данные:** A/B с source-level split. Один источник используется для определения простого gate, второй только для frozen confirmation; затем роли меняются как diagnostic cross-check. C не используется.

**Разрешено:** один заранее описанный простой scoring/gating rule и только признаки, доступные без Gold во время inference.

**Запрещено:** raw union, ручное исправление candidates, выбор правил по C, изменение Local Peak/PELT base parameters, сложный classifier при текущем объёме данных.

**Метрика успеха:** held-out incremental candidate precision, число rescued LP FN, retention Local Peak TP, delta recall и delta F1. Минимальный признак перспективности: положительный delta F1 в обоих направлениях A->B и B->A и added-candidate precision выше 0.5.

**Риск overfitting:** средний. A/B уже изучались, выбор признаков может отражать известные ошибки. Нужна preregistration до расчёта held-out fold.

**Информационная ценность:** высокая. На C PELT rescues 60% LP FN, но raw цена 6.33 incremental FP на rescue; separability является критическим неизвестным.

### Priority 3. Predeclared multi-scale Local Peak ablation

**Hypothesis:** единый 15-секундный scale недостаточен одновременно для short topics и gradual transitions; устойчивость пика на двух временных масштабах может повысить detection без простого снижения threshold.

**Проверяется:** меняется ли recall по boundary types и high-density windows при одном дополнительном заранее выбранном масштабе.

**Данные:** A/B с grouped source-level evaluation. Выполнять только после Priority 1, если audit покажет отсутствие сигнала у существенной доли FN.

**Разрешено:** изменить только block scale в небольшом preregistered ablation и сравнить с frozen 15 s. Остальные параметры и embeddings фиксированы.

**Запрещено:** grid search по threshold/context/smoothing/min-gap, per-window параметры, выбор конфигурации по C.

**Метрика успеха:** Pareto improvement precision/recall на обоих A/B, улучшение internal-boundary recall и recall high-density окон без роста topic-count error. Результат должен быть стабильным по boundary types, а не только aggregate F1.

**Риск overfitting:** средний. Даже малый scale ablation может превратиться в tuning; число вариантов должно быть зафиксировано до запуска.

**Информационная ценность:** средняя и условная. Если Priority 1 покажет, что сигналы уже существуют, multi-scale не нужен и следует исследовать selector.

## 9. Anti-overfitting dataset strategy

1. **Dataset A и B становятся development evidence.** Оба уже многократно анализировались. Их можно использовать для разработки и grouped/source-level cross-validation, но нельзя снова называть untouched validation.
2. **Dataset C остаётся used validation dataset.** Его predictions, FN/FP и типы ошибок известны. На C запрещено выбирать параметры, features, gates, thresholds и архитектуру. Будущие показатели C могут показываться только как историческая frozen reference, не как новое доказательство переносимости.
3. **Dataset D нужен как новый untouched test.** Его следует определить сейчас, до реализации следующего кандидата: заморозить source-selection policy, выбрать новые видео, подготовить окна по механическому правилу и выполнить независимую ручную Gold-разметку без доступа к predictions.
4. **Лучше включить в D два новых видео из разных семинаров.** Это доведёт общий набор до roadmap-цели в пять источников и уменьшит риск зависимости от одного лектора или предмета. Для каждого видео целесообразны 6-8 окон с заранее стратифицированной topic-density.
5. **Gold D нужно захешировать и закрыть до разработки, но Topic Engine на D не запускать.** A/B используются для всех решений. После freeze одной архитектуры, параметров, acceptance criteria и analysis plan выполняется ровно один test-run D.
6. **Acceptance criteria задаются до D.** Помимо P/R/F1 +/-0/1/2 включить internal-boundary metrics без технических стартов, recall по density/position/type, topic-count error и FP per rescued boundary.
7. **Разделить роли.** Gold-author не смотрит predictions; algorithm developer не меняет Gold; итоговый evaluator проверяет hashes, one-run protocol и полный error inventory.
8. **Не использовать цикл C tuning.** Формула процесса: `A/B development -> freeze -> one D test`. C остаётся архивной точкой, а не ступенью повторной оптимизации.

## 10. Architectural recommendation

### 1. Достаточно ли данных, чтобы повысить Local Peak до primary candidate?

**Да, до primary experimental candidate. Нет, до production baseline.** Основания: лучший F1 на B и C, стабильный Precision около 0.58-0.62, 76 predictions против 106 Gold без PELT-подобного взрыва FP. Ограничения: только три исходных видео, density confound, отсутствие заранее заданных acceptance criteria и internal F1 C всего 0.444.

### 2. Следует ли сохранить PELT как comparator/research branch?

**Да.** PELT стабильно предоставляет другой recall-oriented error profile и rescues 6/10 FN Local Peak на C. Как standalone engine он неприемлем без отдельного решения over-segmentation: C Precision 0.238 и 63 predictions при 24 Gold.

### 3. Есть ли достаточно доказательств, чтобы исследовать hybrid Local Peak + PELT?

**Да, чтобы исследовать gated rescue; нет, чтобы реализовать raw union или принять hybrid как архитектуру.** Rescue rate 60% является реальным complementary signal. Одновременно +38 FP и пять потерянных Local-Peak-only TP показывают, что ценность полностью зависит от separability gate. Сначала нужны Priority 1 и Priority 2 на A/B.

Решение review:

- Primary experimental path: Local Peak.
- Recall comparator: PELT.
- Следующий шаг: Priority 1 read-only attribution audit.
- Production promotion: отложить до frozen test на Dataset D.

## 11. Open questions

1. Одинаково ли Product Owner применял Gold-гранулярность на A, B и C? Разница `8.0 -> 5.7 -> 4.0` тем на окно может быть как свойством материала, так и annotation-policy drift.
2. Следует ли техническое начало окна включать в primary boundary metric, если engine добавляет его без semantic decision? Рекомендуется показывать обе метрики.
3. Должны ли короткие организационные вставки, Q&A-переходы и смена участника всегда становиться пользовательскими темами, или для них нужен отдельный event type?
4. Какие inference-признаки реально доступны: speaker changes, паузы, punctuation, SRT confidence, audio VAD? Без ответа нельзя честно спроектировать rescue gate.
5. Как оценивать переход внутри одного SRT-cue, где точная Gold-локализация технически невозможна?
6. Является ли `min_gap_segment_ids=3` допустимым ограничением при Gold-парах вроде `431/433`, или benchmark должен отдельно учитывать structurally unrepresentable pairs?
7. Какой состав Dataset D даст domain shift: два новых лектора, два новых предмета или сочетание лекции и Q&A-heavy семинара?
8. Какие acceptance criteria Product Owner готов утвердить до открытия Dataset D?
