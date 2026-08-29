from __future__ import annotations

from integrity.model import CheckContext, GateResult, gate_definition
from integrity.process import run_process


def _git(context: CheckContext, *args: str):
    return run_process(("git", "-C", str(context.root), *args), context.root)


def run(context: CheckContext) -> GateResult:
    gate = gate_definition(context, "G1")
    top = _git(context, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return GateResult(
            "G1",
            gate["name"],
            "FAIL",
            "repository root cannot be resolved",
            {"stderr": top.stderr.strip()},
        )

    resolved = top.stdout.strip()
    head = _git(context, "rev-parse", "HEAD")
    branch = _git(context, "branch", "--show-current")
    status = _git(context, "status", "--porcelain=v1", "--untracked-files=all")
    if any(item.returncode != 0 for item in (head, branch, status)):
        return GateResult(
            "G1",
            gate["name"],
            "FAIL",
            "one or more local Git identity commands failed",
            {
                "root": resolved,
                "head_error": head.stderr.strip(),
                "branch_error": branch.stderr.strip(),
                "status_error": status.stderr.strip(),
            },
        )

    dirty_entries = [line for line in status.stdout.splitlines() if line]
    missing = []
    untracked_required = []
    component_rows = []
    for component in context.contract["runtime_components"]:
        if not component.get("required", False):
            continue
        relative = component["repository_path"]
        path = context.root / relative
        tracked = _git(context, "ls-files", "--error-unmatch", "--", relative)
        row = {
            "id": component["id"],
            "path": relative,
            "exists": path.is_file(),
            "tracked": tracked.returncode == 0,
        }
        component_rows.append(row)
        if not path.is_file():
            missing.append(relative)
        if tracked.returncode != 0:
            untracked_required.append(relative)

    origin = _git(context, "rev-parse", "--verify", "origin/main")
    origin_available = origin.returncode == 0
    ahead = behind = None
    relation = "UNVERIFIED"
    if origin_available:
        counts = _git(
            context,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...origin/main",
        )
        if counts.returncode == 0:
            raw_ahead, raw_behind = counts.stdout.split()
            ahead, behind = int(raw_ahead), int(raw_behind)
            relation = "CURRENT_OR_AHEAD" if behind == 0 else "BEHIND_OR_DIVERGED"
        else:
            origin_available = False

    evidence = {
        "repository_root": resolved,
        "head_sha": head.stdout.strip(),
        "branch": branch.stdout.strip() or "DETACHED",
        "working_tree_clean": not dirty_entries,
        "dirty_entries": dirty_entries,
        "origin_contact_attempted": False,
        "origin_main_available_locally": origin_available,
        "origin_main_relation": relation,
        "ahead": ahead,
        "behind": behind,
        "required_runtime_components": component_rows,
    }

    failures = []
    if resolved != str(context.root.resolve()):
        failures.append(f"resolved root differs: {resolved}")
    if dirty_entries:
        failures.append("working tree is dirty")
    if missing:
        failures.append("required runtime source missing: " + ", ".join(missing))
    if untracked_required:
        failures.append(
            "required runtime source not tracked: " + ", ".join(untracked_required)
        )
    if origin_available and behind:
        failures.append(f"HEAD is behind origin/main by {behind} commit(s)")
    if failures:
        return GateResult("G1", gate["name"], "FAIL", "; ".join(failures), evidence)
    if not origin_available:
        return GateResult(
            "G1",
            gate["name"],
            "WARN",
            "local origin/main ref unavailable; network was intentionally not contacted",
            evidence,
        )
    return GateResult(
        "G1", gate["name"], "PASS", "local Git truth invariants pass", evidence
    )
