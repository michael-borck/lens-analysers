# audio-lens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone `audio-lens` Python package that transcribes audio files and returns speech metrics, then update `video-lens` to delegate its audio analysis to `audio-lens`.

**Architecture:** `audio-lens` is a thin Python package with three layers: a `Transcriber` (Faster-Whisper), a `SpeechAnalyzer` (metrics from transcription), and an `AudioLens` entry class that composes them. The code is adapted from `video-lens` but simplified — no video coupling, no scene awareness, no config system. `video-lens` is then updated to `pip install audio-lens` and call it instead of its own transcription code.

**Tech Stack:** Python 3.11+, `faster-whisper`, `uv`, pytest.

---

## File Map

| File | Action | Reason |
|------|--------|--------|
| `audio-lens/pyproject.toml` | Create | Package definition |
| `audio-lens/src/audio_lens/__init__.py` | Create | Public API |
| `audio-lens/src/audio_lens/transcriber.py` | Create | Faster-Whisper wrapper |
| `audio-lens/src/audio_lens/speech_analyzer.py` | Create | Metrics from transcription |
| `audio-lens/src/audio_lens/audio_lens.py` | Create | Main entry class |
| `audio-lens/src/audio_lens/cli.py` | Create | CLI: `audio-lens analyse <file>` |
| `audio-lens/tests/conftest.py` | Create | Shared fixtures |
| `audio-lens/tests/test_audio_lens.py` | Create | Integration tests |
| `audio-lens/tests/test_speech_analyzer.py` | Create | Unit tests for metrics |
| `video-lens/pyproject.toml` | Modify | Add audio-lens dependency |
| `video-lens/src/video_lens/analysis/transcriber.py` | Modify | Delegate to audio-lens |

---

## Task 1: Project scaffold

**Files:**
- Create: `audio-lens/pyproject.toml`
- Create: `audio-lens/src/audio_lens/__init__.py`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p /Users/michael/Projects/lens/audio-lens/src/audio_lens
mkdir -p /Users/michael/Projects/lens/audio-lens/tests
```

- [ ] **Step 2: Create pyproject.toml**

Create `/Users/michael/Projects/lens/audio-lens/pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "audio-lens"
version = "0.1.0"
description = "Audio transcription and speech analysis for the prism lens family"
requires-python = ">=3.11"
dependencies = [
    "faster-whisper>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
]

[project.scripts]
audio-lens = "audio_lens.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/audio_lens"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Create `__init__.py`**

Create `/Users/michael/Projects/lens/audio-lens/src/audio_lens/__init__.py`:

```python
from .audio_lens import AudioLens

__all__ = ["AudioLens"]
```

- [ ] **Step 4: Initialise git and install**

```bash
cd /Users/michael/Projects/lens/audio-lens
git init
uv venv
uv pip install -e ".[dev]"
```

Expected: `.venv` created, package installed in editable mode.

- [ ] **Step 5: Commit scaffold**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add .
git commit -m "chore: scaffold audio-lens package"
```

---

## Task 2: Transcriber

**Files:**
- Create: `audio-lens/src/audio_lens/transcriber.py`
- Create: `audio-lens/tests/conftest.py`
- Test: `audio-lens/tests/test_audio_lens.py` (partial — transcriber smoke test)

The `Transcriber` wraps Faster-Whisper. It accepts a `Path` to an audio file directly (unlike the video-lens version which took a `VideoInfo`/`AudioInfo` object). Model is loaded lazily on first use.

- [ ] **Step 1: Create `transcriber.py`**

Create `/Users/michael/Projects/lens/audio-lens/src/audio_lens/transcriber.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Segment:
    start: float
    end: float
    text: str
    avg_logprob: float


@dataclass
class TranscriptionResult:
    text: str
    segments: list[Segment]
    language: str
    duration: float


