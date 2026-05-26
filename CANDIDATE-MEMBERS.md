# Candidate members — analysers we might add

A living backlog of possible future `-analyser` engines. **Nothing here is a
commitment** — it's a shortlist to react to, prune, and pull from. Signals are
sketched, not validated; they need a real audit before building.

Context: the family today is **almost entirely product-signal**. The only process
seeds are `git-analyser` (how code was built) and `conversation-analyser` (how the
student engaged with AI). As assessment shifts **process over product**, the
process axis is where the family is thinnest — and where the higher-value gaps are.

## The test for "is this a new member?"

A new member earns its place by being **a distinct content type _or_ a distinct
signal source**:

- **Distinct content type** — a new format/extension nothing else claims
  (e.g. a spreadsheet's *formulas*, a structured diagram).
- **Distinct signal source** — the same artifact read for a different *kind* of
  signal, especially **process vs product** (e.g. a document's *revision history*
  rather than its text).

If it's the *same bytes a member already claims, read the same way*, it's a **deeper
feature** of that member (or an explicit-only *interpretation* like
`conversation-analyser`) — **not** a new member. That distinction is what keeps the
family from re-accumulating drift.

## Triangulation (for the signal audit)

Product analysers aren't made obsolete by the process shift — they become *inputs*
the process analysers contextualise. The interesting signal is **triangulated**: a
polished document (`document-analyser`) + a thin revision trail (`revision-analyser`)
+ an AI chat with low critical-thinking (`conversation-analyser`) tells a very
different story than the same document with a rich drafting history. Product is one
axis; process is the complementary one.

---

## Process-signal candidates (priority — the frontier)

| Candidate | Ingests | Example signals | Distinct because |
|---|---|---|---|
| **revision-analyser** | doc version history (Google Docs export, Word tracked-changes, or a sequence of drafts) | drafting trajectory, revision depth, growth-over-time, **paste-burst detection** (large insertions ≈ copy/AI) | reads *how a document evolved*, not its final text. The single strongest written-work process signal; nothing covers it. |
| **activity-analyser** | LMS activity export (Moodle / Canvas / Blackboard) | engagement timeline, time-on-task, submission timing, resource access | `records-analyser` profiles the raw CSV; this is the domain layer that turns it into *engagement* signals. |
| **provenance-analyser** | document/file metadata | Office "total editing time", revision count, author chain, creating app, C2PA / AI-gen markers | authorship/effort/AI-origin signal. `image-analyser` already does this for images (C2PA); this generalises it to docs. |
| **reflection-analyser** | reflective writing / learning journals | metacognition markers, criticality, depth of reflection | a *content interpretation* distinct from `document-analyser`'s readability; UDL/process-aligned (likely `auto_routable: false`, like conversation-analyser). |

## Product-signal candidates (completeness — "a start")

| Candidate | Ingests | Example signals | Distinct because |
|---|---|---|---|
| **diagram-analyser** | structured diagrams (`.mmd`/mermaid, drawio, PlantUML, `.puml`); image diagrams via vision | entities, relationships, orphan nodes, cycles, correctness/consistency vs a brief | `image-analyser` only sees raster pixels; these have semantic structure. Gap for CS/IS design units. **Planned** ([plan](docs/superpowers/plans/2026-05-26-product-analysers-plan.md)). |
| **site-analyser** | a deployed site / URL, or a local static-site dir | WCAG accessibility, structure, link health, performance, framework detection, validity | `code-analyser` reads source files, not the *rendered/deployed* site. Good for web-dev assessment. **Planned** ([plan](docs/superpowers/plans/2026-05-26-product-analysers-plan.md)). |

### Graduated from candidate

- **spreadsheet-analyser** → shipped as [v0.1.0](https://pypi.org/project/spreadsheet-analyser/) (2026-05-26). Explicit-only formula-logic interpretation; `.xlsx` continues to auto-route to records-analyser for data values.

## Deliberately *not* separate members (deepen the existing one instead)

- **PDF / prose** → `document-analyser` already owns these bytes.
- **Jupyter notebooks** → `code-analyser` already handles `.ipynb`; deepen it (narrative↔code ratio, reproducibility) rather than split.
- **Slides-as-design** (deck density/whitespace/consistency) → a feature of `document-analyser` (it already takes `.pptx`), not a new member.
- **Math / LaTeX** → fold into `document-analyser` if it ever matters; too niche to split.

## Caveats

- These target **university assessment** signals; usefulness depends on the
  assessment design and will shift as the field moves process-over-product.
- Several process candidates are **data-availability-bound** (revision history, LMS
  logs, keystroke telemetry) and **privacy-sensitive** — scope and consent matter
  before building.
- Audit the *signals* (do they predict/inform anything useful?) before the *code*.

> When one of these graduates from candidate to build, follow
> [ADDING-A-MEMBER.md](ADDING-A-MEMBER.md).
