# lens-contract: A Shared Contract-Surface Package for the Analyser Family (Design)

**Date:** 2026-05-24
**Author:** Dr Michael Borck (with Claude)
**Scope:** Extract the contract boilerplate duplicated across the Python `-analyser` members into one small library, `lens-contract`, without merging the repos into a monorepo. `conversation-analyser` is the pilot adopter.
**Status:** Pilot implemented (lens-contract + conversation-analyser converted, tests green). Awaiting review before rolling out to the remaining members.

---

## 1. Purpose

Every Python member of the family re-implements the same contract surface by hand.
A scan of the workspace on 2026-05-24:

- **11× `manifest.py`** — each with an identical `_version()` try/except + a `MANIFEST` dict of the same seven keys.
- **11× `cli.py`** — each with the same `serve` / `manifest` subcommand dispatch and `uvicorn.run(...)` launcher.
- **6× `api.py`** — each with the same `GET /health`, `GET /manifest`, and the `POST /analyse` upload→tempfile→cleanup dance.

This is the contract from `CONVENTIONS.md` rendered as copy-paste. A contract change
(e.g. adding a manifest field, changing the health payload) is **11 edits across 11
repos** today. The rule of three is long past.

`lens-contract` is a tiny library that owns that surface, so contract changes become
**one release** that members pick up on their normal cadence. It is **infrastructure,
not an analyser** (`role: library`): it never appears in the family table and is not
auto-routable.

## 2. Non-goals

- **Not a monorepo.** The repos stay independent (reconfirmed 2026-05-24). This is the
  middle path: share the *contract surface* via a dependency, keep everything else
  separate. See §9.
- **Not a shared "NLP/utils" grab-bag.** Only the contract boilerplate moves. Domain
  logic, analysers, and `document_analyser.extract_text` stay where they are
  (`CONVENTIONS.md` → "share domain logic, not library calls").
- **Not for non-Python members.** `cite-sight` (TypeScript) keeps its `manifest.json`
  and serves the contract itself. `lens-contract` is the *Python* implementation of
  what `CONVENTIONS.md` specifies in prose, not a second source of truth.
- **Not a forced abstraction.** The human-readable CLI output (`rich`), the analyse
  flags, and the result models are bespoke per analyser and stay that way. `rich` is
  not even a dependency of `lens-contract`.

## 3. What moves vs. what stays

| Moves into `lens-contract` | Stays bespoke in each repo |
|---|---|
| `_version()` + `MANIFEST` schema → `make_manifest(...)` | `analyse()` business logic |
| `GET /health`, `GET /manifest` → `add_contract_routes(app, MANIFEST)` | `_print_human()` (totally different per analyser) |
| `POST /analyse` plumbing (path-only) → `make_app(MANIFEST, analyse)` | the rich analyse-CLI flags (`--llm`, `--parse-mode`, …) |
| upload→tempfile→cleanup → `upload_tempfile(content, filename)` | the `produces` Pydantic model + `response_model` |
| `serve` + `manifest` dispatch → `run_contract_subcommands(...)` | the bare-positional analyse path |

## 4. Public API

```python
from lens_contract import (
    Manifest, make_manifest,            # manifest.py
    add_contract_routes, make_app, upload_tempfile,   # api.py
    run_contract_subcommands,           # cli.py
)
```

- `make_manifest(*, name, accepts, produces, extensions=(), role="analyser", auto_routable=True, **extra) -> Manifest`
  — resolves `version` from installed metadata (falls back to `"0.0.0"` instead of
  raising). `**extra` carries `repo`/`pypi` for non-standard members.
- `add_contract_routes(app, manifest)` — wires the two constant routes; caller owns
  `POST /analyse`.
- `make_app(manifest, analyse)` — full app for the common path-only case.
- `upload_tempfile(content, filename)` — context manager: spool an upload to a temp
  file with the right suffix, yield the path, always clean up.
- `run_contract_subcommands(manifest, *, app_path, default_port, env_prefix, argv=None) -> bool`
  — handles `manifest` + `serve`; returns `False` so the caller parses its own analyse
  args.

## 5. Two adoption shapes

**Common case** (analyse takes only a path, no extra form fields):

