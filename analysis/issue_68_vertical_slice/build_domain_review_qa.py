#!/usr/bin/env python3
"""Build the Issue #68 exception-only DOMAIN_REVIEW QA package.

The QA package keeps the original 262 machine proposals, 18 Concept candidate
seeds, and 254 Topic-to-Concept link proposals as its input inventory while it
reviews the 181 resulting semantic units produced by DOMAIN_AUTHORING.  It is
advisory only: nothing emitted by this builder is semantically accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


SOURCE_ORDER = ("source_video_002", "source_video_003", "source_video_004")

# These are explicit semantic-QA findings, not automatic ReviewDecisions.  Each
# one is bound below to the exact current Canonical Word range. A finding stops
# being an unresolved exception only when an explicit Product Owner decision in
# the DOMAIN_REVIEW ledger below has been validated and applied.
TOPIC_EXCEPTIONS: dict[str, dict[str, Any]] = {
    "issue_68_video_002_topic_proposal_020a": {
        "taxonomy": [
            "NON_SEMANTIC_CONTENT_CONTAMINATION",
            "DISCOURSE_FUNCTION_BOUNDARY_MISSED",
        ],
        "problem": (
            "The semantic assignment is wrapped by two scheduling fragments: "
            "the break announcement at the left and the return-time announcement "
            "at the right. Treating the whole range as one knowledge Topic mixes "
            "seminar organization with the energy-classification task."
        ),
        "recommended_correction": {
            "action": "SPLIT_REALIGN",
            "semantic_part": {
                "title": (
                    "Задание: классификация входящей, внутренней и "
                    "производимой энергии"
                ),
                "start_word_id": "transcript_revision_video_002_r1:word:007526",
                "end_word_id": "transcript_revision_video_002_r1:word:007581",
            },
            "exclude_as_nonsemantic": [
                {
                    "start_word_id": "transcript_revision_video_002_r1:word:007504",
                    "end_word_id": "transcript_revision_video_002_r1:word:007525",
                    "reason": "break scheduling",
                },
                {
                    "start_word_id": "transcript_revision_video_002_r1:word:007582",
                    "end_word_id": "transcript_revision_video_002_r1:word:007588",
                    "reason": "return-time scheduling",
                },
            ],
        },
        "alternative": (
            "Preserve the full range only as SEMINAR_STRUCTURE rather than as a "
            "knowledge Topic."
        ),
        "confidence": "HIGH",
    },
    "issue_68_video_003_topic_proposal_051a": {
        "taxonomy": ["NON_SEMANTIC_CONTENT_CONTAMINATION", "BOUNDARY_OFFSET"],
        "problem": (
            "The unit opens with an unrelated lunch-break duration announcement "
            "before the participant and demonstration-topic selection begins."
        ),
        "recommended_correction": {
            "action": "REALIGN_LEFT",
            "start_word_id": "transcript_revision_video_003_r1:word:015220",
            "preserve_end_word_id": "transcript_revision_video_003_r1:word:015449",
            "exclude_as_nonsemantic": {
                "start_word_id": "transcript_revision_video_003_r1:word:015212",
                "end_word_id": "transcript_revision_video_003_r1:word:015219",
            },
        },
        "alternative": "Preserve the current range as SEMINAR_STRUCTURE.",
        "confidence": "HIGH",
    },
    "issue_68_video_004_topic_proposal_001c": {
        "taxonomy": ["MALFORMED_TITLE", "TRANSCRIPT_UNCERTAINTY"],
        "problem": (
            "The title and machine transcript use «рецессия» for a method whose "
            "surrounding explanation appears to describe temporal regression. "
            "The intended domain term cannot be authoritatively inferred from "
            "the machine TranscriptRevision alone."
        ),
        "recommended_correction": {
            "action": "SELECTIVE_TRANSCRIPT_VERIFICATION_THEN_RENAME_IF_CONFIRMED",
            "candidate_title": (
                "Специфическая, генетическая и неспецифическая регрессия"
            ),
            "preserve_word_range": True,
        },
        "alternative": (
            "Retain «рецессия» with an explicit source-term note if selective "
            "verification confirms that wording."
        ),
        "confidence": "MEDIUM",
    },
    "issue_68_video_004_topic_proposal_024h": {
        "taxonomy": ["OVER-MERGE", "TRANSITION_SPLIT", "PROCEDURAL_CONTENT_MIX"],
        "problem": (
            "The resource-focused discussion ends before a guided brain-gym "
            "sequence and pretest recap. The current range combines two distinct "
            "semantic functions under one title."
        ),
        "recommended_correction": {
            "action": "SPLIT_REALIGN",
            "semantic_part": {
                "preserve_title": True,
                "start_word_id": "transcript_revision_video_004_r1:word:009738",
                "end_word_id": "transcript_revision_video_004_r1:word:010253",
            },
            "separate_semantic_part": {
                "title": "Гимнастика для мозга и повторение претестов перед вопросами",
                "start_word_id": "transcript_revision_video_004_r1:word:010254",
                "end_word_id": "transcript_revision_video_004_r1:word:010431",
                "proposed_role": "SEMANTIC_TOPIC",
            },
        },
        "alternative": (
            "Classify the second part as SEMINAR_STRUCTURE only if the guided "
            "exercise is intended as navigation rather than reusable content."
        ),
        "confidence": "HIGH",
    },
}

VALID_SHORT_TOPICS = {
    "issue_68_video_002_topic_proposal_009": "VALID_SHORT_TOPIC",
    "issue_68_video_002_topic_proposal_046c": "VALID_SHORT_TOPIC",
}

CONCEPT_EXCEPTIONS: dict[str, dict[str, str]] = {
    "issue_68_candidate_concept_correction": {
        "problem": "The label spans multiple distinct correction modalities and is too broad for identity assignment.",
        "recommendation": "Decide whether it is an umbrella Concept or separate modality Concepts.",
    },
    "issue_68_candidate_concept_nervous_system": {
        "problem": "The seed groups nervous system, neural network, and neuron-network language that may denote related but distinct Concepts.",
        "recommendation": "Review as RELATED versus SAME_CONCEPT before identity assignment.",
    },
    "issue_68_candidate_concept_brain": {
        "problem": "«Мозг» and «полушария» mix a whole structure with one of its organizational distinctions.",
        "recommendation": "Choose one umbrella identity or separate hierarchical Concepts.",
    },
    "issue_68_candidate_concept_eye_movement": {
        "problem": "Generic eye movements and the named ДПДГ method are related but not automatically identical.",
        "recommendation": "Review SAME_CONCEPT versus RELATED/hierarchical identities.",
    },
    "issue_68_candidate_concept_consciousness": {
        "problem": "The seed combines levels of consciousness, awareness, and осознавание without an identity decision.",
        "recommendation": "Resolve terminology and Concept scope through DOMAIN_REVIEW.",
    },
    "issue_68_candidate_concept_life_goals": {
        "problem": "The candidate is supported by a narrow title/summary signal and lacks a robust exact-term evidence base.",
        "recommendation": "Confirm that the evidence denotes a reusable Concept rather than a local session formulation.",
    },
    "issue_68_candidate_concept_self_regulation": {
        "problem": "The candidate is generated from a broad summary phrase and has no matching exact source expression in the current authored ranges.",
        "recommendation": "Defer or define the identity only with explicit human evidence review.",
    },
}

CONCEPT_PATTERNS = {
    "stress": r"стресс",
    "kinesiology": r"кинезиолог",
    "muscle_testing": r"мышечн\w*\s+(?:тест|тестирован)",
    "correction": r"коррекц",
    "protocol": r"протокол",
    "emotion": r"эмоц",
    "nervous_system": r"нервн\w*\s+систем",
    "neural_connections_and_networks": (
        r"(?:нейронн\w*\s+(?:связ|сет|цеп)|нервн\w*\s+(?:связ|сет|цеп))"
    ),
    "adaptation": r"адаптац|адаптив",
    "brain": r"мозг",
    "cerebral_hemispheres": r"полушар",
    "meridians": r"меридиан",
    "eye_movement": r"дпдг|движени\w*\s+глаз|глазодвиг",
    "eye_movements_only": r"движени\w*\s+глаз\w*",
    "emdr": r"\bдпдг\b",
    "extraocular_muscles": r"глазодвигатель\w*",
    "consciousness": r"уровн\w*\s+(?:созн|осознав|осознан)",
    "three_level_awareness": r"уровн\w*\s+(?:созн|осознав|осознан)",
    "subconscious": r"подсозн",
    "memory": r"памят|воспомин|запомин",
    "trauma": r"травм",
    "psychosomatics": r"психосомат",
    "life_goals": r"жизненн\w*\s+цел|цел\w*\s+жизн",
    "self_regulation": r"саморегуляц|самовосстанов|управлен\w*\s+стресс",
}

RELATED_PARTITION_STRATEGIES = {
    "NERVOUS_SYSTEM_VS_NEURAL_CONNECTIONS_EXACT_TERMS": {
        "target_concept_id": "issue_68_candidate_concept_nervous_system",
        "related_concept_id": (
            "issue_68_candidate_concept_neural_connections_and_networks"
        ),
        "retained_pattern_key": "nervous_system",
        "related_pattern_key": "neural_connections_and_networks",
        "semantic_relation": None,
    },
    "BRAIN_VS_CEREBRAL_HEMISPHERES_EXACT_TERMS": {
        "target_concept_id": "issue_68_candidate_concept_brain",
        "related_concept_id": "issue_68_candidate_concept_cerebral_hemispheres",
        "retained_pattern_key": "brain",
        "related_pattern_key": "cerebral_hemispheres",
        "semantic_relation": {
            "type": "PART_OF",
            "source_concept_id": (
                "issue_68_candidate_concept_cerebral_hemispheres"
            ),
            "target_concept_id": "issue_68_candidate_concept_brain",
        },
    },
    "EYE_MOVEMENTS_VS_EMDR_VS_EXTRAOCULAR_MUSCLES_EXACT_TERMS": {
        "target_concept_id": "issue_68_candidate_concept_eye_movement",
        "retained_pattern_key": "eye_movements_only",
        "related_concepts": [
            {
                "candidate_concept_id": "issue_68_candidate_concept_emdr",
                "pattern_key": "emdr",
            },
            {
                "candidate_concept_id": (
                    "issue_68_candidate_concept_extraocular_muscles"
                ),
                "pattern_key": "extraocular_muscles",
            },
        ],
        "semantic_relations": [
            {
                "type": "USED_IN",
                "source_concept_id": "issue_68_candidate_concept_eye_movement",
                "target_concept_id": "issue_68_candidate_concept_emdr",
            },
            {
                "type": "PERFORMED_BY",
                "source_concept_id": "issue_68_candidate_concept_eye_movement",
                "target_concept_id": (
                    "issue_68_candidate_concept_extraocular_muscles"
                ),
            },
        ],
    },
    "HAWKINS_VS_THREE_LEVEL_AWARENESS_EXACT_CONTEXT": {
        "target_concept_id": "issue_68_candidate_concept_consciousness",
        "related_concept_id": (
            "issue_68_candidate_concept_three_level_awareness"
        ),
        "retained_pattern_key": "consciousness",
        "related_pattern_key": "consciousness",
        "semantic_relation": None,
        "retained_topic_references": ["issue_113_reviewed_topic_08"],
        "related_topic_references": [
            "issue_68_video_003_topic_proposal_015",
            "issue_68_video_003_topic_proposal_016",
            "issue_68_video_003_topic_proposal_019",
            "issue_68_video_003_topic_proposal_020",
            "issue_68_video_003_topic_proposal_049",
            "issue_68_video_003_topic_proposal_062",
        ],
        "shared_contextual_source_terms": ["Уровни сознания"],
        "component_concept_labels": ["Сознание", "Подсознание", "Тело"],
        "component_identities_merged": False,
    },
}

NEW_CONCEPT_STRATEGIES = {
    "LIFE_GOAL_REUSABLE_CONCEPT_WITH_EXACT_LINK_REVIEW": {
        "target_concept_id": "issue_68_candidate_concept_life_goals",
        "accepted_canonical_label": "Цель жизни",
        "accepted_lexical_forms": [
            "цель жизни",
            "жизненные цели",
            "цели жизни",
        ],
        "accepted_topic_references": [
            "issue_68_video_003_topic_proposal_060"
        ],
        "rejected_topic_references": [
            "issue_68_video_003_topic_proposal_064"
        ],
    },
}

REJECT_CONCEPT_STRATEGIES = {
    "SELF_REGULATION_UNSUPPORTED_MACHINE_SUMMARY": {
        "target_concept_id": "issue_68_candidate_concept_self_regulation",
        "rejected_canonical_label": "Саморегуляция",
        "rejected_source_terms": ["Управление стрессом"],
        "rejected_topic_references": [
            "issue_68_video_003_topic_proposal_069",
            "issue_68_video_004_topic_proposal_006",
        ],
    },
}

TRANSCRIPT_EXCEPTIONS = [
    {
        "exception_id": "issue_68_transcript_exception_craniosacral_term",
        "source_id": "source_video_002",
        "topic_references": ["issue_68_video_002_topic_proposal_044"],
        "machine_form": "крайне-сакральный / крайне сакральный",
        "candidate_human_form": "краниосакральный",
        "effect": "Topic title and domain terminology",
        "required_action": "SELECTIVE_VERIFICATION_WITHOUT_TRANSCRIPT_MUTATION",
    },
    {
        "exception_id": "issue_68_transcript_exception_regression_term",
        "source_id": "source_video_004",
        "topic_references": [
            "issue_68_video_004_topic_proposal_001c",
            "issue_68_video_004_topic_proposal_011a",
            "issue_68_video_004_topic_proposal_011b",
            "issue_68_video_004_topic_proposal_011e",
            "issue_68_video_004_topic_proposal_024a",
            "issue_68_video_004_topic_proposal_024b",
        ],
        "machine_form": "рецессия",
        "candidate_human_form": "регрессия",
        "effect": "Topic identity, titles, and method terminology",
        "required_action": "SELECTIVE_VERIFICATION_WITHOUT_TRANSCRIPT_MUTATION",
    },
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_authoring_builder(repository: Path) -> Any:
    path = repository / "analysis/issue_68_vertical_slice/build_semantic_authoring_package.py"
    spec = importlib.util.spec_from_file_location("issue_68_authoring_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def word_sequence(word_id: str) -> int:
    return int(word_id.rsplit(":", 1)[1])


def evidence_excerpt(words: list[dict[str, Any]], radius: int = 16) -> dict[str, Any]:
    midpoint = len(words) // 2
    slices = {
        "beginning": words[: radius * 2],
        "middle": words[max(0, midpoint - radius) : midpoint + radius],
        "end": words[-radius * 2 :],
    }
    return {
        key: {
            "start_word_id": value[0]["id"],
            "end_word_id": value[-1]["id"],
            "text": " ".join(item["text"] for item in value),
        }
        for key, value in slices.items()
    }


def authored_units(package: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for proposal in package["topic_proposals"]:
        if proposal.get("authoring_disposition") == "MERGED_INTO_PREVIOUS":
            continue
        if proposal.get("authored_topics"):
            for part in proposal["authored_topics"]:
                if part.get("authoring_disposition") != "SEMANTIC_TOPIC":
                    continue
                units.append(
                    {
                        "topic_id": part["topic_id"],
                        "source_id": part["source_id"],
                        "title": part["authored_title"],
                        "start_word_id": part["start_word_id"],
                        "end_word_id": part["end_word_id"],
                        "start_word_sequence": part["start_word_sequence"],
                        "end_word_sequence": part["end_word_sequence"],
                        "start_time": part["start_time"],
                        "end_time": part["end_time"],
                        "origin_proposal_id": proposal["proposal_id"],
                        "authoring_authority": proposal["authoring_decision"]["authority"],
                    }
                )
            continue
        units.append(
            {
                "topic_id": proposal["proposal_id"],
                "source_id": proposal["source_id"],
                "title": proposal.get("authored_title", proposal["proposed_title"]),
                "start_word_id": proposal["start_word_id"],
                "end_word_id": proposal["end_word_id"],
                "start_word_sequence": proposal["start_word_sequence"],
                "end_word_sequence": proposal["end_word_sequence"],
                "start_time": proposal["start_time"],
                "end_time": proposal["end_time"],
                "origin_proposal_id": proposal["proposal_id"],
                "authoring_authority": proposal["authoring_decision"]["authority"],
            }
        )
    return units


def apply_domain_review_decisions(
    units: list[dict[str, Any]],
    decision_ledger: dict[str, Any],
    words_by_source: dict[str, list[dict[str, Any]]],
    errors: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    """Apply only exact, explicitly authorized exception decisions.

    This layer does not accept the full semantic package. It replaces the
    reviewed target's provisional range/title, preserves non-semantic source
    fragments as explicit lineage records, and leaves every other item under
    the existing review policy.
    """

    if decision_ledger.get("artifact_type") != "seminartext.issue_68_domain_review_decisions":
        errors.append("invalid DOMAIN_REVIEW decision-ledger artifact type")
        return units, [], set()
    if decision_ledger.get("review_gate") != "DOMAIN_REVIEW":
        errors.append("invalid DOMAIN_REVIEW decision-ledger gate")
    if decision_ledger.get("package_semantic_authority") != "PROVISIONAL_UNREVIEWED":
        errors.append("DOMAIN_REVIEW ledger must not promote package authority")

    unit_by_id = {item["topic_id"]: item for item in units}
    original_order = {item["topic_id"]: index for index, item in enumerate(units)}
    resolved: set[str] = set()
    resolutions: list[dict[str, Any]] = []

    for decision in decision_ledger.get("decisions", []):
        decision_id = decision.get("decision_id", "<missing>")
        target_id = decision.get("target_topic_id")
        if decision.get("authority") != "PRODUCT_OWNER_DOMAIN_REVIEW":
            errors.append(f"non-authoritative DOMAIN_REVIEW decision {decision_id}")
            continue
        if decision.get("action") not in {
            "SPLIT_REALIGN",
            "REALIGN_LEFT",
            "CONFIRM_AUDIO_RECESSION_SEMANTIC_NORMALIZATION_TO_REGRESSION",
        }:
            errors.append(f"unsupported DOMAIN_REVIEW action in {decision_id}")
            continue
        if target_id in resolved:
            errors.append(f"duplicate DOMAIN_REVIEW target {target_id}")
            continue
        target = unit_by_id.get(target_id)
        if target is None:
            errors.append(f"orphan DOMAIN_REVIEW target {target_id}")
            continue

        source_id = target["source_id"]
        expected_original = decision.get("original_range", {})
        if (
            expected_original.get("start_word_id") != target["start_word_id"]
            or expected_original.get("end_word_id") != target["end_word_id"]
        ):
            errors.append(f"DOMAIN_REVIEW original-range mismatch for {target_id}")
            continue

        results = decision.get("results", [])
        if not results:
            errors.append(f"DOMAIN_REVIEW decision has no results: {decision_id}")
            continue
        sequences: list[tuple[int, int]] = []
        semantic_results = []
        resolved_results = []
        malformed = False
        for result in results:
            if result.get("source_id") != source_id:
                errors.append(f"DOMAIN_REVIEW source mismatch in {decision_id}")
                malformed = True
                break
            start = word_sequence(result["start_word_id"])
            end = word_sequence(result["end_word_id"])
            if start > end:
                errors.append(f"DOMAIN_REVIEW inverted range in {decision_id}")
                malformed = True
                break
            source_words = words_by_source[source_id]
            if (
                start >= len(source_words)
                or end >= len(source_words)
                or source_words[start]["id"] != result["start_word_id"]
                or source_words[end]["id"] != result["end_word_id"]
            ):
                errors.append(f"DOMAIN_REVIEW unresolved evidence in {decision_id}")
                malformed = True
                break
            disposition = result.get("disposition")
            if disposition not in {"SEMANTIC_TOPIC", "NON_SEMANTIC_EXCLUDED"}:
                errors.append(f"DOMAIN_REVIEW invalid disposition in {decision_id}")
                malformed = True
                break
            sequences.append((start, end))
            resolved_results.append(
                {
                    **result,
                    "start_word_sequence": start,
                    "end_word_sequence": end,
                    "start_time": source_words[start]["start_seconds"],
                    "end_time": source_words[end]["end_seconds"],
                    "canonical_evidence_sha256": sha256_bytes(
                        " ".join(word["text"] for word in source_words[start : end + 1]).encode("utf-8")
                    ),
                }
            )
            if disposition == "SEMANTIC_TOPIC":
                semantic_results.append(resolved_results[-1])
        if malformed:
            continue
        sequences.sort()
        original_start = target["start_word_sequence"]
        original_end = target["end_word_sequence"]
        if (
            sequences[0][0] != original_start
            or sequences[-1][1] != original_end
            or any(left[1] + 1 != right[0] for left, right in zip(sequences, sequences[1:]))
        ):
            errors.append(f"DOMAIN_REVIEW results do not exactly partition {target_id}")
            continue
        semantic_ids = [item.get("topic_id") for item in semantic_results]
        if not semantic_results or semantic_ids.count(target_id) != 1:
            errors.append(f"DOMAIN_REVIEW must preserve the semantic target identity for {target_id}")
            continue
        if any(not item for item in semantic_ids) or len(set(semantic_ids)) != len(semantic_ids):
            errors.append(f"DOMAIN_REVIEW semantic result IDs are invalid for {target_id}")
            continue
        if any(item != target_id and item in unit_by_id for item in semantic_ids):
            errors.append(f"DOMAIN_REVIEW semantic result ID collision for {target_id}")
            continue

        semantic = next(item for item in semantic_results if item["topic_id"] == target_id)
        target.update(
            {
                "title": semantic["title"],
                "start_word_id": semantic["start_word_id"],
                "end_word_id": semantic["end_word_id"],
                "start_word_sequence": semantic["start_word_sequence"],
                "end_word_sequence": semantic["end_word_sequence"],
                "start_time": semantic["start_time"],
                "end_time": semantic["end_time"],
                "domain_review_decision_id": decision_id,
                "domain_review_authority": decision["authority"],
                "domain_review_action": decision["action"],
            }
        )
        index = original_order[target_id]
        previous_unit = units[index - 1] if index > 0 and units[index - 1]["source_id"] == source_id else None
        next_unit = units[index + 1] if index + 1 < len(units) and units[index + 1]["source_id"] == source_id else None
        neighborhood_checks = {
            "previous_topic_id": previous_unit["topic_id"] if previous_unit else None,
            "previous_topic_ends_before_original_range": bool(
                previous_unit and previous_unit["end_word_sequence"] + 1 == original_start
            ),
            "decision_results_exactly_partition_original_range": True,
            "semantic_range_inside_original_range": (
                original_start <= semantic["start_word_sequence"]
                and semantic["end_word_sequence"] <= original_end
            ),
            "next_topic_id": next_unit["topic_id"] if next_unit else None,
            "next_topic_starts_after_original_range": bool(
                next_unit and original_end + 1 == next_unit["start_word_sequence"]
            ),
            "neighboring_topic_overlap": bool(
                (previous_unit and previous_unit["end_word_sequence"] >= original_start)
                or (next_unit and next_unit["start_word_sequence"] <= original_end)
            ),
        }
        if not all(
            value is True
            for key, value in neighborhood_checks.items()
            if key not in {"previous_topic_id", "next_topic_id", "neighboring_topic_overlap"}
        ) or neighborhood_checks["neighboring_topic_overlap"]:
            errors.append(f"DOMAIN_REVIEW neighborhood QA failed for {target_id}")
            continue

        additional_units = []
        for item in semantic_results:
            if item["topic_id"] == target_id:
                continue
            additional_units.append(
                {
                    "topic_id": item["topic_id"],
                    "source_id": source_id,
                    "title": item["title"],
                    "start_word_id": item["start_word_id"],
                    "end_word_id": item["end_word_id"],
                    "start_word_sequence": item["start_word_sequence"],
                    "end_word_sequence": item["end_word_sequence"],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "origin_proposal_id": target["origin_proposal_id"],
                    "authoring_authority": target["authoring_authority"],
                    "domain_review_decision_id": decision_id,
                    "domain_review_authority": decision["authority"],
                    "domain_review_action": decision["action"],
                }
            )
        if additional_units:
            units[index + 1 : index + 1] = sorted(
                additional_units, key=lambda item: item["start_word_sequence"]
            )
            for offset, item in enumerate(units):
                original_order[item["topic_id"]] = offset
                unit_by_id[item["topic_id"]] = item

        result_topic_ids = [item["topic_id"] for item in semantic_results]
        resolved.update(result_topic_ids)
        resolutions.append(
            {
                "decision_id": decision_id,
                "target_topic_id": target_id,
                "result_topic_ids": result_topic_ids,
                "authority": decision["authority"],
                "review_gate": "DOMAIN_REVIEW",
                "status": "DECIDED",
                "action": decision["action"],
                "rationale": decision["rationale"],
                "rejected_alternative": decision["rejected_alternative"],
                "results": resolved_results,
                "neighborhood_qa": neighborhood_checks,
                "package_semantic_promotion": False,
                **(
                    {"terminology_normalization": decision["terminology_normalization"]}
                    if "terminology_normalization" in decision
                    else {}
                ),
            }
        )

    return units, resolutions, resolved


def apply_concept_identity_decisions(
    candidates: list[dict[str, Any]],
    decision_ledger: dict[str, Any],
    words_by_source: dict[str, list[dict[str, Any]]],
    errors: list[str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    set[str],
    dict[tuple[str, str], dict[str, Any]],
]:
    """Validate explicit Product Owner decisions over Concept identity.

    A SAME_CONCEPT umbrella decision binds only the generic lexical forms and
    the stated umbrella scope. It does not merge the identities of methods
    mentioned by the linked Topics.
    """

    transformed = [dict(item) for item in candidates]
    candidate_by_id = {item["candidate_concept_id"]: item for item in transformed}
    resolutions: list[dict[str, Any]] = []
    resolved: set[str] = set()
    link_rewrites: dict[tuple[str, str], dict[str, Any]] = {}
    for decision in decision_ledger.get("concept_identity_decisions", []):
        decision_id = decision.get("decision_id", "<missing>")
        target_id = decision.get("target_candidate_concept_id")
        if decision.get("authority") != "PRODUCT_OWNER_DOMAIN_REVIEW":
            errors.append(f"non-authoritative Concept decision {decision_id}")
            continue
        outcome = decision.get("outcome")
        if outcome not in {"SAME_CONCEPT", "NEW_CONCEPT", "RELATED", "REJECT"}:
            errors.append(f"unsupported Concept decision outcome in {decision_id}")
            continue
        if target_id in resolved:
            errors.append(f"duplicate Concept decision target {target_id}")
            continue
        candidate = candidate_by_id.get(target_id)
        if candidate is None:
            errors.append(f"orphan Concept decision target {target_id}")
            continue
        snapshot = decision.get("candidate_snapshot", {})
        if snapshot.get("proposed_canonical_label") != candidate.get(
            "proposed_canonical_label"
        ):
            errors.append(f"Concept label snapshot mismatch in {decision_id}")
            continue
        if snapshot.get("source_terms") != candidate.get("source_terms"):
            errors.append(f"Concept source-term snapshot mismatch in {decision_id}")
            continue
        if snapshot.get("evidence_reference_count") != len(
            candidate.get("evidence_references", [])
        ):
            errors.append(f"Concept evidence-count snapshot mismatch in {decision_id}")
            continue
        if outcome == "REJECT":
            strategy = REJECT_CONCEPT_STRATEGIES.get(decision.get("review_strategy"))
            if not strategy or target_id != strategy["target_concept_id"]:
                errors.append(f"unsupported REJECT review in {decision_id}")
                continue
            rejected_topics = decision.get("rejected_topic_references", [])
            if (
                decision.get("rejected_canonical_label")
                != strategy["rejected_canonical_label"]
                or decision.get("rejected_source_terms")
                != strategy["rejected_source_terms"]
                or rejected_topics != strategy["rejected_topic_references"]
                or set(rejected_topics) != set(candidate.get("topic_references", []))
            ):
                errors.append(f"REJECT candidate snapshot mismatch in {decision_id}")
                continue
            if (
                decision.get("rejected_provisional_candidate") is not True
                or decision.get("source_term_identity_not_confirmed") is not True
                or decision.get("all_link_proposals_rejected") is not True
                or decision.get("package_semantic_promotion") is not False
                or not decision.get("rejection_reason")
            ):
                errors.append(f"REJECT safeguards missing in {decision_id}")
                continue

            evidence_partition = []
            for topic_reference, evidence in zip(
                candidate["topic_references"], candidate["evidence_references"]
            ):
                rewrite = {
                    "decision_id": decision_id,
                    "target_concept_ids": [],
                    "review_outcome": "REJECT",
                    "partition_basis": "PRODUCT_OWNER_EXACT_EVIDENCE_REJECTION",
                    "unresolved_exact_term_signal": False,
                }
                link_rewrites[(target_id, topic_reference)] = rewrite
                evidence_partition.append(
                    {"topic_reference": topic_reference, **evidence, **rewrite}
                )

            transformed = [
                item
                for item in transformed
                if item["candidate_concept_id"] != target_id
            ]
            candidate_by_id.pop(target_id)
            resolved.add(target_id)
            resolutions.append(
                {
                    "decision_id": decision_id,
                    "target_candidate_concept_id": target_id,
                    "result_concept_ids": [],
                    "authority": decision["authority"],
                    "review_gate": "DOMAIN_REVIEW",
                    "status": "DECIDED",
                    "outcome": "REJECT",
                    "rejected_provisional_candidate": True,
                    "rejected_canonical_label": decision[
                        "rejected_canonical_label"
                    ],
                    "rejected_source_terms": decision["rejected_source_terms"],
                    "source_term_identity_not_confirmed": True,
                    "rejected_topic_references": rejected_topics,
                    "all_link_proposals_rejected": True,
                    "candidate_snapshot": snapshot,
                    "evidence_partition": evidence_partition,
                    "link_rebuild_authority": (
                        "PRODUCT_OWNER_EXPLICIT_EVIDENCE_LINK_REJECTION"
                    ),
                    "link_semantic_acceptance": False,
                    "rejection_reason": decision["rejection_reason"],
                    "rationale": decision["rationale"],
                    "package_semantic_promotion": False,
                }
            )
            continue
        if outcome == "NEW_CONCEPT":
            strategy = NEW_CONCEPT_STRATEGIES.get(decision.get("review_strategy"))
            if not strategy or target_id != strategy["target_concept_id"]:
                errors.append(f"unsupported NEW_CONCEPT review in {decision_id}")
                continue
            if (
                decision.get("accepted_canonical_label")
                != strategy["accepted_canonical_label"]
                or decision.get("accepted_lexical_forms")
                != strategy["accepted_lexical_forms"]
            ):
                errors.append(f"NEW_CONCEPT terminology mismatch in {decision_id}")
                continue
            accepted_topics = decision.get("accepted_topic_references", [])
            rejected_topics = decision.get("rejected_topic_references", [])
            if (
                accepted_topics != strategy["accepted_topic_references"]
                or rejected_topics != strategy["rejected_topic_references"]
                or set(accepted_topics) & set(rejected_topics)
                or set(accepted_topics) | set(rejected_topics)
                != set(candidate.get("topic_references", []))
            ):
                errors.append(f"NEW_CONCEPT link partition mismatch in {decision_id}")
                continue
            if decision.get("identity_confirmed_reusable") is not True:
                errors.append(f"NEW_CONCEPT reusable identity missing in {decision_id}")
                continue
            if not decision.get("rejected_link_reason"):
                errors.append(f"NEW_CONCEPT rejected-link reason missing in {decision_id}")
                continue
            if decision.get("package_semantic_promotion") is not False:
                errors.append(f"NEW_CONCEPT package promotion in {decision_id}")
                continue

            accepted_evidence: list[dict[str, Any]] = []
            accepted_topic_results: list[str] = []
            evidence_partition = []
            for topic_reference, evidence in zip(
                candidate["topic_references"], candidate["evidence_references"]
            ):
                accepted = topic_reference in accepted_topics
                target_ids = [target_id] if accepted else []
                if accepted:
                    accepted_topic_results.append(topic_reference)
                    accepted_evidence.append(evidence)
                rewrite = {
                    "decision_id": decision_id,
                    "target_concept_ids": target_ids,
                    "review_outcome": "ACCEPT" if accepted else "REJECT",
                    "partition_basis": "EXPLICIT_EVIDENCE_LINK_REVIEW",
                    "unresolved_exact_term_signal": False,
                }
                link_rewrites[(target_id, topic_reference)] = rewrite
                evidence_partition.append(
                    {"topic_reference": topic_reference, **evidence, **rewrite}
                )

            reviewed_candidate = dict(candidate)
            reviewed_candidate["proposed_canonical_label"] = decision[
                "accepted_canonical_label"
            ]
            reviewed_candidate["source_terms"] = decision[
                "accepted_lexical_forms"
            ]
            reviewed_candidate["topic_references"] = accepted_topic_results
            reviewed_candidate["evidence_references"] = accepted_evidence
            position = next(
                index
                for index, item in enumerate(transformed)
                if item["candidate_concept_id"] == target_id
            )
            transformed[position] = reviewed_candidate
            candidate_by_id[target_id] = reviewed_candidate
            resolved.add(target_id)
            resolutions.append(
                {
                    "decision_id": decision_id,
                    "target_candidate_concept_id": target_id,
                    "result_concept_ids": [target_id],
                    "authority": decision["authority"],
                    "review_gate": "DOMAIN_REVIEW",
                    "status": "DECIDED",
                    "outcome": "NEW_CONCEPT",
                    "accepted_canonical_label": decision[
                        "accepted_canonical_label"
                    ],
                    "accepted_lexical_forms": decision[
                        "accepted_lexical_forms"
                    ],
                    "identity_confirmed_reusable": True,
                    "accepted_topic_references": accepted_topics,
                    "rejected_topic_references": rejected_topics,
                    "rejected_link_reason": decision["rejected_link_reason"],
                    "candidate_snapshot": snapshot,
                    "evidence_partition": evidence_partition,
                    "link_rebuild_authority": (
                        "PRODUCT_OWNER_EXPLICIT_EVIDENCE_LINK_REVIEW"
                    ),
                    "link_semantic_acceptance": False,
                    "rationale": decision["rationale"],
                    "package_semantic_promotion": False,
                }
            )
            continue
        if outcome == "SAME_CONCEPT":
            if decision.get("accepted_canonical_label") != candidate.get(
                "proposed_canonical_label"
            ):
                errors.append(f"Concept accepted-label mismatch in {decision_id}")
                continue
            if decision.get("canonical_role") != "UMBRELLA_CONCEPT":
                errors.append(f"Concept umbrella role missing in {decision_id}")
                continue
            if decision.get("identity_scope") != "GENERAL_CORRECTION_PROCESS_ONLY":
                errors.append(f"Concept identity scope mismatch in {decision_id}")
                continue
            if decision.get("separate_method_identities_merged") is not False:
                errors.append(f"Concept method-identity safeguard missing in {decision_id}")
                continue
            if decision.get("method_identity_policy") != (
                "DISTINCT_UNLESS_SEPARATELY_HUMAN_REVIEWED"
            ):
                errors.append(f"Concept method-identity policy mismatch in {decision_id}")
                continue
            resolved.add(target_id)
            resolutions.append(
                {
                    "decision_id": decision_id,
                    "target_candidate_concept_id": target_id,
                    "result_concept_ids": [target_id],
                    "authority": decision["authority"],
                    "review_gate": "DOMAIN_REVIEW",
                    "status": "DECIDED",
                    "outcome": "SAME_CONCEPT",
                    "accepted_canonical_label": decision[
                        "accepted_canonical_label"
                    ],
                    "canonical_role": "UMBRELLA_CONCEPT",
                    "identity_scope": decision["identity_scope"],
                    "separate_method_identities_merged": False,
                    "method_identity_policy": decision["method_identity_policy"],
                    "rationale": decision["rationale"],
                    "package_semantic_promotion": False,
                }
            )
            continue

        retained_spec = decision.get("retained_concept", {})
        strategy = RELATED_PARTITION_STRATEGIES.get(decision.get("partition_strategy"))
        if not strategy or target_id != strategy["target_concept_id"]:
            errors.append(f"unsupported RELATED partition in {decision_id}")
            continue
        if strategy.get("related_concepts"):
            related_specs = decision.get("related_concepts", [])
            strategy_related = strategy["related_concepts"]
            expected_related_ids = [
                item["candidate_concept_id"] for item in strategy_related
            ]
            related_ids = [item.get("candidate_concept_id") for item in related_specs]
            if (
                related_ids != expected_related_ids
                or any(not item or item in candidate_by_id for item in related_ids)
            ):
                errors.append(f"invalid related Concept identities in {decision_id}")
                continue
            if decision.get("semantic_relations") != strategy["semantic_relations"]:
                errors.append(f"RELATED semantic relations mismatch in {decision_id}")
                continue
            if (
                retained_spec.get("candidate_concept_id") != target_id
                or not retained_spec.get("proposed_canonical_label")
                or any(not item.get("proposed_canonical_label") for item in related_specs)
            ):
                errors.append(f"RELATED Concept results mismatch in {decision_id}")
                continue
            term_groups = [
                retained_spec.get("source_terms", []),
                *(item.get("source_terms", []) for item in related_specs),
            ]
            flattened_terms = [term for group in term_groups for term in group]
            if (
                len(flattened_terms) != len(set(flattened_terms))
                or set(flattened_terms) != set(candidate.get("source_terms", []))
            ):
                errors.append(f"RELATED source-term partition mismatch in {decision_id}")
                continue
            if decision.get("identities_merged") is not False:
                errors.append(f"RELATED decision merged identities in {decision_id}")
                continue
            if decision.get("relation") != "RELATED":
                errors.append(f"RELATED relation missing in {decision_id}")
                continue
            if len(candidate.get("topic_references", [])) != len(
                candidate.get("evidence_references", [])
            ):
                errors.append(f"Concept reference alignment mismatch in {decision_id}")
                continue

            retained_pattern = re.compile(
                CONCEPT_PATTERNS[strategy["retained_pattern_key"]], re.IGNORECASE
            )
            related_patterns = {
                item["candidate_concept_id"]: re.compile(
                    CONCEPT_PATTERNS[item["pattern_key"]], re.IGNORECASE
                )
                for item in strategy_related
            }
            topics_by_id: dict[str, list[str]] = {
                target_id: [],
                **{item: [] for item in related_ids},
            }
            evidence_by_id: dict[str, list[dict[str, Any]]] = {
                target_id: [],
                **{item: [] for item in related_ids},
            }
            evidence_partition = []
            for topic_reference, evidence in zip(
                candidate["topic_references"], candidate["evidence_references"]
            ):
                source_id = evidence["source_id"]
                start = word_sequence(evidence["start_word_id"])
                end = word_sequence(evidence["end_word_id"])
                source_words = words_by_source[source_id]
                text = " ".join(
                    item["text"] for item in source_words[start : end + 1]
                )
                match_counts = {
                    target_id: len(retained_pattern.findall(text)),
                    **{
                        concept_id: len(pattern.findall(text))
                        for concept_id, pattern in related_patterns.items()
                    },
                }
                target_ids = [
                    concept_id
                    for concept_id, count in match_counts.items()
                    if count
                ]
                unresolved = not target_ids
                if unresolved:
                    target_ids = [target_id]
                for concept_id in target_ids:
                    topics_by_id[concept_id].append(topic_reference)
                    evidence_by_id[concept_id].append(evidence)
                rewrite = {
                    "decision_id": decision_id,
                    "target_concept_ids": target_ids,
                    "exact_match_counts": match_counts,
                    "unresolved_exact_term_signal": unresolved,
                }
                link_rewrites[(target_id, topic_reference)] = rewrite
                evidence_partition.append(
                    {"topic_reference": topic_reference, **evidence, **rewrite}
                )

            retained = dict(candidate)
            retained["proposed_canonical_label"] = retained_spec[
                "proposed_canonical_label"
            ]
            retained["source_terms"] = retained_spec["source_terms"]
            retained["topic_references"] = topics_by_id[target_id]
            retained["evidence_references"] = evidence_by_id[target_id]
            related_candidates = [
                {
                    "candidate_concept_id": spec["candidate_concept_id"],
                    "proposed_canonical_label": spec["proposed_canonical_label"],
                    "source_terms": spec["source_terms"],
                    "topic_references": topics_by_id[spec["candidate_concept_id"]],
                    "evidence_references": evidence_by_id[
                        spec["candidate_concept_id"]
                    ],
                    "semantic_status": "PROVISIONAL",
                    "review_status": "DOMAIN_REVIEW_DECIDED",
                }
                for spec in related_specs
            ]
            position = next(
                index
                for index, item in enumerate(transformed)
                if item["candidate_concept_id"] == target_id
            )
            transformed[position : position + 1] = [retained, *related_candidates]
            candidate_by_id[target_id] = retained
            for related_candidate in related_candidates:
                candidate_by_id[
                    related_candidate["candidate_concept_id"]
                ] = related_candidate
            result_ids = [target_id, *related_ids]
            resolved.update(result_ids)
            resolutions.append(
                {
                    "decision_id": decision_id,
                    "target_candidate_concept_id": target_id,
                    "result_concept_ids": result_ids,
                    "authority": decision["authority"],
                    "review_gate": "DOMAIN_REVIEW",
                    "status": "DECIDED",
                    "outcome": "RELATED",
                    "relation": "RELATED",
                    "semantic_relations": decision["semantic_relations"],
                    "identities_merged": False,
                    "retained_concept": retained_spec,
                    "related_concepts": related_specs,
                    "evidence_partition": evidence_partition,
                    "link_rebuild_authority": (
                        "CODEX_DETERMINISTIC_EXACT_TERM_PARTITION"
                    ),
                    "link_semantic_acceptance": False,
                    "rationale": decision["rationale"],
                    "package_semantic_promotion": False,
                }
            )
            continue

        related = decision.get("related_concept", {})
        related_id = related.get("candidate_concept_id")
        if not related_id or related_id in candidate_by_id:
            errors.append(f"invalid related Concept identity in {decision_id}")
            continue
        if related_id != strategy["related_concept_id"]:
            errors.append(f"RELATED result identity mismatch in {decision_id}")
            continue
        if decision.get("semantic_relation") != strategy["semantic_relation"]:
            errors.append(f"RELATED semantic relation mismatch in {decision_id}")
            continue
        if (
            retained_spec.get("candidate_concept_id") != target_id
            or not retained_spec.get("proposed_canonical_label")
            or not related.get("proposed_canonical_label")
        ):
            errors.append(f"RELATED Concept result mismatch in {decision_id}")
            continue
        retained_terms = retained_spec.get("source_terms", [])
        related_terms = related.get("source_terms", [])
        shared_contextual_terms = set(
            strategy.get("shared_contextual_source_terms", [])
        )
        if (
            set(retained_terms) & set(related_terms) != shared_contextual_terms
            or set(retained_terms) | set(related_terms)
            != set(candidate.get("source_terms", []))
            or decision.get("shared_contextual_source_terms", [])
            != strategy.get("shared_contextual_source_terms", [])
        ):
            errors.append(f"RELATED source-term partition mismatch in {decision_id}")
            continue
        retained_topic_partition = strategy.get("retained_topic_references")
        related_topic_partition = strategy.get("related_topic_references")
        if retained_topic_partition is not None:
            if (
                decision.get("retained_topic_references")
                != retained_topic_partition
                or decision.get("related_topic_references")
                != related_topic_partition
                or set(retained_topic_partition) & set(related_topic_partition)
                or set(retained_topic_partition) | set(related_topic_partition)
                != set(candidate.get("topic_references", []))
            ):
                errors.append(f"RELATED context partition mismatch in {decision_id}")
                continue
            if (
                decision.get("component_concept_labels")
                != strategy.get("component_concept_labels")
                or decision.get("component_identities_merged")
                is not strategy.get("component_identities_merged")
            ):
                errors.append(f"RELATED component safeguard mismatch in {decision_id}")
                continue
        if decision.get("identities_merged") is not False:
            errors.append(f"RELATED decision merged identities in {decision_id}")
            continue
        if decision.get("relation") != "RELATED":
            errors.append(f"RELATED relation missing in {decision_id}")
            continue
        if len(candidate.get("topic_references", [])) != len(
            candidate.get("evidence_references", [])
        ):
            errors.append(f"Concept reference alignment mismatch in {decision_id}")
            continue

        retained_pattern = re.compile(
            CONCEPT_PATTERNS[strategy["retained_pattern_key"]], re.IGNORECASE
        )
        related_pattern = re.compile(
            CONCEPT_PATTERNS[strategy["related_pattern_key"]], re.IGNORECASE
        )
        retained_topics: list[str] = []
        retained_evidence: list[dict[str, Any]] = []
        related_topics: list[str] = []
        related_evidence: list[dict[str, Any]] = []
        evidence_partition = []
        for topic_reference, evidence in zip(
            candidate["topic_references"], candidate["evidence_references"]
        ):
            source_id = evidence["source_id"]
            start = word_sequence(evidence["start_word_id"])
            end = word_sequence(evidence["end_word_id"])
            source_words = words_by_source[source_id]
            text = " ".join(item["text"] for item in source_words[start : end + 1])
            retained_matches = len(retained_pattern.findall(text))
            related_matches = len(related_pattern.findall(text))
            target_ids = []
            if retained_topic_partition is not None:
                if topic_reference in retained_topic_partition:
                    target_ids.append(target_id)
                elif topic_reference in related_topic_partition:
                    target_ids.append(related_id)
                else:
                    errors.append(
                        f"unpartitioned RELATED context in {decision_id}: "
                        f"{topic_reference}"
                    )
            elif retained_matches or not related_matches:
                target_ids.append(target_id)
            if target_id in target_ids:
                retained_topics.append(topic_reference)
                retained_evidence.append(evidence)
            if (
                related_id in target_ids
                or retained_topic_partition is None
                and related_matches
            ):
                related_topics.append(topic_reference)
                related_evidence.append(evidence)
                if related_id not in target_ids:
                    target_ids.append(related_id)
            link_rewrites[(target_id, topic_reference)] = {
                "decision_id": decision_id,
                "target_concept_ids": target_ids,
                "exact_retained_match_count": retained_matches,
                "exact_related_match_count": related_matches,
                "unresolved_exact_term_signal": (
                    not retained_matches
                    and not related_matches
                    and retained_topic_partition is None
                ),
                "partition_basis": (
                    "EXPLICIT_EVIDENCE_CONTEXT"
                    if retained_topic_partition is not None
                    else "EXACT_TERM_MATCH"
                ),
            }
            evidence_partition.append(
                {
                    "topic_reference": topic_reference,
                    **evidence,
                    **link_rewrites[(target_id, topic_reference)],
                }
            )

        retained = dict(candidate)
        retained["proposed_canonical_label"] = retained_spec[
            "proposed_canonical_label"
        ]
        retained["source_terms"] = retained_terms
        retained["topic_references"] = retained_topics
        retained["evidence_references"] = retained_evidence
        related_candidate = {
            "candidate_concept_id": related_id,
            "proposed_canonical_label": related["proposed_canonical_label"],
            "source_terms": related["source_terms"],
            "topic_references": related_topics,
            "evidence_references": related_evidence,
            "semantic_status": "PROVISIONAL",
            "review_status": "DOMAIN_REVIEW_DECIDED",
        }
        position = next(
            index
            for index, item in enumerate(transformed)
            if item["candidate_concept_id"] == target_id
        )
        transformed[position : position + 1] = [retained, related_candidate]
        candidate_by_id[target_id] = retained
        candidate_by_id[related_id] = related_candidate
        resolved.update({target_id, related_id})
        resolutions.append(
            {
                "decision_id": decision_id,
                "target_candidate_concept_id": target_id,
                "result_concept_ids": [target_id, related_id],
                "authority": decision["authority"],
                "review_gate": "DOMAIN_REVIEW",
                "status": "DECIDED",
                "outcome": "RELATED",
                "relation": "RELATED",
                "semantic_relation": decision.get("semantic_relation"),
                "shared_contextual_source_terms": decision.get(
                    "shared_contextual_source_terms", []
                ),
                "component_concept_labels": decision.get(
                    "component_concept_labels", []
                ),
                "component_identities_merged": decision.get(
                    "component_identities_merged"
                ),
                "identities_merged": False,
                "retained_concept": retained_spec,
                "related_concept": related,
                "evidence_partition": evidence_partition,
                "link_rebuild_authority": (
                    "CODEX_DETERMINISTIC_EVIDENCE_CONTEXT_PARTITION"
                    if retained_topic_partition is not None
                    else "CODEX_DETERMINISTIC_EXACT_TERM_PARTITION"
                ),
                "link_semantic_acceptance": False,
                "rationale": decision["rationale"],
                "package_semantic_promotion": False,
            }
        )
    return transformed, resolutions, resolved, link_rewrites


def apply_link_decisions(
    link_results: list[dict[str, Any]],
    decision_ledger: dict[str, Any],
    topic_results: list[dict[str, Any]],
    words_by_source: dict[str, list[dict[str, Any]]],
    errors: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply exact Product Owner decisions over provisional Topic→Concept links."""

    transformed = [dict(item) for item in link_results]
    resolutions: list[dict[str, Any]] = []
    decided: set[str] = set()
    for decision in decision_ledger.get("link_decisions", []):
        decision_id = decision.get("decision_id", "<missing>")
        target_id = decision.get("target_link_id")
        if decision.get("authority") != "PRODUCT_OWNER_DOMAIN_REVIEW":
            errors.append(f"non-authoritative link decision {decision_id}")
            continue
        outcome = decision.get("outcome")
        if outcome not in {
            "ACCEPT_LINK",
            "REJECT_LINK",
            "REMAP_LINK",
            "MERGE_LINK_PROVENANCE",
        }:
            errors.append(f"unsupported link decision outcome in {decision_id}")
            continue
        if target_id in decided:
            errors.append(f"duplicate link decision target {target_id}")
            continue
        link = next(
            (item for item in transformed if item["link_id"] == target_id),
            None,
        )
        if link is None:
            errors.append(f"orphan link decision target {target_id}")
            continue
        snapshot = decision.get("link_snapshot", {})
        if snapshot != {
            "input_topic_reference": link["input_topic_reference"],
            "candidate_concept_reference": link["candidate_concept_reference"],
            "source_id": link["source_id"],
            "classification": link["classification"],
            "exact_term_target_references": link["exact_term_target_references"],
            "evidence_support": link["evidence_support"],
        }:
            errors.append(f"link snapshot mismatch in {decision_id}")
            continue
        if link["classification"] != "LINK_EXCEPTION":
            errors.append(f"link decision target is not an exception in {decision_id}")
            continue
        if (
            decision.get("topic_changed") is not False
            or decision.get("concept_changed") is not False
            or decision.get("package_semantic_promotion") is not False
        ):
            errors.append(f"link rejection safeguards missing in {decision_id}")
            continue

        if outcome == "ACCEPT_LINK":
            accepted_topic = next(
                (
                    item
                    for item in topic_results
                    if item["topic_id"] == link["input_topic_reference"]
                ),
                None,
            )
            concept_key = link["candidate_concept_reference"].removeprefix(
                "issue_68_candidate_concept_"
            )
            pattern = CONCEPT_PATTERNS[concept_key]
            if accepted_topic is None or accepted_topic["source_id"] != link["source_id"]:
                errors.append(f"accepted link Topic mismatch in {decision_id}")
                continue
            source_words = words_by_source[accepted_topic["source_id"]]
            start = accepted_topic["start_word_sequence"]
            end = accepted_topic["end_word_sequence"]
            accepted_text = " ".join(
                item["text"] for item in source_words[start : end + 1]
            )
            match_count = len(list(re.finditer(pattern, accepted_text, re.IGNORECASE)))
            if (
                decision.get("single_match_context_reviewed") is not True
                or match_count != decision.get("expected_exact_pattern_match_count")
                or match_count != 1
                or not decision.get("accept_reason")
            ):
                errors.append(f"accepted link evidence mismatch in {decision_id}")
                continue

            accepted = {
                **link,
                "classification": "LINK_CLEAR",
                "relevance_basis": (
                    "PRODUCT_OWNER_ACCEPT_WITH_CONTEXT_REVIEWED_EXACT_EVIDENCE"
                ),
                "semantic_status": "PROVISIONAL",
                "domain_review_status": "DECIDED",
                "link_review_decision_id": decision_id,
            }
            position = next(
                index
                for index, item in enumerate(transformed)
                if item["link_id"] == target_id
            )
            transformed[position] = accepted
            decided.add(target_id)
            resolutions.append(
                {
                    "decision_id": decision_id,
                    "target_link_id": target_id,
                    "result_link_id": target_id,
                    "authority": decision["authority"],
                    "review_gate": "DOMAIN_REVIEW",
                    "status": "DECIDED",
                    "outcome": "ACCEPT_LINK",
                    "owner_decision": "ACCEPT",
                    "link_snapshot": snapshot,
                    "accepted_topic_reference": link["input_topic_reference"],
                    "accepted_exact_pattern_match_count": match_count,
                    "single_match_context_reviewed": True,
                    "topic_changed": False,
                    "concept_changed": False,
                    "accept_reason": decision["accept_reason"],
                    "rationale": decision["rationale"],
                    "package_semantic_promotion": False,
                }
            )
            continue

        if outcome == "MERGE_LINK_PROVENANCE":
            merge_target_id = decision.get("merge_into_link_id")
            merge_target = next(
                (
                    item
                    for item in transformed
                    if item["link_id"] == merge_target_id
                ),
                None,
            )
            if (
                merge_target is None
                or merge_target_id == target_id
                or merge_target["candidate_concept_reference"]
                != link["candidate_concept_reference"]
                or merge_target["source_id"] != link["source_id"]
                or merge_target["input_topic_reference"]
                != decision.get("contained_by_topic_reference")
                or link["overlapping_authored_topic_references"]
                != [decision.get("contained_by_topic_reference")]
                or decision.get("additional_semantic_link_created") is not False
                or not decision.get("merge_reason")
            ):
                errors.append(f"link provenance merge mismatch in {decision_id}")
                continue
            if any(
                item.get("source_link_id") == target_id
                for item in merge_target.get("merged_source_link_provenance", [])
            ):
                errors.append(f"duplicate merged link provenance in {decision_id}")
                continue

            provenance = {
                "decision_id": decision_id,
                "source_link_id": target_id,
                "source_topic_reference": link["input_topic_reference"],
                "evidence_support": link["evidence_support"],
                "merge_basis": "CONTAINED_BY_ALREADY_REVIEWED_AUTHORED_TOPIC",
                "semantic_link_created": False,
            }
            merged = dict(merge_target)
            merged["merged_source_link_provenance"] = [
                *merge_target.get("merged_source_link_provenance", []),
                provenance,
            ]
            merged["merged_provenance_decision_ids"] = [
                *merge_target.get("merged_provenance_decision_ids", []),
                decision_id,
            ]
            transformed = [item for item in transformed if item["link_id"] != target_id]
            merge_position = next(
                index
                for index, item in enumerate(transformed)
                if item["link_id"] == merge_target_id
            )
            transformed[merge_position] = merged
            decided.add(target_id)
            resolutions.append(
                {
                    "decision_id": decision_id,
                    "target_link_id": target_id,
                    "result_link_id": merge_target_id,
                    "authority": decision["authority"],
                    "review_gate": "DOMAIN_REVIEW",
                    "status": "DECIDED",
                    "outcome": "MERGE_LINK_PROVENANCE",
                    "link_snapshot": snapshot,
                    "contained_by_topic_reference": decision[
                        "contained_by_topic_reference"
                    ],
                    "merged_source_link_provenance": provenance,
                    "additional_semantic_link_created": False,
                    "topic_changed": False,
                    "concept_changed": False,
                    "merge_reason": decision["merge_reason"],
                    "rationale": decision["rationale"],
                    "package_semantic_promotion": False,
                }
            )
            continue

        if outcome == "REMAP_LINK":
            replacement_topic_id = decision.get("replacement_topic_reference")
            replacement_topic = next(
                (
                    item
                    for item in topic_results
                    if item["topic_id"] == replacement_topic_id
                ),
                None,
            )
            expected_topic_snapshot = decision.get("replacement_topic_snapshot")
            if replacement_topic is None or expected_topic_snapshot != {
                "source_id": replacement_topic["source_id"],
                "title": replacement_topic["title"],
                "start_word_id": replacement_topic["start_word_id"],
                "end_word_id": replacement_topic["end_word_id"],
                "canonical_evidence_sha256": replacement_topic[
                    "canonical_evidence_sha256"
                ],
            }:
                errors.append(f"replacement Topic snapshot mismatch in {decision_id}")
                continue
            if replacement_topic["source_id"] != link["source_id"]:
                errors.append(f"cross-source link remap in {decision_id}")
                continue
            concept_key = link["candidate_concept_reference"].removeprefix(
                "issue_68_candidate_concept_"
            )
            pattern = CONCEPT_PATTERNS[concept_key]
            source_words = words_by_source[replacement_topic["source_id"]]
            start = replacement_topic["start_word_sequence"]
            end = replacement_topic["end_word_sequence"]
            replacement_words = source_words[start : end + 1]
            replacement_text = " ".join(item["text"] for item in replacement_words)
            match_count = len(
                list(re.finditer(pattern, replacement_text, re.IGNORECASE))
            )
            single_match_context_reviewed = (
                decision.get("single_match_context_reviewed") is True
            )
            if (
                match_count != decision.get("expected_exact_pattern_match_count")
                or match_count < (1 if single_match_context_reviewed else 2)
                or not decision.get("remap_reason")
            ):
                errors.append(f"replacement evidence mismatch in {decision_id}")
                continue
            replacement_link_id = (
                f"issue_68_link_{replacement_topic_id}_{concept_key}"
            )
            if any(
                item["link_id"] == replacement_link_id
                and item["link_id"] != target_id
                for item in transformed
            ):
                errors.append(f"duplicate replacement link in {decision_id}")
                continue
            replacement_evidence = {
                "authored_topic_reference": replacement_topic_id,
                "intersection_start_word_id": replacement_words[0]["id"],
                "intersection_end_word_id": replacement_words[-1]["id"],
                "intersection_sha256": sha256_bytes(
                    replacement_text.encode("utf-8")
                ),
                "exact_pattern_match_count": match_count,
                "authored_title_correspondence": bool(
                    re.search(pattern, replacement_topic["title"], re.IGNORECASE)
                ),
            }
            resolution = {
                "decision_id": decision_id,
                "target_link_id": target_id,
                "result_link_id": replacement_link_id,
                "authority": decision["authority"],
                "review_gate": "DOMAIN_REVIEW",
                "status": "DECIDED",
                "outcome": "REMAP_LINK",
                "link_snapshot": snapshot,
                "replacement_topic_reference": replacement_topic_id,
                "replacement_topic_snapshot": expected_topic_snapshot,
                "replacement_evidence_support": replacement_evidence,
                "single_match_context_reviewed": single_match_context_reviewed,
                "topic_changed": False,
                "concept_changed": False,
                "remap_reason": decision["remap_reason"],
                "rationale": decision["rationale"],
                "package_semantic_promotion": False,
            }
            replacement = {
                "link_id": replacement_link_id,
                "input_topic_reference": replacement_topic_id,
                "candidate_concept_reference": link[
                    "candidate_concept_reference"
                ],
                "source_id": link["source_id"],
                "classification": "LINK_CLEAR",
                "overlapping_authored_topic_references": [replacement_topic_id],
                "exact_term_target_references": [replacement_topic_id],
                "recommended_target_topic_references": [replacement_topic_id],
                "evidence_support": [replacement_evidence],
                "relevance_basis": (
                    "PRODUCT_OWNER_REMAP_WITH_CONTEXT_REVIEWED_EXACT_EVIDENCE"
                    if single_match_context_reviewed
                    else "PRODUCT_OWNER_REMAP_WITH_REPEATED_EXACT_EVIDENCE"
                ),
                "semantic_status": "PROVISIONAL",
                "domain_review_status": "DECIDED",
                "link_review_decision_id": decision_id,
            }
            position = next(
                index
                for index, item in enumerate(transformed)
                if item["link_id"] == target_id
            )
            transformed[position] = replacement
            decided.add(target_id)
            resolutions.append(resolution)
            continue

        rejection_basis = decision.get("rejection_basis")
        if rejection_basis is None and decision.get("named_program_reference_only") is True:
            rejection_basis = "NAMED_PROGRAM_REFERENCE_ONLY"
        valid_rejection_basis = (
            rejection_basis == "NAMED_PROGRAM_REFERENCE_ONLY"
            and decision.get("named_program_reference_only") is True
            or rejection_basis == "ALTERNATIVE_METHOD_MENTION_ONLY"
            and decision.get("alternative_method_reference_only") is True
        )
        if (
            not decision.get("rejection_reason")
            or not valid_rejection_basis
        ):
            errors.append(f"link rejection safeguards missing in {decision_id}")
            continue

        transformed = [item for item in transformed if item["link_id"] != target_id]
        decided.add(target_id)
        resolutions.append(
            {
                "decision_id": decision_id,
                "target_link_id": target_id,
                "authority": decision["authority"],
                "review_gate": "DOMAIN_REVIEW",
                "status": "DECIDED",
                "outcome": "REJECT_LINK",
                "link_snapshot": snapshot,
                "rejection_basis": rejection_basis,
                "named_program_reference_only": (
                    decision.get("named_program_reference_only") is True
                ),
                "alternative_method_reference_only": (
                    decision.get("alternative_method_reference_only") is True
                ),
                "topic_changed": False,
                "concept_changed": False,
                "rejection_reason": decision["rejection_reason"],
                "rationale": decision["rationale"],
                "package_semantic_promotion": False,
            }
        )
    return transformed, resolutions


