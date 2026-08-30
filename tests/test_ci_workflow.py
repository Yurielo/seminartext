from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
PROTECTION = ROOT / ".github" / "MAIN_PROTECTION.md"


def test_ci_exposes_one_deterministic_quality_gate():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "name: SeminarText CI" in text
    assert text.count("runs-on:") == 1
    assert "name: Quality Gate" in text
    assert "pull_request:" in text
    assert "branches:" in text and "- main" in text
    assert "permissions:\n  contents: read" in text
    assert "SEMINARTEXT_DEV_REPO: ${{ github.workspace }}" in text
    assert "SEMINARTEXT_PYTHON: python" in text
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in text
    assert 'python-version: "3.14.6"' in text


def test_ci_runs_supported_checks_without_deployment_or_experiments():
    text = WORKFLOW.read_text(encoding="utf-8")

    required = (
        "requirements-dev.txt",
        "seminartext-dependencies doctor --profile dev_test --json",
        "./scripts/seminartext-dev check",
        "tests/test_milestone_reconciliation.py",
        "python -m pytest -q -rs -p no:cacheprovider",
        "./scripts/seminartext-integrity",
        "./scripts/seminartext-integrity --json",
    )
    assert all(command in text for command in required)
    assert "seminartext-dev deploy" not in text
    assert "dataset-d" not in text.lower()
    assert "topic-benchmark-run" not in text


def test_main_protection_contract_names_the_required_check_and_boundary():
    text = PROTECTION.read_text(encoding="utf-8")

    assert "required status check `Quality Gate`" in text
    assert "pull requests required before merge" in text
    assert "force pushes and branch deletion blocked" in text
    assert "direct pushes blocked" in text
    assert "G2 may be `WARN`/unverified" in text
    assert "not evidence that the settings are currently enabled" in text
