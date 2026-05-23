# FastAPI Addition + Envelope Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drop the `{"success": true, "data": {...}}` envelope from audio-lens, data-lens, and poly-lens, and add a FastAPI HTTP server to audio-lens and data-lens with `GET /`, `GET /health`, and `POST /analyse` endpoints.

**Architecture:** Each lens gets an `exceptions.py` (typed error), the core `.analyse()` method returns data directly or raises, the CLI catches exceptions, and `app.py` is a self-contained FastAPI app. poly-lens router switches from checking `result["success"]` to checking subprocess returncode and HTTP status code. Tasks are ordered: audio-lens end-to-end → data-lens end-to-end → poly-lens update.

**Tech Stack:** FastAPI 0.111+, uvicorn[standard], python-multipart, slowapi, Pydantic v2, pytest + FastAPI TestClient

---

## File map

### audio-lens (`/Users/michael/Projects/lens/audio-lens/`)
| Action | Path |
|---|---|
| Create | `src/audio_lens/exceptions.py` |
| Modify | `src/audio_lens/audio_lens.py` |
| Modify | `src/audio_lens/cli.py` |
| Create | `src/audio_lens/schemas.py` |
| Create | `src/audio_lens/app.py` |
| Modify | `pyproject.toml` |
| Modify | `tests/test_audio_lens.py` |
| Create | `tests/test_app.py` |

### data-lens (`/Users/michael/Projects/lens/data-lens/`)
| Action | Path |
|---|---|
| Create | `src/data_lens/exceptions.py` |
| Modify | `src/data_lens/data_lens.py` |
| Modify | `src/data_lens/cli.py` |
| Create | `src/data_lens/schemas.py` |
| Create | `src/data_lens/app.py` |
| Modify | `pyproject.toml` |
| Modify | `tests/test_data_lens.py` |
| Create | `tests/test_app.py` |

### poly-lens (`/Users/michael/Projects/lens/poly-lens/`)
| Action | Path |
|---|---|
| Modify | `src/poly_lens/router.py` |
| Modify | `src/poly_lens/cli.py` |
| Modify | `src/poly_lens/config.py` |
| Modify | `poly-lens.example.yaml` |
| Modify | `tests/test_router.py` |

---

## Task 1: audio-lens — exceptions + drop envelope from core

**Files:**
- Create: `audio-lens/src/audio_lens/exceptions.py`
- Modify: `audio-lens/src/audio_lens/audio_lens.py`
- Modify: `audio-lens/tests/test_audio_lens.py`

- [ ] **Step 1: Write the failing tests**

In `audio-lens/tests/test_audio_lens.py`, replace the entire file:

```python
"""Integration tests for AudioLens."""

from pathlib import Path

import pytest

from audio_lens import AudioLens
from audio_lens.exceptions import AudioLensError


class TestAudioLensSilent:
    def test_unsupported_format_raises(self, tmp_path: Path):
        lens = AudioLens()
        p = tmp_path / "file.xyz"
        p.write_bytes(b"not audio")
        with pytest.raises(AudioLensError, match="Unsupported"):
            lens.analyse(p)

    def test_missing_file_raises(self, tmp_path: Path):
        lens = AudioLens()
        with pytest.raises(AudioLensError, match="not found"):
            lens.analyse(tmp_path / "missing.wav")

    def test_string_path_accepted(self, tmp_path: Path):
        lens = AudioLens()
        p = tmp_path / "file.xyz"
        p.write_bytes(b"not audio")
        with pytest.raises(AudioLensError, match="Unsupported"):
            lens.analyse(str(p))

    def test_success_shape(self, silent_wav: Path):
        """Full transcription of silent audio — requires faster-whisper installed."""
        lens = AudioLens()
        result = lens.analyse(silent_wav)
        assert "transcript" in result
        assert "language" in result
        assert "duration" in result
        assert "segments" in result
        assert "speech_metrics" in result
        assert "file_path" in result
        assert "file_size" in result
        assert result["file_size"] > 0
        assert "success" not in result
        assert "data" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py -v 2>&1 | tail -20
```

Expected: `ImportError: cannot import name 'AudioLensError'`

- [ ] **Step 3: Create exceptions module**

Create `src/audio_lens/exceptions.py`:

```python
class AudioLensError(Exception):
    """Raised when audio-lens cannot analyse a file."""
```

- [ ] **Step 4: Rewrite audio_lens.py to drop envelope**

Replace `src/audio_lens/audio_lens.py`:

```python
from pathlib import Path
from typing import Any

from .exceptions import AudioLensError
from .speech_analyzer import SpeechAnalyzer
from .transcriber import Transcriber


class AudioLens:
    """Transcribes audio files and returns speech metrics.

    Args:
        model_size: Whisper model size. Options: tiny, base, small, medium, large-v3.
    """

    def __init__(self, model_size: str = "base") -> None:
        self._transcriber = Transcriber(model_size=model_size)
        self._analyzer = SpeechAnalyzer()

    def analyse(self, file_path: Path | str) -> dict[str, Any]:
        """Analyse an audio file. Returns the analysis dict directly.

        Raises:
            AudioLensError: if the file is missing, format is unsupported,
                            or transcription fails.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise AudioLensError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in self._transcriber.SUPPORTED_EXTENSIONS:
            raise AudioLensError(
                f"Unsupported audio format: {file_path.suffix}. "
                f"Supported: {', '.join(sorted(self._transcriber.SUPPORTED_EXTENSIONS))}"
            )

        try:
            file_size = file_path.stat().st_size
            result = self._transcriber.transcribe(file_path)
            metrics = self._analyzer.analyse(result)

            return {
                "transcript": result.text,
                "language": result.language,
                "duration": result.duration,
                "segments": [
                    {"start": s.start, "end": s.end, "text": s.text}
                    for s in result.segments
                ],
                "speech_metrics": metrics,
                "file_path": str(file_path),
                "file_size": file_size,
            }
        except AudioLensError:
            raise
        except Exception as e:
            raise AudioLensError(repr(e)) from e
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py -v 2>&1 | tail -15
```