class Transcriber:
    """Wraps Faster-Whisper for audio transcription.

    Model is loaded lazily on first call to transcribe().
    """

    SUPPORTED_EXTENSIONS = {
        ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".opus",
    }

    def __init__(self, model_size: str = "base") -> None:
        self._model_size = model_size
        self._model = None

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute = "float16" if device == "cuda" else "int8"
            self._model = WhisperModel(self._model_size, device=device, compute_type=compute)
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe an audio file. Raises ValueError for unsupported formats."""
        if audio_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio format: {audio_path.suffix}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        model = self._load()
        raw_segments, info = model.transcribe(str(audio_path), word_timestamps=False)

        segments = []
        texts = []
        for seg in raw_segments:
            segments.append(Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
                avg_logprob=seg.avg_logprob,
            ))
            texts.append(seg.text.strip())

        return TranscriptionResult(
            text=" ".join(texts),
            segments=segments,
            language=info.language,
            duration=info.duration,
        )
```

- [ ] **Step 2: Create `conftest.py` with a minimal WAV fixture**

Create `/Users/michael/Projects/lens/audio-lens/tests/conftest.py`:

```python
"""Shared test fixtures for audio-lens."""

import struct
import wave
from pathlib import Path

import pytest


@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    """A minimal valid WAV file containing 1 second of silence."""
    path = tmp_path / "silent.wav"
    sample_rate = 16000
    num_samples = sample_rate  # 1 second

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)

    return path


@pytest.fixture
def sample_audio_dir() -> Path:
    """Points to video-lens test fixtures if present, else returns None."""
    candidate = Path(__file__).parents[3] / "video-lens" / "tests"
    return candidate if candidate.exists() else None
```

- [ ] **Step 3: Write transcriber smoke test**

Create `/Users/michael/Projects/lens/audio-lens/tests/test_audio_lens.py`:

```python
"""Integration tests for AudioLens."""

from pathlib import Path

import pytest

from audio_lens import AudioLens


class TestAudioLensSilent:
    """Tests using the silent WAV fixture — no Whisper model required for format checks."""

    def test_unsupported_format_returns_failure(self, tmp_path: Path):
        lens = AudioLens()
        p = tmp_path / "file.xyz"
        p.write_bytes(b"not audio")
        result = lens.analyse(p)
        assert result["success"] is False
        assert "Unsupported" in result["error"]

    def test_missing_file_returns_failure(self, tmp_path: Path):
        lens = AudioLens()
        result = lens.analyse(tmp_path / "missing.wav")
        assert result["success"] is False
        assert "error" in result

    def test_string_path_accepted(self, tmp_path: Path):
        lens = AudioLens()
        p = tmp_path / "file.xyz"
        p.write_bytes(b"not audio")
        result = lens.analyse(str(p))
        # Should fail on unsupported format, not on path type
        assert result["success"] is False
        assert "Unsupported" in result["error"]

    def test_success_shape(self, silent_wav: Path):
        """Full transcription of silent audio — requires faster-whisper installed."""
        lens = AudioLens()
        result = lens.analyse(silent_wav)
        assert result["success"] is True
        data = result["data"]
        assert "transcript" in data
        assert "language" in data
        assert "duration" in data
        assert "segments" in data
        assert "speech_metrics" in data
        assert "file_path" in data
        assert "file_size" in data
        assert data["file_size"] > 0
```

- [ ] **Step 4: Run tests — expect failures on missing AudioLens class**

```bash
cd /Users/michael/Projects/lens/audio-lens
uv run pytest tests/test_audio_lens.py -v 2>&1 | tail -15
```

Expected: `ImportError` — `AudioLens` not yet defined. Confirms tests are wired.

---

## Task 3: SpeechAnalyzer

**Files:**
- Create: `audio-lens/src/audio_lens/speech_analyzer.py`
- Create: `audio-lens/tests/test_speech_analyzer.py`

- [ ] **Step 1: Write the failing tests**

Create `/Users/michael/Projects/lens/audio-lens/tests/test_speech_analyzer.py`:

```python
"""Unit tests for SpeechAnalyzer — no audio files needed."""

from audio_lens.speech_analyzer import SpeechAnalyzer
from audio_lens.transcriber import Segment, TranscriptionResult


def _make_result(text: str, duration: float, segments=None) -> TranscriptionResult:
    if segments is None:
        segments = [Segment(start=0.0, end=duration * 0.8, text=text, avg_logprob=-0.2)]
    return TranscriptionResult(text=text, segments=segments, language="en", duration=duration)


class TestSpeechMetrics:
    def test_word_count(self):
        result = _make_result("hello world foo bar", duration=60.0)
        metrics = SpeechAnalyzer().analyse(result)
        assert metrics["word_count"] == 4

    def test_speaking_rate_wpm(self):
        # 60 words in 60 seconds = 60 wpm
        text = " ".join(["word"] * 60)
        result = _make_result(text, duration=60.0)
        metrics = SpeechAnalyzer().analyse(result)
        assert metrics["speaking_rate_wpm"] == 60.0

    def test_filler_word_detection(self):
        result = _make_result("um so basically I um think", duration=10.0)
        metrics = SpeechAnalyzer().analyse(result)
        assert metrics["filler_word_count"] >= 2

    def test_silence_ratio_between_0_and_1(self):
        result = _make_result("hello", duration=10.0)
        metrics = SpeechAnalyzer().analyse(result)
        assert 0.0 <= metrics["silence_ratio"] <= 1.0

    def test_empty_transcript(self):
        result = _make_result("", duration=10.0, segments=[])
        metrics = SpeechAnalyzer().analyse(result)
        assert metrics["word_count"] == 0
        assert metrics["speaking_rate_wpm"] == 0.0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/michael/Projects/lens/audio-lens
uv run pytest tests/test_speech_analyzer.py -v 2>&1 | tail -10
```

Expected: `ImportError` — `SpeechAnalyzer` not yet defined.

- [ ] **Step 3: Create `speech_analyzer.py`**

Create `/Users/michael/Projects/lens/audio-lens/src/audio_lens/speech_analyzer.py`:

```python
from typing import Any
from .transcriber import TranscriptionResult

_FILLER_WORDS = {
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "sort of", "kind of", "right", "okay", "so",
}


class SpeechAnalyzer:
    """Derives speech quality metrics from a TranscriptionResult."""

    def analyse(self, result: TranscriptionResult) -> dict[str, Any]:
        words = result.text.split() if result.text else []
        word_count = len(words)
        duration_minutes = result.duration / 60

        speaking_rate = round(word_count / duration_minutes, 1) if duration_minutes > 0 else 0.0

        text_lower = result.text.lower()
        filler_words_found = [fw for fw in _FILLER_WORDS if fw in text_lower]
        filler_count = sum(text_lower.count(fw) for fw in filler_words_found)
        filler_rate = round(filler_count / duration_minutes, 2) if duration_minutes > 0 else 0.0

        speaking_time = sum(s.end - s.start for s in result.segments)
        silence_ratio = round(
            1.0 - (speaking_time / result.duration), 3
        ) if result.duration > 0 else 0.0

        return {
            "word_count": word_count,
            "speaking_rate_wpm": speaking_rate,
            "filler_word_count": filler_count,
            "filler_word_rate": filler_rate,
            "filler_words_found": filler_words_found,
            "silence_ratio": silence_ratio,
            "actual_speaking_time": round(speaking_time, 1),
        }
```

- [ ] **Step 4: Run tests — all should pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
uv run pytest tests/test_speech_analyzer.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/speech_analyzer.py tests/test_speech_analyzer.py
git commit -m "feat: add SpeechAnalyzer with filler word and silence metrics"
```

---

## Task 4: AudioLens entry class

**Files:**
- Create: `audio-lens/src/audio_lens/audio_lens.py`

- [ ] **Step 1: Create `audio_lens.py`**

Create `/Users/michael/Projects/lens/audio-lens/src/audio_lens/audio_lens.py`:

```python
from pathlib import Path
from typing import Any

from .transcriber import Transcriber
from .speech_analyzer import SpeechAnalyzer


class AudioLens:
    """Transcribes audio files and returns speech metrics.

    Args:
        model_size: Whisper model size. Options: tiny, base, small, medium, large-v3.
                    Larger = more accurate, slower. Default 'base' suits most cases.
    """

    def __init__(self, model_size: str = "base") -> None:
        self._transcriber = Transcriber(model_size=model_size)
        self._analyzer = SpeechAnalyzer()

    def analyse(self, file_path: Path | str) -> dict[str, Any]:
        """Analyse an audio file.

        Returns:
            dict with keys:
              success (bool)
              data (dict): transcript, language, duration, segments,
                           speech_metrics, file_path, file_size
              error (str): present only on failure
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            if file_path.suffix.lower() not in self._transcriber.SUPPORTED_EXTENSIONS:
                return {
                    "success": False,
                    "error": (
                        f"Unsupported audio format: {file_path.suffix}. "
                        f"Supported: {', '.join(sorted(self._transcriber.SUPPORTED_EXTENSIONS))}"
                    ),
                    "data": {},
                }

            file_size = file_path.stat().st_size
            result = self._transcriber.transcribe(file_path)
            metrics = self._analyzer.analyse(result)

            return {
                "success": True,
                "data": {
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
                },
            }
        except Exception as e:
            return {"success": False, "error": repr(e), "data": {}}
