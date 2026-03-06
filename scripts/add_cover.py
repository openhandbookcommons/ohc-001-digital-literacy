#!/usr/bin/env python3
import os
from pathlib import Path

import yaml
from pypdf import PdfReader, PdfWriter

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def pagesize_from_name(name: str):
    name = (name or "").lower()
    if name in ("letter", "usletter"):
        return letter
    return A4


def find_rendered_pdfs() -> list[Path]:
    files_env = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").strip()
    if not files_env:
        return []
    paths = [Path(x.strip()) for x in files_env.splitlines()]
    return [p for p in paths if p.suffix.lower() == ".pdf"]


def register_fonts():
    font_dir = Path("fonts")

    regular = font_dir / "LibertinusSerif-Regular.ttf"
    bold = font_dir / "LibertinusSerif-Bold.ttf"

    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("MainFont", str(regular)))
        pdfmetrics.registerFont(TTFont("MainFont-Bold", str(bold)))
        return "MainFont", "MainFont-Bold"

    return "Helvetica", "Helvetica-Bold"


def make_cover_pdf(
    out_pdf: Path,
    pagesize,
    bg_image: Path,
    title,
    subtitle,
    author,
    logo,
    overlay_opacity,
    margin_mm,
    title_size,
    subtitle_size,
    author_size,
    url_text,
):

    page_w, page_h = pagesize
    c = canvas.Canvas(str(out_pdf), pagesize=pagesize)

    main_font, main_bold = register_fonts()

    # ---------- background ----------
    bg = ImageReader(str(bg_image))
    iw, ih = bg.getSize()

    scale = max(page_w / iw, page_h / ih)
    dw, dh = iw * scale, ih * scale

    x = (page_w - dw) / 2
    y = (page_h - dh) / 2

    c.drawImage(bg, x, y, width=dw, height=dh, mask="auto")

    # ---------- overlay ----------
    if overlay_opacity > 0:
        c.saveState()
        c.setFillColorRGB(0, 0, 0, alpha=overlay_opacity)
        c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
        c.restoreState()

    margin = margin_mm * mm

        # ---------- top text (fixed top frame so it never goes off-page) ----------
    title = (title or "").strip() or " "
    subtitle = (subtitle or "").strip() if subtitle else ""
    author_line = ""

    if author:
        if isinstance(author, list):
            author_line = ", ".join([str(a) for a in author if a])
        else:
            author_line = str(author).strip()

    block = f"<font name='{main_bold}' size='{title_size}' color='white'><b>{title}</b></font>"

    if subtitle:
        block += (
            f"<br/><br/><font name='{main_font}' size='{subtitle_size}' color='white'>{subtitle}</font>"
        )

    if author_line:
        block += (
            f"<br/><br/><font name='{main_font}' size='{author_size}' color='#DDDDDD'>{author_line}</font>"
        )

    style = ParagraphStyle(
        "cover_top",
        alignment=TA_CENTER,
        fontName=main_font,
        fontSize=float(subtitle_size),
        leading=max(float(subtitle_size) * 1.35, 14),
        textColor="white",
    )

    para = Paragraph(block, style)

    frame_w = page_w - (margin * 2)

    # Fixed top area: top ~45% of page (safe, never negative)
    top_area_h = page_h * 0.45
    top_area_y = page_h - margin - top_area_h

    top_frame = Frame(
        margin,
        top_area_y,
        frame_w,
        top_area_h,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        showBoundary=0,
    )

    top_frame.addFromList([para], c)

    # ---------- bottom row ----------
    bottom_y = margin * 0.8

    # logo left
    if logo and logo.exists():
        try:
            img = ImageReader(str(logo))
            lw, lh = img.getSize()

            target_h = 25 * mm
            target_w = (lw / lh) * target_h

            c.drawImage(
                img,
                margin,
                bottom_y,
                width=target_w,
                height=target_h,
                mask="auto",
            )
        except Exception as e:
            print("Logo draw failed:", e)

    # url right
    if url_text:
        c.setFillColorRGB(1, 1, 1, alpha=0.85)
        c.setFont(main_font, 16)
        c.drawRightString(page_w - margin, bottom_y + 3, url_text)

    c.showPage()
    c.save()


def prepend_cover(cover_pdf: Path, target_pdf: Path):
    """
    Prepend cover to target_pdf while preserving bookmarks/outlines and document metadata.
    Requires pypdf version that supports clone_document_from_reader().
    """
    cover_reader = PdfReader(str(cover_pdf))
    target_reader = PdfReader(str(target_pdf))

    writer = PdfWriter()

    # Clone the entire original PDF structure (includes outlines/bookmarks)
    try:
        writer.clone_document_from_reader(target_reader)
    except AttributeError as e:
        raise SystemExit(
            "Your pypdf version is too old (clone_document_from_reader not available).\n"
            "Upgrade with: pip install -U pypdf\n"
            "Or use qpdf-based prepend (recommended if available)."
        ) from e

    # Insert cover as first page
    writer.insert_page(cover_reader.pages[0], 0)

    tmp = target_pdf.with_suffix(".tmp.pdf")
    with tmp.open("wb") as f:
        writer.write(f)

    tmp.replace(target_pdf)

def main():

    root = Path.cwd()

    cfg = load_yaml(root / "_quarto.yml")

    book = cfg.get("book", {})
    title = book.get("title", "")
    subtitle = book.get("subtitle")
    author = book.get("author")

    cover_cfg = cfg.get("ohc", {}).get("cover", {})

    papersize = pagesize_from_name(cover_cfg.get("papersize", "A4"))

    bg = root / cover_cfg.get("image", "cover/cover-bg.jpg")

    logo = cover_cfg.get("logo")
    logo = root / logo if logo else None

    overlay = float(cover_cfg.get("overlay_opacity", 0.45))
    margin = float(cover_cfg.get("margin_mm", 18))

    title_size = float(cover_cfg.get("title_size", 34))
    subtitle_size = float(cover_cfg.get("subtitle_size", 15))
    author_size = float(cover_cfg.get("author_size", 16))

    url = cover_cfg.get("url_text")

    pdfs = find_rendered_pdfs()

    if not pdfs:
        out_dir = Path(cfg.get("project", {}).get("output-dir", "_book"))
        fallback = out_dir / "index.pdf"
        if fallback.exists():
            pdfs = [fallback]

    if not pdfs:
        raise SystemExit("No rendered PDF found.")

    for pdf in pdfs:

        pdf = pdf.resolve()
        cover = pdf.with_suffix(".cover.pdf")

        make_cover_pdf(
            cover,
            papersize,
            bg,
            title,
            subtitle,
            author,
            logo,
            overlay,
            margin,
            title_size,
            subtitle_size,
            author_size,
            url,
        )

        prepend_cover(cover, pdf)

        cover.unlink(missing_ok=True)

        print("Cover added:", pdf)


if __name__ == "__main__":
    main()