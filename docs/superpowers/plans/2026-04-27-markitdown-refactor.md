# markitdown Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace duplicated hand-rolled document parsers in `document-lens` and `extracta` with Microsoft's `markitdown` library, while keeping `pdfplumber` in `document-lens` for real page-boundary extraction required by the desktop research viewer.

**Architecture:** `document-lens` keeps pdfplumber for PDF page extraction (required by the desktop per-page viewer) and delegates all other formats (DOCX, PPTX, XLSX, CSV, text) to markitdown via a single `_extract_with_markitdown()` method. `extracta` replaces all format-specific parsers with a single `MarkItDown().convert(path)` call, since it has no page-level requirement.

**Tech Stack:** Python, `markitdown[docx,pptx,xlsx]` (document-lens), `markitdown[docx,pptx,xlsx,pdf]` (extracta), `pdfplumber` (document-lens PDF path only), `pypdf` (document-lens PDF metadata), `uv` for dependency management.

**Spec:** `docs/superpowers/specs/2026-04-27-markitdown-refactor-design.md`

---

## File Map

| File | Action | Reason |
|------|--------|--------|
| `document-lens/pyproject.toml` | Modify | Swap python-docx/pptx for markitdown |
| `document-lens/app/services/document_processor.py` | Modify | Replace non-PDF parsers with markitdown |
| `document-lens/test-data/sample.docx` | Create | Test fixture for DOCX extraction |
| `document-lens/tests/test_files.py` | Modify | Add DOCX smoke test |
| `extracta/pyproject.toml` | Modify | Swap all document deps for markitdown |
| `extracta/extracta/lenses/document_lens/document_lens.py` | Modify | Replace all parsers with markitdown |
| `extracta/tests/test_document_lens.py` | Create | New tests for DocumentLens |

---

## Task 1: Create DOCX test fixture while python-docx is still installed

**Files:**
- Create: `document-lens/test-data/sample.docx`

> We create this now, before removing python-docx, so it lives in the repo as a committed binary.

- [ ] **Step 1: Generate the sample DOCX**

```bash
cd /Users/michael/Projects/lens/document-lens
python3 -c "
from docx import Document
doc = Document()
doc.add_heading('Sample Test Document', 0)
doc.add_paragraph('This document is used for automated testing of the document extraction pipeline.')
doc.add_paragraph('It contains several sentences to verify that text extraction is working correctly.')
table = doc.add_table(rows=2, cols=2)
table.cell(0, 0).text = 'Column A'
table.cell(0, 1).text = 'Column B'
table.cell(1, 0).text = 'Value 1'
table.cell(1, 1).text = 'Value 2'
doc.save('test-data/sample.docx')
print('Created test-data/sample.docx')
"
```

Expected: `Created test-data/sample.docx`

- [ ] **Step 2: Verify file exists**

```bash
ls -lh /Users/michael/Projects/lens/document-lens/test-data/sample.docx
```

Expected: file listed with non-zero size

- [ ] **Step 3: Commit the test fixture**

```bash
cd /Users/michael/Projects/lens/document-lens
git add test-data/sample.docx
git commit -m "test: add sample.docx fixture for DOCX extraction tests"
```

---

## Task 2: Write failing DOCX upload test (document-lens)

**Files:**
- Modify: `document-lens/tests/test_files.py`

- [ ] **Step 1: Add the DOCX upload test class**

Append this to the end of `document-lens/tests/test_files.py`:

```python


class TestDocxFileUpload:
    """Smoke tests for DOCX file upload and text extraction."""

    @pytest.mark.docx
    def test_upload_docx_returns_200(self, client: TestClient, sample_docx_paths: list[Path]):
        """Uploading a DOCX should return 200 OK."""
        if not sample_docx_paths:
            pytest.skip("No DOCX files in test-data directory")

        docx_path = sample_docx_paths[0]
        with open(docx_path, "rb") as f:
            response = client.post(
                "/files",
                files={"files": (docx_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )

        assert response.status_code == 200

    @pytest.mark.docx
    def test_upload_docx_with_extracted_text(self, client: TestClient, sample_docx_paths: list[Path]):
        """DOCX upload with include_extracted_text should return non-empty text."""
        if not sample_docx_paths:
            pytest.skip("No DOCX files in test-data directory")

        docx_path = sample_docx_paths[0]
        with open(docx_path, "rb") as f:
            response = client.post(
                "/files",
                files={"files": (docx_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"include_extracted_text": "true"},
            )

        assert response.status_code == 200
        data = response.json()
        file_result = data["results"]["individual_files"][0]

        assert "extracted_text" in file_result
        extracted = file_result["extracted_text"]
        assert "full_text" in extracted
        assert len(extracted["full_text"]) > 0
        assert extracted["total_pages"] == 1
        assert len(extracted["pages"]) == 1
        assert extracted["pages"][0]["page_number"] == 1
```