```

- [ ] **Step 2: Run integration tests**

```bash
cd /Users/michael/Projects/lens/audio-lens
uv run pytest tests/test_audio_lens.py -v
```

Expected: All tests PASS (silent WAV test will run Whisper — takes ~10–30s on first run while model downloads).

- [ ] **Step 3: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/audio_lens.py tests/test_audio_lens.py tests/conftest.py
git commit -m "feat: add AudioLens entry class with full transcription pipeline"
```

---

## Task 5: CLI

**Files:**
- Create: `audio-lens/src/audio_lens/cli.py`

- [ ] **Step 1: Create `cli.py`**

Create `/Users/michael/Projects/lens/audio-lens/src/audio_lens/cli.py`:

```python
"""CLI entry point for audio-lens.

Usage:
  audio-lens analyse recording.mp3
  audio-lens analyse recording.wav --model small
  audio-lens analyse recording.m4a --json
"""

import json
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
        default="base",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size (default: base)",
    )
    analyse.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output raw JSON",
    )

    args = parser.parse_args()

    if args.command == "analyse":
        from .audio_lens import AudioLens

        lens = AudioLens(model_size=args.model)
        result = lens.analyse(args.file)

        if args.as_json:
            print(json.dumps(result, indent=2))
        else:
            if not result["success"]:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)

            data = result["data"]
            print(f"Language:      {data['language']}")
            print(f"Duration:      {data['duration']:.1f}s")
            print(f"Words:         {data['speech_metrics']['word_count']}")
            print(f"Speaking rate: {data['speech_metrics']['speaking_rate_wpm']} wpm")
            print(f"Filler words:  {data['speech_metrics']['filler_word_count']}")
            print(f"Silence ratio: {data['speech_metrics']['silence_ratio']:.1%}")
            print()
            print("Transcript:")
            print(data["transcript"])
```