```python
app = make_app(MANIFEST, lambda path: NameAnalyser().analyse(path))
```

**Custom case** (extra form fields and/or a typed `response_model`) — this is what the
pilot uses, because its `/analyse` takes an `llm` toggle:

```python
app = FastAPI(title=MANIFEST["name"], version=MANIFEST["version"])
add_contract_routes(app, MANIFEST)

@app.post("/analyse", response_model=ConversationAnalysis)
async def analyse(file: UploadFile = File(...), llm: bool = Form(False)):
    content = await file.read()
    if not content:
        raise HTTPException(422, "Empty file")
    with upload_tempfile(content, file.filename) as path:
        ...
```

Having the pilot exercise the *custom* path on purpose proves the scaffolding is
flexible, not just a one-shape wrapper.

## 6. Manifest-table non-pollution

`lens-analysers/scripts/generate_family_table.py` discovers members via
`WORKSPACE.glob("*/**/manifest.py")` and reads each module's `MANIFEST` constant.
`lens_contract/manifest.py` deliberately defines **only `make_manifest`/`Manifest`,
no module-level `MANIFEST`**, so `_load_manifest` returns `None` and the generator
skips it. A regression test (`test_manifest_module_has_no_constant`) locks this in.

## 7. Packaging & distribution

- `hatchling`, `requires-python >=3.10` (looser than members, so all can depend on it),
  `readme = "README.md"`.
- Core deps per `CONVENTIONS.md`: `fastapi`, `uvicorn[standard]`, `python-multipart`.
  No `rich`, no pydantic pin (comes via fastapi).
- Published to PyPI like the rest; members pin `lens-contract>=0.1.0`.
- **Local dev across sibling repos:** members add
  `[tool.uv.sources] lens-contract = { path = "../lens-contract", editable = true }`.
  uv strips this from the built wheel, so the published artifact keeps the plain PyPI
  pin — the workspace gets the local checkout, consumers get PyPI.
- Versioning: treat the manifest schema + route shapes as public API; semver strictly,
  since every member depends on it.

## 8. Pilot result (conversation-analyser)

- `manifest.py`: 31 → 21 lines (the `_version()` helper and the literal dict gone).
- `api.py`: hand-written `/health`, `/manifest`, the `version()` plumbing, and the
  tempfile dance removed; only the bespoke `/analyse` remains.
- `cli.py`: the `serve`/`manifest` dispatch and the `_serve` launcher (and the now-unused
  `json`/`os` imports) removed.
- Verification: `lens-contract` ships 11 tests (green); the converted `manifest.py`
  builds the real `ConversationAnalysis` manifest through `make_manifest`; all three
  converted files compile. The pilot's own `test_api.py` / `test_cli_smoke.py` /
  `test_manifest.py` should be run once its env is reprovisioned.

## 9. Trade-offs & alternatives

- **Hub dependency.** This adds the one coupling the independent-repos setup avoided:
  every member now depends on `lens-contract`. Accepted because the surface is small
  and stable, and *propagating contract changes is the entire point*. Mitigation: strict
  semver, a frozen manifest schema, a thorough test suite in `lens-contract` itself.
- **vs. monorepo.** Rejected (again) — the family has only ~2 genuine cross-repo code
  edges, mixed languages (Python + TS + JS apps), and high migration cost. A shared
  contract package captures ~80% of the "one atomic contract change" benefit without
  the migration.
- **vs. a cookiecutter/template.** A template removes the *typing* but not the *drift*:
  copies still diverge. A library is the only option where one change reaches all
  members.
- **vs. doing nothing.** Viable, but every future contract tweak stays an 11-repo chore.

## 10. Rollout

1. ✅ Build `lens-contract`; convert `conversation-analyser` as pilot.
2. Review this spec; confirm the API surface.
3. Migrate a second, *simpler* member that uses the **common** `make_app` path (e.g.
   `records-analyser` or `git-analyser`) to validate that shape too.
4. Roll out to the remaining Python members opportunistically (when each is next
   touched), not as a big-bang.
5. Update `CONVENTIONS.md` to reference `lens-contract` as the canonical implementation
   of the contract for Python members.
```