- [ ] **Step 2: Run the new test to confirm it currently passes (python-docx still installed)**

```bash
cd /Users/michael/Projects/lens/document-lens
uv run pytest tests/test_files.py::TestDocxFileUpload -v -m docx
```

Expected: PASS (python-docx still installed). We're confirming the test is valid before the swap.

- [ ] **Step 3: Commit the test**

```bash
cd /Users/michael/Projects/lens/document-lens
git add tests/test_files.py
git commit -m "test: add DOCX upload smoke tests"
```

---

## Task 3: Swap document-lens dependencies

**Files:**
- Modify: `document-lens/pyproject.toml`

- [ ] **Step 1: Update pyproject.toml**

In `document-lens/pyproject.toml`, find the `dependencies` list and make these changes:

Remove these lines:
```toml
    "python-docx>=1.1.0",
```

Add this line (after `"pdfplumber>=0.10.3",`):
```toml
    "markitdown[docx,pptx,xlsx]>=0.1.0",
```

Also remove from dependencies if present (check first with `grep "python-pptx" pyproject.toml`):
```bash
grep "python-pptx\|python-docx" /Users/michael/Projects/lens/document-lens/pyproject.toml
```

- [ ] **Step 2: Sync dependencies**

```bash
cd /Users/michael/Projects/lens/document-lens
uv sync
```

Expected: uv resolves and installs markitdown with docx/pptx/xlsx extras; python-docx removed.

- [ ] **Step 3: Verify markitdown installed, python-docx gone**

```bash
cd /Users/michael/Projects/lens/document-lens
uv run python3 -c "import markitdown; print('markitdown ok')"
uv run python3 -c "import docx" 2>&1 | head -1
```

Expected:
```
markitdown ok
ModuleNotFoundError: No module named 'docx'
```

- [ ] **Step 4: Run DOCX test to confirm it now fails**

```bash
cd /Users/michael/Projects/lens/document-lens
uv run pytest tests/test_files.py::TestDocxFileUpload -v -m docx 2>&1 | tail -20
```

Expected: FAIL — either `ImportError: No module named 'docx'` or 422 response code, confirming the old code is broken.

---

## Task 4: Refactor document_processor.py

**Files:**
- Modify: `document-lens/app/services/document_processor.py`

Replace the entire file with the following. Key changes:
- Remove all `try/except ImportError` blocks for docx/pptx
- Add `markitdown` import and module-level instance
- Add `_extract_with_markitdown()` that writes to a temp file and calls markitdown
- Simplify `extract_text` and `extract_text_with_pages` dispatch
- Simplify `extract_metadata` (remove docx/pptx metadata helpers)
- Keep PDF path (pdfplumber + pypdf) completely unchanged

- [ ] **Step 1: Replace the file**

