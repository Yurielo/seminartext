# «Стресс код» — итоговая семантическая структура для авторской проверки

**Статус: проект на DOMAIN_REVIEW, НЕ ПРИНЯТО.** Подготовлено как читаемая проекция уже существующего QA-пакета; этот документ не является новой семантической разметкой, решением владельца или Canonical Knowledge.

**Источник:** PR #121, commit `eac0d004d63923f46205a2721775458e891140e0`; `analysis/issue_68_vertical_slice/domain_review_v1/domain_review_qa.json` (Git blob `dbb9beeed1972b6adb9064fbd3d89aad194429d7`).

## Краткая сводка

- Смысловых единиц: **182** (все QA REVIEW_CLEAR, но семантически PROVISIONAL).
- Кандидатов в понятия: **22** (все ожидают итогового авторского принятия).
- Связей тема → понятие в итоговой QA-проекции: **246**, из них **239** технически CLEAR и **7** отложены. QA CLEAR ≠ семантическое ACCEPT.
- Активных материальных исключений для пакетной проверки: **0**; 7 отложенных связей не принимаются автоматически.
- Выборочная проверка машинной транскрипции: **2** исключения.
- Evidence для 4 видео; 3 зарегистрированных документа без Evidence в текущем пакете. Полное покрытие семи источников не заявлено.

**Для решения:** проверить общую структуру и границы тем, список понятий и принципиальные связи. Подтверждение финального DOMAIN_REVIEW — отдельное явное решение владельца. Все утверждения семинара представлены как авторский материал, а не независимая научная верификация.

## 1. Кандидаты в понятия (22)

| № | Понятие | Исходные термины | Evidence-ссылок | Статус |
|---:|---|---|---:|---|
| 1 | Стресс | Стресс, стресс, Стресса, стресса, стрессом | 52 | PROVISIONAL |
| 2 | Кинезиология | кинезиологии, кинезиологический, кинезиология | 8 | PROVISIONAL |
| 3 | Мышечное тестирование | мышечного тестирования, Мышечное тестирование, мышечное тестирование | 4 | PROVISIONAL |
| 4 | Коррекция | коррекции, коррекцию, Коррекция, коррекция | 45 | PROVISIONAL |
| 5 | Протокол работы | Протокол, протокол, протокола, протоколу | 9 | PROVISIONAL |
| 6 | Эмоции | Эмоции, эмоции, Эмоций, эмоций, Эмоциональное, эмоциональное, Эмоциональный, эмоциональный | 39 | PROVISIONAL |
| 7 | Нервная система | Нервная Система, Нервная система, нервная система, нервной системы | 8 | PROVISIONAL |
| 8 | Нейронные связи и сети | Нейронные сети, Нервная сеть | 4 | PROVISIONAL |
| 9 | Адаптация | адаптации, адаптация | 3 | PROVISIONAL |
| 10 | Мозг | Мозг, мозг, мозга | 12 | PROVISIONAL |
| 11 | Полушария головного мозга | полушарий, полушария | 3 | PROVISIONAL |
| 12 | Меридианы | Меридиан, меридиан, меридианов, Меридианы, меридианы | 16 | PROVISIONAL |
| 13 | Движения глаз | движения глаз | 3 | PROVISIONAL |
| 14 | ДПДГ | ДПДГ | 6 | PROVISIONAL |
| 15 | Глазодвигательные мышцы | Глазодвигательная, Глазодвигательные, глазодвигательные | 5 | PROVISIONAL |
| 16 | Уровни развития сознания по Дэвиду Хокинсу | Уровни сознания | 1 | PROVISIONAL |
| 17 | Три уровня осознания: сознание, подсознание и тело | Уровень Осознавания, Уровни Осознания, Уровни сознания, уровни сознания | 6 | PROVISIONAL |
| 18 | Подсознание | Подсознание, подсознание, Подсознанием, подсознанием | 12 | PROVISIONAL |
| 19 | Память | Воспоминания, воспоминания, запоминание, памяти, Память, память | 15 | PROVISIONAL |
| 20 | Травма | Травма, травма | 5 | PROVISIONAL |
| 21 | Психосоматика | Психосоматика, психосоматика | 2 | PROVISIONAL |
| 22 | Цель жизни | цель жизни, жизненные цели, цели жизни | 1 | PROVISIONAL |

## 2. Тематическая структура (182 смысловые единицы)

Указаны точные времена и диапазоны слов в текущих ревизиях источников. Статус всех строк: **QA REVIEW_CLEAR / semantic PROVISIONAL**.

### source_video_002 — 86 тем

