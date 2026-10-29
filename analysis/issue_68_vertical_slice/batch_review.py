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
# They are intentionally presentation-only: ``apply_batch`` still accepts only a
# hash-bound, explicit Product Owner decision.  Keeping the proposals alongside
# the existing renderer prevents a second review format from drifting away from
# the governed JSON package.
RECOMMENDATION_PROFILES = {
    "ACCEPT": (
        "Контекст показывает, что понятие является предметом объяснения или упражнения в этой теме.",
        "средняя: решение опирается на доступный фрагмент и требует подтверждения владельца",
    ),
    "REJECT": (
        "Понятие названо как пример, фон или сопутствующее действие; предмет темы другой.",
        "средняя: в доступном контексте нет самостоятельного раскрытия понятия",
    ),
    "DEFER": (
        "Доступного фрагмента недостаточно, чтобы отличить предметное обсуждение от упоминания.",
        "высокая: перед решением нужен более широкий исходный контекст",
    ),
    "CONFIRMED_REJECT": (
        "Владелец уже отклонил именно эту связь: «коррекция» здесь лишь упомянута, а не раскрыта по существу.",
        "подтверждено владельцем; техническое внесение ожидает hash-bound submission",
    ),
}

RECOMMENDATIONS = {
    "issue_68_link_issue_68_video_002_topic_proposal_069_correction": "CONFIRMED_REJECT",
    "issue_68_link_issue_68_video_002_topic_proposal_082_correction": "REJECT",
    "issue_68_link_issue_68_video_003_topic_proposal_001_correction": "REJECT",
    "issue_68_link_issue_68_video_004_topic_proposal_021_correction": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_027_correction": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_032_correction": "REJECT",
    "issue_68_link_issue_68_video_004_topic_proposal_047_correction": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_057_correction": "ACCEPT",
    "issue_68_link_issue_68_video_002_topic_proposal_007_protocol": "ACCEPT",
    "issue_68_link_issue_68_video_002_topic_proposal_061_protocol": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_061_protocol": "DEFER",
    "issue_68_link_issue_68_video_002_topic_proposal_002_emotion": "REJECT",
    "issue_68_link_issue_68_video_002_topic_proposal_058_emotion": "ACCEPT",
    "issue_68_link_issue_68_video_002_topic_proposal_084_emotion": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_006_emotion": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_042_emotion": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_071_emotion": "DEFER",
    "issue_68_link_issue_68_video_003_topic_proposal_072_emotion": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_026_emotion": "ACCEPT",
    "issue_68_link_issue_68_video_002_topic_proposal_010_nervous_system": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_026_neural_connections_and_networks": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_086_nervous_system": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_090_nervous_system": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_092_nervous_system": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_014_nervous_system": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_014_neural_connections_and_networks": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_040_nervous_system": "REJECT",
    "issue_68_link_issue_68_video_003_topic_proposal_031_adaptation": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_026_brain": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_041_brain": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_085_brain": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_088_brain": "DEFER",
    "issue_68_link_issue_68_video_004_topic_proposal_008_meridians": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_039_meridians": "REJECT",
    "issue_68_link_issue_68_video_004_topic_proposal_043_meridians": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_076_extraocular_muscles": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_074_extraocular_muscles": "ACCEPT",
    "issue_68_link_issue_113_reviewed_topic_08_consciousness": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_015_three_level_awareness": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_016_three_level_awareness": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_019_three_level_awareness": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_020_three_level_awareness": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_019_subconscious": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_071_subconscious": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_082_subconscious": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_052_subconscious": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_045_memory": "ACCEPT",
    "issue_68_link_issue_68_video_003_topic_proposal_061_memory": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_013_memory": "REJECT",
    "issue_68_link_issue_68_video_004_topic_proposal_015_memory": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_077_memory": "ACCEPT",
    "issue_68_link_issue_68_video_004_topic_proposal_042_trauma": "ACCEPT",
}


def recommendation_for(entry: dict[str, Any]) -> tuple[str, str, str]:
    """Return a presentation-only recommendation for one governed entry."""
    # A rebuild can expose a different unresolved item after a valid, atomic
    # human decision.  It must remain reviewable, but no prior proposal may be
    # silently extended to it; DEFER is the only safe presentation fallback.
    profile = RECOMMENDATIONS.get(entry["link_id"], "DEFER")
    action = "REJECT" if profile == "CONFIRMED_REJECT" else profile
    rationale, uncertainty = RECOMMENDATION_PROFILES[profile]
    return action, rationale, uncertainty


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
        mention_excerpt = ""
        for source_text in source_texts:
            found = re.search(concept_pattern, source_text, re.IGNORECASE)
            if found:
                mention_excerpt = source_text[max(0, found.start() - 90):found.end() + 90]
                break
        if not mention_excerpt:
            mention_excerpt = source_texts[0][:180]
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
        "- Связь «Постановка Целей Сессии» → «Коррекция» должна быть отклонена: в теме есть лишь упоминание коррекции, а не её предметное объяснение. Решение сохранено из обсуждения PR #121 и не требует повторного решения; для записи в ledger ещё нужен hash-bound submission текущего пакета.",
        "",
        "## Активные рекомендации",
        "",
    ]
    by_concept: dict[str, list[dict[str, Any]]] = {}
    for entry in package["active"]:
        by_concept.setdefault(entry["concept_label"], []).append(entry)
    for concept, entries in by_concept.items():
        lines += [f"### {concept}", "", "| Источник | Тема | Контекст | Рекомендация | Основание и неопределённость |", "| --- | --- | --- | --- | --- |"]
        for entry in entries:
            action, rationale, uncertainty = recommendation_for(entry)
            context = entry["mention_excerpt"].replace("|", "\\|").replace("\n", " ")
            basis = f"{rationale} Неопределённость: {uncertainty}."
            lines.append("| " + " | ".join((
                entry["source_id"], entry["topic_title"].replace("|", "\\|"), context,
                action, basis.replace("|", "\\|"),
            )) + " |")
        lines += ["", "Идентификаторы этой группы: " + ", ".join(
            f"`{entry['link_id']}`" for entry in entries) + ".", ""]
    lines += [
        f"Активных связей: **{len(package['active'])}**. Все 52 имеют индивидуальную рекомендацию; группировка не объединяет решения.",
        "", "## Особое внимание и отложенные вопросы", "",
        "- Рекомендации `DEFER`: фрагмент для «Тема требует ручной проверки», «Работа с Подсознанием в Терапии» и «Нейронные сети и запоминание» не даёт достаточной самостоятельной основы для решения.",
        "- В двух местах есть selective transcript-verification exceptions; они сохранены в `domain_review_qa.json` и не являются семантическим подтверждением.",
        "- Четыре видео имеют Canonical Evidence/Word Timeline; три зарегистрированных документа не имеют Canonical Evidence. Это не полное покрытие всех семи источников.",
        "", "## Ранее отложенная связь", "",
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
    historical_ids = {d["decision_id"] for key in ("decisions", "concept_identity_decisions", "link_decisions")
                      for d in original[key]}
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
