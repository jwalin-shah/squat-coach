# Squat Coach Data Methodology

This document explains what the project data represents, how it was created, and what is intentionally excluded from the public repo.

## Objective

Build an on-device squat coaching system that can:

- detect setup quality and readiness
- extract deterministic squat-state features from pose data
- generate short coaching cues and severity labels
- evaluate coaching quality over repeated sessions

## Data Types Used

- Real session pose records:
  - webcam-captured pose landmarks
  - derived squat-state snapshots (angles, phase, rep number, depth history)
- Synthetic data:
  - generated squat trajectories and synthetic labels for coverage
- Teacher-labeled coaching data:
  - LLM-assisted labeling used to bootstrap/expand training and eval sets
- Evaluation outputs:
  - benchmark summaries and model comparison results

## Collection Workflow

1. Capture side-view squat sessions locally (on-device).
2. Extract pose landmarks and compute deterministic squat-state fields.
3. Export structured session JSON for offline processing.
4. Generate/augment datasets (synthetic and teacher-reviewed).
5. Run evaluation harnesses to compare prompting/model variants.

## Labeling Workflow

- Primary label targets include:
  - coaching feedback text
  - severity (good/warn/bad style buckets)
  - cue timing/speak behavior where applicable
- Label quality is checked with:
  - prompt/eval scripts
  - holdout comparisons
  - guardrail and policy mismatch checks

## Privacy and Public-Safe Rules

This public repo intentionally excludes personal runtime artifacts:

- no personal logs are included
- no exported session event logs are included
- no local model cache/checkpoint artifacts are included
- no machine-specific user paths are retained

The `logs/` directory is scaffold-only (`.gitkeep`), and runtime artifacts are ignored via `.gitignore`.

## Reproducibility Notes

- Scripts in this repo provide the framework and pipeline.
- Any new data you generate should be local and privacy-reviewed before sharing.
- Use environment variables for API credentials; never hardcode secrets.
