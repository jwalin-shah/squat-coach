# Dependency Audit - 2026-05-19

## Scope

Audited the dependency manifests and local install state for this repo:

- `package.json`
- `package-lock.json`
- `requirements.txt`
- Python and browser imports in committed source
- Setup/runtime scripts: `setup.sh`, `run.sh`, `README.md`

Network access was unavailable during the audit, so registry-backed vulnerability
and outdated-version checks could not be completed.

## Executive Summary

Status: **needs cleanup before relying on reproducible setup**.

Main issues:

1. **No `.venv` exists locally**, even though repo docs and scripts expect one.
2. **`node_modules` is missing**, so the locked npm dependencies are not installed.
3. **`requirements.txt` is underdeclared** for committed training/evaluation scripts.
4. **Python dependencies are not locked**, so installs are not reproducible.
5. **`setup.sh` still depends on network fallbacks** for MediaPipe assets, the pose model, and MLX model weights when local caches are missing.
6. **Security audit could not run** because `npm audit` could not reach `registry.npmjs.org`.

## JavaScript Dependencies

### Direct Dependencies

From `package.json`:

| Package | Declared | Locked | Purpose | Notes |
|---|---:|---:|---|---|
| `@mediapipe/tasks-vision` | `^0.10.32` | `0.10.32` | Browser pose estimation / local WASM assets | Version matches `setup.sh` hard-coded `MEDIAPIPE_VERSION=0.10.32`. |
| `vite` | `^7.3.1` | `7.3.1` | Dev/build tooling | Listed as a production dependency, though the app is served by `server.py`. Consider moving to `devDependencies` if not needed at runtime. |

### Lockfile

- `package-lock.json` uses lockfile version `3`.
- Locked transitive set includes `vite@7.3.1`, `rollup@4.59.0`, `esbuild@0.27.3`, `postcss@8.5.6`, `nanoid@3.3.11`, and platform-specific Rollup/esbuild packages.
- Licenses in the npm lockfile are permissive: mostly `MIT`, with `@mediapipe/tasks-vision` as `Apache-2.0`, `picocolors` as `ISC`, and `source-map-js` as `BSD-3-Clause`.

### Local Install State

`npm ls --all --json` failed with `ELSPROBLEMS`:

- `missing: @mediapipe/tasks-vision@^0.10.32`
- `missing: vite@^7.3.1`

This means the repo has a lockfile, but the local npm install is absent or incomplete.

### Npm Security Audit

`npm audit --json` failed because the registry could not be resolved:

- `getaddrinfo ENOTFOUND registry.npmjs.org`

No npm vulnerability conclusion should be drawn from this run.

## Python Dependencies

### Declared Runtime Requirements

From `requirements.txt`:

| Package | Declared Range | Local Observed Version | Status |
|---|---:|---:|---|
| `fastapi` | `>=0.115.0,<1` | `0.115.14` | Satisfies declared range in the fallback Python environment. |
| `uvicorn[standard]` | `>=0.32.0` | `0.29.0` | Does **not** satisfy declared range in the fallback Python environment. |
| `mlx-lm` | `>=0.21.0` | not importable | Required by `server.py` MLX backend and `setup.sh`. |
| `loguru` | `>=0.7.0` | not importable | Used by `benchmark_gemma.py` and `generate_synthetic_data.py`. |

Important context: `.venv` is missing, so `pip list` and `pip check` ran against the ambient Python environment, not a project-isolated environment.

### Local Python Environment Health

`pip check` reported:

```text
aider-chat 0.82.3 has requirement click==8.1.8, but you have click 8.3.3.
```

This conflict is likely from the ambient environment, but it reinforces that the repo needs an isolated `.venv` before dependency validation is meaningful.

### Underdeclared Python Dependencies

Committed scripts import packages that are not declared in `requirements.txt`:

| Package / Import | Files Using It | Current Declaration |
|---|---|---|
| `google.genai` / `google` | Gemini dataset/review scripts including `generate_gemini_dataset.py`, `judge_model_outputs_with_gemini.py`, `batch_video_vision_review.py`, `calibrate_mediapipe_with_gemini.py`, and related scripts | Not declared. README suggests `pip install -U google-genai` separately. |
| `torch` | `train_gemma_lora.py`, `eval_one_model_clean.py` | Not declared. |
| `datasets` | `train_gemma_lora.py` | Not declared. |
| `peft` | `train_gemma_lora.py`, `eval_one_model_clean.py` | Not declared. |
| `transformers` | `train_gemma_lora.py`, `eval_one_model_clean.py` | Not declared. |

