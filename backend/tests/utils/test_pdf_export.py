"""Tests for PDF export helpers."""

from types import SimpleNamespace

from src.utils.pdf_export import (
    HEBREW_ALEPH,
    HEBREW_TAV,
    build_content_disposition,
    build_export_filename,
    build_export_filename_utf8,
    contains_hebrew,
    is_rtl_language,
    normalize_pdf_language,
    prepare_pdf_text,
    recipe_uses_rtl,
    register_pdf_fonts,
    resolve_pdf_fonts,
    resolve_pdf_language,
    translate_difficulty,
    translate_pdf_text,
    wrap_text_to_width,
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
        assert prepare_pdf_text("Tom & <b>Jerry</b>") == "Tom &amp; &lt;b&gt;Jerry&lt;/b&gt;"

    def test_prepare_pdf_text_keeps_quotes_unescaped(self):
        # Quote entities would split the paragraph into separate fragments,
        # which breaks the visual ordering of a reordered Hebrew line.
        assert prepare_pdf_text("""Tom's "Jerry\"""") == """Tom's "Jerry\""""

    def test_prepare_pdf_text_reorders_hebrew(self):
        original = "מתכון לפנקייק"
        prepared = prepare_pdf_text(original)
        assert prepared != original

    def test_prepare_pdf_text_reorders_hebrew_with_apostrophe_as_one_run(self):
        prepared = prepare_pdf_text("• 500 גר' מסקרפונה")

        assert "&apos;" not in prepared
        assert "<br/>" not in prepared

    def test_prepare_pdf_text_breaks_hebrew_lines_when_given_a_width(self):
        fonts = register_pdf_fonts()
        long_text = "לערבב חלמונים וסוכר היטב ואז לדפוק את הביצים עד לקבלת קצף יציב"

        prepared = prepare_pdf_text(
            long_text,
            font_name=fonts.regular,
            font_size=10,
            max_width=80,
        )

        assert "<br/>" in prepared

    def test_wrap_text_to_width_keeps_words_intact(self):
        fonts = register_pdf_fonts()

        lines = wrap_text_to_width(
            "one two three four five six seven eight nine ten",
            font_name=fonts.regular,
            font_size=10,
            max_width=60,
        )

        assert len(lines) > 1
        assert " ".join(lines).split() == "one two three four five six seven eight nine ten".split()

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


class TestPdfLocalization:
    def _recipe(self, title="English", difficulty="Easy"):
        return SimpleNamespace(
            title=title,
            description="Desc",
            difficulty_level=difficulty,
            ingredients=[{"name": "flour", "amount": "1 cup"}],
            instructions=["Mix"],
        )

    def test_normalize_pdf_language_accepts_regional_tags(self):
        assert normalize_pdf_language("he-IL") == "he"
        assert normalize_pdf_language("EN") == "en"
        assert normalize_pdf_language("fr") is None
        assert normalize_pdf_language(None) is None

    def test_is_rtl_language(self):
        assert is_rtl_language("he")
        assert not is_rtl_language("en")

    def test_resolve_pdf_language_prefers_explicit_request(self):
        hebrew_recipe = self._recipe(title="מתכון")

        assert resolve_pdf_language("en", hebrew_recipe) == "en"

    def test_resolve_pdf_language_falls_back_to_recipe_content(self):
        assert resolve_pdf_language(None, self._recipe(title="מתכון")) == "he"
        assert resolve_pdf_language(None, self._recipe()) == "en"
        assert resolve_pdf_language("fr", self._recipe(title="מתכון")) == "he"

    def test_translate_pdf_text_returns_localized_labels(self):
        assert translate_pdf_text("en", "ingredients") == "Ingredients"
        assert translate_pdf_text("he", "ingredients") == "רכיבים"

    def test_translate_pdf_text_formats_placeholders(self):
        assert translate_pdf_text("en", "minutes", count=30) == "30 minutes"
        assert translate_pdf_text("he", "minutes", count=30) == "30 דקות"
        assert translate_pdf_text("he", "step", number=2) == "שלב 2:"

    def test_translate_pdf_text_falls_back_to_english(self):
        assert translate_pdf_text("fr", "servings") == "Servings"

    def test_translate_difficulty(self):
        assert translate_difficulty("he", "Medium") == "בינוני"
        assert translate_difficulty("en", "Medium") == "Medium"
        assert translate_difficulty("he", "Unknown") == "Unknown"
        assert translate_difficulty("he", None) == ""
