# Analyser family — UX consistency gotchas

Field notes from integrating the family into an external consumer (a university
assignment-grading toolkit) on 2026-05-21. Every item was reproduced against the
installed packages, not inferred from source. The theme: the family is close to a
consistent contract but a handful of divergences make it harder to treat the tools
interchangeably — which is the whole promise of a "family".

Versions exercised: `code-analyser 1.0.3`, `git-analyser 0.2.1`,
`wordpress-analyser 0.2.2`, `document-analyser 0.1.2`, `auto-analyser 0.2.1`,
`bundle-analyser 0.2.1`, `image-analyser 0.1.3` (installed from local source in
this repo, not PyPI).

> **Historical record (note added 2026-06-11).** These notes pre-date the family's
> lens-contract conversion (2026-05-24/25), which resolved the structural
> divergences: every member now serves `pkg.api:app`, speaks argparse with
> bare-positional analyse via `run_contract_subcommands`, and carries `add_cors`.
> Keep the items below as the rationale behind the conventions, not as live bugs.

---

## 1. `document-analyser` CLI crashes on every invocation — **blocker**

```
$ document-analyser report.docx --json
AttributeError: 'DocumentAnalysis' object has no attribute 'flesch_reading_ease'
```

`document_analyser/cli.py:_cmd_analyse` reads four attributes that the
`DocumentAnalysis` model does not expose:

| CLI reads | Model actually has |
|---|---|
| `analysis.flesch_reading_ease` | `flesch_score` |
| `analysis.gunning_fog` | — (not present) |
| `analysis.smog_index` | — (not present) |
| `analysis.automated_readability_index` | — (not present) |

The CLI is unusable for any document. **Fix:** align the CLI to the model's real
fields (`word_count`, `sentence_count`, `avg_words_per_sentence`,
`paragraph_count`, `flesch_score`, `flesch_kincaid_grade`), or extend the model to
provide the missing metrics. Add a smoke test that runs the CLI against a fixture
and asserts exit 0 — this class of bug should never ship.

---

## 2. Inconsistent public Python API surface — **high**

Only `code-analyser` exposes a usable top-level import. The other three force
consumers to reach into private-looking submodules:

| Package | `dir(pkg)` top-level | How you actually call it |
|---|---|---|
| `code_analyser` | `CodeAnalyser`, `CodeAnalysis`, `core`, `detect`, `models`, `pipeline` | `code_analyser.CodeAnalyser(...)` ✅ clean |
| `git_analyser` | *(empty)* | `from git_analyser.core import ...` |
| `wordpress_analyser` | *(empty)* | `from wordpress_analyser.core import analyse_file` |
| `document_analyser` | *(empty)* | `from document_analyser.analyzers.readability import ReadabilityAnalyzer` |

A consumer that wants to call all four has to learn four different import paths,
three of which look like internal API that could move without notice. **Fix:**
each package should re-export its primary entry point and result model from
`__init__.py`, so `from <pkg> import <Analyser>, <Result>` works everywhere.

---

## 3. `analyse` vs `analyze` spelling is mixed — **high (papercut, but everywhere)**

- `code-analyser`: British — `CodeAnalyser` class.
- `document-analyser`: American — `ReadabilityAnalyzer().analyze()`.

For a family whose entire value is interchangeability, callers should not have to
remember which spelling each member chose. **Fix:** pick one spelling for the
public surface family-wide (the package names are all `-analyser`, so British is
the natural choice) and provide the other as an alias for back-compat.

---

## 4. Result types are not uniform — **medium**

- `wordpress-analyser` returns a pydantic model (`.model_dump()` to get a dict).
- `document-analyser`'s analyzer returns a pydantic model, but its CLI hand-builds
  a *different* dict shape on top of it.
- `git-analyser`'s CLI emits dict-shaped JSON; `code-analyser` returns a model.

A consumer can't assume "call it, get a model" or "call it, get a dict". **Fix:**
standardise on returning a pydantic model from the Python API, and have every CLI
do `print(result.model_dump_json(indent=2))` — single code path, identical shape
between API and CLI.

---

## 5. `document-analyser` writes nltk noise to stdout — **medium (breaks `--json`)**