Expected: `9 passed` (or fewer if faster-whisper is slow — `test_success_shape` needs the model).

- [ ] **Step 6: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/exceptions.py src/audio_lens/audio_lens.py tests/test_audio_lens.py
git commit -m "feat(audio-lens): drop success/data envelope — raise AudioLensError on failure"
```

---

## Task 2: audio-lens — CLI update (drop envelope + serve subcommand)

**Files:**
- Modify: `audio-lens/src/audio_lens/cli.py`

- [ ] **Step 1: Write the failing test**

Add to `audio-lens/tests/test_audio_lens.py` a new class (append to the file):

```python
import subprocess
import sys


class TestCLI:
    def test_analyse_unsupported_exits_1(self, tmp_path: Path):
        p = tmp_path / "file.xyz"
        p.write_bytes(b"data")
        proc = subprocess.run(
            [sys.executable, "-m", "audio_lens.cli", "analyse", str(p), "--json"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1
        err = __import__("json").loads(proc.stderr)
        assert "error" in err
        assert "success" not in err

    def test_serve_help(self):
        proc = subprocess.run(
            [sys.executable, "-m", "audio_lens.cli", "serve", "--help"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0
        assert "--port" in proc.stdout
        assert "--host" in proc.stdout
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py::TestCLI -v 2>&1 | tail -10
```

Expected: `FAILED` — `test_analyse_unsupported_exits_1` fails because stderr is not JSON, and `test_serve_help` fails because `serve` subcommand doesn't exist yet.

- [ ] **Step 3: Rewrite cli.py**

Replace `src/audio_lens/cli.py`:

```python
"""CLI entry point for audio-lens.

Usage:
  audiolens analyse recording.mp3
  audiolens analyse recording.wav --model small
  audiolens analyse recording.m4a --json
  audiolens serve
  audiolens serve --port 8001 --host 0.0.0.0
"""

import json
import os
import sys
from pathlib import Path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="audio-lens",
        description="Audio transcription and speech analysis",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyse = sub.add_parser("analyse", help="Analyse an audio file")
    analyse.add_argument("file", type=Path, help="Path to audio file")
    analyse.add_argument(
        "--model",
        default=None,
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size (default: AUDIO_LENS_MODEL env var or 'base')",
    )
    analyse.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output raw JSON",
    )

    serve = sub.add_parser("serve", help="Start the FastAPI HTTP server")
    serve.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("AUDIO_LENS_PORT", "8001")),
        help="Port to listen on (default: AUDIO_LENS_PORT or 8001)",
    )
    serve.add_argument(
        "--host",
        default=os.getenv("AUDIO_LENS_HOST", "127.0.0.1"),
        help="Host to bind (default: AUDIO_LENS_HOST or 127.0.0.1)",
    )
    serve.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)",
    )

    args = parser.parse_args()

    if args.command == "analyse":
        _cmd_analyse(args)
    elif args.command == "serve":
        _cmd_serve(args)


def _cmd_analyse(args) -> None:
    from .audio_lens import AudioLens
    from .exceptions import AudioLensError

    model = args.model or os.getenv("AUDIO_LENS_MODEL", "base")
    lens = AudioLens(model_size=model)

    try:
        result = lens.analyse(args.file)
    except AudioLensError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Language:      {result['language']}")
    print(f"Duration:      {result['duration']:.1f}s")
    print(f"Words:         {result['speech_metrics']['word_count']}")
    print(f"Speaking rate: {result['speech_metrics']['speaking_rate_wpm']} wpm")
    print(f"Filler words:  {result['speech_metrics']['filler_word_count']}")
    print(f"Silence ratio: {result['speech_metrics']['silence_ratio']:.1%}")
    print()
    print("Transcript:")
    print(result["transcript"])


