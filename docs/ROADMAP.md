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

## Phase 1 — Hygiene sweep

- [ ] Add a thin `examples/` (single-tool usage snippet) to every analyser
- [ ] git-analyser: replace placeholder README, fix "Planning" → shipped status
- [ ] wordpress-analyser: same
- [ ] bundle-analyser: LICENSE © 2024 → 2026; flesh out the minimal README
- [ ] Remove `"ai-detection"` from revision-analyser + provenance-analyser pyproject keywords
- [ ] Commit untracked: assessment-lens `CLAUDE.md`, assessment-bench `uv.lock`
- [ ] document-analyser: drop stale `InferredMetadata` legacy
- [ ] Decide release cadence (default: batch on main, release in waves — mind the PyPI new-project/throughput cap)

## Phase 2 — Embedding infrastructure (keystone)

Open decisions (locking now): model · structure · modality scope. See the
decision log below once answered.

- [ ] Add optional embedding output to the text analysers (document, conversation, reflection, speech transcript, code)
- [ ] (if all-modality) CLIP-style vectors for image / video / diagram
- [ ] Expose via result model + manifest `produces`; behind an opt-in extra so core stays light

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

- _(pending)_ Embedding model · structure · modality scope — see open questions.
