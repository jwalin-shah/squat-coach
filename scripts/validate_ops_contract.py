"""Validate the documented squat-coach repository operations contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_SCHEMA = ROOT / "SQUAT_STATE_SCHEMA.md"
OPS_CONTRACT = ROOT / "docs" / "OPERATIONS_CONTRACT.md"
PACKAGE_JSON = ROOT / "package.json"
GITIGNORE = ROOT / ".gitignore"
SERVER = ROOT / "server.py"
RUN_MLX_DEMO = ROOT / "run_mlx_demo.sh"
FIXTURE_README = ROOT / "data" / "fixtures" / "README.md"

REQUIRED_STATE_FIELDS = (
    "phase",
    "rep_number",
    "knee_angle",
    "hip_angle",
    "torso_angle",
    "shin_angle",
    "hip_below_knee",
    "confidence_min",
)

REQUIRED_RUNTIME_BOUNDARY = (
    "video -> MediaPipe -> deterministic squat state -> local model -> coaching JSON"
)


def read_text(path: Path) -> str:
    """Read a UTF-8 text file.

    Parameters
    ----------
    path : Path
        File to read.

    Returns
    -------
    str
        File contents.
    """
    return path.read_text(encoding="utf-8")


def check_file_exists(path: Path, errors: list[str]) -> None:
    """Record an error when a required file is missing.

    Parameters
    ----------
    path : Path
        Required file path.
    errors : list of str
        Mutable collection of validation failures.
    """
    if not path.exists():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")


def check_state_schema(errors: list[str]) -> None:
    """Validate the compact state-schema documentation.

    Parameters
    ----------
    errors : list of str
        Mutable collection of validation failures.
    """
    schema = read_text(STATE_SCHEMA)

    for field in REQUIRED_STATE_FIELDS:
        if f"`{field}`" not in schema and f'"{field}"' not in schema:
            errors.append(f"SQUAT_STATE_SCHEMA.md does not document `{field}`")

    if "knee_valgus_ratio" not in schema:
        errors.append("SQUAT_STATE_SCHEMA.md does not document optional `knee_valgus_ratio`")

    if REQUIRED_RUNTIME_BOUNDARY not in schema:
        errors.append("SQUAT_STATE_SCHEMA.md does not document the runtime boundary")


def check_ops_contract(errors: list[str]) -> None:
    """Validate the repo operations contract documentation.

    Parameters
    ----------
    errors : list of str
        Mutable collection of validation failures.
    """
    contract = read_text(OPS_CONTRACT)

    for required_text in (
        REQUIRED_RUNTIME_BOUNDARY,
        "Fixture And Runtime Output Contract",
        "Runtime outputs default to ignored local paths.",
        "The only tracked path under `data/` is `data/fixtures/`.",
        "npm run ops:validate",
        "make validate-ops",
        "Public commits must not include",
    ):
        if required_text not in contract:
            errors.append(f"docs/OPERATIONS_CONTRACT.md is missing `{required_text}`")

    for field in REQUIRED_STATE_FIELDS:
        if f"`{field}`" not in contract:
            errors.append(f"docs/OPERATIONS_CONTRACT.md does not list `{field}`")


def check_runtime_output_defaults(errors: list[str]) -> None:
    """Validate local runtime outputs are separated from tracked fixtures.

    Parameters
    ----------
    errors : list of str
        Mutable collection of validation failures.
    """
    gitignore = read_text(GITIGNORE)
    server = read_text(SERVER)
    run_mlx_demo = read_text(RUN_MLX_DEMO)
    fixture_readme = read_text(FIXTURE_README)

    required_gitignore_entries = (
        ".runtime/",
        "data/*",
        "!data/fixtures/",
        "!data/fixtures/README.md",
        "logs/*.jsonl",
    )
    for entry in required_gitignore_entries:
        if entry not in gitignore.splitlines():
            errors.append(f".gitignore does not include `{entry}`")

    if "data/" in gitignore.splitlines():
        errors.append(".gitignore must not ignore `data/` itself because `data/fixtures/` is tracked")

    if '.runtime" / "logs" / "coach_events.jsonl"' not in server:
        errors.append("server.py default COACH_LOG_PATH must write under `.runtime/logs/`")

    if "$ROOT/.runtime/logs/coach_events.jsonl" not in run_mlx_demo:
        errors.append("run_mlx_demo.sh default COACH_LOG_PATH must write under `.runtime/logs/`")

    for required_text in (
        "only tracked path under `data/`",
        "small, deterministic fixtures",
        "Runtime outputs",
    ):
        if required_text not in fixture_readme:
            errors.append(f"data/fixtures/README.md is missing `{required_text}`")

    if FIXTURE_README.stat().st_size > 4096:
        errors.append("data/fixtures/README.md should stay small")


def check_package_scripts(errors: list[str]) -> None:
    """Validate required npm operations scripts.

    Parameters
    ----------
    errors : list of str
        Mutable collection of validation failures.
    """
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    scripts = package.get("scripts", {})

    expected_scripts = {
        "setup": "bash setup.sh",
        "serve": "python3 server.py",
        "ops:validate": "python3 scripts/validate_ops_contract.py",
    }

    for name, command in expected_scripts.items():
        if scripts.get(name) != command:
            errors.append(f"package.json script `{name}` should be `{command}`")


def main() -> int:
    """Run operations contract validation.

    Returns
    -------
    int
        Process exit code. Returns 0 on success, 1 on validation failure.
    """
    errors: list[str] = []

    for path in (STATE_SCHEMA, OPS_CONTRACT, PACKAGE_JSON, GITIGNORE, SERVER, RUN_MLX_DEMO, FIXTURE_README):
        check_file_exists(path, errors)

    if not errors:
        check_state_schema(errors)
        check_ops_contract(errors)
        check_package_scripts(errors)
        check_runtime_output_defaults(errors)

    if errors:
        sys.stderr.write("Operations contract validation failed:\n")
        for error in errors:
            sys.stderr.write(f"- {error}\n")
        return 1

    sys.stdout.write("Operations contract validation passed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
