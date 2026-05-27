# lens-analysers

The **analyser family** — a set of small, independent Python tools that each take a
file (or text) and return structured JSON signals. One tool per content type; a
shared contract so they compose. This is the umbrella: the big picture, the
conventions, and links out to each package (which lives in its own repo and ships
to PyPI independently).

> Docs only. No code lives here — each analyser is its own repository.

## The model

Two tiers, with deliberately different suffixes:

- **`-analyser`** — a reusable analysis *engine*. Takes its input directly, returns
  JSON. Most are **auto-routable** (their file extension implies the analysis).
- **`-lens`** — a bespoke *application/product* built on top of the engines
  (e.g. document-lens, insight-lens, udl-lens). Purpose-built UIs, not general tools.

Within the engines there's a second distinction that matters for routing:

- **Auto-routable** — the format implies the analysis (`.py` → code, `.csv` → records,
  `.wav` → speech). `auto-analyser` can pick these for you.
- **Explicit-only** — a *content interpretation* the format doesn't imply, that can
  overlay bytes another analyser already claims (e.g. a PDF read as a *conversation*).
  These set `auto_routable: false` and must be invoked deliberately.

## The family

<!-- family-table:start -->

| Package | Version | Handles | Extensions | Routable | Links |
|---|---|---|---|---|---|
| [code-analyser](https://github.com/michael-borck/code-analyser) | 1.2.0 | source code — style, complexity, quality | `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.html`, `.css`, `.scss`, `.sql`, `.ipynb` | auto | [PyPI](https://pypi.org/project/code-analyser/) · [repo](https://github.com/michael-borck/code-analyser) |
| [diagram-analyser](https://github.com/michael-borck/diagram-analyser) | 0.1.0 | mermaid / PlantUML / Graphviz / drawio — nodes, edges, cycles, depth, naming | `.mmd`, `.mermaid`, `.puml`, `.plantuml`, `.dot`, `.gv`, `.drawio` | auto | [PyPI](https://pypi.org/project/diagram-analyser/) · [repo](https://github.com/michael-borck/diagram-analyser) |
| [document-analyser](https://github.com/michael-borck/document-analyser) | 0.6.0 | PDF, DOCX, PPTX, TXT, MD — text, readability, .pptx slide-design | `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`, `.qmd`, `.rst` | auto | [PyPI](https://pypi.org/project/document-analyser/) · [repo](https://github.com/michael-borck/document-analyser) |
| [image-analyser](https://github.com/michael-borck/image-analyser) | 0.4.0 | images — metadata, quality, OCR, captions, barcodes | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp` | auto | [PyPI](https://pypi.org/project/image-analyser/) · [repo](https://github.com/michael-borck/image-analyser) |
| [records-analyser](https://github.com/michael-borck/records-analyser) | 0.4.0 | CSV, Excel, SQLite, Parquet, JSON — data profiling | `.csv`, `.tsv`, `.xlsx`, `.xls`, `.parquet`, `.sqlite`, `.db`, `.sqlite3`, `.json`, `.yaml`, `.yml`, `.xml` | auto | [PyPI](https://pypi.org/project/records-analyser/) · [repo](https://github.com/michael-borck/records-analyser) |
| [speech-analyser](https://github.com/michael-borck/speech-analyser) | 0.5.0 | audio/video — transcript + speech metrics | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.opus` | auto | [PyPI](https://pypi.org/project/speech-analyser/) · [repo](https://github.com/michael-borck/speech-analyser) |
| [video-analyser](https://github.com/michael-borck/video-analyser) | 0.9.0 | video — frames, scenes, transcript + visual quality | `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv` | auto | [PyPI](https://pypi.org/project/video-analyser/) · [repo](https://github.com/michael-borck/video-analyser) |
| [wordpress-analyser](https://github.com/michael-borck/wordpress-analyser) | 0.4.0 | WordPress PHP — hooks, API usage, quality | `.php` | auto | [PyPI](https://pypi.org/project/wordpress-analyser/) · [repo](https://github.com/michael-borck/wordpress-analyser) |
| [cite-sight](https://github.com/michael-borck/cite-sight) | 0.3.7 | citations & references — verify (Crossref/OpenAlex), DOI, format, cross-refs | — | explicit | [repo](https://github.com/michael-borck/cite-sight) |
| [conversation-analyser](https://github.com/michael-borck/conversation-analyser) | 0.2.2 | human-AI conversations — engagement + critical-thinking | — | explicit | [PyPI](https://pypi.org/project/conversation-analyser/) · [repo](https://github.com/michael-borck/conversation-analyser) |
| [git-analyser](https://github.com/michael-borck/git-analyser) | 0.4.0 | git repositories — commit history + churn | — | explicit | [PyPI](https://pypi.org/project/git-analyser/) · [repo](https://github.com/michael-borck/git-analyser) |
| [provenance-analyser](https://github.com/michael-borck/provenance-analyser) | 0.1.0 | document metadata — creator app, editing time, authorship, AI-gen markers | `.docx`, `.pdf`, `.pptx`, `.xlsx` | explicit | [PyPI](https://pypi.org/project/provenance-analyser/) · [repo](https://github.com/michael-borck/provenance-analyser) |
| [reflection-analyser](https://github.com/michael-borck/reflection-analyser) | 0.1.0 | reflective writing — metacognition, criticality, depth bands | — | explicit | [PyPI](https://pypi.org/project/reflection-analyser/) · [repo](https://github.com/michael-borck/reflection-analyser) |
| [revision-analyser](https://github.com/michael-borck/revision-analyser) | 0.1.0 | .docx tracked-changes — drafting trajectory, paste-burst detection | `.docx` | explicit | [PyPI](https://pypi.org/project/revision-analyser/) · [repo](https://github.com/michael-borck/revision-analyser) |
| [site-analyser](https://github.com/michael-borck/site-analyser) | 0.1.0 | deployed URL or static-site dir — accessibility, structure, SEO, links, validity | — | explicit | [PyPI](https://pypi.org/project/site-analyser/) · [repo](https://github.com/michael-borck/site-analyser) |
| [spreadsheet-analyser](https://github.com/michael-borck/spreadsheet-analyser) | 0.1.0 | Excel — formula logic, dependencies, error cells, hygiene smells | `.xlsx`, `.xlsm` | explicit | [PyPI](https://pypi.org/project/spreadsheet-analyser/) · [repo](https://github.com/michael-borck/spreadsheet-analyser) |
| [auto-analyser](https://github.com/michael-borck/auto-analyser) | 0.6.0 | any file — detects format and routes to the right tool | — | orchestrator | [PyPI](https://pypi.org/project/auto-analyser/) · [repo](https://github.com/michael-borck/auto-analyser) |
| [bundle-analyser](https://github.com/michael-borck/bundle-analyser) | 0.4.0 | folders & zips — analyse a collection of files | — | orchestrator | [PyPI](https://pypi.org/project/bundle-analyser/) · [repo](https://github.com/michael-borck/bundle-analyser) |

<!-- family-table:end -->

*This table is generated from each package's capability manifest by
[`scripts/generate_family_table.py`](scripts/generate_family_table.py) — single
source of truth, so it never drifts. Versions are each package's current release;
follow the PyPI links to install. Every Python member is built on the shared
[lens-contract](https://github.com/michael-borck/lens-contract) library.*

Possible future members (a backlog, not commitments) live in
[CANDIDATE-MEMBERS.md](CANDIDATE-MEMBERS.md) — weighted toward *process* signals
(revision history, activity logs) where the family is currently thin.

For picking the right *combination* of members for an assessment design — the
two-axis Product/Process × Convergent/Divergent map, worked examples, and
named bundles — see **[ASSESSMENT-MAP.md](docs/ASSESSMENT-MAP.md)**.

## How they compose

The engines are single-purpose; chain them for richer tasks:

- PDF/DOCX chat → **document-analyser** (extract text) → **conversation-analyser**
- audio chat → **speech-analyser** (transcribe) → **conversation-analyser**
- a folder of mixed files → **bundle-analyser** → **auto-analyser** per file
- any single file → **auto-analyser** → the right engine

For ready-made compositions matched to common assessment shapes (e.g. an
`authentic-essay` bundle that runs document + provenance + revision + reflection
in parallel), see the bundles section of
[ASSESSMENT-MAP.md](docs/ASSESSMENT-MAP.md#bundles--first-class-presets).

Text extraction (binary → text) has one canonical home: `document_analyser.extract_text()`.
Other analysers import it rather than re-implementing extraction.

## The shared contract

Every member converges on one shape — see **[CONVENTIONS.md](CONVENTIONS.md)** for the
full spec. In brief:

- **Python:** `from <pkg> import <Name>Analyser, <Name>Analysis` → `.analyse(input)` returns a pydantic model.
- **CLI:** `<pkg> <path> [--json]`; `serve` and `manifest` subcommands; British spelling; JSON to stdout, diagnostics to stderr.
- **HTTP:** `GET /health`, `GET /manifest`, `POST /analyse` (file upload). Ports 8000–8010 (`auto-analyser` on 8010).
- **Manifest:** every member exposes a `MANIFEST` (name, version, role, accepts, extensions, `auto_routable`, produces) as a constant, a CLI subcommand, and `/manifest`. `auto-analyser` builds its routing table from these.

Python members implement this contract via **[lens-contract](https://github.com/michael-borck/lens-contract)** — a small shared library (`make_manifest`, `add_contract_routes`/`make_app`, `upload_tempfile`, `run_contract_subcommands`) so the boilerplate lives in one place instead of being copy-pasted per repo. It's infrastructure (`role: library`), not an analyser, so it doesn't appear in the family table above. Non-Python members (e.g. cite-sight) implement the same contract themselves.

Building a new analyser? See the **[ADDING-A-MEMBER.md](ADDING-A-MEMBER.md)** checklist.

## Routing

`auto-analyser` discovers each analyser's manifest (via HTTP or CLI) to learn what it
handles and whether it's auto-routable, then routes accordingly — falling back to a
static map when a service is offline. See
[auto-analyser/docs/adr/0001-manifest-driven-routing.md](https://github.com/michael-borck/auto-analyser/blob/main/docs/adr/0001-manifest-driven-routing.md).

It also **serves the contract itself**: `auto-analyser serve` (port 8010) exposes a
routing `POST /analyse` that detects an uploaded file's format, forwards it to the
right member, and returns that member's result with a `routed_to` key — one HTTP
front door for the whole family.

## Install

Each package installs independently from PyPI:

```bash
pip install document-analyser conversation-analyser auto-analyser   # etc.
```

Each also runs as an HTTP service. `auto-analyser serve` gives a single endpoint
that routes any file to the right member:

```bash
auto-analyser serve                              # one front door, port 8010
curl -F file=@report.pdf http://localhost:8010/analyse
```

## Repository layout

Everything lives in a local `lens/` **workspace** — a plain folder (not a git repo)
that holds each project as an independent clone, side by side:

```
lens/                      ← workspace (not a repo)
├── lens-analysers/        ← this repo: docs only (README, CONVENTIONS, docs/, scripts/)
├── lens-contract/         ← shared contract library used by the Python members
├── document-analyser/     ← each analyser/app is its own repo, beside the umbrella
├── conversation-analyser/
├── auto-analyser/
└── …
```

This umbrella tracks only documentation (`README.md`, `CONVENTIONS.md`,
`ANALYSER-FAMILY-UX-GOTCHAS.md`, `docs/`). Each analyser is an independent repo with its
own issues, releases, and PyPI package — no submodules, no nesting, so there are no
cross-repo git dependencies. Bidirectional links keep discovery easy, and
`scripts/generate_family_table.py` scans the sibling repos to rebuild the table above.

## Apps built on the family (`-lens`)

Bespoke products that consume the engines: **document-lens** (sustainability/SDG
keyword research), **insight-lens** (Curtin survey-PDF analysis), **udl-lens**
(Universal Design for Learning assessment). These are separate repos and not part of
the analyser packages.
