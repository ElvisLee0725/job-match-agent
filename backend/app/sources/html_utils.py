import html as html_lib

from bs4 import BeautifulSoup


def strip_html(html: str | None) -> str:
    if not html:
        return ""
    # Some sources (e.g. Greenhouse) return HTML-entity-escaped markup (`&lt;p&gt;`)
    # rather than literal tags — unescape first so BeautifulSoup parses real markup
    # instead of treating the escaped entities as plain text. A no-op for content
    # that's already literal HTML (nothing to unescape).
    unescaped = html_lib.unescape(html)
    return BeautifulSoup(unescaped, "lxml").get_text(separator="\n").strip()
