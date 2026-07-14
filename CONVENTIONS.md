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
- **`-bench`** = a measurement/benchmark product that *evaluates* approaches rather
  than analysing artefacts. `assessment-bench` is the first: it runs a cohort
  through competing assessment arms (pure-LLM marking vs `assessment-lens`'s
  signal-based observations) and reports consistency + agreement-vs-human stats.
  A bench **measures; it never marks** — the scores an LLM arm emits are data
  under test, not grades for students. It declares `role="bench"`,
  `auto_routable=False` (invoked deliberately, never routed to by file type).
  - Both `-lens` and `-bench` *consume* the family rather than analyse artefacts,
    but they differ in family-table visibility: a bench ships a `manifest.py`
    (and an optional `serve` HTTP face for a UI), so it speaks the contract and
    appears in the table; a pure-CLI lens like `assessment-lens` has no manifest
    and stays out of it. Manifest presence means "I have a discoverable HTTP
    face," not "I'm an analyser."
- Package `name-analyser`, import module `name_analyser`, classes
  `NameAnalyser` / `NameAnalysis`.

## Python API

Every member exposes the **same canonical surface** from its top-level package,
all listed in `__all__`:

```python
from name_analyser import NameAnalyser, NameAnalysis, analyse, MANIFEST, __version__

result = NameAnalyser().analyse(input)   # the class…
result = analyse(input)                   # …or the module-level convenience fn
print(result.model_dump_json(indent=2))   # result is a pydantic model where one exists
```

- **`NameAnalyser`** — the engine class with `.analyse(...)`. Members that predate
  this (e.g. document-analyser, git-analyser) expose a thin facade class that wraps
  their existing function; the wrap adds no behaviour.
- **`analyse(input, …)`** — a module-level convenience function mirroring the class's
  `.analyse` signature. `analyse(x)` == `NameAnalyser().analyse(x)`.
- **`NameAnalysis`** — the pydantic result model. Where the internal model has a
  different name it is exported under that name *and* aliased to `NameAnalysis`
  (e.g. speech-analyser exports `AudioAnalysis` + `SpeechAnalysis`). A few members
  whose `.analyse` historically returns a plain `dict` keep doing so — the model is
  still exported as the documented result type.
- **`MANIFEST`**, **`__version__`** — always exported.
- The base exception (`NameAnalyserError`) is exported where one exists.

Orchestrators (auto-analyser, bundle-analyser) follow the same surface: `analyse()`
+ `MANIFEST` + `__version__`, plus their primary class (`Router`/`AutoAnalyser`,
`BundleAnalyser`). document-analyser additionally keeps re-exporting the family's
canonical text extractor, `extract_text`.

> The *contract* surfaces are the CLI, HTTP, and MANIFEST (below); the Python
> surface above is the in-process convenience. Input types legitimately vary by
> modality (path, text, bytes, URL) — the *names* are uniform, the argument is each
> member's natural input.

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
revision 8016, thematic 8017.

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
| `role` | `analyser`, `orchestrator`, or `bench` |
| `accepts` | content kinds it handles (e.g. `["code"]`) |
| `extensions` | file extensions it claims for auto-routing (`[]` if none) |
| `auto_routable` | may `auto-analyser` route to it automatically? |
| `produces` | result model name |
| `repo`, `pypi` | optional; for non-Python members. `pypi: false` = not on PyPI |

`auto-analyser` builds its routing table from these (HTTP/CLI discovery), excluding
`auto_routable: false`, with a static `_ROUTES` map as the offline fallback. See
ADR 0001 in the auto-analyser repo.

**One extension, one auto-route** — when two members read the same extension, the
*default* interpretation owns auto-routing and the other is explicit-only. The
settled cases (re-confirmed 2026-06-11): `.xlsx`/`.xls` auto-route to
**records-analyser** (data values); **spreadsheet-analyser** (formula logic) is
explicit. `.docx` auto-routes to **document-analyser** (prose);
**revision-analyser** (tracked changes) and **provenance-analyser** (metadata) are
explicit. `.html`/`.css`/`.js` auto-route to **code-analyser** (source files);
**site-analyser** (a deployed site) is explicit. A cascade rule (à la
image→diagram) is the upgrade path if a default member ever emits a trigger
signal — e.g. records-analyser flagging formulas to cascade into
spreadsheet-analyser — but no such trigger exists today.

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
