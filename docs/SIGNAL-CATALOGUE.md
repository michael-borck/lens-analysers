# Signal catalogue — every signal each analyser produces

> The enumerated companion to [ASSESSMENT-MAP.md](./ASSESSMENT-MAP.md).
> ASSESSMENT-MAP answers *"which analysers should this assessment use?"*;
> this doc answers *"what exactly does each analyser output?"* — the full
> per-member signal list, grouped by submission mode.

Each `-analyser` reads **one submission mode** and returns structured JSON
signals. `auto-analyser` routes a file to the right member; `bundle-analyser`
runs many over a folder/zip. The **headline signal** (the composite score or
verdict) is flagged per member where one exists.

> Code-verified against each member's result schema. Re-verify after schema
> changes — treat the schema (`produces` model) as source of truth.

---

## ✍️ Text / writing submissions

### document-analyser — essays, reports, prose (`.pdf .docx .pptx .txt .md`)
**Headline: Integrity score (0–100)** — composite (100 = clean).
- AI-generation indicators (AI words/phrases, LLM artefacts, em-dash/bullet ratios) → confidence + risk level (low/med/high)
- Readability — Flesch, Flesch-Kincaid grade, Gunning Fog, SMOG, ARI
- Writing quality — passive %, sentence variety, transitions, hedging, academic tone
- Vocabulary richness (type-token ratio, hapax), word/bigram/trigram frequency
- Self-plagiarism (reused passages), citation anomalies, style-shift detection
- Reference verification — broken URLs, unresolved DOIs, orphan/missing-in-text citations
- Granular sentiment (doc → section → paragraph → sentence), named entities (NER)
- Domain/topic mapping; structural mismatch (out-of-place sentences → coherence score)
- Inferred metadata (probable year/company/industry/type); keyword search

### reflection-analyser — journals, reflective / metacognitive writing
**Headline: Depth band** — descriptive → dialogic → critical → transformative (Moon-style), + 0–1 depth score.
- Markers (count, coverage per 100 words, example sentences): metacognition · criticality · evidence · affect · forward-looking

### conversation-analyser — AI chat transcripts (student ↔ LLM)
**Headline: Critical-thinking score (0–100)** + engagement band (Delegator → Iterative → Critical).
- Per-turn taxonomy: New-query / Follow-up / Challenge / Extension / Delegation / Acknowledge / Meta
- Prompt effort — length, readability, typo rate, self-similarity; question ratio; pushback count
- Longest engaged chain; filler-heavy flag; sentiment trajectory; duration / time-of-day

### cite-sight — citation & reference integrity (`.pdf .docx .txt .md`)
*(Standalone TypeScript app, not a manifest-driven Python member, but a rich signal source.)*
**Headline: per-reference verification** — verified / likely-valid / not-found / **suspicious** (Crossref · Semantic Scholar · OpenAlex).
- DOI resolution; URL liveness (live/dead/redirect); citation-format checks (APA/MLA/Chicago)
- In-text ↔ bibliography cross-check (orphan citations / orphan entries); per-reference confidence (0–1)
- Plus readability, writing-quality, and word-analysis signals (overlaps document-analyser)

### revision-analyser — Word `.docx` with tracked changes
**Headline: integrity flags** — paste-burst present / single vs multiple authors / short timeline / no revisions.
- Edit totals (insert/delete/move + word counts); per-author rollup; edit-timeline span
- **Paste-burst detection** — single insertions ≥ 25 words (likely copied blocks)

### provenance-analyser — document metadata (`.docx .pdf .pptx .xlsx`)
**Headline: heuristic flags** — AI-generation marker / edit-time-too-low-for-size / created≈modified / author mismatch / zero revisions / missing metadata.
- Authoring-app & PDF-producer fingerprint; author + last-modified-by; created/modified times
- **Total editing minutes + save (revision) count** (Office); size hints (pages/words)

---

## 🎤 Media submissions

### speech-analyser — audio (`.mp3 .wav .m4a …`)
**Headline: Delivery quality score (0–100)** — clarity · depth · balance · pace.
- Transcript + language; speaking rate (WPM) + pace category; filler-word count/rate
- Silence ratio + actual speaking time; speaker diarization → per-speaker talk-time share + balance

