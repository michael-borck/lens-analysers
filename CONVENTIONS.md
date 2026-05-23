# Analyser family — conventions (the contract)

The shared shape every `-analyser` package converges on. New members follow this;
existing ones move toward it. Field notes on current divergences live in
[ANALYSER-FAMILY-UX-GOTCHAS.md](ANALYSER-FAMILY-UX-GOTCHAS.md).

## Naming

- **`-analyser`** = a reusable engine (this contract). British spelling in class
  names where practical (`<Name>Analyser`).
- **`-lens`** = a bespoke app/product built on the engines. Never use `-lens` for an
  engine.
- Package `name-analyser`, import module `name_analyser`, classes
  `NameAnalyser` / `NameAnalysis`.

## Python API

```python
from name_analyser import NameAnalyser, NameAnalysis
result = NameAnalyser().analyse(input)   # returns a pydantic model
print(result.model_dump_json(indent=2))
```

## CLI

- Bare positional is "analyse": `name-analyser <path> [--json]`.
- Human-readable summary by default; `--json` prints `model_dump_json(indent=2)` and
  **nothing else** to stdout. Diagnostics/progress/download chatter → stderr only.
- Subcommands: `serve` (HTTP API) and `manifest` (print the capability manifest).
- Optional/costly tiers are opt-in flags (e.g. `--llm`), not on by default.

## HTTP API

Module-level `app` in `api.py`/`app.py`, launched by the `serve` subcommand via
`uvicorn.run("pkg.api:app", ...)`. Endpoints:

- `GET /health` — status + version
- `GET /manifest` — the capability manifest
- `POST /analyse` — multipart file upload, `response_model=<Name>Analysis`

Ports: document 8000, speech 8001, video 8002, records 8003, code 8004,
wordpress 8005, image 8006, git 8007, bundle 8008, conversation 8009.

`fastapi`, `uvicorn[standard]`, `python-multipart`, `rich` are **core**
dependencies (serve + CLI are always available).

## Capability manifest

Every member exposes a `MANIFEST` constant, a `manifest` CLI subcommand, and a
`GET /manifest` endpoint, with these fields:

| Field | Meaning |
|---|---|
| `name` | package name |
| `version` | installed version |
| `role` | `analyser` or `orchestrator` |
| `accepts` | content kinds it handles (e.g. `["code"]`) |
| `extensions` | file extensions it claims for auto-routing (`[]` if none) |
| `auto_routable` | may `auto-analyser` route to it automatically? |
| `produces` | result model name |
| `repo`, `pypi` | optional; for non-Python members. `pypi: false` = not on PyPI |

`auto-analyser` builds its routing table from these (HTTP/CLI discovery), excluding
`auto_routable: false`, with a static `_ROUTES` map as the offline fallback. See
ADR 0001 in the auto-analyser repo.

### Membership is the contract, not the language

A family member is anything that speaks the contract (HTTP `/analyse` + `/manifest`
+ `/health`, and/or the CLI), regardless of implementation language. Don't
reimplement an existing engine in another language to "join the family" — expose the
one you have. Members declare their manifest one of two ways, both read by
`scripts/generate_family_table.py`:

- **Python members** — a `MANIFEST` constant in `manifest.py`.
- **Language-neutral members** — a `manifest.json` at the repo root.

`cite-sight` is the first non-Python member: a TypeScript monorepo whose
`cite-sight-core` engine is served by `cite-sight-server`, which exposes the
contract routes; it ships a `manifest.json` (`auto_routable: false`, `pypi: false`).

## Composition & shared primitives

- **Text extraction** (binary → text) has one home: `document_analyser.extract_text()`.
  Other analysers import it; do not re-implement pdfplumber/markitdown.
- **Share domain logic, not library calls.** No shared "NLP module" — import
  textstat/VADER/etc. directly. Extract a shared util only at the rule of three.

## Packaging

- hatchling build backend; `pyproject.toml` with `readme = "README.md"` (so the PyPI
  page renders), `[project.scripts]` entry point, optional-dependency extras for heavy
  tiers (`[llm]`, `[embeddings]`, …).
- A CLI smoke test per package (run against a fixture, assert exit 0 + valid JSON).
