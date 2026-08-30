import re
import shutil
from pathlib import Path

import pytest

from scripts.validate_product_rules import (
    CANONICAL_REGISTRY,
    CONTROL_LOOP_FILES,
    ProductRulesValidationError,
    parse_registry,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    relatives = {CANONICAL_REGISTRY, *(Path(item) for item in CONTROL_LOOP_FILES)}
    for relative in relatives:
        source = ROOT / relative
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return root


def _registry(root: Path) -> Path:
    return root / CANONICAL_REGISTRY


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _future_rule(
    rule_id: str = "PR-012",
    *,
    status: str = "ACTIVE",
    supersedes: str = "NONE",
    superseded_by: str = "NONE",
) -> str:
    return f"""

<!-- PRODUCT_RULE_START -->
## {rule_id} — Future Authorized Rule

### ID
{rule_id}

### Title
Future Authorized Rule

### Status
{status}

### Normative Rule
A bounded future rule used only by the structural validation fixture.

### Rationale
Prove deterministic safe append behavior without adopting a real Product Rule.

### Scope
Synthetic validator fixture only.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
{supersedes}

### Superseded By
{superseded_by}

### Related Contracts / Issues
Synthetic test fixture
<!-- PRODUCT_RULE_END -->
"""


def test_valid_registry_and_exact_authorized_initial_inventory_pass():
    result = validate_repository(ROOT)
    rules = parse_registry((ROOT / CANONICAL_REGISTRY).read_text(encoding="utf-8"))

    assert result["rule_count"] == 11
    assert result["active"] == 11
    assert result["superseded"] == 0
    assert result["retired"] == 0
    assert result["next_rule_id"] == "PR-012"
    assert [rule.rule_id for rule in rules] == [f"PR-{index:03d}" for index in range(1, 12)]
    assert {rule.status for rule in rules} == {"ACTIVE"}


def test_duplicate_or_reused_id_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text = path.read_text(encoding="utf-8") + _future_rule("PR-011")
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="duplicate or reused"):
        validate_repository(root)


def test_invalid_id_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text = path.read_text(encoding="utf-8").replace(
        "### ID\nPR-001", "### ID\nRULE-001", 1
    )
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="invalid Product Rule ID"):
        validate_repository(root)


def test_unknown_status_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text = path.read_text(encoding="utf-8").replace(
        "### Status\nACTIVE", "### Status\nDRAFT", 1
    )
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="unknown lifecycle status"):
        validate_repository(root)


def test_broken_supersedes_reference_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    _write(path, path.read_text(encoding="utf-8") + _future_rule(supersedes="PR-999"))

    with pytest.raises(ProductRulesValidationError, match="broken supersession reference PR-999"):
        validate_repository(root)


def test_broken_superseded_by_reference_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text = path.read_text(encoding="utf-8")
    text = text.replace("### Status\nACTIVE", "### Status\nSUPERSEDED", 1)
    text = text.replace("### Superseded By\nNONE", "### Superseded By\nPR-011", 1)
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="does not reciprocate Supersedes"):
        validate_repository(root)


def test_cyclic_supersession_chain_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text = path.read_text(encoding="utf-8")
    text += _future_rule(
        "PR-012",
        status="SUPERSEDED",
        supersedes="PR-013",
        superseded_by="PR-013",
    )
    text += _future_rule(
        "PR-013",
        status="SUPERSEDED",
        supersedes="PR-012",
        superseded_by="PR-012",
    )
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="supersession chain contains cycle"):
        validate_repository(root)


def test_invalid_lifecycle_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text = path.read_text(encoding="utf-8").replace(
        "### Status\nACTIVE", "### Status\nSUPERSEDED", 1
    )
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="SUPERSEDED rule requires"):
        validate_repository(root)


def test_missing_required_field_fails(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    text, count = re.subn(
        r"\n### Rationale\n.*?(?=\n### Scope)",
        "",
        path.read_text(encoding="utf-8"),
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1
    _write(path, text)

    with pytest.raises(ProductRulesValidationError, match="missing required field.*Rationale"):
        validate_repository(root)


def test_missing_canonical_registry_fails(tmp_path):
    root = _fixture(tmp_path)
    _registry(root).unlink()

    with pytest.raises(ProductRulesValidationError, match="canonical Product Rules Registry missing"):
        validate_repository(root)


def test_operating_contract_without_registry_reference_fails(tmp_path):
    root = _fixture(tmp_path)
    workflow = root / "DEVELOPMENT_WORKFLOW.md"
    _write(
        workflow,
        workflow.read_text(encoding="utf-8").replace(
            CANONICAL_REGISTRY.as_posix(), "missing/product_rules.md"
        ),
    )

    with pytest.raises(ProductRulesValidationError, match="DEVELOPMENT_WORKFLOW.md does not contain"):
        validate_repository(root)


def test_competing_canonical_registry_fails(tmp_path):
    root = _fixture(tmp_path)
    duplicate = root / "archive" / CANONICAL_REGISTRY.name
    duplicate.parent.mkdir()
    shutil.copy2(_registry(root), duplicate)

    with pytest.raises(ProductRulesValidationError, match="must be unique"):
        validate_repository(root)


def test_future_append_of_next_valid_rule_passes(tmp_path):
    root = _fixture(tmp_path)
    path = _registry(root)
    _write(path, path.read_text(encoding="utf-8") + _future_rule())

    result = validate_repository(root)

    assert result["rule_count"] == 12
    assert result["next_rule_id"] == "PR-013"


def test_human_review_compatibility_is_explicit_without_alias_enum_conflation():
    registry = (ROOT / CANONICAL_REGISTRY).read_text(encoding="utf-8")

    assert "Evidence -> Topic Draft ->" in registry
    assert "REVIEW_REQUIRED -> Human Review -> ReviewDecision" in registry
    assert all(decision in registry for decision in ("ACCEPT", "RENAME", "SPLIT", "MERGE", "REJECT", "DEFER"))
    assert all(outcome in registry for outcome in ("SAME_CONCEPT", "NEW_CONCEPT", "RELATED", "DISTINCT"))
    assert "do not redefine the existing Topic ReviewDecision" in registry