def _cmd_serve(args) -> None:
    import uvicorn
    uvicorn.run(
        "audio_lens.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py::TestCLI -v 2>&1 | tail -10
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/cli.py tests/test_audio_lens.py
git commit -m "feat(audio-lens): update CLI for no-envelope output, add serve subcommand"
```

---

## Task 3: audio-lens — FastAPI app (schemas + app + dependencies)

**Files:**
- Create: `audio-lens/src/audio_lens/schemas.py`
- Create: `audio-lens/src/audio_lens/app.py`
- Modify: `audio-lens/pyproject.toml`

- [ ] **Step 1: Add dependencies to pyproject.toml**

In `audio-lens/pyproject.toml`, replace the `dependencies` list:

```toml
dependencies = [
    "faster-whisper>=1.0.0",
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "python-multipart>=0.0.9",
    "slowapi>=0.1.9",
]
```

Install:

```bash
cd /Users/michael/Projects/lens/audio-lens
uv pip install -e ".[dev]" -q
```

Expected: no errors.

- [ ] **Step 2: Create schemas.py**

Create `src/audio_lens/schemas.py`:

```python
from pydantic import BaseModel


class SpeechMetrics(BaseModel):
    word_count: int
    speaking_rate_wpm: float
    filler_word_count: int
    filler_word_rate: float
    filler_words_found: list[str]
    silence_ratio: float
    actual_speaking_time: float


class AudioAnalysis(BaseModel):
    transcript: str
    language: str
    duration: float
    segments: list[dict]
    speech_metrics: SpeechMetrics
    file_path: str
    file_size: int


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
```

- [ ] **Step 3: Create app.py**

Create `src/audio_lens/app.py`:

```python
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .audio_lens import AudioLens
from .exceptions import AudioLensError
from .schemas import AudioAnalysis, HealthResponse

_VERSION = "0.1.0"
_START_TIME = time.time()
_VALID_MODELS = {"tiny", "base", "small", "medium", "large-v3"}

# Cache AudioLens instances by model size — model loading is expensive
_lens_cache: dict[str, AudioLens] = {}


def _get_lens(model_size: str) -> AudioLens:
    if model_size not in _lens_cache:
        _lens_cache[model_size] = AudioLens(model_size=model_size)
    return _lens_cache[model_size]


app = FastAPI(
    title="audio-lens",
    description="Audio transcription and speech analysis API",
    version=_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — desktop mode allows any localhost origin (for Electron)
if os.getenv("AUDIO_LENS_MODE") == "desktop":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=(
            r"^(https?://localhost(:\d+)?"
            r"|https?://127\.0\.0\.1(:\d+)?"
            r"|file://.*"
            r"|null)$"
        ),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    _origins = os.getenv(
        "AUDIO_LENS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

# Optional rate limiting — off by default, enable with AUDIO_LENS_RATE_LIMIT_ENABLED=true
if os.getenv("AUDIO_LENS_RATE_LIMIT_ENABLED", "false").lower() == "true":
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    _limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "audio-lens",
        "version": _VERSION,
        "status": "running",
        "endpoints": {"health": "/health", "analyse": "/analyse"},
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=_VERSION,
        uptime=round(time.time() - _START_TIME, 1),
    )


@app.post("/analyse", response_model=AudioAnalysis)
async def analyse(
    file: UploadFile = File(..., description="Audio file to analyse"),
    model: str | None = Form(default=None, description="Whisper model size (optional)"),
) -> AudioAnalysis:
    model_size = model or os.getenv("AUDIO_LENS_MODEL", "base")

    if model_size not in _VALID_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model_size}'. Must be one of: {', '.join(sorted(_VALID_MODELS))}",
        )

    suffix = Path(file.filename or "upload").suffix or ".wav"
    content = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        data = _get_lens(model_size).analyse(tmp_path)
    except AudioLensError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    return AudioAnalysis(**data)
```

- [ ] **Step 4: Verify the app imports cleanly**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -c "from audio_lens.app import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/schemas.py src/audio_lens/app.py pyproject.toml
git commit -m "feat(audio-lens): add FastAPI app with /health and /analyse endpoints"
```

---

## Task 4: audio-lens — API tests

**Files:**
- Create: `audio-lens/tests/test_app.py`
- Modify: `audio-lens/tests/conftest.py`

- [ ] **Step 1: Add `silent_wav_bytes` fixture to conftest.py**

Append to `audio-lens/tests/conftest.py`:

```python
@pytest.fixture
def silent_wav_bytes(silent_wav: Path) -> bytes:
    """Raw bytes of the silent WAV fixture."""
    return silent_wav.read_bytes()
```

- [ ] **Step 2: Write the tests**

Create `audio-lens/tests/test_app.py`:

```python
"""Tests for the audio-lens FastAPI app."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from audio_lens.app import app

client = TestClient(app)

_FAKE_ANALYSIS = {
    "transcript": "hello world",
    "language": "en",
    "duration": 5.0,
    "segments": [{"start": 0.0, "end": 5.0, "text": "hello world"}],
    "speech_metrics": {
        "word_count": 2,
        "speaking_rate_wpm": 24.0,
        "filler_word_count": 0,
        "filler_word_rate": 0.0,
        "filler_words_found": [],
        "silence_ratio": 0.0,
        "actual_speaking_time": 5.0,
    },
    "file_path": "/tmp/test.wav",
    "file_size": 1234,
}


class TestHealthEndpoint:
    def test_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_has_required_fields(self):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert isinstance(data["uptime"], float)


class TestRootEndpoint:
    def test_returns_200(self):
        assert client.get("/").status_code == 200

    def test_has_service_info(self):
        data = client.get("/").json()
        assert data["service"] == "audio-lens"
        assert "health" in data["endpoints"]
        assert "analyse" in data["endpoints"]


class TestAnalyseEndpoint:
    def test_no_file_returns_422(self):
        assert client.post("/analyse").status_code == 422

    def test_unsupported_format_returns_400(self):
        response = client.post(
            "/analyse",
            files={"file": ("test.xyz", b"not audio", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_invalid_model_returns_400(self):
        response = client.post(
            "/analyse",
            files={"file": ("test.wav", b"fake", "audio/wav")},
            data={"model": "giant"},
        )
        assert response.status_code == 400
        assert "Invalid model" in response.json()["detail"]

    def test_valid_file_returns_analysis_shape(self, silent_wav_bytes: bytes):
        with patch("audio_lens.app._get_lens") as mock_get_lens:
            mock_get_lens.return_value.analyse.return_value = _FAKE_ANALYSIS.copy()
            response = client.post(
                "/analyse",
                files={"file": ("test.wav", silent_wav_bytes, "audio/wav")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "hello world"
        assert data["language"] == "en"
        assert "speech_metrics" in data
        assert "success" not in data
        assert "data" not in data

    def test_response_has_no_envelope(self, silent_wav_bytes: bytes):
        with patch("audio_lens.app._get_lens") as mock_get_lens:
            mock_get_lens.return_value.analyse.return_value = _FAKE_ANALYSIS.copy()
            data = client.post(
                "/analyse",
                files={"file": ("test.wav", silent_wav_bytes, "audio/wav")},
            ).json()
        assert "success" not in data
        assert "error" not in data
```

