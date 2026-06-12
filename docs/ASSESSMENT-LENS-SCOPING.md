# assessment-lens — scoping

Working scope for **assessment-lens**, a `document-lens`-style **lens** (product)
that helps a lecturer run **signals-based assessment**: tools generate signals
about student submissions; the lens maps those signals to a rubric as
**observations, not grades**; the lecturer reads them, weighs them, and assigns
the mark. The AI never marks; a human stays in the loop.

> Architecture rationale: [ADR-0001](./adr/0001-alignment-lives-in-assessment-lens.md).
> Signals it consumes: [SIGNAL-CATALOGUE.md](./SIGNAL-CATALOGUE.md).
> Assessment-design framing: [ASSESSMENT-MAP.md](./ASSESSMENT-MAP.md).
> Status: built — assessment-lens 0.2.0 on PyPI (CLI; Electron/web later). This doc is the design record.

## What it is (and isn't)
- A **lens** (assessment-aware product), not an `-analyser`. It *consumes* analysers; it does not generate signals.
- **Alignment** (submission ↔ spec + rubric) is an **internal module** (`alignment-check`), not a standalone member (no second consumer → rule of three).
- The processing app is **dumb about a submission's meaning** — it works on folders. Group/individual splits, folder assembly, and mark-combining are handled *outside* (pre/post-processing) or by running the app per folder.

## Glossary
- **Assignment** — a task set to a cohort; owns a Specification and a Rubric.
- **Specification** — the human-readable brief (what to do / submit). Free-form is the common case.
- **Expected Deliverable** — a thing the Specification requires ("2000-word report", "5-min video"); has an `accepts` content-kind.
- **Rubric → Criterion** — the marking criteria; one Criterion = one judged dimension (may pin `signals_of_interest`).
- **Submission** — what *one student or one group* handed in = **one subfolder**. The app neither knows nor cares which.
- **Artefact** — one file inside a Submission.
- **Signal** — a raw observation an analyser emits about an Artefact (see SIGNAL-CATALOGUE).
- **Observation** — a Signal (or few) *mapped to a Criterion or Deliverable*, with cited evidence + a short narration + coverage. **Never a grade.** The unit `alignment-check` produces.

## Pipeline
```
Specification ──draft-rubric (LLM, reviewed)──▶ Rubric (Criteria + mapping) + Expected Deliverables  [structured YAML/JSON]
Submissions root ──discover──▶ one Submission per subfolder (= Artefacts)
each Submission folder ──bundle-analyser──▶ Signals          (bundle → auto-analyser → analysers)
Signals + Criteria + Deliverables ──alignment-check──▶ Observations (per criterion, evidence-bound)
                                                          └─▶ cohort triage sheet + per-student reports
lecturer reads observations → assigns marks → writes feedback
```

## Two commands
- **`draft-rubric`** — free-form Specification → *proposed* structured rubric + deliverables + signal→criterion mapping. LLM-assisted; reuses `document-analyser` text extraction; **output is reviewed/edited by the lecturer** before use. Emits *per-component* rubrics for group+individual splits (group/individual awareness lives here, never in `assess`).
- **`assess`** — structured rubric + a submissions folder → Observations (cohort sheet + per-student reports).

## Composition
- `assessment-lens` composes **only `bundle-analyser`**, called **once per Submission subfolder** (preserves the student/group boundary). bundle-analyser handles per-file routing (via `auto-analyser`) + aggregation. The lens never talks to individual analysers or `auto-analyser` directly.
- **Deliverable reconciliation is the lens's own job** — it maps a submission's files to `expected_deliverables` by `accepts`, emitting a deterministic Observation when one is missing/wrong-type.

## Rubric / deliverables schema (the central contract)
```yaml
assignment: "Data-Viz Project"
component: individual            # plain label; assess ignores it
expected_deliverables:
  - id: report
    description: "Written report (~2000 words)"
    accepts: [document]
  - id: demo
    description: "≤5-min recorded demo"
    accepts: [video]
rubric:
  - id: critical-thinking
    description: "Evidence of critical engagement / analysis"
    signals_of_interest: [conversation.critical_thinking, reflection.depth]   # OPTIONAL mapping
  - id: technical-quality
    description: "Code quality and correctness"
    signals_of_interest: [code.complexity, code.lint, code.code_level]
```
- `signals_of_interest` is the **signal→criterion mapping**, and it is **optional**. Pinned → deterministic. Blank → `alignment-check` selects signals at runtime and shows its choice in the evidence.
- The mapping is **confirmed/edited once per assignment** (at the rubric stage), not per submission — which also keeps it consistent across the cohort.

