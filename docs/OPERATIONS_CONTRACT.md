# Squat Coach Operations Contract

This contract keeps the repo handoff small, repeatable, and aligned with the
current on-device architecture.

## Runtime Boundary

The runtime boundary remains:

```text
video -> MediaPipe -> deterministic squat state -> local model -> coaching JSON
```

The browser owns webcam capture, pose estimation, setup gating, squat-state
extraction, and offline export. The Python server owns local static serving and
optional local model coaching through `/ws/coach`. Runtime code must not depend
on cloud services after setup assets and models are installed.

## State Contract

`SQUAT_STATE_SCHEMA.md` is the source of truth for the model-facing compact
state. Runtime, offline export, teacher data, and model evaluation work should
reduce live coaching examples to the v1 fields documented there before using
them as model inputs.

The required v1 fields are:

- `phase`
- `rep_number`
- `knee_angle`
- `hip_angle`
- `torso_angle`
- `shin_angle`
- `hip_below_knee`
- `confidence_min`

`knee_valgus_ratio` is optional for v1. Raw landmarks, full coordinate streams,
camera metadata, and user-specific metadata are debugging or offline artifacts,
not model-facing contract fields.

## Data And Privacy Rules

Public commits may include source, docs, deterministic scripts, and scaffold
directories. Public commits must not include personal session exports, runtime
logs, generated videos, model caches, API keys, or files that can reconstruct a
person's workout video or biometrics beyond the compact state needed for
debugging.

Generated data should be treated as local until it is intentionally reviewed for
public release. Gemini or other cloud teacher outputs belong in local data
directories unless a maintainer explicitly approves sharing them.

## Validation Hook

Run this lightweight operations check before handing off repo-ops or schema
changes:

```bash
npm run ops:validate
```

Equivalent Make target:

```bash
make validate-ops
```

The hook is intentionally narrow. It verifies that the required docs exist, the
compact state fields remain documented, and the expected local setup/serve
scripts are still exposed.