- [ ] **Step 3: Add `httpx` to dev dependencies (TestClient needs it)**

In `audio-lens/pyproject.toml`, update `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.27.0",
]
```

```bash
cd /Users/michael/Projects/lens/audio-lens
uv pip install -e ".[dev]" -q
```

- [ ] **Step 4: Run all audio-lens tests**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/ -v 2>&1 | tail -20
```

Expected: all tests pass (9 existing + 2 CLI + 7 API = 18 tests, or similar count depending on slow test skips).

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add tests/test_app.py tests/conftest.py pyproject.toml
git commit -m "test(audio-lens): add FastAPI endpoint tests"
```

---

## Task 5: data-lens — exceptions + drop envelope from core

**Files:**
- Create: `data-lens/src/data_lens/exceptions.py`
- Modify: `data-lens/src/data_lens/data_lens.py`
- Modify: `data-lens/tests/test_data_lens.py`

- [ ] **Step 1: Write the failing tests**

Replace `data-lens/tests/test_data_lens.py`:

```python
"""Integration tests for DataLens."""

from pathlib import Path

import pytest

from data_lens import DataLens
from data_lens.exceptions import DataLensError


class TestDataLensCSV:
    def test_csv_returns_dict_directly(self, sample_csv: Path):
        result = DataLens().analyse(sample_csv)
        assert isinstance(result, dict)
        assert "success" not in result
        assert "data" not in result

    def test_csv_has_expected_keys(self, sample_csv: Path):
        result = DataLens().analyse(sample_csv)
        assert "format" in result
        assert "profile" in result
        assert "file_path" in result
        assert "file_size" in result

    def test_csv_profile_row_count(self, sample_csv: Path):
        result = DataLens().analyse(sample_csv)
        assert result["profile"]["rows"] == 3

    def test_csv_missing_values_detected(self, sample_csv: Path):
        result = DataLens().analyse(sample_csv)
        col = result["profile"]["column_profiles"]["score"]
        assert col["missing"] == 1


class TestDataLensJSON:
    def test_json_array_is_tabular(self, sample_json_array: Path):
        result = DataLens().analyse(sample_json_array)
        assert result["profile"]["rows"] == 2

    def test_json_object_has_warning(self, sample_json_object: Path):
        result = DataLens().analyse(sample_json_object)
        assert result["warning"] is not None
        assert "document-lens" in result["warning"]


class TestDataLensSQLite:
    def test_sqlite_returns_tables(self, sample_sqlite: Path):
        result = DataLens().analyse(sample_sqlite)
        assert "tables" in result
        assert "users" in result["tables"]

    def test_sqlite_table_profiled(self, sample_sqlite: Path):
        users = DataLens().analyse(sample_sqlite)["tables"]["users"]
        assert users["rows"] == 2


class TestDataLensEdgeCases:
    def test_unsupported_format_raises(self, tmp_path: Path):
        p = tmp_path / "file.xyz"
        p.write_bytes(b"data")
        with pytest.raises(DataLensError, match="Unsupported"):
            DataLens().analyse(p)

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(DataLensError, match="not found"):
            DataLens().analyse(tmp_path / "missing.csv")

    def test_string_path_accepted(self, sample_csv: Path):
        result = DataLens().analyse(str(sample_csv))
        assert "format" in result
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /Users/michael/Projects/lens/data-lens
python -m pytest tests/test_data_lens.py -v 2>&1 | tail -15
```

Expected: `ImportError: cannot import name 'DataLensError'` and several assertion failures.

- [ ] **Step 3: Create exceptions module**

Create `src/data_lens/exceptions.py`:

```python
class DataLensError(Exception):
    """Raised when data-lens cannot analyse a file."""
```

- [ ] **Step 4: Rewrite data_lens.py to drop envelope**

Replace `src/data_lens/data_lens.py`:

```python
from pathlib import Path
from typing import Any

from .exceptions import DataLensError
from .loaders import SUPPORTED_EXTENSIONS, load
from .profiler import profile_dataframe, profile_raw


class DataLens:
    """Profiles structured data files.

    Supports: CSV, TSV, XLSX, XLS, JSON, YAML, XML, SQLite, Parquet.
    """

    def analyse(self, file_path: Path | str) -> dict[str, Any]:
        """Profile a structured data file. Returns the profile dict directly.

        Raises:
            DataLensError: if the file is missing, format is unsupported,
                           or loading fails.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise DataLensError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise DataLensError(
                f"Unsupported format: {file_path.suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        try:
            file_size = file_path.stat().st_size
            loaded = load(file_path)

            data: dict[str, Any] = {
                "format": loaded.format,
                "file_path": str(file_path),
                "file_size": file_size,
            }

            if loaded.warning:
                data["warning"] = loaded.warning

            if loaded.tables:
                data["tables"] = {
                    name: profile_dataframe(df)
                    for name, df in loaded.tables.items()
                }
                data["profile"] = {
                    "table_count": len(loaded.tables),
                    "table_names": list(loaded.tables.keys()),
                }
            elif loaded.df is not None:
                data["profile"] = profile_dataframe(loaded.df)
            else:
                data["profile"] = profile_raw(loaded.raw)

            return data

        except DataLensError:
            raise
        except Exception as e:
            raise DataLensError(repr(e)) from e
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/data-lens
python -m pytest tests/test_data_lens.py -v 2>&1 | tail -15
```

