import pytest
from src.utils.sanitization import (
    strip_html_tags,
    remove_dangerous_patterns,
    sanitize_text,
    sanitize_url,
    MAX_LENGTHS,
)


class TestStripHtmlTags:
    def test_removes_simple_tags(self):
        assert strip_html_tags("<b>bold</b>") == "bold"

    def test_removes_script_tags(self):
        assert strip_html_tags('<script>alert("xss")</script>') == 'alert("xss")'

    def test_removes_nested_tags(self):
        assert strip_html_tags("<div><p>hello</p></div>") == "hello"

    def test_preserves_plain_text(self):
        assert strip_html_tags("just plain text") == "just plain text"

    def test_angle_brackets_around_text_treated_as_tag(self):
        result = strip_html_tags("5 < 10 and 20 > 15")
        assert "5" in result and "15" in result

    def test_removes_self_closing_tags(self):
        assert strip_html_tags("line<br/>break") == "linebreak"

    def test_removes_tags_with_attributes(self):
        assert strip_html_tags('<a href="http://evil.com">click</a>') == "click"

    def test_handles_img_with_onerror(self):
        result = strip_html_tags('<img src=x onerror=alert(1)>')
        assert "<img" not in result


class TestRemoveDangerousPatterns:
    def test_removes_javascript_protocol(self):
        assert "javascript" not in remove_dangerous_patterns("javascript:alert(1)").lower()

    def test_removes_javascript_with_spaces(self):
        assert "javascript" not in remove_dangerous_patterns("javascript :void(0)").lower()

    def test_removes_vbscript_protocol(self):
        assert "vbscript" not in remove_dangerous_patterns("vbscript:msgbox").lower()

    def test_removes_onload_handler(self):
        result = remove_dangerous_patterns('onload=alert(1)')
        assert "onload=" not in result.lower()

    def test_removes_onerror_handler(self):
        result = remove_dangerous_patterns('onerror=alert(1)')
        assert "onerror=" not in result.lower()

    def test_removes_data_text_html(self):
        result = remove_dangerous_patterns("data:text/html,<script>alert(1)</script>")
        assert "data:text/html" not in result.lower()

    def test_preserves_safe_text(self):
        safe = "This is a perfectly safe recipe description."
        assert remove_dangerous_patterns(safe) == safe

    def test_case_insensitive(self):
        assert "JAVASCRIPT" not in remove_dangerous_patterns("JAVASCRIPT:alert(1)")


class TestSanitizeText:
    def test_strips_html_and_trims(self):
        assert sanitize_text("  <b>hello</b>  ") == "hello"

    def test_removes_script_injection(self):
        result = sanitize_text('<script>alert("xss")</script>Normal text')
        assert "<script>" not in result
        assert "Normal text" in result

    def test_enforces_max_length(self):
        long_text = "a" * 500
        result = sanitize_text(long_text, max_length=100)
        assert len(result) == 100

    def test_max_length_none_allows_any_length(self):
        long_text = "a" * 10000
        result = sanitize_text(long_text)
        assert len(result) == 10000

    def test_strips_whitespace_by_default(self):
        assert sanitize_text("  hello  ") == "hello"

    def test_preserves_whitespace_when_requested(self):
        result = sanitize_text("  hello  ", strip_whitespace=False)
        assert result == "  hello  "

    def test_combined_xss_payload(self):
        payload = '<img src="x" onerror="alert(1)">Safe text<script>evil()</script>'
        result = sanitize_text(payload)
        assert "<" not in result or ">" not in result
        assert "Safe text" in result

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_preserves_unicode(self):
        assert sanitize_text("שלום עולם") == "שלום עולם"

    def test_preserves_newlines_in_content(self):
        result = sanitize_text("line1\nline2", strip_whitespace=False)
        assert "line1\nline2" in result


class TestSanitizeUrl:
    def test_accepts_http(self):
        url = "http://example.com/image.jpg"
        assert sanitize_url(url) == url

    def test_accepts_https(self):
        url = "https://example.com/image.jpg"
        assert sanitize_url(url) == url

    def test_rejects_javascript_scheme(self):
        assert sanitize_url("javascript:alert(1)") == ""

    def test_rejects_data_scheme(self):
        assert sanitize_url("data:text/html,<script>alert(1)</script>") == ""

    def test_rejects_ftp_scheme(self):
        assert sanitize_url("ftp://example.com/file") == ""

    def test_rejects_no_scheme(self):
        assert sanitize_url("example.com/image.jpg") == ""

    def test_rejects_empty_string(self):
        assert sanitize_url("") == ""

    def test_strips_whitespace(self):
        assert sanitize_url("  https://example.com  ") == "https://example.com"

    def test_rejects_too_long_url(self):
        long_url = "https://example.com/" + "a" * 3000
        assert sanitize_url(long_url) == ""

    def test_rejects_no_netloc(self):
        assert sanitize_url("https://") == ""

    def test_accepts_url_with_path_and_query(self):
        url = "https://example.com/path?q=search&page=1"
        assert sanitize_url(url) == url

    def test_accepts_url_with_port(self):
        url = "https://example.com:8080/image.jpg"
        assert sanitize_url(url) == url

    def test_custom_max_length(self):
        url = "https://example.com/" + "a" * 50
        assert sanitize_url(url, max_length=30) == ""


class TestMaxLengths:
    """Verify all expected keys exist in MAX_LENGTHS."""

    def test_recipe_fields_exist(self):
        assert "recipe_title" in MAX_LENGTHS
        assert "recipe_description" in MAX_LENGTHS
        assert "ingredient_name" in MAX_LENGTHS
        assert "ingredient_amount" in MAX_LENGTHS
        assert "instruction" in MAX_LENGTHS
        assert "image_url" in MAX_LENGTHS

    def test_user_fields_exist(self):
        assert "user_full_name" in MAX_LENGTHS

    def test_tag_fields_exist(self):
        assert "tag_name" in MAX_LENGTHS

    def test_ai_fields_exist(self):
        assert "ai_prompt" in MAX_LENGTHS
        assert "ai_query" in MAX_LENGTHS

    def test_llm_fields_exist(self):
        assert "llm_system_prompt" in MAX_LENGTHS
        assert "llm_user_prompt_template" in MAX_LENGTHS
        assert "llm_description" in MAX_LENGTHS
        assert "llm_service_name" in MAX_LENGTHS
        assert "llm_model_name" in MAX_LENGTHS

    def test_all_values_are_positive_ints(self):
        for key, val in MAX_LENGTHS.items():
            assert isinstance(val, int), f"{key} is not an int"
            assert val > 0, f"{key} is not positive"
