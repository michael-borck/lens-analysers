# Desktop apps for non-technical users — design (Phase 5)

Two **install-and-run** Electron desktop apps, for educators with no CLI/Python:

1. **assessment-lens desktop** — mark a real cohort: load submissions + a rubric,
   get observation sheets and per-student reports. *Built first* (establishes the
   shared scaffold and the Python-sidecar-with-first-run-install pattern).
2. **assessment-bench desktop** — research which assessment method to trust.
   *Built second* (its backend already has `serve` + `api.py` + Ollama, so it's
   mostly UI).

> Status: tracking lives in [ROADMAP.md](ROADMAP.md) Phase 5. Reconnaissance of
> the existing apps is in the `desktop-app-patterns` memory.

## Principles

- **Non-technical**: download an installer, run it. No terminal, no Python, no
  `pip`. First run sets everything up with visible progress.
- **Privacy-first / local**: student submissions never leave the machine. All
  analysis runs in a local sidecar; the LLM is local (Ollama). No telemetry.
- **Fully offline after setup**: models bundled or downloaded-once with checksums;
  thereafter no network needed to assess.
- **Cross-platform**: macOS (x64 + arm64), Windows, Linux — the family's existing
  electron-builder pipeline already does all three.
- **Never scores**: the desktop apps inherit the family invariant. assessment-lens
  surfaces observations a human marks; the bench *measures* methods, it doesn't
  grade students.

## Architecture (both apps)

```
┌──────────────────────────────────────────────────────────────┐
│  Electron app  (the only thing the user installs/sees)         │
│                                                                │
│  renderer (React)  ── IPC ──►  main process                    │
│    the workflow UI               ├─ spawns + supervises ▼       │
│                                  │     Python sidecar (bundled) │
│                                  │       FastAPI `serve`        │
│                                  │       assessment-lens/-bench │
│                                  │       + analyser stack       │
│                                  │   ◄─ localhost HTTP + token ─┤
│                                  ├─ detects/guides Ollama ──────┼─► Ollama
│                                  └─ first-run installer ────────┤   (local LLM)
│                                       (heavy pkgs + models)     │
└──────────────────────────────────────────────────────────────┘
        everything on localhost; nothing leaves the machine
```

The **HTTP contract is the seam**: the renderer never touches Python. The sidecar
exposes the family contract (`/health`, `/manifest`, plus each tool's run
endpoints). assessment-lens's API landed in 0.4.0 (`POST /assessments` → poll →
result); assessment-bench already has `POST /experiments`.

## The `lens-desktop` template (build during app #1)

The existing apps (document-lens, insight-lens, talk-buddy, study-buddy,
career-compass) are **copy-paste siblings, not a shared scaffold** — which has
already caused drift (a provider env-var bug). So extract a **GitHub _template_
repo** `lens-desktop`. Apps are created *from* it (so they stay self-contained and
can diverge) but start identical, so the patterns and fixes live in one place.

The template provides:

| Piece | Harvest from | Notes |
|---|---|---|
| Electron main + window + IPC + preload bridge | career-compass | contextBridge surface (store, secureStorage, fetch, sidecar) |
| **Python sidecar manager** | document-lens `BackendManager` + talk-buddy `index.js` | spawn, `findAvailablePort`, per-session bearer token, `/health` poll, phase state machine, auto-restart, graceful→SIGTERM→SIGKILL |
| **First-run installer** | talk-buddy `setup.sh` + `EmbeddedInstallModal` | venv + pip heavy pkgs + checksummed model download, streamed to a progress modal; **+ a new Windows PowerShell equivalent** |
| **Ollama setup** | insight-lens / career-compass `OllamaSetupCard` + `ollama-setup.ts` | probe `:11434/api/tags` → guide install → curated model → streaming NDJSON pull → connect |
| Provider abstraction + secure key storage | career-compass `src/shared/providers.js` + `secure-storage.js` | safeStorage (Keychain/DPAPI/libsecret) + plaintext fallback |
| Security baseline | document-lens | contextIsolation, fs-guard, keyed-query IPC (no raw SQL/paths from renderer) |
| Packaging + notarize + auto-update | all five (identical) | electron-builder (mac dmg+zip, win nsis, linux AppImage+deb), custom `notarize.js` (`NOTARIZE_APPLE_*`), electron-updater, GitHub publish |

