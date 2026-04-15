"""Input sanitization utilities for defense-in-depth against stored XSS and malicious input.

All user-facing text fields should be sanitized before storage.
React's JSX auto-escaping protects the frontend, but sanitizing on the backend
ensures safety for non-browser consumers (PDF export, API clients, future
rich-text rendering, etc.).
"""

import re
from urllib.parse import urlparse

_HTML_TAG_RE = re.compile(r"<[^>]+>")

_DANGEROUS_PATTERNS = [
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
]

ALLOWED_URL_SCHEMES = {"http", "https"}

MAX_LENGTHS = {
    "recipe_title": 200,
    "recipe_description": 5000,
    "ingredient_name": 200,
    "ingredient_amount": 100,
    "instruction": 2000,
    "image_url": 2048,
    "user_full_name": 150,
    "tag_name": 50,
    "ai_prompt": 10000,
    "ai_query": 500,
    "llm_system_prompt": 10000,
    "llm_user_prompt_template": 10000,
    "llm_description": 1000,
    "llm_service_name": 100,
    "llm_model_name": 100,
}


def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from a string."""
    return _HTML_TAG_RE.sub("", text)


def remove_dangerous_patterns(text: str) -> str:
    """Remove javascript:, vbscript:, onevent= and data:text/html patterns."""
    result = text
    for pattern in _DANGEROUS_PATTERNS:
        result = pattern.sub("", result)
    return result


def sanitize_text(text: str, *, max_length: int | None = None, strip_whitespace: bool = True) -> str:
    """Sanitize a general text field: strip HTML, remove dangerous patterns, trim, enforce length.

    Args:
        text: Raw input string.
        max_length: Optional maximum character count after cleaning.
        strip_whitespace: Whether to strip leading/trailing whitespace (default True).

    Returns:
        Cleaned string.
    """
    cleaned = strip_html_tags(text)
    cleaned = remove_dangerous_patterns(cleaned)
    if strip_whitespace:
        cleaned = cleaned.strip()
    if max_length is not None and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def sanitize_url(url: str, *, max_length: int = MAX_LENGTHS["image_url"]) -> str:
    """Validate and sanitize a URL string.

    Allows only http and https schemes. Returns an empty string for invalid/dangerous URLs.
    """
    url = url.strip()
    if not url:
        return ""
    if len(url) > max_length:
        return ""
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        return ""
    if not parsed.netloc:
        return ""
    return url