| № | Тема | Время | Canonical Word range | Topic ID |
|---:|---|---|---|---|
| 1 | Начало второго дня: переход от теории кинезиологии к практике | 00:00:04.950–00:01:13.200 | transcript_revision_video_002_r1:word:000000 → transcript_revision_video_002_r1:word:000066 | `issue_68_video_002_topic_proposal_001` |
| 2 | Мануальное мышечное тестирование и реакция мышц на стресс | 00:01:13.600–00:02:21.598 | transcript_revision_video_002_r1:word:000067 → transcript_revision_video_002_r1:word:000169 | `issue_68_video_002_topic_proposal_002` |
| 3 | Претесты и выбор передней порции дельтовидной мышцы | 00:02:21.618–00:04:48.490 | transcript_revision_video_002_r1:word:000170 → transcript_revision_video_002_r1:word:000402 | `issue_68_video_002_topic_proposal_003a` |
| 4 | Очное и дистанционное тестирование: получение индивидуальной информации | 00:04:48.490–00:08:07.950 | transcript_revision_video_002_r1:word:000403 → transcript_revision_video_002_r1:word:000724 | `issue_68_video_002_topic_proposal_003b` |
| 5 | Передняя порция дельтовидной мышцы: анатомия и техника тестирования | 00:08:11.425–00:09:59.970 | transcript_revision_video_002_r1:word:000725 → transcript_revision_video_002_r1:word:000896 | `issue_68_video_002_topic_proposal_003c` |
| 6 | Дыхание, вода и передача сигналов нервной системой | 00:10:02.023–00:13:39.670 | transcript_revision_video_002_r1:word:000897 → transcript_revision_video_002_r1:word:001218 | `issue_68_video_002_topic_proposal_003d` |
| 7 | Разбор домашнего мышечного тестирования: различение сильного и слабого ответа | 00:13:40.091–00:18:19.443 | transcript_revision_video_002_r1:word:001219 → transcript_revision_video_002_r1:word:001712 | `issue_68_video_002_topic_proposal_004` |
| 8 | Сильный и слабый мышечный ответ как индикатор стресса | 00:18:19.464–00:20:46.358 | transcript_revision_video_002_r1:word:001713 → transcript_revision_video_002_r1:word:001920 | `issue_68_video_002_topic_proposal_005` |
| 9 | Пример коррекции стресса и принцип мышечного ответа в кинезиологии | 00:20:46.418–00:23:38.277 | transcript_revision_video_002_r1:word:001921 → transcript_revision_video_002_r1:word:002201 | `issue_68_video_002_topic_proposal_006` |
| 10 | Претест «очищение»: восстановление нормотонуса мышцы | 00:23:42.407–00:27:49.750 | transcript_revision_video_002_r1:word:002202 → transcript_revision_video_002_r1:word:002586 | `issue_68_video_002_topic_proposal_007` |
| 11 | Претест «перегрузка» и коррекция «переключение» | 00:27:49.810–00:35:46.134 | transcript_revision_video_002_r1:word:002587 → transcript_revision_video_002_r1:word:003418 | `issue_68_video_002_topic_proposal_008` |
| 12 | Претест «блокировка»: состояние угрозы | 00:35:46.194–00:36:10.142 | transcript_revision_video_002_r1:word:003419 → transcript_revision_video_002_r1:word:003446 | `issue_68_video_002_topic_proposal_009` |
| 13 | Претест «блокировка»: диагностика и коррекция перенапряжения | 00:36:13.994–00:37:46.037 | transcript_revision_video_002_r1:word:003447 → transcript_revision_video_002_r1:word:003556 | `issue_68_video_002_topic_proposal_010` |
| 14 | Баланс поляризации: коррекция дыханием через ноздри | 00:37:46.077–00:42:40.175 | transcript_revision_video_002_r1:word:003557 → transcript_revision_video_002_r1:word:003928 | `issue_68_video_002_topic_proposal_011` |
| 15 | Коррекция поляризации через меридианы и завершение претестов | 00:42:40.195–00:47:36.911 | transcript_revision_video_002_r1:word:003929 → transcript_revision_video_002_r1:word:004430 | `issue_68_video_002_topic_proposal_012` |
| 16 | Возраст начала прямого мышечного тестирования у детей | 00:47:36.931–00:48:37.564 | transcript_revision_video_002_r1:word:004431 → transcript_revision_video_002_r1:word:004535 | `issue_68_video_002_topic_proposal_013a` |
| 17 | Работа без осознанного ответа: ограничения текущего метода и альтернативы | 00:48:40.450–00:51:34.472 | transcript_revision_video_002_r1:word:004536 → transcript_revision_video_002_r1:word:004853 | `issue_68_video_002_topic_proposal_013b` |
| 18 | Вопросы по мышечному тестированию и отработка претестов | 00:51:42.478–00:54:26.660 | transcript_revision_video_002_r1:word:004854 → transcript_revision_video_002_r1:word:005115 | `issue_68_video_002_topic_proposal_014a` |
| 19 | Перерыв на гимнастику: перекрёстный шаг и баланс полушарий | 00:54:26.660–00:57:48.646 | transcript_revision_video_002_r1:word:005116 → transcript_revision_video_002_r1:word:005352 | `issue_68_video_002_topic_proposal_014b` |
| 20 | Дистанционная работа: эффективность и поиск научного объяснения | 00:57:51.350–00:59:59.749 | transcript_revision_video_002_r1:word:005353 → transcript_revision_video_002_r1:word:005508 | `issue_68_video_002_topic_proposal_014c` |
| 21 | Очный мышечный эксперимент с мысленной похвалой и критикой | 00:59:59.769–01:03:01.457 | transcript_revision_video_002_r1:word:005509 → transcript_revision_video_002_r1:word:005839 | `issue_68_video_002_topic_proposal_015a` |
| 22 | Влияние мыслей на состояние человека и понятие аутоагрессии | 01:03:01.538–01:04:19.015 | transcript_revision_video_002_r1:word:005840 → transcript_revision_video_002_r1:word:005969 | `issue_68_video_002_topic_proposal_015b` |
| 23 | Проявления аутоагрессии и саморазрушающего поведения | 01:04:19.055–01:06:52.208 | transcript_revision_video_002_r1:word:005970 → transcript_revision_video_002_r1:word:006197 | `issue_68_video_002_topic_proposal_015c` |
| 24 | Сила мысли: совпадения и ощущение чужого взгляда | 01:06:52.228–01:08:00.712 | transcript_revision_video_002_r1:word:006198 → transcript_revision_video_002_r1:word:006328 | `issue_68_video_002_topic_proposal_016a` |
| 25 | Представления об энергии в разных культурах и невидимые формы энергии | 01:08:00.732–01:10:32.521 | transcript_revision_video_002_r1:word:006329 → transcript_revision_video_002_r1:word:006596 | `issue_68_video_002_topic_proposal_016b` |
| 26 | Строение материи: от органов и клеток к атомам и субатомным частицам | 01:10:34.131–01:13:15.317 | transcript_revision_video_002_r1:word:006597 → transcript_revision_video_002_r1:word:006827 | `issue_68_video_002_topic_proposal_017` |
| 27 | Материя и человек как энергетические системы | 01:13:15.598–01:16:33.763 | transcript_revision_video_002_r1:word:006828 → transcript_revision_video_002_r1:word:007061 | `issue_68_video_002_topic_proposal_018a` |
| 28 | Восприятие энергии органами чувств | 01:16:33.824–01:18:54.026 | transcript_revision_video_002_r1:word:007062 → transcript_revision_video_002_r1:word:007329 | `issue_68_video_002_topic_proposal_018b` |
| 29 | Получение, обработка и передача информации как потоки энергии | 01:18:54.046–01:20:18.716 | transcript_revision_video_002_r1:word:007330 → transcript_revision_video_002_r1:word:007503 | `issue_68_video_002_topic_proposal_019` |
| 30 | Задание: классификация входящей, внутренней и производимой энергии | 4831.481–4865.015 | transcript_revision_video_002_r1:word:007526 → transcript_revision_video_002_r1:word:007581 | `issue_68_video_002_topic_proposal_020a` |
| 31 | Входящая энергия и её источники во взаимодействии человека с окружающей средой | 01:21:12.030–01:24:23.617 | transcript_revision_video_002_r1:word:007589 → transcript_revision_video_002_r1:word:007865 | `issue_68_video_002_topic_proposal_020b` |
| 32 | Внутренняя энергия человека: химическая, электрическая и магнитная | 01:24:23.677–01:26:12.280 | transcript_revision_video_002_r1:word:007866 → transcript_revision_video_002_r1:word:008034 | `issue_68_video_002_topic_proposal_021` |
| 33 | Энергетические структуры человека: меридианы, чакры и аура | 01:26:12.581–01:26:59.917 | transcript_revision_video_002_r1:word:008035 → transcript_revision_video_002_r1:word:008095 | `issue_68_video_002_topic_proposal_022a` |
| 34 | Исходящая энергия человека: мысли, эмоции, тепло и звук | 01:26:59.957–01:27:35.534 | transcript_revision_video_002_r1:word:008096 → transcript_revision_video_002_r1:word:008140 | `issue_68_video_002_topic_proposal_022b` |
| 35 | Энергетический обмен человека и формирование реальности | 01:27:45.229–01:29:16.198 | transcript_revision_video_002_r1:word:008159 → transcript_revision_video_002_r1:word:008353 | `issue_68_video_002_topic_proposal_023b` |
| 36 | Квантовая связанность: общее поле и влияние на расстоянии | 01:29:17.600–01:33:09.006 | transcript_revision_video_002_r1:word:008354 → transcript_revision_video_002_r1:word:008756 | `issue_68_video_002_topic_proposal_024` |
| 37 | Материальность мыслей и след действий и намерений во Вселенной | 01:33:09.106–01:34:07.788 | transcript_revision_video_002_r1:word:008757 → transcript_revision_video_002_r1:word:008876 | `issue_68_video_002_topic_proposal_025a` |
| 38 | Мышечный тест как способ проверки истинности утверждений | 01:34:07.828–01:34:43.668 | transcript_revision_video_002_r1:word:008877 → transcript_revision_video_002_r1:word:008941 | `issue_68_video_002_topic_proposal_025b` |
| 39 | Непрожитые эмоции и генетическая передача эмоциональных программ | 01:34:43.688–01:35:31.009 | transcript_revision_video_002_r1:word:008942 → transcript_revision_video_002_r1:word:009030 | `issue_68_video_002_topic_proposal_025c` |
| 40 | Макс Планк о материи, как проявлении Силы | 01:35:31.049–01:36:35.293 | transcript_revision_video_002_r1:word:009031 → transcript_revision_video_002_r1:word:009133 | `issue_68_video_002_topic_proposal_026` |
| 41 | Выводы о материи, энергии и разумном начале | 01:36:37.660–01:37:33.913 | transcript_revision_video_002_r1:word:009134 → transcript_revision_video_002_r1:word:009213 | `issue_68_video_002_topic_proposal_027` |
| 42 | Квантовая связанность, энергия и намерение в работе на расстоянии | 01:37:34.034–01:39:02.396 | transcript_revision_video_002_r1:word:009214 → transcript_revision_video_002_r1:word:009345 | `issue_68_video_002_topic_proposal_028` |
| 43 | Примеры применения кинезиологии и резонансных техник на расстоянии | 01:39:02.496–01:40:26.019 | transcript_revision_video_002_r1:word:009346 → transcript_revision_video_002_r1:word:009473 | `issue_68_video_002_topic_proposal_029a` |
| 44 | Введение в дистанционное тестирование и выбор метода самотеста | 01:40:26.080–01:41:21.518 | transcript_revision_video_002_r1:word:009474 → transcript_revision_video_002_r1:word:009558 | `issue_68_video_002_topic_proposal_029b` |
| 45 | Метод сцепленных звеньев: техника различения сильного и слабого ответа | 01:41:21.538–01:44:23.133 | transcript_revision_video_002_r1:word:009559 → transcript_revision_video_002_r1:word:009832 | `issue_68_video_002_topic_proposal_029c` |
| 46 | Метод одной руки: техника и преимущества самотестирования | 01:44:23.173–01:48:04.550 | transcript_revision_video_002_r1:word:009833 → transcript_revision_video_002_r1:word:010249 | `issue_68_video_002_topic_proposal_030` |
| 47 | Разбор результатов самотестирования: усилие, контроль и расслабление | 01:48:10.640–01:49:51.727 | transcript_revision_video_002_r1:word:010250 → transcript_revision_video_002_r1:word:010444 | `issue_68_video_002_topic_proposal_031` |
| 48 | Самотестирование указательного пальца с участием второй руки | 01:49:51.747–01:52:02.915 | transcript_revision_video_002_r1:word:010445 → transcript_revision_video_002_r1:word:010664 | `issue_68_video_002_topic_proposal_032a` |
| 49 | Метод кольца: два варианта самотестирования | 01:52:02.955–01:53:25.506 | transcript_revision_video_002_r1:word:010665 → transcript_revision_video_002_r1:word:010791 | `issue_68_video_002_topic_proposal_032b` |
| 50 | Тестирование лучевого сгибателя кисти | 01:53:25.566–01:56:23.640 | transcript_revision_video_002_r1:word:010792 → transcript_revision_video_002_r1:word:011056 | `issue_68_video_002_topic_proposal_032c` |
| 51 | Освоение мышечного тестирования: терпение, практика и мотивация | 01:56:23.720–02:00:34.864 | transcript_revision_video_002_r1:word:011057 → transcript_revision_video_002_r1:word:011506 | `issue_68_video_002_topic_proposal_034` |
| 52 | Дисциплина как основа результата в обучении | 02:00:41.150–02:02:21.751 | transcript_revision_video_002_r1:word:011507 → transcript_revision_video_002_r1:word:011657 | `issue_68_video_002_topic_proposal_035` |
| 53 | Тестирование по изображению: восприятие сильного и слабого ответа | 02:02:21.771–02:08:43.557 | transcript_revision_video_002_r1:word:011658 → transcript_revision_video_002_r1:word:012186 | `issue_68_video_002_topic_proposal_036` |
| 54 | Проекция человека: дистанционное тестирование и коррекция | 02:08:43.577–02:11:36.098 | transcript_revision_video_002_r1:word:012187 → transcript_revision_video_002_r1:word:012516 | `issue_68_video_002_topic_proposal_038a` |
| 55 | Фантом человека: дистанционная работа и возвращение в тело | 02:11:41.154–02:16:27.311 | transcript_revision_video_002_r1:word:012517 → transcript_revision_video_002_r1:word:013057 | `issue_68_video_002_topic_proposal_038b` |
| 56 | Практика тестирования проекции человека | 02:16:27.351–02:18:43.887 | transcript_revision_video_002_r1:word:013058 → transcript_revision_video_002_r1:word:013226 | `issue_68_video_002_topic_proposal_039a` |
| 57 | Практика тестирования фантома и его возвращения | 02:18:43.927–02:20:55.740 | transcript_revision_video_002_r1:word:013227 → transcript_revision_video_002_r1:word:013353 | `issue_68_video_002_topic_proposal_039b` |
| 58 | Фасциальное тестирование: принцип, техника и преимущества | 02:20:55.760–02:27:30.060 | transcript_revision_video_002_r1:word:013354 → transcript_revision_video_002_r1:word:014008 | `issue_68_video_002_topic_proposal_041` |
| 59 | Краниосакральный ритм: ощущение, калибровка и дистанционное тестирование | 02:27:30.140–02:36:34.799 | transcript_revision_video_002_r1:word:014009 → transcript_revision_video_002_r1:word:014840 | `issue_68_video_002_topic_proposal_044` |
| 60 | Обратная связь и применение освоенных методов тестирования онлайн | 02:36:35.300–02:37:52.969 | transcript_revision_video_002_r1:word:014841 → transcript_revision_video_002_r1:word:014954 | `issue_68_video_002_topic_proposal_046a` |
| 61 | Мышечное тестирование как основной инструмент кинезиологии | 02:38:35.185–02:38:45.662 | transcript_revision_video_002_r1:word:015028 → transcript_revision_video_002_r1:word:015046 | `issue_68_video_002_topic_proposal_046c` |
| 62 | Суррогатное тестирование через ассистента: контактная и дистанционная работа | 02:40:00.000–02:44:43.800 | transcript_revision_video_002_r1:word:015124 → transcript_revision_video_002_r1:word:015549 | `issue_68_video_002_topic_proposal_049` |
| 63 | Тестирование по доверенности: проведение коррекции, передача результата и безопасность | 02:44:47.342–02:49:29.857 | transcript_revision_video_002_r1:word:015550 → transcript_revision_video_002_r1:word:016012 | `issue_68_video_002_topic_proposal_052` |
| 64 | Настройка намерения на клиента и контрольные вопросы | 02:49:29.877–02:51:24.048 | transcript_revision_video_002_r1:word:016013 → transcript_revision_video_002_r1:word:016217 | `issue_68_video_002_topic_proposal_053a` |
| 65 | Завершение механики тестирования и выбор подходящего метода | 02:51:24.068–02:52:37.884 | transcript_revision_video_002_r1:word:016218 → transcript_revision_video_002_r1:word:016331 | `issue_68_video_002_topic_proposal_053b` |
| 66 | Согласие на коррекцию и ответственность за решение | 02:52:37.904–02:53:43.397 | transcript_revision_video_002_r1:word:016332 → transcript_revision_video_002_r1:word:016427 | `issue_68_video_002_topic_proposal_053c` |
| 67 | Работа с животными методом «Эмоциональный код»: примеры с кошками | 02:53:43.437–02:58:01.725 | transcript_revision_video_002_r1:word:016428 → transcript_revision_video_002_r1:word:016879 | `issue_68_video_002_topic_proposal_055` |
| 68 | Работа с животными методом «Эмоциональный код»: примеры со слоном и телёнком | 02:58:04.291–02:59:13.278 | transcript_revision_video_002_r1:word:016880 → transcript_revision_video_002_r1:word:016999 | `issue_68_video_002_topic_proposal_056a` |
| 69 | Тестирование по стрессу без вопроса: поиск уровня для коррекции | 02:59:16.641–03:03:33.454 | transcript_revision_video_002_r1:word:017000 → transcript_revision_video_002_r1:word:017428 | `issue_68_video_002_topic_proposal_056b` |
| 70 | Тестирование посредством вопроса: интерпретация сильного и слабого ответа | 03:03:33.594–03:05:51.629 | transcript_revision_video_002_r1:word:017429 → transcript_revision_video_002_r1:word:017640 | `issue_68_video_002_topic_proposal_056c` |
| 71 | Сравнение двух способов интерпретации результатов мышечного теста | 03:05:51.689–03:07:54.887 | transcript_revision_video_002_r1:word:017641 → transcript_revision_video_002_r1:word:017822 | `issue_68_video_002_topic_proposal_056d` |
| 72 | Разрешение на работу: готовность, ответственность и польза от сессии | 03:09:14.718–03:21:49.242 | transcript_revision_video_002_r1:word:017930 → transcript_revision_video_002_r1:word:019375 | `issue_68_video_002_topic_proposal_061` |
| 73 | Вопросы безопасности: проверка допуска к сессии | 03:21:49.282–03:24:43.531 | transcript_revision_video_002_r1:word:019376 → transcript_revision_video_002_r1:word:019633 | `issue_68_video_002_topic_proposal_064` |
| 74 | Постановка темы сессии через работу со стрессом «подумай о» | 03:24:43.551–03:28:33.598 | transcript_revision_video_002_r1:word:019634 → transcript_revision_video_002_r1:word:020046 | `issue_68_video_002_topic_proposal_065a` |
| 75 | Позитивная формулировка запроса и переход к центрированному состоянию | 03:28:33.618–03:37:44.641 | transcript_revision_video_002_r1:word:020047 → transcript_revision_video_002_r1:word:020803 | `issue_68_video_002_topic_proposal_065b` |
| 76 | Гимнастика для мозга и повторение способов постановки темы сессии | 03:37:44.701–03:42:08.307 | transcript_revision_video_002_r1:word:020804 → transcript_revision_video_002_r1:word:021070 | `issue_68_video_002_topic_proposal_065c` |
| 77 | Субъективная шкала дискомфорта и фиксация результата коррекции | 03:42:08.387–03:47:55.797 | transcript_revision_video_002_r1:word:021071 → transcript_revision_video_002_r1:word:021715 | `issue_68_video_002_topic_proposal_072a` |
| 78 | Притча о двух волках как иллюстрация внимания и центрированности | 03:47:55.897–03:51:58.420 | transcript_revision_video_002_r1:word:021716 → transcript_revision_video_002_r1:word:022090 | `issue_68_video_002_topic_proposal_072b` |
| 79 | Объективная оценка проблемы: уровни негативной и позитивной эмоциональной энергии | 03:51:58.440–03:58:12.087 | transcript_revision_video_002_r1:word:022091 → transcript_revision_video_002_r1:word:022624 | `issue_68_video_002_topic_proposal_077a` |
| 80 | Критерий завершения сессии по УНЭ/УП и выбор дальнейших действий | 03:58:12.187–04:02:49.357 | transcript_revision_video_002_r1:word:022625 → transcript_revision_video_002_r1:word:023061 | `issue_68_video_002_topic_proposal_077b` |
| 81 | Техническое определение УНЭ и УП с помощью мышечного теста | 04:02:49.437–04:10:20.058 | transcript_revision_video_002_r1:word:023062 → transcript_revision_video_002_r1:word:023654 | `issue_68_video_002_topic_proposal_081` |
| 82 | Практика в паре: разрешение на работу, гипертонус и оценка УНЭ/УП | 04:10:22.160–04:22:37.887 | transcript_revision_video_002_r1:word:023655 → transcript_revision_video_002_r1:word:024812 | `issue_68_video_002_topic_proposal_083a` |
| 83 | Стимуляция тимуса и точки селезёнки 21 для поддержки иммунной системы | 04:22:37.947–04:24:59.240 | transcript_revision_video_002_r1:word:024813 → transcript_revision_video_002_r1:word:025071 | `issue_68_video_002_topic_proposal_083b` |
| 84 | Продолжение практики: настройка теста и интерпретация числовых ответов | 04:25:00.000–04:35:34.153 | transcript_revision_video_002_r1:word:025072 → transcript_revision_video_002_r1:word:026077 | `issue_68_video_002_topic_proposal_083c` |
| 85 | Вторая практика в паре: стресс на обучение и измерение УНЭ/УП | 04:35:34.173–04:40:29.947 | transcript_revision_video_002_r1:word:026078 → transcript_revision_video_002_r1:word:026487 | `issue_68_video_002_topic_proposal_083d` |
| 86 | Итоги второго дня и домашняя практика мышечного тестирования | 04:40:29.967–04:44:02.939 | transcript_revision_video_002_r1:word:026488 → transcript_revision_video_002_r1:word:026822 | `issue_68_video_002_topic_proposal_091` |

