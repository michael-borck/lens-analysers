# Alignment lives in assessment-lens (a lens), not a standalone analyser

**Status:** accepted

Judging a submission against an *assignment specification + rubric* ("alignment")
is **assessment-aware**, which by the family's own definition disqualifies it from
the analyser layer — analysers are *reusable, assessment-agnostic signal
generators*. So alignment lives one layer up, in a new **`assessment-lens`**: a
`document-lens`-style product (CLI first, Electron/web later) that orchestrates
the analysers and holds the assessment logic. Alignment is an **internal module**
inside that lens (`alignment-check`: signals + spec + rubric → per-criterion
alignment), **not** a standalone `-analyser`.

**Why a module, not a standalone member:** there is no consumer of "alignment"
outside assessment today, so the family's *rule of three* (extract a shared util
only at the third use) says keep it in-app. Precedent: `document-lens` keeps its
Wedding Cake *scoring* (signals + rubric → judgement, the same shape) inside the
lens, never as a `scoring-analyser`. Keeping "analyser" meaning exactly one thing
— an agnostic signal generator — is what keeps the whole family composable.

**Consequence:** the LLM rubric-grading currently embedded in `video-analyser`
(an assessment-aware act inside an analyser) moves **up** into `assessment-lens`'s
alignment module. `video-analyser` reverts to emitting signals only.

**Revisit when:** a second, non-assessment consumer of pure alignment appears
(e.g. "does this report meet a brief/template", or a UDL-checklist check) — then
lift `alignment-check` into a standalone member (rule of three).

**Note — two distinct senses of "alignment", do not conflate:**
1. **Audio-visual coherence** (within `video-analyser`): do the on-screen visuals
   match the narration? A *signal* about the artefact itself — stays in the
   analyser layer (could become an explicit video-analyser signal).
2. **Submission ↔ specification alignment** (this ADR): does the work meet the
   assignment + rubric? An *assessment-aware judgement* — lives in `assessment-lens`.
