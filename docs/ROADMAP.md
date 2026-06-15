# Lens family — roadmap & signal backlog

Living tracker. Started 2026-06-13 from a full read-only audit of every Python
member. Framing principle that governs all signal work:
[describe process/engagement, never claim AI detection](#framing-principle).

Sequence: **hygiene sweep → embedding infrastructure → distinctiveness signal →
backlog**. Tick boxes as we go.

---

## Audit snapshot (2026-06-13)

Family is structurally healthy: contract-conformant across the board
(manifest + api.py + add_cors + run_contract_subcommands + lens-contract pin;
assessment-lens correctly has none), ~900 test functions total, no broken
members. Gaps are additive.

| Member | Ver | Tests | examples/ | Note |
|---|---|---|---|---|
| document-analyser | 0.7.0 | 71 | ✗ | stale `InferredMetadata` legacy |
| conversation-analyser | 0.3.1 | 42 | ✗ | clean |
| reflection-analyser | 0.1.0 | 37 | ✗ | lexicon-only (no LLM aug yet) |
| revision-analyser | 0.1.0 | 25 | ✗ | "ai-detection" in pyproject keywords |
| provenance-analyser | 0.1.0 | 18 | ✗ | "ai-detection" keyword + `ai_generation_marker` flag |
| speech-analyser | 0.5.0 | 88 | ✗ | clean |
| video-analyser | 0.10.0 | 282 | ✗ | clean (signal-only) |
| image-analyser | 0.4.0 | 73 | ✗ | clean (C2PA is provenance, fine) |
| diagram-analyser | 0.1.0 | 42 | ✗ | vision path returns no parsed structure |
| code-analyser | 1.2.0 | 98 | ✗ | clean |
| git-analyser | 0.4.0 | 29 | ✗ | placeholder README + "Status: Planning" at 0.4.0 |
| spreadsheet-analyser | 0.1.0 | 48 | ✗ | clean |
| records-analyser | 0.4.0 | 39 | ✗ | loosely-typed profile dict |
| site-analyser | 0.1.0 | 40 | ✗ | clean |
| wordpress-analyser | 0.4.0 | 37 | ✗ | placeholder README + "Status: Planning" at 0.4.0 |
| auto-analyser | 0.6.0 | 49 | n/a | only 1 cascade rule; presets unvalidated |
| bundle-analyser | 0.4.0 | 25 | ✗ | minimal README; LICENSE © 2024; per-file subprocess cost |
| assessment-lens | 0.2.0 | 35 | ✓(1) | CLAUDE.md untracked |
| assessment-bench | 0.3.0 | 24 | ✗ | uv.lock untracked |

**The keystone finding:** *no analyser exposes embeddings / topic-vectors.* That
single missing output is what blocks both cross-artefact consistency and the
cohort-distinctiveness signal. Build it once, both unlock.

---

## Phase 1 — Hygiene sweep  ✅ (done 2026-06-13, except one deferred item)

- [x] Add a thin `examples/basic_usage.md` (CLI + verified Python + HTTP) to all 17 analysers/orchestrators
- [x] git-analyser: README status "coming soon" → "available on PyPI" (it's shipped at 0.4.0)
- [x] wordpress-analyser: same
- [x] bundle-analyser: LICENSE © 2024 → 2026 (README usage now covered by examples/)
- [x] Remove `"ai-detection"` from revision- + provenance-analyser keywords
- [x] Commit assessment-bench `uv.lock` (assessment-lens CLAUDE.md was already tracked — audit miscall)
- [ ] document-analyser: drop stale `InferredMetadata` legacy — **deferred** (code change in schemas.py, verify truly unused first; not a hygiene rush)
- [x] Release cadence decided: **batch on main, no PyPI release this pass** — all changes are dev-facing (examples/README/keywords/LICENSE/lock), nothing runtime-affecting. Releases ride the next substantive change per package.

## Phase 2 — Embedding infrastructure (keystone)

**Decided 2026-06-13:** local **sentence-transformers** (text) + **CLIP/open_clip**
(image) · **one focused shared library** (new package, role `library`, à la
lens-contract — working name `lens-embed`; single-purpose, not a junk drawer) ·
**all modalities** in the first pass. Opt-in install so analyser cores stay light.

- [x] Stand up `lens-embed` 0.1.0: `embed_text/embed_texts` + `embed_image/embed_images`, `cosine_similarity`/`pairwise_similarity`/`most_similar`, pinned model ids (text `all-MiniLM-L6-v2`, image CLIP `ViT-B-32`), opt-in `[text]`/`[image]` extras, numpy-only core. **On PyPI + repo `michael-borck/lens-embed`.** 16 tests.
- [x] lens-embed 0.1.1: `embed_long_text` (mean-pooled document vector — pooling lives in lens-embed so per-analyser wiring stays a one-liner)
- [x] Wire text analysers — **DONE** (all on main, not released): document, reflection, code, speech (transcript), conversation. Each: opt-in `[embeddings]` extra (`lens-embed[text]`) + sibling source; tiny `embed_document()` helper (import-guard + `backend_available` + try/except → None); `embedding: list[float] | None = None` on the result model; embed the canonical text in the assembly; graceful None without the extra; no manifest change. Special cases handled: speech injects into its dict→AudioAnalysis; conversation **consolidated** its pre-existing `[embeddings]` extra onto `lens-embed[text]` (its internal prompt self-similarity still resolves sentence-transformers transitively).
- [x] Wire image/video/diagram — **DONE** (judgment call, flagged): only **image** is a true CLIP case (`lens-embed[image]`, embeds the image). **video** embeds its transcript text and **diagram** its source text (`lens-embed[text]`) — diagrams are text-format and a video's narration must be comparable to a *report*, which CLIP frames can't do. Per-key-frame CLIP (video) and rendered-image CLIP (diagram) are deferred refinements for visual similarity.
- [x] **Coordinated release wave DONE (2026-06-13)** — all 8 embedding-enabled members published to PyPI: document 0.8.0, reflection 0.2.0, code 1.3.0, speech 0.6.0, conversation 0.4.0, image 0.5.0, video 0.11.0, diagram 0.2.0. (lens-embed 0.1.1 underpins them.)

**✅ Phase 2 complete.** Every text-or-image artefact in the family now exposes an optional, comparable `embedding`. Phase 3 (distinctiveness) is unblocked.

## Phase 3 — Distinctiveness signal (cohort-relative)  ✅ (done 2026-06-13)

Compare each submission against the *others in the same batch* — signal-space
**and** raw-text (everything converts to text). Neutral, **direction-agnostic**
observation (standing apart can be an out-of-the-box answer *or* a thin one),
**never** a collusion/plagiarism verdict and never a quality judgement.

- [x] assessment-lens (0.2.0, on main): cohort post-pass in `assess()` — once every submission's vector is in hand, `distinctiveness.annotate_cohort` attaches a per-submission `Distinctiveness` across **three spaces** (text = pooled Phase-2 embeddings; signal = z-normalised numeric signal values; combined = the mean). Flags are **relative to the cohort's own distribution** (z-scores, `_MIN_FOR_RELATIVE=5`), so a tightly-clustered cohort (a prescriptive/weak task) doesn't trip everyone while a genuine outlier still surfaces — this resolves the clustering concern without needing a separate NN model. Pure consumer (numpy-only lens-embed core); degradable to None. Report shows per-space cohort comparison in student reports + a distinctiveness row in the cohort sheet.
- [x] assessment-bench (0.4.0, on main): **refined the home** — distinctiveness is arm-independent, so it lives on `ExperimentResult.distinctiveness` (per submission, once) not duplicated across each `ArmOutcome`. Reuses assessment-lens's `Distinctiveness` model unchanged. `run_signals_arm` → `run_cohort_pass` returns the full `AssessmentResult` so distinctiveness survives the one shared (expensive) analyser pass; pure-LLM experiments pay nothing. Surfaced as a correlatable measure (`distinctiveness.mean_similarity` vs human marks — answers "do the arms/marks treat distinctive submissions differently?") instead of a literal extra arm. New `distinctiveness.csv`.

## Phase 4 — Backlog (revisit after the above)

- **Per-analyser engagement signals** (all neutrally framed):
  - conversation → prompt-sophistication *trajectory*; human-vs-AI word-count asymmetry
  - reflection → specificity (concrete vs generic), temporal orientation, claim→evidence chain depth
  - document → stylistic variance across sections
  - revision → edit-churn/thrashing rate, large-block deletions
  - speech/video → disfluency/repair rate, prosody flatness, pacing coherence
  - code → per-function complexity distribution, test-presence, stylistic uniformity
  - git → incremental-vs-monolithic cadence, co-change patterns
  - provenance → normalized effort ratio (edit-time ÷ size), timestamp-order validity
- **Cross-artefact consistency** (consumer layer, built on Phase 2 vectors): does the video narration match the report? code match the reflection?
- **Framing rename** (schema-touching, own release): provenance `ai_generation_marker` → neutral authoring-tool/producer observation (the *blurb* is already neutralised in the README + table generator; the schema field rename is the remaining work)
- [x] **Umbrella rendered site** — DONE 2026-06-13. Quarto website over the existing markdown (no restructuring; Quarto was already in the toolchain). `_quarto.yml` + `index.qmd` (includes README, single source) + `.github/workflows/publish.yml` (render → Pages on push to main, Actions source). **Live: https://michael-borck.github.io/lens-analysers/**
- [x] **Cookbook repo** (`lens-cookbook`) — DONE 2026-06-15. Executable Quarto book; recipes use the uniform `from <pkg> import analyse` surface; pinned PyPI; `freeze` + local-render-then-publish. **Live: https://michael-borck.github.io/lens-cookbook/**
- auto-analyser: add cascade rules beyond image→diagram; validate preset member signal-richness

---

## Phase 5 — Desktop apps for non-technical users (Electron, privacy-first, local)

Two install-and-run desktop apps (no CLI) for educators, processing student
submissions **fully locally** for privacy, with a **local LLM via Ollama**.
All submission types day one; models bundled (offline); heavy packages
(torch/ffmpeg) installed first-run into an app-local dir. **assessment-lens app
first** (establishes the scaffold), **assessment-bench app second** (mostly UI —
its backend is ready). Reconnaissance done: every hard piece already exists in
sibling apps (talk-buddy = Python sidecar + first-run model install; insight/
career-compass = Ollama flow; document-lens = security; all five = identical
electron-builder/notarize/updater). See the desktop-app-patterns memory.

Sequence: **(a) prereqs → (b) design doc → (c) scaffold → app #1 → app #2.**

- [x] **(a) assessment-lens HTTP API** — DONE (v0.4.0, on main, not yet on PyPI): `serve` + `api.py` (`POST /assessments` → poll → result) + `manifest.py` (role lens) + `[serve]` extra. 51 tests.
- [x] **(a) assessment-lens local LLM provider** — DONE (0.4.0): `llm.py` now multi-provider — default Anthropic, `ASSESSMENT_LENS_PROVIDER=ollama` (or openai/openrouter) for fully-local narration. `[llm]` extra adds openai.
- [x] **(b) Design doc** — DONE: [docs/DESKTOP-APPS-DESIGN.md](DESKTOP-APPS-DESIGN.md) (on the site).
- [x] **(c) `lens-desktop` template** — SCAFFOLDED locally (`/Users/michael/Projects/lens/lens-desktop`, 23 files, git main; **no remote yet**). Sidecar manager, first-run installer (incl. the Windows `install.ps1`), Ollama module + card, electron-builder/notarize, minimal React shell. **Not yet npm-installed/launched — needs a verification pass (esp. per-OS first-run install) before app #1.**
- [x] **App #1: assessment-lens desktop** — SCAFFOLDED + builds clean. Repo `github.com/michael-borck/assessment-lens-desktop`. Marking UI (pick rubric + cohort → run → observations/deliverables/distinctiveness); file-picker + sidecar-proxy IPC (since backported into the template). **assessment-lens 0.4.0 released to PyPI** (unblocks first-run).
- [x] **App #2: assessment-bench desktop** — SCAFFOLDED + builds clean. Repo `github.com/michael-borck/assessment-bench-desktop`. Experiment UI (pick YAML → run → agreement-with-human-marks + arm reliability); `experiment:start` reads/resolves the YAML and POSTs to the bench sidecar. (assessment-bench 0.4.0 already on PyPI.)

**Remaining for both apps (needs real machines, not doable from here):** the live per-OS verification — launch the GUI, let first-run build the venv + install the full stack, confirm the sidecar serves and the workflow runs end to end on macOS / Windows / Linux. The Windows `install.ps1` is untested. Then tagged-build CI → electron-updater releases.

---

## Framing principle

The family observes **how a student worked** (process, engagement, critical
thinking, ownership of ideas) and surfaces it as neutral observations for a
human to interpret. It does **not** detect AI authorship and is never framed as
if it does — we can't, and a "detection" framing invites accusatory misuse.
Avoid the terms "AI detection / AI generation / AI flavour". Describe the
process; don't accuse the tool. (Consistent with the assessment-lens invariant:
the LLM narrates and cites; it never scores; a human marks.)

## Decision log

- **2026-06-13 — Embeddings:** local sentence-transformers (text) + CLIP/open_clip (image); one focused shared library (`lens-embed`, role `library`); all modalities in the first pass; opt-in install. Cores stay light.