Expected: `19 passed`

- [ ] **Step 6: Commit**

```bash
cd /Users/michael/Projects/lens/data-lens
git add src/data_lens/exceptions.py src/data_lens/data_lens.py tests/test_data_lens.py
git commit -m "feat(data-lens): drop success/data envelope — raise DataLensError on failure"
```

---

## Task 6: data-lens — CLI update (drop envelope + serve subcommand)

**Files:**
- Modify: `data-lens/src/data_lens/cli.py`
- Modify: `data-lens/tests/test_data_lens.py`

- [ ] **Step 1: Write failing CLI tests**

Append to `data-lens/tests/test_data_lens.py`:

```python
import subprocess
import sys


class TestCLI:
    def test_analyse_unsupported_exits_1(self, tmp_path: Path):
        p = tmp_path / "file.xyz"
        p.write_bytes(b"data")
        proc = subprocess.run(
            [sys.executable, "-m", "data_lens.cli", "analyse", str(p), "--json"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1
        err = __import__("json").loads(proc.stderr)
        assert "error" in err
        assert "success" not in err

    def test_serve_help(self):
        proc = subprocess.run(
            [sys.executable, "-m", "data_lens.cli", "serve", "--help"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0
        assert "--port" in proc.stdout
        assert "--host" in proc.stdout
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /Users/michael/Projects/lens/data-lens
python -m pytest tests/test_data_lens.py::TestCLI -v 2>&1 | tail -10
```

Expected: both tests fail.

- [ ] **Step 3: Rewrite cli.py**

Replace `src/data_lens/cli.py`:

```python
"""CLI entry point for data-lens.

Usage:
  datalens analyse data.csv
  datalens analyse data.xlsx --json
  datalens serve
  datalens serve --port 8002 --host 0.0.0.0
"""

import json
import os
import sys
from pathlib import Path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="data-lens",
        description="Structured data profiling",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyse = sub.add_parser("analyse", help="Profile a data file")
    analyse.add_argument("file", type=Path, help="Path to data file")
    analyse.add_argument("--json", action="store_true", dest="as_json",
                         help="Output raw JSON")

    serve = sub.add_parser("serve", help="Start the FastAPI HTTP server")
    serve.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("DATA_LENS_PORT", "8002")),
        help="Port to listen on (default: DATA_LENS_PORT or 8002)",
    )
    serve.add_argument(
        "--host",
        default=os.getenv("DATA_LENS_HOST", "127.0.0.1"),
        help="Host to bind (default: DATA_LENS_HOST or 127.0.0.1)",
    )
    serve.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)",
    )

    args = parser.parse_args()

    if args.command == "analyse":
        _cmd_analyse(args)
    elif args.command == "serve":
        _cmd_serve(args)


def _cmd_analyse(args) -> None:
    from .data_lens import DataLens
    from .exceptions import DataLensError

    try:
        result = DataLens().analyse(args.file)
    except DataLensError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}, indent=2, default=str), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
        return

    data = result
    print(f"Format:    {data['format']}")
    print(f"File size: {data['file_size']:,} bytes")

    if data.get("warning"):
        print(f"Warning:   {data['warning']}")

    if "tables" in data:
        print(f"Tables:    {', '.join(data['tables'].keys())}")
        for name, profile in data["tables"].items():
            print(f"\n  [{name}] {profile['rows']} rows x {profile['columns']} columns")
    elif "profile" in data:
        profile = data["profile"]
        if "rows" in profile:
            print(f"Shape:     {profile['rows']} rows x {profile['columns']} columns")
            print("\nColumn profiles:")
            for col, info in profile["column_profiles"].items():
                if info["type"] == "numeric":
                    print(f"  {col}: numeric  min={info['min']}  max={info['max']}  mean={info['mean']}  missing={info['missing']}")
                else:
                    print(f"  {col}: categorical  unique={info['unique']}  missing={info['missing']}")
        else:
            for k, v in profile.items():
                print(f"  {k}: {v}")


def _cmd_serve(args) -> None:
    import uvicorn
    uvicorn.run(
        "data_lens.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/data-lens
python -m pytest tests/test_data_lens.py::TestCLI -v 2>&1 | tail -10
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/data-lens
git add src/data_lens/cli.py tests/test_data_lens.py
git commit -m "feat(data-lens): update CLI for no-envelope output, add serve subcommand"
```

---

## Task 7: data-lens — FastAPI app (schemas + app + dependencies)

**Files:**
- Create: `data-lens/src/data_lens/schemas.py`
- Create: `data-lens/src/data_lens/app.py`
- Modify: `data-lens/pyproject.toml`

- [ ] **Step 1: Add dependencies**