```python
"""
Document processing service for text extraction from various file formats
"""

import io
import re
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from markitdown import MarkItDown

try:
    import pypdf
    from pypdf import PdfReader
except ImportError:
    pypdf = None  # type: ignore[assignment]
    PdfReader = None  # type: ignore[misc,assignment]

try:
    from pdfplumber.pdf import PDF as PDFPlumberPDF  # noqa: N811
except ImportError:
    PDFPlumberPDF = None  # type: ignore[assignment, misc]

# MIME types handled by markitdown (all non-PDF formats)
_MARKITDOWN_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
}

_markitdown = MarkItDown()


class DocumentProcessor:
    """Handles text extraction from various document formats"""

    def __init__(self) -> None:
        self.pdf_available = PdfReader is not None

    async def extract_text(self, content: bytes, content_type: str, filename: str) -> str:
        """
        Extract text from document based on content type.

        Args:
            content: Raw file content as bytes
            content_type: MIME type of the file
            filename: Name of the file (for error reporting)

        Returns:
            Extracted text as string
        """
        try:
            if content_type == "application/pdf":
                return await self._extract_from_pdf(content, filename)
            elif content_type in _MARKITDOWN_MIME_TYPES:
                return await self._extract_with_markitdown(content, filename)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Failed to extract text from {filename}: {e!s}"
            ) from e

    async def extract_text_with_pages(
        self, content: bytes, content_type: str, filename: str
    ) -> dict[str, Any]:
        """
        Extract text from document with page-level granularity.

        PDFs return real per-page text. All other formats return a single page.

        Args:
            content: Raw file content as bytes
            content_type: MIME type of the file
            filename: Name of the file (for error reporting)

        Returns:
            Dictionary with full_text, pages list, and total_pages
        """
        try:
            if content_type == "application/pdf":
                return await self._extract_from_pdf_with_pages(content, filename)
            elif content_type in _MARKITDOWN_MIME_TYPES:
                text = await self._extract_with_markitdown(content, filename)
                return {
                    "full_text": text,
                    "pages": [{"page_number": 1, "text": text}],
                    "total_pages": 1,
                }
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Failed to extract text from {filename}: {e!s}"
            ) from e

    async def _extract_with_markitdown(self, content: bytes, filename: str) -> str:
        """Extract text from any non-PDF format using markitdown."""
        suffix = Path(filename).suffix or ".bin"
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            result = _markitdown.convert(tmp_path)
            text = result.text_content or ""
            if not text.strip():
                raise ValueError(f"No text could be extracted from {filename}")
            return text
        finally:
            if tmp_path and Path(tmp_path).exists():
                Path(tmp_path).unlink()

    async def _extract_from_pdf(self, content: bytes, filename: str) -> str:
        """Extract text from PDF file"""
        result = await self._extract_from_pdf_with_pages(content, filename)
        full_text: str = result["full_text"]
        return full_text

    async def _extract_from_pdf_with_pages(self, content: bytes, filename: str) -> dict[str, Any]:
        """Extract text from PDF file with real page-level granularity."""
        if not pypdf:
            raise ImportError("pypdf not available. Install with: pip install pypdf")

        pages: list[dict[str, Any]] = []

        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = pypdf.PdfReader(pdf_file)

            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                pages.append({"page_number": page_num, "text": text if text else ""})

            # Fall back to pdfplumber if pypdf extracted almost nothing
            total_text = "".join(p["text"] for p in pages)
            if len(total_text) < 100 and PDFPlumberPDF is not None:
                pdf_file.seek(0)
                with PDFPlumberPDF(pdf_file) as pdf:
                    pages = []
                    for page_num, page in enumerate(pdf.pages, start=1):  # type: ignore[assignment]
                        text = page.extract_text()
                        pages.append({"page_number": page_num, "text": text if text else ""})

        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e!s}") from e

        non_empty_texts = [p["text"] for p in pages if p["text"].strip()]
        if not non_empty_texts:
            raise ValueError("No text could be extracted from PDF")

        return {
            "full_text": "\n\n".join(non_empty_texts),
            "pages": pages,
            "total_pages": len(pages),
        }

    def validate_file_size(self, content: bytes, max_size: int) -> bool:
        """Validate file size"""
        return len(content) <= max_size

    async def extract_metadata(
        self, content: bytes, content_type: str, filename: str
    ) -> dict[str, Any]:
        """Extract metadata from document."""
        metadata: dict[str, Any] = {
            "filename": filename,
            "size": len(content),
            "content_type": content_type,
        }
        try:
            if content_type == "application/pdf":
                metadata.update(self._extract_pdf_metadata(content))
            elif content_type.startswith("text/"):
                text = content.decode("utf-8", errors="replace")
                metadata["lines"] = len(text.splitlines())
                metadata["characters"] = len(text)
        except Exception as e:
            metadata["extraction_error"] = str(e)
        return metadata

    def _extract_pdf_metadata(self, content: bytes) -> dict[str, Any]:
        """Extract metadata from PDF using pypdf."""
        metadata: dict[str, Any] = {}

        if self.pdf_available:
            try:
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)

                metadata["pages"] = len(reader.pages)

                if reader.metadata:
                    doc_info = reader.metadata
                    metadata["title"] = str(doc_info.get("/Title", "")).strip()
                    metadata["author"] = str(doc_info.get("/Author", "")).strip()
                    metadata["subject"] = str(doc_info.get("/Subject", "")).strip()
                    metadata["creator"] = str(doc_info.get("/Creator", "")).strip()
                    metadata["producer"] = str(doc_info.get("/Producer", "")).strip()

                    creation_date = doc_info.get("/CreationDate")
                    if creation_date:
                        metadata["creation_date"] = str(creation_date)

                    mod_date = doc_info.get("/ModDate")
                    if mod_date:
                        metadata["modification_date"] = str(mod_date)

            except Exception as e:
                metadata["pdf_metadata_error"] = str(e)

        return metadata

    def infer_metadata_from_content(self, text: str, filename: str | None = None) -> dict[str, Any]:
        """
        Infer metadata from document content using pattern matching.

        Designed for corporate annual reports and sustainability documents.
        """
        result: dict[str, Any] = {
            "probable_year": None,
            "probable_company": None,
            "probable_industry": None,
            "document_type": None,
            "confidence_scores": {
                "year": 0.0,
                "company": 0.0,
                "industry": 0.0,
                "document_type": 0.0,
            },
            "extraction_notes": [],
        }

        sample_text = text[:10000]
        full_text_lower = text.lower()

        result.update(self._infer_year(sample_text, filename))
        result.update(self._infer_company(sample_text, filename))
        result.update(self._infer_industry(full_text_lower))
        result.update(self._infer_document_type(full_text_lower, filename))

        return result

    def _infer_year(self, sample_text: str, filename: str | None) -> dict[str, Any]:
        """Extract probable year from document"""
        result: dict[str, Any] = {
            "probable_year": None,
            "confidence_scores": {"year": 0.0},
            "extraction_notes": [],
        }

        year_candidates: dict[int, float] = {}

        annual_report_pattern = r"(?:annual\s+report|sustainability\s+report|integrated\s+report)\s*(\d{4})|(\d{4})\s*(?:annual\s+report|sustainability\s+report|integrated\s+report)"
        for match in re.finditer(annual_report_pattern, sample_text, re.IGNORECASE):
            year_str = match.group(1) or match.group(2)
            year = int(year_str)
            if 1990 <= year <= 2030:
                year_candidates[year] = year_candidates.get(year, 0) + 0.9

        fy_pattern = r"(?:fiscal\s+year|fy)\s*(\d{4})"
        for match in re.finditer(fy_pattern, sample_text, re.IGNORECASE):
            year = int(match.group(1))
            if 1990 <= year <= 2030:
                year_candidates[year] = year_candidates.get(year, 0) + 0.85

        year_ended_pattern = r"(?:for\s+the\s+)?year\s+ended?\s+\w+\s+\d{1,2},?\s*(\d{4})"
        for match in re.finditer(year_ended_pattern, sample_text, re.IGNORECASE):
            year = int(match.group(1))
            if 1990 <= year <= 2030:
                year_candidates[year] = year_candidates.get(year, 0) + 0.8

        if filename:
            filename_year_match = re.search(r"(20\d{2})", filename)
            if filename_year_match:
                year = int(filename_year_match.group(1))
                if 1990 <= year <= 2030:
                    year_candidates[year] = year_candidates.get(year, 0) + 0.7
                    result["extraction_notes"].append(f"Year {year} found in filename")

        copyright_pattern = r"(?:©|copyright)\s*(\d{4})"
        for match in re.finditer(copyright_pattern, sample_text, re.IGNORECASE):
            year = int(match.group(1))
            if 1990 <= year <= 2030:
                year_candidates[year] = year_candidates.get(year, 0) + 0.3

        if year_candidates:
            best_year = max(year_candidates, key=lambda y: year_candidates[y])
            result["probable_year"] = best_year
            result["confidence_scores"]["year"] = min(year_candidates[best_year], 1.0)

        return result

    def _infer_company(self, sample_text: str, filename: str | None) -> dict[str, Any]:
        """Extract probable company name from document"""
        result: dict[str, Any] = {
            "probable_company": None,
            "confidence_scores": {"company": 0.0},
            "extraction_notes": [],
        }

        company_candidates: dict[str, float] = {}

        corp_patterns = [
            r"([A-Z][A-Za-z\s&]+(?:Corporation|Corp\.?|Inc\.?|Ltd\.?|Limited|PLC|plc|Group|Holdings|Company|Co\.?))\s+(?:Annual|Sustainability|Integrated)\s+Report",
            r"(?:Annual|Sustainability|Integrated)\s+Report\s+of\s+([A-Z][A-Za-z\s&]+(?:Corporation|Corp\.?|Inc\.?|Ltd\.?|Limited|PLC|plc|Group|Holdings|Company|Co\.?))",
        ]
        for pattern in corp_patterns:
            for match in re.finditer(pattern, sample_text):
                company = match.group(1).strip()
                if 3 <= len(company) <= 100:
                    company_candidates[company] = company_candidates.get(company, 0) + 0.85

        about_pattern = r"About\s+([A-Z][A-Za-z\s&]+(?:Corporation|Corp\.?|Inc\.?|Ltd\.?|Limited|PLC|plc|Group|Holdings)?)"
        for match in re.finditer(about_pattern, sample_text):
            company = match.group(1).strip()
            if 3 <= len(company) <= 100 and company.lower() not in ["this", "our", "the"]:
                company_candidates[company] = company_candidates.get(company, 0) + 0.6

        if filename:
            clean_name = re.sub(r"\.\w+$", "", filename)
            clean_name = re.sub(r"[-_]?(20\d{2})[-_]?", " ", clean_name)
            clean_name = re.sub(
                r"[-_]?(annual|sustainability|report|integrated)[-_]?",
                " ",
                clean_name,
                flags=re.IGNORECASE,
            )
            clean_name = clean_name.strip()
            if len(clean_name) >= 3:
                company_candidates[clean_name] = company_candidates.get(clean_name, 0) + 0.5
                result["extraction_notes"].append(f"Company hint from filename: {clean_name}")

        if company_candidates:
            best_company = max(company_candidates, key=lambda c: company_candidates[c])
            result["probable_company"] = best_company
            result["confidence_scores"]["company"] = min(company_candidates[best_company], 1.0)

        return result

    def _infer_industry(self, full_text_lower: str) -> dict[str, Any]:
        """Detect probable industry from document content"""
        result: dict[str, Any] = {
            "probable_industry": None,
            "confidence_scores": {"industry": 0.0},
            "extraction_notes": [],
        }

        industry_keywords: dict[str, list[tuple[str, float]]] = {
            "Energy": [
                ("oil and gas", 0.9), ("petroleum", 0.8), ("natural gas", 0.7),
                ("drilling", 0.5), ("refinery", 0.7), ("upstream", 0.4),
                ("downstream", 0.4), ("barrel", 0.3), ("crude oil", 0.8),
                ("lng", 0.6), ("renewable energy", 0.7), ("solar power", 0.7),
                ("wind power", 0.7), ("hydroelectric", 0.7),
            ],
            "Financial Services": [
                ("banking", 0.8), ("investment management", 0.8), ("asset management", 0.7),
                ("wealth management", 0.7), ("insurance", 0.6), ("underwriting", 0.6),
                ("mortgage", 0.5), ("deposits", 0.4), ("loan portfolio", 0.7),
                ("credit risk", 0.6), ("capital adequacy", 0.7),
            ],
            "Technology": [
                ("software", 0.6), ("cloud computing", 0.8), ("artificial intelligence", 0.7),
                ("machine learning", 0.6), ("saas", 0.8), ("data center", 0.6),
                ("semiconductor", 0.8), ("cybersecurity", 0.7), ("digital transformation", 0.5),
            ],
            "Healthcare": [
                ("pharmaceutical", 0.9), ("clinical trial", 0.9), ("drug development", 0.8),
                ("patient", 0.4), ("hospital", 0.6), ("medical device", 0.8),
                ("fda approval", 0.9), ("therapeutic", 0.7), ("biotech", 0.8),
            ],
            "Consumer Goods": [
                ("retail", 0.6), ("consumer products", 0.8), ("brand portfolio", 0.7),
                ("fmcg", 0.9), ("packaged goods", 0.8), ("e-commerce", 0.5),
                ("store locations", 0.6),
            ],
            "Manufacturing": [
                ("manufacturing", 0.7), ("production facility", 0.7), ("supply chain", 0.5),
                ("factory", 0.6), ("industrial", 0.5), ("machinery", 0.6),
                ("assembly", 0.5), ("automotive", 0.7),
            ],
            "Utilities": [
                ("electric utility", 0.9), ("power generation", 0.8), ("transmission", 0.5),
                ("distribution network", 0.6), ("megawatt", 0.7), ("grid", 0.5),
                ("ratepayer", 0.8),
            ],
            "Mining & Metals": [
                ("mining", 0.8), ("ore", 0.7), ("extraction", 0.5), ("mineral", 0.6),
                ("gold", 0.5), ("copper", 0.5), ("iron ore", 0.8), ("smelting", 0.8),
            ],
            "Real Estate": [
                ("real estate", 0.9), ("property", 0.5), ("reit", 0.9), ("tenant", 0.6),
                ("occupancy rate", 0.8), ("square feet", 0.5), ("commercial property", 0.8),
            ],
            "Transportation": [
                ("airline", 0.9), ("aviation", 0.8), ("shipping", 0.7), ("logistics", 0.6),
                ("freight", 0.7), ("fleet", 0.5), ("passenger", 0.5), ("cargo", 0.6),
            ],
        }

        industry_scores: dict[str, float] = {}
        for industry, keywords in industry_keywords.items():
            score = 0.0
            for keyword, weight in keywords:
                count = full_text_lower.count(keyword)
                if count > 0:
                    score += weight * min(count, 10) / 10
            if score > 0:
                industry_scores[industry] = score

        if industry_scores:
            best_industry = max(industry_scores, key=lambda i: industry_scores[i])
            max_score = industry_scores[best_industry]
            confidence = min(max_score / 3.0, 1.0)
            if confidence >= 0.2:
                result["probable_industry"] = best_industry
                result["confidence_scores"]["industry"] = confidence

        return result

    def _infer_document_type(self, full_text_lower: str, filename: str | None) -> dict[str, Any]:
        """Detect document type from content"""
        result: dict[str, Any] = {
            "document_type": None,
            "confidence_scores": {"document_type": 0.0},
            "extraction_notes": [],
        }

        doc_type_patterns: dict[str, list[tuple[str, float]]] = {
            "Annual Report": [
                ("annual report", 0.9), ("form 10-k", 0.95), ("10-k", 0.8),
                ("fiscal year", 0.5), ("shareholders", 0.3), ("board of directors", 0.4),
            ],
            "Sustainability Report": [
                ("sustainability report", 0.95), ("esg report", 0.9),
                ("corporate responsibility", 0.7), ("environmental, social", 0.8),
                ("carbon footprint", 0.5), ("sustainable development goals", 0.7),
                ("sdg", 0.4), ("gri standards", 0.8), ("tcfd", 0.6),
            ],
            "Integrated Report": [
                ("integrated report", 0.95), ("integrated annual report", 0.95),
                ("value creation", 0.4), ("six capitals", 0.8), ("iirc", 0.9),
            ],
            "CSR Report": [
                ("csr report", 0.95), ("corporate social responsibility", 0.9),
                ("community investment", 0.5), ("social impact", 0.5),
            ],
            "Climate Report": [
                ("climate report", 0.95), ("climate-related", 0.6), ("net zero", 0.5),
                ("carbon neutral", 0.6), ("greenhouse gas", 0.5),
                ("scope 1", 0.6), ("scope 2", 0.6), ("scope 3", 0.6),
            ],
        }

        doc_type_scores: dict[str, float] = {}
        for doc_type, patterns in doc_type_patterns.items():
            score = sum(weight for pattern, weight in patterns if pattern in full_text_lower)
            if score > 0:
                doc_type_scores[doc_type] = score

        if filename:
            filename_lower = filename.lower()
            for doc_type in doc_type_patterns:
                if doc_type.lower().replace(" ", "") in filename_lower.replace(" ", "").replace("-", "").replace("_", ""):
                    doc_type_scores[doc_type] = doc_type_scores.get(doc_type, 0) + 0.5
                    result["extraction_notes"].append("Document type hint from filename")

        if doc_type_scores:
            best_type = max(doc_type_scores, key=lambda t: doc_type_scores[t])
            confidence = min(doc_type_scores[best_type] / 2.0, 1.0)
            if confidence >= 0.3:
                result["document_type"] = best_type
                result["confidence_scores"]["document_type"] = confidence

        return result
```

