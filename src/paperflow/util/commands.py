import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(
    args: Sequence[str],
    cwd: Path | None = None,
    timeout_s: int = 600,
) -> CommandResult:
    """Run an external command safely. Never uses shell=True."""
    result = subprocess.run(
        [str(a) for a in args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout_s,
    )
    return CommandResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
