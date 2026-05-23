# Design: markitdown Refactor

**Date:** 2026-04-27
**Status:** Approved
**Scope:** `document-lens`, `extracta` (Python projects only)

---

## Problem

Document parsing logic is duplicated across three places:

| Project | Language | PDF | DOCX | PPTX | XLSX/CSV |
|---------|----------|-----|------|------|----------|
| `document-lens` | Python | pypdf + pdfplumber | python-docx | python-pptx | pandas + openpyxl |
| `extracta` | Python | PyPDF2 + pdfplumber | python-docx | python-pptx | pandas + openpyxl |
| `cite-sight` | TypeScript | pdfjs-dist | mammoth | — | — |

`cite-sight` is out of scope — it was intentionally kept TypeScript-only to avoid a Python deployment dependency, and its parsers are clean and purposeful.

The Python duplication (~600 lines per project) is the target. Microsoft's `markitdown` is a mature, maintained library that handles all these formats and replaces the hand-rolled parsers.

---

## Approach

**Option B selected:** pdfplumber for PDFs in `document-lens` (page-level required), markitdown for everything else in both projects.

### Why not markitdown for PDFs in `document-lens`?

The desktop app (`document-lens-desktop`) has a per-page document viewer — a research feature where users need to see the page context of where analysis occurred. pdfplumber extracts text page-by-page with real page boundaries. markitdown returns one combined markdown string with no page boundary information.

`extracta` has no page requirement, so markitdown handles PDFs there without issue.

---

## Changes

### `document-lens/app/services/document_processor.py`

- **PDFs**: unchanged. pdfplumber page-by-page extraction preserved. Response shape unchanged: `{full_text, pages: [{page_number, text}], total_pages}`.
- **DOCX, PPTX, XLSX, CSV, plain text**: replaced with `markitdown.convert(path).text_content`. Wrapped as single-page response: `{full_text, pages: [{page_number: 1, text: ...}], total_pages: 1}`.
- **API response shape**: no change. All callers unaffected.

**Dependencies — remove:**
- `python-docx`
- `python-pptx`
- `pandas`
- `openpyxl`

**Dependencies — add:**
- `markitdown[docx,pptx,xlsx]`

### `extracta/extracta/lenses/document_lens/document_lens.py`

- **All formats** (PDF, DOCX, PPTX, XLSX, CSV, text): replaced with `MarkItDown().convert(file_path).text_content`.
- **Return shape**: unchanged `{success, data: {content_type, raw_content, file_path, file_size}}`. Downstream analyzers unaffected.
- **`SUPPORTED_EXTENSIONS`**: expanded to markitdown's full set, adding `.html`, `.epub`, `.ipynb`, `.xml`, `.zip` for free.

**Dependencies — remove from `[documents]`:**
- `PyPDF2`
- `pdfplumber`
- `python-docx`

**Dependencies — remove from `[presentations]`:**
- `python-pptx`
- `PyMuPDF`

**Dependencies — add:**
- `markitdown[docx,pptx,xlsx,pdf]` under `[documents]` optional group

---

## Out of Scope

### Image extraction (future feature)

The desktop app has a planned feature for viewing images embedded in documents (PDFs, DOCX, PPTX). markitdown does not extract images as binary data. The hook for this feature is:

- **PPTX/DOCX**: post-conversion pass over `shape.image.blob` entries (accessible via python-pptx or mammoth internals)
- **PDF**: PyMuPDF (`fitz`) added back as an optional dependency, used only for image extraction (separate from text extraction which stays on pdfplumber)
- **PPTX with LLM**: markitdown's `PptxConverter` supports `llm_client` + `llm_model` kwargs to generate image descriptions — useful for analysis, not viewing

This is additive and does not block the current refactor.

### `cite-sight` TypeScript parsers

`cite-sight/packages/core/src/extractors/` has its own DOCX (mammoth) and PDF (pdfjs-dist) extractors. These are clean, short, and correctly scoped. Centralising them via the `document-lens` API would add a deployment dependency that was deliberately avoided. Revisit if `document-lens` ever becomes a shared infrastructure dependency for cite-sight.

---

## Testing

- Run existing test suites in both projects — they test output shape, not parsing internals, and should pass without modification.
- Add one smoke test per project using real sample files (`document-lens/test-data/`, `document-lens-desktop/samples/`) to confirm markitdown produces non-empty output for each supported format.
- No API contract changes — no integration test changes required in `document-lens-desktop`.

---

## What does NOT change

- `document-lens-desktop` — no changes. Calls the same Python API endpoints, gets the same response shapes.
- `cite-sight` — no changes.
- All NLP analyzers in `document-lens` — they receive the same text strings as before.
- All analyzers in `extracta` — they receive the same `raw_content` string as before.
- The `document-lens` + `document-lens-desktop` embedded architecture — unchanged.
