# Adding a new analyser to the family

A step-by-step checklist for building a new `-analyser` engine that's consistent
with the rest of the family from day one.

- **[CONVENTIONS.md](CONVENTIONS.md)** is the contract spec (the *what*).
- **[lens-contract](https://github.com/michael-borck/lens-contract)** is the shared
  library that implements the contract surface (the *how*).
- This file is the *recipe* — the steps in order, plus the gotchas we've already paid for.

The fastest reliable path: follow this list. (Copying an existing member also works,
but copy a recently-converted one — e.g. `git-analyser` for a simple file-upload
analyser, `speech-analyser` for one with CORS + rate-limit — not an old one.)

---

## 0. Decide what it is

- **Engine (`-analyser`)** vs app (`-lens`). This guide is for engines.
- **auto-routable** (a file extension implies the analysis, e.g. `.csv`) vs
  **explicit-only** (`auto_routable=False` — the content interpretation isn't implied
  by the extension, e.g. a conversation).
- **role**: `"analyser"` (default) or `"orchestrator"` (routes/aggregates, like
  auto-analyser / bundle-analyser).

## 1. Naming & layout

- Package `name-analyser`, import module `name_analyser`, classes
  `NameAnalyser` / `NameAnalysis` (British spelling).
- Layout (prefer the `src/` layout for new members):

  ```
  name-analyser/
    pyproject.toml
    LICENSE            # MIT, mirror an existing member
    README.md
    src/name_analyser/
      __init__.py      # exports NameAnalyser, NameAnalysis, MANIFEST
      manifest.py
      api.py
      cli.py
      ...              # the analyser logic
    tests/
  ```

  > **Gotcha:** if your HTTP layer needs a `api/` **package** (multiple route
  > modules), put the FastAPI app in `api/__init__.py` — you can't have both an
  > `api.py` module and an `api/` package. The launch string stays `name_analyser.api:app`.

## 2. pyproject.toml

```toml
[project]
name = "name-analyser"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "lens-contract>=0.2.0",          # or lens-contract[ratelimit]>=0.2.0 if you use add_rate_limit
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.9",
    "rich>=13.7.0",
    # ... your own deps
]

[project.scripts]
name-analyser = "name_analyser.cli:main"

# Local dev: resolve lens-contract from the sibling checkout. uv strips this from
# the published wheel (the PyPI pin remains).
[tool.uv.sources]
lens-contract = { path = "../lens-contract", editable = true }

[tool.hatch.build.targets.wheel]
packages = ["src/name_analyser"]
```

- Pin **`lens-contract>=0.2.0`** (that's the floor for `add_cors`/`add_rate_limit`).
  Use the **`[ratelimit]`** extra *only* if you call `add_rate_limit` (it pulls slowapi).

## 3. manifest.py

```python
from lens_contract import make_manifest

MANIFEST = make_manifest(
    name="name-analyser",
    accepts=["..."],
    produces="NameAnalysis",
    extensions=[".ext"],     # [] for explicit-only
    auto_routable=True,      # False for explicit-only
    # role="orchestrator",   # only for orchestrators
)
```

Don't hand-roll a `MANIFEST` dict or a `_version()` helper — `make_manifest` does both.

## 4. api.py

**Common case** — `analyse(path)` takes only a file, no extra fields:

```python
from lens_contract import make_app, add_cors
from name_analyser import NameAnalyser
from name_analyser.manifest import MANIFEST

app = make_app(MANIFEST, lambda path: NameAnalyser().analyse(path))
add_cors(app, env_prefix="NAME_ANALYSER")
```

**Custom case** — extra form fields, a typed `response_model`, or a long pipeline:

```python
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from lens_contract import add_contract_routes, add_cors, add_rate_limit, upload_tempfile

app = FastAPI(title=MANIFEST["name"], version=MANIFEST["version"])
add_contract_routes(app, MANIFEST)            # GET /health + GET /manifest
add_cors(app, env_prefix="NAME_ANALYSER")     # every member gets CORS
# add_rate_limit(app, env_prefix="NAME_ANALYSER")  # opt-in; needs the [ratelimit] extra

@app.post("/analyse", response_model=NameAnalysis)
async def analyse(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Empty file")
    with upload_tempfile(content, file.filename) as path:
        # For a slow/heavy pipeline, offload so GET /health stays responsive:
        #   return await run_in_threadpool(NameAnalyser().analyse, path)
        return NameAnalyser().analyse(path)
```

- **Every HTTP member calls `add_cors`** so any can front a browser/Electron app via
  env (`NAME_ANALYSER_MODE=desktop` or `NAME_ANALYSER_ALLOWED_ORIGINS`).
- `add_rate_limit` actually enforces (via `SlowAPIMiddleware`) — a bare `slowapi`
  `Limiter` with no middleware/decorators is a silent no-op (several members had that bug).

## 5. cli.py

```python
import argparse, sys
from pathlib import Path

def main() -> None:
    from lens_contract import run_contract_subcommands
    from name_analyser.manifest import MANIFEST

    if run_contract_subcommands(
        MANIFEST,
        app_path="name_analyser.api:app",
        default_port=80NN,                 # your assigned port (see step 6)
        env_prefix="NAME_ANALYSER",
    ):
        return  # handled `serve` or `manifest`

    parser = argparse.ArgumentParser(
        prog="name-analyser",
        epilog="subcommands: `serve` (HTTP API), `manifest` (capability manifest)",
    )
    parser.add_argument("file", type=Path, help="file to analyse")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    ...
```

- **argparse + `run_contract_subcommands`** — the family standard, not typer/click.
- Bare positional = analyse (no explicit `analyse` subcommand). Human summary by
  default; `--json` prints `model_dump_json(indent=2)` and nothing else; diagnostics → stderr.
- Surface `serve`/`manifest` in the `epilog` so `--help` documents them.

## 6. Port

Claim the next free port and add it to the registry in CONVENTIONS.md.
Current: 8000–8016 are taken (revision-analyser is 8016), so the next is **8017**.

## 7. Tests

At minimum a smoke test (the family pattern):

- `TestClient`: `GET /health` (status/version/uptime), `GET /manifest`,
  `POST /analyse` on a fixture (+ empty file → 422).
- CLI: `--version`, bare-positional analyse on a fixture, missing file → non-zero.

## 8. Ship

1. `uv venv && uv pip install -e '../lens-contract' -e '.[dev]'` then `pytest`.
2. `uv build` and `uvx twine upload dist/*` (or your publish flow).
3. `gh repo create michael-borck/name-analyser --public --source=. --push`.
4. Regenerate the umbrella table: `python lens-analysers/scripts/generate_family_table.py`
   (it auto-discovers your manifest + reads the version from your pyproject).

---

## Compose, don't reimplement

Before adding analysis logic, check whether the family already has it:

- **binary → text**: `from document_analyser import extract_text` (don't re-add pdfplumber/markitdown).
- **audio → transcript/speech metrics**: compose with **speech-analyser** (word-level since 0.5.0).
- **per-image quality/caption/OCR**: compose with **image-analyser**.

Reimplementing one of these is exactly the drift this family was cleaned up to remove.

## Gotchas we've already paid for

- **`lens-contract>=0.2.0`** is the floor — anything using `add_cors`/`add_rate_limit`
  on an older pin can resolve a version without them and crash on import.
- **`[ratelimit]` extra** only when you actually call `add_rate_limit`.
- **`api.py` vs `api/` package** collide — use `api/__init__.py` if you have a routes package.
- **Don't break consumers' launch path.** If a `-lens` app or another member launches
  you by module path (e.g. `name_analyser.api:app`), keep it stable or update the
  consumer in the same change (renaming `main.py`→`api` broke document-lens until fixed).
- **The orchestrators (`auto`/`bundle`) shell out to members bare-positional**
  (`name-analyser <file> --json`) or via HTTP `/analyse` — so the bare-positional CLI
  isn't optional.
