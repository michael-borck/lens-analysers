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

- [ ] Stand up `lens-embed`: `embed_text()` (sentence-transformers) + `embed_image()` (CLIP); pinned model ids; opt-in extras
- [ ] Wire text analysers (document, conversation, reflection, speech transcript, code) to expose an optional embedding in their result model + manifest `produces`
- [ ] Wire image/video/diagram to expose CLIP vectors (video = per-key-frame)
- [ ] New PyPI project + repo for `lens-embed` (mind the new-project rate cap)

## Phase 3 — Distinctiveness signal (cohort-relative)

Compare each submission against the *others in the same batch* — signal-space
**and** raw-text (everything converts to text). Neutral "unusually similar to X"
observation, **never** a collusion/plagiarism verdict.

- [ ] assessment-lens: cohort mode — collect all submissions' evidence first, then add a distinctiveness Observation per criterion (seam: `alignment.gather_evidence`)
- [ ] assessment-bench: distinctiveness field on `ArmOutcome` (distance matrix / similarity-to-centroid), optionally its own measured arm

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
- **Framing rename** (schema-touching, own release): provenance `ai_generation_marker` → neutral authoring-tool/producer observation
- **Umbrella rendered site**: Quarto → GitHub Pages (conceptual docs + the generated family table)
- **Cookbook repo** (`lens-cookbook`): end-to-end multi-tool use cases + shared mock cohorts (sample PDF/audio/video/code), reused by assessment-lens, assessment-bench, and demos
- auto-analyser: add cascade rules beyond image→diagram; validate preset member signal-richness

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
