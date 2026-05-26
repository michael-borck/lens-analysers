# Candidate members — analysers we might add

A living backlog of possible future `-analyser` engines. **Nothing here is a
commitment** — it's a shortlist to react to, prune, and pull from. Signals are
sketched, not validated; they need a real audit before building.

**As of 2026-05-26** the product axis is well-covered — all originally-listed
product candidates have shipped (see [Graduated](#graduated-from-candidate)
below). The **process axis** is where the family is thinnest and where the
highest-value gaps remain. `git-analyser` and `conversation-analyser` are the
only process members shipped so far; the four candidates listed below are the
frontier.

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

## Process-signal candidates (the frontier)

| Candidate | Ingests | Example signals | Distinct because |
|---|---|---|---|
| **revision-analyser** | doc version history (Google Docs export, Word tracked-changes, or a sequence of drafts) | drafting trajectory, revision depth, growth-over-time, **paste-burst detection** (large insertions ≈ copy/AI) | reads *how a document evolved*, not its final text. The single strongest written-work process signal; nothing covers it. |
| **activity-analyser** | LMS activity export (Moodle / Canvas / Blackboard) | engagement timeline, time-on-task, submission timing, resource access | `records-analyser` profiles the raw CSV; this is the domain layer that turns it into *engagement* signals. |
| **provenance-analyser** | document/file metadata | Office "total editing time", revision count, author chain, creating app, C2PA / AI-gen markers | authorship/effort/AI-origin signal. `image-analyser` already does this for images (C2PA); this generalises it to docs. |
| **reflection-analyser** | reflective writing / learning journals | metacognition markers, criticality, depth of reflection | a *content interpretation* distinct from `document-analyser`'s readability; UDL/process-aligned (likely `auto_routable: false`, like conversation-analyser). |

## Product-signal candidates

_All listed product candidates have shipped — see [Graduated](#graduated-from-candidate) below. New product gaps that surface in real assessment use can be added here._

## Deliberately *not* separate members (deepen the existing one instead)

- **PDF / prose** → `document-analyser` already owns these bytes.
- **Jupyter notebooks** → `code-analyser` already handles `.ipynb`; deepen it (narrative↔code ratio, reproducibility) rather than split.
- **Slides-as-design** (deck density/title coverage/text overload/layout diversity) → **shipped as part of `document-analyser` 0.6.0** ([slide_design block on .pptx](https://pypi.org/project/document-analyser/)).
- **Math / LaTeX** → fold into `document-analyser` if it ever matters; too niche to split.

---

## Graduated from candidate

New family members shipped:

- **spreadsheet-analyser** → [v0.1.0](https://pypi.org/project/spreadsheet-analyser/) (2026-05-26). Explicit-only formula-logic interpretation; `.xlsx` continues to auto-route to records-analyser for data values.
- **site-analyser** → [v0.1.0](https://pypi.org/project/site-analyser/) (2026-05-26). Hybrid pure-Python core (httpx + bs4 + html5lib) with optional Lighthouse/vnu shell-out. Accepts a URL or a local static-site dir.
- **diagram-analyser** → [v0.1.0](https://pypi.org/project/diagram-analyser/) (2026-05-26). mermaid / PlantUML / Graphviz / drawio text formats (auto-routable) + optional `[vision]` extra for image diagrams via Anthropic Claude Vision.

Cross-member extensions that complete the cascade chain:

- **image-analyser 0.4.0** → adds an `is_diagram` heuristic signal (color quantization + flat-region ratio, ~50 ms) with optional vision-confirm via the existing `[api]` extra. The signal lives on the image-analyser result; the cascade decision lives in auto-analyser.
- **auto-analyser 0.5.0** → adds **cascade routing**. When a primary's result satisfies a rule's trigger predicate, the same file is forwarded to a downstream member and its result attached under a `cascade` key. v1 rule: `image-analyser.diagram.is_diagram == True → diagram-analyser`. Best-effort: failures attach `cascade.error` rather than failing the primary. Also adds the three new members to the default config and the static-routes fallback.
- **document-analyser 0.6.0** → adds the **slide-design** block (python-pptx) on `.pptx` input — slide count, title coverage, words-per-slide, images-per-slide, bullet depth, layout diversity, empty slides, text-overloaded slides. Additive on top of existing prose/readability.

## Caveats

- These target **university assessment** signals; usefulness depends on the
  assessment design and will shift as the field moves process-over-product.
- Several process candidates are **data-availability-bound** (revision history, LMS
  logs, keystroke telemetry) and **privacy-sensitive** — scope and consent matter
  before building.
- Audit the *signals* (do they predict/inform anything useful?) before the *code*.

> When one of these graduates from candidate to build, follow
> [ADDING-A-MEMBER.md](ADDING-A-MEMBER.md).
