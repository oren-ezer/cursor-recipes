"""Tests for PDF export helpers."""

from types import SimpleNamespace

from src.utils.pdf_export import (
    HEBREW_ALEPH,
    HEBREW_TAV,
    build_content_disposition,
    build_export_filename,
    build_export_filename_utf8,
    contains_hebrew,
    prepare_pdf_text,
    recipe_uses_rtl,
    register_pdf_fonts,
    resolve_pdf_fonts,
)


class TestPdfExportHelpers:
    def test_contains_hebrew(self):
        assert contains_hebrew("מתכון")
        assert not contains_hebrew("Pancakes")

    def test_recipe_uses_rtl(self):
        recipe = SimpleNamespace(
            title="English",
            description="Desc",
            difficulty_level="Easy",
            ingredients=[{"name": "flour", "amount": "1 cup"}],
            instructions=["Mix"],
        )
        assert not recipe_uses_rtl(recipe)

        recipe.title = "מתכון"
        assert recipe_uses_rtl(recipe)

    def test_prepare_pdf_text_escapes_xml(self):
        assert prepare_pdf_text('Tom & "Jerry"') == "Tom &amp; &quot;Jerry&quot;"

    def test_prepare_pdf_text_reorders_hebrew(self):
        original = "מתכון לפנקייק"
        prepared = prepare_pdf_text(original, rtl=True)
        assert prepared != original

    def test_build_export_filename_preserves_ascii(self):
        assert build_export_filename("Pancake Recipe", 7, "pdf") == "Pancake_Recipe.pdf"

    def test_build_export_filename_hebrew_uses_ascii_fallback(self):
        assert build_export_filename("מתכון לפנקייק", 7, "pdf") == "recipe_7.pdf"

    def test_build_export_filename_utf8_preserves_hebrew(self):
        assert build_export_filename_utf8("מתכון לפנקייק", 7, "pdf") == "מתכון_לפנקייק.pdf"

    def test_build_content_disposition_is_latin1_safe(self):
        header = build_content_disposition("מתכון לפנקייק", 7, "pdf")
        header.encode("latin-1")
        assert 'filename="recipe_7.pdf"' in header
        assert "filename*=UTF-8''" in header

    def test_resolve_pdf_fonts_covers_hebrew(self):
        from reportlab.pdfbase.ttfonts import TTFont

        family, regular_path, bold_path = resolve_pdf_fonts()

        assert regular_path.is_file()
        assert bold_path.is_file()

        face = TTFont(f"{family}-coverage-probe", str(regular_path)).face
        for codepoint in range(HEBREW_ALEPH, HEBREW_TAV + 1):
            assert codepoint in face.charToGlyph

    def test_register_pdf_fonts_is_cached(self):
        fonts = register_pdf_fonts()

        assert fonts.regular
        assert fonts.bold.endswith("-Bold")
        assert register_pdf_fonts() is fonts
