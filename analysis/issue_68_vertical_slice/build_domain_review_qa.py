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
        "taxonomy": ["OVER-MERGE", "TRANSITION_SPLIT", "PROCEDURAL_FRAGMENTATION"],
        "problem": (
            "The resource-focused discussion ends before an extended brain-gym "
            "and pretest recap. The current range combines those different "
            "discourse functions under one title."
        ),
        "recommended_correction": {
            "action": "SPLIT_REALIGN",
            "semantic_part": {
                "preserve_title": True,
                "start_word_id": "transcript_revision_video_004_r1:word:009738",
                "end_word_id": "transcript_revision_video_004_r1:word:010256",
            },
            "separate_structure_part": {
                "title": "Гимнастика и повторение претестов перед вопросами",
                "start_word_id": "transcript_revision_video_004_r1:word:010257",
                "end_word_id": "transcript_revision_video_004_r1:word:010431",
                "proposed_role": "SEMINAR_STRUCTURE",
            },
        },
        "alternative": "Exclude the exercise recap from Canonical Knowledge.",
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
    "nervous_system": r"(?:нервн\w*\s+(?:систем|сет)|нейронн\w*\s+сет)",
    "adaptation": r"адаптац|адаптив",
    "brain": r"мозг|полушар",
    "meridians": r"меридиан",
    "eye_movement": r"дпдг|движени\w*\s+глаз|глазодвиг",
    "consciousness": r"уровн\w*\s+(?:созн|осознав|осознан)",
    "subconscious": r"подсозн",
    "memory": r"памят|воспомин|запомин",
    "trauma": r"травм",
    "psychosomatics": r"психосомат",
    "life_goals": r"жизненн\w*\s+цел|цел\w*\s+жизн",
    "self_regulation": r"саморегуляц|самовосстанов|управлен\w*\s+стресс",
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
        if decision.get("action") != "SPLIT_REALIGN":
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
        if len(semantic_results) != 1 or semantic_results[0].get("topic_id") != target_id:
            errors.append(f"DOMAIN_REVIEW must preserve one semantic target identity for {target_id}")
            continue

        semantic = semantic_results[0]
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

        resolved.add(target_id)
        resolutions.append(
            {
                "decision_id": decision_id,
                "target_topic_id": target_id,
                "authority": decision["authority"],
                "review_gate": "DOMAIN_REVIEW",
                "status": "DECIDED",
                "action": decision["action"],
                "rationale": decision["rationale"],
                "rejected_alternative": decision["rejected_alternative"],
                "results": resolved_results,
                "neighborhood_qa": neighborhood_checks,
                "package_semantic_promotion": False,
            }
        )

    return units, resolutions, resolved


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
                "title_content_correspondence": "REVIEW_REQUIRED" if exception and "MALFORMED_TITLE" in exception["taxonomy"] else "PASS",
                "left_boundary": "REVIEW_REQUIRED" if left_boundary_requires_review else "PASS",
                "right_boundary": "REVIEW_REQUIRED" if right_boundary_requires_review else "PASS",
                "semantic_coherence": "REVIEW_REQUIRED" if exception else "PASS",
                "neighbor_relationship": "REVIEW_REQUIRED" if exception else "PASS",
                "provenance": "PASS",
                "transcript_assurance": "MACHINE_UNVERIFIED_EXPLICIT",
            },
            "protected_pattern": VALID_SHORT_TOPICS.get(unit["topic_id"]),
        }
        if exception:
            result["exception"] = {**exception, "human_decision_required": True}
        if unit["topic_id"] in resolved_topic_ids:
            result["domain_review_resolution"] = next(
                item
                for item in domain_review_resolutions
                if item["target_topic_id"] == unit["topic_id"]
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

    concept_results = []
    for candidate in baseline["concept_candidates"]:
        candidate_id = candidate["candidate_concept_id"]
        exception = CONCEPT_EXCEPTIONS.get(candidate_id)
        concept_results.append(
            {
                "candidate_concept_id": candidate_id,
                "proposed_canonical_label": candidate["proposed_canonical_label"],
                "source_terms": candidate["source_terms"],
                "evidence_reference_count": len(candidate["evidence_references"]),
                "classification": "IDENTITY_EXCEPTION" if exception else "CLEAR_FOR_HUMAN_BATCH_REVIEW",
                "exception": ({**exception, "human_decision_required": True} if exception else None),
                "semantic_status": "PROVISIONAL",
            }
        )

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

    link_results = []
    for link in baseline["topic_concept_link_proposals"]:
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

    topic_clear = sum(item["classification"] == "REVIEW_CLEAR" for item in topic_results)
    topic_exceptions = len(topic_results) - topic_clear
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
            "concept_candidates": len(concept_results),
            "topic_concept_link_proposals": len(link_results),
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
            "qa_concept_input": len(concept_results),
            "qa_link_input": len(link_results),
            "explanation": (
                "The QA input rebuilds the original provisional 18/254 inventory "
                "from the same hash-bound generator artifacts before DOMAIN_AUTHORING. "
                "The current 15/179 projection is a lossy preview-based regeneration "
                "after split/merge authoring and is not treated as deletion or review."
            ),
            "semantic_change_inferred": False,
        },
        "summary": {
            "topic_results_total": len(topic_results),
            "topic_review_clear": topic_clear,
            "topic_review_exception": topic_exceptions,
            "topic_domain_review_decisions": len(domain_review_resolutions),
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
        "concept_results": concept_results,
        "link_results": link_results,
        "selective_transcript_verification_exceptions": TRANSCRIPT_EXCEPTIONS,
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
- Concept candidates: **{summary['concept_candidates_total']}**
- Concept identity exceptions: **{summary['concept_identity_exception']}**
- Topic→Concept input links: **{summary['links_total']}**
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
    else:
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