First run prints:

```
[nltk_data] Downloading package punkt to /Users/.../nltk_data...
[nltk_data]   Unzipping tokenizers/punkt.zip.
```

If this lands on stdout it corrupts `--json` output for any downstream parser.
**Fix:** route diagnostics to stderr, or (better) ship the required nltk data /
switch to a tokenizer without a runtime download, so a first run isn't special.

---

## 6. CLI argument grammar differs across the family — **medium**

| Tool | Invocation grammar |
|---|---|
| `git-analyser` | `git-analyser analyse <path>` (subcommand, `analyse` default) |
| `code-analyser` | `code-analyser <path>` (positional) |
| `document-analyser` | `document-analyser <path>` (positional) |
| `wordpress-analyser` | `wordpress-analyser <path>` (positional) |
| `auto-analyser` | `auto-analyser analyse <path>` / `detect` / `status` (subcommands) |

Mixed subcommand-vs-positional means muscle memory doesn't transfer. **Fix:**
agree on one grammar. A reasonable convention: bare positional `<path>` is the
default "analyse" action for every single-input tool; reserve subcommands
(`serve`, `detect`, `status`) for genuinely different modes, and let them be
consistent across tools that have them.

---

## 7. Directory / collection handling is inconsistent — **low/medium**

`code-analyser <dir>` fails with `Error: Unsupported file type:` (empty type).
You must zip the directory first, or use `bundle-analyser`. That's a defensible
separation of concerns, but the error message doesn't say so. **Fix:** when a
directory is passed to a single-file tool, emit a clear message:
`code-analyser operates on single files; pass a .zip or use bundle-analyser <dir>`.

---

## Suggested family-wide contract (the "north star")

For every member:

1. `from <pkg> import Analyser, Result` — primary class + result model re-exported.
2. `Analyser().analyse(input)` — British spelling, returns a pydantic `Result`.
3. `<pkg> <path>` — bare positional is "analyse"; `--json` prints
   `result.model_dump_json(indent=2)` and **nothing else** to stdout.
4. Diagnostics, progress, and data-download chatter go to stderr only.
5. Directory passed to a single-file tool → actionable message pointing at
   `bundle-analyser`.
6. A CLI smoke test per package (run against a fixture, assert exit 0 + valid JSON).

Items 1–3 alone would let a consumer write one adapter shape and reuse it across
the whole family, instead of special-casing each tool as we currently must.

---

*Authored from a downstream-integration perspective; happy to turn any of these
into PRs against the individual packages if useful.*

---

## Conventions established 2026-05-23

Family-wide cleanup landed alongside the new `conversation-analyser`:

- **`-analyser` is the only backend suffix.** `-lens` is reserved for bespoke web
  apps (document-lens, insight-lens, udl-lens); do not use it for an engine.
- **Auto-routable vs explicit.** Most analysers are auto-routable (their extension
  implies the analysis). Explicit-only *content interpretations* —
  `conversation-analyser` (and `git-analyser`, `bundle-analyser`, which take repos
  /collections) — set `auto_routable=False` and are never silently routed to.
- **Capability manifests.** Every member exposes a `MANIFEST` (name, version, role,
  accepts, extensions, auto_routable, produces) via a constant, a `manifest` CLI
  subcommand, and `GET /manifest`. `auto-analyser` builds routes from manifests,
  with `detector._ROUTES` kept as the offline fallback. See
  `auto-analyser/docs/adr/0001-manifest-driven-routing.md`.
- **Canonical text extraction.** Binary→text lives once in
  `document_analyser.extract_text()`; other analysers import it instead of
  re-implementing pdfplumber/markitdown. conversation-analyser delegates document
  extraction this way.
- **Outlier (since resolved):** `video-analyser` used a Gradio UI and shipped only a
  manifest constant. As of 0.8.0 it is a full contract member (Gradio dropped,
  `api.py` + `run_contract_subcommands`), and 0.10.0 is signal-only (grading moved
  to `assessment-lens`, ADR-0001).

These address consistency items above (manifest gives a uniform discovery contract;
extraction de-duplication; clearer routing). The CLI/output-shape items (1–4) remain
the per-package north star.