### source_video_003 — 55 тем

| № | Тема | Время | Canonical Word range | Topic ID |
|---:|---|---|---|---|
| 1 | Начало третьего дня и приглашение поделиться результатами практики | 00:00:05.699–00:00:56.447 | transcript_revision_video_003_r1:word:000000 → transcript_revision_video_003_r1:word:000091 | `issue_68_video_003_topic_proposal_001a` |
| 2 | Обратная связь после показательной коррекции: спокойствие и устойчивость к стрессу | 00:00:56.487–00:04:41.008 | transcript_revision_video_003_r1:word:000092 → transcript_revision_video_003_r1:word:000597 | `issue_68_video_003_topic_proposal_001b` |
| 3 | Разбор практики: гипертонус и темы ответственности и пользы | 00:04:41.088–00:10:37.284 | transcript_revision_video_003_r1:word:000598 → transcript_revision_video_003_r1:word:001230 | `issue_68_video_003_topic_proposal_001c` |
| 4 | Повторение: целостная модель здоровья и направления интегральной кинезиологии | 00:11:07.969–00:25:40.976 | transcript_revision_video_003_r1:word:001263 → transcript_revision_video_003_r1:word:002530 | `issue_68_video_003_topic_proposal_006a` |
| 5 | Повторение: путь стресса от сознания к подсознанию и телу | 00:25:40.996–00:26:57.694 | transcript_revision_video_003_r1:word:002531 → transcript_revision_video_003_r1:word:002662 | `issue_68_video_003_topic_proposal_006b` |
| 6 | Повторение: протокол, мышечное тестирование, разрешение и безопасность | 00:26:57.755–00:37:23.551 | transcript_revision_video_003_r1:word:002663 → transcript_revision_video_003_r1:word:003672 | `issue_68_video_003_topic_proposal_006c` |
| 7 | Повторение: постановка темы сессии и переход к нейтральному состоянию | 00:37:23.571–00:44:59.989 | transcript_revision_video_003_r1:word:003673 → transcript_revision_video_003_r1:word:004470 | `issue_68_video_003_topic_proposal_006d` |
| 8 | Повторение: субъективная и объективная оценка результата сессии | 00:45:00.100–00:48:32.304 | transcript_revision_video_003_r1:word:004471 → transcript_revision_video_003_r1:word:004776 | `issue_68_video_003_topic_proposal_006e` |
| 9 | Вопросы по предыдущим занятиям и план перехода к практике | 00:48:32.364–00:49:58.307 | transcript_revision_video_003_r1:word:004777 → transcript_revision_video_003_r1:word:004861 | `issue_68_video_003_topic_proposal_011` |
| 10 | Гимнастика для мозга и последовательность претестов | 00:49:58.327–00:58:52.799 | transcript_revision_video_003_r1:word:004862 → transcript_revision_video_003_r1:word:005462 | `issue_68_video_003_topic_proposal_012` |
| 11 | Проверка интерпретации сильного и слабого ответа мышечного теста | 00:58:52.819–01:13:02.826 | transcript_revision_video_003_r1:word:005463 → transcript_revision_video_003_r1:word:006308 | `issue_68_video_003_topic_proposal_015` |
| 12 | Эмоции как адаптационный механизм и система оценки безопасности | 01:13:02.886–01:24:50.276 | transcript_revision_video_003_r1:word:006309 → transcript_revision_video_003_r1:word:007273 | `issue_68_video_003_topic_proposal_022a` |
| 13 | Жизненный опыт, прогнозирование будущего и устойчивые эмоциональные реакции | 01:24:50.376–01:29:06.529 | transcript_revision_video_003_r1:word:007274 → transcript_revision_video_003_r1:word:007633 | `issue_68_video_003_topic_proposal_022b` |
| 14 | Категории эмоций: отношение к себе, внешнему миру и усвоенная оценка | 01:29:07.910–01:32:50.622 | transcript_revision_video_003_r1:word:007634 → transcript_revision_video_003_r1:word:007914 | `issue_68_video_003_topic_proposal_022c` |
| 15 | Резюме теории эмоций перед переходом к стрессу | 01:33:14.565–01:34:01.917 | transcript_revision_video_003_r1:word:007933 → transcript_revision_video_003_r1:word:008013 | `issue_68_video_003_topic_proposal_022e` |
| 16 | Теория стресса: неспецифическая адаптационная реакция организма | 01:34:01.977–01:40:38.445 | transcript_revision_video_003_r1:word:008014 → transcript_revision_video_003_r1:word:008591 | `issue_68_video_003_topic_proposal_028a` |
| 17 | Острая реакция «бей или беги»: животное и человек | 01:40:38.465–01:51:20.725 | transcript_revision_video_003_r1:word:008592 → transcript_revision_video_003_r1:word:009608 | `issue_68_video_003_topic_proposal_028b` |
| 18 | Три стадии стресса: тревога, сопротивление и истощение | 01:51:20.745–01:54:30.929 | transcript_revision_video_003_r1:word:009609 → transcript_revision_video_003_r1:word:009926 | `issue_68_video_003_topic_proposal_032a` |
| 19 | Стадия тревоги: физиологические признаки и сужение восприятия | 01:54:30.969–01:58:12.503 | transcript_revision_video_003_r1:word:009927 → transcript_revision_video_003_r1:word:010340 | `issue_68_video_003_topic_proposal_032b` |
| 20 | Стадия сопротивления: адаптация, зрительный дисбаланс и травматизация | 01:58:12.563–02:02:46.618 | transcript_revision_video_003_r1:word:010341 → transcript_revision_video_003_r1:word:010837 | `issue_68_video_003_topic_proposal_032c` |
| 21 | Стадия истощения: хронический стресс и психосоматические последствия | 02:02:46.638–02:07:31.629 | transcript_revision_video_003_r1:word:010838 → transcript_revision_video_003_r1:word:011255 | `issue_68_video_003_topic_proposal_032d` |
| 22 | Гимнастика для мозга и повторение претестов после теории стресса | 02:07:31.749–02:12:14.759 | transcript_revision_video_003_r1:word:011256 → transcript_revision_video_003_r1:word:011554 | `issue_68_video_003_topic_proposal_037` |
| 23 | Антистрессовая коррекция и функциональные нарушения обработки информации | 02:12:14.799–02:17:30.352 | transcript_revision_video_003_r1:word:011555 → transcript_revision_video_003_r1:word:012039 | `issue_68_video_003_topic_proposal_039a` |
| 24 | Механизм антистрессовой коррекции: лобные доли и зрительная кора | 02:17:30.372–02:21:07.717 | transcript_revision_video_003_r1:word:012040 → transcript_revision_video_003_r1:word:012431 | `issue_68_video_003_topic_proposal_039b` |
| 25 | Признаки завершения и бытовое применение антистрессовой коррекции | 02:21:07.797–02:23:28.828 | transcript_revision_video_003_r1:word:012432 → transcript_revision_video_003_r1:word:012687 | `issue_68_video_003_topic_proposal_039c` |
| 26 | Применение антистрессовой коррекции для осознания и в протоколе сессии | 02:23:28.888–02:27:12.585 | transcript_revision_video_003_r1:word:012688 → transcript_revision_video_003_r1:word:013084 | `issue_68_video_003_topic_proposal_039d` |
| 27 | Переход к демонстрации, типы эмоций и понятие алекситимии | 02:27:12.625–02:30:14.950 | transcript_revision_video_003_r1:word:013085 → transcript_revision_video_003_r1:word:013355 | `issue_68_video_003_topic_proposal_039e` |
| 28 | Алекситимия: трудности распознавания и выражения эмоционального состояния | 02:30:14.950–02:32:15.547 | transcript_revision_video_003_r1:word:013356 → transcript_revision_video_003_r1:word:013500 | `issue_68_video_003_topic_proposal_044` |
| 29 | Структура карты эмоций: уровни, категории и парные состояния | 02:32:17.590–02:35:33.208 | transcript_revision_video_003_r1:word:013501 → transcript_revision_video_003_r1:word:013739 | `issue_68_video_003_topic_proposal_045a` |
| 30 | Трёхзначное кодирование и тестирование эмоционального состояния | 02:35:33.810–02:41:12.100 | transcript_revision_video_003_r1:word:013740 → transcript_revision_video_003_r1:word:014260 | `issue_68_video_003_topic_proposal_045b` |
| 31 | Назначение карты эмоций и взаимосвязь уровней осознания | 02:41:12.284–02:43:33.412 | transcript_revision_video_003_r1:word:014261 → transcript_revision_video_003_r1:word:014542 | `issue_68_video_003_topic_proposal_045c` |
| 32 | Временной охват сознания, подсознания и уровня тела | 02:43:33.532–02:46:22.277 | transcript_revision_video_003_r1:word:014543 → transcript_revision_video_003_r1:word:014764 | `issue_68_video_003_topic_proposal_045d` |
| 33 | Чтение негативного и позитивного состояний с антистрессовой коррекцией | 02:46:22.317–02:49:59.469 | transcript_revision_video_003_r1:word:014765 → transcript_revision_video_003_r1:word:015163 | `issue_68_video_003_topic_proposal_045e` |
| 34 | Подготовка демонстрации антистрессовой коррекции | 02:49:59.529–02:50:35.949 | transcript_revision_video_003_r1:word:015164 → transcript_revision_video_003_r1:word:015211 | `issue_68_video_003_topic_proposal_045f` |
| 35 | Выбор участника и темы демонстрационной сессии | 10239.952–10509.07 | transcript_revision_video_003_r1:word:015220 → transcript_revision_video_003_r1:word:015449 | `issue_68_video_003_topic_proposal_051a` |
| 36 | Настройка протокола и определение эмоционального состояния | 02:55:25.044–03:01:07.731 | transcript_revision_video_003_r1:word:015450 → transcript_revision_video_003_r1:word:015857 | `issue_68_video_003_topic_proposal_051b` |
| 37 | Чтение негативных состояний: загруженность и ощущение несостоятельности | 03:01:12.143–03:12:07.669 | transcript_revision_video_003_r1:word:015858 → transcript_revision_video_003_r1:word:016870 | `issue_68_video_003_topic_proposal_051c` |
| 38 | Связь состояния с запросом и поиск возрастного контекста | 03:12:07.710–03:20:12.625 | transcript_revision_video_003_r1:word:016871 → transcript_revision_video_003_r1:word:017639 | `issue_68_video_003_topic_proposal_051d` |
| 39 | Чтение позитивных состояний и проверка их связи с запросом | 03:20:12.665–03:25:49.776 | transcript_revision_video_003_r1:word:017640 → transcript_revision_video_003_r1:word:018092 | `issue_68_video_003_topic_proposal_051e` |
| 40 | Возвращение в настоящее и интеграция смысла коррекции | 03:25:49.856–03:29:44.219 | transcript_revision_video_003_r1:word:018093 → transcript_revision_video_003_r1:word:018506 | `issue_68_video_003_topic_proposal_051f` |
| 41 | Оценка результата, осознания участницы и практическая рекомендация | 03:29:44.259–03:38:52.501 | transcript_revision_video_003_r1:word:018507 → transcript_revision_video_003_r1:word:019409 | `issue_68_video_003_topic_proposal_051g` |
| 42 | Завершение сессии и фиксация позитивного фокуса | 03:38:52.581–03:40:24.633 | transcript_revision_video_003_r1:word:019410 → transcript_revision_video_003_r1:word:019558 | `issue_68_video_003_topic_proposal_051h` |
| 43 | Итоги демонстрации антистрессовой коррекции по карте эмоций | 03:40:45.036–03:43:28.133 | transcript_revision_video_003_r1:word:019586 → transcript_revision_video_003_r1:word:019739 | `issue_68_video_003_topic_proposal_051j` |
| 44 | ДПДГ: переработка травматического опыта и переход от негатива к позитиву | 03:43:28.233–03:50:17.692 | transcript_revision_video_003_r1:word:019740 → transcript_revision_video_003_r1:word:020337 | `issue_68_video_003_topic_proposal_070a` |
| 45 | Принцип глазодвигательной коррекции негативного состояния | 03:50:17.712–03:51:44.748 | transcript_revision_video_003_r1:word:020338 → transcript_revision_video_003_r1:word:020456 | `issue_68_video_003_topic_proposal_070b` |
| 46 | Траектории движений глаз и очная техника ДПДГ | 03:51:46.770–03:55:49.646 | transcript_revision_video_003_r1:word:020457 → transcript_revision_video_003_r1:word:020890 | `issue_68_video_003_topic_proposal_070c` |
| 47 | Дистанционная техника и распознавание стрессовых направлений взгляда | 03:55:49.706–04:00:04.587 | transcript_revision_video_003_r1:word:020891 → transcript_revision_video_003_r1:word:021355 | `issue_68_video_003_topic_proposal_070d` |
| 48 | Две фазы ДПДГ и межполушарная интеграция | 04:00:04.607–04:04:57.779 | transcript_revision_video_003_r1:word:021356 → transcript_revision_video_003_r1:word:021854 | `issue_68_video_003_topic_proposal_070e` |
| 49 | Практическая демонстрация ДПДГ: негативная и позитивная фазы | 04:05:02.960–04:15:03.904 | transcript_revision_video_003_r1:word:021855 → transcript_revision_video_003_r1:word:022566 | `issue_68_video_003_topic_proposal_070f` |
| 50 | Связь ДПДГ с антистрессовой коррекцией и выбором метода | 04:15:03.924–04:17:24.880 | transcript_revision_video_003_r1:word:022567 → transcript_revision_video_003_r1:word:022730 | `issue_68_video_003_topic_proposal_070g` |
| 51 | Формирование позитивного образа: воображаемый опыт и файловая модель памяти | 04:17:31.332–04:23:10.444 | transcript_revision_video_003_r1:word:022731 → transcript_revision_video_003_r1:word:023187 | `issue_68_video_003_topic_proposal_084a` |
| 52 | Перенос заряда со старой нейронной связи на позитивное воспоминание | 04:23:10.484–04:27:44.687 | transcript_revision_video_003_r1:word:023188 → transcript_revision_video_003_r1:word:023601 | `issue_68_video_003_topic_proposal_084b` |
| 53 | Условия формирования памяти и позитивной опоры для будущего поведения | 04:27:44.747–04:37:58.099 | transcript_revision_video_003_r1:word:023602 → transcript_revision_video_003_r1:word:024529 | `issue_68_video_003_topic_proposal_084c` |
| 54 | Практическое построение насыщенного позитивного образа в прошлом | 04:37:58.179–04:39:52.857 | transcript_revision_video_003_r1:word:024530 → transcript_revision_video_003_r1:word:024809 | `issue_68_video_003_topic_proposal_084d` |
| 55 | Интеграция позитивного образа и возвращение в настоящее | 04:40:02.042–04:48:01.178 | transcript_revision_video_003_r1:word:024810 → transcript_revision_video_003_r1:word:025600 | `issue_68_video_003_topic_proposal_092` |

