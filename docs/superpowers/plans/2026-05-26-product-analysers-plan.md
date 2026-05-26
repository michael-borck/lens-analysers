# Plan: four product-signal analysers

**Date:** 2026-05-26
**Goal:** add the remaining high-coverage *product* analysers, all on the family
contract (see [ADDING-A-MEMBER.md](../../../ADDING-A-MEMBER.md) + lens-contract).
Together with the existing members these cover ~90% of submittable products.

Build order (simplest → heaviest): **spreadsheet → site → diagram → slides**.
Each built test-first (`tdd` skill). Ports continue the registry: spreadsheet **8011**,
site **8012**, diagram **8013** (slides is an extension of document-analyser, no new port).

PyPI names confirmed free: `spreadsheet-analyser`, `site-analyser`, `diagram-analyser`.

---

## 1. spreadsheet-analyser  (new member · explicit-only)

The spreadsheet's **formula logic**, not its data (records-analyser owns the data).
`.xlsx` already auto-routes to records-analyser, so this is **`auto_routable: false`**
(invoke deliberately, or via auto-analyser `--analyser spreadsheet-analyser`).

- **Input:** `.xlsx` / `.xlsm` (openpyxl, `data_only=False` to read formulas). `.ods` later.
- **Contract:** standard file-upload `/analyse` (it *is* a file); CLI bare-positional `<file>`.
- **Signals → `SpreadsheetAnalysis`** (per-sheet + overall):
  - **formulas:** count, % cells formula vs constant, unique functions used, max nesting depth, longest formula.
  - **dependencies:** cross-sheet references, dependency-chain depth, **circular references**.
  - **errors:** error cells (`#REF!`/`#DIV/0!`/`#VALUE!`/`#N/A`), formulas pointing at empty cells.
  - **structure:** sheet count, used range, named ranges, tables, charts present.
  - **hygiene/quality:** volatile functions (`NOW`/`RAND`/`OFFSET`/`INDIRECT`), **hardcoded magic numbers inside formulas**, inconsistent formulas across a row/column region.
- **Deps:** lens-contract, openpyxl, fastapi/uvicorn/python-multipart, rich. **No external tools** — clean pip; that's why it's first.

## 2. site-analyser  (new member · hybrid)

Generic site-quality signals from a **deployed URL or a local static-site dir**.
Generalises the reusable parts of `ISYS3004/.../assess-a1` (`site_crawl`, `code_validation`,
`structure_check`); the *course rubric* (`requirements_check`) stays in the course and
**calls** site-analyser.

- **Input:** a URL **or** a local directory. Like git-analyser, `/analyse` takes a JSON
  body `{ "url": ... }` / `{ "path": ... }` (not a multipart upload); CLI bare-positional
  `site-analyser <url-or-dir>`.
- **Tooling: hybrid.** Pure-Python core (always pip-installable) + optional shell-out to
  Lighthouse / `vnu` when Node/Chrome/Java are present (graceful degradation, reported).
- **Signals → `SiteAnalysis`** (per-page + overall):
  - **crawl:** internal-link discovery, page count, **broken links** (internal + external HEAD).
  - **structure:** semantic HTML (header/nav/main/footer), heading hierarchy, landmarks.
  - **accessibility:** alt-text coverage, form-label coverage, `lang`, ARIA, skip-link, contrast heuristic (pure-Python WCAG checks; deeper via Lighthouse if present).
  - **SEO:** title, meta description, OpenGraph, canonical, viewport.
  - **tech:** framework/CDN detection (Bootstrap/Tailwind/React/Vue), inline style/script smells.
  - **validity:** HTML/CSS parse-error count (html5lib; deep W3C via `vnu` if present).
  - **perf:** light hints (page weight, request count); real scores via Lighthouse if present.
- **Deps:** lens-contract, httpx, beautifulsoup4, html5lib, fastapi/uvicorn/python-multipart, rich. (Lighthouse/vnu detected at runtime, not pip deps.)

## 3. diagram-analyser  (new member · text + optional vision)

- **Input (text, auto-routable):** mermaid `.mmd`, PlantUML `.puml`, Graphviz `.dot`,
  drawio `.drawio` (XML) → parse to a node/edge graph. These extensions aren't claimed
  elsewhere, so **auto_routable: true** for them.
- **Input (image, explicit + optional):** `.png`/`.jpg` of a diagram → vision/LLM extraction.
  Those extensions auto-route to image-analyser, so the image path is **explicit-only** and
  behind a **`[vision]` extra + API key** (anthropic/openai, mirroring image-analyser's captioning).
- **Signals → `DiagramAnalysis`:** diagram type, node/edge counts, **orphan nodes, cycles**,
  max depth, naming quality; for ER/UML: entities, relationships, cardinality. Vision path
  returns the same metrics where extractable + a described structure.
- **Deps:** lens-contract, networkx (cycles/orphans), the text parsers, fastapi/uvicorn/multipart, rich.
  `[vision]` extra: anthropic (+ openai) for the image path. Biggest of the four (4 parsers + vision).

## 4. document-analyser — slide-design extension  (NOT a new member)

document-analyser already ingests `.pptx` (text + readability). **Add** a `python-pptx`
slide-design analyzer so `.pptx` input also yields design signals.

- **Signals (a `slide_design` block on `DocumentAnalysis` for `.pptx`):** slide count,
  words/slide (density), images/slide, bullet depth, title coverage, empty slides,
  **text-overloaded slides**, layout consistency.
- **Deps:** add `python-pptx`. Version bump (→ 0.6.0). Additive; existing prose/readability unchanged.

---

## Per-member checklist (each build)

Follow [ADDING-A-MEMBER.md](../../../ADDING-A-MEMBER.md): make_manifest → api.py
(`add_contract_routes` + `add_cors` [+ `add_rate_limit` only if wanted]) → argparse CLI
(`run_contract_subcommands`) → smoke tests → publish → regenerate the family table →
`gh repo create`. Pin `lens-contract>=0.2.0`. Add the new port to CONVENTIONS.

**Verification caveat:** site-analyser's optional Lighthouse/vnu path and diagram-analyser's
vision path can only be unit-tested with mocks here (external tools / API keys / live URLs);
the pure-Python cores are fully testable.