def build_qa(
    repository: Path,
    project: Path,
    review_result_path: Path,
    semantic_package_path: Path,
    domain_review_decisions_path: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    package = read_json(semantic_package_path)
    bundle_path = project / "evidence/canonical_bundle.json"
    bundle = read_json(bundle_path)
    authoring_builder = load_authoring_builder(repository)
    baseline, _ = authoring_builder.build_package(project, review_result_path, None)

    if package.get("semantic_authority") != "PROVISIONAL_UNREVIEWED":
        errors.append("semantic package is not PROVISIONAL_UNREVIEWED")
    progress = package.get("domain_authoring_progress", {})
    if progress.get("completed") != 262 or progress.get("pending") != 0:
        errors.append("DOMAIN_AUTHORING is not complete at 262/262")
    if baseline.get("errors"):
        errors.extend(f"baseline: {item}" for item in baseline["errors"])
    if len(baseline.get("concept_candidates", [])) != 18:
        errors.append("baseline Concept candidate count is not 18")
    if len(baseline.get("topic_concept_link_proposals", [])) != 254:
        errors.append("baseline Topic-to-Concept link count is not 254")
    for source_id in SOURCE_ORDER:
        coverage = package.get("coverage", {}).get(source_id, {})
        if coverage.get("gaps") or coverage.get("overlaps"):
            errors.append(f"coverage defect in {source_id}")

    words_by_source: dict[str, list[dict[str, Any]]] = {}
    for word in bundle["words"]:
        words_by_source.setdefault(word["source_id"], []).append(word)
    for words in words_by_source.values():
        words.sort(key=lambda item: item["sequence"])

    decision_ledger = read_json(domain_review_decisions_path)
    units = authored_units(package)
    units, domain_review_resolutions, resolved_topic_ids = apply_domain_review_decisions(
        units, decision_ledger, words_by_source, errors
    )
    topic_results: list[dict[str, Any]] = []
    for unit in units:
        words = words_by_source[unit["source_id"]][
            unit["start_word_sequence"] : unit["end_word_sequence"] + 1
        ]
        if not words or words[0]["id"] != unit["start_word_id"] or words[-1]["id"] != unit["end_word_id"]:
            errors.append(f"unresolved exact evidence for {unit['topic_id']}")
            continue
        full_text = " ".join(item["text"] for item in words)
        exception = (
            None
            if unit["topic_id"] in resolved_topic_ids
            else TOPIC_EXCEPTIONS.get(unit["topic_id"])
        )
        terminology_normalized = (
            unit.get("domain_review_action")
            == "CONFIRM_AUDIO_RECESSION_SEMANTIC_NORMALIZATION_TO_REGRESSION"
        )
        classification = "REVIEW_EXCEPTION" if exception else "REVIEW_CLEAR"
        correction = exception.get("recommended_correction", {}) if exception else {}
        boundary_action = correction.get("action")
        left_boundary_requires_review = bool(
            exception
            and (
                boundary_action in {"REALIGN_LEFT", "SPLIT_REALIGN"}
                or correction.get("exclude_as_nonsemantic")
            )
        )
        right_boundary_requires_review = bool(
            exception
            and (
                boundary_action == "SPLIT_REALIGN"
                or "TRANSITION_SPLIT" in exception["taxonomy"]
                or "OVER-MERGE" in exception["taxonomy"]
            )
        )
        result = {
            **unit,
            "word_count": len(words),
            "canonical_evidence_sha256": sha256_bytes(full_text.encode("utf-8")),
            "evidence_preview": evidence_excerpt(words),
            "classification": classification,
            "review_method": "CODEX_SEMANTIC_QA_OVER_FULL_CANONICAL_WORD_RANGE",
            "semantic_status": "PROVISIONAL",
            "domain_review_status": (
                "DECIDED" if unit["topic_id"] in resolved_topic_ids else "REVIEW_REQUIRED"
            ),
            "qa_dimensions": {
                "title_content_correspondence": (
                    "REVIEW_REQUIRED"
                    if exception and "MALFORMED_TITLE" in exception["taxonomy"]
                    else "PASS"
                ),
                "left_boundary": "REVIEW_REQUIRED" if left_boundary_requires_review else "PASS",
                "right_boundary": "REVIEW_REQUIRED" if right_boundary_requires_review else "PASS",
                "semantic_coherence": "REVIEW_REQUIRED" if exception else "PASS",
                "neighbor_relationship": "REVIEW_REQUIRED" if exception else "PASS",
                "provenance": "PASS",
                "transcript_assurance": (
                    "SELECTIVE_AUDIO_TERM_VERIFIED"
                    if terminology_normalized
                    else "MACHINE_UNVERIFIED_EXPLICIT"
                ),
            },
            "protected_pattern": VALID_SHORT_TOPICS.get(unit["topic_id"]),
        }
        if exception:
            result["exception"] = {**exception, "human_decision_required": True}
        if unit["topic_id"] in resolved_topic_ids:
            result["domain_review_resolution"] = next(
                item
                for item in domain_review_resolutions
                if unit["topic_id"] in item["result_topic_ids"]
            )
        topic_results.append(result)

    link_units: list[dict[str, Any]] = [
        {
            "topic_id": item["topic_id"],
            "source_id": item["source_id"],
            "title": item["title"],
            "start_word_sequence": item["start_word_sequence"],
            "end_word_sequence": item["end_word_sequence"],
        }
        for item in topic_results
    ]
    for item in package["day_1"]["topics"]:
        start = word_sequence(item["start_word_id"])
        end = word_sequence(item["end_word_id"])
        link_units.append(
            {
                "topic_id": item["topic_id"],
                "source_id": item["source_id"],
                "title": item["title"],
                "start_word_sequence": start,
                "end_word_sequence": end,
            }
        )

    (
        reviewed_concept_candidates,
        concept_identity_resolutions,
        resolved_concept_ids,
        concept_link_rewrites,
    ) = apply_concept_identity_decisions(
        baseline["concept_candidates"], decision_ledger, words_by_source, errors
    )
    concept_results = []
    for candidate in reviewed_concept_candidates:
        candidate_id = candidate["candidate_concept_id"]
        exception = (
            None
            if candidate_id in resolved_concept_ids
            else CONCEPT_EXCEPTIONS.get(candidate_id)
        )
        result = {
            "candidate_concept_id": candidate_id,
            "proposed_canonical_label": candidate["proposed_canonical_label"],
            "source_terms": candidate["source_terms"],
            "evidence_reference_count": len(candidate["evidence_references"]),
            "classification": "IDENTITY_EXCEPTION" if exception else "CLEAR_FOR_HUMAN_BATCH_REVIEW",
            "exception": ({**exception, "human_decision_required": True} if exception else None),
            "semantic_status": "PROVISIONAL",
            "domain_review_status": (
                "DECIDED" if candidate_id in resolved_concept_ids else "REVIEW_REQUIRED"
            ),
        }
        if candidate_id in resolved_concept_ids:
            result["domain_review_resolution"] = next(
                item
                for item in concept_identity_resolutions
                if candidate_id in item["result_concept_ids"]
            )
        concept_results.append(result)

    baseline_topics = {
        item["proposal_id"]: item for item in baseline["topic_proposals"]
    }
    for item in baseline["day_1"]["topics"]:
        baseline_topics[item["topic_id"]] = {
            "source_id": item["source_id"],
            "start_word_sequence": word_sequence(item["start_word_id"]),
            "end_word_sequence": word_sequence(item["end_word_id"]),
            "proposed_title": item["title"],
        }

    reviewed_links = []
    for link in baseline["topic_concept_link_proposals"]:
        rewrite = concept_link_rewrites.get(
            (link["candidate_concept_reference"], link["topic_reference"])
        )
        target_concept_ids = (
            rewrite["target_concept_ids"]
            if rewrite
            else [link["candidate_concept_reference"]]
        )
        original_key = link["candidate_concept_reference"].removeprefix(
            "issue_68_candidate_concept_"
        )
        for target_concept_id in target_concept_ids:
            rebuilt = dict(link)
            rebuilt["candidate_concept_reference"] = target_concept_id
            if target_concept_id != link["candidate_concept_reference"]:
                target_key = target_concept_id.removeprefix(
                    "issue_68_candidate_concept_"
                )
                rebuilt["link_id"] = (
                    link["link_id"].removesuffix(f"_{original_key}")
                    + f"_{target_key}"
                )
            if rewrite:
                rebuilt["concept_identity_rebuild"] = {
                    **rewrite,
                    "semantic_status": "PROVISIONAL",
                    "semantic_acceptance": False,
                }
            reviewed_links.append(rebuilt)

    link_results = []
    for link in reviewed_links:
        concept_key = link["candidate_concept_reference"].removeprefix(
            "issue_68_candidate_concept_"
        )
        pattern = CONCEPT_PATTERNS[concept_key]
        original = baseline_topics[link["topic_reference"]]
        overlaps = [
            unit
            for unit in link_units
            if unit["source_id"] == original["source_id"]
            and unit["start_word_sequence"] <= original["end_word_sequence"]
            and unit["end_word_sequence"] >= original["start_word_sequence"]
        ]
        exact_targets = []
        context_supported_targets = []
        evidence_support = []
        for unit in overlaps:
            intersection_start = max(
                unit["start_word_sequence"], original["start_word_sequence"]
            )
            intersection_end = min(
                unit["end_word_sequence"], original["end_word_sequence"]
            )
            intersection_words = words_by_source[unit["source_id"]][
                intersection_start : intersection_end + 1
            ]
            intersection_text = " ".join(item["text"] for item in intersection_words)
            matches = list(re.finditer(pattern, intersection_text, re.IGNORECASE))
            title_match = bool(re.search(pattern, unit["title"], re.IGNORECASE))
            if matches:
                exact_targets.append(unit["topic_id"])
            if matches and (title_match or len(matches) >= 2):
                context_supported_targets.append(unit["topic_id"])
            evidence_support.append(
                {
                    "authored_topic_reference": unit["topic_id"],
                    "intersection_start_word_id": intersection_words[0]["id"],
                    "intersection_end_word_id": intersection_words[-1]["id"],
                    "intersection_sha256": sha256_bytes(
                        intersection_text.encode("utf-8")
                    ),
                    "exact_pattern_match_count": len(matches),
                    "authored_title_correspondence": title_match,
                }
            )
        is_clear = bool(context_supported_targets)
        classification = "LINK_CLEAR" if is_clear else "LINK_EXCEPTION"
        result = {
            "link_id": link["link_id"],
            "input_topic_reference": link["topic_reference"],
            "candidate_concept_reference": link["candidate_concept_reference"],
            "source_id": link["source_id"],
            "classification": classification,
            "overlapping_authored_topic_references": [item["topic_id"] for item in overlaps],
            "exact_term_target_references": exact_targets,
            "recommended_target_topic_references": context_supported_targets,
            "evidence_support": evidence_support,
            "relevance_basis": (
                "AUTHORED_TITLE_OR_REPEATED_EXACT_EVIDENCE"
                if is_clear
                else "INSUFFICIENT_CONTEXT_BEYOND_SINGLE_OR_MISSING_TERM_SIGNAL"
            ),
            "semantic_status": "PROVISIONAL",
        }
        if "concept_identity_rebuild" in link:
            result["concept_identity_rebuild"] = link[
                "concept_identity_rebuild"
            ]
        if not is_clear:
            result["exception"] = {
                "problem": (
                    "The current proposal is not supported beyond a single or "
                    "missing term signal in the authored semantic unit(s)."
                ),
                "recommended_correction": "Review the exact context and accept, remap, or reject this link.",
                "human_decision_required": True,
                "confidence": "MEDIUM",
            }
        link_results.append(result)

    link_results, link_review_resolutions = apply_link_decisions(
        link_results, decision_ledger, topic_results, words_by_source, errors
    )

    topic_clear = sum(item["classification"] == "REVIEW_CLEAR" for item in topic_results)
    topic_exceptions = sum(
        item["classification"] == "REVIEW_EXCEPTION" for item in topic_results
    )
    concept_clear = sum(
        item["classification"] == "CLEAR_FOR_HUMAN_BATCH_REVIEW"
        for item in concept_results
    )
    link_clear = sum(item["classification"] == "LINK_CLEAR" for item in link_results)

    first_topic_exception = next(
        (item for item in topic_results if item["classification"] == "REVIEW_EXCEPTION"),
        None,
    )
    first_concept_exception = next(
        (item for item in concept_results if item["classification"] == "IDENTITY_EXCEPTION"),
        None,
    )
    first_link_exception = next(
        (item for item in link_results if item["classification"] == "LINK_EXCEPTION"),
        None,
    )
    first_exception = first_topic_exception or first_concept_exception or first_link_exception
    transcript_exception_results = [dict(item) for item in TRANSCRIPT_EXCEPTIONS]
    for item in transcript_exception_results:
        if item["exception_id"] == "issue_68_transcript_exception_regression_term":
            item["partial_resolution"] = {
                "topic_id": "issue_68_video_004_topic_proposal_001c",
                "decision_id": "issue_68_domain_review_topic_001c",
                "status": "SOURCE_TERM_CONFIRMED_SEMANTIC_TERM_NORMALIZED",
                "source_term": "рецессия",
                "semantic_term": "регрессия",
                "transcript_revision_mutated": False,
            }

    return {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.issue_68_exception_only_domain_review_qa",
        "artifact_id": "issue_68_stress_code_domain_review_qa_v1",
        "status": "INVALID" if errors else ("READY_WITH_EXCEPTIONS" if first_exception else "READY_FOR_FINAL_DOMAIN_REVIEW"),
        "semantic_authority": "PROVISIONAL_UNREVIEWED",
        "review_policy": {
            "mode": "EXCEPTION_ONLY_WITH_CONSOLIDATED_DOMAIN_REVIEW",
            "review_clear_is_accepted": False,
            "automatic_semantic_acceptance": False,
            "present_only_first_material_exception": True,
        },
        "input_inventory": {
            "machine_topic_proposals": len(baseline["topic_proposals"]),
            "authored_topic_results": len(topic_results),
            "concept_candidates": len(baseline["concept_candidates"]),
            "topic_concept_link_proposals": len(
                baseline["topic_concept_link_proposals"]
            ),
            "semantic_package_sha256": sha256(semantic_package_path),
            "canonical_evidence_sha256": sha256(bundle_path),
            "review_result_sha256": sha256(review_result_path),
            "domain_review_decisions_sha256": sha256(domain_review_decisions_path),
            "baseline_rebuilt_without_authoring_decisions": True,
        },
        "inventory_reconciliation": {
            "current_semantic_package_concept_projection": len(
                package["concept_candidates"]
            ),
            "current_semantic_package_link_projection": len(
                package["topic_concept_link_proposals"]
            ),
            "qa_concept_results_after_review_decisions": len(concept_results),
            "qa_link_results_after_review_decisions": len(link_results),
            "explanation": (
                "The QA input rebuilds the original provisional 18/254 inventory "
                "from the same hash-bound generator artifacts before DOMAIN_AUTHORING. "
                "Explicit DOMAIN_REVIEW identity decisions may create additional "
                "Concept and provisional link results without deleting baseline "
                "provenance. The current 15/179 projection is a lossy preview-based "
                "regeneration after split/merge authoring and is not treated as "
                "deletion or review."
            ),
            "semantic_change_inferred": False,
        },
        "summary": {
            "topic_results_total": len(topic_results),
            "topic_review_clear": topic_clear,
            "topic_review_exception": topic_exceptions,
            "topic_domain_review_decisions": len(domain_review_resolutions),
            "concept_domain_review_decisions": len(concept_identity_resolutions),
            "link_domain_review_decisions": len(link_review_resolutions),
            "concept_candidates_total": len(concept_results),
            "concept_clear": concept_clear,
            "concept_identity_exception": len(concept_results) - concept_clear,
            "links_total": len(link_results),
            "link_clear": link_clear,
            "link_exception": len(link_results) - link_clear,
            "selective_transcript_verification_exceptions": len(TRANSCRIPT_EXCEPTIONS),
            "coverage_gaps": sum(len(item["gaps"]) for item in package["coverage"].values()),
            "coverage_overlaps": sum(len(item["overlaps"]) for item in package["coverage"].values()),
        },
        "day_semantic_maps": {
            source_id: {
                "topic_count": len(
                    [item for item in topic_results if item["source_id"] == source_id]
                ),
                "coherence_status": (
                    "REVIEW_EXCEPTION_PRESENT"
                    if any(
                        item["source_id"] == source_id
                        and item["classification"] == "REVIEW_EXCEPTION"
                        for item in topic_results
                    )
                    else "REVIEW_CLEAR"
                ),
                "repeated_titles": sorted(
                    {
                        item["title"]
                        for item in topic_results
                        if item["source_id"] == source_id
                        and sum(
                            candidate["source_id"] == source_id
                            and candidate["title"] == item["title"]
                            for candidate in topic_results
                        )
                        > 1
                    }
                ),
                "topics": [
                    {
                        "topic_id": item["topic_id"],
                        "title": item["title"],
                        "start_time": item["start_time"],
                        "end_time": item["end_time"],
                        "classification": item["classification"],
                    }
                    for item in topic_results
                    if item["source_id"] == source_id
                ],
            }
            for source_id in SOURCE_ORDER
        },
        "topic_results": topic_results,
        "domain_review_resolutions": domain_review_resolutions,
        "rejected_concept_resolutions": [
            item
            for item in concept_identity_resolutions
            if item["outcome"] == "REJECT"
        ],
        "link_review_resolutions": link_review_resolutions,
        "concept_results": concept_results,
        "link_results": link_results,
        "selective_transcript_verification_exceptions": transcript_exception_results,
        "coverage": package["coverage"],
        "first_material_exception": first_exception,
        "safety": {
            "day_1_unchanged": package["day_1"]["status"] == "PRESERVED_ACCEPTED_HUMAN_REVIEWED",
            "all_reviewed_outputs_remain_provisional": True,
            "transcript_revision_mutated": False,
            "concept_identity_invented": False,
            "accepted_obsidian_export_created": False,
            "dataset_d_or_e_accessed": False,
            "gold_modified": False,
        },
        "errors": errors,
    }


def write_review_markdown(path: Path, qa: dict[str, Any]) -> None:
    summary = qa["summary"]
    first = qa["first_material_exception"]
    text = f"""# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **{qa['input_inventory']['machine_topic_proposals']}**
- Resulting authored semantic units: **{summary['topic_results_total']}**
- Topic `REVIEW_CLEAR`: **{summary['topic_review_clear']}**
- Topic `REVIEW_EXCEPTION`: **{summary['topic_review_exception']}**
- Concept candidates after review decisions: **{summary['concept_candidates_total']}** (baseline: **{qa['input_inventory']['concept_candidates']}**)
- Concept identity exceptions: **{summary['concept_identity_exception']}**
- Topic→Concept QA results after review decisions: **{summary['links_total']}** (baseline: **{qa['input_inventory']['topic_concept_link_proposals']}**)
- Link exceptions: **{summary['link_exception']}**
- Selective transcript-verification exceptions: **{summary['selective_transcript_verification_exceptions']}**
- Coverage gaps / overlaps: **{summary['coverage_gaps']} / {summary['coverage_overlaps']}**

The full deterministic classification and Day 2–4 semantic maps are stored in
`domain_review_qa.json`. In accordance with the exception-only UX, this human
packet exposes only the first unresolved material exception.
"""
    if first is None:
        text += """
## Final consolidated DOMAIN_REVIEW

No material exception remains. Proposed decision: `DOMAIN_REVIEW_ACCEPT` or
`DOMAIN_REVIEW_REJECT`.
"""
    elif first["classification"] == "REVIEW_EXCEPTION":
        exception = first["exception"]
        preview = first["evidence_preview"]
        text += f"""
## First material exception

- Source: `{first['source_id']}`
- Topic: `{first['topic_id']}`
- Time: `{first['start_time']}` — `{first['end_time']}`
- Words: `{first['start_word_id']}` — `{first['end_word_id']}`
- Current title: **{first['title']}**
- Classification: `REVIEW_EXCEPTION`
- Taxonomy: {', '.join(exception['taxonomy'])}
- Confidence: `{exception['confidence']}`

### Exact problem

{exception['problem']}

### Exact evidence preview

- Beginning: {preview['beginning']['text']}
- Middle: {preview['middle']['text']}
- End: {preview['end']['text']}

### Recommended correction

```json
{json.dumps(exception['recommended_correction'], ensure_ascii=False, indent=2, sort_keys=True)}
```

Alternative: {exception['alternative']}

### Human decision required

Choose one bounded outcome for this exception. No other exception is presented
until this decision is persisted and the affected neighborhood is rebuilt and
re-QA'd.
"""
    elif first["classification"] == "IDENTITY_EXCEPTION":
        exception = first["exception"]
        text += f"""
## First material exception — Concept identity

- Concept candidate: `{first['candidate_concept_id']}`
- Proposed label: **{first['proposed_canonical_label']}**
- Source terms: {', '.join(first['source_terms'])}
- Exact evidence references: **{first['evidence_reference_count']}**
- Classification: `IDENTITY_EXCEPTION`

### Exact problem

{exception['problem']}

### Recommended review

{exception['recommendation']}

### Human decision required

Choose one bounded Concept-identity outcome. No later exception is presented
until this decision is persisted and the affected Topic→Concept links are
rebuilt and re-QA'd.
"""
    else:
        exception = first["exception"]
        text += f"""
## First material exception — Topic→Concept link

- Link: `{first['link_id']}`
- Topic: `{first['input_topic_reference']}`
- Concept candidate: `{first['candidate_concept_reference']}`
- Source: `{first['source_id']}`
- Classification: `LINK_EXCEPTION`

### Exact problem

{exception['problem']}

### Recommended review

{exception['recommended_correction']}

### Human decision required

Accept, remap, reject, or defer this exact link. No later exception is
presented until this decision is persisted and the affected neighborhood is
re-QA'd.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--review-result", type=Path, required=True)
    parser.add_argument("--semantic-package", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--domain-review-decisions", type=Path)
    args = parser.parse_args()

    repository = args.repository.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    decision_path = (
        args.domain_review_decisions.resolve()
        if args.domain_review_decisions
        else output / "domain_review_decisions.json"
    )
    qa = build_qa(
        repository,
        args.project.resolve(),
        args.review_result.resolve(),
        args.semantic_package.resolve(),
        decision_path,
    )
    qa_path = output / "domain_review_qa.json"
    review_path = output / "DOMAIN_REVIEW.md"
    write_json(qa_path, qa)
    write_review_markdown(review_path, qa)
    write_json(
        output / "manifest.json",
        {
            "schema_version": "1.0.0",
            "artifact_type": "seminartext.issue_68_domain_review_manifest",
            "semantic_authority": qa["semantic_authority"],
            "qa_status": qa["status"],
            "summary": qa["summary"],
            "files": {
                "domain_review_decisions.json": sha256(decision_path),
                "domain_review_qa.json": sha256(qa_path),
                "DOMAIN_REVIEW.md": sha256(review_path),
            },
        },
    )
    return 1 if qa["status"] == "INVALID" else 0


if __name__ == "__main__":
    raise SystemExit(main())
