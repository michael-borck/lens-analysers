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

| Package | Handles | Routable | Links |
|---|---|---|---|
| document-analyser | PDF, DOCX, PPTX, TXT, MD — text + readability | auto | [PyPI](https://pypi.org/project/document-analyser/) · [repo](https://github.com/michael-borck/document-analyser) |
| speech-analyser | audio/video — transcript + speech metrics | auto | [PyPI](https://pypi.org/project/speech-analyser/) · [repo](https://github.com/michael-borck/speech-analyser) |
| video-analyser | video — frames, scenes, visual quality (Gradio UI) | auto | [PyPI](https://pypi.org/project/video-analyser/) · [repo](https://github.com/michael-borck/video-analyser) |
| records-analyser | CSV, Excel, SQLite, Parquet, JSON — data profiling | auto | [PyPI](https://pypi.org/project/records-analyser/) · [repo](https://github.com/michael-borck/records-analyser) |
| code-analyser | source code — style, complexity, quality | auto | [PyPI](https://pypi.org/project/code-analyser/) · [repo](https://github.com/michael-borck/code-analyser) |
| image-analyser | images — metadata, quality, OCR, captions, barcodes | auto | [PyPI](https://pypi.org/project/image-analyser/) · [repo](https://github.com/michael-borck/image-analyser) |
| wordpress-analyser | WordPress PHP — hooks, API usage, quality | auto | [PyPI](https://pypi.org/project/wordpress-analyser/) · [repo](https://github.com/michael-borck/wordpress-analyser) |
| git-analyser | git repositories — commit history + churn | explicit | [PyPI](https://pypi.org/project/git-analyser/) · [repo](https://github.com/michael-borck/git-analyser) |
| conversation-analyser | human-AI conversations — engagement + critical-thinking | explicit | [PyPI](https://pypi.org/project/conversation-analyser/) · [repo](https://github.com/michael-borck/conversation-analyser) |
| bundle-analyser | folders & zips — analyse a collection of files | explicit | [PyPI](https://pypi.org/project/bundle-analyser/) · [repo](https://github.com/michael-borck/bundle-analyser) |
| auto-analyser | any file — detects format and routes to the right tool | orchestrator | [PyPI](https://pypi.org/project/auto-analyser/) · [repo](https://github.com/michael-borck/auto-analyser) |

*Versions live on PyPI (linked); this table is intentionally version-free so it
never drifts. It can also be generated from each package's capability manifest.*

## How they compose

The engines are single-purpose; chain them for richer tasks:

- PDF/DOCX chat → **document-analyser** (extract text) → **conversation-analyser**
- audio chat → **speech-analyser** (transcribe) → **conversation-analyser**
- a folder of mixed files → **bundle-analyser** → **auto-analyser** per file
- any single file → **auto-analyser** → the right engine

Text extraction (binary → text) has one canonical home: `document_analyser.extract_text()`.
Other analysers import it rather than re-implementing extraction.

## The shared contract

Every member converges on one shape — see **[CONVENTIONS.md](CONVENTIONS.md)** for the
full spec. In brief:

- **Python:** `from <pkg> import <Name>Analyser, <Name>Analysis` → `.analyse(input)` returns a pydantic model.
- **CLI:** `<pkg> <path> [--json]`; `serve` and `manifest` subcommands; British spelling; JSON to stdout, diagnostics to stderr.
- **HTTP:** `GET /health`, `GET /manifest`, `POST /analyse` (file upload). Ports 8000–8009.
- **Manifest:** every member exposes a `MANIFEST` (name, version, role, accepts, extensions, `auto_routable`, produces) as a constant, a CLI subcommand, and `/manifest`. `auto-analyser` builds its routing table from these.

## Routing

`auto-analyser` discovers each analyser's manifest (via HTTP or CLI) to learn what it
handles and whether it's auto-routable, then routes accordingly — falling back to a
static map when a service is offline. See
[auto-analyser/docs/adr/0001-manifest-driven-routing.md](https://github.com/michael-borck/auto-analyser/blob/main/docs/adr/0001-manifest-driven-routing.md).

## Install

Each package installs independently from PyPI:

```bash
pip install document-analyser conversation-analyser auto-analyser   # etc.
```

## Repository layout

This umbrella tracks only documentation (`README.md`, `CONVENTIONS.md`,
`ANALYSER-FAMILY-UX-GOTCHAS.md`, `docs/`). Each analyser is an independent repo with
its own issues, releases, and PyPI package — cloned alongside this one in a local
`lens/` workspace and ignored here. Bidirectional links keep discovery easy.

## Apps built on the family (`-lens`)

Bespoke products that consume the engines: **document-lens** (sustainability/SDG
keyword research), **insight-lens** (Curtin survey-PDF analysis), **udl-lens**
(Universal Design for Learning assessment). These are separate repos and not part of
the analyser packages.