In `data-lens/pyproject.toml`, replace the `dependencies` list:

```toml
dependencies = [
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
    "xlrd>=2.0.0",
    "PyYAML>=6.0.0",
    "pyarrow>=14.0.0",
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "python-multipart>=0.0.9",
    "slowapi>=0.1.9",
]
```

```bash
cd /Users/michael/Projects/lens/data-lens
uv pip install -e ".[dev]" -q
```

- [ ] **Step 2: Create schemas.py**

Create `src/data_lens/schemas.py`:

```python
from typing import Any

from pydantic import BaseModel


class DataAnalysis(BaseModel):
    format: str
    file_path: str
    file_size: int
    warning: str | None = None
    profile: dict[str, Any] | None = None
    tables: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
```

- [ ] **Step 3: Create app.py**

Create `src/data_lens/app.py`:

```python
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .data_lens import DataLens
from .exceptions import DataLensError
from .schemas import DataAnalysis, HealthResponse

_VERSION = "0.1.0"
_START_TIME = time.time()
_lens = DataLens()

app = FastAPI(
    title="data-lens",
    description="Structured data profiling API",
    version=_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — desktop mode allows any localhost origin (for Electron)
if os.getenv("DATA_LENS_MODE") == "desktop":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=(
            r"^(https?://localhost(:\d+)?"
            r"|https?://127\.0\.0\.1(:\d+)?"
            r"|file://.*"
            r"|null)$"
        ),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    _origins = os.getenv(
        "DATA_LENS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

# Optional rate limiting — off by default, enable with DATA_LENS_RATE_LIMIT_ENABLED=true
if os.getenv("DATA_LENS_RATE_LIMIT_ENABLED", "false").lower() == "true":
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    _limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "data-lens",
        "version": _VERSION,
        "status": "running",
        "endpoints": {"health": "/health", "analyse": "/analyse"},
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=_VERSION,
        uptime=round(time.time() - _START_TIME, 1),
    )


@app.post("/analyse", response_model=DataAnalysis)
async def analyse(
    file: UploadFile = File(..., description="Data file to analyse"),
) -> DataAnalysis:
    suffix = Path(file.filename or "upload").suffix or ".csv"
    content = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        data = _lens.analyse(tmp_path)
    except DataLensError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    return DataAnalysis(**data)
```

- [ ] **Step 4: Verify the app imports cleanly**

```bash
cd /Users/michael/Projects/lens/data-lens
python -c "from data_lens.app import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/data-lens
git add src/data_lens/schemas.py src/data_lens/app.py pyproject.toml
git commit -m "feat(data-lens): add FastAPI app with /health and /analyse endpoints"
```

---

## Task 8: data-lens — API tests

**Files:**
- Create: `data-lens/tests/test_app.py`
- Modify: `data-lens/pyproject.toml`

- [ ] **Step 1: Add httpx to dev dependencies**

In `data-lens/pyproject.toml`, update `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.27.0",
]
```

```bash
cd /Users/michael/Projects/lens/data-lens
uv pip install -e ".[dev]" -q
```

- [ ] **Step 2: Write the tests**

Create `data-lens/tests/test_app.py`:

```python
"""Tests for the data-lens FastAPI app."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from data_lens.app import app

client = TestClient(app)

_FAKE_CSV_ANALYSIS = {
    "format": "csv",
    "file_path": "/tmp/test.csv",
    "file_size": 512,
    "warning": None,
    "profile": {
        "rows": 3,
        "columns": 2,
        "column_profiles": {
            "name": {"type": "categorical", "unique": 3, "missing": 0},
            "value": {"type": "numeric", "min": 1.0, "max": 3.0,
                      "mean": 2.0, "median": 2.0, "std": 1.0,
                      "q25": 1.5, "q75": 2.5, "missing": 0},
        },
    },
    "tables": None,
}


class TestHealthEndpoint:
    def test_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_has_required_fields(self):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert isinstance(data["uptime"], float)


class TestRootEndpoint:
    def test_returns_200(self):
        assert client.get("/").status_code == 200

    def test_has_service_info(self):
        data = client.get("/").json()
        assert data["service"] == "data-lens"
        assert "health" in data["endpoints"]
        assert "analyse" in data["endpoints"]


class TestAnalyseEndpoint:
    def test_no_file_returns_422(self):
        assert client.post("/analyse").status_code == 422

    def test_unsupported_format_returns_400(self):
        response = client.post(
            "/analyse",
            files={"file": ("test.xyz", b"not data", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_valid_csv_returns_analysis_shape(self, sample_csv: Path):
        with patch("data_lens.app._lens") as mock_lens:
            mock_lens.analyse.return_value = _FAKE_CSV_ANALYSIS.copy()
            response = client.post(
                "/analyse",
                files={"file": ("data.csv", sample_csv.read_bytes(), "text/csv")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"
        assert "profile" in data
        assert "success" not in data
        assert "error" not in data

    def test_response_has_no_envelope(self, sample_csv: Path):
        with patch("data_lens.app._lens") as mock_lens:
            mock_lens.analyse.return_value = _FAKE_CSV_ANALYSIS.copy()
            data = client.post(
                "/analyse",
                files={"file": ("data.csv", sample_csv.read_bytes(), "text/csv")},
            ).json()
        assert "success" not in data
        assert "data" not in data
```

- [ ] **Step 3: Run all data-lens tests**