## Python sidecar strategy (the crux)

Bundling the full ML stack (torch + whisper + CLIP) with PyInstaller `--onefile`
is impractical (multi-GB). So a **hybrid**, exactly as decided:

- **Ship lean**: the installer contains the Electron app + a small launcher, not
  torch.
- **First run installs heavy packages** into an app-local dir (e.g.
  `app.getPath('userData')/runtime`): create a venv (or relocatable Python),
  `pip install` the analyser stack with **CPU-only torch wheels pinned**, with a
  streamed progress modal (talk-buddy already does this in dev — promote it to
  production).
- **Models bundled / downloaded-once with SHA-256** (talk-buddy's pattern): the
  sentence-transformer, Whisper, and CLIP models live in the app or are fetched
  once and verified, then it's fully offline. ffmpeg is another first-run
  checksummed binary per OS.
- **Sidecar = the tool's own `serve`**: the manager spawns
  `assessment-lens serve` / `assessment-bench serve` from the installed runtime.

**The known gap**: talk-buddy's installer is bash (`setup.sh`), macOS/Linux only.
Windows needs a **PowerShell installer** doing the same steps (venv, pip, download,
checksum, progress) — this is net-new work in the template.

## Per-app UX

### assessment-lens desktop (app #1)
A simple linear marking workflow (not document-lens's IDE-like layout, which is too
complex for non-tech markers):

1. **Pick a cohort folder** (one subfolder per submission) + **a rubric**
   (or draft one from a spec — `draft-rubric`, needs the local LLM).
2. **Run** — progress per submission (the API streams it), engine warms up.
3. **Cohort sheet** — sortable triage table (all `absent` first, distinctiveness
   flags), and **per-student observation reports**. No marks — a column for the
   human's mark, exported as they go.
4. **Settings** — Ollama setup card; engine status chip; where reports are saved.

### assessment-bench desktop (app #2)
A research console: define arms (LLM / signals / hybrid), point at a cohort +
human marks CSV, run, watch progress, see reliability + agreement charts. Backend
ready; this is mostly the UI + reusing the template.

## Prerequisites (the `(a)` items)

- [x] **assessment-lens HTTP API** — done, v0.4.0 (`serve`, `api.py`, `manifest`).
- [ ] **assessment-lens local LLM provider** — `llm.py` is Anthropic-only; add an
  Ollama / OpenAI-compatible provider (career-compass's registry is the template)
  so narration + draft-rubric run locally. Required for the privacy goal.

## Sequencing & milestones

1. **(a)** finish prerequisites: local LLM provider in assessment-lens.
2. **(c)** extract `lens-desktop` template (this doc → working scaffold).
3. **App #1**: assessment-lens desktop on the template; prove the first-run
   installer on all three OSes (the riskiest milestone).
4. **App #2**: assessment-bench desktop from the template.

Release each via the family's existing tagged-build CI (mac/win/linux) →
electron-updater.

## Risks (watch these)

- **Per-OS first-run install** of the ML stack — Windows PowerShell installer is
  net-new; torch wheel selection (CPU-only), arm64 Mac, resumable multi-GB
  downloads all need real per-OS testing. *Highest risk.*
- **Footprint** — "all submission types day one" (audio/video = whisper+ffmpeg) is
  the heaviest path; first-run could pull gigabytes. Progress UX + resumability
  matter.
- **Code-signing/notarization** — solved per-app before, but it's setup each time.
- **Sidecar startup time** on first cohort (model warmup) — show a clear "engine
  starting" state (document-lens has the chip).

## Open questions

- Relocatable Python vs venv-on-first-run vs a partial PyInstaller core + pip the
  rest? (Lean toward venv-on-first-run; revisit if startup/footprint hurts.)
- Bundle models in the installer (fatter download, instant offline) vs first-run
  download with checksums (lean installer, one network setup)? Decided: heavy
  *packages* first-run; *models* lean toward bundled where size allows, else
  checksummed download.
- Does the bench app reuse the lens sidecar (shared runtime) or ship its own?
  (Likely its own, for self-containment.)
