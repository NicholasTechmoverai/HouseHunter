import pytest
from utils.sanitizers import sanitizeContents, sanitize_name, clean_and_truncate

def test_sanitize_contents_basic():
    # Test that simple text is returned unchanged
    assert sanitizeContents("Hello World") == "Hello World"
    
    # Test that allowed tags are preserved
    assert "<strong>important</strong>" in sanitizeContents("<strong>important</strong>")
    assert "<p>paragraph</p>" in sanitizeContents("<p>paragraph</p>")

def test_sanitize_contents_strips_malicious():
    # Test that <script> tags are stripped out
    dirty_html = "Hello <script>alert('hack');</script>World"
    result = sanitizeContents(dirty_html)
    assert "<script>" not in result
    assert "</script>" not in result

def test_sanitize_contents_linkify():
    # Test that URLs are converted to clickable links
    html = "Visit https://example.com for more details."
    result = sanitizeContents(html)
    assert '<a href="https://example.com" rel="nofollow">https://example.com</a>' in result

@pytest.mark.anyio
async def test_sanitize_name():
    # Test cleaning names for uploads
    assert await sanitize_name("My Custom Image File.PNG") == "my_custom_image_filepng"
    assert await sanitize_name("User Profile!!!") == "user_profile"
    assert await sanitize_name("   Spaces  Everywhere   ") == "spaces_everywhere"
    assert await sanitize_name("hello-world_123") == "hello-world_123"

def test_clean_and_truncate():
    # Test removing tags and truncating
    text_with_html = "<div>This is a <strong>very long</strong> description that needs truncation.</div>"
    
    # Under limit
    assert clean_and_truncate("Short text", 30) == "Short text"
    
    # HTML removal and truncation
    truncated = clean_and_truncate(text_with_html, 20)
    assert truncated == "This is a very lo..."
    assert "strong" not in truncated
    assert "div" not in truncated

    # Empty string
    assert clean_and_truncate("", 20) == ""
    assert clean_and_truncate(None, 20) == ""

    # HTML entity decoding
    assert clean_and_truncate("Fish &amp; Chips", 30) == "Fish & Chips"
