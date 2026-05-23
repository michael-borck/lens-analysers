# audio-lens v2: Rich Metrics + Speaker Diarization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend audio-lens with multi-word filler detection, quality scoring, pace benchmarking, natural-language insights, model download warnings, and optional speaker diarization with talk-time distribution via pyannote.audio.

**Architecture:** Five self-contained tasks, each committable independently. Tasks 1–2 add metrics and error types with no new runtime deps. Task 3 adds an optional `diarizer.py` module gated behind `audio-lens[diarization]`. Tasks 4–5 wire everything together — `AudioLens.analyse()` gains a `diarize` flag, the Pydantic schemas grow, and the FastAPI app + CLI get the corresponding form field and flag. Diarization is off by default; the result shape is backward-compatible (new keys default to `None`/`False`).

**Tech Stack:** Python 3.11+, faster-whisper, pyannote.audio 3.1+ (optional), FastAPI, Pydantic v2, pytest

---

## File map

### Modified
| File | What changes |
|---|---|
| `src/audio_lens/speech_analyzer.py` | Full rewrite — multi-word fillers, quality score, pace category, insights |
| `src/audio_lens/exceptions.py` | Add `ModelNotAvailableError` |
| `src/audio_lens/transcriber.py` | Download progress warning in `_load()` |
| `src/audio_lens/audio_lens.py` | Wire diarization, new output shape |
| `src/audio_lens/__init__.py` | Export `ModelNotAvailableError` |
| `src/audio_lens/schemas.py` | New Pydantic models for all new fields |
| `src/audio_lens/app.py` | `diarize` Form param, 503 for `ModelNotAvailableError` |
| `src/audio_lens/cli.py` | `--diarize` flag on `analyse` subcommand |
| `pyproject.toml` | Add `[diarization]` optional dep group |
| `tests/conftest.py` | Add `two_speaker_wav` fixture |
| `tests/test_speech_analyzer.py` | Tests for all new metrics |
| `tests/test_audio_lens.py` | Updated shape assertions |
| `tests/test_app.py` | Updated `_FAKE_ANALYSIS`, new schema fields |

### Created
| File | Purpose |
|---|---|
| `src/audio_lens/diarizer.py` | `Diarizer` class + `DiarizationTurn` dataclass |
| `tests/test_diarizer.py` | Unit tests with mocked pyannote pipeline |

---

## Task 1: Speech analyzer improvements

**Files:**
- Modify: `audio-lens/src/audio_lens/speech_analyzer.py`
- Modify: `audio-lens/tests/test_speech_analyzer.py`

### What changes and why

Current `speech_analyzer.py` has three problems:
1. `_FILLER_WORDS` uses `\b` regex for multi-word phrases like "you know" — `\b` matches word boundaries, so "you know" becomes two separate boundary checks and never matches as a phrase.
2. `filler_word_rate` is fillers-per-minute (weird); it should be a fraction of total words (0.0–1.0), consistent with `silence_ratio`.
3. No quality score, pace category, or insights.

- [ ] **Step 1: Write the failing tests**

Replace `tests/test_speech_analyzer.py` entirely:

```python
"""Unit tests for SpeechAnalyzer — no audio files needed."""

import pytest
from audio_lens.speech_analyzer import SpeechAnalyzer, _detect_fillers, _pace_category, _quality_score
from audio_lens.transcriber import Segment, TranscriptionResult


def _make_result(text: str, duration: float, segments=None) -> TranscriptionResult:
    if segments is None:
        segments = [Segment(start=0.0, end=duration * 0.8, text=text, avg_logprob=-0.2)]
    return TranscriptionResult(text=text, segments=segments, language="en", duration=duration)


class TestFillerDetection:
    def test_single_word_filler(self):
        count, found = _detect_fillers("um well I um think so")
        assert count >= 3
        assert "um" in found

    def test_multi_word_filler(self):
        count, found = _detect_fillers("I you know think you know")
        assert count >= 2
        assert "you know" in found

    def test_i_mean_detected(self):
        count, found = _detect_fillers("I mean that is i mean fine")
        assert "i mean" in found

    def test_empty_text(self):
        count, found = _detect_fillers("")
        assert count == 0
        assert found == []

    def test_no_fillers(self):
        count, found = _detect_fillers("The quick brown fox jumps")
        assert count == 0


class TestPaceCategory:
    def test_slow(self):
        assert _pace_category(70.0) == "slow"

    def test_natural(self):
        assert _pace_category(150.0) == "natural"

    def test_fast(self):
        assert _pace_category(220.0) == "fast"

    def test_boundary_90_is_natural(self):
        assert _pace_category(90.0) == "natural"

    def test_boundary_200_is_natural(self):
        assert _pace_category(200.0) == "natural"


class TestQualityScore:
    def test_score_in_range(self):
        score, factors, ratings = _quality_score(
            filler_rate=0.02, avg_words_per_segment=15.0, wpm=150.0, speaker_percentages=[]
        )
        assert 0 <= score <= 100

    def test_excellent_pace_scores_25(self):
        _, factors, _ = _quality_score(
            filler_rate=0.0, avg_words_per_segment=15.0, wpm=150.0, speaker_percentages=[]
        )
        assert factors["pace"] == 25

    def test_single_speaker_balance_neutral(self):
        _, factors, _ = _quality_score(
            filler_rate=0.0, avg_words_per_segment=15.0, wpm=150.0, speaker_percentages=[]
        )
        assert factors["balance"] == 18

    def test_balanced_two_speakers(self):
        _, factors, _ = _quality_score(
            filler_rate=0.0, avg_words_per_segment=15.0, wpm=150.0,
            speaker_percentages=[50.0, 50.0],
        )
        assert factors["balance"] == 25

    def test_dominant_speaker_penalised(self):
        _, factors, _ = _quality_score(
            filler_rate=0.0, avg_words_per_segment=15.0, wpm=150.0,
            speaker_percentages=[90.0, 10.0],
        )
        assert factors["balance"] < 18

    def test_ratings_are_valid_strings(self):
        _, _, ratings = _quality_score(
            filler_rate=0.05, avg_words_per_segment=10.0, wpm=130.0, speaker_percentages=[]
        )
        valid = {"excellent", "good", "fair", "low"}
        for v in ratings.values():
            assert v in valid


class TestSpeechAnalyzer:
    def test_word_count(self):
        result = _make_result("hello world foo bar", duration=60.0)
        m = SpeechAnalyzer().analyse(result)
        assert m["word_count"] == 4

    def test_speaking_rate_wpm(self):
        text = " ".join(["word"] * 60)
        result = _make_result(text, duration=60.0)
        m = SpeechAnalyzer().analyse(result)
        assert m["speaking_rate_wpm"] == 60.0

    def test_filler_word_rate_is_fraction(self):
        # "um" appears 1 time in 10 words → rate = 0.1
        result = _make_result("um " + " ".join(["word"] * 9), duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert 0.0 <= m["filler_word_rate"] <= 1.0

    def test_silence_ratio_between_0_and_1(self):
        result = _make_result("hello", duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert 0.0 <= m["silence_ratio"] <= 1.0

    def test_pace_category_present(self):
        result = _make_result("hello world", duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert m["pace_category"] in {"slow", "natural", "fast"}

    def test_quality_score_present(self):
        result = _make_result("hello world", duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert "quality_score" in m
        assert 0 <= m["quality_score"] <= 100

    def test_quality_factors_keys(self):
        result = _make_result("hello world", duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert set(m["quality_factors"].keys()) == {"clarity", "depth", "balance", "pace"}

    def test_insights_structure(self):
        result = _make_result("hello world", duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert "insights" in m
        assert "strengths" in m["insights"]
        assert "observations" in m["insights"]
        assert isinstance(m["insights"]["strengths"], list)
        assert isinstance(m["insights"]["observations"], list)

    def test_empty_transcript(self):
        result = _make_result("", duration=10.0, segments=[])
        m = SpeechAnalyzer().analyse(result)
        assert m["word_count"] == 0
        assert m["speaking_rate_wpm"] == 0.0

    def test_multi_word_fillers_detected(self):
        result = _make_result("you know I think you know maybe", duration=10.0)
        m = SpeechAnalyzer().analyse(result)
        assert "you know" in m["filler_words_found"]
        assert m["filler_word_count"] >= 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_speech_analyzer.py -v 2>&1 | tail -20
```

