from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VALID_STATUSES = {
    "PASS",
    "FAIL",
    "WARN",
    "NOT_IMPLEMENTED",
    "NOT_APPLICABLE",
}


@dataclass(frozen=True)
class CheckContext:
    root: Path
    deploy_dir: Path
    contract: dict[str, Any]
    test_command: tuple[str, ...]
    governance_command: tuple[str, ...]


@dataclass
class GateResult:
    gate_id: str
    name: str
    status: str
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid gate status: {self.status}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.gate_id,
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
            "evidence": self.evidence,
        }


def gate_definition(context: CheckContext, gate_id: str) -> dict[str, Any]:
    for gate in context.contract["gates"]:
        if gate["id"] == gate_id:
            return gate
    raise KeyError(f"gate not declared in contract: {gate_id}")
