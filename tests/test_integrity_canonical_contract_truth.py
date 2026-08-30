import copy
import json
import shutil
from pathlib import Path

from integrity.checks import canonical_contract_truth
from integrity.model import CheckContext
from integrity.runner import load_contract


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "integrity/integrity_contract.json",
    "schemas/canonical_evidence_v1.schema.json",
    "schemas/validate_canonical_evidence_v1.py",
    "schemas/canonical_knowledge_v1.schema.json",
    "schemas/validate_canonical_knowledge_v1.py",
    "schemas/canonical_knowledge_lifecycle_v1.json",
    "analysis/word_timeline_mvp/canonical_evidence_bundle.json",
    "analysis/golden_knowledge_slice/golden_knowledge_slice.json",
    "analysis/golden_knowledge_slice/curation.json",
    "analysis/golden_knowledge_slice/build_golden_slice.py",
    "tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json",
)


def _context(root: Path) -> CheckContext:
    contract = load_contract(root)
    return CheckContext(root, root / "deploy", contract, ("python",), ("python",))


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for relative in REQUIRED:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return root


def test_g5_composes_all_canonical_evidence_and_knowledge_checks():
    result = canonical_contract_truth.run(_context(ROOT))
    assert result.status == "PASS", result.reason
    checks = result.evidence["checks"]
    assert all(
        checks[name]["status"] == "PASS"
        for name in (
            "canonical_evidence_schema",
            "canonical_evidence_invariants",
            "canonical_knowledge_schema",
            "canonical_knowledge_invariants",
            "cross_record_references",
            "source_pointers_and_hashes",
            "golden_slice_compatibility",
            "fail_closed_negative_cases",
        )
    )
    assert result.evidence["fail_closed"] is True


def test_g5_fails_closed_when_a_canonical_reference_is_dangling(tmp_path):
    root = _fixture(tmp_path)
    path = root / "tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["topics"][0]["concept_refs"].append("concept_missing")
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    result = canonical_contract_truth.run(_context(root))
    assert result.status == "FAIL"
    assert any("dangling reference" in error for error in result.evidence["checks"]["canonical_knowledge_invariants"]["errors"])


def test_g5_fails_closed_when_canonical_evidence_schema_is_invalid(tmp_path):
    root = _fixture(tmp_path)
    path = root / "analysis/word_timeline_mvp/canonical_evidence_bundle.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["schema_version"] = "2.0.0"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    result = canonical_contract_truth.run(_context(root))
    assert result.status == "FAIL"
    assert result.evidence["checks"]["canonical_evidence_schema"]["status"] == "FAIL"


def test_g5_fails_closed_when_golden_slice_changes(tmp_path):
    root = _fixture(tmp_path)
    path = root / "analysis/golden_knowledge_slice/golden_knowledge_slice.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["product_review"]["status"] = "changed_without_review"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = canonical_contract_truth.run(_context(root))
    assert result.status == "FAIL"
    assert result.evidence["checks"]["golden_slice_compatibility"]["status"] == "FAIL"