## Observation schema (the output)
```yaml
# per submission, per criterion (and per missing deliverable)
observations:
  - criterion_id: critical-thinking
    evidence:                                  # deterministic anchor (cited signals + values)
      - { signal: conversation.critical_thinking, value: 62 }
      - { signal: reflection.depth, value: "dialogic" }
    note: "Pushback on 3 of 11 turns; dialogic reflection — moderate engagement."   # LLM narration, bound to evidence
    coverage: partial                          # present | partial | absent
  - deliverable_id: demo
    status: missing
    note: "Expected a ≤5-min video demo; none found."
```
- **`coverage`** = *is the evidence there?* (NOT a mark). **Deterministic from thresholds** where `signals_of_interest` are pinned; an LLM-suggested coverage is always flagged as a suggestion.

## Core principles (candidate ADRs in the assessment-lens repo)
1. **The LLM narrates and cites; it never scores.** Signals (deterministic) are the anchor; observations cite them; coverage is threshold-derived where possible. This is the whole point — LLMs are inconsistent at the precise act of marking, so the lens keeps them off it. A human assigns every mark.
2. **The app is folder-dumb.** All "what kind of assessment is this" complexity is handled by pre/post-processing or by running `assess` per folder. `assess` only ever sees: one rubric + one folder of submission subfolders.

## Output
- One **structured result** (JSON) is the source of truth; rendered into:
  - a **cohort triage sheet** — row per *(submission × criterion)*, sortable (e.g. all `coverage: absent`), for 300-cohort scale;
  - **per-student observation reports** — one readable sheet per submission, for the marking + feedback moment.

## MVP boundary
- **In v1:** CLI; one assignment; **structured rubric supplied as input**; folder-per-submission; compose `bundle-analyser`; `alignment-check` (narrate + cite + threshold coverage); cohort sheet + per-student reports.
- **Near-term (separate workstream):** `draft-rubric` (free-form spec → proposed rubric), since free-form is the common case.
- **Deferred:** Electron/web UI; multi-assignment management; the analyser-bundling/packaging story for desktop (the whole ML stack must be reachable — likely talk to analyser *services* rather than bundle them all).

## Harvest from video-analyser (head-start, do not rewrite from scratch)
When scaffolding assessment-lens, lift + adapt the assessment subsystem removed
from **video-analyser** at pre-removal commit **`b3ae7e19`** (`git show b3ae7e19:<path>`):

| Path (in video-analyser @ b3ae7e19) | Reuse |
|---|---|
| `src/video_analyser/analysis/rubric_system.py` (Rubric / Criterion / `RubricRepository`) | **High — lift mostly as-is** (this is our rubric model + storage) |
| `src/video_analyser/analysis/default_rubrics.py` | **High** — starter rubrics for `draft-rubric` |
| `src/video_analyser/utils/api_keys.py` | **High** — multi-provider LLM key mgmt |
| `src/video_analyser/reports/assessment_session.py` · `assessment_storage.py` · `assessment_report.py` · `assessment_integration.py` | **Medium — lift + adapt** to Submission/Observation model |
| `src/video_analyser/reports/grading_sheet_renderer.py` | **Medium — adapt** to render *observations* (cohort sheet + per-student) |
| `src/video_analyser/cli.py` `_build_grading_prompt` / `_generate_grading_feedback` | **Reference only — rewrite** to *narrate-and-cite, never score* |

## ✅ Released (2026-06-11)
The hold is over: **`assessment-lens` 0.2.0** landed LLM narration (`assess --llm`)
and `draft-rubric` (both narrate-and-cite, never score) and is on PyPI, so
**`video-analyser` 0.10.0** (grading removed, ADR-0001) was published to PyPI the
same day. video-analyser's README points `--grade` users at assessment-lens as the
migration path. `main` and PyPI are back in sync for video-analyser.

## Open questions for the next pass
- Stack specifics: Python CLI first; what to lift from `document-lens` for the eventual Electron app.
- How `assess` reaches `bundle-analyser` at runtime (CLI subprocess vs HTTP) and how the analyser stack is provisioned.
- Coverage threshold definitions — where the lecturer sets them (in the rubric per criterion?).
- LLM provider/keys reuse (align with the family's existing `HF_TOKEN`/provider config patterns).