### source_video_004 — 41 тем

| № | Тема | Время | Canonical Word range | Topic ID |
|---:|---|---|---|---|
| 1 | Начало четвёртого дня и уточнение раздаточного материала | 00:00:02.920–00:03:01.029 | transcript_revision_video_004_r1:word:000000 → transcript_revision_video_004_r1:word:000173 | `issue_68_video_004_topic_proposal_001a` |
| 2 | Время коррекции, память и возможность работы с прошлым | 00:03:01.049–00:08:41.253 | transcript_revision_video_004_r1:word:000174 → transcript_revision_video_004_r1:word:000614 | `issue_68_video_004_topic_proposal_001b` |
| 3 | Специфическая, генетическая и неспецифическая регрессия | 526.571–626.178 | transcript_revision_video_004_r1:word:000615 → transcript_revision_video_004_r1:word:000754 | `issue_68_video_004_topic_proposal_001c` |
| 4 | Поиск возраста коррекции по диапазонам | 00:10:26.198–00:12:47.336 | transcript_revision_video_004_r1:word:000755 → transcript_revision_video_004_r1:word:000969 | `issue_68_video_004_topic_proposal_001d` |
| 5 | Учебное задание: определить возраст четырнадцать лет | 00:12:49.638–00:20:07.103 | transcript_revision_video_004_r1:word:000970 → transcript_revision_video_004_r1:word:001178 | `issue_68_video_004_topic_proposal_001e` |
| 6 | Гимнастика, претесты и закладка позитивного прошлого | 00:20:07.144–00:25:35.760 | transcript_revision_video_004_r1:word:001179 → transcript_revision_video_004_r1:word:001466 | `issue_68_video_004_topic_proposal_001f` |
| 7 | Разбор поиска возраста по стрессу и по вопросам | 00:25:35.780–00:29:01.375 | transcript_revision_video_004_r1:word:001467 → transcript_revision_video_004_r1:word:001804 | `issue_68_video_004_topic_proposal_001g` |
| 8 | Этапы специфической рецессии и два пути входа в генетическое прошлое | 00:29:01.395–00:36:57.537 | transcript_revision_video_004_r1:word:001805 → transcript_revision_video_004_r1:word:002521 | `issue_68_video_004_topic_proposal_011a` |
| 9 | Поиск поколения и родительской линии генетической программы | 00:36:57.557–00:43:08.860 | transcript_revision_video_004_r1:word:002522 → transcript_revision_video_004_r1:word:003181 | `issue_68_video_004_topic_proposal_011b` |
| 10 | Работа с унаследованной моделью поведения, а не с образом предка | 00:43:09.061–00:52:54.480 | transcript_revision_video_004_r1:word:003182 → transcript_revision_video_004_r1:word:004103 | `issue_68_video_004_topic_proposal_011c` |
| 11 | Ограничение домысливания и работа без принуждения к воспоминаниям | 00:52:54.500–00:56:00.643 | transcript_revision_video_004_r1:word:004104 → transcript_revision_video_004_r1:word:004450 | `issue_68_video_004_topic_proposal_011d` |
| 12 | Техника неспецифической рецессии и возврата в настоящее | 00:56:00.704–01:03:19.665 | transcript_revision_video_004_r1:word:004451 → transcript_revision_video_004_r1:word:005082 | `issue_68_video_004_topic_proposal_011e` |
| 13 | Преимущества и ограничения неспецифической рецессии | 01:03:19.705–01:08:46.611 | transcript_revision_video_004_r1:word:005083 → transcript_revision_video_004_r1:word:005526 | `issue_68_video_004_topic_proposal_024a` |
| 14 | Время возникновения причины, осознания и прослеживание по возрастам | 01:08:46.631–01:18:15.399 | transcript_revision_video_004_r1:word:005527 → transcript_revision_video_004_r1:word:006507 | `issue_68_video_004_topic_proposal_024b` |
| 15 | Определение типа времени после нахождения возраста | 01:18:15.459–01:21:50.444 | transcript_revision_video_004_r1:word:006508 → transcript_revision_video_004_r1:word:006917 | `issue_68_video_004_topic_proposal_024c` |
| 16 | Зачатие и предимплантационный период как отдельные интервалы | 01:21:50.464–01:25:31.466 | transcript_revision_video_004_r1:word:006918 → transcript_revision_video_004_r1:word:007251 | `issue_68_video_004_topic_proposal_024d` |
| 17 | Триместры беременности и характерные стрессовые факторы | 01:25:32.290–01:30:56.947 | transcript_revision_video_004_r1:word:007252 → transcript_revision_video_004_r1:word:007858 | `issue_68_video_004_topic_proposal_024e` |
| 18 | Четыре стадии родов и связанные с ними переживания | 01:30:56.967–01:38:13.089 | transcript_revision_video_004_r1:word:007859 → transcript_revision_video_004_r1:word:008611 | `issue_68_video_004_topic_proposal_024f` |
| 19 | Рефлекс Моро, первый год жизни и формирование моделей поведения | 01:38:13.109–01:51:40.109 | transcript_revision_video_004_r1:word:008612 → transcript_revision_video_004_r1:word:009737 | `issue_68_video_004_topic_proposal_024g` |
| 20 | Генетический опыт: предел глубины анализа и переход к ресурсному состоянию | 6700.189–7079.241 | transcript_revision_video_004_r1:word:009738 → transcript_revision_video_004_r1:word:010253 | `issue_68_video_004_topic_proposal_024h` |
| 21 | Гимнастика для мозга и повторение претестов | 7079.261–7279.486 | transcript_revision_video_004_r1:word:010254 → transcript_revision_video_004_r1:word:010431 | `issue_68_video_004_topic_proposal_024h2` |
| 22 | Сращивание событий, эмоций и модели поведения при работе в прошлом | 02:01:19.506–02:08:10.817 | transcript_revision_video_004_r1:word:010432 → transcript_revision_video_004_r1:word:011057 | `issue_68_video_004_topic_proposal_024i` |
| 23 | Общий протокол как каркас для последующих коррекций | 02:08:10.897–02:13:57.822 | transcript_revision_video_004_r1:word:011058 → transcript_revision_video_004_r1:word:011660 | `issue_68_video_004_topic_proposal_024j` |
| 24 | Простукивание с прослеживанием: мудра, меридианные точки и принцип коррекции | 02:13:57.862–02:24:47.628 | transcript_revision_video_004_r1:word:011661 → transcript_revision_video_004_r1:word:012723 | `issue_68_video_004_topic_proposal_044a` |
| 25 | Выбор меридианных точек и техника простукивания с движениями глаз | 02:24:47.648–02:29:15.910 | transcript_revision_video_004_r1:word:012724 → transcript_revision_video_004_r1:word:013158 | `issue_68_video_004_topic_proposal_044b` |
| 26 | Ретест после коррекции и определение времени проекции в будущее | 02:29:15.910–02:34:10.342 | transcript_revision_video_004_r1:word:013159 → transcript_revision_video_004_r1:word:013676 | `issue_68_video_004_topic_proposal_044c` |
| 27 | Создание позитивного будущего и возврат в настоящее | 02:34:10.362–02:39:12.349 | transcript_revision_video_004_r1:word:013677 → transcript_revision_video_004_r1:word:014181 | `issue_68_video_004_topic_proposal_044d` |
| 28 | Завершение коррекции и проверка необходимости дополнительных действий | 02:39:42.775–02:45:17.262 | transcript_revision_video_004_r1:word:014235 → transcript_revision_video_004_r1:word:014883 | `issue_68_video_004_topic_proposal_051b` |
| 29 | Домашнее задание, сроки выполнения и рекомендации клиенту | 02:45:17.282–02:50:06.424 | transcript_revision_video_004_r1:word:014884 → transcript_revision_video_004_r1:word:015426 | `issue_68_video_004_topic_proposal_051c` |
| 30 | Изменение поведения после сессии и предел ответственности специалиста | 02:50:06.444–03:01:12.268 | transcript_revision_video_004_r1:word:015427 → transcript_revision_video_004_r1:word:016428 | `issue_68_video_004_topic_proposal_051d` |
| 31 | Ответственность за позитивные изменения и реалистичный объём работы | 03:01:12.308–03:13:04.587 | transcript_revision_video_004_r1:word:016429 → transcript_revision_video_004_r1:word:017447 | `issue_68_video_004_topic_proposal_051e` |
| 32 | Факторы результата, ожидания клиента и риск обесценивания изменений | 03:13:04.607–03:26:10.234 | transcript_revision_video_004_r1:word:017448 → transcript_revision_video_004_r1:word:018928 | `issue_68_video_004_topic_proposal_051f` |
| 33 | Дискомфорт после сессии, ложная причинность и флексионный тип реакции | 03:26:10.294–03:37:03.736 | transcript_revision_video_004_r1:word:018929 → transcript_revision_video_004_r1:word:019994 | `issue_68_video_004_topic_proposal_051g` |
| 34 | Настройка демонстрационной сессии и определение эмоционального состояния | 03:37:06.200–03:43:02.646 | transcript_revision_video_004_r1:word:019995 → transcript_revision_video_004_r1:word:020503 | `issue_68_video_004_topic_proposal_066a` |
| 35 | Негативные состояния в обучении: негодование, язвительность и бесчувственность | 03:43:02.686–03:54:38.968 | transcript_revision_video_004_r1:word:020504 → transcript_revision_video_004_r1:word:021860 | `issue_68_video_004_topic_proposal_066b` |
| 36 | Позитивная самооценка и формулирование желаемого состояния | 03:54:39.009–03:59:59.970 | transcript_revision_video_004_r1:word:021861 → transcript_revision_video_004_r1:word:022328 | `issue_68_video_004_topic_proposal_066c` |
| 37 | Поиск возраста и школьное воспоминание о несправедливой оценке | 04:00:00.470–04:05:06.815 | transcript_revision_video_004_r1:word:022329 → transcript_revision_video_004_r1:word:022859 | `issue_68_video_004_topic_proposal_066d` |
| 38 | Выбор меридианов и коррекция простукиванием с прослеживанием | 04:05:06.856–04:13:17.471 | transcript_revision_video_004_r1:word:022860 → transcript_revision_video_004_r1:word:023553 | `issue_68_video_004_topic_proposal_066e` |
| 39 | Создание позитивного школьного воспоминания и проверка результата | 04:13:17.551–04:18:13.897 | transcript_revision_video_004_r1:word:023554 → transcript_revision_video_004_r1:word:024030 | `issue_68_video_004_topic_proposal_066f` |
| 40 | Ретест, рекомендации участнице и итоги четырёхдневного обучения | 04:18:15.481–04:25:29.555 | transcript_revision_video_004_r1:word:024031 → transcript_revision_video_004_r1:word:024792 | `issue_68_video_004_topic_proposal_066g` |
| 41 | Заключительные вопросы и завершение семинара | 04:25:30.280–04:26:40.776 | transcript_revision_video_004_r1:word:024793 → transcript_revision_video_004_r1:word:024934 | `issue_68_video_004_topic_proposal_079` |

