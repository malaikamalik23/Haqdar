import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_web as cw  # noqa: E402

CSP = "default-src 'self'; script-src 'self'; style-src 'self'"


def page(body="<p>hi</p>", head_extra="", csp=CSP, attrs='lang="ur" dir="rtl"'):
    csp_tag = f'<meta http-equiv="Content-Security-Policy" content="{csp}">' if csp else ""
    return (f'<!doctype html><html {attrs}><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">{csp_tag}'
            f'<link rel="stylesheet" href="style.css">{head_extra}</head><body>{body}</body></html>')


def site(tmp_path, html):
    (tmp_path / "index.html").write_text(html, encoding="utf-8")
    (tmp_path / "style.css").write_text("body{}", encoding="utf-8")
    return cw.check_site(tmp_path)


def test_a_clean_page_passes(tmp_path):
    assert site(tmp_path, page()) == {"index.html": []}


def test_inline_script_style_and_handlers_are_flagged(tmp_path):
    bad = page(body='<p style="color:red" onclick="x()">hi</p><script>alert(1)</script><style>p{}</style>')
    problems = site(tmp_path, bad)["index.html"]
    assert any("inline style attribute" in p for p in problems)
    assert any("event handler" in p for p in problems)
    assert any("inline <script>" in p for p in problems)
    assert any("inline <style>" in p for p in problems)


def test_weak_or_missing_csp_is_flagged(tmp_path):
    assert any("no Content-Security-Policy" in p for p in site(tmp_path, page(csp=None))["index.html"])
    weak = page(csp="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'")
    assert any("unsafe-inline" in p for p in site(tmp_path, weak)["index.html"])


def test_missing_files_and_duplicate_ids_are_flagged(tmp_path):
    bad = page(body='<img src="gone.png" alt=""><p id="a"></p><p id="a"></p>')
    problems = site(tmp_path, bad)["index.html"]
    assert any("missing file: gone.png" in p for p in problems)
    assert any("duplicate ids" in p for p in problems)


def test_unbalanced_tags_and_unsafe_blank_links_are_flagged(tmp_path):
    problems = site(tmp_path, page(body='<div><p>hi</div><a href="https://x.example" target="_blank">x</a>'))["index.html"]
    assert any("unexpected" in p or "unclosed" in p for p in problems)
    assert any("noopener" in p for p in problems)


def test_html_needs_lang_and_dir(tmp_path):
    assert any("lang and dir" in p for p in site(tmp_path, page(attrs=""))["index.html"])


def test_tool_page_must_have_the_elements_app_js_uses(tmp_path):
    (tmp_path / "app.js").write_text('const a = $("q"); const b = $("btn-review");', encoding="utf-8")
    html = page(body="<p>x</p>").replace("<body>", '<body data-mode="ask">')
    problems = site(tmp_path, html)["index.html"]
    assert any("app.js expects" in p for p in problems)


def test_service_worker_and_manifest_are_checked(tmp_path):
    (tmp_path / "sw.js").write_text('const SHELL = ["./", "style.css", "missing.js"];', encoding="utf-8")
    (tmp_path / "manifest.json").write_text('{"icons": [{"src": "nope.png"}]}', encoding="utf-8")
    results = site(tmp_path, page())
    assert results["sw.js"] == ["precached file does not exist: missing.js"]
    assert results["manifest.json"] == ["icon file missing: nope.png"]


def test_the_real_site_passes():
    real = Path(__file__).resolve().parents[2] / "web"
    if real.exists():
        problems = {k: v for k, v in cw.check_site(real).items() if v}
        assert problems == {}