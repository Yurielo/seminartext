#!/usr/bin/env python3
"""Export the accepted bounded Golden Slice as a derived Obsidian vault."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPORT_SCHEMA_VERSION = "1.0.0"
EXPECTED_SLICE_ID = "golden_slice_stress_code_video_001_v1"
EXPECTED_SLICE_SHA256 = "177d030a6ac3e3dc0a28d655db0f12321e09caba8eff494c078aeb828339d4d6"
EXPECTED_COUNTS = {"topics": 3, "concepts": 7, "evidence": 10}
CANONICAL_REPO_PATH = "analysis/word_timeline_mvp/canonical_evidence_bundle.json"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def frontmatter(metadata: dict[str, Any]) -> str:
    """Emit a JSON mapping, which is also a strict YAML 1.2 mapping."""

    return "---\n" + json.dumps(
        metadata, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n---\n"


def note(metadata: dict[str, Any], title: str, body: str) -> bytes:
    text = frontmatter(metadata) + f"\n# {title}\n\n{body.rstrip()}\n"
    return text.encode("utf-8")


def wikilink(folder: str, stable_id: str, label: str) -> str:
    if any(character in label for character in "[]|"):
        raise ValueError(f"unsupported wikilink label: {label!r}")
    return f"[[{folder}/{stable_id}|{label}]]"


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def quote_block(value: str) -> str:
    return "\n".join(">" if not line else f"> {line}" for line in value.splitlines())


def human_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"


def base_metadata(
    stable_id: str,
    note_type: str,
    slice_document: dict[str, Any],
    slice_sha256: str,
) -> dict[str, Any]:
    return {
        "derived_from_artifact_id": slice_document["artifact_id"],
        "derived_from_artifact_sha256": slice_sha256,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "generated_by": "seminartext_obsidian_bounded_exporter",
        "lifecycle_status": "derived_view",
        "note_type": note_type,
        "stable_id": stable_id,
    }


def load_and_validate_inputs(
    slice_path: Path, canonical_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    slice_sha = sha256_file(slice_path)
    if slice_sha != EXPECTED_SLICE_SHA256:
        raise ValueError(f"Golden Slice SHA-256 mismatch: {slice_sha}")
    document = json.loads(slice_path.read_text(encoding="utf-8"))
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))

    if document.get("artifact_id") != EXPECTED_SLICE_ID:
        raise ValueError("unexpected Golden Slice artifact")
    if document.get("artifact_type") != "seminartext.golden_knowledge_slice":
        raise ValueError("unexpected Golden Slice type")
    if document.get("product_review") != {"required": True, "status": "pending"}:
        raise ValueError("Golden Slice Product Review boundary changed")
    for collection, expected in EXPECTED_COUNTS.items():
        if len(document.get(collection, [])) != expected:
            raise ValueError(f"bounded {collection} count changed")

    canonical_spec = document["canonical_evidence"]
    if canonical_spec["path"] != CANONICAL_REPO_PATH:
        raise ValueError("canonical repo path changed")
    canonical_sha = sha256_file(canonical_path)
    if canonical_sha != canonical_spec["sha256"]:
        raise ValueError(f"Canonical Evidence SHA-256 mismatch: {canonical_sha}")
    if canonical.get("artifact_id") != canonical_spec["artifact_id"]:
        raise ValueError("canonical artifact identity changed")

    words = {item["id"]: item for item in canonical["words"]}
    sources = {item["id"]: item for item in canonical["sources"]}
    transcripts = {
        item["id"]: item for item in canonical["transcript_revisions"]
    }
    evidence = {item["id"]: item for item in document["evidence"]}
    topics = {item["id"]: item for item in document["topics"]}
    concepts = {item["id"]: item for item in document["concepts"]}

    for item in document["evidence"]:
        first = words.get(item["canonical_word_start_id"])
        last = words.get(item["canonical_word_end_id"])
        source = sources.get(item["canonical_source_id"])
        transcript = transcripts.get(item["canonical_transcript_revision_id"])
        if None in (first, last, source, transcript):
            raise ValueError(f"{item['id']}: orphan canonical reference")
        assert first is not None and last is not None and transcript is not None
        selected = canonical["words"][first["sequence"] : last["sequence"] + 1]
        expected_quote = transcript["canonical_text"][
            first["char_start"] : last["char_end"]
        ]
        if item["quote"] != expected_quote:
            raise ValueError(f"{item['id']}: quote diverged from canonical text")
        aligned = [word for word in selected if word["alignment_status"] == "aligned"]
        expected_locator = {
            "end_seconds": aligned[-1]["end_seconds"],
            "start_seconds": aligned[0]["start_seconds"],
            "type": "time_interval",
        }
        if item["locator"] != expected_locator:
            raise ValueError(f"{item['id']}: canonical locator mismatch")
        expected_unaligned = [
            word["id"] for word in selected if word["alignment_status"] == "unaligned"
        ]
        if item["unaligned_word_ids"] != expected_unaligned:
            raise ValueError(f"{item['id']}: unaligned limitations changed")

    for topic in topics.values():
        if any(item not in evidence for item in topic["evidence_ids"]):
            raise ValueError(f"{topic['id']}: orphan Evidence")
        if any(item not in concepts for item in topic["concept_ids"]):
            raise ValueError(f"{topic['id']}: orphan Concept")
    for concept in concepts.values():
        if concept["derivation_status"] != "provisional_manual_curation":
            raise ValueError(f"{concept['id']}: provisional status changed")
        if concept["review_status"] != "product_review_required":
            raise ValueError(f"{concept['id']}: Product Review status changed")
        if any(item not in evidence for item in concept["evidence_ids"]):
            raise ValueError(f"{concept['id']}: orphan Evidence")
        if any(item not in topics for item in concept["topic_ids"]):
            raise ValueError(f"{concept['id']}: orphan Topic")
        for topic_id in concept["topic_ids"]:
            if concept["id"] not in topics[topic_id]["concept_ids"]:
                raise ValueError(f"{concept['id']}: asymmetric Topic relation")

    return document, canonical, slice_sha


def build_vault(
    slice_path: Path, canonical_path: Path
) -> tuple[dict[str, bytes], dict[str, Any]]:
    document, canonical, slice_sha = load_and_validate_inputs(
        slice_path.resolve(), canonical_path.resolve()
    )
    files: dict[str, bytes] = {}
    seminar = document["seminar"]
    source = document["sources"][0]
    topics = {item["id"]: item for item in document["topics"]}
    concepts = {item["id"]: item for item in document["concepts"]}
    evidence = {item["id"]: item for item in document["evidence"]}

    def metadata(stable_id: str, note_type: str) -> dict[str, Any]:
        return base_metadata(stable_id, note_type, document, slice_sha)

    start_meta = metadata("view_start_here", "index")
    start_meta["review_status"] = "product_review_required"
    files["00_START_HERE.md"] = note(
        start_meta,
        "SeminarText — Golden Slice",
        "This vault is a disposable, rebuildable derived view. Canonical Evidence "
        "remains the source of truth.\n\n"
        "## Start\n\n"
        + bullets(
            [
                wikilink("Seminars", seminar["id"], seminar["title"]),
                wikilink("Sources", source["id"], source["title"]),
                wikilink("_meta", "canonical_evidence_reference", "Canonical Evidence reference"),
                "[[PRODUCT_OWNER_REVIEW_GUIDE|Product Owner review guide]]",
            ]
        )
        + "\n\n## Scope\n\n"
        "Only the accepted bounded Golden Slice from Issue #44 is rendered: "
        "3 Topics, 7 provisional Concepts and 10 Evidence items. This is not a "
        "full-seminar export and it is not an editable canonical database.",
    )

    review_meta = metadata("view_product_owner_review_guide", "review_guide")
    review_meta["review_status"] = "product_review_required"
    files["PRODUCT_OWNER_REVIEW_GUIDE.md"] = note(
        review_meta,
        "Product Owner Review Guide",
        "Product Review has **not** been completed. Concepts retain "
        "`provisional_manual_curation` and `product_review_required`.\n\n"
        "## Review path\n\n"
        "1. Open [[Seminars/seminar_stress_code|Стресс код]].\n"
        "2. Follow any Topic and judge whether its title and summary are useful.\n"
        "3. Follow a Concept and confirm that its provisional status is obvious.\n"
        "4. From `Выживаемость в меняющейся среде`, inspect use in two Topics.\n"
        "5. Follow an Evidence note and read the short canonical excerpt.\n"
        "6. Confirm source ID, exact start/end, Word IDs and timing limitation.\n"
        "7. Use normal Obsidian backlinks to return through the path.\n\n"
        "## Product decisions requested\n\n"
        "- Is the Seminar → Topic → Concept → Evidence navigation natural?\n"
        "- Are names and note granularity useful?\n"
        "- Are provenance and time locators understandable without excess noise?\n"
        "- Which provisional Concepts should be accepted, renamed, split, merged, "
        "rejected or deferred?\n"
        "- Should this bounded export contract proceed to the minimum next step?\n\n"
        "Do not edit these generated files as canonical truth; rebuild them from "
        "the accepted JSON inputs.",
    )

    canonical_meta = metadata("view_canonical_evidence_reference", "canonical_reference")
    canonical_meta.update(
        {
            "canonical_artifact_id": canonical["artifact_id"],
            "canonical_artifact_sha256": document["canonical_evidence"]["sha256"],
            "canonical_evidence_repo_path": CANONICAL_REPO_PATH,
            "canonical_schema_version": canonical["schema_version"],
        }
    )
    files["_meta/canonical_evidence_reference.md"] = note(
        canonical_meta,
        "Canonical Evidence Reference",
        "This note is a pointer, not a copy of canonical data.\n\n"
        f"- Artifact ID: `{canonical['artifact_id']}`\n"
        f"- SHA-256: `{document['canonical_evidence']['sha256']}`\n"
        f"- Repository path: `{CANONICAL_REPO_PATH}`\n"
        "- [Open canonical JSON](../../../word_timeline_mvp/canonical_evidence_bundle.json)\n\n"
        "Evidence notes resolve through canonical Source, TranscriptRevision and "
        "Word IDs. Generated Markdown is always disposable.",
    )

    seminar_meta = metadata(seminar["id"], "seminar")
    seminar_meta.update(
        {
            "canonical_project_id": seminar["canonical_project_id"],
            "review_status": "accepted_bounded_input",
            "source_ids": seminar["source_ids"],
            "topic_ids": seminar["topic_ids"],
        }
    )
    files[f"Seminars/{seminar['id']}.md"] = note(
        seminar_meta,
        seminar["title"],
        "## Bounded prototype\n\n"
        "This card renders only the accepted Golden Slice; it does not represent "
        "the full seminar.\n\n"
        "## Source\n\n"
        + bullets([wikilink("Sources", source["id"], source["title"])])
        + "\n\n## Topics\n\n"
        + bullets(
            [wikilink("Topics", item["id"], item["title"]) for item in document["topics"]]
        ),
    )

    source_meta = metadata(source["id"], "source")
    source_meta.update(
        {
            "canonical_source_id": source["canonical_source_id"],
            "content_sha256": source["content_sha256"],
            "duration_seconds": source["duration_seconds"],
            "media_kind": source["kind"],
            "review_status": "accepted_canonical_identity",
        }
    )
    source_evidence = [
        wikilink("Evidence", item["id"], item["claim"])
        for item in document["evidence"]
    ]
    files[f"Sources/{source['id']}.md"] = note(
        source_meta,
        source["title"],
        f"- Source ID: `{source['canonical_source_id']}`\n"
        f"- Duration: `{human_time(source['duration_seconds'])}` "
        f"(`{source['duration_seconds']}` seconds)\n"
        f"- Content SHA-256: `{source['content_sha256']}`\n"
        f"- Canonical record: {wikilink('_meta', 'canonical_evidence_reference', 'Canonical Evidence')}\n\n"
        "## Evidence in this bounded slice\n\n" + bullets(source_evidence),
    )

    evidence_topics: dict[str, list[dict[str, Any]]] = {item: [] for item in evidence}
    evidence_concepts: dict[str, list[dict[str, Any]]] = {item: [] for item in evidence}
    for item in document["topics"]:
        for evidence_id in item["evidence_ids"]:
            evidence_topics[evidence_id].append(item)
    for item in document["concepts"]:
        for evidence_id in item["evidence_ids"]:
            evidence_concepts[evidence_id].append(item)

    for item in document["topics"]:
        item_meta = metadata(item["id"], "topic")
        item_meta.update(
            {
                "canonical_source_id": item["canonical_source_id"],
                "canonical_transcript_revision_id": item["canonical_transcript_revision_id"],
                "canonical_word_end_id": item["canonical_word_end_id"],
                "canonical_word_start_id": item["canonical_word_start_id"],
                "concept_ids": item["concept_ids"],
                "coverage": item["coverage"],
                "end_seconds": item["locator"]["end_seconds"],
                "evidence_ids": item["evidence_ids"],
                "review_status": item["structure_provenance"]["review_status"],
                "start_seconds": item["locator"]["start_seconds"],
                "structure_origin": item["structure_origin"],
                "timing_status": item["timing_status"],
                "unaligned_word_ids": item["unaligned_word_ids"],
            }
        )
        concept_links = [
            wikilink("Concepts", concept_id, concepts[concept_id]["preferred_label"])
            for concept_id in item["concept_ids"]
        ]
        evidence_links = [
            wikilink("Evidence", evidence_id, evidence[evidence_id]["claim"])
            for evidence_id in item["evidence_ids"]
        ]
        files[f"Topics/{item['id']}.md"] = note(
            item_meta,
            item["title"],
            f"**Review status:** `{item_meta['review_status']}`\n\n"
            f"**Source interval:** `{human_time(item['locator']['start_seconds'])}`–"
            f"`{human_time(item['locator']['end_seconds'])}`\n\n"
            "## Summary\n\n"
            + item["summary"]
            + "\n\nThis derived summary is grounded by the Evidence links below.\n\n"
            "## Concepts\n\n"
            + bullets(concept_links)
            + "\n\n## Evidence provenance\n\n"
            + bullets(evidence_links)
            + "\n\n## Navigation\n\n"
            + wikilink("Seminars", seminar["id"], seminar["title"]),
        )

    for item in document["concepts"]:
        item_meta = metadata(item["id"], "concept")
        item_meta.update(
            {
                "aliases": item["aliases"],
                "derivation_status": item["derivation_status"],
                "evidence_ids": item["evidence_ids"],
                "review_status": item["review_status"],
                "topic_ids": item["topic_ids"],
            }
        )
        topic_links = [
            wikilink("Topics", topic_id, topics[topic_id]["title"])
            for topic_id in item["topic_ids"]
        ]
        evidence_links = [
            wikilink("Evidence", evidence_id, evidence[evidence_id]["claim"])
            for evidence_id in item["evidence_ids"]
        ]
        files[f"Concepts/{item['id']}.md"] = note(
            item_meta,
            item["preferred_label"],
            "**PROVISIONAL — Product Review required.** Display in Obsidian does "
            "not make this an accepted ontology fact.\n\n"
            "## Evidence-grounded description\n\n"
            + item["description"]
            + "\n\n## Identity rationale\n\n"
            + item["identity_rationale"]
            + "\n\n## Used in Topics\n\n"
            + bullets(topic_links)
            + "\n\n## Evidence provenance\n\n"
            + bullets(evidence_links),
        )

    for item in document["evidence"]:
        locator = item["locator"]
        item_meta = metadata(item["id"], "evidence")
        item_meta.update(
            {
                "canonical_source_id": item["canonical_source_id"],
                "canonical_transcript_revision_id": item["canonical_transcript_revision_id"],
                "canonical_word_end_id": item["canonical_word_end_id"],
                "canonical_word_start_id": item["canonical_word_start_id"],
                "claim_status": "evidence_grounded_product_review_required",
                "end_seconds": locator["end_seconds"],
                "review_status": "product_review_required",
                "start_seconds": locator["start_seconds"],
                "timing_status": item["timing_status"],
                "unaligned_word_ids": item["unaligned_word_ids"],
            }
        )
        limitations = (
            "No unaligned Words in this evidence span."
            if not item["unaligned_word_ids"]
            else "The following Words have no native timing: "
            + ", ".join(f"`{word_id}`" for word_id in item["unaligned_word_ids"])
            + ". The displayed interval is the aligned envelope; no synthetic timing was created."
        )
        topic_links = [
            wikilink("Topics", topic["id"], topic["title"])
            for topic in evidence_topics[item["id"]]
        ]
        concept_links = [
            wikilink("Concepts", concept["id"], concept["preferred_label"])
            for concept in evidence_concepts[item["id"]]
        ]
        files[f"Evidence/{item['id']}.md"] = note(
            item_meta,
            item["claim"],
            "## Claim from accepted Golden Slice\n\n"
            + item["claim"]
            + "\n\n## Canonical excerpt\n\n"
            + quote_block(item["quote"])
            + "\n\n## Exact source locator\n\n"
            f"- Source: {wikilink('Sources', source['id'], source['title'])}\n"
            f"- Source ID: `{item['canonical_source_id']}`\n"
            f"- Time: `{human_time(locator['start_seconds'])}`–"
            f"`{human_time(locator['end_seconds'])}` "
            f"(`{locator['start_seconds']}`–`{locator['end_seconds']}` seconds)\n"
            f"- Transcript revision: `{item['canonical_transcript_revision_id']}`\n"
            f"- Word range: `{item['canonical_word_start_id']}` → "
            f"`{item['canonical_word_end_id']}`\n"
            f"- Canonical source of truth: {wikilink('_meta', 'canonical_evidence_reference', 'Canonical Evidence')}\n\n"
            "## Timing limitation\n\n"
            + limitations
            + "\n\n## Used by Topics\n\n"
            + bullets(topic_links)
            + "\n\n## Supports provisional Concepts\n\n"
            + bullets(concept_links),
        )

    manifest = {
        "artifact_type": "seminartext.obsidian_knowledge_prototype_export",
        "canonical_evidence": {
            "artifact_id": canonical["artifact_id"],
            "path": CANONICAL_REPO_PATH,
            "sha256": document["canonical_evidence"]["sha256"],
        },
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "files": {
            path: sha256_bytes(payload) for path, payload in sorted(files.items())
        },
        "generated_note_count": len(files),
        "golden_slice": {
            "artifact_id": document["artifact_id"],
            "path": "analysis/golden_knowledge_slice/golden_knowledge_slice.json",
            "sha256": slice_sha,
        },
        "portable": True,
        "product_review": {"required": True, "status": "pending"},
        "source_of_truth": "canonical_evidence_json_not_markdown",
    }
    return dict(sorted(files.items())), manifest


def export_vault(
    files: dict[str, bytes], output: Path, manifest: dict[str, Any], manifest_path: Path
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    existing = {
        path.relative_to(output).as_posix() for path in output.rglob("*.md")
    }
    unexpected = sorted(existing - set(files))
    if unexpected:
        raise ValueError(f"refusing to delete unmanaged Markdown: {unexpected}")
    for relative, payload in files.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(canonical_json_bytes(manifest))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slice", required=True, type=Path)
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    files, manifest = build_vault(args.slice, args.canonical)
    export_vault(files, args.output, manifest, args.manifest)
    print(
        json.dumps(
            {
                "generated_note_count": len(files),
                "manifest_sha256": sha256_bytes(canonical_json_bytes(manifest)),
                "output": str(args.output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