**Первое видео:** темы Day 1 ранее рассмотрены в Issue #113 и сохраняют собственный авторитетный review-артефакт. Здесь представлены 182 единиц из текущей QA-проекции Days 2–4; нельзя подменять ими Day 1.

## 3. Связи тема → понятие (246)

Статусы ниже являются результатами QA, **не итоговой семантической авторизацией**. Для каждой связи сохранён точный идентификатор и ссылка на исходный Topic.

| № | Источник | Topic ID | Понятие | QA-классификация | Link ID |
|---:|---|---|---|---|---|
| 1 | source_video_001 | `issue_113_reviewed_topic_01` | Стресс | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_01_stress` |
| 2 | source_video_001 | `issue_113_reviewed_topic_03` | Стресс | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_03_stress` |
| 3 | source_video_002 | `issue_68_video_002_topic_proposal_002` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_002_stress` |
| 4 | source_video_002 | `issue_68_video_002_topic_proposal_006` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_006_stress` |
| 5 | source_video_002 | `issue_68_video_002_topic_proposal_056` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_056_stress` |
| 6 | source_video_002 | `issue_68_video_002_topic_proposal_057` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_057_stress` |
| 7 | source_video_002 | `issue_68_video_002_topic_proposal_058` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_058_stress` |
| 8 | source_video_002 | `issue_68_video_002_topic_proposal_059` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_059_stress` |
| 9 | source_video_002 | `issue_68_video_002_topic_proposal_065` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_065_stress` |
| 10 | source_video_002 | `issue_68_video_002_topic_proposal_066` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_066_stress` |
| 11 | source_video_002 | `issue_68_video_002_topic_proposal_081` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_081_stress` |
| 12 | source_video_002 | `issue_68_video_002_topic_proposal_083` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_083_stress` |
| 13 | source_video_002 | `issue_68_video_002_topic_proposal_088` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_088_stress` |
| 14 | source_video_003 | `issue_68_video_003_topic_proposal_003` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_003_stress` |
| 15 | source_video_003 | `issue_68_video_003_topic_proposal_008` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_008_stress` |
| 16 | source_video_003 | `issue_68_video_003_topic_proposal_015` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_015_stress` |
| 17 | source_video_003 | `issue_68_video_003_topic_proposal_017` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_017_stress` |
| 18 | source_video_003 | `issue_68_video_003_topic_proposal_028` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_028_stress` |
| 19 | source_video_003 | `issue_68_video_003_topic_proposal_029` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_029_stress` |
| 20 | source_video_003 | `issue_68_video_003_topic_proposal_030` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_030_stress` |
| 21 | source_video_003 | `issue_68_video_003_topic_proposal_031` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_031_stress` |
| 22 | source_video_003 | `issue_68_video_003_topic_proposal_032` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_032_stress` |
| 23 | source_video_003 | `issue_68_video_003_topic_proposal_033` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_033_stress` |
| 24 | source_video_003 | `issue_68_video_003_topic_proposal_034` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_034_stress` |
| 25 | source_video_003 | `issue_68_video_003_topic_proposal_036` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_036_stress` |
| 26 | source_video_003 | `issue_68_video_003_topic_proposal_037` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_037_stress` |
| 27 | source_video_003 | `issue_68_video_003_topic_proposal_039` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_039_stress` |
| 28 | source_video_003 | `issue_68_video_003_topic_proposal_040` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_040_stress` |
| 29 | source_video_003 | `issue_68_video_003_topic_proposal_041` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_041_stress` |
| 30 | source_video_003 | `issue_68_video_003_topic_proposal_042` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_042_stress` |
| 31 | source_video_003 | `issue_68_video_003_topic_proposal_043` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_043_stress` |
| 32 | source_video_003 | `issue_68_video_003_topic_proposal_051b` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_051b_stress` |
| 33 | source_video_003 | `issue_68_video_003_topic_proposal_065` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_065_stress` |
| 34 | source_video_003 | `issue_68_video_003_topic_proposal_069` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_069_stress` |
| 35 | source_video_003 | `issue_68_video_003_topic_proposal_070a` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_070a_stress` |
| 36 | source_video_003 | `issue_68_video_003_topic_proposal_073` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_073_stress` |
| 37 | source_video_003 | `issue_68_video_003_topic_proposal_075` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_075_stress` |
| 38 | source_video_004 | `issue_68_video_004_topic_proposal_006` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_006_stress` |
| 39 | source_video_004 | `issue_68_video_004_topic_proposal_009` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_009_stress` |
| 40 | source_video_004 | `issue_68_video_004_topic_proposal_010` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_010_stress` |
| 41 | source_video_004 | `issue_68_video_004_topic_proposal_027` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_027_stress` |
| 42 | source_video_004 | `issue_68_video_004_topic_proposal_028` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_028_stress` |
| 43 | source_video_004 | `issue_68_video_004_topic_proposal_029` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_029_stress` |
| 44 | source_video_004 | `issue_68_video_004_topic_proposal_024g` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_024g_stress` |
| 45 | source_video_004 | `issue_68_video_004_topic_proposal_047` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_047_stress` |
| 46 | source_video_004 | `issue_68_video_004_topic_proposal_048` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_048_stress` |
| 47 | source_video_004 | `issue_68_video_004_topic_proposal_049` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_049_stress` |
| 48 | source_video_004 | `issue_68_video_004_topic_proposal_055` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_055_stress` |
| 49 | source_video_004 | `issue_68_video_004_topic_proposal_066` | Стресс | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_066_stress` |
| 50 | source_video_001 | `issue_113_reviewed_topic_02` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_02_kinesiology` |
| 51 | source_video_001 | `issue_113_reviewed_topic_04b` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_04b_kinesiology` |
| 52 | source_video_001 | `issue_113_reviewed_topic_07` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_07_kinesiology` |
| 53 | source_video_001 | `issue_113_reviewed_topic_12a` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_12a_kinesiology` |
| 54 | source_video_002 | `issue_68_video_002_topic_proposal_001` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_001_kinesiology` |
| 55 | source_video_002 | `issue_68_video_002_topic_proposal_002` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_002_kinesiology` |
| 56 | source_video_002 | `issue_68_video_002_topic_proposal_047` | Кинезиология | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_047_kinesiology` |
| 57 | source_video_001 | `issue_113_reviewed_topic_25` | Мышечное тестирование | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_25_muscle_testing` |
| 58 | source_video_001 | `issue_113_reviewed_topic_26` | Мышечное тестирование | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_26_muscle_testing` |
| 59 | source_video_001 | `issue_113_reviewed_topic_27` | Мышечное тестирование | LINK_EXCEPTION | `issue_68_link_issue_113_reviewed_topic_27_muscle_testing` |
| 60 | source_video_002 | `issue_68_video_002_topic_proposal_002` | Мышечное тестирование | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_002_muscle_testing` |
| 61 | source_video_001 | `issue_113_reviewed_topic_14a` | Коррекция | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_14a_correction` |
| 62 | source_video_001 | `issue_113_reviewed_topic_19` | Коррекция | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_19_correction` |
| 63 | source_video_001 | `issue_113_reviewed_topic_21` | Коррекция | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_21_correction` |
| 64 | source_video_001 | `issue_113_reviewed_topic_23` | Коррекция | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_23_correction` |
| 65 | source_video_001 | `issue_113_reviewed_topic_24` | Коррекция | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_24_correction` |
| 66 | source_video_002 | `issue_68_video_002_topic_proposal_006` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_006_correction` |
| 67 | source_video_002 | `issue_68_video_002_topic_proposal_007` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_007_correction` |
| 68 | source_video_002 | `issue_68_video_002_topic_proposal_008` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_008_correction` |
| 69 | source_video_002 | `issue_68_video_002_topic_proposal_009` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_009_correction` |
| 70 | source_video_002 | `issue_68_video_002_topic_proposal_012` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_012_correction` |
| 71 | source_video_002 | `issue_68_video_002_topic_proposal_052` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_052_correction` |
| 72 | source_video_002 | `issue_68_video_002_topic_proposal_054` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_054_correction` |
| 73 | source_video_002 | `issue_68_video_002_topic_proposal_074` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_074_correction` |
| 74 | source_video_002 | `issue_68_video_002_topic_proposal_079` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_079_correction` |
| 75 | source_video_003 | `issue_68_video_003_topic_proposal_008` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_008_correction` |
| 76 | source_video_003 | `issue_68_video_003_topic_proposal_039` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_039_correction` |
| 77 | source_video_003 | `issue_68_video_003_topic_proposal_040` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_040_correction` |
| 78 | source_video_003 | `issue_68_video_003_topic_proposal_041` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_041_correction` |
| 79 | source_video_003 | `issue_68_video_003_topic_proposal_042` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_042_correction` |
| 80 | source_video_003 | `issue_68_video_003_topic_proposal_043` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_043_correction` |
| 81 | source_video_003 | `issue_68_video_003_topic_proposal_050` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_050_correction` |
| 82 | source_video_003 | `issue_68_video_003_topic_proposal_065` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_065_correction` |
| 83 | source_video_003 | `issue_68_video_003_topic_proposal_069` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_069_correction` |
| 84 | source_video_003 | `issue_68_video_003_topic_proposal_072` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_072_correction` |
| 85 | source_video_003 | `issue_68_video_003_topic_proposal_073` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_073_correction` |
| 86 | source_video_003 | `issue_68_video_003_topic_proposal_077` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_077_correction` |
| 87 | source_video_003 | `issue_68_video_003_topic_proposal_082` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_082_correction` |
| 88 | source_video_003 | `issue_68_video_003_topic_proposal_083` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_083_correction` |
| 89 | source_video_004 | `issue_68_video_004_topic_proposal_002` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_002_correction` |
| 90 | source_video_004 | `issue_68_video_004_topic_proposal_021` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_021_correction` |
| 91 | source_video_004 | `issue_68_video_004_topic_proposal_027` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_027_correction` |
| 92 | source_video_004 | `issue_68_video_004_topic_proposal_042` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_042_correction` |
| 93 | source_video_004 | `issue_68_video_004_topic_proposal_046` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_046_correction` |
| 94 | source_video_004 | `issue_68_video_004_topic_proposal_047` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_047_correction` |
| 95 | source_video_004 | `issue_68_video_004_topic_proposal_048` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_048_correction` |
| 96 | source_video_004 | `issue_68_video_004_topic_proposal_049` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_049_correction` |
| 97 | source_video_004 | `issue_68_video_004_topic_proposal_051` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_051_correction` |
| 98 | source_video_004 | `issue_68_video_004_topic_proposal_055` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_055_correction` |
| 99 | source_video_004 | `issue_68_video_004_topic_proposal_057` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_057_correction` |
| 100 | source_video_004 | `issue_68_video_004_topic_proposal_060` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_060_correction` |
| 101 | source_video_004 | `issue_68_video_004_topic_proposal_072` | Коррекция | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_072_correction` |
| 102 | source_video_001 | `issue_113_reviewed_topic_14a` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_14a_protocol` |
| 103 | source_video_001 | `issue_113_reviewed_topic_15` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_15_protocol` |
| 104 | source_video_002 | `issue_68_video_002_topic_proposal_007` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_007_protocol` |
| 105 | source_video_002 | `issue_68_video_002_topic_proposal_061` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_061_protocol` |
| 106 | source_video_002 | `issue_68_video_002_topic_proposal_063` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_063_protocol` |
| 107 | source_video_003 | `issue_68_video_003_topic_proposal_008` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_008_protocol` |
| 108 | source_video_003 | `issue_68_video_003_topic_proposal_043` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_043_protocol` |
| 109 | source_video_004 | `issue_68_video_004_topic_proposal_061` | Протокол работы | LINK_EXCEPTION | `issue_68_link_issue_68_video_004_topic_proposal_061_protocol` |
| 110 | source_video_004 | `issue_68_video_004_topic_proposal_065` | Протокол работы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_065_protocol` |
| 111 | source_video_001 | `issue_113_reviewed_topic_13` | Эмоции | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_13_emotion` |
| 112 | source_video_002 | `issue_68_video_002_topic_proposal_006` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_006_emotion` |
| 113 | source_video_002 | `issue_68_video_002_topic_proposal_014` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_014_emotion` |
| 114 | source_video_002 | `issue_68_video_002_topic_proposal_022` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_022_emotion` |
| 115 | source_video_002 | `issue_68_video_002_topic_proposal_023` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_023_emotion` |
| 116 | source_video_002 | `issue_68_video_002_topic_proposal_025` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_025_emotion` |
| 117 | source_video_002 | `issue_68_video_002_topic_proposal_026` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_026_emotion` |
| 118 | source_video_002 | `issue_68_video_002_topic_proposal_055` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_055_emotion` |
| 119 | source_video_002 | `issue_68_video_002_topic_proposal_058` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_058_emotion` |
| 120 | source_video_002 | `issue_68_video_002_topic_proposal_084` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_084_emotion` |
| 121 | source_video_003 | `issue_68_video_003_topic_proposal_006` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_006_emotion` |
| 122 | source_video_003 | `issue_68_video_003_topic_proposal_010` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_010_emotion` |
| 123 | source_video_003 | `issue_68_video_003_topic_proposal_022` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_022_emotion` |
| 124 | source_video_003 | `issue_68_video_003_topic_proposal_023` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_023_emotion` |
| 125 | source_video_003 | `issue_68_video_003_topic_proposal_024` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_024_emotion` |
| 126 | source_video_003 | `issue_68_video_003_topic_proposal_025` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_025_emotion` |
| 127 | source_video_003 | `issue_68_video_003_topic_proposal_026` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_026_emotion` |
| 128 | source_video_003 | `issue_68_video_003_topic_proposal_027` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_027_emotion` |
| 129 | source_video_003 | `issue_68_video_003_topic_proposal_028` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_028_emotion` |
| 130 | source_video_003 | `issue_68_video_003_topic_proposal_039` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_039_emotion` |
| 131 | source_video_003 | `issue_68_video_003_topic_proposal_042` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_042_emotion` |
| 132 | source_video_003 | `issue_68_video_003_topic_proposal_043` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_043_emotion` |
| 133 | source_video_003 | `issue_68_video_003_topic_proposal_044` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_044_emotion` |
| 134 | source_video_003 | `issue_68_video_003_topic_proposal_045` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_045_emotion` |
| 135 | source_video_003 | `issue_68_video_003_topic_proposal_047` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_047_emotion` |
| 136 | source_video_003 | `issue_68_video_003_topic_proposal_048` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_048_emotion` |
| 137 | source_video_003 | `issue_68_video_003_topic_proposal_054` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_054_emotion` |
| 138 | source_video_003 | `issue_68_video_003_topic_proposal_065` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_065_emotion` |
| 139 | source_video_003 | `issue_68_video_003_topic_proposal_069` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_069_emotion` |
| 140 | source_video_003 | `issue_68_video_003_topic_proposal_071` | Эмоции | LINK_EXCEPTION | `issue_68_link_issue_68_video_003_topic_proposal_071_emotion` |
| 141 | source_video_003 | `issue_68_video_003_topic_proposal_072` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_072_emotion` |
| 142 | source_video_003 | `issue_68_video_003_topic_proposal_082` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_082_emotion` |
| 143 | source_video_003 | `issue_68_video_003_topic_proposal_085` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_085_emotion` |
| 144 | source_video_003 | `issue_68_video_003_topic_proposal_088` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_088_emotion` |
| 145 | source_video_004 | `issue_68_video_004_topic_proposal_026` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_026_emotion` |
| 146 | source_video_004 | `issue_68_video_004_topic_proposal_030` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_030_emotion` |
| 147 | source_video_004 | `issue_68_video_004_topic_proposal_041` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_041_emotion` |
| 148 | source_video_004 | `issue_68_video_004_topic_proposal_073` | Эмоции | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_073_emotion` |
| 149 | source_video_001 | `issue_113_reviewed_topic_03` | Нервная система | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_03_nervous_system` |
| 150 | source_video_002 | `issue_68_video_002_topic_proposal_010` | Нервная система | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_010_nervous_system` |
| 151 | source_video_003 | `issue_68_video_003_topic_proposal_026` | Нейронные связи и сети | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_026_neural_connections_and_networks` |
| 152 | source_video_003 | `issue_68_video_003_topic_proposal_086` | Нервная система | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_086_nervous_system` |
| 153 | source_video_003 | `issue_68_video_003_topic_proposal_086` | Нейронные связи и сети | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_086_neural_connections_and_networks` |
| 154 | source_video_003 | `issue_68_video_003_topic_proposal_088` | Нейронные связи и сети | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_088_neural_connections_and_networks` |
| 155 | source_video_003 | `issue_68_video_003_topic_proposal_090` | Нервная система | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_090_nervous_system` |
| 156 | source_video_003 | `issue_68_video_003_topic_proposal_092` | Нервная система | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_092_nervous_system` |
| 157 | source_video_004 | `issue_68_video_004_topic_proposal_014` | Нервная система | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_014_nervous_system` |
| 158 | source_video_004 | `issue_68_video_004_topic_proposal_014` | Нейронные связи и сети | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_014_neural_connections_and_networks` |
| 159 | source_video_004 | `issue_68_video_004_topic_proposal_015` | Нервная система | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_015_nervous_system` |
| 160 | source_video_001 | `issue_113_reviewed_topic_03` | Адаптация | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_03_adaptation` |
| 161 | source_video_003 | `issue_68_video_003_topic_proposal_023` | Адаптация | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_023_adaptation` |
| 162 | source_video_003 | `issue_68_video_003_topic_proposal_031` | Адаптация | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_031_adaptation` |
| 163 | source_video_001 | `issue_113_reviewed_topic_05c` | Мозг | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_05c_brain` |
| 164 | source_video_001 | `issue_113_reviewed_topic_09` | Мозг | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_09_brain` |
| 165 | source_video_001 | `issue_113_reviewed_topic_09` | Полушария головного мозга | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_09_cerebral_hemispheres` |
| 166 | source_video_002 | `issue_68_video_002_topic_proposal_014` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_014_brain` |
| 167 | source_video_002 | `issue_68_video_002_topic_proposal_014` | Полушария головного мозга | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_014_cerebral_hemispheres` |
| 168 | source_video_002 | `issue_68_video_002_topic_proposal_070` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_070_brain` |
| 169 | source_video_003 | `issue_68_video_003_topic_proposal_041` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_041_brain` |
| 170 | source_video_003 | `issue_68_video_003_topic_proposal_077` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_077_brain` |
| 171 | source_video_003 | `issue_68_video_003_topic_proposal_077` | Полушария головного мозга | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_077_cerebral_hemispheres` |
| 172 | source_video_003 | `issue_68_video_003_topic_proposal_083` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_083_brain` |
| 173 | source_video_003 | `issue_68_video_003_topic_proposal_084` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_084_brain` |
| 174 | source_video_003 | `issue_68_video_003_topic_proposal_085` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_085_brain` |
| 175 | source_video_003 | `issue_68_video_003_topic_proposal_088` | Мозг | LINK_EXCEPTION | `issue_68_link_issue_68_video_003_topic_proposal_088_brain` |
| 176 | source_video_004 | `issue_68_video_004_topic_proposal_040` | Мозг | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_040_brain` |
| 177 | source_video_001 | `issue_113_reviewed_topic_10` | Меридианы | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_10_meridians` |
| 178 | source_video_002 | `issue_68_video_002_topic_proposal_012` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_012_meridians` |
| 179 | source_video_002 | `issue_68_video_002_topic_proposal_022` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_022_meridians` |
| 180 | source_video_002 | `issue_68_video_002_topic_proposal_071` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_071_meridians` |
| 181 | source_video_003 | `issue_68_video_003_topic_proposal_008` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_008_meridians` |
| 182 | source_video_004 | `issue_68_video_004_topic_proposal_008` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_008_meridians` |
| 183 | source_video_004 | `issue_68_video_004_topic_proposal_040` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_040_meridians` |
| 184 | source_video_004 | `issue_68_video_004_topic_proposal_043` | Меридианы | LINK_EXCEPTION | `issue_68_link_issue_68_video_004_topic_proposal_043_meridians` |
| 185 | source_video_004 | `issue_68_video_004_topic_proposal_044` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_044_meridians` |
| 186 | source_video_004 | `issue_68_video_004_topic_proposal_045` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_045_meridians` |
| 187 | source_video_004 | `issue_68_video_004_topic_proposal_046` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_046_meridians` |
| 188 | source_video_004 | `issue_68_video_004_topic_proposal_047` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_047_meridians` |
| 189 | source_video_004 | `issue_68_video_004_topic_proposal_048` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_048_meridians` |
| 190 | source_video_004 | `issue_68_video_004_topic_proposal_072` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_072_meridians` |
| 191 | source_video_004 | `issue_68_video_004_topic_proposal_073` | Меридианы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_073_meridians` |
| 192 | source_video_001 | `issue_113_reviewed_topic_19` | Движения глаз | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_19_eye_movement` |
| 193 | source_video_001 | `issue_113_reviewed_topic_19` | ДПДГ | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_19_emdr` |
| 194 | source_video_001 | `issue_113_reviewed_topic_19` | Глазодвигательные мышцы | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_19_extraocular_muscles` |
| 195 | source_video_003 | `issue_68_video_003_topic_proposal_034` | Глазодвигательные мышцы | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_034_extraocular_muscles` |
| 196 | source_video_003 | `issue_68_video_003_topic_proposal_071` | ДПДГ | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_071_emdr` |
| 197 | source_video_003 | `issue_68_video_003_topic_proposal_072` | ДПДГ | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_072_emdr` |
| 198 | source_video_003 | `issue_68_video_003_topic_proposal_073` | Глазодвигательные мышцы | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_073_extraocular_muscles` |
| 199 | source_video_003 | `issue_68_video_003_topic_proposal_076` | Глазодвигательные мышцы | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_076_extraocular_muscles` |
| 200 | source_video_003 | `issue_68_video_003_topic_proposal_080` | Движения глаз | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_080_eye_movement` |
| 201 | source_video_003 | `issue_68_video_003_topic_proposal_082` | ДПДГ | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_082_emdr` |
| 202 | source_video_003 | `issue_68_video_003_topic_proposal_083` | Движения глаз | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_083_eye_movement` |
| 203 | source_video_003 | `issue_68_video_003_topic_proposal_083` | ДПДГ | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_083_emdr` |
| 204 | source_video_004 | `issue_68_video_004_topic_proposal_046` | ДПДГ | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_046_emdr` |
| 205 | source_video_004 | `issue_68_video_004_topic_proposal_074` | Глазодвигательные мышцы | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_074_extraocular_muscles` |
| 206 | source_video_001 | `issue_113_reviewed_topic_08` | Уровни развития сознания по Дэвиду Хокинсу | LINK_CLEAR | `issue_68_link_issue_113_reviewed_topic_08_consciousness` |
| 207 | source_video_003 | `issue_68_video_003_topic_proposal_015` | Три уровня осознания: сознание, подсознание и тело | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_015_three_level_awareness` |
| 208 | source_video_003 | `issue_68_video_003_topic_proposal_016` | Три уровня осознания: сознание, подсознание и тело | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_016_three_level_awareness` |
| 209 | source_video_003 | `issue_68_video_003_topic_proposal_019` | Три уровня осознания: сознание, подсознание и тело | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_019_three_level_awareness` |
| 210 | source_video_003 | `issue_68_video_003_topic_proposal_020` | Три уровня осознания: сознание, подсознание и тело | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_020_three_level_awareness` |
| 211 | source_video_003 | `issue_68_video_003_topic_proposal_049` | Три уровня осознания: сознание, подсознание и тело | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_049_three_level_awareness` |
| 212 | source_video_003 | `issue_68_video_003_topic_proposal_062` | Три уровня осознания: сознание, подсознание и тело | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_062_three_level_awareness` |
| 213 | source_video_002 | `issue_68_video_002_topic_proposal_014` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_014_subconscious` |
| 214 | source_video_002 | `issue_68_video_002_topic_proposal_059` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_002_topic_proposal_059_subconscious` |
| 215 | source_video_003 | `issue_68_video_003_topic_proposal_015` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_015_subconscious` |
| 216 | source_video_003 | `issue_68_video_003_topic_proposal_016` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_016_subconscious` |
| 217 | source_video_003 | `issue_68_video_003_topic_proposal_017` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_017_subconscious` |
| 218 | source_video_003 | `issue_68_video_003_topic_proposal_018` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_018_subconscious` |
| 219 | source_video_003 | `issue_68_video_003_topic_proposal_019` | Подсознание | LINK_EXCEPTION | `issue_68_link_issue_68_video_003_topic_proposal_019_subconscious` |
| 220 | source_video_003 | `issue_68_video_003_topic_proposal_045` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_045_subconscious` |
| 221 | source_video_003 | `issue_68_video_003_topic_proposal_048` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_048_subconscious` |
| 222 | source_video_003 | `issue_68_video_003_topic_proposal_071` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_071_subconscious` |
| 223 | source_video_003 | `issue_68_video_003_topic_proposal_082` | Подсознание | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_082_subconscious` |
| 224 | source_video_004 | `issue_68_video_004_topic_proposal_052` | Подсознание | LINK_EXCEPTION | `issue_68_link_issue_68_video_004_topic_proposal_052_subconscious` |
| 225 | source_video_003 | `issue_68_video_003_topic_proposal_027` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_027_memory` |
| 226 | source_video_003 | `issue_68_video_003_topic_proposal_040` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_040_memory` |
| 227 | source_video_003 | `issue_68_video_003_topic_proposal_045` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_045_memory` |
| 228 | source_video_003 | `issue_68_video_003_topic_proposal_061` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_061_memory` |
| 229 | source_video_003 | `issue_68_video_003_topic_proposal_070` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_070_memory` |
| 230 | source_video_003 | `issue_68_video_003_topic_proposal_071` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_071_memory` |
| 231 | source_video_003 | `issue_68_video_003_topic_proposal_083` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_083_memory` |
| 232 | source_video_003 | `issue_68_video_003_topic_proposal_085` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_085_memory` |
| 233 | source_video_003 | `issue_68_video_003_topic_proposal_086` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_086_memory` |
| 234 | source_video_003 | `issue_68_video_003_topic_proposal_087` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_087_memory` |
| 235 | source_video_003 | `issue_68_video_003_topic_proposal_088` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_088_memory` |
| 236 | source_video_003 | `issue_68_video_003_topic_proposal_090` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_090_memory` |
| 237 | source_video_004 | `issue_68_video_004_topic_proposal_015` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_015_memory` |
| 238 | source_video_004 | `issue_68_video_004_topic_proposal_077` | Память | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_077_memory` |
| 239 | source_video_003 | `issue_68_video_003_topic_proposal_028` | Травма | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_028_trauma` |
| 240 | source_video_003 | `issue_68_video_003_topic_proposal_034` | Травма | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_034_trauma` |
| 241 | source_video_003 | `issue_68_video_003_topic_proposal_069` | Травма | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_069_trauma` |
| 242 | source_video_003 | `issue_68_video_003_topic_proposal_070` | Травма | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_070_trauma` |
| 243 | source_video_004 | `issue_68_video_004_topic_proposal_042` | Травма | LINK_CLEAR | `issue_68_link_issue_68_video_004_topic_proposal_042_trauma` |
| 244 | source_video_003 | `issue_68_video_003_topic_proposal_028` | Психосоматика | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_028_psychosomatics` |
| 245 | source_video_003 | `issue_68_video_003_topic_proposal_036` | Психосоматика | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_036_psychosomatics` |
| 246 | source_video_003 | `issue_68_video_003_topic_proposal_060` | Цель жизни | LINK_CLEAR | `issue_68_link_issue_68_video_003_topic_proposal_060_life_goals` |

