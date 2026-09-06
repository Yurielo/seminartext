#!/usr/bin/env python3
"""Build the Issue #68 provisional semantic-authoring review package.

The builder projects existing machine Topic candidates onto Canonical Word
ranges and prepares conservative Concept/link candidates.  It never writes to
the inspected project and never marks machine semantics as accepted.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


SOURCE_NUMBERS = (2, 3, 4)
DECISIONS = [
    "ACCEPT",
    "RENAME",
    "REALIGN",
    "SPLIT",
    "MERGE",
    "EXCLUDE_NON_SEMANTIC",
    "OTHER",
]
AUTHORING_DISPOSITIONS = {"SEMANTIC_TOPIC", "NON_SEMANTIC_EXCLUDED"}

# These are proposal seeds, not Canonical Concept identities.  Matching is
# deliberately transparent and conservative; identity remains a human gate.
CONCEPT_SEEDS = [
    ("stress", "Стресс", ["стресс", "стресса", "стрессом"], "Стресс и его проявления."),
    ("kinesiology", "Кинезиология", ["кинезиология", "кинезиологии", "кинезиологический"], "Кинезиологический подход и практика."),
    ("muscle_testing", "Мышечное тестирование", ["мышечное тестирование", "мышечного тестирования", "мышечный тест"], "Получение и проверка информации посредством мышечного теста."),
    ("correction", "Коррекция", ["коррекция", "коррекции", "коррекцию"], "Практика коррекции выявленного состояния."),
    ("protocol", "Протокол работы", ["протокол", "протокола", "протоколу"], "Последовательность действий в практической работе."),
    ("emotion", "Эмоции", ["эмоции", "эмоций", "эмоциональный", "эмоциональное"], "Эмоциональные состояния и реакции."),
    ("nervous_system", "Нервная система", ["нервная система", "нервной системы", "нервная сеть", "нейронные сети"], "Нервная система и нейронные процессы."),
    ("adaptation", "Адаптация", ["адаптация", "адаптации", "адаптивный"], "Адаптация организма и поведения."),
    ("brain", "Мозг и полушария", ["мозг", "мозга", "полушарий", "полушария"], "Работа мозга и взаимодействие полушарий."),
    ("meridians", "Меридианы", ["меридианы", "меридианов", "меридиан"], "Меридианы в методологии семинара."),
    ("eye_movement", "Движения глаз и ДПДГ", ["дпдг", "движения глаз", "глазодвигательная", "глазодвигательные"], "Коррекционные практики, связанные с движениями глаз."),
    ("consciousness", "Уровни сознания", ["уровни сознания", "уровни осознания", "уровень осознавания"], "Уровни сознания и осознавания."),
    ("subconscious", "Подсознание", ["подсознание", "подсознанием", "подсознательного"], "Работа с подсознательными процессами."),
    ("memory", "Память", ["память", "памяти", "воспоминания", "запоминание"], "Память, воспоминания и запоминание."),
    ("trauma", "Травма", ["травма", "травмы", "травматический"], "Травматический опыт и его последствия."),
    ("psychosomatics", "Психосоматика", ["психосоматика", "психосоматический"], "Связь психических состояний и телесных проявлений."),
    ("life_goals", "Жизненные цели", ["жизненные цели", "цели жизни", "жизненная цель"], "Цели и направленность жизни."),
    ("self_regulation", "Саморегуляция", ["саморегуляция", "самовосстановление", "управление стрессом"], "Саморегуляция и восстановление состояния."),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_time(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def excerpt(words: list[dict[str, Any]], center: int, radius: int = 8) -> dict[str, Any]:
    left = max(0, center - radius)
    right = min(len(words), center + radius + 1)
    selected = words[left:right]
    return {
        "start_word_id": selected[0]["id"],
        "end_word_id": selected[-1]["id"],
        "text": " ".join(word["text"] for word in selected),
    }


def recommendation(topic: dict[str, Any], boundary_kind: str) -> tuple[str, list[str]]:
    title = topic["title"].casefold()
    summary = topic.get("summary", "").casefold()
    flags: list[str] = []
    if topic.get("qa_status") != "ok" or "ручной проверки" in title:
        flags.extend(["MALFORMED_TITLE_RISK", "TITLE_LOCAL_FRAGMENT_BIAS_REVIEW"])
        return "RENAME", flags
    if any(token in f"{title} {summary}" for token in ("перерыв", "обед", "техническ", "приветств")):
        flags.append("NON_SEMANTIC_CONTENT_CANDIDATE")
        return "EXCLUDE_NON_SEMANTIC", flags
    duration = topic["end_seconds"] - topic["start_seconds"]
    if duration < 45:
        flags.append("VALID_SHORT_TOPIC_REQUIRES_SEMANTIC_REVIEW")
    if duration > 600:
        flags.append("VALID_LONG_TOPIC_REQUIRES_SEMANTIC_REVIEW")
    if boundary_kind == "FIXED_WINDOW_EDGE":
        flags.append("LOCAL_WINDOW_EDGE_REVIEW")
    if any(token in title for token in ("этап", "упражнен", "тестирован", "коррекц")):
        flags.append("PROCEDURAL_CONTINUITY_REVIEW")
    return "ACCEPT", flags


def confidence(topic: dict[str, Any], flags: list[str]) -> dict[str, Any]:
    level = "MEDIUM"
    basis = ["legacy_gemma3_4b_two_stage_candidate"]
    if topic.get("qa_status") != "ok":
        level = "LOW"
        basis.append("label_fallback_requires_human_review")
    if "LOCAL_WINDOW_EDGE_REVIEW" in flags:
        level = "LOW"
        basis.append("issue_113_local_window_edge_regression_risk")
    basis.append("no_calibrated_probability_available")
    return {"level": level, "basis": basis}


def build_package(
    project: Path,
    review_result_path: Path,
    decisions_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle_path = project / "evidence/canonical_bundle.json"
    bundle = read_json(bundle_path)
    review_result = read_json(review_result_path)
    bundle_hash = sha256(bundle_path)
    errors: list[str] = []

    if review_result.get("application_status") != "APPLIED":
        errors.append("Day-1 Topic review result is not APPLIED")
    if review_result.get("canonical_evidence", {}).get("sha256") != bundle_hash:
        errors.append("Day-1 review is not bound to the current Canonical Evidence bundle")

    revisions = {item["source_id"]: item for item in bundle["transcript_revisions"]}
    words_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for word in bundle["words"]:
        words_by_source[word["source_id"]].append(word)
    for words in words_by_source.values():
        words.sort(key=lambda item: item["sequence"])

    decision_document: dict[str, Any] | None = None
    decisions_by_proposal: dict[str, dict[str, Any]] = {}
    if decisions_path is not None:
        decision_document = read_json(decisions_path)
        if decision_document.get("semantic_gate") != "DOMAIN_AUTHORING":
            errors.append("decision ledger is not a DOMAIN_AUTHORING artifact")
        for decision in decision_document.get("decisions", []):
            proposal_id = decision.get("proposal_id")
            if not proposal_id or proposal_id in decisions_by_proposal:
                errors.append(f"invalid or duplicate DOMAIN_AUTHORING decision for {proposal_id}")
                continue
            decisions_by_proposal[proposal_id] = decision

    proposals: list[dict[str, Any]] = []
    topic_input_hashes: dict[str, Any] = {}
    per_source: dict[str, Any] = {}
    for number in SOURCE_NUMBERS:
        registry_id = f"video_{number:03d}"
        source_id = f"source_{registry_id}"
        topic_path = project / "transcript" / registry_id / "topics.json"
        qa_path = project / "transcript" / registry_id / "topics_qa.json"
        if not topic_path.exists() or not qa_path.exists():
            errors.append(f"missing Topic generator output for {source_id}")
            continue
        topic_doc = read_json(topic_path)
        qa_doc = read_json(qa_path)
        if topic_doc.get("model") != "gemma3:4b" or topic_doc.get("detail") != "auto":
            errors.append(f"unexpected generator identity/configuration for {source_id}")
        if qa_doc.get("model") != "gemma3:4b" or qa_doc.get("detail") != "auto":
            errors.append(f"unexpected QA generator identity/configuration for {source_id}")

        topics = topic_doc.get("topics", [])
        words = words_by_source[source_id]
        timed = [(word["start_seconds"], word["sequence"]) for word in words if word.get("start_seconds") is not None]
        timed_starts = [item[0] for item in timed]
        window_starts = {window["start_segment_id"] for window in qa_doc.get("windows", [])}
        start_sequences: list[int] = []
        for index, topic in enumerate(topics):
            if index == 0:
                sequence = 0
            else:
                at = bisect.bisect_left(timed_starts, topic["start_seconds"])
                sequence = timed[min(at, len(timed) - 1)][1]
            start_sequences.append(sequence)

        word_by_id = {word["id"]: word for word in words}
        left_boundary_decisions: dict[str, dict[str, Any]] = {}
        absorbed_by_proposal: dict[str, dict[str, Any]] = {}
        for index in range(len(topics) - 1):
            proposal_id = f"issue_68_{registry_id}_topic_proposal_{index + 1:03d}"
            boundary_decision = decisions_by_proposal.get(proposal_id)
            if not boundary_decision or boundary_decision.get("boundary_action") != "REALIGN_RIGHT":
                continue
            absorbed_ids = boundary_decision.get("absorbed_proposal_ids", [])
            if absorbed_ids and boundary_decision.get("action") != "SPLIT_REALIGN":
                errors.append(
                    f"absorbed proposals require SPLIT_REALIGN for {proposal_id}"
                )
            expected_absorbed_ids = [
                f"issue_68_{registry_id}_topic_proposal_{item + 1:03d}"
                for item in range(index + 1, index + 1 + len(absorbed_ids))
            ]
            if absorbed_ids != expected_absorbed_ids:
                errors.append(f"absorbed proposals are not consecutive for {proposal_id}")
            next_index = index + 1 + len(absorbed_ids)
            if next_index >= len(topics):
                errors.append(f"realigned boundary has no following proposal for {proposal_id}")
                continue
            next_proposal_id = (
                f"issue_68_{registry_id}_topic_proposal_{next_index + 1:03d}"
            )
            next_word = word_by_id.get(boundary_decision.get("next_start_word_id"))
            end_word = word_by_id.get(boundary_decision.get("end_word_id"))
            if next_word is None or end_word is None:
                errors.append(f"unresolved realigned Word boundary for {proposal_id}")
                continue
            if boundary_decision.get("next_proposal_id") != next_proposal_id:
                errors.append(f"realigned boundary has wrong adjacent proposal for {proposal_id}")
            if next_word["source_id"] != source_id or end_word["source_id"] != source_id:
                errors.append(f"realigned boundary crosses source for {proposal_id}")
            if end_word["sequence"] + 1 != next_word["sequence"]:
                errors.append(f"realigned boundary is not Canonical Word-contiguous for {proposal_id}")
            if boundary_decision.get("end_word_anchor_time") != format_time(
                end_word.get("start_seconds")
            ):
                errors.append(f"realigned end anchor timestamp mismatch for {proposal_id}")
            if boundary_decision.get("next_start_word_anchor_time") != format_time(
                next_word.get("start_seconds")
            ):
                errors.append(f"realigned next-start timestamp mismatch for {proposal_id}")
            start_sequences[next_index] = next_word["sequence"]
            left_boundary_decisions[next_proposal_id] = boundary_decision
            for absorbed_id in absorbed_ids:
                if absorbed_id in absorbed_by_proposal:
                    errors.append(f"proposal absorbed more than once: {absorbed_id}")
                absorbed_by_proposal[absorbed_id] = boundary_decision

        for index in range(1, len(start_sequences)):
            if start_sequences[index] <= start_sequences[index - 1]:
                errors.append(f"non-increasing Canonical Word boundary in {source_id} topic {index + 1}")

        for index, topic in enumerate(topics):
            proposal_id = f"issue_68_{registry_id}_topic_proposal_{index + 1:03d}"
            decision_record = decisions_by_proposal.get(proposal_id)
            start_sequence = start_sequences[index]
            end_sequence = start_sequences[index + 1] - 1 if index + 1 < len(topics) else len(words) - 1
            if decision_record and decision_record.get("absorbed_proposal_ids"):
                authored_end = word_by_id.get(decision_record.get("end_word_id"))
                if authored_end is not None:
                    end_sequence = authored_end["sequence"]
            selected = words[start_sequence : end_sequence + 1]
            if not selected:
                errors.append(f"empty Canonical Word range in {source_id} topic {index + 1}")
                continue
            boundary_kind = (
                "FIXED_WINDOW_EDGE"
                if topic["start_segment_id"] in window_starts
                else "WITHIN_WINDOW_MODEL_BOUNDARY"
            )
            decision, flags = recommendation(topic, boundary_kind)
            timed_selected = [word for word in selected if word.get("start_seconds") is not None]
            locator_start = timed_selected[0]["start_seconds"] if timed_selected else topic["start_seconds"]
            locator_end = timed_selected[-1]["end_seconds"] if timed_selected else topic["end_seconds"]
            previews = {
                "beginning": excerpt(selected, 0),
                "middle": excerpt(selected, len(selected) // 2),
                "end": excerpt(selected, len(selected) - 1),
            }
            machine_summary = topic.get("summary", "").strip()
            if not machine_summary:
                machine_summary = "Машинное резюме отсутствует; содержание требует ручной проверки."
            review_summary = [
                machine_summary,
                (
                    "Фрагмент проходит от «"
                    + " ".join(previews["beginning"]["text"].split()[:7])
                    + "…» к «"
                    + " ".join(previews["end"]["text"].split()[-7:])
                    + "»."
                ),
            ]
            proposal = {
                    "proposal_number": len(proposals) + 1,
                    "proposal_id": proposal_id,
                    "source_id": source_id,
                    "transcript_revision_id": revisions[source_id]["id"],
                    "start_word_id": selected[0]["id"],
                    "end_word_id": selected[-1]["id"],
                    "start_word_sequence": start_sequence,
                    "end_word_sequence": end_sequence,
                    "start_time": format_time(locator_start),
                    "end_time": format_time(locator_end),
                    "start_seconds": locator_start,
                    "end_seconds": locator_end,
                    "generator_interval": {
                        "start_seconds": topic["start_seconds"],
                        "end_seconds": topic["end_seconds"],
                        "start_segment_id": topic["start_segment_id"],
                    },
                    "proposed_title": topic["title"],
                    "proposed_summary": machine_summary,
                    "review_summary": review_summary,
                    "evidence_preview": previews,
                    "boundary_reason": {
                        "kind": boundary_kind,
                        "generator": "legacy_gemma3_4b_two_stage_topic_pipeline",
                        "regression_flags": flags,
                    },
                    "confidence": confidence(topic, flags),
                    "transcript_assurance": revisions[source_id]["transcript_provenance"],
                    "provenance": {
                        "canonical_evidence_artifact_id": bundle["artifact_id"],
                        "canonical_evidence_sha256": bundle_hash,
                        "topic_input_sha256": sha256(topic_path),
                        "topic_qa_sha256": sha256(qa_path),
                        "generator_engine": topic_doc.get("engine"),
                        "generator_model": topic_doc.get("model"),
                        "generator_detail": topic_doc.get("detail"),
                        "generator_qa_status": topic.get("qa_status"),
                        "generator_qa_attempt": topic.get("qa_attempt"),
                    },
                    "recommended_decision": decision,
                    "available_decisions": DECISIONS,
                    "authoring_status": "PENDING",
                    "semantic_status": "PROVISIONAL",
                    "domain_review_status": "REVIEW_REQUIRED",
                    "review_status": "UNREVIEWED",
                }
            left_boundary_decision = left_boundary_decisions.get(proposal_id)
            if left_boundary_decision is not None:
                proposal["left_boundary_authoring_decision"] = {
                    "decision_id": left_boundary_decision.get("decision_id"),
                    "from_word_id": left_boundary_decision.get("previous_next_start_word_id"),
                    "to_word_id": left_boundary_decision.get("next_start_word_id"),
                    "authority": left_boundary_decision.get("authority"),
                }
            absorption_decision = absorbed_by_proposal.get(proposal_id)
            if absorption_decision is not None:
                if decision_record is not None:
                    errors.append(f"absorbed proposal has its own decision: {proposal_id}")
                proposal["authoring_status"] = "COMPLETED"
                proposal["authoring_disposition"] = "MERGED_INTO_PREVIOUS"
                proposal["absorbed_by_authoring_decision"] = {
                    "decision_id": absorption_decision.get("decision_id"),
                    "proposal_id": absorption_decision.get("proposal_id"),
                    "authored_topic_id": absorption_decision.get("split_parts", [{}])[-1].get(
                        "part_id"
                    ),
                    "authority": absorption_decision.get("authority"),
                }
            if decision_record is not None:
                action = decision_record.get("action")
                if action not in {"RENAME", "REALIGN_RENAME", "SPLIT_REALIGN"}:
                    errors.append(f"unsupported authoring action for {proposal_id}")
                if action in {"RENAME", "REALIGN_RENAME"} and not decision_record.get(
                    "new_title"
                ):
                    errors.append(f"RENAME has no new_title for {proposal_id}")
                expected_boundary_action = (
                    "REALIGN_RIGHT"
                    if action in {"REALIGN_RENAME", "SPLIT_REALIGN"}
                    else "PRESERVE"
                )
                if decision_record.get("boundary_action") != expected_boundary_action:
                    errors.append(f"unexpected boundary mutation for {proposal_id}")
                if decision_record.get("source_id") != source_id:
                    errors.append(f"decision source mismatch for {proposal_id}")
                if (
                    decision_record.get("start_word_id") != proposal["start_word_id"]
                    or decision_record.get("end_word_id") != proposal["end_word_id"]
                ):
                    errors.append(f"decision Word range mismatch for {proposal_id}")
                if action == "SPLIT_REALIGN":
                    split_parts = decision_record.get("split_parts", [])
                    authored_topics: list[dict[str, Any]] = []
                    expected_part_sequence = start_sequence
                    part_ids: set[str] = set()
                    if len(split_parts) < 2:
                        errors.append(f"SPLIT_REALIGN requires at least two parts for {proposal_id}")
                    for part in split_parts:
                        part_id = part.get("part_id")
                        authoring_disposition = part.get(
                            "authoring_disposition", "SEMANTIC_TOPIC"
                        )
                        start_word = word_by_id.get(part.get("start_word_id"))
                        end_word = word_by_id.get(part.get("end_word_id"))
                        if not part_id or part_id in part_ids:
                            errors.append(f"invalid or duplicate split part id for {proposal_id}")
                            continue
                        part_ids.add(part_id)
                        if not part.get("title"):
                            errors.append(f"split part has no title for {part_id}")
                        if authoring_disposition not in AUTHORING_DISPOSITIONS:
                            errors.append(
                                f"unsupported authoring disposition for {part_id}"
                            )
                        if start_word is None or end_word is None:
                            errors.append(f"unresolved split Word range for {part_id}")
                            continue
                        if (
                            start_word["source_id"] != source_id
                            or end_word["source_id"] != source_id
                        ):
                            errors.append(f"split part crosses source for {part_id}")
                        if start_word["sequence"] != expected_part_sequence:
                            errors.append(f"split parts are not Canonical Word-contiguous for {proposal_id}")
                        if end_word["sequence"] < start_word["sequence"]:
                            errors.append(f"invalid split Word range for {part_id}")
                            continue
                        if part.get("start_word_anchor_time") != format_time(
                            start_word.get("start_seconds")
                        ):
                            errors.append(f"split start anchor timestamp mismatch for {part_id}")
                        if part.get("end_word_anchor_time") != format_time(
                            end_word.get("start_seconds")
                        ):
                            errors.append(f"split end anchor timestamp mismatch for {part_id}")
                        part_words = words[start_word["sequence"] : end_word["sequence"] + 1]
                        part_timed = [
                            word for word in part_words if word.get("start_seconds") is not None
                        ]
                        part_previews = {
                            "beginning": excerpt(part_words, 0),
                            "middle": excerpt(part_words, len(part_words) // 2),
                            "end": excerpt(part_words, len(part_words) - 1),
                        }
                        authored_topics.append(
                            {
                                "topic_id": part_id,
                                "part_label": part.get("part_label"),
                                "authored_title": part.get("title"),
                                "authoring_disposition": authoring_disposition,
                                "source_id": source_id,
                                "start_word_id": start_word["id"],
                                "end_word_id": end_word["id"],
                                "start_word_sequence": start_word["sequence"],
                                "end_word_sequence": end_word["sequence"],
                                "start_time": format_time(
                                    part_timed[0]["start_seconds"] if part_timed else None
                                ),
                                "end_time": format_time(
                                    part_timed[-1]["end_seconds"] if part_timed else None
                                ),
                                "start_word_anchor_time": part.get("start_word_anchor_time"),
                                "end_word_anchor_time": part.get("end_word_anchor_time"),
                                "evidence_preview": part_previews,
                                "semantic_status": "PROVISIONAL",
                                "domain_review_status": "REVIEW_REQUIRED",
                                "review_status": "UNREVIEWED",
                            }
                        )
                        expected_part_sequence = end_word["sequence"] + 1
                    if expected_part_sequence != end_sequence + 1:
                        errors.append(f"split parts do not cover the full authored range for {proposal_id}")
                    proposal["authored_topics"] = authored_topics
                else:
                    proposal["authored_title"] = decision_record.get("new_title")
                proposal["authoring_status"] = "COMPLETED"
                proposal["authoring_decision"] = {
                    "decision_id": decision_record.get("decision_id"),
                    "action": decision_record.get("action"),
                    "boundary_action": decision_record.get("boundary_action"),
                    "end_word_anchor_time": decision_record.get("end_word_anchor_time"),
                    "next_start_word_anchor_time": decision_record.get(
                        "next_start_word_anchor_time"
                    ),
                    "authority": decision_record.get("authority"),
                    "split_part_ids": [
                        part.get("part_id") for part in decision_record.get("split_parts", [])
                    ],
                    "absorbed_proposal_ids": decision_record.get(
                        "absorbed_proposal_ids", []
                    ),
                    "ledger_artifact_id": decision_document.get("artifact_id") if decision_document else None,
                    "ledger_sha256": sha256(decisions_path) if decisions_path else None,
                }
            proposals.append(proposal)

        source_proposals = [item for item in proposals if item["source_id"] == source_id]
        coverage_proposals = [
            item
            for item in source_proposals
            if item.get("authoring_disposition") != "MERGED_INTO_PREVIOUS"
        ]
        gaps: list[dict[str, int]] = []
        overlaps: list[dict[str, int]] = []
        expected = 0
        for item in coverage_proposals:
            if item["start_word_sequence"] > expected:
                gaps.append({"start_sequence": expected, "end_sequence": item["start_word_sequence"] - 1})
            if item["start_word_sequence"] < expected:
                overlaps.append({"start_sequence": item["start_word_sequence"], "end_sequence": expected - 1})
            expected = item["end_word_sequence"] + 1
        if expected < len(words):
            gaps.append({"start_sequence": expected, "end_sequence": len(words) - 1})
        per_source[source_id] = {
            "proposal_count": len(source_proposals),
            "canonical_word_count": len(words),
            "covered_word_count": sum(
                item["end_word_sequence"] - item["start_word_sequence"] + 1
                for item in coverage_proposals
            ),
            "gaps": gaps,
            "overlaps": overlaps,
            "review_status": "UNREVIEWED",
        }
        topic_input_hashes[source_id] = {
            "topics_path": str(topic_path.relative_to(project)),
            "topics_sha256": sha256(topic_path),
            "qa_path": str(qa_path.relative_to(project)),
            "qa_sha256": sha256(qa_path),
        }

    accepted_day1 = []
    for item in review_result.get("semantic_knowledge", []):
        accepted_day1.append(
            {
                "topic_id": item["id"],
                "source_id": item["source_id"],
                "title": item["title"],
                "summary": item.get("summary", ""),
                "start_word_id": item["word_start_id"],
                "end_word_id": item["word_end_id"],
                "semantic_status": "ACCEPTED_HUMAN_REVIEWED_EXISTING",
            }
        )

    concept_topics: list[dict[str, Any]] = []
    concept_topics.extend(accepted_day1)
    for item in proposals:
        if item.get("authoring_disposition") == "MERGED_INTO_PREVIOUS":
            continue
        if item.get("authored_topics"):
            for authored in item["authored_topics"]:
                if authored["authoring_disposition"] == "NON_SEMANTIC_EXCLUDED":
                    continue
                previews = authored["evidence_preview"]
                concept_topics.append(
                    {
                        "topic_id": authored["topic_id"],
                        "source_id": authored["source_id"],
                        "title": authored["authored_title"],
                        "summary": "",
                        "start_word_id": authored["start_word_id"],
                        "end_word_id": authored["end_word_id"],
                        "evidence_text": " ".join(
                            previews[key]["text"] for key in ("beginning", "middle", "end")
                        ),
                        "semantic_status": "PROVISIONAL_UNREVIEWED",
                    }
                )
            continue
        previews = item["evidence_preview"]
        concept_topics.append(
            {
                "topic_id": item["proposal_id"],
                "source_id": item["source_id"],
                "title": item.get("authored_title", item["proposed_title"]),
                "summary": item["proposed_summary"],
                "start_word_id": item["start_word_id"],
                "end_word_id": item["end_word_id"],
                "evidence_text": " ".join(previews[key]["text"] for key in ("beginning", "middle", "end")),
                "semantic_status": "PROVISIONAL_UNREVIEWED",
            }
        )

    concepts: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    for seed_id, label, aliases, description in CONCEPT_SEEDS:
        topic_refs: list[str] = []
        evidence_refs: list[dict[str, str]] = []
        source_terms: set[str] = set()
        for topic in concept_topics:
            text = " ".join(
                [topic.get("title", ""), topic.get("summary", ""), topic.get("evidence_text", "")]
            )
            matches = []
            for alias in aliases:
                matches.extend(match.group(0) for match in re.finditer(re.escape(alias), text, re.IGNORECASE))
            if not matches:
                continue
            topic_refs.append(topic["topic_id"])
            source_terms.update(matches)
            evidence_refs.append(
                {
                    "source_id": topic["source_id"],
                    "start_word_id": topic["start_word_id"],
                    "end_word_id": topic["end_word_id"],
                }
            )
            links.append(
                {
                    "link_id": f"issue_68_link_{topic['topic_id']}_{seed_id}",
                    "topic_reference": topic["topic_id"],
                    "candidate_concept_reference": f"issue_68_candidate_concept_{seed_id}",
                    "source_id": topic["source_id"],
                    "status": "PROVISIONAL",
                    "review_status": "UNREVIEWED",
                }
            )
        if not topic_refs:
            continue
        concepts.append(
            {
                "candidate_concept_id": f"issue_68_candidate_concept_{seed_id}",
                "proposed_canonical_label": label,
                "source_terms": sorted(source_terms, key=lambda item: (item.casefold(), item)),
                "topic_references": topic_refs,
                "evidence_references": evidence_refs,
                "short_description": description,
                "possible_aliases": aliases,
                "identity_ambiguities": {
                    "note": "Label similarity and source terminology do not establish Concept identity.",
                    "human_choices": ["SAME_CONCEPT", "NEW_CONCEPT", "RELATED", "DISTINCT", "DEFER"],
                },
                "confidence": {
                    "level": "MEDIUM" if len(topic_refs) >= 3 else "LOW",
                    "basis": ["transparent_term_match", "identity_not_inferred"],
                },
                "semantic_status": "PROVISIONAL",
                "review_status": "UNREVIEWED",
            }
        )

    # One item per batch is intentionally conservative for first-pass boundary
    # review.  The UI contract still permits a later presenter to group up to
    # three straightforward adjacent units.
    completed_authoring = {
        item["proposal_id"] for item in proposals if item["authoring_status"] == "COMPLETED"
    }
    batches = {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.issue_68_domain_authoring_batches",
        "review_order": ["source_video_002", "source_video_003", "source_video_004", "concepts", "links"],
        "topic_batches": [
            {
                "batch_id": f"issue_68_topic_batch_{index + 1:03d}",
                "source_id": item["source_id"],
                "proposal_references": [item["proposal_id"]],
                "authoring_status": (
                    "COMPLETED" if item["proposal_id"] in completed_authoring else "PENDING"
                ),
            }
            for index, item in enumerate(proposals)
        ],
        "concept_review_deferred_until_topic_review": True,
        "link_review_deferred_until_concept_review": True,
    }

    package = {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.issue_68_semantic_authoring_package",
        "artifact_id": "issue_68_stress_code_semantic_authoring_v1",
        "status": "READY_FOR_DOMAIN_AUTHORING" if not errors else "INVALID",
        "semantic_authority": "PROVISIONAL_UNREVIEWED",
        "generator": {
            "pipeline": "legacy_gemma3_4b_two_stage_topic_pipeline",
            "model": "gemma3:4b",
            "detail": "auto",
            "not_generated_by": "bge_m3_local_peak_v1",
            "parameters_changed": False,
            "training_or_tuning_performed": False,
        },
        "canonical_evidence": {
            "artifact_id": bundle["artifact_id"],
            "sha256": bundle_hash,
            "word_count": len(bundle["words"]),
        },
        "day_1": {
            "status": "PRESERVED_ACCEPTED_HUMAN_REVIEWED",
            "topic_count": len(accepted_day1),
            "source_artifact_id": review_result["artifact_id"],
            "source_sha256": sha256(review_result_path),
            "topics": accepted_day1,
        },
        "topic_proposals": proposals,
        "concept_candidates": concepts,
        "topic_concept_link_proposals": links,
        "coverage": per_source,
        "input_artifacts": topic_input_hashes,
        "domain_authoring_decision_ledger": (
            {
                "artifact_id": decision_document["artifact_id"],
                "sha256": sha256(decisions_path),
                "decision_count": len(decisions_by_proposal),
            }
            if decision_document is not None and decisions_path is not None
            else None
        ),
        "domain_authoring_progress": {
            "completed": len(completed_authoring),
            "pending": len(proposals) - len(completed_authoring),
            "total": len(proposals),
            "next_proposal_id": next(
                (item["proposal_id"] for item in proposals if item["authoring_status"] == "PENDING"),
                None,
            ),
        },
        "safety": {
            "all_new_topics_unreviewed": all(item["review_status"] == "UNREVIEWED" for item in proposals),
            "all_concepts_provisional": all(item["semantic_status"] == "PROVISIONAL" for item in concepts),
            "all_links_provisional": all(item["status"] == "PROVISIONAL" for item in links),
            "day_1_reauthored": False,
            "transcript_revision_mutated": False,
            "dataset_d_or_e_accessed": False,
            "gold_created_or_modified": False,
            "accepted_obsidian_export_created": False,
        },
        "errors": errors,
    }
    return package, batches


def write_review_markdown(path: Path, package: dict[str, Any]) -> None:
    counts = package["coverage"]
    first = next(
        item for item in package["topic_proposals"] if item["authoring_status"] == "PENDING"
    )
    preview = first["evidence_preview"]
    text = f"""# Issue #68 — Semantic DOMAIN_AUTHORING review