- [ ] **Step 2: Test the CLI manually**

```bash
cd /Users/michael/Projects/lens/audio-lens
uv run audio-lens --help
uv run audio-lens analyse --help
```

Expected: help text printed, no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/cli.py
git commit -m "feat: add audio-lens CLI with analyse subcommand"
```

---

## Task 6: Update video-lens to call audio-lens

**Files:**
- Modify: `video-lens/pyproject.toml`
- Modify: `video-lens/src/video_lens/analysis/transcriber.py`

The goal is video-lens delegates to audio-lens's `Transcriber` rather than owning it. The video-lens `transcriber.py` currently takes `AudioInfo` (from `audio_extractor.py`). We keep that interface but internally use audio-lens.

- [ ] **Step 1: Add audio-lens to video-lens dependencies**

In `/Users/michael/Projects/lens/video-lens/pyproject.toml`, add to `dependencies`:

```toml
"audio-lens>=0.1.0",
```

For local development before audio-lens is published to PyPI, use a path dependency:

```toml
"audio-lens @ file:///Users/michael/Projects/lens/audio-lens",
```

- [ ] **Step 2: Update video-lens transcriber to delegate**

In `/Users/michael/Projects/lens/video-lens/src/video_lens/analysis/transcriber.py`, replace the `WhisperModel` loading and transcription logic with a call to `audio_lens.Transcriber`:

```python
from audio_lens.transcriber import Transcriber as _AudioTranscriber
from audio_lens.transcriber import TranscriptionResult, Segment

class Transcriber:
    """Delegates transcription to audio-lens."""

    def __init__(self, config=None):
        self._config = config or get_config()
        model_size = getattr(self._config, "whisper_model_size", "base")
        self._inner = _AudioTranscriber(model_size=model_size)

    def transcribe_audio(self, audio_info) -> TranscriptionResult:
        return self._inner.transcribe(audio_info.file_path)
```

Verify all existing video-lens call sites (`pipeline_coordinator.py`, `speech_analyzer.py`) still work — they receive `TranscriptionResult` which is now imported from audio-lens.

- [ ] **Step 3: Run video-lens tests**

```bash
cd /Users/michael/Projects/lens/video-lens
uv run pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: same pass/fail count as before the change.

- [ ] **Step 4: Commit both repos**

```bash
cd /Users/michael/Projects/lens/audio-lens
git tag v0.1.0

cd /Users/michael/Projects/lens/video-lens
git add pyproject.toml src/video_lens/analysis/transcriber.py
git commit -m "refactor: delegate transcription to audio-lens"
```

---

## Completion Checklist

- [ ] `audio-lens` package installable via `pip install audio-lens`
- [ ] `audio-lens analyse recording.wav` works from CLI
- [ ] All unit tests pass (speech_analyzer)
- [ ] Integration test passes with silent WAV fixture
- [ ] `video-lens` delegates to `audio-lens` transcriber
- [ ] `video-lens` tests unaffected