## 4. Отложенные связи — не принимать автоматически

| № | Источник | Topic ID | Понятие | Link ID |
|---:|---|---|---|---|
| 1 | source_video_001 | `issue_113_reviewed_topic_27` | Мышечное тестирование | `issue_68_link_issue_113_reviewed_topic_27_muscle_testing` |
| 2 | source_video_004 | `issue_68_video_004_topic_proposal_061` | Протокол работы | `issue_68_link_issue_68_video_004_topic_proposal_061_protocol` |
| 3 | source_video_003 | `issue_68_video_003_topic_proposal_071` | Эмоции | `issue_68_link_issue_68_video_003_topic_proposal_071_emotion` |
| 4 | source_video_003 | `issue_68_video_003_topic_proposal_088` | Мозг | `issue_68_link_issue_68_video_003_topic_proposal_088_brain` |
| 5 | source_video_004 | `issue_68_video_004_topic_proposal_043` | Меридианы | `issue_68_link_issue_68_video_004_topic_proposal_043_meridians` |
| 6 | source_video_003 | `issue_68_video_003_topic_proposal_019` | Подсознание | `issue_68_link_issue_68_video_003_topic_proposal_019_subconscious` |
| 7 | source_video_004 | `issue_68_video_004_topic_proposal_052` | Подсознание | `issue_68_link_issue_68_video_004_topic_proposal_052_subconscious` |

