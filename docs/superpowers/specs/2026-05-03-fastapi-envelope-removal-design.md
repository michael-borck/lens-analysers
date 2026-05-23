# FastAPI Addition + Envelope Removal Design

**Goal:** Add FastAPI HTTP interfaces to audio-lens and data-lens, and drop the `{"success": true, "data": {...}}` envelope from all lenses and poly-lens simultaneously.

**Architecture:** Each lens gains a `app.py` FastAPI module alongside its existing CLI. The CLI `--json` success output and the API `200 OK` body are byte-identical — the raw analysis dict with no wrapper. Success/failure is signalled by exit code (CLI) and HTTP status code (API). poly-lens router is updated to use these signals instead of the envelope.

**Tech Stack:** FastAPI, uvicorn, python-multipart, slowapi (optional rate limiting), Pydantic v2

---

## 1. Envelope removal (cross-cutting)

### Current shape (dropped everywhere)
```json
{"success": true, "data": {...}}
{"success": false, "error": "message"}
```

### New shape
**Success — stdout (CLI) / 200 OK body (API):**
```json
{
  "language": "en",
  "duration": 42.3,
  "transcript": "...",
  "speech_metrics": {...}
}
```

**Failure — stderr (CLI) / 4xx–5xx body (API):**
```json
{"error": "File not found: recording.xyz"}
```

### Changes per package

**audio-lens:** `AudioLens.analyse()` returns the data dict directly on success. On failure it raises `AudioLensError(message)`. The CLI catches it, prints `{"error": message}` to stderr, exits 1.

**data-lens:** Same pattern — `DataLens.analyse()` returns data dict or raises `DataLensError`.

**poly-lens router:** `Router.route()` checks `proc.returncode` (CLI lenses) and HTTP status code (HTTP lenses) instead of `result["success"]`. Returns the data dict with a `routed_to` key injected on success. Raises `RoutingError` on failure. The poly-lens CLI catches it, prints `{"error": message}` to stderr, exits 1.

---

## 2. FastAPI app structure

Both lenses get `src/<package>/app.py`. No sub-router files — each lens has one operation.

### Endpoints (identical structure for both lenses)

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service info: name, version, status, endpoint list |
| GET | `/health` | `{"status": "healthy", "version": "0.1.0", "uptime": 42.3}` |
| POST | `/analyse` | Multipart file upload → analysis JSON |

### POST /analyse — audio-lens
Form fields:
- `file`: audio file (required)
- `model`: `tiny` / `base` / `small` / `medium` / `large-v3` (optional)

Model resolution order: per-request field → `AUDIO_LENS_MODEL` env var → `"base"` hardcoded fallback.

Response (200):
```json
{
  "language": "en",
  "duration": 42.3,
  "transcript": "Full transcribed text...",
  "segments": [{"start": 0.0, "end": 2.1, "text": "Hello world"}],
  "speech_metrics": {
    "word_count": 500,
    "speaking_rate_wpm": 120,
    "filler_word_count": 5,
    "filler_word_rate": 1.0,
    "filler_words_found": ["um", "uh"],
    "silence_ratio": 0.15,
    "actual_speaking_time": 36.0
  }
}
```

### POST /analyse — data-lens
Form fields:
- `file`: data file (required)

Response (200): the same dict `DataLens.analyse()` returns (format, file_size, profile/tables, optional warning). No model selection needed — analysis is deterministic.

### Error responses (both lenses)
- `422 Unprocessable Entity` — missing or invalid form fields (FastAPI automatic)
- `400 Bad Request` — unsupported file format
- `500 Internal Server Error` — analysis failed

Body: `{"detail": "message"}` (FastAPI convention for HTTP errors).

### Pydantic response models

**audio-lens:**
```python
class SpeechMetrics(BaseModel):
    word_count: int
    speaking_rate_wpm: float
    filler_word_count: int
    filler_word_rate: float
    filler_words_found: list[str]
    silence_ratio: float
    actual_speaking_time: float

class AudioAnalysis(BaseModel):
    language: str
    duration: float
    transcript: str
    segments: list[dict]
    speech_metrics: SpeechMetrics

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
```

**data-lens:** `DataAnalysis` with `format`, `file_size`, `warning`, and either `profile` or `tables` depending on the source format. Both optional fields, validated at runtime.

---

## 3. CORS

**Desktop mode** (`AUDIO_LENS_MODE=desktop` / `DATA_LENS_MODE=desktop`):
```python
allow_origin_regex=r"^(https?://localhost(:\d+)?|https?://127\.0\.0\.1(:\d+)?|file://.*|null)$"
allow_credentials=False
allow_methods=["*"]
allow_headers=["*"]
```