Expected: import errors on `_detect_fillers`, `_pace_category`, `_quality_score`.

- [ ] **Step 3: Rewrite speech_analyzer.py**

Replace `src/audio_lens/speech_analyzer.py` entirely:

```python
import re
from typing import Any

from .transcriber import TranscriptionResult

_SINGLE_WORD_FILLERS = {
    "um", "uh", "er", "ah", "hmm", "mm",
    "like", "so", "well", "actually", "basically",
    "literally", "honestly", "obviously", "right",
    "okay", "yeah", "anyway",
}

_MULTI_WORD_FILLERS = [
    "you know", "i mean", "kind of", "sort of", "you see",
    "i guess", "or something", "or whatever",
]


def _detect_fillers(text: str) -> tuple[int, list[str]]:
    """Return (total_count, sorted list of distinct filler expressions found)."""
    if not text:
        return 0, []

    lower = text.lower()
    tokens = lower.split()
    counts: dict[str, int] = {}

    for tok in tokens:
        clean = re.sub(r"^[^\w']+|[^\w']+$", "", tok)
        if clean in _SINGLE_WORD_FILLERS:
            counts[clean] = counts.get(clean, 0) + 1

    joined = " " + " ".join(tokens) + " "
    for phrase in _MULTI_WORD_FILLERS:
        needle = " " + phrase + " "
        idx, n = 0, 0
        while (idx := joined.find(needle, idx)) != -1:
            n += 1
            idx += len(needle) - 1
        if n:
            counts[phrase] = counts.get(phrase, 0) + n

    total = sum(counts.values())
    return total, sorted(counts.keys())


def _pace_category(wpm: float) -> str:
    if wpm < 90:
        return "slow"
    if wpm > 200:
        return "fast"
    return "natural"


def _quality_score(
    filler_rate: float,
    avg_words_per_segment: float,
    wpm: float | None,
    speaker_percentages: list[float],
) -> tuple[int, dict[str, int], dict[str, str]]:
    # Clarity — inverse of filler rate (fraction 0-1)
    if filler_rate <= 0.02:
        clarity = 25
    elif filler_rate <= 0.05:
        clarity = 21
    elif filler_rate <= 0.08:
        clarity = 16
    elif filler_rate <= 0.12:
        clarity = 11
    else:
        clarity = 6

    # Depth — average words per Whisper segment
    w = avg_words_per_segment
    if 12 <= w <= 25:
        depth = 25
    elif 8 <= w <= 30:
        depth = 20
    elif 5 <= w <= 40:
        depth = 15
    elif w >= 3:
        depth = 10
    else:
        depth = 5

    # Balance — only meaningful with multiple speakers; neutral (18) otherwise
    if len(speaker_percentages) > 1:
        dominant = max(speaker_percentages)
        ideal = 100.0 / len(speaker_percentages)
        deviation = abs(dominant - ideal)
        if deviation <= 10:
            balance = 25
        elif deviation <= 20:
            balance = 20
        elif deviation <= 30:
            balance = 15
        elif deviation <= 45:
            balance = 10
        else:
            balance = 5
    else:
        balance = 18

    # Pace — natural conversational range: 130-170 wpm
    if wpm is None or wpm <= 0:
        pace = 18
    elif 130 <= wpm <= 170:
        pace = 25
    elif 110 <= wpm <= 190:
        pace = 20
    elif 90 <= wpm <= 210:
        pace = 15
    elif 60 <= wpm <= 240:
        pace = 10
    else:
        pace = 5

    score = clarity + depth + balance + pace

    def _rate(v: int) -> str:
        if v >= 22:
            return "excellent"
        if v >= 17:
            return "good"
        if v >= 12:
            return "fair"
        return "low"

    factors = {"clarity": clarity, "depth": depth, "balance": balance, "pace": pace}
    ratings = {k: _rate(v) for k, v in factors.items()}
    return score, factors, ratings


def _insights(
    filler_rate: float,
    avg_words_per_segment: float,
    wpm: float | None,
    quality_ratings: dict[str, str],
    speaker_data: list[dict],
) -> dict[str, list[str]]:
    strengths: list[str] = []
    observations: list[str] = []

    if quality_ratings["clarity"] == "excellent":
        strengths.append("Very few filler words — speech is clear")
    if quality_ratings["depth"] == "excellent":
        strengths.append("Turns are substantive (12–25 words on average)")
    if len(speaker_data) > 1 and quality_ratings["balance"] == "excellent":
        strengths.append("Speakers contribute roughly evenly")
    if quality_ratings["pace"] == "excellent":
        strengths.append("Speaking pace is in the natural conversational range (130–170 wpm)")

    if filler_rate > 0.08:
        observations.append(f"Filler words make up {filler_rate:.1%} of spoken words")
    if avg_words_per_segment < 5:
        observations.append("Very short turns — could indicate hesitation or rapid exchange")
    if avg_words_per_segment > 30:
        observations.append("Long turns — may be a lecture or monologue format")
    if wpm is not None and wpm < 90:
        observations.append(f"Slow pace ({wpm:.0f} wpm) — may include long pauses")
    if wpm is not None and wpm > 200:
        observations.append(f"Fast pace ({wpm:.0f} wpm) — speakers talking quickly")
    if len(speaker_data) > 1:
        dominant = max(speaker_data, key=lambda s: s["percentage"])
        if dominant["percentage"] > 70:
            observations.append(
                f"{dominant['id']} dominates with {dominant['percentage']:.0f}% of spoken words"
            )

    if not strengths:
        strengths.append("Transcript analysed successfully")

    return {"strengths": strengths, "observations": observations}


class SpeechAnalyzer:
    """Derives speech quality metrics from a TranscriptionResult."""

    def analyse(
        self,
        result: TranscriptionResult,
        speaker_data: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Args:
            result: output from Transcriber.transcribe()
            speaker_data: optional list of dicts with 'id' and 'percentage' keys,
                          populated by AudioLens after diarization
        """
        words = result.text.split() if result.text else []
        word_count = len(words)
        duration_minutes = result.duration / 60

        wpm = round(word_count / duration_minutes, 1) if duration_minutes > 0 else 0.0

        filler_count, filler_words_found = _detect_fillers(result.text)
        filler_rate = round(filler_count / word_count, 4) if word_count > 0 else 0.0

        speaking_time = sum(s.end - s.start for s in result.segments)
        silence_ratio = round(
            1.0 - (speaking_time / result.duration), 3
        ) if result.duration > 0 else 0.0

        avg_words_per_segment = (
            sum(len(s.text.split()) for s in result.segments) / len(result.segments)
            if result.segments else 0.0
        )

        pace_cat = _pace_category(wpm) if wpm > 0 else "natural"

        spk = speaker_data or []
        speaker_percentages = [s["percentage"] for s in spk]

        quality_score, quality_factors, quality_ratings = _quality_score(
            filler_rate=filler_rate,
            avg_words_per_segment=avg_words_per_segment,
            wpm=wpm if wpm > 0 else None,
            speaker_percentages=speaker_percentages,
        )

        insights = _insights(
            filler_rate=filler_rate,
            avg_words_per_segment=avg_words_per_segment,
            wpm=wpm if wpm > 0 else None,
            quality_ratings=quality_ratings,
            speaker_data=spk,
        )

        return {
            "word_count": word_count,
            "speaking_rate_wpm": wpm,
            "pace_category": pace_cat,
            "filler_word_count": filler_count,
            "filler_word_rate": filler_rate,
            "filler_words_found": filler_words_found,
            "silence_ratio": silence_ratio,
            "actual_speaking_time": round(speaking_time, 1),
            "quality_score": quality_score,
            "quality_factors": quality_factors,
            "quality_ratings": quality_ratings,
            "insights": insights,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_speech_analyzer.py -v 2>&1 | tail -25
```