## 5. Исключения машинной транскрипции

Транскрипция остаётся машинного происхождения, не полностью подтверждённой человеком.

| ID | Источник | Машинная форма | Предполагаемая форма | Действие |
|---|---|---|---|---|
| `issue_68_transcript_exception_craniosacral_term` | source_video_002 | крайне-сакральный / крайне сакральный | краниосакральный | SELECTIVE_VERIFICATION_WITHOUT_TRANSCRIPT_MUTATION |
| `issue_68_transcript_exception_regression_term` | source_video_004 | рецессия | регрессия | SELECTIVE_VERIFICATION_WITHOUT_TRANSCRIPT_MUTATION |

## 6. Граница авторского решения

Владелец уже утвердил 52 отдельных решения по связям (37 ACCEPT, 9 REJECT, 6 DEFER), и ранее отложенная связь сохранена. **Эти решения не равны итоговому принятию 182 тем и 22 понятий.**

Возможное итоговое решение: принять семантическую структуру **в пределах поддержанных четырёх видео**, сохранив 7 DEFER и 2 выборочных исключения транскрипции, либо отклонить итоговую структуру с конкретными замечаниями. Итоговое принятие должно быть связано с точным QA-пакетом и пройти существующий governed workflow. Не изменять этот документ вместо авторитетного журнала решений.
