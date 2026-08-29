from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Mapping, Sequence


def run_process(
    command: Sequence[str], cwd: Path, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
