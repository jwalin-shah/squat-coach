#!/usr/bin/env python3
"""Validate the no-secret CLI smoke contract for the server entrypoint."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a server CLI command for contract validation.

    Parameters
    ----------
    args : list of str
        Command-line arguments to pass after the Python executable.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed subprocess result with captured text output.
    """
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    """Run successful and failing CLI smoke checks.

    Returns
    -------
    int
        Zero when the smoke path succeeds and bad CLI input fails clearly.
    """
    smoke = run_command(["server.py", "--smoke"])
    if smoke.returncode != 0:
        sys.stderr.write("server.py --smoke failed:\n")
        sys.stderr.write(smoke.stdout)
        sys.stderr.write(smoke.stderr)
        return smoke.returncode or 1
    if "Server CLI smoke check passed." not in smoke.stdout:
        sys.stderr.write("server.py --smoke did not report success.\n")
        return 1

    bad_input = run_command(["server.py", "--port", "0", "--smoke"])
    if bad_input.returncode == 0:
        sys.stderr.write("server.py accepted invalid port 0.\n")
        return 1
    if "port must be between 1 and 65535" not in bad_input.stderr:
        sys.stderr.write("server.py invalid-port failure was not clear:\n")
        sys.stderr.write(bad_input.stderr)
        return 1

    print("Server CLI smoke contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
