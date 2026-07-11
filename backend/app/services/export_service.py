"""PDF / Excel / CSV export service.

WeasyPrint and openpyxl are soft-imports — the rest of the app boots
without them. They're declared in requirements.txt as optional; install
explicitly to enable PDF/XLSX exports.

The service writes to ``settings.EXPORT_DIR`` and returns the absolute
path. Callers (report endpoints) typically stream the file back via
:class:`fastapi.responses.FileResponse`.
"""
from __future__ import annotations

import csv
import io
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

from app.config import settings

logger = logging.getLogger(__name__)


_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe_filename(stem: str, ext: str) -> Path:
    settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    cleaned = _FILENAME_SAFE.sub("_", stem).strip("_") or "export"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return settings.EXPORT_DIR / f"{cleaned}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"


# ─── CSV ──────────────────────────────────────────────────────────────────
def export_csv(
    rows: Sequence[dict],
    *,
    columns: Optional[Sequence[str]] = None,
    filename_stem: str = "export",
) -> Path:
    """Write a list of dict rows to a CSV file. Returns the path."""
    path = _safe_filename(filename_stem, "csv")
    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    fieldnames = list(columns) if columns else list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def export_csv_bytes(
    rows: Sequence[dict], *, columns: Optional[Sequence[str]] = None
) -> bytes:
    """Same as :func:`export_csv` but returns the bytes directly."""
    if not rows:
        return b""
    fieldnames = list(columns) if columns else list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


# ─── Excel ────────────────────────────────────────────────────────────────
def export_xlsx(
    rows: Sequence[dict],
    *,
    columns: Optional[Sequence[str]] = None,
    sheet_name: str = "Sheet1",
    filename_stem: str = "export",
) -> Path:
    """Write rows to an .xlsx file. Returns the path."""
    try:
        from openpyxl import Workbook  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "openpyxl is not installed. Add `openpyxl>=3.1.0` to requirements.txt."
        ) from exc

    path = _safe_filename(filename_stem, "xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31] or "Sheet1"

    if rows:
        fieldnames = list(columns) if columns else list(rows[0].keys())
        ws.append(fieldnames)
        for row in rows:
            ws.append([_xlsx_safe(row.get(col)) for col in fieldnames])
        # Reasonable autosize approximation
        for col_idx, name in enumerate(fieldnames, start=1):
            max_len = max(
                [len(str(name))] + [len(str(row.get(name, ""))) for row in rows]
            )
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = (
                min(max_len + 2, 60)
            )

    wb.save(path)
    return path


def _xlsx_safe(value: Any) -> Any:
    """openpyxl can serialize most types; coerce the rest to str."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool, datetime)):
        return value
    return str(value)


# ─── PDF ──────────────────────────────────────────────────────────────────
def export_pdf_from_html(
    html: str, *, filename_stem: str = "export", base_url: Optional[str] = None
) -> Path:
    """Render an HTML string to a PDF file. Returns the path.

    Use Jinja2 (already a project dep) to produce ``html`` from a
    template before calling this — keeps WeasyPrint focused on rendering.
    """
    try:
        from weasyprint import HTML  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "weasyprint is not installed. Add `weasyprint>=60.0` to requirements.txt."
        ) from exc

    path = _safe_filename(filename_stem, "pdf")
    HTML(string=html, base_url=base_url).write_pdf(str(path))
    return path


def export_pdf_table(
    title: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    filename_stem: str = "report",
) -> Path:
    """Convenience: render a simple titled table to PDF."""
    head_cells = "".join(f"<th>{_html_escape(c)}</th>" for c in columns)
    body_rows: List[str] = []
    for row in rows:
        cells = "".join(f"<td>{_html_escape(c)}</td>" for c in row)
        body_rows.append(f"<tr>{cells}</tr>")

    html = f"""\
<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 24px; color: #111; }}
  h1 {{ font-size: 18px; margin: 0 0 16px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
  th {{ background: #f6f7f9; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .meta {{ color: #666; font-size: 10px; margin-bottom: 12px; }}
</style>
</head><body>
<h1>{_html_escape(title)}</h1>
<div class="meta">Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}</div>
<table><thead><tr>{head_cells}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>
</body></html>"""
    return export_pdf_from_html(html, filename_stem=filename_stem)


def _html_escape(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
