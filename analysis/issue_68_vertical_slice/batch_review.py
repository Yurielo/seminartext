"""Issue #68 batch presentation and atomic admission of explicit link decisions.

The existing DOMAIN_REVIEW ledger and QA builder remain the semantic authority.
This module never chooses an outcome: every action and governed decision record
must be supplied explicitly by the human reviewer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import build_domain_review_qa as governed
from jsonschema import Draft202012Validator


ACTIONS = {
    "ACCEPT": "ACCEPT_LINK",
    "REJECT": "REJECT_LINK",
    "REASSIGN": "REMAP_LINK",
    "DEFER": "DEFER_LINK",
}
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas/issue_68_batch_review_v1.schema.json"

# These are non-authoritative review proposals for the bounded Issue #68 packet.
# They are presentation-only: ``apply_batch`` still requires a hash-bound,
# explicit Product Owner decision.  Each note cites the evidence actually shown
# for its link; no action is inferred from a label or keyword alone.
RECOMMENDATIONS: dict[str, tuple[str, str, str, str]] = {
    "issue_68_link_issue_68_video_002_topic_proposal_069_correction": ("REJECT", "В теме о целях сессии слово «коррекциями» служит общим описанием результата сессий, без объяснения терапевтического действия.", "подтверждено владельцем; ledger ждёт hash-bound submission", "CONFIRMED_OWNER_DECISION"),
    "issue_68_link_issue_68_video_002_topic_proposal_082_correction": ("REJECT", "Фрагмент объясняет шкалу тестирования УНЭ/УП; самостоятельного объяснения коррекции как терапевтического действия в нём нет.", "средняя: доступный диапазон не развивает понятие", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_001_correction": ("REJECT", "Во вводном обсуждении участницу просят сообщить результат после показательной коррекции; это отчёт о прошлом примере, а не разбор коррекции.", "низкая: роль упоминания явно справочная", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_021_correction": ("ACCEPT", "Инструкция клиенту задаёт условие «когда коррекция пройдёт» и сопровождает его конкретным действием и проверкой мышц; коррекция — часть демонстрируемой процедуры.", "средняя: термин не определяется отдельно", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_027_correction": ("ACCEPT", "После вопросов о родителях ведущий предписывает снять стресс и провести коррекцию; это следующий рабочий шаг темы, а не случайное упоминание.", "средняя: источник не раскрывает полный метод коррекции", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_032_correction": ("REJECT", "При разборе рефлекса Моро сказано, что эмоциональными коррекциями проблему не решить, и предлагаются другие средства; коррекция названа только как неуместный вариант.", "низкая: отрицательная роль понятия выражена прямо", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_047_correction": ("ACCEPT", "Тема учит находить точку для коррекции мышечным тестом, перечисляет точки и интерпретирует слабый ответ; понятие составляет предмет процедуры.", "низкая: связь поддержана последовательным описанием", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_057_correction": ("ACCEPT", "Фрагмент объясняет, что при коррекции высвобождается энергия, и как её направить после сессии; это предметное последствие коррекции.", "средняя: объясняется эффект, а не техника", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_002_topic_proposal_007_protocol": ("ACCEPT", "Претесты прямо названы первым пунктом протокола и объяснены как подготовка мышцы к тестированию.", "низкая: роль в протоколе названа явно", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_002_topic_proposal_061_protocol": ("ACCEPT", "Ведущий вводит последовательность пунктов протокола, включая претесты и получение разрешения на работу; протокол организует тему.", "низкая: есть последовательное описание шагов", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_061_protocol": ("DEFER", "В доступном коротком фрагменте лишь обещана демонстрация «в одну сессию»; содержание и роль протокола не раскрыты.", "высокая: требуется более широкий исходный контекст", "INSUFFICIENT_EVIDENCE"),
    "issue_68_link_issue_68_video_002_topic_proposal_002_emotion": ("REJECT", "При введении мышечного тестирования эмоции перечислены как один из видов стресса наряду с химическим; самостоятельного разбора эмоций нет.", "низкая: понятие используется как классификационный пример", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_002_topic_proposal_058_emotion": ("ACCEPT", "Страх, гнев и обида проверяются как эмоциональные причины слабого ответа, после чего описывается работа с найденной эмоцией.", "низкая: эмоции являются объектом проверки", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_002_topic_proposal_084_emotion": ("ACCEPT", "Ведущий предлагает измерять уровень негативных эмоций и демонстрирует это тестирование перед упражнением для иммунитета.", "средняя: эмоции — рабочий параметр, хотя тема включает второй предмет", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_006_emotion": ("ACCEPT", "Эмоции названы одной из сторон треугольника здоровья и фактором патологических состояний в объяснении приоритетов.", "низкая: понятие раскрыто в модели темы", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_042_emotion": ("ACCEPT", "Карта эмоций названа одним из основных инструментов при антистрессовой коррекции и обсуждении материала.", "средняя: раскрыта инструментальная, а не теоретическая роль", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_071_emotion": ("DEFER", "Фрагмент говорит о самоощущении на карте эмоций, но основное объяснение посвящено смене модели поведения и терапии подсознания.", "высокая: доступный контекст не устанавливает, является ли эмоция самостоятельным предметом", "INSUFFICIENT_EVIDENCE"),
    "issue_68_link_issue_68_video_003_topic_proposal_072_emotion": ("ACCEPT", "В коррекции ДПДГ состояние определяется по карте эмоций и заменяется уравновешивающим состоянием; эмоции управляют демонстрацией.", "средняя: термин раскрыт через применение карты", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_026_emotion": ("ACCEPT", "При разборе поведенческих моделей ведущий прямо предписывает определять эмоции для состояния родителей и раннего периода.", "средняя: роль эмоций процедурно существенна", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_002_topic_proposal_010_nervous_system": ("ACCEPT", "Перенапряжение нервной системы описано как состояние, его признаки и способ снять блокировку объясняются в теме.", "низкая: понятие — предмет объяснения", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_026_neural_connections_and_networks": ("ACCEPT", "Текст объясняет построение нервных связей и сетей, которые запоминают жизненный опыт и направляют реакции.", "низкая: понятие раскрыто прямо", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_086_nervous_system": ("ACCEPT", "Позитивное воспоминание описано как новая опора, на которую будет опираться нервная система при формировании поведения.", "средняя: роль системы объяснена причинно", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_090_nervous_system": ("ACCEPT", "В теме негативного поведения нервная система названа анализатором базы опыта, для которой создаётся позитивная опора.", "средняя: понятие поддерживает объяснение поведения", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_092_nervous_system": ("ACCEPT", "Фрагмент связывает позитивный опыт с тем, на что будет опираться нервная система, и помещает это в ход работы по протоколу.", "средняя: роль системы предметно объяснена", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_014_nervous_system": ("ACCEPT", "Семейная модель поведения объясняется тем, что нервная система сохраняет полезное для выживания и записывает его в генетике.", "средняя: это авторское объяснение причин модели", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_014_neural_connections_and_networks": ("ACCEPT", "Та же семейная модель прямо описана как запись в психике с помощью нейронных связей.", "низкая: связь сформулирована в источнике", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_040_nervous_system": ("REJECT", "В доступном диапазоне перечислены меридианы, гимнастика для мозга и вопросы; «нервная система» не объясняется и не упоминается.", "низкая: исходная опора для связи отсутствует", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_031_adaptation": ("ACCEPT", "Сужение поля зрения объяснено как реакция на стресс и связано с нереализованными адаптационными механизмами.", "низкая: понятие раскрыто причинно", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_026_brain": ("REJECT", "В теме о нервных сетях мозг упомянут лишь в пояснении, что вместе с ним прекращается жизненный опыт; предметом остаются сети и опыт.", "низкая: это фоновое упоминание", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_041_brain": ("ACCEPT", "Антистрессовая коррекция связывается с затылочной частью мозга, зрительной корой и лобными долями; мозг объясняет наблюдаемый эффект.", "низкая: есть несколько предметных ссылок", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_085_brain": ("ACCEPT", "Рассказ о Пенфилде связывает разные части мозга с воспроизведением событий и описывает хранение воспоминаний.", "низкая: мозг — предмет примера", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_088_brain": ("DEFER", "Доступный диапазон разбирает память и нейронные связи; явного предметного объяснения мозга в нём нет.", "высокая: без более широкого контекста нельзя установить связь", "INSUFFICIENT_EVIDENCE"),
    "issue_68_link_issue_68_video_004_topic_proposal_008_meridians": ("ACCEPT", "В ходе закладки позитива ведущий даёт последовательность действий, где после дыхания нужно промахивать меридианы.", "средняя: меридианы входят в демонстрируемое упражнение", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_039_meridians": ("REJECT", "В длинном разборе генетической линии промахивание меридианов перечислено среди общей разминки, без объяснения меридианов.", "низкая: понятие остаётся фоновым действием", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_043_meridians": ("DEFER", "Источник упоминает меридианы при перечислении материалов, но не объясняет их роль в работе с информацией.", "высокая: доступный диапазон не показывает предметную связь", "INSUFFICIENT_EVIDENCE"),
    "issue_68_link_issue_68_video_003_topic_proposal_076_extraocular_muscles": ("ACCEPT", "При сравнении очной и онлайн работы объясняется, что движение глаз по фигурам вовлекает глазодвигательные мышцы.", "низкая: физиологическая роль названа прямо", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_074_extraocular_muscles": ("ACCEPT", "Упражнение требует двигать глазами по кругу с максимальной траекторией, ограниченной глазодвигательными мышцами.", "низкая: понятие является частью инструкции", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_113_reviewed_topic_08_consciousness": ("ACCEPT", "Ведущий прямо формулирует уровни развития сознания по Дэвиду Хокинсу и поясняет их через близость к состоянию счастья.", "низкая: понятие объяснено самостоятельно", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_015_three_level_awareness": ("ACCEPT", "Три уровня — сознание, подсознание и тело — перечислены и применяются для определения уровня проблемы тестированием.", "низкая: состав и применение понятия раскрыты", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_016_three_level_awareness": ("ACCEPT", "Участникам предлагается различить сознание, подсознание и тело по сильному и слабому ответу; три уровня образуют задание.", "средняя: объяснение краткое, но процедурно полное", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_019_three_level_awareness": ("ACCEPT", "Вопрос «где находится проблема» требует выбора между сознанием, подсознанием и телом; это непосредственное применение трёх уровней.", "средняя: контекст учебного примера достаточен", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_020_three_level_awareness": ("ACCEPT", "Последовательно тестируются сознание, подсознание и тело, чтобы определить уровень проблемы.", "низкая: все элементы понятия задействованы", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_019_subconscious": ("DEFER", "Подсознание лишь названо одним вариантом ответа наряду с сознанием и телом; отдельного объяснения подсознания нет.", "высокая: не следует превращать один ярлык в самостоятельную связь", "INSUFFICIENT_EVIDENCE"),
    "issue_68_link_issue_68_video_003_topic_proposal_071_subconscious": ("ACCEPT", "Терапия ДПДГ описана как работа со скрытыми областями, когда проблема находится на уровне подсознания или тела.", "средняя: подсознание — условие и предмет терапевтического объяснения", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_082_subconscious": ("ACCEPT", "Перед выбором коррекции ДПДГ проверяются сознание, подсознание и тело; подсознание — необходимый параметр процедуры.", "средняя: роль процедурная, а не отдельная теория", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_052_subconscious": ("DEFER", "В теме домашних заданий подсознание появляется в незавершённом объяснении, почему клиент не выполняет задание.", "высокая: доступный фрагмент не раскрывает причинную модель", "INSUFFICIENT_EVIDENCE"),
    "issue_68_link_issue_68_video_003_topic_proposal_045_memory": ("ACCEPT", "Карта эмоций включает клеточную память как уровень тела и затем объясняет структуру уровней и категорий карты.", "средняя: память является элементом объясняемой карты", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_003_topic_proposal_061_memory": ("ACCEPT", "Ведущий просит восстановить событие 2005 года и объясняет, что при отсутствии воспоминания настаивать не следует; воспоминание управляет упражнением.", "средняя: используется конкретный эпизод, а не определение памяти", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_013_memory": ("REJECT", "Текст обсуждает наследование событий и генную информацию предков, но не объясняет память как понятие.", "средняя: нельзя приравнять генную информацию к памяти без решения владельца", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_015_memory": ("ACCEPT", "Нервная система описана как сохраняющая опыт, полезный для выживания, включая запись генной информации.", "средняя: авторское употребление прямо связывает тему с запоминанием", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_077_memory": ("ACCEPT", "В упражнении школьное воспоминание наполняется погодой, запахами и позитивным состоянием; воспоминание — материал работы.", "низкая: процедура построена вокруг воспоминания", "MACHINE_RECOMMENDATION"),
    "issue_68_link_issue_68_video_004_topic_proposal_042_trauma": ("ACCEPT", "Позитивное воспоминание создаётся взамен травмирующего; травма задаёт предмет замены в описанной технике.", "средняя: понятие используется как необходимый контраст", "MACHINE_RECOMMENDATION"),
}


def recommendation_for(entry: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return a presentation-only recommendation for one governed entry."""
    recommendation = RECOMMENDATIONS.get(entry["link_id"])
    if recommendation is not None:
        return recommendation
    # A valid later rebuild can expose a different unresolved link. Do not
    # extend a prior semantic proposal to it: present the safe default only.
    return (
        "DEFER",
        "Для этой новой нерешённой связи в пакете ещё нет проверенной индивидуальной рекомендации.",
        "высокая: нужен отдельный анализ исходного контекста",
        "INSUFFICIENT_EVIDENCE",
    )