**Web mode** (default):
```python
allow_origins=os.getenv("AUDIO_LENS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
allow_credentials=True
allow_methods=["GET", "POST", "OPTIONS"]
allow_headers=["*"]
```

---

## 4. Rate limiting

Off by default. Opt-in via env var.

```python
RATE_LIMIT_ENABLED = os.getenv("AUDIO_LENS_RATE_LIMIT_ENABLED", "false").lower() == "true"
RATE_LIMIT = os.getenv("AUDIO_LENS_RATE_LIMIT", "60/minute")
```

When enabled: slowapi limiter attached to the app, keyed by remote IP.

README documents: rate limiting is provided for convenience when exposing the lens directly. For production public deployments, use a reverse proxy (nginx `limit_req`, Caddy rate limit plugin, Cloudflare) — it handles rate limiting more robustly and without app restarts.

---

## 5. CLI serve subcommand

```
audiolens serve [--port 8001] [--host 127.0.0.1] [--reload]
datalens serve  [--port 8002] [--host 127.0.0.1] [--reload]
```

Port and host also readable from env vars (`AUDIO_LENS_PORT`, `AUDIO_LENS_HOST`) so Electron can configure without touching the command line. `--reload` passes uvicorn hot-reload for development.

Implementation: `uvicorn.run("audio_lens.app:app", host=host, port=port, reload=reload)`.

---

## 6. Dependencies added

Both `pyproject.toml` files gain:
```toml
[project]
dependencies = [
  ...existing...
  "fastapi>=0.111.0",
  "uvicorn[standard]>=0.29.0",
  "python-multipart>=0.0.9",
  "slowapi>=0.1.9",
]
```

---

## 7. poly-lens config defaults update

Port assignments updated to reflect the HTTP servers:

```python
_DEFAULTS = {
    "document-lens": {"type": "http", "url": "http://localhost:8000"},
    "audio-lens":    {"type": "cli",  "command": "audiolens"},   # CLI default; use http when server running
    "data-lens":     {"type": "cli",  "command": "datalens"},    # CLI default; use http when server running
    "code-lens":     {"type": "http", "url": "http://localhost:8003"},
    "video-lens":    {"type": "cli",  "command": "videolens"},
}
```

audio-lens and data-lens keep `cli` as the poly-lens default (works without starting a server). The `poly-lens.example.yaml` documents the HTTP alternatives at ports 8001 and 8002 for users who prefer to run the servers.

---

## 8. File map

### audio-lens
| Action | File |
|---|---|
| Modify | `src/audio_lens/audio_lens.py` — return dict / raise `AudioLensError` |
| Create | `src/audio_lens/exceptions.py` — `AudioLensError` |
| Create | `src/audio_lens/app.py` — FastAPI app |
| Create | `src/audio_lens/schemas.py` — Pydantic models |
| Modify | `src/audio_lens/cli.py` — drop envelope, add `serve` |
| Modify | `pyproject.toml` — add dependencies |
| Modify | `tests/` — update for new return format |
| Create | `tests/test_app.py` — API endpoint tests |

### data-lens
| Action | File |
|---|---|
| Modify | `src/data_lens/data_lens.py` — return dict / raise `DataLensError` |
| Create | `src/data_lens/exceptions.py` — `DataLensError` |
| Create | `src/data_lens/app.py` — FastAPI app |
| Create | `src/data_lens/schemas.py` — Pydantic models |
| Modify | `src/data_lens/cli.py` — drop envelope, add `serve` |
| Modify | `pyproject.toml` — add dependencies |
| Modify | `tests/` — update for new return format |
| Create | `tests/test_app.py` — API endpoint tests |

### poly-lens
| Action | File |
|---|---|
| Modify | `src/poly_lens/router.py` — returncode/HTTP status, no envelope |
| Modify | `src/poly_lens/cli.py` — drop envelope handling |
| Modify | `src/poly_lens/config.py` — update port defaults |
| Modify | `poly-lens.example.yaml` — add HTTP options for audio/data |
| Modify | `tests/` — update for new format |

---

## 9. Testing approach

**Unit tests** (existing, updated): mock `AudioLens.analyse()` / `DataLens.analyse()` to return data dict directly. Assert no `success`/`data` keys in output.

**API tests** (new, using `httpx.AsyncClient` + FastAPI `TestClient`):
- `GET /health` → 200, uptime is a float
- `GET /` → 200, contains endpoint map
- `POST /analyse` with valid file → 200, response matches Pydantic schema
- `POST /analyse` with unsupported format → 400
- `POST /analyse` with no file → 422

**poly-lens tests** (updated): mock subprocess returncode 0 / non-zero instead of mocking `result["success"]`.