Expected: all tests pass.

- [ ] **Step 5: Run full suite to check for regressions**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: `test_app.py` and `test_audio_lens.py` may show failures because `_FAKE_ANALYSIS` in `test_app.py` no longer matches the new `SpeechMetrics` schema and `test_success_shape` may need updating. That is expected — those will be fixed in Task 5. Count the failures; all others should pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/speech_analyzer.py tests/test_speech_analyzer.py
git commit -m "feat(audio-lens): multi-word fillers, quality score, pace category, insights"
```

---

## Task 2: ModelNotAvailableError + transcriber download warning

**Files:**
- Modify: `audio-lens/src/audio_lens/exceptions.py`
- Modify: `audio-lens/src/audio_lens/__init__.py`
- Modify: `audio-lens/src/audio_lens/transcriber.py`

### What and why

`ModelNotAvailableError` signals "model not downloaded or not configured" — distinct from a file-not-found or transcription failure. The API will return 503 for this (service unavailable, try later) rather than 400 (bad request). The transcriber `_load()` currently downloads the Whisper model silently on first use; for large models (large-v3 = 1.5 GB) this causes a long hang with no feedback.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_audio_lens.py` (append to the existing `TestAudioLensSilent` class):

```python
def test_model_not_available_is_subclass_of_audio_lens_error(self):
    from audio_lens.exceptions import ModelNotAvailableError, AudioLensError
    assert issubclass(ModelNotAvailableError, AudioLensError)

def test_model_not_available_exported_from_package(self):
    from audio_lens import ModelNotAvailableError  # noqa: F401
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py::TestAudioLensSilent::test_model_not_available_is_subclass_of_audio_lens_error tests/test_audio_lens.py::TestAudioLensSilent::test_model_not_available_exported_from_package -v 2>&1 | tail -10
```

Expected: `ImportError: cannot import name 'ModelNotAvailableError'`.

- [ ] **Step 3: Update exceptions.py**

Replace `src/audio_lens/exceptions.py`:

```python
class AudioLensError(Exception):
    """Raised when audio-lens cannot analyse a file."""


class ModelNotAvailableError(AudioLensError):
    """Raised when a required model is not installed or not yet downloaded.

    The message includes instructions for resolving the issue.
    Callers should treat this as a recoverable condition (e.g. HTTP 503).
    """
```

- [ ] **Step 4: Update __init__.py**

Replace `src/audio_lens/__init__.py`:

```python
from .audio_lens import AudioLens
from .exceptions import AudioLensError, ModelNotAvailableError

__all__ = ["AudioLens", "AudioLensError", "ModelNotAvailableError"]
```

- [ ] **Step 5: Update transcriber.py to warn before download**

Replace `src/audio_lens/transcriber.py`:

```python
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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


# Maps model size → approximate download size for the user-facing warning.
_MODEL_SIZES = {
    "tiny": "39 MB",
    "base": "74 MB",
    "small": "244 MB",
    "medium": "769 MB",
    "large-v3": "1.5 GB",
}


def _is_whisper_cached(model_size: str) -> bool:
    """Return True if the faster-whisper model is already in the HF cache."""
    try:
        from huggingface_hub import try_to_load_from_cache
        repo_id = f"Systran/faster-whisper-{model_size}"
        result = try_to_load_from_cache(repo_id, "config.json")
        return result is not None and result != "not in cache"
    except Exception:
        return True  # assume cached on any error to avoid false warnings


class Transcriber:
    """Wraps Faster-Whisper for audio transcription.

    Model is loaded lazily on first call to transcribe().
    """

    SUPPORTED_EXTENSIONS = {
        ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".opus",
    }

    def __init__(self, model_size: str = "base") -> None:
        self._model_size = model_size
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            if not _is_whisper_cached(self._model_size):
                size_hint = _MODEL_SIZES.get(self._model_size, "unknown size")
                print(
                    f"[audio-lens] Downloading Whisper '{self._model_size}' model "
                    f"({size_hint}) — this only happens once.",
                    file=sys.stderr,
                    flush=True,
                )
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe an audio file."""
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

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py::TestAudioLensSilent::test_model_not_available_is_subclass_of_audio_lens_error tests/test_audio_lens.py::TestAudioLensSilent::test_model_not_available_exported_from_package -v 2>&1 | tail -10
```

Expected: `2 passed`.

- [ ] **Step 7: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/exceptions.py src/audio_lens/__init__.py src/audio_lens/transcriber.py tests/test_audio_lens.py
git commit -m "feat(audio-lens): ModelNotAvailableError, Whisper download progress warning"
```

---

## Task 3: Diarizer module

**Files:**
- Create: `audio-lens/src/audio_lens/diarizer.py`
- Create: `audio-lens/tests/test_diarizer.py`
- Modify: `audio-lens/pyproject.toml`

### What and why

`diarizer.py` wraps pyannote.audio's `Pipeline`. It is entirely self-contained — `AudioLens` imports it but the dependency (`pyannote.audio`) is optional. If pyannote is not installed or no HF token is found, the class raises `ModelNotAvailableError` with actionable instructions. The pipeline is loaded lazily and cached on the instance.

pyannote.audio requires a Hugging Face token with access to `pyannote/speaker-diarization-3.1`. Users get this by:
1. Creating a free account at huggingface.co
2. Accepting the model terms at `https://huggingface.co/pyannote/speaker-diarization-3.1`
3. Setting `HF_TOKEN=<token>` environment variable

- [ ] **Step 1: Add the optional dependency to pyproject.toml**

Read `pyproject.toml`, then replace the `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
diarization = [
    "pyannote.audio>=3.1.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_diarizer.py`:

```python
"""Unit tests for Diarizer — pyannote pipeline is always mocked."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from audio_lens.diarizer import Diarizer, DiarizationTurn
from audio_lens.exceptions import AudioLensError, ModelNotAvailableError


class TestDiarizerImportGuard:
    def test_raises_model_not_available_when_pyannote_missing(self, tmp_path):
        d = Diarizer()
        with patch.object(d, "_import_pipeline", side_effect=ImportError("no module named pyannote")):
            with pytest.raises(ModelNotAvailableError, match="not installed"):
                d.diarize(tmp_path / "x.wav")

    def test_model_not_available_is_audio_lens_error(self, tmp_path):
        d = Diarizer()
        with patch.object(d, "_import_pipeline", side_effect=ImportError("no module")):
            with pytest.raises(AudioLensError):
                d.diarize(tmp_path / "x.wav")


class TestDiarizerNoToken:
    def test_raises_when_no_token(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)

        mock_pipeline_cls = MagicMock()
        d = Diarizer()
        with patch.object(d, "_import_pipeline", return_value=mock_pipeline_cls):
            with patch("audio_lens.diarizer.Path") as mock_path_cls:
                # Make the token file appear not to exist
                mock_token_file = MagicMock()
                mock_token_file.exists.return_value = False
                mock_path_cls.home.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_token_file
                with pytest.raises(ModelNotAvailableError, match="No Hugging Face token"):
                    d.diarize(tmp_path / "x.wav")


class TestDiarizerTurns:
    def _make_diarizer_with_annotation(self, tracks):
        """Create a Diarizer whose pipeline returns a mock annotation."""
        mock_ann = MagicMock()
        mock_ann.itertracks.return_value = tracks

        d = Diarizer()
        d._pipeline = MagicMock(return_value=mock_ann)
        return d

    def test_returns_sorted_turns(self, silent_wav):
        t1 = MagicMock(start=0.0, end=2.0)
        t2 = MagicMock(start=2.5, end=5.0)
        d = self._make_diarizer_with_annotation([
            (t2, None, "SPEAKER_01"),
            (t1, None, "SPEAKER_00"),
        ])
        turns = d.diarize(silent_wav)
        assert len(turns) == 2
        assert turns[0].start == 0.0
        assert turns[0].speaker == "SPEAKER_00"
        assert turns[1].start == 2.5
        assert turns[1].speaker == "SPEAKER_01"

    def test_returns_diarization_turn_objects(self, silent_wav):
        t = MagicMock(start=1.0, end=3.0)
        d = self._make_diarizer_with_annotation([(t, None, "SPEAKER_00")])
        turns = d.diarize(silent_wav)
        assert isinstance(turns[0], DiarizationTurn)

    def test_empty_annotation_returns_empty_list(self, silent_wav):
        d = self._make_diarizer_with_annotation([])
        turns = d.diarize(silent_wav)
        assert turns == []

    def test_num_speakers_passed_to_pipeline(self, silent_wav):
        t = MagicMock(start=0.0, end=1.0)
        mock_ann = MagicMock()
        mock_ann.itertracks.return_value = [(t, None, "SPEAKER_00")]
        mock_pipeline = MagicMock(return_value=mock_ann)
        d = Diarizer()
        d._pipeline = mock_pipeline
        d.diarize(silent_wav, num_speakers=2)
        mock_pipeline.assert_called_once_with(str(silent_wav), num_speakers=2)

    def test_pipeline_error_raises_audio_lens_error(self, silent_wav):
        d = Diarizer()
        d._pipeline = MagicMock(side_effect=RuntimeError("CUDA error"))
        with pytest.raises(AudioLensError, match="Diarization failed"):
            d.diarize(silent_wav)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_diarizer.py -v 2>&1 | tail -15
```

