"""Generate a downloadable analysis report in Markdown and PDF formats."""

from __future__ import annotations

import io
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional


def _heading(text: str, level: int = 1) -> str:
    return f"{'#' * level} {text}\n\n"


def _bullet(items: list, indent: int = 0) -> str:
    prefix = "  " * indent
    return "".join(f"{prefix}- {item}\n" for item in items)


def _hr() -> str:
    return "\n---\n\n"


def _table(headers: List[str], rows: List[List[str]]) -> str:
    """Build a simple Markdown table."""
    lines: list[str] = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines) + "\n\n"


# ─────────────────────────────────────────────────────────────────────────────
# Main report builder
# ─────────────────────────────────────────────────────────────────────────────

def generate_report_markdown(
    result: Dict[str, Any],
    essay_text: str = "",
    level: str = "",
    discipline: str = "",
    rubric: str = "",
    history: Optional[List[Dict]] = None,
) -> str:
    """Return the full analysis report as a Markdown string.

    Parameters
    ----------
    result : dict
        The dict returned by ``analyse_essay()`` stored in ``st.session_state["result"]``.
    essay_text : str
        The original essay (included as an appendix).
    level, discipline, rubric : str
        Context fields displayed in the report header.
    history : list[dict] | None
        Session history rows (Run #, Overall, Band …).
    """
    md: list[str] = []

    # ── Title & metadata ─────────────────────────────────────────────────────
    md.append(_heading("AI Essay Analyst — Analysis Report"))
    md.append(
        f"**Generated:** {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n"
    )
    if level or discipline or rubric:
        md.append(
            _table(
                ["Field", "Value"],
                [
                    ["Academic level", level or "—"],
                    ["Discipline", discipline or "—"],
                    ["Rubric profile", rubric or "—"],
                    ["Word count", str(len(essay_text.split())) if essay_text else "—"],
                ],
            )
        )

    md.append(_hr())

    sc = result.get("scores", {})
    band = result.get("band", "—")

    # ── 1. Scorecard ─────────────────────────────────────────────────────────
    md.append(_heading("Scorecard", 2))
    md.append(
        _table(
            ["Dimension", "Score (/100)"],
            [
                ["Overall", str(sc.get("overall", "—"))],
                ["Structure", str(sc.get("structure", "—"))],
                ["Argument Depth", str(sc.get("argument_depth", "—"))],
                ["Evidence Use", str(sc.get("evidence_use", "—"))],
                ["Coherence", str(sc.get("coherence", "—"))],
            ],
        )
    )
    md.append(f"**Grade band:** {band}\n\n")

    conf = result.get("confidence", 0)
    md.append(
        f"**Model confidence:** {int(float(conf) * 100)}%\n\n"
    )
    notes = result.get("confidence_notes", "")
    if notes:
        md.append(f"> {notes}\n\n")

    md.append(_hr())

    # ── 2. Strengths ─────────────────────────────────────────────────────────
    md.append(_heading("Strengths", 2))
    strengths = result.get("strengths", [])
    if strengths:
        for s in strengths:
            md.append(f"- **{s.get('dimension', '')}** — {s.get('point', '')}\n")
        md.append("\n")
    else:
        md.append("_No specific strengths identified._\n\n")

    # ── 3. Weaknesses ────────────────────────────────────────────────────────
    md.append(_heading("Weaknesses", 2))
    weaknesses = result.get("weaknesses", [])
    if weaknesses:
        for w in weaknesses:
            md.append(f"- **{w.get('dimension', '')}** — {w.get('point', '')}\n")
        md.append("\n")
    else:
        md.append("_No specific weaknesses identified._\n\n")

    md.append(_hr())

    # ── 4. Revision Roadmap ──────────────────────────────────────────────────
    md.append(_heading("Revision Roadmap", 2))
    roadmap = sorted(
        result.get("revision_roadmap", []),
        key=lambda x: x.get("priority", 99),
    )
    if roadmap:
        for item in roadmap:
            md.append(
                f"### #{item.get('priority', '?')} · "
                f"{item.get('dimension', '')} — {item.get('title', '')}\n\n"
            )
            md.append(f"- **Impact:** {item.get('impact', '—')}\n")
            md.append(f"- **Effort:** {item.get('effort', '—')}\n")
            md.append(f"- **Action:** {item.get('action', '—')}\n\n")
    else:
        md.append("_No revision actions suggested._\n\n")

    md.append(_hr())

    # ── 5. RAG Sources ───────────────────────────────────────────────────────
    md.append(_heading("RAG Sources", 2))
    sources = result.get("rag_sources", [])
    if sources:
        headers = list(sources[0].keys()) if sources else []
        rows = [list(str(v) for v in s.values()) for s in sources]
        md.append(_table(headers, rows))
    else:
        md.append("_No references retrieved._\n\n")

    # ── 6. Session History ───────────────────────────────────────────────────
    if history:
        md.append(_hr())
        md.append(_heading("Session History", 2))
        h_headers = list(history[0].keys())
        h_rows = [list(str(v) for v in h.values()) for h in history]
        md.append(_table(h_headers, h_rows))

    md.append(_hr())

    # ── Appendix: Essay Text ─────────────────────────────────────────────────
    if essay_text:
        md.append(_heading("Appendix — Submitted Essay", 2))
        # Wrap long lines for readability
        wrapped = "\n\n".join(
            textwrap.fill(para, width=100)
            for para in essay_text.split("\n")
            if para.strip()
        )
        md.append(f"```\n{wrapped}\n```\n\n")

    md.append(
        "_Report generated by EssayInsight · "
        "https://github.com/your-org/EssayInsight_\n"
    )

    return "".join(md)


