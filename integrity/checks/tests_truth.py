from __future__ import annotations

import re
import os

from integrity.model import CheckContext, GateResult, gate_definition
from integrity.process import run_process


def _count(pattern: str, output: str) -> int:
    matches = re.findall(pattern, output)
    return int(matches[-1]) if matches else 0


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G7")
    try:
        process = run_process(
            context.test_command,
            context.root,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except OSError as exc:
        return GateResult(
            "G7",
            gate["name"],
            "FAIL",
            "supported test command is unavailable; PASS was not fabricated",
            {"command": list(context.test_command), "error": str(exc)},
        )

    output = "\n".join(part for part in (process.stdout, process.stderr) if part)
    passed = _count(r"(\d+) passed", output)
    failed = _count(r"(\d+) failed", output)
    skipped = _count(r"(\d+) skipped", output)
    skip_lines = [
        line.strip()
        for line in output.splitlines()
        if line.lstrip().startswith("SKIPPED ")
    ]
    evidence = {
        "command": list(context.test_command),
        "exit_code": process.returncode,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "skip_details": skip_lines,
        "skip_policy": context.contract["test_policy"]["skip_policy"],
        "skip_policy_limitation": context.contract["test_policy"][
            "known_current_limitation"
        ],
        "output_tail": output.splitlines()[-30:],
    }
    if process.returncode != 0 or failed:
        return GateResult(
            "G7", gate["name"], "FAIL", "full repository test command failed", evidence
        )
    if passed == 0:
        return GateResult(
            "G7",
            gate["name"],
            "FAIL",
            "test command reported no passing tests; capability is UNVERIFIED",
            evidence,
        )
    if skipped:
        return GateResult(
            "G7",
            gate["name"],
            "WARN",
            f"tests passed with {skipped} visible skip(s); G4 profile is declared, rebuild the active runtime from requirements-dev.txt",
            evidence,
        )
    return GateResult(
        "G7",
        gate["name"],
        "PASS",
        f"full repository tests passed ({passed} passed, 0 skipped)",
        evidence,
    )
