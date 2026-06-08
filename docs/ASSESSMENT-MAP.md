# Assessment map — what the family reads, and which assessments use what

> A reference for picking the right combination of analyser-family members
> for an assessment design. Pairs the family with the kinds of questions it
> can usefully answer.

Each `-analyser` reads a single signal source through a single interpretive
frame. None of them is a generalist. Useful assessments aren't built from a
single signal — they're **triangulated** across the family. This document
names the axes, plots each member, calls out high-stakes signals, and
proposes named bundles for common assessment shapes.

The doc carries **two complementary views** at different levels of detail:

| View | Question it answers | Best for |
|---|---|---|
| **[Simple view](#the-simple-view--product--process)** — Product × Process | *"Across my unit's assessments, am I generating both kinds of signal?"* | Course coordinators · workshop / PD / faculty conversations |
| **[Detailed view](#the-detailed-view--tool-signals)** — Convergent/Divergent × Product/Process | *"For this specific assessment, which exact tool generates which kind of signal?"* | Tool selection · bundle design · signal audit |

The simple view is the front door. The detailed view is for picking
specific tools. Same family, two reading depths.

> See also: [SIGNAL-CATALOGUE.md](./SIGNAL-CATALOGUE.md) (every signal each
> member emits, enumerated) ·
> [CONVENTIONS.md](../CONVENTIONS.md) (contract spec) ·
> [ADDING-A-MEMBER.md](../ADDING-A-MEMBER.md) (how to build a new member) ·
> [CANDIDATE-MEMBERS.md](../CANDIDATE-MEMBERS.md) (the backlog) ·
> the README's [family table](../README.md#the-family).

---

## The simple view — Product × Process

The starting question for unit-level assessment design: **does each
assessment generate signal on both dimensions, and does the unit as a whole
span both?** Two axes, both "more is better":

- **X — Product:** how much signal comes from the *artefact* the student
  submits (low → high coverage of the work itself).
- **Y — Process:** how much signal comes from *how the artefact came to be*
  (low → high coverage of the trajectory, authoring, revision, reflection).

```
                          HIGH PROCESS
                               │
        ┌─ Process-heavy ──────┼── IDEAL (fuller-spectrum) ──┐
        │  (process-only,      │  (artefact + drafting        │
        │   no artefact to     │   trail + reflection)        │
        │   show)              │                              │
        │                      │  e.g. major project + git    │
        │  e.g. reflective     │  history + reflection writeup│
        │  journal alone       │                              │
        ├──────────────────────┼──────────────────────────────┤
        │                      │                              │
        │  WEAK                │  Output-only                 │
        │  (almost no signal   │  (graded on the artefact     │
        │   from either        │   alone)                     │
        │   dimension)         │                              │
        │                      │  e.g. essay graded just on   │
        │  e.g. one-line       │  the text · timed skill-     │
        │  multiple choice     │  check exam                  │
        │                      │                              │
        └─ Low Process ────────┼── High Process ──────────────┘
                               │
                          LOW PROCESS
              ←─ LOW PRODUCT ────── HIGH PRODUCT ─→
```

### "Ideal = top-right" — but at the *unit* level, not per assessment

The top-right cell is fuller-spectrum: the assessment generates substantial
signal on both axes, so it's hard to game and easy to triangulate. But a
single assessment **doesn't need to live there**. A timed skill-check
(bottom-right, output-only) is a legitimate design when it sits inside a
unit that *also* includes a reflective journal (top-left, process-heavy) and
a major project + writeup (top-right, fuller-spectrum). The skill-check
isn't broken; it's playing a specific role.

What matters is **cumulative coverage across the unit**. Plot each
assessment as a dot on the quadrant. If the dots cluster in one cell —
especially bottom-right (output-only) or bottom-left (weak) — the unit is
unbalanced. If they spread across cells, the unit hits both dimensions
across the semester.

### Example — a unit plotted

The same ISYS1001 example used [below in detail](#unit-level-coverage--detailed-breakdown),
read as the simple view:

```
        HIGH PROCESS
              │
              │       ● A3  ● A4         ← project + journal; reflective essay
              │
              │
        ──────┼─────────────────
              │
              │
              │       ● A1  ● A2         ← programming lab; design portfolio
              │
        LOW PROCESS
   ←─ LOW PRODUCT ──── HIGH PRODUCT ─→
```

The diagnostic is immediate: the unit reaches top-right (A3 + A4 carry the
triangulation weight) so the cumulative coverage is fine. The absence of any
dot in the *left* half is informative but not damning — every assessment in
this unit produces a real artefact, so nothing is purely process-only.

A red-flag pattern in this view would be **all four assessments in
bottom-right** (output-only) or **the whole cluster in one cell**.

> The simple view tells you **whether** to add process or product signal to
> the unit. To decide **which** specific signals (and which tools generate
> them), drop down to the detailed view below.

---

## The detailed view — tool signals

Where the simple view treats Product and Process as scalar dimensions, the
detailed view splits each into two interpretive frames — giving four
distinct signal *types* that map to specific tools in the family.

**X — what's being read:** *Product* (the artifact submitted) ↔ *Process*
(how the artifact came to be).

**Y — what kind of question:** *Convergent* (verifiable, single right answer
or pass/fail) ↔ *Divergent* (open, qualitative, interpretive judgement).

Together they yield four quadrants with very different assessment-design
questions:

| Quadrant | Question | Examples of signals |
|---|---|---|
| **Q1 Correctness** | Did they do it right? | Code lints clean; formulas have no `#REF!`; citations resolve. |
| **Q2 Quality** | Is the work good? | Readability; accessibility; design coherence. |
| **Q3 Authenticity** | Did they do it themselves, properly? | Editing time; revision history; AI-gen markers; commit hygiene. |
| **Q4 Metacognition** | How did they think through this? | Reflective depth; AI-conversation critical-thinking; drafting trajectory. |

---

## The map

```
                          CONVERGENT (verifiable, right/wrong)
                                       │
        ┌─ Q1 CORRECTNESS ──────────────┼── Q3 AUTHENTICITY ─┐
        │                               │                    │
        │   • cite-sight                │   ⚠ provenance-    │
        │     • records-analyser        │     analyser       │
        │       • code-analyser         │                    │
        │     • wordpress-analyser      │  ⚠ revision-       │
        │  • spreadsheet-analyser       │     analyser·      │
        │      • image-analyser (OCR    │      • git-        │
        │         + barcode + C2pa)     │        analyser·   │
        │  ▸ site-analyser (a11y/links) │                    │
        │  ▸ video-analyser (quality)   │                    │
        │  ▸ diagram-analyser (struct)  │                    │
        │                               │                    │
        ├───────────────────────────────┼────────────────────┤
        │                               │                    │
        │  ▸ site-analyser (structure)  │  • revision-       │
        │            • document-analyser│    analyser·       │
        │            (readability+slide)│    (trajectory)    │
        │  ▸ diagram-analyser (vision)  │   • git-analyser·  │
        │            • speech-analyser  │     (narrative)    │
        │  ▸ video-analyser (scenes)    │                    │
        │                               │   ⚠ reflection-    │
        │                               │     analyser       │
        │                               │   ⚠ conversation-  │
        │                               │     analyser       │
        │                               │                    │
        └─ Q2 QUALITY ──────────────────┼── Q4 METACOGNITION ┘
                                       │
                          DIVERGENT (open, qualitative)
              ←─ PRODUCT (artifact) ── PROCESS (how it was made) ─→
```

**Legend.** `•` single-quadrant member; `▸` one read of a multi-quadrant
member (same package, different lens); `·` after a name means the same
member legitimately reads as either Q3 or Q4 depending on the question;
`⚠` marks high-stakes signals (see [Stakes](#stakes-)).

A few members appear in multiple positions on purpose:

- **`site-analyser`** splits between Q1 (WCAG / broken-link checks, which
  are pass/fail) and Q2 (structure, SEO, perf, which are interpretive).
- **`video-analyser`** splits between Q1 (per-frame quality metrics) and Q2
  (scene structure, transcript quality).
- **`diagram-analyser`** splits between Q1 (structural parsing — orphans,
  cycles, DAG-ness — deterministic) and Q2 (vision-extracted structure —
  interpretive).
- **`image-analyser`** spans Q1 (barcode/OCR/C2PA are convergent) and
  carries the `is_diagram` cascade trigger (a routing decision more than a
  signal).
- **`git-analyser`** and **`revision-analyser`** sit between Q3 and Q4 —
  the *same data* reads as **authenticity** when you ask "is this
  consistent with one human working honestly?" and as **metacognition**
  when you ask "what story do these edits tell about how the student
  thought?".

## The empty centre is by design

No member sits near the centre of the map. The family is composed of
**opinionated edge-tools, not blunt generalists**. Each member has a point
of view — *I read X, in interpretive frame Y*. Composition across members
is what produces nuance; a centred generalist would dilute the signal
rather than enrich it.

The orchestrators ([`auto-analyser`](https://github.com/michael-borck/auto-analyser),
[`bundle-analyser`](https://github.com/michael-borck/bundle-analyser)) wire
across members; the framework's value is precisely that it *requires*
composition. The named bundles in the next section make the common
compositions discoverable.

---

## Stakes — ⚠ flags vs informational signals

Not every signal is equal. Some surface **flags that can plausibly trigger
an integrity process**; others are **informational** — they inform grading
judgement but don't warrant escalation alone.

| ⚠ High-stakes member | Flags it produces | Why high-stakes |
|---|---|---|
| `provenance-analyser` | `ai_generation_marker`, `edit_time_low_for_size`, `author_mismatch`, `created_modified_same_minute` | Direct authorship-doubt signals |
| `revision-analyser` | `paste_burst_present`, `no_revisions_recorded` | Direct authorship-doubt signals |
| `reflection-analyser` | `descriptive` band on a graded reflective task | Direct effect on a grade |
| `conversation-analyser` | low critical-thinking score combined with high AI-coverage | AI-use disclosure / integrity signal |

The unannotated members produce informational signals (e.g. a Flesch-Kincaid
grade, a Lighthouse accessibility score, a `cite-sight` broken-citation
count). These inform feedback but don't on their own warrant academic-
misconduct processes.

> **Important.** High-stakes signals are *least* trustworthy when read in
> isolation. A 15-minute total editing time on its own proves nothing
> (maybe the student drafted in a different tool). A single paste-burst
> may be a quoted passage. Triangulation across quadrants is required for
> any consequential decision — not optional.

---

## The triangulation principle

**Robust assessments span ≥3 quadrants.** Single-quadrant assessments are
easy to game:

- Pure Q1 (just correctness) → an LLM can produce a passing answer in seconds.
- Pure Q2 (just quality) → an LLM can produce a polished essay or a
  competent design.
- Pure Q3 (just authenticity) → degenerates into surveillance theatre.
- Pure Q4 (just metacognition) → unverifiable claims about thinking.

The interesting story for any submission is **across** quadrants:

> A polished essay (Q2: `document-analyser`) + 15 minutes total editing
> time (Q3: `provenance-analyser`) + a single 1,800-word paste-burst (Q3:
> `revision-analyser`) + descriptive band on the accompanying reflection
> (Q4: `reflection-analyser`) tells a coherent story that no single signal
> can.

None of those numbers is conclusive alone. Together they're defensible.

---

## Discipline overlay

Each discipline naturally clusters in different quadrants. Worth knowing
when you're picking signals for a *new* assessment design.

| Discipline | Primary quadrants | Members typically used |
|---|---|---|
| **Programming** | Q1 + Q3 | code-analyser, git-analyser, provenance-analyser, wordpress-analyser |
| **Data / analytical** | Q1 (+ Q3 + Q4) | records-analyser, spreadsheet-analyser, provenance, reflection |
| **Written work** | Q2 + Q3 + Q4 | document-analyser, provenance, revision, reflection, cite-sight |
| **Web / multimedia** | Q2 + Q1 + Q3 | site-analyser, code, image, video, speech, provenance |
| **Design** (diagrams, slides, UI) | Q2 (+ Q3 + Q4) | diagram-analyser, document-analyser (slides), site, provenance, reflection |
| **Reflective / portfolio** | Q4 (+ Q3) | reflection-analyser, conversation-analyser, revision (trajectory), provenance |

Every discipline lands in ≥2 quadrants for a defensible design — no
single-quadrant assessment is sufficient in the current era.

---

## Worked examples

### Q1-anchored — programming lab ("build a working CRUD endpoint")

| Read | Member | Quadrant | What you learn |
|---|---|---|---|
| Primary | `code-analyser` | Q1 | Lint, complexity, tests pass |
| +Process | `git-analyser` (commit hygiene) | Q3 | Incremental commits vs one final push |
| +Process | `provenance-analyser` | Q3 | Files modified over hours, not minutes |
| +Meta | short writeup → `reflection-analyser` | Q4 | Reasoning about design choices |

Without Q3/Q4 cross-reads, this is gameable — an LLM produces clean linted
CRUD in 30 seconds. Adding `git` + `provenance` forces evidence of
construction; adding `reflection` forces evidence of understanding.

### Q2-anchored — portfolio website (ISYS3004 A1)

| Read | Member | Quadrant |
|---|---|---|
| Primary | `site-analyser` (deployed-site quality) | Q2 |
| +Source | `code-analyser` (HTML/CSS/JS style) | Q1 |
| +Process | `git-analyser` (commit timeline) | Q3 |
| Optional | reflection writeup → `reflection-analyser` | Q4 |

### Q3-anchored — anti-AI essay check

| Read | Member | Quadrant |
|---|---|---|
| Primary ⚠ | `provenance-analyser` | Q3 — editing time, creator app, AI markers |
| Primary ⚠ | `revision-analyser` | Q3 — paste-burst detection, drafting trail |
| +Product | `document-analyser` | Q2 — what the essay actually says |
| +Meta | `conversation-analyser` (if AI-chat is part of the brief) | Q4 |

A single-signal Q3 read is surveillance theatre; triangulating with
revision history *and* the document content gives a defensible story
when consequential conclusions are at stake.

### Q4-anchored — reflective journal / UDL portfolio

| Read | Member | Quadrant |
|---|---|---|
| Primary ⚠ | `reflection-analyser` | Q4 — depth band, metacognition, criticality |
| Cross-read | `conversation-analyser` if AI was used | Q4 |
| Trajectory | `revision-analyser` (as Q4 read) | Q4 — drafting as growth |
| Authenticity floor | `provenance-analyser` | Q3 |

A Q3 authenticity floor prevents "I had a transformative reflection that
I wrote in 4 minutes flat." It doesn't moralise — it gives the grader
context.

---

## Bundles — first-class presets

Common signal compositions get **named bundles**. Each bundle invokes
multiple members in parallel and aggregates the results. The orchestrator
(`auto-analyser`) is the home for these — the doc names them, the
implementation will follow once the orchestrator is updated.

| Preset name | Members invoked | When you use it |
|---|---|---|
| `skill-with-evidence` | code + git + provenance | Programming / build assessments |
| `authentic-essay` | document + provenance + revision + reflection | Written-work assessment in the AI era |
| `design-with-rationale` | diagram **or** site + provenance + reflection | Architecture / UI / portfolio tasks |
| `multimedia-evidence` | video + speech + image + provenance | Recorded artefact tasks |
| `reflective-practice` | reflection + conversation + revision (trajectory) | Reflective journals, UDL portfolios |

### Proposed orchestrator surface (not yet implemented)

```bash
auto-analyser --preset authentic-essay essay.docx
auto-analyser --preset skill-with-evidence app.py
auto-analyser presets                          # list available
```

```http
POST /analyse?preset=authentic-essay
```

The preset returns each invoked member's result plus a flattened list of
flags across the bundle:

```json
{
  "preset": "authentic-essay",
  "members": {
    "document-analyser": { ... },
    "provenance-analyser": { ... },
    "revision-analyser": { ... },
    "reflection-analyser": null
  },
  "flags_across_bundle": [
    "provenance-analyser:edit_time_low_for_size",
    "revision-analyser:paste_burst_present"
  ]
}
```

This differs from the existing **cascade routing** (one primary fires →
secondary invoked on a trigger predicate). Presets are *declarative
parallel composition*; cascade is *reactive sequential composition*. Both
mechanisms coexist in `auto-analyser`. Members that don't apply to the
input format are gracefully skipped (`null`), not errors.

---

## Where the family is currently thin

The map exposes coverage gaps honestly.

| Quadrant | Coverage | Notes |
|---|---|---|
| **Q1 Correctness** | Dense (6 members) | Well-covered |
| **Q2 Quality** | Dense (5 dedicated + 3 splits) | Well-covered |
| **Q3 Authenticity** | Good (provenance + revision + git) | Recent batch closed the gap |
| **Q4 Metacognition** | **Thinnest** (2 dedicated + 2 cross-reads) | Where deliberate growth is needed |

The remaining process-axis candidate in
[CANDIDATE-MEMBERS.md](../CANDIDATE-MEMBERS.md) — `activity-analyser` (LMS
exports → engagement timeline / time-on-task) — would land squarely in Q4.

---

## Unit-level coverage — detailed breakdown

The [simple view](#the-simple-view--product--process) above answers
*"does the unit reach top-right?"* at a glance. This section is the
deeper read: for each assessment, *which* of the four detailed quadrants
it touches, and what the per-quadrant unit coverage looks like.

Same ISYS1001 example, read through the four detailed quadrants:

```
Unit: ISYS1001 — 4 assessments
                              Q1   Q2   Q3   Q4
A1: Programming lab           ●●   ·    ·    ·    output-only (simple view)
A2: Design portfolio          ·    ●●   ·    ·    output-only (simple view)
A3: Final project + journal   ●    ●    ●    ●    top-right (simple view)
A4: Reflective essay          ·    ●    ●    ●    top-right (simple view)
                              ──   ──   ──   ──
Unit coverage:                2    3    2    2    ✓ all 4 quadrants reached

Recommendations:
- A1 + A2 sit in the simple view's bottom-right (output-only). That's a
  legitimate role for skill-check assessments, AS LONG AS A3+A4 carry the
  triangulation weight at the unit level — which they do here.
- If you wanted to move A1 toward top-right, the obvious lever is a
  process artefact (commit history via git-analyser, or a dev log →
  reflection-analyser).
- The unit as a whole is well-balanced across all four detailed quadrants;
  students touch each kind of signal across the semester.
```

Both views answer the same question (*"is this unit balanced?"*) at
different resolutions. The simple view is the educator-friendly executive
summary; the detailed view tells you which specific signal types each
assessment generates — and from there, [which named bundle](#bundles--first-class-presets)
or hand-picked tools to wire up.

A unit-level audit tool is intentionally *not* in the family right now —
see [Related tools](#related-tools-for-assessment-design) below for what
already exists in this space and why we haven't built another.

### Related tools for assessment design

The analyser family is **reactive** — it takes student submissions and
produces signals. Adjacent tools cover the **prescriptive** side:

- **[udl-lens](https://github.com/michael-borck/udl-lens)** — a web tool
  that audits assessments against the UDL Guidelines 3.0. AI pre-fills
  checkpoint ratings from briefs, produces a radar chart and PDF report.
  It's a *complementary* lens: UDL asks "is this assessment inclusive and
  accessible?", the quadrant map asks "what kind of evidence does it
  actually generate?". A unit can rate well on one and poorly on the
  other — both lenses matter.
- **[curriculum-curator](https://github.com/michael-borck/curriculum-curator)**
  — content-creation tool for authoring curriculum (9 teaching
  philosophies, AI-assisted, exports to LMS formats). Useful when you're
  *building* assessments, not auditing them.

A dedicated "quadrant-audit" tool isn't on the roadmap — the framework is
captured here in docs, and if real educator demand emerges, the natural
home would be a second lens inside `udl-lens` (same workflow, same
audience, same input format) rather than a standalone build.

---

## How to use this doc

**As an educator designing a single assessment:**

1. Decide what *kind* of question you want the assessment to answer — pick
   1–4 quadrants from the [quadrant table](#the-two-axes).
2. Cross-reference with the [discipline overlay](#discipline-overlay) to
   find the members that fit your subject.
3. If a [named bundle](#bundles--first-class-presets) matches, use it.
4. Otherwise, hand-pick members across ≥3 quadrants. Heed the
   [triangulation principle](#the-triangulation-principle) — single-
   quadrant assessments are gameable.
5. For consequential decisions, never act on a ⚠ high-stakes flag alone —
   always read it in the context of the other quadrants.

**As an educator designing a unit's assessment plan:**

1. **Start with the [simple view](#the-simple-view--product--process).**
   Plot each of your unit's assessments as a dot on the Product × Process
   quadrant. If the dots cluster in one cell (especially bottom-right —
   output-only — or bottom-left — weak), the unit is unbalanced.
2. The *unit's cumulative coverage* should reach top-right; individual
   assessments don't all need to. A timed skill-check + a reflective
   journal + a major project together can cover both axes even though
   each one is single-cell.
3. **For more detail**, drop into the [unit-level coverage breakdown](#unit-level-coverage--detailed-breakdown)
   — which of the four detailed quadrants each assessment touches.
4. Pair this lens with `udl-lens` (UDL audit per assessment) — neither
   replaces the other; UDL asks "is it inclusive?" while this map asks
   "what kind of evidence does it generate?".

**As a developer building a new member:**

1. Plot where it would sit on the map. If it lands in an empty area, it
   may be a genuine new member.
2. If it overlaps an existing member's quadrant *and* reads the same bytes
   the same way, it's a feature of that member, not a new one. See [the
   "is this a new member?" test](../CANDIDATE-MEMBERS.md#the-test-for-is-this-a-new-member)
   in CANDIDATE-MEMBERS.md.
3. If it adds a Q4-quadrant signal, prioritise it — that's where the
   family is thinnest.