Expected: `ImportError: cannot import name 'Diarizer'`.

- [ ] **Step 4: Create diarizer.py**

Create `src/audio_lens/diarizer.py`:

```python
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import AudioLensError, ModelNotAvailableError

_MODEL_ID = "pyannote/speaker-diarization-3.1"


@dataclass
class DiarizationTurn:
    start: float
    end: float
    speaker: str


class Diarizer:
    """Speaker diarization via pyannote.audio.

    Requires:
      - pip install 'audio-lens[diarization]'  (installs pyannote.audio)
      - HF_TOKEN env var with access granted to pyannote/speaker-diarization-3.1
        Get a token: https://huggingface.co/settings/tokens
        Accept terms: https://huggingface.co/pyannote/speaker-diarization-3.1
    """

    def __init__(self) -> None:
        self._pipeline: Any = None

    def _import_pipeline(self):
        """Import Pipeline from pyannote.audio. Separate method for testability."""
        from pyannote.audio import Pipeline
        return Pipeline

    def _resolve_token(self) -> str | None:
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if token:
            return token
        token_file = Path.home() / ".cache" / "huggingface" / "token"
        if token_file.exists():
            val = token_file.read_text().strip()
            return val or None
        return None

    def _load(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        try:
            Pipeline = self._import_pipeline()
        except ImportError as e:
            raise ModelNotAvailableError(
                "pyannote.audio is not installed. "
                "Install with: pip install 'audio-lens[diarization]'"
            ) from e

        token = self._resolve_token()
        if not token:
            raise ModelNotAvailableError(
                "No Hugging Face token found. Diarization requires a token with access to "
                f"{_MODEL_ID}. Set the HF_TOKEN environment variable. "
                "Get a free token at https://huggingface.co/settings/tokens and accept "
                f"the model terms at https://huggingface.co/{_MODEL_ID}"
            )

        try:
            from huggingface_hub import try_to_load_from_cache
            cached = try_to_load_from_cache(_MODEL_ID, "config.yaml")
            if cached is None:
                print(
                    f"[audio-lens] Downloading diarization model '{_MODEL_ID}' "
                    f"(~2 GB, first use only)...",
                    file=sys.stderr,
                    flush=True,
                )
        except Exception:
            pass

        try:
            self._pipeline = Pipeline.from_pretrained(_MODEL_ID, use_auth_token=token)
        except Exception as e:
            raise ModelNotAvailableError(
                f"Could not load diarization model: {e}. "
                "Ensure you have accepted the model terms at "
                f"https://huggingface.co/{_MODEL_ID}"
            ) from e

        return self._pipeline

    def diarize(
        self, audio_path: Path, num_speakers: int | None = None
    ) -> list[DiarizationTurn]:
        """Run speaker diarization on an audio file.

        Returns list of DiarizationTurn sorted by start time.

        Raises:
            ModelNotAvailableError: pyannote.audio not installed or no HF token.
            AudioLensError: diarization pipeline failed.
        """
        pipeline = self._load()

        kwargs: dict[str, Any] = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers

        try:
            annotation = pipeline(str(audio_path), **kwargs)
        except Exception as e:
            raise AudioLensError(f"Diarization failed: {e}") from e

        turns = [
            DiarizationTurn(
                start=round(turn.start, 3),
                end=round(turn.end, 3),
                speaker=speaker,
            )
            for turn, _, speaker in annotation.itertracks(yield_label=True)
        ]
        turns.sort(key=lambda t: t.start)
        return turns
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_diarizer.py -v 2>&1 | tail -20
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/diarizer.py tests/test_diarizer.py pyproject.toml
git commit -m "feat(audio-lens): add Diarizer module with pyannote.audio, optional dep"
```

---

## Task 4: Wire diarization into AudioLens

**Files:**
- Modify: `audio-lens/src/audio_lens/audio_lens.py`
- Modify: `audio-lens/tests/conftest.py`
- Modify: `audio-lens/tests/test_audio_lens.py`

### What and why

`AudioLens.analyse()` gains a `diarize: bool = False` parameter. When `True`, it calls `Diarizer.diarize()`, assigns speakers to segments by maximum time overlap, computes talk-time distribution, and passes `speaker_data` to `SpeechAnalyzer` so the balance factor in the quality score reflects real speaker proportions. The result dict gains three new top-level keys: `diarization_available`, `speakers`, `talk_time`. Segments gain a `speaker` key (always present, `None` when diarization is off).

Helper functions `_assign_speakers` and `_compute_talk_time` are module-level for testability.

- [ ] **Step 1: Add two-speaker WAV fixture to conftest.py**

Append to `tests/conftest.py`:

```python
import math
import struct


@pytest.fixture
def two_speaker_wav(tmp_path: Path) -> Path:
    """A WAV with two tones at different frequencies, simulating two speakers.

    4 seconds total: 440 Hz for first 2s, 880 Hz for second 2s.
    Useful for testing speaker assignment logic with mocked diarization.
    """
    path = tmp_path / "two_speaker.wav"
    sample_rate = 16000
    duration = 4  # seconds

    frames = bytearray()
    for i in range(sample_rate * duration):
        t = i / sample_rate
        freq = 440.0 if t < 2.0 else 880.0
        sample = int(32767 * math.sin(2 * math.pi * freq * t))
        frames += struct.pack("<h", sample)

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))

    return path
```

Note: `import math`, `import struct`, and `import wave` must be at the top of conftest.py. Read the file first — `wave` is already there, add `import math` and `import struct`.

- [ ] **Step 2: Write the failing tests**

Append to the `TestAudioLensSilent` class in `tests/test_audio_lens.py`:

```python
def test_success_shape_has_diarization_keys(self, silent_wav: Path):
    lens = AudioLens()
    result = lens.analyse(silent_wav)
    assert "diarization_available" in result
    assert "speakers" in result
    assert "talk_time" in result
    assert result["diarization_available"] is False
    assert result["speakers"] is None
    assert result["talk_time"] is None

def test_segments_have_speaker_key(self, silent_wav: Path):
    lens = AudioLens()
    result = lens.analyse(silent_wav)
    for seg in result["segments"]:
        assert "speaker" in seg
        assert seg["speaker"] is None  # no diarization

def test_speech_metrics_has_new_fields(self, silent_wav: Path):
    lens = AudioLens()
    result = lens.analyse(silent_wav)
    m = result["speech_metrics"]
    assert "pace_category" in m
    assert "quality_score" in m
    assert "quality_factors" in m
    assert "quality_ratings" in m
    assert "insights" in m
    assert m["pace_category"] in {"slow", "natural", "fast"}
    assert 0 <= m["quality_score"] <= 100
```

Add a new test class for diarization integration:

```python
class TestAudioLensDiarization:
    def test_diarize_flag_populates_speakers(self, silent_wav: Path):
        from unittest.mock import patch
        from audio_lens.diarizer import DiarizationTurn

        fake_turns = [
            DiarizationTurn(start=0.0, end=0.5, speaker="SPEAKER_00"),
        ]
        with patch("audio_lens.audio_lens.Diarizer.diarize", return_value=fake_turns):
            result = AudioLens().analyse(silent_wav, diarize=True)

        assert result["diarization_available"] is True
        assert result["speakers"] is not None
        assert len(result["speakers"]) >= 1
        assert result["speakers"][0]["id"] == "SPEAKER_00"

    def test_diarize_assigns_speaker_to_segments(self, silent_wav: Path):
        from unittest.mock import patch
        from audio_lens.diarizer import DiarizationTurn

        fake_turns = [
            DiarizationTurn(start=0.0, end=10.0, speaker="SPEAKER_00"),
        ]
        with patch("audio_lens.audio_lens.Diarizer.diarize", return_value=fake_turns):
            result = AudioLens().analyse(silent_wav, diarize=True)

        # All segments should be assigned to SPEAKER_00 (covers the whole file)
        for seg in result["segments"]:
            if seg["speaker"] is not None:
                assert seg["speaker"] == "SPEAKER_00"

    def test_diarize_talk_time_populated(self, silent_wav: Path):
        from unittest.mock import patch
        from audio_lens.diarizer import DiarizationTurn

        fake_turns = [
            DiarizationTurn(start=0.0, end=0.5, speaker="SPEAKER_00"),
        ]
        with patch("audio_lens.audio_lens.Diarizer.diarize", return_value=fake_turns):
            result = AudioLens().analyse(silent_wav, diarize=True)

        assert result["talk_time"] is not None
        assert "is_balanced" in result["talk_time"]

    def test_diarize_false_skips_diarizer(self, silent_wav: Path):
        from unittest.mock import patch
        with patch("audio_lens.audio_lens.Diarizer.diarize") as mock_diarize:
            AudioLens().analyse(silent_wav, diarize=False)
        mock_diarize.assert_not_called()
```

- [ ] **Step 3: Run to verify failure**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py -k "diarization_keys or speaker_key or new_fields or diarize" -v 2>&1 | tail -15
```

Expected: failures because `AudioLens.analyse()` doesn't accept `diarize` param yet and doesn't have the new output keys.

- [ ] **Step 4: Rewrite audio_lens.py**

Replace `src/audio_lens/audio_lens.py`:

```python
from pathlib import Path
from typing import Any

from .diarizer import Diarizer, DiarizationTurn
from .exceptions import AudioLensError, ModelNotAvailableError
from .speech_analyzer import SpeechAnalyzer
from .transcriber import Segment, Transcriber


