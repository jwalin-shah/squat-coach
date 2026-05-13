#!/usr/bin/env python3
"""Static smoke checks for the offline Squat Coach demo."""

from __future__ import annotations

import json
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
    assert package["scripts"]["validate"] == "python3 scripts/validate_static_app.py"
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
    validate_offline_page()
    validate_server_contract()
    validate_prompt_contract()
    print("Static Squat Coach validation passed.")


if __name__ == "__main__":
    main()
