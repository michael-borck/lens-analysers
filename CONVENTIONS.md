# Analyser family — conventions (the contract)

The shared shape every `-analyser` package converges on. New members follow this;
existing ones move toward it. Field notes on current divergences live in
[ANALYSER-FAMILY-UX-GOTCHAS.md](ANALYSER-FAMILY-UX-GOTCHAS.md).

Python members get this contract from the **[lens-contract](https://github.com/michael-borck/lens-contract)**
library (`make_manifest`, `add_contract_routes`/`make_app`, `run_contract_subcommands`)
instead of re-implementing the boilerplate. This document stays the language-neutral
spec that `lens-contract` — and non-Python members like cite-sight — implement.

> **Building a new member?** Follow the step-by-step
> **[ADDING-A-MEMBER.md](ADDING-A-MEMBER.md)** checklist — it turns this spec into an
> ordered recipe (naming, layout, deps, port, manifest/api/cli wiring, publish) and
> lists the gotchas already paid for.

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

- Built with **argparse + `lens_contract.run_contract_subcommands`** — the standard
  (not typer/click): stdlib, no extra dep, and the shared helper is the single source
  of truth for the `serve`/`manifest` dispatch. Surface those two in the argparse
  `epilog` so `--help` still documents them.
- Bare positional is "analyse": `name-analyser <path> [--json]`.
- Human-readable summary by default; `--json` prints `model_dump_json(indent=2)` and
  **nothing else** to stdout. Diagnostics/progress/download chatter → stderr only.
- Subcommands: `serve` (HTTP API) and `manifest` (print the capability manifest).
- Optional/costly tiers are opt-in flags (e.g. `--llm`), not on by default.

## HTTP API

Module-level `app` in **`api.py`** (the standard — not `app.py` or `main.py`),
launched by the `serve` subcommand via `uvicorn.run("pkg.api:app", ...)`. Endpoints:

- `GET /health` — status + version  (from `lens_contract.add_contract_routes`)
- `GET /manifest` — the capability manifest  (from `lens_contract.add_contract_routes`)
- `POST /analyse` — multipart file upload, `response_model=<Name>Analysis`

Ports: document 8000, speech 8001, video 8002, records 8003, code 8004,
wordpress 8005, image 8006, git 8007, bundle 8008, conversation 8009, auto 8010,
spreadsheet 8011, site 8012, diagram 8013, provenance 8014, reflection 8015,
revision 8016.

The orchestrator (`auto-analyser`) also serves the contract: its `POST /analyse`
detects a file's format and forwards it to the right member, returning that
member's result with a `routed_to` key.

`fastapi`, `uvicorn[standard]`, `python-multipart`, `rich` are **core**
dependencies (serve + CLI are always available).

**Cross-cutting serving concerns** (opt-in, one consistent implementation in
`lens-contract`, so they don't drift between members):

- **CORS** — `lens_contract.add_cors(app, env_prefix="NAME_ANALYSER")`. Any member
  becomes browser/Electron-frontable via env vars (`NAME_ANALYSER_MODE=desktop` or
  `NAME_ANALYSER_ALLOWED_ORIGINS`); never defaults to `*`. Lean/CLI-only members just
  don't call it.
- **Rate limiting** — `lens_contract.add_rate_limit(app, env_prefix="NAME_ANALYSER")`,
  opt-in via `NAME_ANALYSER_RATE_LIMIT_ENABLED=true`; needs the `lens-contract[ratelimit]`
  extra.

All members have converged on this surface (the 2026-05-25 conversion batch).
One deliberate layout exception: `document-analyser` serves from `api/__init__.py`
(it already had an `api/` routes package), so `document_analyser.api:app` still
resolves; it also keeps per-route slowapi limits instead of the global
`add_rate_limit`, and is the first member wiring the opt-in `add_auth`.

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
