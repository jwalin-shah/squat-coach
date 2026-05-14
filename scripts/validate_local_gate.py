#!/usr/bin/env python3
"""Run the authoritative local validation gate for PR handoff."""

from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VALIDATORS = (
    ROOT / "scripts" / "validate_static_app.py",
    ROOT / "scripts" / "validate_cli_smoke.py",
    ROOT / "scripts" / "validate_split_dataset_contract.py",
    ROOT / "scripts" / "validate_ops_contract.py",
    ROOT / "scripts" / "validate_state_policy_contract.py",
)

PYTHON_COMPILE_TARGETS = (
    ROOT / "server.py",
    ROOT / "prompt_templates.py",
    ROOT / "generate_synthetic_data.py",
    ROOT / "generate_gemini_dataset.py",
    ROOT / "evaluate_coach_dataset.py",
    ROOT / "split_dataset_by_group.py",
)


def display_path(path: Path) -> Path:
    """Return a readable path for validation output.

    Parameters
    ----------
    path : Path
        File path to display.

    Returns
    -------
    Path
        Repo-relative path when possible, otherwise the original path.
    """
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def run_validator(path: Path) -> None:
    """Run one executable validator.

    Parameters
    ----------
    path : Path
        Validator script to execute with the current Python interpreter.
    """
    relative = display_path(path)
    print(f"Running {relative}...", flush=True)
    subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)


def compile_python(path: Path) -> None:
    """Compile one Python module and fail on syntax errors.

    Parameters
    ----------
    path : Path
        Python module to compile.
    """
    relative = display_path(path)
    print(f"Compiling {relative}...", flush=True)
    py_compile.compile(str(path), doraise=True)


def main() -> int:
    """Run all local validation checks.

    Returns
    -------
    int
        Process exit code. Returns 0 when every validator and compile check
        passes; otherwise returns the failing command's nonzero exit code.
    """
    try:
        for validator in VALIDATORS:
            run_validator(validator)
        for target in PYTHON_COMPILE_TARGETS:
            compile_python(target)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except py_compile.PyCompileError as exc:
        sys.stderr.write(f"Python compile validation failed:\n{exc}\n")
        return 1

    print("Local validation gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