def _assign_speakers(
    segments: list[Segment], turns: list[DiarizationTurn]
) -> list[str | None]:
    """Assign each segment its speaker by maximum time overlap with diarization turns."""
    result: list[str | None] = []
    for seg in segments:
        best_speaker: str | None = None
        best_overlap = 0.0
        for turn in turns:
            overlap = max(0.0, min(seg.end, turn.end) - max(seg.start, turn.start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn.speaker
        result.append(best_speaker)
    return result


def _compute_talk_time(
    segments: list[Segment], speaker_assignments: list[str | None]
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Compute per-speaker word count, duration, and percentage.

    Returns (talk_time dict, speaker_data list). Both are None/[] if no speakers assigned.
    """
    counts: dict[str, dict[str, Any]] = {}
    for seg, spk in zip(segments, speaker_assignments):
        if spk is None:
            continue
        if spk not in counts:
            counts[spk] = {"words": 0, "duration": 0.0}
        counts[spk]["words"] += len(seg.text.split())
        counts[spk]["duration"] += seg.end - seg.start

    total_words = sum(v["words"] for v in counts.values())
    if total_words == 0:
        return None, []

    speaker_data = sorted(
        [
            {
                "id": spk,
                "word_count": data["words"],
                "duration_seconds": round(data["duration"], 1),
                "percentage": round(data["words"] / total_words * 100, 1),
            }
            for spk, data in counts.items()
        ],
        key=lambda s: s["percentage"],
        reverse=True,
    )

    dominant = speaker_data[0]
    is_balanced = dominant["percentage"] <= 70
    talk_time = {
        "is_balanced": is_balanced,
        "dominant_speaker": None if is_balanced else dominant["id"],
    }
    return talk_time, speaker_data


class AudioLens:
    """Transcribes audio files and returns speech metrics.

    Args:
        model_size: Whisper model size (tiny, base, small, medium, large-v3).
    """

    def __init__(self, model_size: str = "base") -> None:
        self._transcriber = Transcriber(model_size=model_size)
        self._analyzer = SpeechAnalyzer()
        self._diarizer = Diarizer()

    def analyse(self, file_path: Path | str, diarize: bool = False) -> dict[str, Any]:
        """Analyse an audio file.

        Args:
            file_path: path to the audio file.
            diarize: if True, run speaker diarization (requires audio-lens[diarization]
                     and HF_TOKEN env var). Default False.

        Returns:
            Analysis dict with transcript, language, duration, segments, speech_metrics,
            diarization_available, speakers, talk_time, file_path, file_size.

        Raises:
            AudioLensError: file missing, format unsupported, or transcription failed.
            ModelNotAvailableError: diarize=True but pyannote.audio not installed or
                                    no HF token configured.
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

            diarization_available = False
            speaker_assignments: list[str | None] = [None] * len(result.segments)
            talk_time: dict[str, Any] | None = None
            speaker_data: list[dict[str, Any]] = []

            if diarize:
                turns = self._diarizer.diarize(file_path)
                speaker_assignments = _assign_speakers(result.segments, turns)
                diarization_available = True
                talk_time, speaker_data = _compute_talk_time(result.segments, speaker_assignments)

            metrics = self._analyzer.analyse(
                result,
                speaker_data=speaker_data if speaker_data else None,
            )

            return {
                "transcript": result.text,
                "language": result.language,
                "duration": result.duration,
                "segments": [
                    {
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                        "speaker": speaker_assignments[i],
                    }
                    for i, s in enumerate(result.segments)
                ],
                "speech_metrics": metrics,
                "diarization_available": diarization_available,
                "speakers": speaker_data if speaker_data else None,
                "talk_time": talk_time,
                "file_path": str(file_path),
                "file_size": file_size,
            }
        except (AudioLensError, ModelNotAvailableError):
            raise
        except Exception as e:
            raise AudioLensError(str(e)) from e
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/test_audio_lens.py -v 2>&1 | tail -20
```

Expected: all tests pass (including the diarization tests).

- [ ] **Step 6: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/audio_lens.py tests/conftest.py tests/test_audio_lens.py
git commit -m "feat(audio-lens): wire diarization into AudioLens.analyse(), add speakers + talk_time to output"
```

---

## Task 5: Update schemas, app, CLI, and API tests

**Files:**
- Modify: `audio-lens/src/audio_lens/schemas.py`
- Modify: `audio-lens/src/audio_lens/app.py`
- Modify: `audio-lens/src/audio_lens/cli.py`
- Modify: `audio-lens/tests/test_app.py`

### What and why

The Pydantic schemas must reflect the new output shape. The FastAPI app gets a `diarize: bool = Form(default=False)` parameter and handles `ModelNotAvailableError` as HTTP 503. The CLI `analyse` subcommand gets `--diarize`. `test_app.py`'s `_FAKE_ANALYSIS` must include all new fields.

- [ ] **Step 1: Update schemas.py**

Replace `src/audio_lens/schemas.py`:

```python
from typing import Any

from pydantic import BaseModel


class QualityFactors(BaseModel):
    clarity: int
    depth: int
    balance: int
    pace: int


class QualityRatings(BaseModel):
    clarity: str
    depth: str
    balance: str
    pace: str


class Insights(BaseModel):
    strengths: list[str]
    observations: list[str]


class SpeechMetrics(BaseModel):
    word_count: int
    speaking_rate_wpm: float
    pace_category: str
    filler_word_count: int
    filler_word_rate: float
    filler_words_found: list[str]
    silence_ratio: float
    actual_speaking_time: float
    quality_score: int
    quality_factors: QualityFactors
    quality_ratings: QualityRatings
    insights: Insights


class SpeakerInfo(BaseModel):
    id: str
    word_count: int
    duration_seconds: float
    percentage: float


class TalkTime(BaseModel):
    is_balanced: bool
    dominant_speaker: str | None = None


class AudioAnalysis(BaseModel):
    transcript: str
    language: str
    duration: float
    segments: list[dict[str, Any]]
    speech_metrics: SpeechMetrics
    diarization_available: bool
    speakers: list[SpeakerInfo] | None = None
    talk_time: TalkTime | None = None
    file_path: str
    file_size: int


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
```

- [ ] **Step 2: Update app.py**

Read the current `src/audio_lens/app.py`, then apply two changes:

**Change 1** — add `ModelNotAvailableError` import at the top:
```python
from .exceptions import AudioLensError, ModelNotAvailableError
```

**Change 2** — add `diarize` Form field and 503 handler in the `analyse` endpoint. Replace the entire `analyse` function:

```python
@app.post("/analyse", response_model=AudioAnalysis)
async def analyse(
    file: UploadFile = File(..., description="Audio file to analyse"),
    model: str | None = Form(default=None, description="Whisper model size (optional)"),
    diarize: bool = Form(
        default=False,
        description="Run speaker diarization (requires audio-lens[diarization] and HF_TOKEN)",
    ),
) -> AudioAnalysis:
    model_size = model if model is not None else os.getenv("AUDIO_LENS_MODEL", "base")

    if model_size not in _VALID_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model_size}'. Must be one of: {', '.join(sorted(_VALID_MODELS))}",
        )

    # Respect env-var default for diarize if not explicitly passed
    if not diarize:
        diarize = os.getenv("AUDIO_LENS_DIARIZE", "false").lower() == "true"

    suffix = Path(file.filename or "upload").suffix or ".wav"
    content = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        data = _get_lens(model_size).analyse(tmp_path, diarize=diarize)
        return AudioAnalysis(**data)
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AudioLensError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)
```

- [ ] **Step 3: Update cli.py**

Read `src/audio_lens/cli.py`. Then:

**Change 1** — add `--diarize` to the `analyse` subparser (after the `--json` argument):

```python
analyse.add_argument(
    "--diarize",
    action="store_true",
    help="Run speaker diarization (requires audio-lens[diarization] and HF_TOKEN)",
)
```

**Change 2** — update `_cmd_analyse` to pass `diarize` to `lens.analyse()` and handle `ModelNotAvailableError`:

```python
def _cmd_analyse(args) -> None:
    from .audio_lens import AudioLens
    from .exceptions import AudioLensError, ModelNotAvailableError

    model = args.model if args.model is not None else os.getenv("AUDIO_LENS_MODEL", "base")
    diarize = args.diarize or os.getenv("AUDIO_LENS_DIARIZE", "false").lower() == "true"
    lens = AudioLens(model_size=model)

    try:
        result = lens.analyse(args.file, diarize=diarize)
    except ModelNotAvailableError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        else:
            print(f"Diarization unavailable: {e}", file=sys.stderr)
        sys.exit(2)
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
    print(f"Speaking rate: {result['speech_metrics']['speaking_rate_wpm']} wpm "
          f"({result['speech_metrics']['pace_category']})")
    print(f"Filler words:  {result['speech_metrics']['filler_word_count']} "
          f"({result['speech_metrics']['filler_word_rate']:.1%})")
    print(f"Silence ratio: {result['speech_metrics']['silence_ratio']:.1%}")
    print(f"Quality score: {result['speech_metrics']['quality_score']}/100")

    insights = result["speech_metrics"]["insights"]
    if insights["strengths"]:
        print(f"\nStrengths:")
        for s in insights["strengths"]:
            print(f"  • {s}")
    if insights["observations"]:
        print(f"\nObservations:")
        for o in insights["observations"]:
            print(f"  • {o}")

    if result.get("speakers"):
        print(f"\nSpeakers ({len(result['speakers'])}):")
        for spk in result["speakers"]:
            print(f"  {spk['id']}: {spk['percentage']:.0f}% ({spk['word_count']} words)")

    print(f"\nTranscript:")
    print(result["transcript"])
```

- [ ] **Step 4: Update test_app.py with new _FAKE_ANALYSIS**

Read `tests/test_app.py`. Replace `_FAKE_ANALYSIS` with the complete new shape:

```python
_FAKE_ANALYSIS = {
    "transcript": "hello world",
    "language": "en",
    "duration": 5.0,
    "segments": [{"start": 0.0, "end": 5.0, "text": "hello world", "speaker": None}],
    "speech_metrics": {
        "word_count": 2,
        "speaking_rate_wpm": 24.0,
        "pace_category": "slow",
        "filler_word_count": 0,
        "filler_word_rate": 0.0,
        "filler_words_found": [],
        "silence_ratio": 0.0,
        "actual_speaking_time": 5.0,
        "quality_score": 62,
        "quality_factors": {"clarity": 25, "depth": 5, "balance": 18, "pace": 14},
        "quality_ratings": {"clarity": "excellent", "depth": "low", "balance": "good", "pace": "fair"},
        "insights": {
            "strengths": ["Very few filler words — speech is clear"],
            "observations": [],
        },
    },
    "diarization_available": False,
    "speakers": None,
    "talk_time": None,
    "file_path": "/tmp/test.wav",
    "file_size": 1234,
}
```

Also add a test for the `diarize` form param and 503 handling:

```python
class TestDiarizeEndpoint:
    def test_diarize_param_accepted(self, silent_wav_bytes: bytes):
        with patch("audio_lens.app._get_lens") as mock_get_lens:
            mock_get_lens.return_value.analyse.return_value = _FAKE_ANALYSIS.copy()
            response = client.post(
                "/analyse",
                files={"file": ("test.wav", silent_wav_bytes, "audio/wav")},
                data={"diarize": "false"},
            )
        assert response.status_code == 200

    def test_diarize_model_unavailable_returns_503(self, silent_wav_bytes: bytes):
        from audio_lens.exceptions import ModelNotAvailableError
        with patch("audio_lens.app._get_lens") as mock_get_lens:
            mock_get_lens.return_value.analyse.side_effect = ModelNotAvailableError(
                "pyannote.audio is not installed"
            )
            response = client.post(
                "/analyse",
                files={"file": ("test.wav", silent_wav_bytes, "audio/wav")},
                data={"diarize": "true"},
            )
        assert response.status_code == 503
        assert "pyannote" in response.json()["detail"]
```

- [ ] **Step 5: Run the full test suite**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -m pytest tests/ -v 2>&1 | tail -30
```

Expected: all tests pass.

- [ ] **Step 6: Verify the app imports cleanly**

```bash
cd /Users/michael/Projects/lens/audio-lens
python -c "from audio_lens.app import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
cd /Users/michael/Projects/lens/audio-lens
git add src/audio_lens/schemas.py src/audio_lens/app.py src/audio_lens/cli.py tests/test_app.py
git commit -m "feat(audio-lens): update schemas, app, CLI for new output shape + diarize param"
```

---

## Self-Review

### Spec coverage check

| Requirement | Task | Status |
|---|---|---|
| Multi-word filler phrases ("you know", "i mean", etc.) | Task 1 | ✅ |
| `filler_word_rate` as fraction (not per-minute) | Task 1 | ✅ |
| Quality score 0-100 with 4 factors | Task 1 | ✅ |
| Per-factor ratings (excellent/good/fair/low) | Task 1 | ✅ |
| Pace benchmarking (slow/natural/fast) | Task 1 | ✅ |
| Insights (strengths + observations) | Task 1 | ✅ |
| `ModelNotAvailableError` subclass | Task 2 | ✅ |
| Exported from package root | Task 2 | ✅ |
| Whisper download warning on stderr | Task 2 | ✅ |
| `Diarizer` class with pyannote.audio | Task 3 | ✅ |
| `[diarization]` optional dep group | Task 3 | ✅ |
| Graceful ImportError → `ModelNotAvailableError` | Task 3 | ✅ |
| HF token resolution (env + file) | Task 3 | ✅ |
| Diarization download warning on stderr | Task 3 | ✅ |
| `analyse(diarize=False)` default | Task 4 | ✅ |
| Speaker assignment by max overlap | Task 4 | ✅ |
| `diarization_available` in result | Task 4 | ✅ |
| `speakers` list in result | Task 4 | ✅ |
| `talk_time` dict in result | Task 4 | ✅ |
| `speaker` key on each segment | Task 4 | ✅ |
| Quality score uses real balance when speakers present | Task 4 (via speaker_data param to SpeechAnalyzer) | ✅ |
| Updated Pydantic schemas | Task 5 | ✅ |
| `diarize` Form param in `/analyse` | Task 5 | ✅ |
| `AUDIO_LENS_DIARIZE` env var default | Task 5 | ✅ |
| HTTP 503 for `ModelNotAvailableError` | Task 5 | ✅ |
| `--diarize` CLI flag | Task 5 | ✅ |
| `AUDIO_LENS_DIARIZE` env var in CLI | Task 5 | ✅ |
| `ModelNotAvailableError` → exit code 2 in CLI | Task 5 | ✅ |

### Placeholder scan

No TBD, TODO, or incomplete sections found.

### Type consistency

- `DiarizationTurn` defined in Task 3 (`diarizer.py`), imported in Task 4 (`audio_lens.py`) — consistent.
- `speaker_data` is `list[dict]` passed from `AudioLens` to `SpeechAnalyzer.analyse()` — Task 1 and Task 4 both use `list[dict]` with `"id"` and `"percentage"` keys.
- `_FAKE_ANALYSIS` in Task 5 includes all fields defined in `schemas.py` Task 5 — consistent.
- `ModelNotAvailableError` defined Task 2, used Task 3 (`diarizer.py`), re-raised Task 4 (`audio_lens.py`), caught Task 5 (`app.py`, `cli.py`) — consistent.
