"""Unit tests for analyst.pdf_utils.extract_pdf_text."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, call, patch

import pytest

from analyst.pdf_utils import extract_pdf_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes(texts: list[str]) -> bytes:
    """Build a real, minimal in-memory PDF with one blank page per *texts* entry.

    Text content is injected via a raw content stream so that pypdf's
    ``extract_text()`` can retrieve it.  The encoding used is plain ASCII
    wrapped in a Type1 (Helvetica) font, which pypdf understands without any
    ToUnicode map.
    """
    from pypdf import PdfWriter
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
        RectangleObject,
    )

    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=612, height=792)

        # Build a minimal content stream that draws *text* with Helvetica 12pt.
        stream_bytes = (
            f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET\n".encode("latin-1")
        )
        stream_obj = DecodedStreamObject()
        stream_obj.set_data(stream_bytes)

        # Attach font resource so pypdf recognises the text operator.
        font_dict = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        resources = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_dict})}
        )
        page[NameObject("/Resources")] = resources
        page[NameObject("/Contents")] = stream_obj

    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests using mocks (fast, no real PDF needed)
# ---------------------------------------------------------------------------

class TestExtractPdfTextMocked:
    """Logic-level tests using a patched PdfReader."""

    def _patched_reader(self, page_texts: list[str | None]):
        """Return a mock PdfReader whose .pages yield the given texts."""
        pages = []
        for t in page_texts:
            p = MagicMock()
            p.extract_text.return_value = t
            pages.append(p)
        mock_reader = MagicMock()
        mock_reader.pages = pages
        return mock_reader

    # PdfReader is imported lazily *inside* extract_pdf_text, so we patch the
    # name at its source module ("pypdf.PdfReader") rather than on pdf_utils.
    _PATCH_TARGET = "pypdf.PdfReader"

    def test_single_page(self):
        reader = self._patched_reader(["Hello World"])
        with patch(self._PATCH_TARGET, return_value=reader):
            result = extract_pdf_text(b"fake")
        assert result == "Hello World"

    def test_multi_page_joined_with_newline(self):
        reader = self._patched_reader(["Page one.", "Page two.", "Page three."])
        with patch(self._PATCH_TARGET, return_value=reader):
            result = extract_pdf_text(b"fake")
        assert result == "Page one.\nPage two.\nPage three."

    def test_empty_pdf_returns_empty_string(self):
        reader = self._patched_reader([])
        with patch(self._PATCH_TARGET, return_value=reader):
            result = extract_pdf_text(b"fake")
        assert result == ""

    def test_none_extract_text_treated_as_empty(self):
        """Pages where extract_text() returns None should produce "" not "None"."""
        reader = self._patched_reader([None, "Real text", None])
        with patch(self._PATCH_TARGET, return_value=reader):
            result = extract_pdf_text(b"fake")
        assert result == "\nReal text\n"

    def test_page_exception_silently_swallowed(self):
        """An exception from a single page should not abort extraction."""
        pages = []
        for raw in ["Good page", None]:
            p = MagicMock()
            if raw is None:
                p.extract_text.side_effect = RuntimeError("corrupt page")
            else:
                p.extract_text.return_value = raw
            pages.append(p)
        mock_reader = MagicMock()
        mock_reader.pages = pages
        with patch(self._PATCH_TARGET, return_value=mock_reader):
            result = extract_pdf_text(b"fake")
        # corrupt page falls back to ""
        assert result == "Good page\n"

    def test_progress_callback_called_per_page(self):
        reader = self._patched_reader(["A", "B", "C"])
        calls_received: list[tuple[int, int]] = []

        def callback(idx: int, total: int) -> None:
            calls_received.append((idx, total))

        with patch(self._PATCH_TARGET, return_value=reader):
            extract_pdf_text(b"fake", progress_callback=callback)

        assert calls_received == [(0, 3), (1, 3), (2, 3)]

    def test_no_progress_callback_does_not_raise(self):
        reader = self._patched_reader(["text"])
        with patch(self._PATCH_TARGET, return_value=reader):
            # should complete without error when no callback is provided
            extract_pdf_text(b"fake", progress_callback=None)


# ---------------------------------------------------------------------------
# Tests using a real pypdf-generated fixture PDF
# ---------------------------------------------------------------------------

class TestExtractPdfTextRealFixture:
    """End-to-end tests that build actual PDF bytes via pypdf.PdfWriter."""

    def test_blank_page_returns_string(self):
        """A blank page should return a string (possibly empty), not raise."""
        pdf_bytes = _make_pdf_bytes([""])
        result = extract_pdf_text(pdf_bytes)
        assert isinstance(result, str)

    def test_single_page_text_content(self):
        """Text injected into the content stream should be extractable."""
        pdf_bytes = _make_pdf_bytes(["Hello PDF"])
        result = extract_pdf_text(pdf_bytes)
        assert "Hello" in result

    def test_multi_page_real_pdf(self):
        """Multi-page PDF should produce a non-empty result with the right structure."""
        pdf_bytes = _make_pdf_bytes(["First page", "Second page"])
        result = extract_pdf_text(pdf_bytes)
        # Both pages' text should appear in the output
        assert "First" in result
        assert "Second" in result

    def test_progress_callback_called_correct_number_of_times(self):
        pdf_bytes = _make_pdf_bytes(["A", "B", "C"])
        seen_totals: list[int] = []

        def cb(idx: int, total: int) -> None:
            seen_totals.append(total)

        extract_pdf_text(pdf_bytes, progress_callback=cb)
        assert len(seen_totals) == 3
        assert all(t == 3 for t in seen_totals)
