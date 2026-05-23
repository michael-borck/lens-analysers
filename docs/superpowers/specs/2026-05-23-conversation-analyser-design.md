# conversation-analyser: Critical-Thinking Analysis of AI Conversations (Design)

**Date:** 2026-05-23
**Author:** Dr Michael Borck (with Claude)
**Scope:** A new member of the `lens` analyser family that scores a single AI conversation on two tiers — domain-neutral analytics, and AI-literacy / critical-thinking of the human's prompting.
**Status:** Awaiting user review before implementation planning.

---

## 1. Purpose

Build a standalone `lens` analyser, `conversation-analyser`, that ingests one human↔AI conversation (structured or raw text) and produces a structured `ConversationAnalysis`:

1. **Analytics tier** (always on, offline) — domain-neutral conversation metrics: turn/word counts, prompt/response lengths, question ratio, pushback hits, readability, sentiment trajectory, prompt self-similarity, and (when timestamps exist) temporal metrics.
2. **Critical-thinking tier** (opt-in, needs an LLM) — classifies every human turn under a 7-label prompt taxonomy, derives engagement ratios, an engagement **band**, and a composite **0–100 critical-thinking score** with a transparent component breakdown.

The critical-thinking tier reuses the validated taxonomy, prompts, and band heuristic from `curtin/ISYS6020-Assignment-2-Submissions/src/marking_pipeline/` (`taxonomy.py`, `config.py`, `transcript.py`). Those are **copied** into this package and from then on evolve independently (see §11).

It fits the family's "north-star" contract (see `ANALYSER-FAMILY-UX-GOTCHAS.md`): `ConversationAnalyser().analyse(input) -> ConversationAnalysis` (a pydantic model), CLI `conversation-analyser <path> [--json]`, British spelling, JSON to stdout / diagnostics to stderr.

## 2. Non-goals

