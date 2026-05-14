# Demo Validation

This checklist proves the portfolio demo path without changing product behavior.
It separates static validation from manual camera/model checks so a reviewer can
tell what is automated and what still needs a live browser.

## Automated Checks

Run from the repo root:

```bash
npm run validate
```

Expected result:

- Static app validation passes.
- Operations and state-policy contract validation pass.
- Core Python demo/eval modules compile.

Before PR handoff, also run the repository hygiene check required by the work
pack:

```bash
git diff --check
```

Expected result: no whitespace errors are present in the diff.

## Local Runtime Setup

Install dependencies and restore local MediaPipe assets:

```bash
python3 -m pip install -r requirements.txt
npm install
bash setup.sh
```

Start the local server:

```bash
python3 server.py
```

Open:

```text
http://localhost:8420
```

After `setup.sh` has copied MediaPipe assets and downloaded the pose model, the
main demo should not depend on a CDN at runtime.

## Manual Browser Smoke

Use a browser with webcam permission:

1. Load `http://localhost:8420`.
2. Confirm the loading screen reaches the start screen.
3. Click start and grant camera permission.
4. Confirm the video preview renders.
5. Stand in side view until the setup gate reports ready.
6. Confirm phase indicators update when squatting.
7. Confirm rep count increments after a complete squat.
8. Click `Start Rec`, perform a short set, click `Stop Rec`, then export JSON.
9. Confirm no raw video or pose data leaves the local machine during the demo.

## Optional Local Model Smoke

For deterministic fallback without an LLM:

```bash
COACH_BACKEND=ollama OLLAMA_BASE_URL=http://127.0.0.1:11434 python3 server.py
```

If Ollama is not running, the websocket path falls back to rule-based coaching.
For MLX-backed local inference, run with a local model path:

```bash
COACH_BACKEND=mlx \
MLX_MODEL=/absolute/path/to/local-mlx-model \
MLX_ADAPTER_PATH=/absolute/path/to/local-mlx-adapter \
python3 server.py
```

Expected result:

- Setup messages are deterministic and local.
- Live cues use one of the canonical cue strings.
- `.runtime/logs/coach_events.jsonl` records snapshots and emitted cues.

## Known Limits

- Webcam framing, MediaPipe rendering, and speech output remain manual checks.
- First-time `setup.sh` downloads the pose model; offline operation applies
  after dependencies and model assets are installed.
- Fine-tuned Gemma student-model validation is out of scope for the static app
  check and belongs to the training/eval workflow.
