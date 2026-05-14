# CODEX Workpad

## Portfolio Readiness Pass - 2026-05-12

### Scope

- No product functionality changes.
- Added a repeatable static validation command for the offline demo shell.
- Preserved the existing runtime model/camera/Ollama/MLX paths.

### Validation Contract

Run:

```bash
npm run validate
git diff --check
```

### Notes

- `npm run validate` is the authoritative local gate. It runs the executable
  static app, operations contract, and state policy validators, then compiles
  the core Python demo/eval modules.
- `python3 -m unittest discover` currently discovers zero tests and should not be treated as validation evidence.
- Live webcam, MediaPipe model download, and local model inference remain manual demo checks.

## Demo Validation - 2026-05-13

Scope:

- Added `docs/DEMO_VALIDATION.md` to make the local portfolio demo check
  explicit.
- Linked the checklist from `README.md`.
- No product behavior changes.

Validation:

```bash
npm run validate
git diff --check
```

Result: passed.

Gemini secondary review:

- Attempted with Gemini CLI on 2026-05-13 for the scoped validation/docs
  change.
- Blocked by `MODEL_CAPACITY_EXHAUSTED` / HTTP 429 for
  `gemini-3-flash-preview`; no Gemini findings were returned.