### video-analyser — video (`.mp4 .mov …`)
**Headline: overall quality aggregates** — reliability, critical issues, recommended actions.
- Scene/shot detection; per-scene + overall speech metrics (WPM, fillers, pauses, sentiment, transcription confidence)
- Per-frame visual quality (blur, exposure, composition); frame captions + on-screen OCR (slides); presentation-layout detection

### image-analyser — images (`.png .jpg …`)
- **C2PA content-credentials → AI-generated claim** (authenticity); perceptual hashes (duplicate/tamper)
- Quality (blur, exposure, brightness, contrast, noise, JPEG quality); EXIF/IPTC/XMP metadata (camera, GPS, capture time)
- OCR text; object detection; caption; dominant colours; barcodes/QR; "is-this-a-diagram" hint

### diagram-analyser — flowcharts / UML / graphs (`.mmd .puml .dot .drawio`)
- Parsed graph (nodes/edges/counts); structure — orphan nodes, cycles, max depth, is-DAG, disconnected components
- Naming — label coverage, average label length, suspiciously-short (placeholder) labels

---

## 💻 Technical submissions

### code-analyser — source code (`.py .ipynb .html .css .js .ts .sql`)
- Per-language: syntax validity, lint errors/warnings, cyclomatic complexity, nesting depth, LOC/comment density, docstring/type coverage, naming consistency, TODO/print/debug smells
- HTML/CSS: accessibility (alt/label/heading/ARIA), semantic-vs-div, layout technique, validity
- SQL: unsafe patterns (UPDATE/DELETE without WHERE, SELECT *), join/subquery depth
- Notebooks: execution-order validity + has-outputs (did they actually run it)
- **Optional LLM signals**: comment/naming quality, **code_level (beginner/intermediate/advanced)**, suggestions

### git-analyser — a git repository
**Headline: suspicious flags** — bulk-upload (≤2 commits) / single-session dump (<24h) / huge commit / multiple authors.
- Learning signals: commit-cadence regularity, add/delete (refactor) ratio, generic-message ratio, time span, gaps — *incremental work vs. last-minute dump*

### spreadsheet-analyser — Excel (`.xlsx .xlsm`)
- Formula ratio (computed vs hard-coded), unique functions, nesting depth, longest formula, volatile functions, magic numbers
- Error cells (#REF!/#DIV0!…), circular references, cross-sheet refs, dependency-chain depth; charts/tables/named ranges

### site-analyser — a website / static site
- Accessibility (alt/label coverage, lang, ARIA, skip-link, heading hierarchy); SEO (title/meta/OG/canonical/viewport)
- Semantic structure; inline-code smells; framework/CDN detection; broken links; HTML validity; page size
- Optional **Lighthouse scores** (a11y / perf / SEO / best-practices) + Nu validator

### records-analyser — tabular data (`.csv .xlsx .json .sqlite .parquet …`)
- Descriptive profile only (no scoring): row/col counts, per-column stats (min/max/mean/median/std/quartiles), missing %, uniqueness, top values, multi-table profiles

---

## 🔀 Infrastructure (no signals of their own)
- **auto-analyser** — routes a file by extension to the right member; supports **cascades** (e.g. image → diagram when it's a diagram) and named **presets** (parallel bundles).
- **bundle-analyser** — walks a folder/zip, runs auto-analyser per file, aggregates results + a file-type distribution.

---

## Cross-cutting themes (for rubric design)
Three signal families recur across modalities:

1. **Academic-integrity / authenticity** — AI-generation (document · image-C2PA · provenance markers), fake references (cite-sight), paste bursts (revision), bulk-upload / last-minute (git · provenance edit-time).
2. **Process & effort evidence** — git cadence, revision timeline, provenance editing-minutes, conversation engagement — *did the work happen incrementally and authentically?*
3. **Quality / skill level** — the composites: document integrity, reflection depth, conversation critical-thinking, speech delivery, code level.

## Presets — signal bundles that map to assessment shapes
`auto-analyser` defines named presets that run several members on the same submission and roll up `flags_across_bundle`:

| Preset | Members combined |
|---|---|
| **authentic-essay** | document + provenance + revision + reflection |
| **skill-with-evidence** | (skill artefact + supporting evidence) |
| **design-with-rationale** | (design artefact + reasoning) |
| **multimedia-evidence** | (media + supporting signals) |
| **reflective-practice** | (reflection-centred bundle) |

See [ASSESSMENT-MAP.md](./ASSESSMENT-MAP.md) for the strategy behind picking and triangulating these.
