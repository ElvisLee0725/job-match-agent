from app.sources.html_utils import strip_html


def test_strip_html_handles_literal_markup():
    # get_text(separator="\n") joins each tag's text with a newline
    assert strip_html("<p>Hello <strong>world</strong></p>") == "Hello \nworld"


def test_strip_html_handles_entity_escaped_markup():
    # Greenhouse returns content this way: HTML-entity-escaped, not literal tags
    assert strip_html("&lt;p&gt;Hello &lt;strong&gt;world&lt;/strong&gt;&lt;/p&gt;") == "Hello \nworld"


def test_strip_html_handles_none_and_empty():
    assert strip_html(None) == ""
    assert strip_html("") == ""