- **Not a corpus tool.** One conversation per `analyse()` call. Batch/folder/zip handling is `auto-analyser`/`bundle-analyser`'s job. (Idle-gap sub-session splitting *within* one input is in scope — §6.)
- **Not grading.** No rubric pass, no marks, no Blackboard/Turnitin/gradebook handling, no group membership or collation. That stays in `marking_pipeline`.
- **Not assistant-quality scoring.** The subject is the *human's* prompting and the conversation's shape, not the correctness/helpfulness of the AI's answers.
- **Not auto-routing yet.** `auto-analyser` will not silently re-route `.txt`/`.pdf` to this analyser in v1 (see §12).
- **No second-axis taxonomy** (e.g. Bloom's). The 7-label FU/EX set is the only taxonomy.

## 3. Inputs and parsing

Input is a file path (or in-memory text/dict via the Python API). Parsing is **configurable** with a default chain and a **pluggable adapter registry**.

### 3.1 Parse strategy (configurable, default order)

1. **Structured-first.** Try registered structured adapters (§3.2). Highest role fidelity.
2. **Heuristic markers.** For flat text, detect speaker markers (`User:`/`Assistant:`, `Me:`/`ChatGPT:`, `You said:`/`ChatGPT said:`, `Prompt:`/`Response:`, numbered prompts). No LLM.
3. **LLM-segment fallback** (opt-in, needs `[llm]`). The LLM finds and labels each human message directly from arbitrary raw text (port of `taxonomy.classify_transcript` / `SEGMENT_SYSTEM_PROMPT`).

The chosen path is recorded in the result as `parse_mode` (`structured` | `heuristic` | `llm-segment`). Fidelity ranking: structured > heuristic > llm-segment.

### 3.2 Adapter registry (ship 3 + fallback)

A small registry maps a format-detector → parser, so new formats are added by registering an adapter, not by editing core parse code. Ship:

- **`role_content`** — a `[{role, content}, ...]` message list (OpenAI / Anthropic de-facto standard). `role ∈ {user/human, assistant/ai, system}`.
- **`anythingllm`** — `prompt`/`response` paired rows (the AnythingLLM `embed_chats` shape; each row is one human turn + one AI turn).
- **`markers`** — flat-text speaker markers (the heuristic above), also exposed as an adapter.
- **LLM-segment** is the registry's terminal fallback when no adapter matches.

Deferred adapters (documented, not built): ChatGPT account export (nested `mapping` tree), Claude export.

### 3.3 Text extraction for binary inputs

For `.pdf`/`.docx` transcripts, reuse the family's extraction (the `document-analyser` approach: `pdfplumber` for PDF, `markitdown` otherwise) to get raw text, then run the parse chain (markers → llm-segment). The analyser does not re-implement extraction.

## 4. The prompt taxonomy (reused as-is)

Each **human** turn is assigned exactly one of seven mutually-exclusive labels (verbatim from `marking_pipeline/taxonomy.py`):

| Code | Name | Meaning |
|---|---|---|
| `NQ` | New Query | opens a new topic; does not build on the prior turn |
| `FU` | Follow-up | asks for clarification or elaboration on the AI's prior response |
| `CH` | Challenge | pushes back, asks why, requests alternatives, disagrees, tests the AI |
| `EX` | Extension | extends the response in a new direction; applies to a specific context; compares; synthesises |
| `DG` | Delegation | task hand-off with no engagement with the prior response |
| `AC` | Acknowledgement | pure confirmation or thanks; no content |
| `MT` | Meta | about the conversation itself ("go back to…", "summarise so far") |

Tiebreaker rules (CH vs EX, FU vs CH, AC vs MT) and the JSON output contract are ported unchanged. Classification is a single Haiku call per conversation (`classify_turns` for structured turns; `classify_transcript` when segmenting raw text). Invalid/missing labels collapse to `NQ`.

**Derived from the label sequence (deterministic, no extra LLM call):**
- `label_counts` — count per code.
- `ratios` — `critical_thinking = (CH+EX)/n`, `delegation = DG/n`, `filler = (AC+MT)/n`, `extension = EX/n`, `challenge = CH/n`.
- `longest_engaged_chain` — longest run of consecutive `CH`/`EX`/`FU` turns.
- `band` — `suggested_band` heuristic over thresholds in config: **One-Shot / Delegator / Directed / Iterative / Critical**.
- `filler_heavy` — `filler ≥ FILLER_HEAVY_RATIO`.

## 5. Critical-thinking score

A single **0–100** composite, **derived deterministically from the taxonomy labels** (no separate LLM judgement). Always reported with the `band` and a per-component breakdown so it is never a bare number.

```
ct_score = 100 * clamp(
      w_ratio    * critical_thinking_ratio          # (CH+EX)/n
    + w_chain    * normalize(longest_engaged_chain)  # e.g. min(chain/CHAIN_CAP, 1)
    + w_pushback * normalize(pushback_hits)          # min(hits/PUSHBACK_CAP, 1)
    - w_deleg    * delegation_ratio                  # DG/n  (penalty)
    - w_filler   * filler_ratio,                     # (AC+MT)/n (penalty)
    0, 1)
```

- Weights and caps live in `config.py`.
- **Default-weight requirement:** weights are tuned so the score's bins **reproduce the existing `band` boundaries** — the headline number and the band can never disagree. The weights are otherwise **unvalidated**; this is the first calibration target (§15).
- `components` in the result expose each term's contribution for auditability.

## 6. Scope, sessions, and timestamps

- One conversation per `analyse()` call → one `ConversationAnalysis`.
- **Auto-split on idle gaps:** when timestamps are present, split into sub-sessions on idle gaps `≥ IDLE_GAP_MIN` (config, default **30 min**). Each sub-session is scored independently and appears in `sessions[]`.
- When there are no timestamps or no gaps, `sessions[]` has length 1.
- **Headline score = the `aggregate`** (computed over *all* human turns across sessions). Per-session scores live in `sessions[]`. This disambiguates "the score" when splitting fires.
- Temporal metrics (`duration_min`, `hour_of_day_mode`, `weekday_mode`) are computed only when timestamps exist; otherwise omitted, with a `note`.

## 7. Analytics tier (free metrics)

Domain-neutral, computed per session and rolled up into `aggregate`:

- **Volume:** `turn_count`, `human_turn_count`, `assistant_turn_count`, `total_words`.
- **Length:** `mean_prompt_len`, `max_prompt_len`, `mean_response_len`.
- **Engagement:** `question_ratio` (prompts ending `?`), `pushback_count` (regex, ported from `marking_pipeline`).
- **Readability:** `flesch_reading_ease` (`textstat`).
- **Quality:** `mean_typo_rate` (`pyspellchecker`).
- **Sentiment trajectory:** `sentiment_start`, `sentiment_end`, `sentiment_delta` (VADER).
- **Repetition:** `prompt_self_similarity` — mean cosine similarity of consecutive prompt embeddings (`sentence-transformers` `all-MiniLM-L6-v2`). **`[embeddings]` extra**; `None` with a note when absent or when <2 prompts.
- **Temporal (timestamps only):** `duration_min`, `hour_of_day_mode`, `weekday_mode`.

## 8. Output data model

```
ConversationAnalysis (pydantic BaseModel)
  input: str
  format_detected: str            # role_content | anythingllm | markdown | text | pdf | ...
  parse_mode: str                 # structured | heuristic | llm-segment
  llm_used: bool
  notes: list[str]                # "llm_unavailable", "no timestamps", "embeddings_unavailable", ...
  session_count: int
  aggregate: SessionAnalysis      # rolled up over ALL human turns (the headline)
  sessions: list[SessionAnalysis] # 1+ (idle-gap split)

SessionAnalysis
  session_index: int
  started_at: datetime | None
  ended_at: datetime | None
  analytics: AnalyticsMetrics
  taxonomy: TaxonomySignals | None        # None when LLM unavailable
  critical_thinking: CriticalThinking | None
  turns: list[TurnLabel]

AnalyticsMetrics
  turn_count, human_turn_count, assistant_turn_count: int
  total_words: int
  mean_prompt_len, max_prompt_len, mean_response_len: float
  question_ratio: float
  pushback_count: int
  prompt_self_similarity: float | None
  flesch_reading_ease: float | None
  mean_typo_rate: float | None
  sentiment_start, sentiment_end, sentiment_delta: float | None
  duration_min: float | None
  hour_of_day_mode, weekday_mode: int | None

TaxonomySignals
  label_counts: dict[str, int]            # {NQ..MT}
  ratios: dict[str, float]                # critical_thinking, delegation, filler, extension, challenge
  longest_engaged_chain: int
  band: str                               # One-Shot | Delegator | Directed | Iterative | Critical
  filler_heavy: bool

CriticalThinking
  score: float                            # 0-100 composite
  band: str
  components: dict[str, float]            # ratio, chain, pushback, deleg_penalty, filler_penalty

TurnLabel
  index: int
  role: "human" | "assistant"
  text_preview: str                       # first ~200 chars
  label: str | None                       # NQ..MT (None for assistant turns / LLM unavailable)
  rationale: str | None                   # one-sentence classifier rationale
```

## 9. Dependency tiers and graceful degradation

Three pip extras, each degrading with a `note` rather than failing:

- **core** (light, offline): `pydantic`, `textstat`, `vaderSentiment`, `pyspellchecker`, stdlib. Runs analytics (minus self-similarity), parsing (structured + markers).
- **`[embeddings]`**: `sentence-transformers` (+ torch). Enables `prompt_self_similarity`. Absent → field `None`, note `embeddings_unavailable`.
- **`[llm]`**: `anthropic`. Enables the taxonomy/CT tier and the LLM-segment parser. Absent (or no API key) → `taxonomy`/`critical_thinking` are `None`, `llm_used=false`, note `llm_unavailable`; analytics still produced.

Heavy imports are lazy (inside functions) to keep core import fast and avoid the family's torch/NLTK-on-import pitfalls. All diagnostics go to stderr; only JSON to stdout.

## 10. Package layout and contract

```
lens/conversation-analyser/
├── pyproject.toml                 # hatchling; [project.scripts]; extras: embeddings, llm, dev
├── README.md
├── src/conversation_analyser/
│   ├── __init__.py                # exports ConversationAnalyser, ConversationAnalysis
│   ├── models.py                  # pydantic result models (§8)
│   ├── pipeline.py                # ConversationAnalyser.analyse() orchestration
│   ├── config.py                  # thresholds, models, weights, idle-gap (ported + extended)
│   ├── parsers/
│   │   ├── registry.py            # adapter registry + detection
│   │   ├── role_content.py
│   │   ├── anythingllm.py
│   │   ├── markers.py
│   │   └── llm_segment.py         # uses taxonomy.classify_transcript
│   ├── taxonomy.py                # ported: labels, prompts, classify_turns, ratios, band
│   ├── analytics.py               # free metrics (§7)
│   ├── scoring.py                 # composite CT score (§5)
│   ├── llm.py                     # call_json wrapper (ported)
│   ├── embeddings.py              # all-MiniLM-L6-v2 self-similarity (lazy)
│   ├── api.py                     # FastAPI app (module-level `app`): GET /health, POST /analyse
│   └── cli.py                     # conversation-analyser <path> [--json] [--llm]; `serve` subcommand
└── tests/
    ├── fixtures/                  # sample transcripts (role_content json, anythingllm, flat-text, pdf)
    ├── test_parsers.py
    ├── test_taxonomy.py           # deterministic given mocked LLM
    ├── test_scoring.py            # score↔band agreement
    ├── test_analytics.py
    └── test_cli_smoke.py
```

**API:** `from conversation_analyser import ConversationAnalyser, ConversationAnalysis`
`ConversationAnalyser().analyse(path | text | messages, *, llm=True) -> ConversationAnalysis`

**CLI (family idiom):** `conversation-analyser <path> [--json] [--llm] [--no-embeddings] [--idle-gap MIN] [--parse-mode ...]` for analysis (human summary by default, `--json` for machines), and a `serve` subcommand. The taxonomy/CT tier is opt-in via `--llm` (matches §1 "opt-in") to avoid surprise API cost; `auto-analyser` routes with `--json` only, so routed calls stay analytics-only and cheap.

**HTTP API:** module-level `app` in `api.py`; `GET /health`, `POST /analyse` (multipart file upload + optional `llm` form field, `response_model=ConversationAnalysis`) — the same `/analyse` contract the family exposes. `serve` runs `uvicorn.run("conversation_analyser.api:app", ...)`.

**Deps note:** `fastapi`, `uvicorn[standard]`, `python-multipart`, `rich` are **core** (not extras) — the whole family bundles them so `serve` and the HTTP API are always available.

**Port (for `serve`):** 8009 (next free in the family).

**Models:** classifier defaults to `claude-haiku-4-5` (config-overridable), matching `marking_pipeline`.

## 11. Relationship to `marking_pipeline` (forked copy)

The validated logic (`taxonomy.py` labels/prompts/tiebreakers, ratios, `longest_engaged_chain`, `suggested_band`, `ENGAGEMENT_BAND_THRESHOLDS`, pushback regex, `call_json`, embeddings self-similarity) is **copied** into `conversation_analyser`. The two then evolve **independently** — `marking_pipeline` (a live, per-semester grading tool) is left untouched. Prompt/threshold fixes made in one are not auto-propagated; this decoupling is deliberate.

## 12. Routing (`auto-analyser`) — deferred

Conversations share extensions (`.txt`, `.md`, `.json`, `.pdf`) with `document-analyser`, so extension routing cannot distinguish them. v1: **explicit invocation only** (CLI / API / import); `auto-analyser` defaults unchanged. Documented follow-up: a content-sniff detector (speaker markers / `role`-array / `prompt`+`response` keys) that routes matching files to `conversation-analyser`.

## 13. Configuration

All in `config.py` (ported and extended): `CLASSIFIER_MODEL`, `ENGAGEMENT_BAND_THRESHOLDS`, `FILLER_HEAVY_RATIO`, `HIGH_REPEAT_SIMILARITY`, `EMBED_MODEL`, plus new: `IDLE_GAP_MIN` (30), CT-score weights `{w_ratio, w_chain, w_pushback, w_deleg, w_filler}` and caps `{CHAIN_CAP, PUSHBACK_CAP}`.

## 14. Testing

pytest; heavy paths gated behind markers (`slow` for embeddings/model download, `integration` if any live LLM). Taxonomy/scoring tests mock `call_json` so they're deterministic. A CLI smoke test asserts non-zero-free exit and valid JSON on each fixture format. Score↔band agreement is an explicit test (§5 requirement).

## 15. Open questions / risks

1. **CT-score weights are unvalidated.** Default them to reproduce `band` boundaries (§5), then calibrate against a labelled sample. First post-build task.
2. **Multi-session headline ambiguity** resolved by §6 (aggregate is headline) — confirm this matches reporting expectations.
3. **LLM-segment fidelity** is lower than structured parsing; `parse_mode` surfaces this, but downstream consumers should weight `llm-segment` results accordingly.
4. **Role inference for `system`/tool turns** in `role_content` — treat non-user/assistant roles as ignored context (not human turns); confirm.

## 16. Build phases (proposed)

1. Package scaffold: `pyproject.toml` (3 extras), module skeleton, models, config, CLI stub, fixtures.
2. Parsers: registry + `role_content` + `anythingllm` + `markers`; structured/heuristic paths green.
3. Analytics tier (core, no embeddings) + tests.
4. Taxonomy port + `llm.py` + `llm_segment` parser; graceful degradation; mocked tests.
5. Scoring (composite + band-agreement); embeddings tier (`[embeddings]`).
6. CLI `--json`/`--serve`, README, smoke tests, fixture coverage across all formats.
7. (Later) `auto-analyser` content-sniff; ChatGPT-export adapter.
