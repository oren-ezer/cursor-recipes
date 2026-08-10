"""PDF export helpers with Unicode and RTL (Hebrew) support."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from bidi.algorithm import get_display
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

DEFAULT_PDF_LANGUAGE = "en"
RTL_LANGUAGES = frozenset({"he"})

PDF_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "preparation_time": "Preparation Time",
        "cooking_time": "Cooking Time",
        "servings": "Servings",
        "difficulty": "Difficulty",
        "tags": "Tags",
        "ingredients": "Ingredients",
        "instructions": "Instructions",
        "minutes": "{count} minutes",
        "step": "Step {number}:",
        "difficulty_easy": "Easy",
        "difficulty_medium": "Medium",
        "difficulty_hard": "Hard",
        "difficulty_expert": "Expert",
    },
    "he": {
        "preparation_time": "זמן הכנה",
        "cooking_time": "זמן בישול",
        "servings": "מספר מנות",
        "difficulty": "רמת קושי",
        "tags": "תגיות",
        "ingredients": "רכיבים",
        "instructions": "הוראות הכנה",
        "minutes": "{count} דקות",
        "step": "שלב {number}:",
        "difficulty_easy": "קל",
        "difficulty_medium": "בינוני",
        "difficulty_hard": "קשה",
        "difficulty_expert": "מומחה",
    },
}

# Families that ship with the OS and cover both Latin and Hebrew, most
# preferred first. Liberation/Nimbus are the metric-compatible clones that
# stand in for Arial and Times New Roman on Linux hosts.
FONT_CANDIDATES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "Arial",
        (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
        ),
        (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
        ),
    ),
    (
        "LiberationSans",
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
        ),
    ),
    (
        "TimesNewRoman",
        (
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            "/Library/Fonts/Times New Roman.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
        ),
        (
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            "/Library/Fonts/Times New Roman Bold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf",
        ),
    ),
    (
        "DejaVuSans",
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/opt/homebrew/share/fonts/DejaVuSans.ttf",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/opt/homebrew/share/fonts/DejaVuSans-Bold.ttf",
        ),
    ),
)

HEBREW_ALEPH = 0x05D0
HEBREW_TAV = 0x05EA


@dataclass(frozen=True)
class PdfFonts:
    """Registered ReportLab font names used for a PDF export."""

    regular: str
    bold: str


_REGISTERED_FONTS: PdfFonts | None = None


def _bundled_fonts_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "fonts"


def _first_existing(paths: tuple[str, ...]) -> Path | None:
    for path in paths:
        candidate = Path(path)
        if candidate.is_file():
            return candidate
    return None


def _supports_hebrew(font_path: Path, font_name: str) -> bool:
    try:
        face = TTFont(font_name, str(font_path)).face
    except Exception:
        return False
    return all(
        codepoint in face.charToGlyph
        for codepoint in range(HEBREW_ALEPH, HEBREW_TAV + 1)
    )


def _bundled_family() -> tuple[str, Path, Path] | None:
    regular = _bundled_fonts_dir() / "DejaVuSans.ttf"
    bold = _bundled_fonts_dir() / "DejaVuSans-Bold.ttf"
    if regular.is_file() and bold.is_file():
        return "DejaVuSans", regular, bold
    return None


def resolve_pdf_fonts() -> tuple[str, Path, Path]:
    """Pick the first installed family that covers Latin and Hebrew."""
    for family, regular_paths, bold_paths in FONT_CANDIDATES:
        regular = _first_existing(regular_paths)
        if not regular or not _supports_hebrew(regular, f"{family}-probe"):
            continue
        bold = _first_existing(bold_paths) or regular
        return family, regular, bold

    bundled = _bundled_family()
    if bundled:
        logger.info("No system Hebrew-capable font found; using bundled fallback.")
        return bundled

    raise FileNotFoundError(
        "No PDF font with Hebrew support found. Install Arial, Liberation Sans, "
        "Times New Roman, or DejaVu Sans, or place DejaVuSans.ttf and "
        f"DejaVuSans-Bold.ttf under {_bundled_fonts_dir()}."
    )


def register_pdf_fonts() -> PdfFonts:
    """Register a Unicode font family for PDF output and return its names."""
    global _REGISTERED_FONTS
    if _REGISTERED_FONTS:
        return _REGISTERED_FONTS

    family, regular_path, bold_path = resolve_pdf_fonts()
    bold_name = f"{family}-Bold"

    pdfmetrics.registerFont(TTFont(family, str(regular_path)))
    pdfmetrics.registerFont(TTFont(bold_name, str(bold_path)))
    pdfmetrics.registerFontFamily(family, normal=family, bold=bold_name)

    logger.info("Registered PDF font family %s from %s", family, regular_path)
    _REGISTERED_FONTS = PdfFonts(regular=family, bold=bold_name)
    return _REGISTERED_FONTS


def contains_hebrew(text: str | None) -> bool:
    if not text:
        return False
    return any("\u0590" <= char <= "\u05FF" for char in text)


def recipe_uses_rtl(recipe, tags: list | None = None) -> bool:
    """Return True when recipe content includes Hebrew text."""
    texts: list[str | None] = [
        recipe.title,
        recipe.description,
        recipe.difficulty_level,
    ]
    for ingredient in recipe.ingredients or []:
        texts.append(ingredient.get("name"))
        texts.append(ingredient.get("amount"))
    texts.extend(recipe.instructions or [])
    for tag in tags or []:
        name = tag.get("name") if isinstance(tag, dict) else getattr(tag, "name", None)
        texts.append(name)
    return any(contains_hebrew(text) for text in texts if text)


def normalize_pdf_language(language: str | None) -> str | None:
    """Map an incoming language tag (``he``, ``he-IL``) to a supported key."""
    if not language:
        return None
    key = language.strip().lower().replace("_", "-").split("-")[0]
    return key if key in PDF_TRANSLATIONS else None


def resolve_pdf_language(requested: str | None, recipe, tags: list | None = None) -> str:
    """Pick the export language: an explicit request wins over content sniffing."""
    normalized = normalize_pdf_language(requested)
    if normalized:
        return normalized
    return "he" if recipe_uses_rtl(recipe, tags) else DEFAULT_PDF_LANGUAGE


def is_rtl_language(language: str) -> bool:
    return language in RTL_LANGUAGES


def translate_pdf_text(language: str, key: str, **values) -> str:
    """Look up a PDF label, falling back to English for unknown languages."""
    catalog = PDF_TRANSLATIONS.get(language, PDF_TRANSLATIONS[DEFAULT_PDF_LANGUAGE])
    template = catalog.get(key) or PDF_TRANSLATIONS[DEFAULT_PDF_LANGUAGE].get(key, key)
    return template.format(**values) if values else template


def translate_difficulty(language: str, difficulty: str | None) -> str:
    """Translate a stored difficulty level, leaving unknown values untouched."""
    if not difficulty:
        return ""
    key = f"difficulty_{difficulty.strip().lower()}"
    catalog = PDF_TRANSLATIONS.get(language, PDF_TRANSLATIONS[DEFAULT_PDF_LANGUAGE])
    return catalog.get(key, difficulty)


def wrap_text_to_width(
    text: str,
    *,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    """Greedily split text into lines that fit within max_width."""
    words = text.split()
    if not words or max_width <= 0:
        return [text]

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}" if current else word
        if current and pdfmetrics.stringWidth(candidate, font_name, font_size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def prepare_pdf_text(
    text: str | None,
    *,
    font_name: str | None = None,
    font_size: float | None = None,
    max_width: float | None = None,
) -> str:
    """Escape text for ReportLab and apply bidi reordering for Hebrew.

    Reordering keys off the text itself rather than the document direction, so
    Hebrew stays readable even in an otherwise left-to-right export. ReportLab
    has no bidi support of its own, and reordering is only correct per rendered
    line, which is why line breaking happens here instead of being left to
    ReportLab: pass the font metrics and the available width to get wrapped
    output.
    """
    if not text:
        return ""
    value = str(text)
    if not contains_hebrew(value):
        return escape(value)

    if font_name and font_size and max_width:
        lines = wrap_text_to_width(
            value,
            font_name=font_name,
            font_size=font_size,
            max_width=max_width,
        )
    else:
        lines = [value]
    return "<br/>".join(escape(get_display(line)) for line in lines)


def make_paragraph_style(
    name: str,
    parent: ParagraphStyle,
    fonts: PdfFonts,
    *,
    rtl: bool = False,
    bold: bool = False,
    font_size: int | None = None,
    color=None,
    space_before: float | None = None,
    space_after: float | None = None,
) -> ParagraphStyle:
    # wordWrap="RTL" is deliberately not set: without the optional rlbidi
    # backend ReportLab only reverses word order, which corrupts the text that
    # prepare_pdf_text has already put into visual order.
    kwargs: dict = {
        "fontName": fonts.bold if bold else fonts.regular,
        "alignment": TA_RIGHT if rtl else TA_LEFT,
    }
    if font_size is not None:
        kwargs["fontSize"] = font_size
    if color is not None:
        kwargs["textColor"] = color
    if space_before is not None:
        kwargs["spaceBefore"] = space_before
    if space_after is not None:
        kwargs["spaceAfter"] = space_after
    return ParagraphStyle(name, parent=parent, **kwargs)


def build_export_filename(title: str | None, recipe_id: int, extension: str) -> str:
    """Build an ASCII-safe attachment filename for HTTP headers."""
    base = (title or "").strip()
    if base:
        cleaned = "".join(
            char
            if char.isascii() and (char.isalnum() or char in {"-", "_"})
            else "_"
            for char in base.replace(" ", "_")
        )
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        cleaned = cleaned.strip("_")
        if cleaned:
            return f"{cleaned}.{extension}"
    return f"recipe_{recipe_id}.{extension}"


def build_export_filename_utf8(title: str | None, recipe_id: int, extension: str) -> str:
    """Build a Unicode attachment filename for RFC 5987 filename*."""
    base = (title or "").strip() or f"recipe_{recipe_id}"
    cleaned = "".join(
        char if char.isalnum() or char in {" ", "-", "_"} else "_"
        for char in base
    )
    cleaned = cleaned.strip().replace(" ", "_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.strip("_") or f"recipe_{recipe_id}"
    return f"{cleaned}.{extension}"


def build_content_disposition(title: str | None, recipe_id: int, extension: str) -> str:
    """Content-Disposition header safe for latin-1 with UTF-8 filename fallback."""
    from urllib.parse import quote

    ascii_filename = build_export_filename(title, recipe_id, extension)
    utf8_filename = quote(build_export_filename_utf8(title, recipe_id, extension))
    return f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{utf8_filename}'
