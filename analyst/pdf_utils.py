"""PDF text-extraction utilities used by the Streamlit front-end."""

from __future__ import annotations

from io import BytesIO
from typing import Callable, Optional


def extract_pdf_text(
    data: bytes,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Extract plain text from *data* (raw PDF bytes).

    Parameters
    ----------
    data:
        Raw bytes of the PDF file.
    progress_callback:
        Optional callable that receives ``(page_index, total_pages)`` after
        each page is processed.  Useful for updating UI progress indicators.

    Returns
    -------
    str
        Concatenated page text joined by newlines, or an empty string when
        the PDF contains no pages or extraction fails for a page.

    Raises
    ------
    Exception
        Re-raises any exception raised by ``PdfReader`` itself (e.g. an
        invalid/encrypted PDF).  Per-page extraction failures are silently
        swallowed and produce an empty string for that page.
    """
    from pypdf import PdfReader  # late import so pypdf is truly optional

    reader = PdfReader(BytesIO(data))
    pages = reader.pages
    if not pages:
        return ""

    total = len(pages)
    extracted: list[str] = []
    for i, page in enumerate(pages):
        try:
            extracted.append(page.extract_text() or "")
        except Exception:
            extracted.append("")
        if progress_callback is not None:
            progress_callback(i, total)

    return "\n".join(extracted)