The complete machine-assisted package is stored in `semantic_authoring_package.json`.
All new Topics, Concept candidates, and Topic→Concept links are provisional and
`UNREVIEWED`. Day 1 remains the previously accepted human-reviewed source.

## Package inventory

| Source | Topic proposals | Canonical words covered | Gaps | Overlaps |
| --- | ---: | ---: | ---: | ---: |
"""
    for source_id in ("source_video_002", "source_video_003", "source_video_004"):
        item = counts[source_id]
        text += f"| `{source_id}` | {item['proposal_count']} | {item['covered_word_count']}/{item['canonical_word_count']} | {len(item['gaps'])} | {len(item['overlaps'])} |\n"
    text += f"""

Concept candidates: **{len(package['concept_candidates'])}**.  Provisional
Topic→Concept links: **{len(package['topic_concept_link_proposals'])}**.

## First review item

### {first['proposal_number']}. {first['proposed_title']}

- Source: `{first['source_id']}`
- Time: `{first['start_time']}` — `{first['end_time']}`
- Words: `{first['start_word_id']}` — `{first['end_word_id']}`
- Summary: {' '.join(first['review_summary'])}
- Beginning: {preview['beginning']['text']}
- Middle: {preview['middle']['text']}
- End: {preview['end']['text']}
- Machine recommendation: `{first['recommended_decision']}`
- Available decisions: {', '.join(first['available_decisions'])}

Natural Russian responses are supported, for example: `Тема {first['proposal_number']} — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--review-result", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--decisions", type=Path)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    decisions_path = args.decisions.resolve() if args.decisions else None
    if decisions_path is None:
        default_decisions = output / "domain_authoring_decisions.json"
        decisions_path = default_decisions if default_decisions.exists() else None
    package, batches = build_package(
        args.project.resolve(), args.review_result.resolve(), decisions_path
    )
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "semantic_authoring_package.json", package)
    write_json(output / "review_batches.json", batches)
    write_review_markdown(output / "DOMAIN_AUTHORING_REVIEW.md", package)
    manifest = {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.issue_68_semantic_package_manifest",
        "package_status": package["status"],
        "semantic_authority": package["semantic_authority"],
        "domain_authoring_decision_ledger": package["domain_authoring_decision_ledger"],
        "files": {
            name: sha256(output / name)
            for name in ("semantic_authoring_package.json", "review_batches.json", "DOMAIN_AUTHORING_REVIEW.md")
        },
    }
    write_json(output / "manifest.json", manifest)
    return 1 if package["status"] == "INVALID" else 0


if __name__ == "__main__":
    raise SystemExit(main())
