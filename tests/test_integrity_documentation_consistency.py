import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_integrity_readme_gate_inventory_matches_authoritative_contract():
    contract = json.loads(
        (ROOT / "integrity" / "integrity_contract.json").read_text(encoding="utf-8")
    )
    readme = (ROOT / "integrity" / "README.md").read_text(encoding="utf-8")

    for gate in contract["gates"]:
        row = (
            f"| {gate['id']} | {gate['name']} | {gate['implementation']} | "
            f"{gate['blocking_policy']} |"
        )
        assert row in readme

    assert "G6 remains explicitly `NOT_IMPLEMENTED`" in readme
    assert "machine-readable contract remains the sole gate definition" in readme


def test_static_workflow_document_does_not_claim_a_current_milestone():
    workflow = (ROOT / "DEVELOPMENT_WORKFLOW.md").read_text(encoding="utf-8")
    assert "must not repeat a current milestone or next action" in workflow
    assert "never a control-plane source of truth" in workflow
    assert "current_milestone_id" not in workflow
    assert "audit_r5" not in workflow


def test_issue_template_requires_all_r5_verification_fields():
    template = (ROOT / ".github" / "ISSUE_TEMPLATE.md").read_text(encoding="utf-8")
    required = (
        "## Human gate",
        "## Requirement-to-evidence mapping",
        "### Focused tests",
        "### Full tests",
        "### Integrity",
        "## Changed-file scope",
        "## Post-merge acceptance",
        "## Deploy or runtime reconciliation",
    )
    assert all(section in template for section in required)


def test_issue_and_pr_templates_require_product_rule_references():
    for relative in (".github/ISSUE_TEMPLATE.md", ".github/PULL_REQUEST_TEMPLATE.md"):
        template = (ROOT / relative).read_text(encoding="utf-8")
        assert "docs/architecture/SEMINARTEXT_PRODUCT_RULES.md" in template
        assert "Applicable Product Rules:" in template
        assert "Product Rule conflicts:" in template
        assert "does not waive an `ACTIVE` Product Rule" in template