```bash
cd /Users/michael/Projects/lens/data-lens
python -m pytest tests/ -v 2>&1 | tail -20
```

Expected: all tests pass (19 existing + 2 CLI + 7 API = 28 tests).

- [ ] **Step 4: Commit**

```bash
cd /Users/michael/Projects/lens/data-lens
git add tests/test_app.py pyproject.toml
git commit -m "test(data-lens): add FastAPI endpoint tests"
```

---

## Task 9: poly-lens — router rewrite (RoutingError + returncode/HTTP status)

**Files:**
- Modify: `poly-lens/src/poly_lens/router.py`
- Modify: `poly-lens/src/poly_lens/cli.py`

- [ ] **Step 1: Write failing tests for the new router behaviour**

Replace `poly-lens/tests/test_router.py`:

```python
"""Tests for the Router."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from poly_lens.config import FamilyConfig, LensConfig
from poly_lens.router import Router, RoutingError


def _make_config(lens_name: str, lens_type: str, **kwargs) -> FamilyConfig:
    return FamilyConfig(lenses={
        lens_name: LensConfig(type=lens_type, **kwargs)
    })


class TestRouterCLI:
    def test_cli_lens_called_with_file(self, sample_csv: Path):
        cfg = _make_config("data-lens", "cli", command="datalens")
        router = Router(config=cfg)

        fake_data = {"format": "csv", "profile": {"rows": 2}}
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(fake_data),
                stderr="",
            )
            result = router.route(sample_csv, lens_name="data-lens")

        assert "success" not in result
        assert result["format"] == "csv"
        assert result["routed_to"] == "data-lens"
        call_args = mock_run.call_args[0][0]
        assert "datalens" in call_args
        assert "analyse" in call_args
        assert str(sample_csv) in call_args

    def test_cli_failure_raises_routing_error(self, sample_csv: Path):
        cfg = _make_config("data-lens", "cli", command="datalens")
        router = Router(config=cfg)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr=json.dumps({"error": "Unsupported format"}),
            )
            with pytest.raises(RoutingError, match="Unsupported format"):
                router.route(sample_csv, lens_name="data-lens")

    def test_unknown_lens_raises_routing_error(self, sample_csv: Path):
        cfg = FamilyConfig(lenses={})
        router = Router(config=cfg)
        with pytest.raises(RoutingError, match="not configured"):
            router.route(sample_csv, lens_name="no-such-lens")


class TestRouterDetect:
    def test_csv_auto_routes_to_data_lens(self, sample_csv: Path):
        cfg = _make_config("data-lens", "cli", command="datalens")
        router = Router(config=cfg)

        fake_data = {"format": "csv", "profile": {}}
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=json.dumps(fake_data), stderr=""
            )
            result = router.route(sample_csv)

        assert result["routed_to"] == "data-lens"
        assert "success" not in result

    def test_unknown_format_raises_routing_error(self, tmp_path: Path):
        cfg = FamilyConfig(lenses={})
        router = Router(config=cfg)
        p = tmp_path / "file.xyz"
        p.write_bytes(b"data")
        with pytest.raises(RoutingError, match="Unknown format"):
            router.route(p)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /Users/michael/Projects/lens/poly-lens
python -m pytest tests/test_router.py -v 2>&1 | tail -15
```

Expected: `ImportError: cannot import name 'RoutingError'` and multiple test failures.

- [ ] **Step 3: Rewrite router.py**

Replace `poly-lens/src/poly_lens/router.py`:

```python
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from .config import FamilyConfig, load_config
from .detector import detect


class RoutingError(Exception):
    """Raised when poly-lens cannot route or analyse a file."""


class Router:
    """Routes a file to the appropriate lens and returns the analysis."""

    def __init__(self, config: FamilyConfig | None = None) -> None:
        self._config = config or load_config()

    def route(
        self,
        file_path: "Path | str",
        lens_name: str | None = None,
    ) -> dict[str, Any]:
        """Analyse a file by routing to the appropriate lens.

        Returns the analysis dict with a 'routed_to' key injected.

        Raises:
            RoutingError: if the file is missing, format unknown, lens not
                          configured, or the lens returns an error.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise RoutingError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise RoutingError(f"Not a file: {file_path}")

        warning = None

        if lens_name is None:
            detection = detect(file_path)
            if detection.lens is None:
                raise RoutingError(
                    f"Unknown format: {file_path.suffix}. "
                    f"Use --lens to specify a lens directly."
                )
            lens_name = detection.lens
            warning = detection.warning

        lens_cfg = self._config.get(lens_name)
        if lens_cfg is None:
            raise RoutingError(
                f"Lens '{lens_name}' is not configured. "
                f"Available: {self._config.available()}"
            )

        if lens_cfg.type == "cli":
            if not lens_cfg.command:
                raise RoutingError(
                    f"Lens '{lens_name}' has type=cli but no command configured."
                )
            data = self._call_cli(lens_cfg.command, file_path)
        elif lens_cfg.type == "http":
            if not lens_cfg.url:
                raise RoutingError(
                    f"Lens '{lens_name}' has type=http but no url configured."
                )
            data = self._call_http(lens_cfg.url, file_path)
        else:
            raise RoutingError(f"Unknown lens type: {lens_cfg.type}")

        data["routed_to"] = lens_name
        if warning:
            data["warning"] = warning
        return data

    def _call_cli(self, command: str, file_path: Path) -> dict[str, Any]:
        try:
            proc = subprocess.run(
                [command, "analyse", str(file_path), "--json"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if proc.returncode != 0:
                try:
                    err = json.loads(proc.stderr)
                    msg = err.get("error", proc.stderr.strip())
                except (json.JSONDecodeError, AttributeError):
                    msg = proc.stderr.strip() or f"{command} exited with code {proc.returncode}"
                raise RoutingError(msg)
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError as e:
                raise RoutingError(
                    f"{command} returned invalid JSON: {e}. "
                    f"stdout={proc.stdout[:200]!r}"
                )
        except FileNotFoundError:
            raise RoutingError(f"CLI tool '{command}' not found. Is it installed?")
        except RoutingError:
            raise
        except Exception as e:
            raise RoutingError(repr(e)) from e

    def _call_http(self, url: str, file_path: Path) -> dict[str, Any]:
        """POST file to {url}/analyse. All HTTP lenses use this endpoint."""
        try:
            with open(file_path, "rb") as f:
                with httpx.Client(timeout=300) as client:
                    response = client.post(
                        f"{url}/analyse",
                        files={"file": (file_path.name, f)},
                    )
            if not response.is_success:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                raise RoutingError(f"HTTP {response.status_code}: {detail}")
            return response.json()
        except httpx.ConnectError:
            raise RoutingError(f"Cannot connect to {url}. Is the service running?")
        except RoutingError:
            raise
        except Exception as e:
            raise RoutingError(repr(e)) from e
```

