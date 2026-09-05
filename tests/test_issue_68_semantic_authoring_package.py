from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "analysis/issue_68_vertical_slice/build_semantic_authoring_package.py"
SPEC = importlib.util.spec_from_file_location("issue_68_semantic_package", BUILDER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def make_fixture(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    words = []
    revisions = []
    for number in range(1, 5):
        source = f"source_video_{number:03d}"
        revision = f"transcript_revision_video_{number:03d}_r1"
        revisions.append(
            {
                "id": revision,
                "source_id": source,
                "transcript_provenance": {
                    "kind": "machine_generated",
                    "verification_state": "machine_unverified",
                },
            }
        )
        for sequence in range(12):
            words.append(
                {
                    "id": f"{revision}:word:{sequence:06d}",
                    "source_id": source,
                    "transcript_revision_id": revision,
                    "sequence": sequence,
                    "text": "Стресс" if sequence == 2 else f"слово{sequence}",
                    "start_seconds": float(sequence),
                    "end_seconds": float(sequence) + 0.8,
                    "alignment_status": "aligned",
                }
            )
    bundle = {
        "artifact_id": "canonical_fixture",
        "transcript_revisions": revisions,
        "words": words,
    }
    bundle_path = project / "evidence/canonical_bundle.json"
    write_json(bundle_path, bundle)
    bundle_hash = MODULE.sha256(bundle_path)
    review = {
        "artifact_id": "review_day1",
        "application_status": "APPLIED",
        "canonical_evidence": {"sha256": bundle_hash},
        "semantic_knowledge": [
            {
                "id": "day1_topic",
                "source_id": "source_video_001",
                "title": "Стресс и адаптация",
                "summary": "",
                "word_start_id": "transcript_revision_video_001_r1:word:000000",
                "word_end_id": "transcript_revision_video_001_r1:word:000011",
            }
        ],
    }
    review_path = project / "review.json"
    write_json(review_path, review)
    for number in MODULE.SOURCE_NUMBERS:
        registry = f"video_{number:03d}"
        topic = {
            "engine": "ollama",
            "model": "gemma3:4b",
            "detail": "auto",
            "topics": [
                {
                    "start_seconds": 0.0,
                    "end_seconds": 6.0,
                    "title": "Стресс",
                    "summary": "Обсуждение стресса.",
                    "start_segment_id": 1,
                    "qa_status": "ok",
                    "qa_attempt": "2stage",
                },
                {
                    "start_seconds": 6.0,
                    "end_seconds": 12.0,
                    "title": "Тема требует ручной проверки",
                    "summary": "",
                    "start_segment_id": 7,
                    "qa_status": "fallback",
                    "qa_attempt": "safe_fallback",
                },
            ],
        }
        qa = {
            "engine": "ollama",
            "model": "gemma3:4b",
            "detail": "auto",
            "windows": [{"start_segment_id": 1}],
        }
        write_json(project / f"transcript/{registry}/topics.json", topic)
        write_json(project / f"transcript/{registry}/topics_qa.json", qa)
    return project, review_path


def test_package_is_complete_provisional_and_word_contiguous(tmp_path: Path) -> None:
    project, review = make_fixture(tmp_path)
    package, batches = MODULE.build_package(project, review)

    assert package["status"] == "READY_FOR_DOMAIN_AUTHORING"
    assert len(package["topic_proposals"]) == 6
    assert all(item["review_status"] == "UNREVIEWED" for item in package["topic_proposals"])
    assert all(item["semantic_status"] == "PROVISIONAL" for item in package["concept_candidates"])
    assert all(item["status"] == "PROVISIONAL" for item in package["topic_concept_link_proposals"])
    assert package["generator"]["not_generated_by"] == "bge_m3_local_peak_v1"
    assert package["safety"]["day_1_reauthored"] is False
    assert len(batches["topic_batches"]) == 6
    for coverage in package["coverage"].values():
        assert coverage["covered_word_count"] == coverage["canonical_word_count"]
        assert coverage["gaps"] == []
        assert coverage["overlaps"] == []


def test_unexpected_generator_fails_closed(tmp_path: Path) -> None:
    project, review = make_fixture(tmp_path)
    path = project / "transcript/video_003/topics.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["model"] = "unauthorized-model"
    write_json(path, document)

    package, _ = MODULE.build_package(project, review)

    assert package["status"] == "INVALID"
    assert any("unexpected generator identity" in item for item in package["errors"])


def test_rename_authoring_decision_preserves_word_range_and_stays_provisional(tmp_path: Path) -> None:
    project, review = make_fixture(tmp_path)
    decision_path = project / "authoring_decisions.json"
    write_json(
        decision_path,
        {
            "artifact_id": "decisions_fixture",
            "semantic_gate": "DOMAIN_AUTHORING",
            "decisions": [
                {
                    "decision_id": "decision_1",
                    "proposal_id": "issue_68_video_002_topic_proposal_001",
                    "source_id": "source_video_002",
                    "action": "RENAME",
                    "new_title": "Новое название",
                    "boundary_action": "PRESERVE",
                    "start_word_id": "transcript_revision_video_002_r1:word:000000",
                    "end_word_id": "transcript_revision_video_002_r1:word:000005",
                    "authority": "PRODUCT_OWNER_DIRECT_DOMAIN_AUTHORING",
                }
            ],
        },
    )

    package, batches = MODULE.build_package(project, review, decision_path)
    proposal = package["topic_proposals"][0]

    assert package["status"] == "READY_FOR_DOMAIN_AUTHORING"
    assert proposal["proposed_title"] == "Стресс"
    assert proposal["authored_title"] == "Новое название"
    assert proposal["authoring_status"] == "COMPLETED"
    assert proposal["semantic_status"] == "PROVISIONAL"
    assert proposal["domain_review_status"] == "REVIEW_REQUIRED"
    assert proposal["start_word_sequence"] == 0
    assert proposal["end_word_sequence"] == 5
    assert batches["topic_batches"][0]["authoring_status"] == "COMPLETED"
    assert package["domain_authoring_progress"] == {
        "completed": 1,
        "pending": 5,
        "total": 6,
        "next_proposal_id": "issue_68_video_002_topic_proposal_002",
    }


def test_realign_rename_moves_shared_boundary_without_gap_or_acceptance(tmp_path: Path) -> None:
    project, review = make_fixture(tmp_path)
    decision_path = project / "authoring_decisions.json"
    write_json(
        decision_path,
        {
            "artifact_id": "decisions_fixture",
            "semantic_gate": "DOMAIN_AUTHORING",
            "decisions": [
                {
                    "decision_id": "decision_realign",
                    "proposal_id": "issue_68_video_002_topic_proposal_001",
                    "next_proposal_id": "issue_68_video_002_topic_proposal_002",
                    "source_id": "source_video_002",
                    "action": "REALIGN_RENAME",
                    "new_title": "Новое название",
                    "boundary_action": "REALIGN_RIGHT",
                    "start_word_id": "transcript_revision_video_002_r1:word:000000",
                    "end_word_id": "transcript_revision_video_002_r1:word:000003",
                    "end_word_anchor_time": "00:00:03.000",
                    "next_start_word_id": "transcript_revision_video_002_r1:word:000004",
                    "next_start_word_anchor_time": "00:00:04.000",
                    "previous_next_start_word_id": "transcript_revision_video_002_r1:word:000006",
                    "authority": "PRODUCT_OWNER_DIRECT_DOMAIN_AUTHORING",
                }
            ],
        },
    )

    package, _ = MODULE.build_package(project, review, decision_path)
    first, second = package["topic_proposals"][:2]

    assert package["status"] == "READY_FOR_DOMAIN_AUTHORING"
    assert first["end_word_sequence"] == 3
    assert second["start_word_sequence"] == 4
    assert first["authored_title"] == "Новое название"
    assert first["semantic_status"] == "PROVISIONAL"
    assert first["domain_review_status"] == "REVIEW_REQUIRED"
    assert second["left_boundary_authoring_decision"]["decision_id"] == "decision_realign"
    assert package["coverage"]["source_video_002"]["gaps"] == []
    assert package["coverage"]["source_video_002"]["overlaps"] == []


def test_split_realign_creates_contiguous_provisional_authored_topics(tmp_path: Path) -> None:
    project, review = make_fixture(tmp_path)
    decision_path = project / "authoring_decisions.json"
    write_json(
        decision_path,
        {
            "artifact_id": "decisions_fixture",
            "semantic_gate": "DOMAIN_AUTHORING",
            "decisions": [
                {
                    "decision_id": "decision_split_realign",
                    "proposal_id": "issue_68_video_002_topic_proposal_001",
                    "next_proposal_id": "issue_68_video_002_topic_proposal_002",
                    "source_id": "source_video_002",
                    "action": "SPLIT_REALIGN",
                    "boundary_action": "REALIGN_RIGHT",
                    "start_word_id": "transcript_revision_video_002_r1:word:000000",
                    "end_word_id": "transcript_revision_video_002_r1:word:000008",
                    "end_word_anchor_time": "00:00:08.000",
                    "next_start_word_id": "transcript_revision_video_002_r1:word:000009",
                    "next_start_word_anchor_time": "00:00:09.000",
                    "previous_next_start_word_id": "transcript_revision_video_002_r1:word:000006",
                    "authority": "PRODUCT_OWNER_DIRECT_DOMAIN_AUTHORING",
                    "split_parts": [
                        {
                            "part_id": "issue_68_video_002_topic_proposal_001a",
                            "part_label": "1A",
                            "title": "Первая часть",
                            "start_word_id": "transcript_revision_video_002_r1:word:000000",
                            "end_word_id": "transcript_revision_video_002_r1:word:000002",
                            "start_word_anchor_time": "00:00:00.000",
                            "end_word_anchor_time": "00:00:02.000",
                        },
                        {
                            "part_id": "issue_68_video_002_topic_proposal_001b",
                            "part_label": "1B",
                            "title": "Вторая часть",
                            "start_word_id": "transcript_revision_video_002_r1:word:000003",
                            "end_word_id": "transcript_revision_video_002_r1:word:000008",
                            "start_word_anchor_time": "00:00:03.000",
                            "end_word_anchor_time": "00:00:08.000",
                        },
                    ],
                }
            ],
        },
    )

    package, _ = MODULE.build_package(project, review, decision_path)
    first, second = package["topic_proposals"][:2]

    assert package["status"] == "READY_FOR_DOMAIN_AUTHORING"
    assert first["end_word_sequence"] == 8
    assert second["start_word_sequence"] == 9
    assert [item["part_label"] for item in first["authored_topics"]] == ["1A", "1B"]
    assert [item["start_word_sequence"] for item in first["authored_topics"]] == [0, 3]
    assert [item["end_word_sequence"] for item in first["authored_topics"]] == [2, 8]
    assert all(
        item["semantic_status"] == "PROVISIONAL"
        and item["domain_review_status"] == "REVIEW_REQUIRED"
        for item in first["authored_topics"]
    )
    assert package["coverage"]["source_video_002"]["gaps"] == []
    assert package["coverage"]["source_video_002"]["overlaps"] == []


def test_committed_real_package_is_complete_and_fail_closed() -> None:
    package_path = (
        ROOT
        / "analysis/issue_68_vertical_slice/semantic_authoring_v1"
        / "semantic_authoring_package.json"
    )
    batches_path = package_path.with_name("review_batches.json")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    batches = json.loads(batches_path.read_text(encoding="utf-8"))

    assert package["status"] == "READY_FOR_DOMAIN_AUTHORING"
    assert package["semantic_authority"] == "PROVISIONAL_UNREVIEWED"
    assert package["day_1"]["status"] == "PRESERVED_ACCEPTED_HUMAN_REVIEWED"
    assert package["day_1"]["topic_count"] == 36
    assert package["errors"] == []
    expected_counts = {
        "source_video_002": 91,
        "source_video_003": 92,
        "source_video_004": 79,
    }
    assert {
        source_id: item["proposal_count"]
        for source_id, item in package["coverage"].items()
    } == expected_counts
    assert len(package["topic_proposals"]) == sum(expected_counts.values())
    assert package["domain_authoring_progress"] == {
        "completed": 12,
        "pending": 250,
        "total": 262,
        "next_proposal_id": "issue_68_video_002_topic_proposal_013",
    }
    assert len({item["proposal_id"] for item in package["topic_proposals"]}) == sum(
        expected_counts.values()
    )
    required = {
        "proposal_id",
        "source_id",
        "start_word_id",
        "end_word_id",
        "start_time",
        "end_time",
        "proposed_title",
        "proposed_summary",
        "review_summary",
        "evidence_preview",
        "boundary_reason",
        "confidence",
        "transcript_assurance",
        "provenance",
        "review_status",
    }
    for proposal in package["topic_proposals"]:
        assert required <= proposal.keys()
        assert proposal["review_status"] == "UNREVIEWED"
        assert len(proposal["review_summary"]) == 2
        assert proposal["transcript_assurance"]["verification_state"] == "machine_unverified"
        assert proposal["semantic_status"] == "PROVISIONAL"
        assert proposal["domain_review_status"] == "REVIEW_REQUIRED"
    first = package["topic_proposals"][0]
    assert first["authored_title"] == "Начало второго дня: переход от теории кинезиологии к практике"
    assert first["authoring_status"] == "COMPLETED"
    assert first["start_word_id"].endswith("word:000000")
    assert first["end_word_id"].endswith("word:000066")
    second = package["topic_proposals"][1]
    third = package["topic_proposals"][2]
    assert second["authored_title"] == "Мануальное мышечное тестирование и реакция мышц на стресс"
    assert second["authoring_status"] == "COMPLETED"
    assert second["start_word_id"].endswith("word:000067")
    assert second["end_word_id"].endswith("word:000169")
    assert third["start_word_id"].endswith("word:000170")
    assert third["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_002"
    assert third["end_word_id"].endswith("word:001218")
    assert third["authoring_status"] == "COMPLETED"
    assert [item["part_label"] for item in third["authored_topics"]] == [
        "3A",
        "3B",
        "3C",
        "3D",
    ]
    assert [item["authored_title"] for item in third["authored_topics"]] == [
        "Претесты и выбор передней порции дельтовидной мышцы",
        "Очное и дистанционное тестирование: получение индивидуальной информации",
        "Передняя порция дельтовидной мышцы: анатомия и техника тестирования",
        "Дыхание, вода и передача сигналов нервной системой",
    ]
    assert all(
        item["semantic_status"] == "PROVISIONAL"
        and item["domain_review_status"] == "REVIEW_REQUIRED"
        for item in third["authored_topics"]
    )
    fourth = package["topic_proposals"][3]
    assert fourth["start_word_id"].endswith("word:001219")
    assert fourth["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_003"
    assert fourth["end_word_id"].endswith("word:001712")
    assert fourth["authored_title"] == (
        "Разбор домашнего мышечного тестирования: различение сильного и слабого ответа"
    )
    assert fourth["authoring_status"] == "COMPLETED"
    fifth = package["topic_proposals"][4]
    assert fifth["start_word_id"].endswith("word:001713")
    assert fifth["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_004"
    assert fifth["end_word_id"].endswith("word:001920")
    assert fifth["authored_title"] == (
        "Сильный и слабый мышечный ответ как индикатор стресса"
    )
    assert fifth["authoring_status"] == "COMPLETED"
    sixth = package["topic_proposals"][5]
    assert sixth["start_word_id"].endswith("word:001921")
    assert sixth["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_005"
    assert sixth["end_word_id"].endswith("word:002201")
    assert sixth["authored_title"] == (
        "Пример коррекции стресса и принцип мышечного ответа в кинезиологии"
    )
    assert sixth["authoring_status"] == "COMPLETED"
    seventh = package["topic_proposals"][6]
    assert seventh["start_word_id"].endswith("word:002202")
    assert seventh["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_006"
    assert seventh["end_word_id"].endswith("word:002586")
    assert seventh["authored_title"] == (
        "Претест «очищение»: восстановление нормотонуса мышцы"
    )
    assert seventh["authoring_status"] == "COMPLETED"
    eighth = package["topic_proposals"][7]
    assert eighth["start_word_id"].endswith("word:002587")
    assert eighth["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_007"
    assert eighth["end_word_id"].endswith("word:003418")
    assert eighth["authored_title"] == (
        "Претест «перегрузка» и коррекция «переключение»"
    )
    assert eighth["authoring_status"] == "COMPLETED"
    ninth = package["topic_proposals"][8]
    assert ninth["start_word_id"].endswith("word:003419")
    assert ninth["left_boundary_authoring_decision"]["decision_id"] == "issue_68_domain_authoring_topic_008"
    assert ninth["end_word_id"].endswith("word:003446")
    assert ninth["authored_title"] == "Претест «блокировка»: состояние угрозы"
    assert ninth["authoring_status"] == "COMPLETED"
    tenth = package["topic_proposals"][9]
    assert tenth["start_word_id"].endswith("word:003447")
    assert tenth["end_word_id"].endswith("word:003556")
    assert tenth["authored_title"] == (
        "Претест «блокировка»: диагностика и коррекция перенапряжения"
    )
    assert tenth["authoring_status"] == "COMPLETED"
    eleventh = package["topic_proposals"][10]
    assert eleventh["start_word_id"].endswith("word:003557")
    assert eleventh["left_boundary_authoring_decision"]["decision_id"] == (
        "issue_68_domain_authoring_topic_010"
    )
    assert eleventh["end_word_id"].endswith("word:003928")
    assert eleventh["authored_title"] == (
        "Баланс поляризации: коррекция дыханием через ноздри"
    )
    assert eleventh["authoring_status"] == "COMPLETED"
    twelfth = package["topic_proposals"][11]
    assert twelfth["start_word_id"].endswith("word:003929")
    assert twelfth["left_boundary_authoring_decision"]["decision_id"] == (
        "issue_68_domain_authoring_topic_011"
    )
    assert twelfth["end_word_id"].endswith("word:004430")
    assert twelfth["authored_title"] == (
        "Коррекция поляризации через меридианы и завершение претестов"
    )
    assert twelfth["authoring_status"] == "COMPLETED"
    thirteenth = package["topic_proposals"][12]
    assert thirteenth["start_word_id"].endswith("word:004431")
    assert thirteenth["left_boundary_authoring_decision"]["decision_id"] == (
        "issue_68_domain_authoring_topic_012"
    )
    for coverage in package["coverage"].values():
        assert coverage["covered_word_count"] == coverage["canonical_word_count"]
        assert coverage["gaps"] == []
        assert coverage["overlaps"] == []
    assert package["concept_candidates"]
    assert package["topic_concept_link_proposals"]
    assert all(
        concept["semantic_status"] == "PROVISIONAL"
        and concept["review_status"] == "UNREVIEWED"
        for concept in package["concept_candidates"]
    )
    assert all(
        link["status"] == "PROVISIONAL" and link["review_status"] == "UNREVIEWED"
        for link in package["topic_concept_link_proposals"]
    )
    assert max(len(batch["proposal_references"]) for batch in batches["topic_batches"]) <= 3
    assert package["safety"] == {
        "accepted_obsidian_export_created": False,
        "all_concepts_provisional": True,
        "all_links_provisional": True,
        "all_new_topics_unreviewed": True,
        "dataset_d_or_e_accessed": False,
        "day_1_reauthored": False,
        "gold_created_or_modified": False,
        "transcript_revision_mutated": False,
    }