- [ ] **Step 2: Run the DOCX test — should now pass**

```bash
cd /Users/michael/Projects/lens/document-lens
uv run pytest tests/test_files.py::TestDocxFileUpload -v -m docx
```

Expected: PASS

- [ ] **Step 3: Run the full test suite**

```bash
cd /Users/michael/Projects/lens/document-lens
uv run pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: All previously passing tests still pass. No regressions.

- [ ] **Step 4: Commit**

```bash
cd /Users/michael/Projects/lens/document-lens
git add pyproject.toml uv.lock app/services/document_processor.py
git commit -m "refactor: replace DOCX/text parsers with markitdown in document-lens

Removes python-docx. PDF path (pdfplumber + pypdf) unchanged to preserve
per-page extraction for the desktop research viewer."
```

---

## Task 5: Write failing DocumentLens tests for extracta

**Files:**
- Create: `extracta/tests/test_document_lens.py`

- [ ] **Step 1: Write the test file**

Create `extracta/tests/test_document_lens.py`:

```python
"""Tests for DocumentLens — document text extraction via markitdown."""

import tempfile
from pathlib import Path

import pytest

from extracta.lenses.document_lens import DocumentLens


@pytest.fixture
def lens():
    return DocumentLens()


@pytest.fixture
def sample_txt(tmp_path: Path) -> Path:
    """A minimal plain-text file."""
    p = tmp_path / "sample.txt"
    p.write_text(
        "This is a sample document.\n"
        "It has multiple lines of text.\n"
        "Used to verify plain-text extraction works correctly.",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def sample_pdf() -> Path | None:
    """Reuse the PDF from document-lens test-data if available."""
    candidate = Path(__file__).parents[2] / "document-lens" / "test-data"
    pdfs = list(candidate.glob("*.pdf")) if candidate.exists() else []
    return pdfs[0] if pdfs else None


class TestDocumentLensExtract:
    def test_extract_txt_returns_success(self, lens: DocumentLens, sample_txt: Path):
        result = lens.extract(sample_txt)
        assert result["success"] is True
        assert "raw_content" in result["data"]
        assert len(result["data"]["raw_content"]) > 0

    def test_extract_txt_contains_text(self, lens: DocumentLens, sample_txt: Path):
        result = lens.extract(sample_txt)
        assert "sample document" in result["data"]["raw_content"].lower()

    def test_extract_txt_has_metadata(self, lens: DocumentLens, sample_txt: Path):
        result = lens.extract(sample_txt)
        data = result["data"]
        assert "file_path" in data
        assert "file_size" in data
        assert data["file_size"] > 0

    def test_extract_unsupported_type_returns_failure(self, lens: DocumentLens, tmp_path: Path):
        p = tmp_path / "file.xyz"
        p.write_bytes(b"binary content")
        result = lens.extract(p)
        assert result["success"] is False
        assert "error" in result

    def test_extract_string_path_accepted(self, lens: DocumentLens, sample_txt: Path):
        result = lens.extract(str(sample_txt))
        assert result["success"] is True

    def test_extract_pdf(self, lens: DocumentLens, sample_pdf: Path | None):
        if sample_pdf is None:
            pytest.skip("No PDF available in document-lens test-data")
        result = lens.extract(sample_pdf)
        assert result["success"] is True
        assert len(result["data"]["raw_content"]) > 0
```

- [ ] **Step 2: Run the tests to verify they currently pass with the old code**

```bash
cd /Users/michael/Projects/lens/extracta
python3 -m pytest tests/test_document_lens.py -v 2>&1 | tail -20
```

Expected: PASS (PyPDF2/python-docx still installed). Confirms tests are valid.

- [ ] **Step 3: Commit the tests**

```bash
cd /Users/michael/Projects/lens/extracta
git add tests/test_document_lens.py
git commit -m "test: add DocumentLens extraction tests"
```

---

## Task 6: Swap extracta dependencies

**Files:**
- Modify: `extracta/pyproject.toml`

- [ ] **Step 1: Update pyproject.toml optional dependencies**

In `extracta/pyproject.toml`, replace the `[project.optional-dependencies]` section entries for `documents` and `presentations`:

Old:
```toml
documents = ["PyPDF2>=3.0.0", "pdfplumber>=0.10.0", "python-docx>=1.1.0"]
presentations = ["python-pptx>=0.6.0", "PyMuPDF>=1.23.0"]
```

New:
```toml
documents = ["markitdown[docx,pptx,xlsx,pdf]>=0.1.0"]
presentations = []  # Future: PyMuPDF for image extraction (see design doc)
```

Also update the `enhanced` group which references `documents`:
```toml
enhanced = ["extracta[text,documents]"]
```

And update `all` — remove `presentations` from the list if it's there:
```toml
all = ["extracta[audio,video,text,image,code,api,documents,conversation,openai,claude,openrouter]"]
```

- [ ] **Step 2: Install with documents extras**

```bash
cd /Users/michael/Projects/lens/extracta
pip install -e ".[documents]"
```

Expected: markitdown and its docx/pptx/xlsx/pdf deps installed; PyPDF2/python-docx not present.

- [ ] **Step 3: Verify markitdown installed, old deps gone**

```bash
python3 -c "from markitdown import MarkItDown; print('markitdown ok')"
python3 -c "import PyPDF2" 2>&1 | head -1
python3 -c "import docx" 2>&1 | head -1
```

Expected:
```
markitdown ok
ModuleNotFoundError: No module named 'PyPDF2'
ModuleNotFoundError: No module named 'docx'
```

- [ ] **Step 4: Run DocumentLens tests to confirm they fail**

```bash
cd /Users/michael/Projects/lens/extracta
python3 -m pytest tests/test_document_lens.py -v 2>&1 | tail -20
```

Expected: Tests fail with import errors or extraction failures.

---

## Task 7: Refactor extracta DocumentLens

**Files:**
- Modify: `extracta/extracta/lenses/document_lens/document_lens.py`

- [ ] **Step 1: Replace the file**

```python
from pathlib import Path
from typing import Any

from markitdown import MarkItDown

from ..base_lens import BaseLens

_markitdown = MarkItDown()


class DocumentLens(BaseLens):
    """Extracts text content from document files via markitdown.

    Supports: PDF, DOCX, PPTX, XLSX, XLS, CSV, TSV, TXT, MD, RST,
              JSON, HTML, EPUB, IPYNB, XML and any format markitdown handles.

    Note on images: markitdown extracts text only. Embedded image extraction
    (for document viewers) is a planned future feature requiring PyMuPDF for
    PDFs and python-pptx blob access for PPTX. See design doc for hook points.
    """

    SUPPORTED_EXTENSIONS = {
        # Plain text
        ".txt", ".md", ".rst",
        # Data
        ".json", ".csv", ".tsv",
        # Office documents
        ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
        # Web / notebook
        ".html", ".htm", ".epub", ".ipynb", ".xml",
    }

    def extract(self, file_path: Path | str) -> dict[str, Any]:
        """Extract text content from a document file.

        Args:
            file_path: Path to the document file (str or Path).

        Returns:
            dict with keys:
              success (bool)
              data (dict): content_type, raw_content, file_path, file_size
              error (str): present only on failure
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_path.suffix}",
                    "data": {},
                }

            result = _markitdown.convert(file_path)
            content = result.text_content or ""

            if not content.strip():
                return {
                    "success": False,
                    "error": "No text could be extracted from file",
                    "data": {},
                }

            return {
                "success": True,
                "data": {
                    "content_type": "text",
                    "raw_content": content,
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e), "data": {}}
```

- [ ] **Step 2: Run the DocumentLens tests**

```bash
cd /Users/michael/Projects/lens/extracta
python3 -m pytest tests/test_document_lens.py -v
```

Expected: All tests PASS.

- [ ] **Step 3: Run the full extracta test suite**

```bash
cd /Users/michael/Projects/lens/extracta
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: All tests pass. No regressions in citation, reference, rubric, text, or URL analyzers.

- [ ] **Step 4: Commit**

```bash
cd /Users/michael/Projects/lens/extracta
git add pyproject.toml extracta/lenses/document_lens/document_lens.py
git commit -m "refactor: replace all document parsers with markitdown in extracta

Removes PyPDF2, pdfplumber, python-docx, python-pptx, PyMuPDF.
Adds markitdown[docx,pptx,xlsx,pdf]. Expands supported formats to
include HTML, EPUB, IPYNB, XML at no extra cost."
```

---

## Completion Checklist

- [ ] `document-lens` DOCX test passes with markitdown
- [ ] `document-lens` full test suite green (PDF path unchanged)
- [ ] `extracta` DocumentLens tests all pass
- [ ] `extracta` full test suite green (no analyzer regressions)
- [ ] `python-docx` removed from both projects
- [ ] `PyPDF2` removed from extracta
- [ ] `markitdown` added to both projects
- [ ] Image extraction noted in `extracta/lenses/document_lens/document_lens.py` docstring
- [ ] Both projects committed

---

## Future: Image Extraction Hook

When implementing embedded image extraction (tracked in design doc), the entry points are:

**PDFs** — add `PyMuPDF` back to extracta's `[presentations]` optional group:
```python
import fitz  # PyMuPDF
doc = fitz.open(file_path)
for page in doc:
    for img in page.get_images():
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
```

**PPTX** — iterate shapes after markitdown conversion:
```python
from pptx import Presentation
prs = Presentation(file_path)
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            image_bytes = shape.image.blob
```

**DOCX** — mammoth (already a markitdown dep) can embed images as base64 in HTML output using `convert_to_html` instead of `extract_raw_text`.