def validate_schema(value: Any) -> None:
    schema = json.loads(SCHEMA_PATH.read_bytes())
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        raise ValueError("batch schema invalid: " + errors[0].message)


def encoded(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(link: dict[str, Any]) -> dict[str, Any]:
    return {key: link[key] for key in (
        "input_topic_reference", "candidate_concept_reference", "source_id",
        "classification", "exact_term_target_references", "evidence_support",
    )}


def prepare(qa_path: Path, evidence_path: Path, semantic_path: Path) -> dict[str, Any]:
    qa_bytes = qa_path.read_bytes()
    qa = json.loads(qa_bytes)
    evidence_bytes = evidence_path.read_bytes()
    if digest(evidence_bytes) != qa["input_inventory"]["canonical_evidence_sha256"]:
        raise ValueError("Canonical Evidence hash differs from QA input")
    evidence = json.loads(evidence_bytes)
    words = {word["id"]: word for word in evidence["words"]}
    semantic_bytes = semantic_path.read_bytes()
    if digest(semantic_bytes) != qa["input_inventory"]["semantic_package_sha256"]:
        raise ValueError("Semantic package hash differs from QA input")
    semantic = json.loads(semantic_bytes)
    topics = {topic["topic_id"]: {**topic, "display_title": topic["title"]}
              for topic in qa["topic_results"]}
    topics.update({topic["proposal_id"]: {**topic, "display_title": topic["proposed_title"]}
                   for topic in semantic["topic_proposals"]})
    topics.update({topic["topic_id"]: {**topic, "display_title": topic["title"]}
                   for topic in semantic["day_1"]["topics"]})
    concepts = {concept["candidate_concept_id"]: concept for concept in qa["concept_results"]}
    decided = {item["target_link_id"] for item in qa["link_review_resolutions"]}
    active, deferred = [], []
    for link in qa["link_results"]:
        if link["classification"] != "LINK_EXCEPTION":
            continue
        link_id = link["link_id"]
        if link_id in decided and link.get("domain_review_status") != "DEFERRED":
            raise ValueError(f"decided link remains unresolved: {link_id}")
        topic = topics[link["input_topic_reference"]]
        concept = concepts[link["candidate_concept_reference"]]
        topic_start = words[topic["start_word_id"]]["sequence"]
        topic_end = words[topic["end_word_id"]]["sequence"]
        topic_text = " ".join(word["text"] for word in evidence["words"]
                             if word["source_id"] == link["source_id"]
                             and topic_start <= word["sequence"] <= topic_end)
        spans, source_texts = [], []
        for support in link["evidence_support"]:
            start = words[support["intersection_start_word_id"]]
            end = words[support["intersection_end_word_id"]]
            if start["source_id"] != link["source_id"] or end["source_id"] != link["source_id"]:
                raise ValueError(f"cross-source evidence: {link_id}")
            source_text = " ".join(word["text"] for word in evidence["words"]
                if word["source_id"] == link["source_id"]
                and start["sequence"] <= word["sequence"] <= end["sequence"])
            if digest(source_text.encode()) != support["intersection_sha256"]:
                raise ValueError(f"source evidence hash mismatch: {link_id}")
            source_texts.append(source_text)
            spans.append({
                "start_word_id": start["id"], "end_word_id": end["id"],
                "source_revision_id": start["transcript_revision_id"],
                "evidence_sha256": support["intersection_sha256"],
                "exact_pattern_match_count": support["exact_pattern_match_count"],
            })
        if not spans or len({item["source_revision_id"] for item in spans}) != 1:
            raise ValueError(f"missing or mixed source revisions: {link_id}")
        pattern_key = link["candidate_concept_reference"].removeprefix("issue_68_candidate_concept_")
        concept_pattern = governed.CONCEPT_PATTERNS[pattern_key]
        # The old overlap-only preview was too short to support a human
        # semantic decision.  Render a bounded excerpt from the full authored
        # Topic range instead; the package still carries the exact hash-bound
        # intersection ranges separately.
        found = re.search(concept_pattern, topic_text, re.IGNORECASE)
        if found:
            mention_excerpt = topic_text[max(0, found.start() - 360):found.end() + 640]
        else:
            mention_excerpt = topic_text[:1000]
        exact_mentions = sum(span["exact_pattern_match_count"] for span in spans)
        entry = {
            "link_id": link_id,
            "topic_id": link["input_topic_reference"], "topic_title": topic["display_title"],
            "concept_id": concept["candidate_concept_id"],
            "concept_label": concept["proposed_canonical_label"],
            "source_id": link["source_id"],
            "source_revision_id": spans[0]["source_revision_id"],
            "evidence_sha256": digest(encoded(spans)),
            "evidence_ranges": spans,
            "topic_range": {"start_word_id": topic["start_word_id"], "end_word_id": topic["end_word_id"]},
            "canonical_evidence_reference": "evidence/canonical_bundle.json",
            "exception_reason": link["exception"]["problem"],
            "mention_excerpt": mention_excerpt,
            "exact_mentions_in_evidence": exact_mentions,
            "evidence_complete": topic["start_word_id"] in words and topic["end_word_id"] in words
                and all(item["start_word_id"] in words and item["end_word_id"] in words for item in spans),
            "explanation_ru": (
                "В теме «" + topic["display_title"] + "» предложена связь с понятием «"
                + concept["proposed_canonical_label"] + "». В связанных фрагментах найдено точных упоминаний: "
                + str(exact_mentions) + ". Нужно проверить, раскрывается ли понятие по существу."
            ),
            "available_decisions": list(ACTIONS),
            "group": {"concept_id": concept["candidate_concept_id"], "source_id": link["source_id"],
                      "reason": link["relevance_basis"], "topic_lineage": link["overlapping_authored_topic_references"]},
            "governed_link_snapshot": snapshot(link),
            "deferred": link.get("domain_review_status") == "DEFERRED",
        }
        (deferred if entry["deferred"] else active).append(entry)
    if len(active) != qa["summary"]["link_exception"] - qa["summary"]["link_deferred"]:
        raise ValueError("active exception coverage mismatch")
    if len(deferred) != qa["summary"]["link_deferred"]:
        raise ValueError("deferred exception coverage mismatch")
    if len({item["link_id"] for item in active + deferred}) != len(active) + len(deferred):
        raise ValueError("duplicate batch link")
    group_index: dict[str, dict[str, list[str]]] = {
        "concept": {}, "source": {}, "reason": {}, "topic_lineage": {},
    }
    for item in active:
        keys = {
            "concept": item["concept_id"],
            "source": item["source_id"],
            "reason": item["group"]["reason"],
            "topic_lineage": ",".join(item["group"]["topic_lineage"]),
        }
        for dimension, value in keys.items():
            group_index[dimension].setdefault(value, []).append(item["link_id"])
    package = {
        "schema_version": "1.0.0", "artifact_type": "seminartext.issue_68_batch_domain_review",
        "semantic_authority": "PROVISIONAL_UNREVIEWED", "qa_sha256": digest(qa_bytes),
        "canonical_evidence_sha256": digest(evidence_bytes),
        "decision_ledger_sha256": qa["input_inventory"]["domain_review_decisions_sha256"],
        "active": active, "deferred": deferred, "groups": group_index,
    }
    validate_schema(package)
    return package


def markdown(package: dict[str, Any]) -> str:
    lines = [
        "# Консолидированная DOMAIN_REVIEW-проверка — Issue #68",
        "",
        "Это один пакет рекомендаций, а не решение системы. Семантическое решение принимает только владелец.",
        "",
        "## Как подтвердить пакет",
        "",
        "Можно подтвердить все рекомендации этого точного пакета, подтвердить их с перечисленными исключениями, отклонить отдельные рекомендации или отложить отдельные связи. Неупомянутые связи остаются нерешёнными; молчание не означает согласие.",
        "",
        "Технические ID, диапазоны слов, ревизии источников и SHA-256 находятся в неизменяемом машинном приложении `batch_review.json`.",
        "",
        "## Уже подтверждено владельцем",
        "",
        "- Связь «Постановка Целей Сессии» → «Коррекция» должна быть отклонена: в теме есть лишь упоминание коррекции, а не её предметное объяснение. Решение сохранено из обсуждения PR #121 и не требует повторного решения.",
        "",
        "## Активные рекомендации",
        "",
    ]
    by_concept: dict[str, list[dict[str, Any]]] = {}
    for entry in package["active"]:
        by_concept.setdefault(entry["concept_label"], []).append(entry)
    for concept, entries in by_concept.items():
        lines += [f"### {concept}", "", "| Источник | Тема | Контекст | Статус | Рекомендация | Основание и неопределённость |", "| --- | --- | --- | --- | --- | --- |"]
        for entry in entries:
            action, rationale, uncertainty, status = recommendation_for(entry)
            context = entry["mention_excerpt"].replace("|", "\\|").replace("\n", " ")
            basis = f"{rationale} Неопределённость: {uncertainty}."
            lines.append("| " + " | ".join((
                entry["source_id"], entry["topic_title"].replace("|", "\\|"), context,
                status, action, basis.replace("|", "\\|"),
            )) + " |")
        lines += ["", "Идентификаторы этой группы: " + ", ".join(
            f"`{entry['link_id']}`" for entry in entries) + ".", ""]
    insufficient = [entry for entry in package["active"]
                    if recommendation_for(entry)[3] == "INSUFFICIENT_EVIDENCE"]
    insufficient_labels = "; ".join(
        f"«{entry['topic_title']}» → «{entry['concept_label']}»" for entry in insufficient
    )
    lines += [
        f"Активных связей: **{len(package['active'])}**. Все 52 имеют индивидуальную рекомендацию; группировка не объединяет решения.",
        "", "## Особое внимание и отложенные вопросы", "",
        "- `INSUFFICIENT_EVIDENCE` / рекомендован `DEFER`: " + insufficient_labels + ".",
        "- В двух местах есть selective transcript-verification exceptions; они сохранены в `domain_review_qa.json` и не являются семантическим подтверждением.",
        "- Четыре видео имеют Canonical Evidence/Word Timeline; три зарегистрированных документа не имеют Canonical Evidence. Это не полное покрытие всех семи источников.",
        "", "## PREVIOUSLY_DEFERRED", "",
    ]
    for entry in package["deferred"]:
        lines.append(f"- `{entry['link_id']}` — {entry['topic_title']} / {entry['concept_label']}: ранее подтверждённое `DEFER`; остаётся доступной для последующей проверки полного контекста.")
    lines += ["", "Допустимые решения: ACCEPT, REJECT, REASSIGN (с точным Topic ID), DEFER. Каждое решение вносится только через существующий hash-bound workflow.", ""]
    return "\n".join(lines)


def apply_batch(package_path: Path, batch_path: Path, ledger_path: Path,
                repository: Path, project: Path, review_result: Path,
                semantic_package: Path, output_dir: Path) -> str:
    package_bytes = package_path.read_bytes()
    package = json.loads(package_bytes)
    batch = json.loads(batch_path.read_bytes())
    validate_schema(package)
    validate_schema(batch)
    ledger_bytes = ledger_path.read_bytes()
    ledger_sha = digest(ledger_bytes)
    if batch.get("review_package_sha256") != digest(package_bytes):
        raise ValueError("stale review package hash")
    original = json.loads(ledger_bytes)
    existing_by_id = {d["decision_id"]: d for d in original["link_decisions"]}
    existing_by_link = {d["target_link_id"]: d for d in original["link_decisions"]}
    historical_ids = {d["decision_id"] for key in ("decisions", "concept_identity_decisions", "link_decisions", "topic_title_corrections")
                      for d in original.get(key, [])}
    entries = batch.get("decisions")
    if not isinstance(entries, list) or not entries:
        raise ValueError("batch requires explicit decisions")
    if any(not isinstance(item, dict) or not isinstance(item.get("governed_decision"), dict) for item in entries):
        raise ValueError("malformed batch decision")
    if len({item.get("link_id") for item in entries}) != len(entries) or len({item.get("governed_decision", {}).get("decision_id") for item in entries}) != len(entries):
        raise ValueError("duplicate batch decision")
    active = {item["link_id"]: item for item in package["active"]}
    for entry in entries:
        link_id = entry["link_id"]
        decision = entry["governed_decision"]
        if link_id not in active:
            raise ValueError(f"unknown or unavailable link: {link_id}")
        item = active[link_id]
        if entry["review_package_sha256"] != digest(package_bytes):
            raise ValueError("stale per-link review package hash")
        for key in ("topic_id", "concept_id", "source_revision_id", "evidence_sha256"):
            if entry.get(key) != item[key]:
                raise ValueError(f"stale {key} for {link_id}")
        if entry.get("action") not in ACTIONS or decision.get("outcome") != ACTIONS[entry["action"]]:
            raise ValueError("unsupported action")
        if decision.get("authority") != "PRODUCT_OWNER_DOMAIN_REVIEW" or entry.get("human_confirmed") is not True:
            raise ValueError("explicit human DOMAIN_REVIEW authority required")
        if decision.get("target_link_id") != link_id or decision.get("link_snapshot") != item["governed_link_snapshot"]:
            raise ValueError("governed decision snapshot mismatch")
    already_applied = [
        existing_by_id.get(item.get("governed_decision", {}).get("decision_id")) == item.get("governed_decision")
        and existing_by_link.get(item.get("link_id")) == item.get("governed_decision")
        for item in entries
    ]
    if all(already_applied):
        verified = governed.build_qa(repository, project, review_result, semantic_package, ledger_path)
        if verified["status"] == "INVALID" or verified["errors"]:
            raise ValueError("governed idempotent retry validation failed")
        with tempfile.TemporaryDirectory(prefix="issue68-batch-output-", dir=output_dir) as staging:
            governed.write_review_outputs(Path(staging), verified, ledger_path,
                project / "evidence" / "canonical_bundle.json", semantic_package)
            for name in ("domain_review_qa.json", "DOMAIN_REVIEW.md", "batch_review.json", "BATCH_REVIEW.md", "manifest.json"):
                os.replace(Path(staging) / name, output_dir / name)
        return ledger_sha
    if any(already_applied):
        raise ValueError("partially applied or conflicting retry")
    if any(item["governed_decision"]["decision_id"] in historical_ids
           or item["link_id"] in existing_by_link for item in entries):
        raise ValueError("duplicate historical decision")
    if batch.get("decision_ledger_sha256") != ledger_sha or package["decision_ledger_sha256"] != ledger_sha:
        raise ValueError("stale decision ledger")
    current_qa = governed.build_qa(repository, project, review_result, semantic_package, ledger_path)
    if current_qa["status"] == "INVALID" or package["qa_sha256"] != digest(encoded(current_qa)):
        raise ValueError("stale or invalid current QA")
    with tempfile.TemporaryDirectory(prefix="issue68-batch-package-") as staging:
        qa_path = Path(staging) / "domain_review_qa.json"
        qa_path.write_bytes(encoded(current_qa))
        expected_package = prepare(qa_path, project / "evidence" / "canonical_bundle.json",
                                   semantic_package)
        if encoded(expected_package) != package_bytes:
            raise ValueError("review package differs from current governed evidence")
    seen_links, seen_ids, pending = set(), set(), []
    for entry in entries:
        link_id = entry.get("link_id")
        decision = entry.get("governed_decision")
        if not isinstance(decision, dict):
            raise ValueError("missing governed decision")
        decision_id = decision.get("decision_id")
        if link_id in seen_links or decision_id in seen_ids:
            raise ValueError("duplicate batch decision")
        seen_links.add(link_id); seen_ids.add(decision_id)
        if not decision_id or decision_id in historical_ids or link_id in existing_by_link:
            raise ValueError("duplicate historical decision")
        pending.append(decision)
    candidate = {**original, "link_decisions": original["link_decisions"] + pending}
    with tempfile.TemporaryDirectory(prefix="issue68-batch-validate-") as staging:
        candidate_path = Path(staging) / "decisions.json"
        candidate_path.write_bytes(encoded(candidate))
        if original.get("topic_title_corrections"):
            parent_hash = original["title_review_revision"]["parent_ledger_sha256"]
            relative = Path("revisions") / f"{parent_hash}.json"
            (Path(staging) / relative).parent.mkdir()
            (Path(staging) / relative).write_bytes((ledger_path.parent / relative).read_bytes())
        verified = governed.build_qa(repository, project, review_result, semantic_package, candidate_path)
        if verified["status"] == "INVALID" or verified["errors"]:
            raise ValueError("governed validation failed: " + "; ".join(verified["errors"]))
        if len(verified["link_review_resolutions"]) != len(current_qa["link_review_resolutions"]) + len(pending):
            raise ValueError("incomplete batch application")
        with tempfile.TemporaryDirectory(prefix="issue68-batch-output-", dir=output_dir) as output_staging:
            governed.write_review_outputs(Path(output_staging), verified, candidate_path,
                project / "evidence" / "canonical_bundle.json", semantic_package)
            # The ledger is the single authoritative decision artifact. Replace it
            # once after the entire batch and all derived outputs have validated.
            if digest(ledger_path.read_bytes()) != ledger_sha:
                raise ValueError("ledger changed during validation")
            fd, temporary_name = tempfile.mkstemp(prefix=".batch-decisions-", dir=ledger_path.parent)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(encoded(candidate)); stream.flush(); os.fsync(stream.fileno())
                os.replace(temporary_name, ledger_path)
                for name in ("domain_review_qa.json", "DOMAIN_REVIEW.md", "batch_review.json", "BATCH_REVIEW.md", "manifest.json"):
                    os.replace(Path(output_staging) / name, output_dir / name)
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)
    return digest(encoded(candidate))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--qa", type=Path, required=True)
    prep.add_argument("--evidence", type=Path, required=True)
    prep.add_argument("--semantic-package", type=Path, required=True)
    prep.add_argument("--output-dir", type=Path, required=True)
    apply = sub.add_parser("apply")
    for name in ("package", "batch", "ledger", "repository", "project", "review-result", "semantic-package"):
        apply.add_argument("--" + name, type=Path, required=True)
    apply.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        package = prepare(args.qa, args.evidence, args.semantic_package)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "batch_review.json").write_bytes(encoded(package))
        (args.output_dir / "BATCH_REVIEW.md").write_text(markdown(package), encoding="utf-8")
        print(f"ACTIVE={len(package['active'])} DEFERRED={len(package['deferred'])}")
    else:
        print("LEDGER_SHA256=" + apply_batch(args.package, args.batch, args.ledger,
            args.repository, args.project, args.review_result, args.semantic_package,
            args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
