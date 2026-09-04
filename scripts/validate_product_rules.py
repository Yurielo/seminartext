#!/usr/bin/env python3
"""Validate the canonical SeminarText Product Rules Registry and control loop."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CANONICAL_REGISTRY = Path("docs/architecture/SEMINARTEXT_PRODUCT_RULES.md")
REGISTRY_NAME = CANONICAL_REGISTRY.name
RULE_START = "<!-- PRODUCT_RULE_START -->"
RULE_END = "<!-- PRODUCT_RULE_END -->"
RULE_ID_PATTERN = re.compile(r"PR-(\d{3})")
RULE_HEADING_PATTERN = re.compile(r"^## (PR-\d{3}) — (.+)$", re.MULTILINE)
FIELD_PATTERN = re.compile(r"^### (.+)$", re.MULTILINE)
ALLOWED_STATUSES = {"ACTIVE", "SUPERSEDED", "RETIRED"}
REQUIRED_FIELDS = (
    "ID",
    "Title",
    "Status",
    "Normative Rule",
    "Rationale",
    "Scope",
    "Authority",
    "Date Adopted",
    "Supersedes",
    "Superseded By",
    "Related Contracts / Issues",
)
CONTROL_LOOP_FILES = {
    "AGENTS.md": (
        CANONICAL_REGISTRY.as_posix(),
        "PRODUCT_RULES_READ",
        "APPLICABLE_PRODUCT_RULES",
        "PRODUCT_RULE_CONFLICTS",
        "AUTONOMOUS UNTIL HUMAN GATE",
        "AUTONOMOUS ALONG APPROVED ROADMAP",
        "NEXT_ROADMAP_ITEM",
        "ROADMAP_EXECUTION_AUTHORITY",
        "MECHANICAL_STATE_RECONCILIATION = AUTO",
        "ISSUE_LIFECYCLE = AUTO",
        "SAFE_MERGE = AUTO",
        "SAFE_RUNTIME_RECONCILIATION = AUTO",
        "governance PR never self-authorizes",
        "user must not be used as a",
        "NEXT_AUTHORIZATION_BOUNDARY",
        "HARD STOP",
    ),
    "DEVELOPMENT_WORKFLOW.md": (
        CANONICAL_REGISTRY.as_posix(),
        "ChatGPT / Prompt 11 control",
        "Applicable Product Rules",
        "Product Rule conflicts",
        "Autonomous Until Human Gate",
        "Autonomous Along Approved Roadmap",
        "NEXT_TECHNICAL_SUBSTEP",
        "NEXT_ROADMAP_ITEM",
        "ROADMAP_EXECUTION_AUTHORITY",
        "ROADMAP_CHANGE",
        "MECHANICAL_STATE_RECONCILIATION = AUTO",
        "ISSUE_LIFECYCLE = AUTO",
        "SAFE_MERGE = AUTO",
        "SAFE_RUNTIME_RECONCILIATION = AUTO",
        "HIGH_RISK_IRREVERSIBLE_OPERATION",
        "cannot use its own unmerged rule as authority",
        "prohibited user-courier antipattern",
        "NEXT_AUTHORIZATION_BOUNDARY",
        "HARD STOP",
    ),
    ".github/ISSUE_TEMPLATE.md": (
        "Applicable Product Rules:",
        "Product Rule conflicts:",
    ),
    ".github/PULL_REQUEST_TEMPLATE.md": (
        "Applicable Product Rules:",
        "Product Rule conflicts:",
    ),
    ".github/workflows/ci.yml": (
        "scripts/validate_product_rules.py",
    ),
    "scripts/check_governance.py": (
        "validate_product_rules",
    ),
}


class ProductRulesValidationError(ValueError):
    """Raised when registry or control-loop structure is invalid."""


@dataclass(frozen=True)
class ProductRule:
    rule_id: str
    title: str
    status: str
    fields: dict[str, str]
    supersedes: tuple[str, ...]
    superseded_by: tuple[str, ...]


def _fail(message: str) -> None:
    raise ProductRulesValidationError(message)


def _canonical_registry_candidates(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob(REGISTRY_NAME)
        if path.is_file() and ".git" not in path.parts
    )


def _parse_fields(block: str, rule_id: str) -> dict[str, str]:
    matches = list(FIELD_PATTERN.finditer(block))
    fields: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        if name in fields:
            _fail(f"{rule_id}: duplicate field {name!r}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        value = block[match.end() : end].strip()
        fields[name] = value

    missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
    if missing:
        _fail(f"{rule_id}: missing required field(s): {', '.join(missing)}")
    unexpected = sorted(set(fields) - set(REQUIRED_FIELDS))
    if unexpected:
        _fail(f"{rule_id}: unknown field(s): {', '.join(unexpected)}")
    return fields


def _parse_references(value: str, rule_id: str, field: str) -> tuple[str, ...]:
    if value == "NONE":
        return ()
    references = tuple(item.strip() for item in value.split(","))
    if not references or any(not RULE_ID_PATTERN.fullmatch(item) for item in references):
        _fail(f"{rule_id}: {field} must be NONE or comma-separated PR-xxx IDs")
    if len(references) != len(set(references)):
        _fail(f"{rule_id}: {field} contains duplicate references")
    return references


def parse_registry(text: str) -> list[ProductRule]:
    if text.count(RULE_START) != text.count(RULE_END):
        _fail("Product Rule marker counts do not match")
    if text.count(RULE_START) == 0:
        _fail("Registry contains no Product Rule records")

    pattern = re.compile(
        re.escape(RULE_START) + r"\s*(.*?)\s*" + re.escape(RULE_END),
        re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != text.count(RULE_START):
        _fail("Registry contains malformed or nested Product Rule markers")

    rules: list[ProductRule] = []
    seen: set[str] = set()
    for match in matches:
        block = match.group(1)
        heading_matches = RULE_HEADING_PATTERN.findall(block)
        if len(heading_matches) != 1:
            _fail("each Product Rule record must contain exactly one PR-xxx heading")
        heading_id, heading_title = heading_matches[0]
        fields = _parse_fields(block, heading_id)
        rule_id = fields["ID"]
        title = fields["Title"]
        if not RULE_ID_PATTERN.fullmatch(rule_id):
            _fail(f"invalid Product Rule ID: {rule_id!r}")
        if rule_id in seen:
            _fail(f"duplicate or reused Product Rule ID: {rule_id}")
        seen.add(rule_id)
        if (heading_id, heading_title) != (rule_id, title):
            _fail(f"{rule_id}: heading must match ID and Title fields")

        status = fields["Status"]
        if status not in ALLOWED_STATUSES:
            _fail(f"{rule_id}: unknown lifecycle status {status!r}")
        try:
            date.fromisoformat(fields["Date Adopted"])
        except ValueError:
            _fail(f"{rule_id}: Date Adopted must be an ISO date")

        rules.append(
            ProductRule(
                rule_id=rule_id,
                title=title,
                status=status,
                fields=fields,
                supersedes=_parse_references(fields["Supersedes"], rule_id, "Supersedes"),
                superseded_by=_parse_references(
                    fields["Superseded By"], rule_id, "Superseded By"
                ),
            )
        )

    numbers = [int(RULE_ID_PATTERN.fullmatch(rule.rule_id).group(1)) for rule in rules]
    expected = list(range(1, len(rules) + 1))
    if numbers != expected:
        _fail(
            "Product Rule IDs must remain ordered and contiguous from PR-001; "
            "historical IDs cannot be deleted, reordered, or reused"
        )
    return rules


def _validate_lifecycle(rules: list[ProductRule]) -> None:
    by_id = {rule.rule_id: rule for rule in rules}
    for rule in rules:
        for reference in (*rule.supersedes, *rule.superseded_by):
            if reference not in by_id:
                _fail(f"{rule.rule_id}: broken supersession reference {reference}")
            if reference == rule.rule_id:
                _fail(f"{rule.rule_id}: a rule cannot supersede itself")

        if rule.status == "ACTIVE" and rule.superseded_by:
            _fail(f"{rule.rule_id}: ACTIVE rule cannot have Superseded By")
        if rule.status == "SUPERSEDED" and not rule.superseded_by:
            _fail(f"{rule.rule_id}: SUPERSEDED rule requires Superseded By")
        if rule.status == "RETIRED" and rule.superseded_by:
            _fail(f"{rule.rule_id}: RETIRED rule cannot have Superseded By")

        for previous_id in rule.supersedes:
            previous = by_id[previous_id]
            if previous.status != "SUPERSEDED":
                _fail(
                    f"{rule.rule_id}: Supersedes target {previous_id} must be SUPERSEDED"
                )
            if rule.rule_id not in previous.superseded_by:
                _fail(
                    f"{rule.rule_id}: {previous_id} does not reciprocate Superseded By"
                )
        for successor_id in rule.superseded_by:
            successor = by_id[successor_id]
            if rule.rule_id not in successor.supersedes:
                _fail(
                    f"{rule.rule_id}: {successor_id} does not reciprocate Supersedes"
                )

    def visit(rule_id: str, path: tuple[str, ...]) -> None:
        if rule_id in path:
            _fail("broken supersession chain contains cycle: " + " -> ".join((*path, rule_id)))
        for successor_id in by_id[rule_id].superseded_by:
            visit(successor_id, (*path, rule_id))

    for rule in rules:
        visit(rule.rule_id, ())


def _validate_control_loop(root: Path) -> None:
    for relative, required_fragments in CONTROL_LOOP_FILES.items():
        path = root / relative
        if not path.is_file():
            _fail(f"required Product Rules control-loop file missing: {relative}")
        content = path.read_text(encoding="utf-8")
        missing = [fragment for fragment in required_fragments if fragment not in content]
        if missing:
            _fail(
                f"{relative} does not contain required Product Rules wiring: "
                + ", ".join(missing)
            )


def validate_repository(root: Path) -> dict[str, object]:
    root = root.resolve()
    registry_path = root / CANONICAL_REGISTRY
    if not registry_path.is_file():
        _fail(f"canonical Product Rules Registry missing: {CANONICAL_REGISTRY}")
    candidates = _canonical_registry_candidates(root)
    if candidates != [registry_path]:
        rendered = ", ".join(path.relative_to(root).as_posix() for path in candidates)
        _fail(f"canonical Product Rules Registry must be unique; found: {rendered}")

    rules = parse_registry(registry_path.read_text(encoding="utf-8"))
    _validate_lifecycle(rules)
    _validate_control_loop(root)
    return {
        "registry": CANONICAL_REGISTRY.as_posix(),
        "rule_count": len(rules),
        "active": sum(rule.status == "ACTIVE" for rule in rules),
        "superseded": sum(rule.status == "SUPERSEDED" for rule in rules),
        "retired": sum(rule.status == "RETIRED" for rule in rules),
        "next_rule_id": f"PR-{len(rules) + 1:03d}",
        "control_loop": "WIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = validate_repository(args.root)
    except (OSError, ProductRulesValidationError) as exc:
        print(f"PRODUCT RULES REGISTRY: FAIL\n{exc}")
        return 1
    print("PRODUCT RULES REGISTRY: PASS")
    for key, value in result.items():
        print(f"  {key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
