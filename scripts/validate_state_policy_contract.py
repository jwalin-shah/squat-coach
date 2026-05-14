"""Validate the compact squat-state schema and live policy wiring."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_JSON = ROOT / "SQUAT_STATE_SCHEMA.json"
SCHEMA_MD = ROOT / "SQUAT_STATE_SCHEMA.md"
PROMPT_TEMPLATES = ROOT / "prompt_templates.py"
SERVER = ROOT / "server.py"
STATIC_INDEX = ROOT / "static" / "index.html"
OFFLINE_EXTRACT = ROOT / "static" / "offline-extract.html"

REQUIRED_FIELDS = (
    "phase",
    "rep_number",
    "knee_angle",
    "hip_angle",
    "torso_angle",
    "shin_angle",
    "hip_below_knee",
    "confidence_min",
)
OPTIONAL_FIELDS = ("knee_valgus_ratio",)
EXCLUDED_MODEL_FIELDS = ("depth_history", "phase_durations_ms")


def load_schema(errors: list[str]) -> dict:
    try:
        return json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load SQUAT_STATE_SCHEMA.json: {exc}")
        return {}


def check_schema_files(schema: dict, errors: list[str]) -> None:
    if tuple(schema.get("model_facing_fields", ())) != REQUIRED_FIELDS:
        errors.append("SQUAT_STATE_SCHEMA.json model_facing_fields drifted from v1")
    if tuple(schema.get("optional_model_facing_fields", ())) != OPTIONAL_FIELDS:
        errors.append("SQUAT_STATE_SCHEMA.json optional fields drifted from v1")

    md = SCHEMA_MD.read_text(encoding="utf-8")
    for field in (*REQUIRED_FIELDS, *OPTIONAL_FIELDS):
        if f"`{field}`" not in md and f'"{field}"' not in md:
            errors.append(f"SQUAT_STATE_SCHEMA.md does not document `{field}`")
    for field in EXCLUDED_MODEL_FIELDS:
        if f"`{field}`" not in md:
            errors.append(f"SQUAT_STATE_SCHEMA.md does not exclude `{field}` from v1")


def literal_function_return(module: ast.Module, function_name: str):
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for statement in node.body:
                if isinstance(statement, ast.Return):
                    return ast.literal_eval(statement.value)
    raise ValueError(f"could not find literal return for {function_name}")


def check_prompt_policy(schema: dict, errors: list[str]) -> None:
    source = PROMPT_TEMPLATES.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(PROMPT_TEMPLATES))

    if "SQUAT_STATE_SCHEMA.json" not in source:
        errors.append("prompt_templates.py does not load SQUAT_STATE_SCHEMA.json")
    if "def compact_squat_state" not in source:
        errors.append("prompt_templates.py does not expose compact_squat_state")

    examples = literal_function_return(module, "live_few_shot_examples")
    allowed = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for index, example in enumerate(examples, start=1):
        keys = set(example["input"])
        missing = set(REQUIRED_FIELDS) - keys
        extra = keys - allowed
        if missing:
            errors.append(f"live feedback example {index} missing fields: {sorted(missing)}")
        if extra:
            errors.append(f"live feedback example {index} has non-contract fields: {sorted(extra)}")

    import importlib.util

    spec = importlib.util.spec_from_file_location("prompt_templates_contract_check", PROMPT_TEMPLATES)
    if spec is None or spec.loader is None:
        errors.append("cannot import prompt_templates.py")
        return
    module_obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_obj)

    payload = {
        "phase": "bottom",
        "rep_count": 4,
        "knee_angle": "112.5",
        "hip_angle": 101,
        "torso_angle": 22,
        "shin_angle": 28,
        "hip_below_knee": False,
        "confidence_min": 0.82,
        "knee_valgus_ratio": 0.91,
        "depth_history": [130, 112],
        "phase_durations_ms": {"bottom": 200},
    }
    compact = module_obj.compact_squat_state(payload)
    expected_keys = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    if set(compact) != expected_keys:
        errors.append(f"compact_squat_state returned unexpected keys: {sorted(compact)}")
    if compact.get("rep_number") != 4:
        errors.append("compact_squat_state did not map rep_count to rep_number")

    if module_obj.SQUAT_STATE_CONTRACT != schema:
        errors.append("prompt_templates.py loaded schema does not match SQUAT_STATE_SCHEMA.json")
    prompt = module_obj.build_live_feedback_prompt(compact, include_examples=True)
    for field in REQUIRED_FIELDS:
        if field not in prompt:
            errors.append(f"live feedback prompt does not mention expected schema term `{field}`")
    for field in EXCLUDED_MODEL_FIELDS:
        if field in prompt:
            errors.append(f"live feedback prompt includes excluded schema term `{field}`")


def check_live_feedback_policy_call_paths(errors: list[str]) -> None:
    import importlib.util
    import types

    prompt_spec = importlib.util.spec_from_file_location("prompt_templates_policy_check", PROMPT_TEMPLATES)
    benchmark_spec = importlib.util.spec_from_file_location("benchmark_gemma_policy_check", ROOT / "benchmark_gemma.py")
    if prompt_spec is None or prompt_spec.loader is None:
        errors.append("cannot import prompt_templates.py for live feedback policy check")
        return
    if benchmark_spec is None or benchmark_spec.loader is None:
        errors.append("cannot import benchmark_gemma.py for live feedback policy check")
        return

    prompt_module = importlib.util.module_from_spec(prompt_spec)
    prompt_spec.loader.exec_module(prompt_module)
    sys.path.insert(0, str(ROOT))
    sys.modules.setdefault("loguru", types.SimpleNamespace(logger=types.SimpleNamespace(info=lambda *args, **kwargs: None)))
    benchmark_module = importlib.util.module_from_spec(benchmark_spec)
    benchmark_spec.loader.exec_module(benchmark_module)

    setup_ok = {
        "head_visible": True,
        "feet_visible": True,
        "distance_ok": True,
        "centered": True,
        "side_view_ok": True,
    }
    cases = (
        {
            "phase": "bottom",
            "rep_number": 2,
            "knee_angle": 116,
            "hip_angle": 91,
            "torso_angle": 49,
            "shin_angle": 28,
            "hip_below_knee": False,
            "confidence_min": 0.9,
            "knee_valgus_ratio": 0.74,
            "expected_reason_code": "torso_forward",
        },
        {
            "phase": "descending",
            "rep_number": 2,
            "knee_angle": 122,
            "hip_angle": 102,
            "torso_angle": 24,
            "shin_angle": 24,
            "hip_below_knee": False,
            "confidence_min": 0.89,
            "knee_valgus_ratio": 0.79,
            "expected_reason_code": "knees_in",
        },
        {
            "phase": "bottom",
            "rep_number": 3,
            "knee_angle": 108,
            "hip_angle": 101,
            "torso_angle": 22,
            "shin_angle": 30,
            "hip_below_knee": False,
            "confidence_min": 0.88,
            "knee_valgus_ratio": 0.95,
            "expected_reason_code": "depth_shallow",
        },
        {
            "phase": "ascending",
            "rep_number": 4,
            "knee_angle": 96,
            "hip_angle": 94,
            "torso_angle": 20,
            "shin_angle": 26,
            "hip_below_knee": True,
            "confidence_min": 0.91,
            "knee_valgus_ratio": 0.98,
            "expected_reason_code": "good_depth",
        },
    )

    for index, case in enumerate(cases, start=1):
        expected_reason_code = case["expected_reason_code"]
        snapshot = {key: value for key, value in case.items() if key != "expected_reason_code"}
        direct = prompt_module.deterministic_live_feedback_for_squat_state(snapshot)
        legacy = prompt_module.rule_live_feedback(snapshot)
        benchmark_feedback = benchmark_module.rules_backend({"input": {**snapshot, "setup_state": setup_ok}})
        if direct.get("reason_code") != expected_reason_code:
            errors.append(f"canonical live feedback case {index} returned {direct.get('reason_code')}")
        if legacy != direct:
            errors.append(f"rule_live_feedback drifted from canonical live feedback in case {index}")
        if benchmark_feedback != direct.get("feedback"):
            errors.append(f"benchmark_gemma rules_backend bypasses canonical live feedback in case {index}")


def check_server_boundary(errors: list[str]) -> None:
    source = SERVER.read_text(encoding="utf-8")
    if "compact_squat_state" not in source:
        errors.append("server.py does not compact snapshots before model/rules fallback")
    if not re.search(r"model_chat\(compact_snapshot\)", source):
        errors.append("server.py does not call model_chat with compact_snapshot")
    log_event_calls = re.findall(r"log_event\(\{\"ts\": time\.time\(\), \"snapshot\": ([^,}]+)", source)
    if not log_event_calls:
        errors.append("server.py does not log coach events with an inspectable snapshot field")
    for call in log_event_calls:
        if call not in {"compact_squat_state(snapshot)", "compact_snapshot"}:
            errors.append(f"server.py logs non-compact snapshot expression `{call}`")


def check_static_payload(errors: list[str]) -> None:
    source = STATIC_INDEX.read_text(encoding="utf-8")
    match = re.search(r"gemma\.sendSignals\(\{(?P<body>.*?)\n\s*\}\);", source, re.DOTALL)
    if not match:
        errors.append("static/index.html does not expose a gemma.sendSignals object literal")
        return
    body = match.group("body")
    for field in REQUIRED_FIELDS:
        if field not in body:
            errors.append(f"static/index.html live model payload is missing `{field}`")
    for field in EXCLUDED_MODEL_FIELDS:
        if field in body:
            errors.append(f"static/index.html live model payload includes excluded `{field}`")
    offline_source = OFFLINE_EXTRACT.read_text(encoding="utf-8")
    compute_live_match = re.search(r"function computeLive\(.*?return \{(?P<body>.*?)\n\s*\};", offline_source, re.DOTALL)
    if not compute_live_match:
        errors.append("static/offline-extract.html does not expose computeLive return object")
        return
    compute_live_body = compute_live_match.group("body")
    for field in REQUIRED_FIELDS:
        if field == "confidence_min":
            continue
        if field not in compute_live_body:
            errors.append(f"static/offline-extract.html computeLive is missing `{field}`")


def main() -> int:
    errors: list[str] = []
    schema = load_schema(errors)
    if schema:
        check_schema_files(schema, errors)
        check_prompt_policy(schema, errors)
        check_live_feedback_policy_call_paths(errors)
        check_server_boundary(errors)
        check_static_payload(errors)

    if errors:
        sys.stderr.write("State policy contract validation failed:\n")
        for error in errors:
            sys.stderr.write(f"- {error}\n")
        return 1

    sys.stdout.write("State policy contract validation passed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