def markdown_to_bytes(md_text: str) -> bytes:
    """Encode the Markdown report as UTF-8 bytes ready for download."""
    return md_text.encode("utf-8")


def generate_pdf_bytes(md_text: str) -> Optional[bytes]:
    """Convert Markdown report to PDF bytes using fpdf2.

    Returns None if ``fpdf2`` is not installed — the caller can fall back
    to Markdown download.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    def _latin1_safe(text: str) -> str:
        """Replace common Unicode chars with latin-1 safe equivalents."""
        replacements = {
            "\u2014": "--",   # em dash
            "\u2013": "-",    # en dash
            "\u2018": "'",    # left single quote
            "\u2019": "'",    # right single quote
            "\u201c": '"',    # left double quote
            "\u201d": '"',    # right double quote
            "\u2022": "-",    # bullet
            "\u2026": "...",  # ellipsis
            "\u00a0": " ",    # non-breaking space
            "\u2009": " ",    # thin space
        }
        for u_char, repl in replacements.items():
            text = text.replace(u_char, repl)
        # Final fallback: encode to latin-1, replacing anything else
        return text.encode("latin-1", errors="replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "AI Essay Analyst - Analysis Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Parse the Markdown line-by-line and render with basic formatting
    safe_md = _latin1_safe(md_text)
    for line in safe_md.split("\n"):
        stripped = line.strip()

        # Skip the title (already rendered) and raw HR lines
        if not stripped or stripped == "---":
            pdf.ln(3)
            continue

        # Headings
        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 6, _latin1_safe(stripped.lstrip("# ").strip()), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.multi_cell(0, 7, _latin1_safe(stripped.lstrip("# ").strip()), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
        elif stripped.startswith("# "):
            continue  # already printed title
        # Bold lines
        elif stripped.startswith("**") and stripped.endswith("**"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 5, _latin1_safe(stripped.strip("*").strip()), new_x="LMARGIN", new_y="NEXT")
        # Bullet points
        elif stripped.startswith("- "):
            pdf.set_font("Helvetica", "", 10)
            text = stripped[2:].replace("**", "").strip()
            text = _latin1_safe(text)
            pdf.multi_cell(0, 5, f"  -  {text}", new_x="LMARGIN", new_y="NEXT")
        # Blockquotes
        elif stripped.startswith("> "):
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 5, _latin1_safe(stripped[2:].strip()), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
        # Table rows — render as aligned text
        elif stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            # Skip separator rows like | --- | --- |
            if cells and all(c.replace("-", "") == "" for c in cells):
                continue
            pdf.set_font("Helvetica", "", 9)
            col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / max(len(cells), 1)
            for cell in cells:
                clean = _latin1_safe(cell.replace("**", "").strip())
                pdf.cell(col_w, 5, clean, border=1)
            pdf.ln()
        # Code blocks
        elif stripped.startswith("```"):
            continue
        # Regular text
        else:
            pdf.set_font("Helvetica", "", 10)
            clean = _latin1_safe(stripped.replace("**", "").replace("_", ""))
            pdf.multi_cell(0, 5, clean, new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