- [ ] **Step 4: Update cli.py to use RoutingError**

Replace the `_cmd_analyse` function in `poly-lens/src/poly_lens/cli.py`:

```python
def _cmd_analyse(args) -> None:
    from .router import Router, RoutingError

    router = Router()
    if not args.file.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        result = router.route(args.file, lens_name=args.lens)
    except RoutingError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}, indent=2, default=str), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
        return

    if result.get("warning"):
        print(f"Note: {result['warning']}\n")

    print(f"Routed to:  {result.get('routed_to', 'unknown')}")
    print()
    print("Full result (use --json for machine-readable output):")
    _print_summary({k: v for k, v in result.items() if k not in ("routed_to", "warning")})
```

The full `cli.py` with the replacement in context — read the current file first, then replace only `_cmd_analyse`. The rest of the file (`main`, `_cmd_detect`, `_cmd_status`, `_print_summary`) stays unchanged.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/poly-lens
python -m pytest tests/test_router.py -v 2>&1 | tail -15
```

Expected: all router tests pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/michael/Projects/lens/poly-lens
git add src/poly_lens/router.py src/poly_lens/cli.py tests/test_router.py
git commit -m "feat(poly-lens): router uses exit codes and HTTP status — drop success/data envelope, add RoutingError"
```

---

## Task 10: poly-lens — config defaults + example yaml + full test suite

**Files:**
- Modify: `poly-lens/src/poly_lens/config.py`
- Modify: `poly-lens/poly-lens.example.yaml`

- [ ] **Step 1: Update config defaults**

In `poly-lens/src/poly_lens/config.py`, replace `_DEFAULTS`:

```python
_DEFAULTS: dict[str, dict] = {
    "document-lens": {"type": "http", "url": "http://localhost:8000"},
    "audio-lens":    {"type": "cli",  "command": "audiolens"},
    "data-lens":     {"type": "cli",  "command": "datalens"},
    "code-lens":     {"type": "http", "url": "http://localhost:8003"},
    "video-lens":    {"type": "cli",  "command": "videolens"},
}
```

- [ ] **Step 2: Update poly-lens.example.yaml**

Replace `poly-lens/poly-lens.example.yaml`:

```yaml
# poly-lens configuration
# Copy to ~/.config/poly-lens/config.yaml or ./poly-lens.yaml and adjust.
#
# Rate limiting: handled by reverse proxy (nginx, Caddy) for public deployments.
# Each lens can be run as CLI (default, no server needed) or HTTP (start server first).

lenses:
  document-lens:
    type: http
    url: http://localhost:8000

  # audio-lens: CLI by default (audiolens must be installed).
  # Switch to http if running: audiolens serve --port 8001
  audio-lens:
    type: cli
    command: audiolens
  # audio-lens:
  #   type: http
  #   url: http://localhost:8001

  # data-lens: CLI by default (datalens must be installed).
  # Switch to http if running: datalens serve --port 8002
  data-lens:
    type: cli
    command: datalens
  # data-lens:
  #   type: http
  #   url: http://localhost:8002

  code-lens:
    type: http
    url: http://localhost:8003

  video-lens:
    type: cli
    command: videolens
```

- [ ] **Step 3: Run the full poly-lens test suite**

```bash
cd /Users/michael/Projects/lens/poly-lens
python -m pytest tests/ -v 2>&1 | tail -20
```

Expected: all 14 tests pass (detector tests unchanged, router tests updated).

- [ ] **Step 4: Run all three packages end-to-end**

```bash
cd /Users/michael/Projects/lens/audio-lens && python -m pytest tests/ -q 2>&1 | tail -5
cd /Users/michael/Projects/lens/data-lens && python -m pytest tests/ -q 2>&1 | tail -5
cd /Users/michael/Projects/lens/poly-lens && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: all green across all three packages.

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/poly-lens
git add src/poly_lens/config.py poly-lens.example.yaml
git commit -m "feat(poly-lens): update config defaults (audiolens/datalens commands, code-lens port 8003)"
```
