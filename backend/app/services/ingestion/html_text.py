"""Extract the article text of a documentation page (Docusaurus) from HTML.

Used only by curation tooling (scripts/verify_knowledge_excerpts.py). Fetched pages are untrusted data:
they are parsed as text, never executed.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

_SKIP = {"script", "style", "svg", "button", "nav", "noscript"}
_BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "h5", "tr", "pre", "div", "br", "blockquote", "td", "th"}


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.skip = 0
        self.out: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if self.depth == 0:
            if tag == "article":
                self.depth = 1
            return
        if tag in _SKIP:
            self.skip += 1
        if tag in _BLOCK:
            self.out.append("\n")
        self.depth += 1

    def handle_startendtag(self, tag, attrs):
        if self.depth and tag == "br":
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if not self.depth:
            return
        if tag in _SKIP and self.skip:
            self.skip -= 1
        self.depth -= 1
        if tag in _BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self.depth and not self.skip:
            self.out.append(data)


def extract_article(html: str) -> tuple[str, str]:
    """Return (page title, article text)."""
    p = _ArticleParser()
    p.feed(html)
    text = re.sub(r"[ \t]+", " ", "".join(p.out))
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return p.title.strip(), text
