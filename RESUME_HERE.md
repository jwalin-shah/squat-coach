# Resume Here

## Project Summary

Squat Coach is a local, on-device realtime squat feedback demo. The core loop is:

```text
webcam video -> MediaPipe Pose -> deterministic squat state -> local coaching model or rule fallback -> coaching UI/audio
```

The browser owns webcam capture, pose estimation, setup gating, squat-state extraction, rep counting, recording, and local JSON/video export. The Python server serves the app and optionally backs `/ws/coach` with a local model runtime such as MLX or Ollama. The product goal is private, low-latency coaching that still works after dependencies and model assets have been installed.

Key docs:

- `README.md` - product direction, setup, architecture, and run instructions.
- `docs/DEMO_VALIDATION.md` - automated and manual validation checklist.
- `docs/OPERATIONS_CONTRACT.md` - runtime boundary, state contract, privacy rules, and validation hook.
- `SQUAT_STATE_SCHEMA.md` / `SQUAT_STATE_SCHEMA.json` - model-facing compact state contract.

## Current State

Status: **SHIPPED**.

This repo should be treated as a shipped portfolio/demo artifact, not an active implementation queue. The shipped surface includes the local webcam pose pipeline, setup gate, automatic setup-to-tracking handoff, rep counting, angle computation, session export, local coaching websocket path, deterministic fallback behavior, and validation scripts.

The important invariant is the local runtime boundary:

```text
video -> MediaPipe -> deterministic squat state -> local model -> coaching JSON
```

Do not resume broad feature work by default. Preserve privacy and demo stability: no personal session exports, runtime logs, generated videos, model caches, API keys, or biometric raw data should be committed. Runtime output belongs in ignored local paths such as `.runtime/` or ignored `data/` subdirectories; only approved deterministic fixtures belong under `data/fixtures/`.

Useful validation commands if touching the repo:

```bash
npm run validate
npm run ops:validate
npm run state:validate
git diff --check
```

## What Would Trigger Resumption

Resume work only for a concrete maintenance or product reason, such as:

- A shipped demo path regresses: local server fails, browser startup breaks, setup gate no longer reaches tracking, rep count no longer increments, export fails, or `/ws/coach` breaks.
- A dependency, browser, MediaPipe asset, or local model-runtime change breaks the current install/run workflow.
- The compact squat-state contract intentionally changes and runtime, fixtures, docs, and validation need to be realigned.
- A privacy or repo-hygiene issue is found, especially accidental tracked logs, session exports, videos, model caches, API keys, or raw biometric data.
- A maintainer explicitly decides to reopen the training/eval track for audited real-session labels or a fine-tuned local Gemma student model.
- A new portfolio/demo requirement is accepted with clear acceptance criteria and a validation command.

If none of those are true, leave the repo alone. The expected handoff posture is: shipped, stable, documented, and resumed only when there is a specific regression, maintenance need, or explicitly approved next milestone.
