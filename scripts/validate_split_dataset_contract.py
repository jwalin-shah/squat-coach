#!/usr/bin/env python3
"""Validate split_dataset_by_group JSONL parser failure modes."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_split(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run the dataset splitter with captured text output.

    Parameters
    ----------
    args : list of str
        Command-line arguments to pass to split_dataset_by_group.py.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process result without raising for nonzero exit codes.
    """
    return subprocess.run(
        [sys.executable, str(ROOT / "split_dataset_by_group.py"), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write fixture rows as JSONL.

    Parameters
    ----------
    path : Path
        Destination fixture path.
    rows : list of dict
        JSON object rows to write.
    """
    path.write_text("".join(f"{json.dumps(row)}\n" for row in rows), encoding="utf-8")


def validate_success(tmpdir: Path) -> None:
    """Verify valid JSONL keeps producing train, eval, and summary outputs.

    Parameters
    ----------
    tmpdir : Path
        Temporary directory for isolated validator fixtures.
    """
    input_path = tmpdir / "valid.jsonl"
    train_path = tmpdir / "train.jsonl"
    eval_path = tmpdir / "eval.jsonl"
    summary_path = tmpdir / "summary.json"
    write_jsonl(
        input_path,
        [
            {"id": "session-a-rep1", "label": "good"},
            {"id": "session-b-rep1", "label": "shallow"},
            {"id": "session-c-rep1", "label": "lean"},
        ],
    )

    result = run_split(
        [
            "--input",
            str(input_path),
            "--train-output",
            str(train_path),
            "--eval-output",
            str(eval_path),
            "--summary-output",
            str(summary_path),
            "--eval-ratio",
            "0.34",
            "--seed",
            "7",
        ]
    )
    if result.returncode != 0:
        raise AssertionError(f"valid split failed:\n{result.stdout}{result.stderr}")
    for path in (train_path, eval_path, summary_path):
        if not path.exists():
            raise AssertionError(f"valid split did not create {path.name}")


def validate_failure(tmpdir: Path) -> None:
    """Verify malformed JSONL fails closed with a line-specific error.

    Parameters
    ----------
    tmpdir : Path
        Temporary directory for isolated validator fixtures.
    """
    input_path = tmpdir / "malformed.jsonl"
    input_path.write_text('{"id": "session-a-rep1"}\n["not", "an", "object"]\n', encoding="utf-8")

    result = run_split(
        [
            "--input",
            str(input_path),
            "--train-output",
            str(tmpdir / "train.bad.jsonl"),
            "--eval-output",
            str(tmpdir / "eval.bad.jsonl"),
        ]
    )
    if result.returncode == 0:
        raise AssertionError("malformed JSONL input was accepted")
    expected = f"{input_path}:2: JSONL row must be an object."
    if expected not in result.stderr:
        raise AssertionError(f"malformed JSONL failure was not clear:\n{result.stderr}")


def main() -> int:
    """Run split-dataset parser contract validation.

    Returns
    -------
    int
        Zero when valid input succeeds and malformed input fails clearly.
    """
    with tempfile.TemporaryDirectory(prefix="split-dataset-contract-") as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)
        validate_success(tmpdir)
        validate_failure(tmpdir)
    print("Split dataset parser contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