This split may be intentional for hackathon/runtime minimalism, but it is not documented as separate requirement groups. A fresh contributor cannot tell which dependencies are needed for runtime, Gemini labeling, training, and evaluation.

## Reproducibility Findings

### Python Is Not Locked

There is no `requirements.lock`, `pyproject.toml`, `uv.lock`, `poetry.lock`, or similar Python lockfile. The range-based `requirements.txt` can resolve differently over time.

Recommended fix: split and lock dependency groups:

- `requirements.txt` or `requirements-runtime.txt` for local demo/runtime.
- `requirements-dev.txt` for validation and tooling.
- `requirements-training.txt` for `torch`, `datasets`, `peft`, `transformers`.
- `requirements-gemini.txt` for `google-genai` teacher/labeling scripts.
- A generated lockfile if reproducible VM setup matters.

### Npm Runtime Surface Is Small

The browser app imports MediaPipe from locally served files:

- `static/index.html`
- `static/offline-extract.html`

`setup.sh` copies `vision_bundle.mjs` and WASM files from `node_modules/@mediapipe/tasks-vision` when available, with CDN fallback otherwise.

The dependency relationship is clean, but `node_modules` must exist before the offline path works.

### Offline Claim Has Setup-Time Caveats

The app can run offline after setup, but setup still pulls from the network when local artifacts are absent:

- MediaPipe WASM and JS bundle fallback to jsDelivr.
- Pose landmarker model downloads from Google Storage.
- MLX model weights can download from Hugging Face via `mlx_lm.load()`.

That is consistent with the README's "run once with internet, then go offline" model, but it is worth documenting explicitly in any demo checklist.

## Recommended Actions

1. **Create a clean local environment and reinstall.**
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `python3 -m pip install -U pip`
   - `python3 -m pip install -r requirements.txt`
   - `npm ci`

2. **Fix the Python dependency grouping.**
   - Keep runtime dependencies minimal.
   - Move Gemini, training, and evaluation dependencies into named extras or separate requirement files.
   - Update README setup commands to use the right file for each workflow.

3. **Add a Python lock strategy if the demo/VM needs repeatability.**
   - For a lightweight repo, `pip-tools` or `uv` would be enough.
   - Lock at least the runtime environment used for live demos.

4. **Move `vite` to `devDependencies` if it is only build/dev tooling.**
   - The local server path is `python3 server.py`; the browser app does not appear to need Vite at runtime.

5. **Run registry-backed audits when network is available.**
   - `npm audit`
   - `npm outdated`
   - Python vulnerability/outdated scan using the chosen project environment.

6. **Make offline asset status explicit.**
   - Add a check command or setup summary that reports whether MediaPipe WASM, `vision_bundle.mjs`, `models/pose_landmarker_lite.task`, and MLX model weights are already cached.

## Commands Run

```bash
sed -n '1,220p' ~/.agent-rules/GLOBAL.md
sed -n '1,220p' CLAUDE.md
sed -n '1,240p' package.json
sed -n '1,220p' requirements.txt
node -e "const p=require('./package-lock.json'); console.log(JSON.stringify({lockfileVersion:p.lockfileVersion, packageManager:p.packageManager, root:p.packages&&p.packages['']}, null, 2))"
npm --version
node --version
python3 --version
npm ls --all --json
npm audit --json
python3 -m pip list --format=json
python3 -m pip check
python3 - <<'PY'
mods=['fastapi','uvicorn','mlx_lm','loguru']
for m in mods:
    try:
        mod=__import__(m)
        print(f'{m}: {getattr(mod, "__version__", "installed-version-unknown")}')
    except Exception as exc:
        print(f'{m}: NOT IMPORTABLE ({type(exc).__name__}: {exc})')
PY
rg -n "from |import |require\\(|@mediapipe|vite|fastapi|uvicorn|mlx|loguru" -g '*.py' -g '*.html' -g '*.js' -g '*.ts' .
```

Tool versions observed:

- `npm 11.12.1`
- `node v26.0.0`
- `Python 3.12.8`

## Audit Limitations

- Network was restricted, so npm advisory and outdated checks failed.
- No `.venv` existed, so Python install-state checks used the ambient Python environment.
- No Python lockfile exists, so transitive Python dependency versions for a fresh install could not be audited from repo files alone.
