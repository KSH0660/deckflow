from __future__ import annotations

import html as htmlmod
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Any

# Stores the last error message from a failed PDF attempt for diagnostics
PDF_ERROR_DETAIL: str | None = None


def _render_pdf_with_playwright(html: str, layout: str = "widescreen") -> bytes | None:
    """Render using headless Chromium via Playwright (executes JS and Tailwind CDN).

    Requires: `pip install playwright` and `playwright install chromium`.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            # Ensure viewport matches our intended page size for layout calculations
            if layout == "widescreen":
                page.set_viewport_size({"width": 1920, "height": 1080})
            elif layout == "a4-landscape":
                page.set_viewport_size({"width": 1280, "height": 900})
            # Use networkidle to wait for Tailwind CDN and fonts
            page.set_content(html, wait_until="networkidle")
            page.emulate_media(media="print")
            # Respect CSS @page size from the combined document
            pdf_bytes = page.pdf(
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()
            return pdf_bytes
    except Exception as e:
        global PDF_ERROR_DETAIL
        PDF_ERROR_DETAIL = f"Playwright failed: {e}"
        return None


def _extract_body_inner_html(html: str) -> str:
    """Extract only the inner HTML inside <body>...</body>.

    Falls back to the original string if <body> is not found.
    Keeps content as-is without sanitization (assumes trusted input from generator).
    """
    if not html:
        return ""
    body_open = re.search(r"<body[^>]*>", html, flags=re.IGNORECASE | re.DOTALL)
    body_close = re.search(r"</body>", html, flags=re.IGNORECASE | re.DOTALL)
    if body_open and body_close:
        start = body_open.end()
        end = body_close.start()
        return html[start:end]

    # Try removing top-level wrappers if present
    # Remove DOCTYPE and <html>/<head>...
    cleaned = re.sub(r"<!DOCTYPE[^>]*>", "", html, flags=re.IGNORECASE)
    cleaned = re.sub(r"<html[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</html>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<head[^>]*>.*?</head>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<body[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</body>", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def render_deck_to_html(
    deck: dict[str, Any],
    layout: str = "widescreen",
    embed: str = "inline",
) -> str:
    """Combine slide HTMLs into a single printable HTML document.

    - Includes Tailwind CDN once at the top (slides already rely on it).
    - Each slide becomes a <section class="slide"> with page-breaks for print/PDF.
    """
    title = deck.get("deck_title", "Presentation")
    slides = deck.get("slides", []) or []

    slide_sections: list[str] = []
    for s in slides:
        html = ((s or {}).get("content") or {}).get("html_content", "")
        if embed == "iframe":
            # Keep full document per slide inside its own browsing context
            srcdoc = htmlmod.escape(html, quote=True)
            section = (
                f"<section class=\"slide\"><iframe class=\"slide-frame\" srcdoc=\"{srcdoc}\" loading=\"lazy\"></iframe></section>"
            )
        else:
            inner = _extract_body_inner_html(html)
            section = f"<section class=\"slide\">{inner}</section>"
        slide_sections.append(section)

    created_at = deck.get("created_at")
    if isinstance(created_at, datetime):
        created_str = created_at.isoformat()
    else:
        created_str = str(created_at) if created_at else ""

    if layout == "widescreen":
        page_css = "@page { size: 1920px 1080px; margin: 0; }"
        slide_box_css = (
            ".slide { page-break-after: always; break-after: page; background: white;"
            " width: 1920px; height: 1080px; margin: 0; padding: 0; }"
        )
    elif layout == "a4-landscape":
        page_css = "@page { size: A4 landscape; margin: 10mm; }"
        slide_box_css = (
            ".slide { page-break-after: always; break-after: page; background: white;"
            " width: auto; min-height: 100vh; margin: 0 auto 16px auto; padding: 12px; }"
        )
    else:
        page_css = "@page { size: A4; margin: 12mm; }"
        slide_box_css = (
            ".slide { page-break-after: always; break-after: page; background: white;"
            " width: auto; min-height: 100vh; margin: 0 auto 16px auto; padding: 16px; }"
        )

    combined_html = f"""
<!DOCTYPE html>
<html lang=\"ko\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{title}</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <style>
      {page_css}
      html, body {{ background: #f8fafc; margin: 0; padding: 0; }}
      main {{ margin: 0; padding: 0; }}
      .deck-meta {{ font-size: 12px; color: #64748b; margin: 8px 16px; }}
      {slide_box_css}
      .slide-frame {{ width: 100%; height: 100%; border: 0; display: block; }}
      .slide:last-child {{ page-break-after: auto; break-after: auto; }}
      @media print {{ html, body, main {{ width: 100%; height: 100%; margin: 0; padding: 0; }} }}
    </style>
  </head>
  <body>
    <main>
      <div class=\"deck-meta\">Generated: {created_str}</div>
      {''.join(slide_sections)}
    </main>
  </body>
</html>
"""
    return combined_html


def _render_pdf_with_weasyprint(html: str) -> bytes | None:
    try:
        # Import inside to avoid hard dependency if not installed
        from weasyprint import HTML as _HTML  # type: ignore

        return _HTML(string=html).write_pdf()
    except Exception as e:
        global PDF_ERROR_DETAIL
        PDF_ERROR_DETAIL = f"WeasyPrint failed: {e}"
        return None


def _render_pdf_with_wkhtmltopdf(html: str) -> bytes | None:
    wk = shutil.which("wkhtmltopdf")
    if not wk:
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=True) as f_html, tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as f_pdf:
            f_html.write(html.encode("utf-8"))
            f_html.flush()
            subprocess.run([wk, f_html.name, f_pdf.name], check=True)
            f_pdf.seek(0)
            return f_pdf.read()
    except Exception as e:
        global PDF_ERROR_DETAIL
        PDF_ERROR_DETAIL = f"wkhtmltopdf failed: {e}"
        return None


def try_render_deck_pdf(html: str, layout: str = "widescreen") -> bytes | None:
    """Best-effort HTML->PDF conversion.

    Tries WeasyPrint, then wkhtmltopdf if available. Returns None if neither works.
    """
    # Reset previous error context
    global PDF_ERROR_DETAIL
    PDF_ERROR_DETAIL = None

    # Prefer Playwright for accurate styling (executes Tailwind CDN JS)
    pdf = _render_pdf_with_playwright(html, layout=layout)
    if pdf:
        return pdf

    # Fallbacks (no JS). May lose Tailwind styles.
    pdf = _render_pdf_with_weasyprint(html)
    if pdf:
        return pdf
    return _render_pdf_with_wkhtmltopdf(html)
