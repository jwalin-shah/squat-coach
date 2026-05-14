#!/usr/bin/env python3
"""Static smoke checks for the offline Squat Coach demo."""

from __future__ import annotations

import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HtmlSmokeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.scripts: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "script":
            self.scripts.append(values.get("src"))


def read(path: str) -> str:
    return (ROOT / path).read_text()


def assert_contains(path: str, *needles: str) -> None:
    body = read(path)
    missing = [needle for needle in needles if needle not in body]
    if missing:
        raise AssertionError(f"{path} is missing expected text: {missing}")


def assert_local_scripts(path: str, parser: HtmlSmokeParser) -> None:
    external = [
        src
        for src in parser.scripts
        if src and (src.startswith("http://") or src.startswith("https://"))
    ]
    if external:
        raise AssertionError(f"{path} references external scripts: {external}")


def validate_package() -> None:
    package = json.loads(read("package.json"))
    assert package["type"] == "commonjs"
    assert package["scripts"]["serve"] == "python3 server.py"
    validate_script = package["scripts"]["validate"]
    if validate_script != "python3 scripts/validate_local_gate.py":
        raise AssertionError("package.json validate script must run validate_local_gate.py")
    for dependency in ("@mediapipe/tasks-vision", "vite"):
        if dependency not in package["dependencies"]:
            raise AssertionError(f"package.json is missing {dependency}")


def validate_main_page() -> None:
    parser = HtmlSmokeParser()
    parser.feed(read("static/index.html"))
    assert_local_scripts("static/index.html", parser)
    required_ids = {
        "loading",
        "start-screen",
        "start-btn",
        "video",
        "overlay",
        "feedback-panel",
        "rep-count",
        "phase-panel",
    }
    missing = sorted(required_ids - parser.ids)
    if missing:
        raise AssertionError(f"static/index.html is missing required ids: {missing}")
    assert_contains(
        "static/index.html",
        "LandmarkSmoother",
        "DecisionGate",
        "SessionRecorder",
        "SetupGate",
        "PhaseDetector",
        "FormChecker",
        "FeedbackEngine",
        "/ws/coach",
        "/models/pose_landmarker_lite.task",
        "/mediapipe/vision_bundle.mjs",
    )


def extract_js(source: str, pattern: str, name: str) -> str:
    """Extract one JavaScript definition from the static app.

    Parameters
    ----------
    source : str
        Full ``static/index.html`` source.
    pattern : str
        Regular expression matching the JavaScript definition.
    name : str
        Human-readable definition name for validation failures.

    Returns
    -------
    str
        Matched JavaScript source.
    """
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        raise AssertionError(f"static/index.html is missing extractable {name}")
    return match.group(0)


def validate_phase_detector_regression() -> None:
    """Validate PhaseDetector rep completion against shallow-pause regressions."""
    source = read("static/index.html")
    config = extract_js(source, r"const CONFIG = \{.*?\n\};", "CONFIG")
    phase = extract_js(source, r"const Phase = \{.*?\};", "Phase")
    detector = extract_js(
        source,
        r"class PhaseDetector \{.*?\n\}",
        "PhaseDetector",
    )
    harness = f"""
const assert = require('node:assert/strict');
{config}
{phase}
{detector}

function runSequence(angles) {{
  const detector = new PhaseDetector();
  const results = [];
  for (const angle of angles) results.push(detector.update(angle));
  return results;
}}

const shallowPause = runSequence([170, 164, 154, 146, 139, 139, 139, 145, 156, 162]);
assert.equal(
  shallowPause.some((result) => result.repComplete),
  false,
  'a mid-descent pause above bottomAngle must not complete a rep'
);

const fullRep = runSequence([170, 164, 154, 146, 120, 109, 109, 109, 112, 130, 156]);
assert.equal(
  fullRep.filter((result) => result.repComplete).length,
  1,
  'a descent through bottomAngle followed by standing should complete one rep'
);
"""
    subprocess.run(["node", "-e", harness], cwd=ROOT, check=True)


def validate_offline_page() -> None:
    parser = HtmlSmokeParser()
    parser.feed(read("static/offline-extract.html"))
    assert_local_scripts("static/offline-extract.html", parser)
    required_ids = {
        "video-file",
        "camera-angle",
        "camera-height",
        "sample-fps",
        "min-conf",
        "process-btn",
        "export-btn",
        "preview",
    }
    missing = sorted(required_ids - parser.ids)
    if missing:
        raise AssertionError(f"static/offline-extract.html is missing required ids: {missing}")


def validate_server_contract() -> None:
    assert_contains(
        "server.py",
        "app = FastAPI(title=\"Squat Coach\")",
        "@app.get(\"/models/{filename}\")",
        "@app.get(\"/mediapipe/wasm/{filename}\")",
        "@app.get(\"/mediapipe/{filename}\")",
        "@app.websocket(\"/ws/coach\")",
        "sanitize_live_feedback",
        "deterministic_setup_feedback",
        "app.mount(\"/static\", StaticFiles",
    )


def validate_prompt_contract() -> None:
    assert_contains(
        "prompt_templates.py",
        "LIVE_FEEDBACK_SCHEMA",
        "build_live_feedback_messages",
        "rule_live_feedback",
        "sanitize_live_feedback",
    )


def main() -> None:
    validate_package()
    validate_main_page()
    validate_phase_detector_regression()
    validate_offline_page()
    validate_server_contract()
    validate_prompt_contract()
    print("Static Squat Coach validation passed.")


if __name__ == "__main__":
    main()
