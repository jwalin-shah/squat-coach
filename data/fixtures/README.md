# Data Fixtures

This directory is the only tracked path under `data/`.

Use it for small, deterministic fixtures that are synthetic or explicitly
approved for public release. Runtime outputs, local session exports, generated
teacher labels, generated videos, evaluation summaries, and model caches must
stay in ignored local paths such as `data/results/`, `data/raw_sessions/`,
`data/generated_videos/`, or `.runtime/logs/`.

Before adding a fixture, document its purpose, source, and why it contains no
private workout video, raw pose stream, or biometric material.
