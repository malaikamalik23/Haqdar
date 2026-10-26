"""Static checks for the Haqdar web app. Run by CI, and safe to run by hand:

    python tools/check_web.py

It fails when a page is malformed, breaks the strict Content-Security-Policy (inline scripts, styles
or event handlers), points at a file that does not exist, or when app.js expects an element a tool
page does not have.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_WEB = Path(__file__).resolve().parent.parent / "web"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
EXTERNAL = re.compile(r"^(https?:|mailto:|data:|#)")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.ids, self.refs = [], [], []
        self.problems = []
        self.csp = None
        self.html_attrs = {}
        self.has_viewport = False
        self.body_attrs = {}

    def _record(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_attrs = a
        if tag == "body":
            self.body_attrs = a
        if "id" in a:
            self.ids.append(a["id"])
        for key in ("href", "src"):
            value = a.get(key)
            if value and not EXTERNAL.match(value):
                self.refs.append(value.split("#")[0].split("?")[0])
        if "style" in a:
            self.problems.append(f"inline style attribute on <{tag}>")
        for name in a:
            if name.startswith("on"):
                self.problems.append(f"inline event handler {name} on <{tag}>")
        if tag == "style":
            self.problems.append("inline <style> block")
        if tag == "script" and "src" not in a:
            self.problems.append("inline <script> block")
        if tag == "meta":
            if (a.get("http-equiv") or "").lower() == "content-security-policy":
                self.csp = a.get("content", "")
            if a.get("name") == "viewport":
                self.has_viewport = True
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""):
            self.problems.append("link with target=_blank is missing rel=noopener")

    def handle_starttag(self, tag, attrs):
        self._record(tag, attrs)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self._record(tag, attrs)  # self-closing, nothing to balance

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"unexpected </{tag}> (open tags: {self.stack[-3:]})")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def check_page(path, web_dir):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    problems = list(parser.problems)
    if parser.stack:
        problems.append(f"unclosed tags: {parser.stack}")
    dupes = sorted({i for i in parser.ids if parser.ids.count(i) > 1})
    if dupes:
        problems.append(f"duplicate ids: {dupes}")
    for ref in sorted({r for r in parser.refs if r}):
        if not (web_dir / ref).exists():
            problems.append(f"missing file: {ref}")
    if parser.csp is None:
        problems.append("no Content-Security-Policy meta tag")
    else:
        for needed in ("script-src 'self'", "style-src 'self'"):
            if needed not in parser.csp:
                problems.append(f"CSP is missing {needed}")
        for banned in ("unsafe-inline", "unsafe-eval"):
            if banned in parser.csp:
                problems.append(f"CSP allows {banned}")
    if not parser.html_attrs.get("lang") or not parser.html_attrs.get("dir"):
        problems.append("<html> needs lang and dir attributes")
    if not parser.has_viewport:
        problems.append("missing viewport meta tag")
    return problems, parser


def check_site(web_dir=DEFAULT_WEB):
    web_dir = Path(web_dir)
    results = {}
    pages = sorted(web_dir.glob("*.html"))
    if not pages:
        return {"(site)": [f"no HTML pages found in {web_dir}"]}

    app_js = web_dir / "app.js"
    expected_ids = set(re.findall(r'\$\("([A-Za-z0-9_-]+)"\)', app_js.read_text(encoding="utf-8"))) if app_js.exists() else set()

    for page in pages:
        problems, parser = check_page(page, web_dir)
        if parser.body_attrs.get("data-mode"):  # a tool page that loads app.js
            absent = sorted(i for i in expected_ids if i not in parser.ids)
            if absent:
                problems.append(f"app.js expects elements this page lacks: {absent}")
        results[page.name] = problems

    sw = web_dir / "sw.js"
    if sw.exists():
        match = re.search(r"const SHELL = \[(.*?)\]", sw.read_text(encoding="utf-8"), re.S)
        shell = re.findall(r'"([^"]+)"', match.group(1)) if match else []
        missing = [f for f in shell if f != "./" and not (web_dir / f).exists()]
        results["sw.js"] = [f"precached file does not exist: {f}" for f in missing]

    manifest = web_dir / "manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            results["manifest.json"] = [f"icon file missing: {i['src']}" for i in data.get("icons", [])
                                        if not (web_dir / i["src"]).exists()]
        except json.JSONDecodeError as exc:
            results["manifest.json"] = [f"not valid JSON: {exc}"]
    return results


def main(argv):
    web_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_WEB
    results = check_site(web_dir)
    failed = False
    for name, problems in results.items():
        print(("FAIL " if problems else "ok   ") + name)
        for problem in problems:
            print("     -", problem)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))