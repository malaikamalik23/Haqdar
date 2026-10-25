from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

CSP_STATIC = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; base-uri 'none'; form-action 'none'"
CSP_TOOL = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' http://localhost:8000; base-uri 'none'; form-action 'none'"

ICONS = {
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "ask": '<path d="M4 5h16v11H9l-5 4z"/><path d="M9 10h6"/>',
    "notice": '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4"/><path d="M10 12h6M10 16h6"/>',
    "about": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.5h.01"/>',
    "bolt": '<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>',
    "card": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M6 16c.6-1.6 5.4-1.6 6 0M14 10h4M14 13h4"/>',
}


def icon(name, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


def bi(ur, en, tag="span", cls=None):
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-l="ur">{ur}</{tag}><{tag}{c} data-l="en">{en}</{tag}>'


def current_attr(key, cur):
    return ' aria-current="page"' if key == cur else ""


def img2(src, alt_ur, alt_en, cls, w, h):
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} data-l="ur" src="{src}" alt="{alt_ur}" width="{w}" height="{h}">'
            f'<img{c} data-l="en" src="{src}" alt="{alt_en}" width="{w}" height="{h}">')


NAV = [
    ("home", "index.html", "مرکزی صفحہ", "Home", "مرکزی", "Home"),
    ("ask", "ask.html", "سوال پوچھیں", "Ask a question", "سوال", "Ask"),
    ("notice", "notice.html", "نوٹس سمجھیں", "Understand a notice", "نوٹس", "Notice"),
    ("about", "about.html", "ہمارے بارے میں", "About", "تعارف", "About"),
]


def header(cur):
    links = "".join(
        f'<a href="{href}"{current_attr(key, cur)}>{bi(ur, en)}</a>'
        for key, href, ur, en, _, _ in NAV
    )
    return f'''<header class="top">
    <div class="top-inner">
      <a class="brand" href="index.html" aria-label="حقدار Haqdar">
        <img src="logo.svg" alt="" width="117" height="44">
        <span class="brand-en" data-l="en">Haqdar</span>
      </a>
      <nav class="site-nav" aria-label="Main">{links}</nav>
      <div class="lang" role="group" aria-label="Language / زبان">
        <button id="lang-ur" type="button" lang="ur" aria-pressed="true">اردو</button>
        <button id="lang-en" type="button" lang="en" aria-pressed="false">English</button>
      </div>
    </div>
  </header>'''


def tabbar(cur):
    links = "".join(
        f'<a href="{href}"{current_attr(key, cur)}>{icon(key)}{bi(sur, sen)}</a>'
        for key, href, _, _, sur, sen in NAV
    )
    return f'<nav class="tabbar" aria-label="Main">{links}</nav>'


def page(cur, title_ur, title_en, body, *, csp, mode=None, scripts=("site.js",), end_scripts=()):
    mode_attr = f' data-mode="{mode}"' if mode else ""
    head_scripts = "\n  ".join(f'<script src="{s}"></script>' for s in scripts)
    tail = "\n  ".join(f'<script src="{s}"></script>' for s in end_scripts)
    return f'''<!doctype html>
<html lang="ur" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="{csp}">
  <meta name="theme-color" content="#0d6b4a">
  <title>{title_ur}</title>
  <link rel="manifest" href="manifest.json">
  <link rel="icon" href="icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="stylesheet" href="style.css">
  {head_scripts}
</head>
<body{mode_attr} data-title-ur="{title_ur}" data-title-en="{title_en}">
  <a class="skip" href="#main">{bi("مرکزی مواد پر جائیں", "Skip to main content")}</a>
  {header(cur)}
{body}
  <footer id="site-footer" class="site-footer"></footer>
  {tabbar(cur)}
  {tail}
</body>
</html>
'''


# ---------------------------------------------------------------- Home
def topic(key, icon_name, t_ur, t_en, s_ur, s_en):
    return f'''<li><a href="ask.html?topic={key}">{icon(icon_name)}<span>{bi(t_ur, t_en)}<small>{bi(s_ur, s_en)}</small></span></a></li>'''


home_body = f'''
  <main id="main">
    <section class="hero" aria-labelledby="hero-title">
      <div class="wrap hero-grid">
        <div class="hero-copy">
          {img2("logo-stacked.svg", "حقدار: آپ کا حق، آسان زبان میں", "Haqdar: your rights, in plain language", "hero-logo", 360, 382)}
          <h1 class="hero-title" id="hero-title">{bi("سرکاری کاغذات سمجھیں، اپنا حق جانیں", "Understand official papers. Know your rights.")}</h1>
          <p class="hero-intro">{bi(
    "حقدار ٹیکس نوٹس، بجلی کے بل، شناختی کارڈ اور کرایہ نامے جیسے سرکاری کاغذات آسان اردو اور انگریزی میں سمجھاتا ہے۔ ہر قدم کے ساتھ اس کا ماخذ ہوتا ہے، اور تصدیق نہ ہو سکے تو حقدار صاف بتا دیتا ہے۔",
    "Haqdar explains tax notices, electricity bills, CNIC procedures and rent agreements in plain Urdu and English. Every step comes with its source, and when Haqdar can't verify something, it says so.", "span")}</p>
          <div class="cta-row">
            <a class="btn btn-primary" href="ask.html">{icon("ask")}{bi("سوال پوچھیں", "Ask a question")}</a>
            <a class="btn btn-secondary" href="notice.html">{icon("notice")}{bi("نوٹس سمجھیں", "Understand a notice")}</a>
          </div>
          <ul class="assure">
            <li>{bi("اکاؤنٹ کی ضرورت نہیں", "No account needed")}</li>
            <li>{bi("ذاتی معلومات بھیجنے سے پہلے چھپ جاتی ہیں", "Personal details are hidden before sending")}</li>
            <li>{bi("آپ کے دستاویزات محفوظ نہیں ہوتے", "Your documents are not stored")}</li>
          </ul>
        </div>
        <div class="hero-art">
          {img2("hero.svg", "ایک الجھا ہوا نوٹس جس میں ذاتی معلومات چھپی ہیں اور «مشکوک» کی مہر لگی ہے، اس کے ساتھ اقدامات کا واضح کارڈ", "A confusing notice with hidden personal details and a suspicious stamp, next to a clear card of steps", "", 640, 520)}
        </div>
      </div>
    </section>

    <section class="band" aria-labelledby="how-title">
      <div class="wrap">
        <h2 id="how-title">{bi("یہ کیسے کام کرتا ہے", "How it works")}</h2>
        <ol class="how">
          <li><div data-l="ur"><strong>لکھیں یا پیسٹ کریں</strong><span class="d">اپنا سوال لکھیں یا نوٹس کا متن پیسٹ کریں۔</span></div>
              <div data-l="en"><strong>Write or paste</strong><span class="d">Ask a question or paste the text of a notice.</span></div></li>
          <li><div data-l="ur"><strong>بھیجنے سے پہلے جانچیں</strong><span class="d">ذاتی معلومات چھپ جاتی ہیں، اور آپ خود دیکھ لیتے ہیں کہ کیا بھیجا جائے گا۔</span></div>
              <div data-l="en"><strong>Review before sending</strong><span class="d">Personal details are hidden, and you see exactly what will be sent.</span></div></li>
          <li><div data-l="ur"><strong>ماخذ کے ساتھ جواب پڑھیں</strong><span class="d">آسان زبان میں اقدامات، ہر قدم کے ساتھ سرکاری ماخذ۔</span></div>
              <div data-l="en"><strong>Read the answer with sources</strong><span class="d">Steps in plain language, each linked to its official source.</span></div></li>
        </ol>
      </div>
    </section>

    <section class="section" aria-labelledby="topics-title">
      <div class="wrap">
        <h2 id="topics-title">{bi("آپ کس بارے میں پوچھ سکتے ہیں", "What you can ask about")}</h2>
        <p class="sub">{bi("شروع کرنے کے لیے کوئی موضوع چنیں۔", "Pick a topic to start.")}</p>
        <ul class="topics">
          {topic("electricity", "bolt", "بجلی کے بل پر اعتراض", "Disputing an electricity bill", "بل زیادہ آئے تو کیا کریں", "What to do when the bill is too high")}
          {topic("fbr", "notice", "ایف بی آر کا نوٹس", "An FBR notice", "نوٹس ملنے پر اگلے اقدامات", "Next steps after you receive one")}
          {topic("cnic", "card", "شناختی کارڈ کی خدمات", "CNIC services", "تجدید اور درستی کا طریقہ", "Renewal and corrections")}
          {topic("rent", "home", "کرایہ نامہ", "Rent agreements", "اس میں کیا ہونا چاہیے", "What one should include")}
        </ul>
      </div>
    </section>

    <section class="trust-wrap trust" aria-labelledby="trust-title">
      <div class="wrap">
        <h2 id="trust-title">{bi("جواب پر بھروسا کیوں کریں", "Why you can trust the answers")}</h2>
        <ul class="checks">
          <li><div data-l="ur"><strong>ہر قدم کے ساتھ ماخذ</strong> ہر قدم اس سرکاری صفحے سے جڑا ہوتا ہے جہاں سے لیا گیا۔</div>
              <div data-l="en"><strong>A source for every step</strong> Each step links to the official page it came from.</div></li>
          <li><div data-l="ur"><strong>تصدیق نہ ہو تو صاف بتاتا ہے</strong> ماخذ جواب کی تائید نہ کریں تو حقدار اندازہ نہیں لگاتا، متعلقہ دفتر کی طرف بھیجتا ہے۔</div>
              <div data-l="en"><strong>It says when it can't verify</strong> If the sources don't support an answer, Haqdar doesn't guess. It points you to the right office.</div></li>
          <li><div data-l="ur"><strong>ذاتی معلومات چھپی رہتی ہیں</strong> شناختی کارڈ، فون اور اکاؤنٹ نمبر بھیجنے سے پہلے چھپا دیے جاتے ہیں۔</div>
              <div data-l="en"><strong>Personal details stay hidden</strong> CNIC, phone and account numbers are masked before anything is sent.</div></li>
        </ul>
        <p><a class="linkbtn" href="about.html">{bi("مزید جانیں", "Learn more about Haqdar")}</a></p>
      </div>
    </section>

    <section class="cta-band" aria-labelledby="cta-title">
      <div class="wrap">
        <h2 id="cta-title">{bi("کوئی نوٹس سمجھ نہیں آ رہا؟", "Got a notice you don't understand?")}</h2>
        <p>{bi("اسے پیسٹ کریں، حقدار سمجھا دے گا اور جعلی ہونے کی علامتیں بھی دیکھے گا۔", "Paste it and Haqdar will explain it and check it for warning signs.")}</p>
        <a class="btn btn-primary" href="notice.html">{icon("notice")}{bi("نوٹس سمجھیں", "Understand a notice")}</a>
      </div>
    </section>
  </main>'''

# ---------------------------------------------------------------- Tool pages (Ask / Notice)
SHIELD = '''<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 2l8 3v6c0 5-3.4 9.4-8 11-4.6-1.6-8-6-8-11V5l8-3z" fill="none" stroke="#0b3d2b" stroke-width="2" stroke-linejoin="round"/>
        <path d="M8.5 12l2.5 2.5 4.5-5" fill="none" stroke="#0b3d2b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>'''


def tool_body(*, spot, h1, sub, label, hint, extra_compose, tips_title, tips_items, placeholder):
    ph = ' data-i18n-placeholder="placeholderAsk"' if placeholder else ""
    return f'''
  <main id="main" class="tool">
    <div class="page-head">
      <img src="{spot}" alt="" width="88" height="88">
      <div>
        <h1>{h1}</h1>
        <p>{sub}</p>
      </div>
    </div>

    <p class="privacy">
      {SHIELD}
      <span>{bi("یہ معلومات ہیں، قانونی مشورہ نہیں۔ اپنا شناختی کارڈ نمبر، فون نمبر یا اکاؤنٹ نمبر نہ لکھیں۔", "This is information, not legal advice. Do not type your CNIC, phone or account number.")}</span>
    </p>

    <ol class="progress" data-i18n-label="progressLabel">
      <li id="step-1" class="is-current" aria-current="step"><span class="dot" aria-hidden="true">1</span>{bi("لکھیں", "Write")}</li>
      <li id="step-2"><span class="dot" aria-hidden="true">2</span>{bi("جانچیں", "Review")}</li>
      <li id="step-3"><span class="dot" aria-hidden="true">3</span>{bi("جواب", "Answer")}</li>
    </ol>

    <noscript><p class="status error">{bi("اس صفحے کے لیے JavaScript ضروری ہے۔", "This page needs JavaScript to work.")}</p></noscript>
    <div id="status" class="status" hidden></div>

    <section id="compose" class="sheet">
      <label for="q">{label}</label>
      <textarea id="q" maxlength="4000"{ph}></textarea>
      <div class="meta"><span id="count" dir="ltr">0 / 4000</span></div>
      <p class="hint">{hint}</p>
      <div id="chips" class="chips"></div>{extra_compose}
      <button id="btn-review" class="primary" type="button">{bi("بھیجنے سے پہلے جانچیں", "Review and send")}</button>
    </section>

    <section id="preview" class="sheet" aria-labelledby="preview-title" hidden>
      <h2 id="preview-title" tabindex="-1">{bi("بھیجنے سے پہلے دیکھ لیں", "Review before sending")}</h2>
      <p>{bi("صرف یہی متن آپ کے آلے سے نکلے گا۔ کالی پٹیاں وہ ذاتی معلومات ہیں جو چھپا دی گئی ہیں۔", "Only this text will leave your device. Black bars mark personal details we hid.")}</p>
      <div id="preview-text" class="preview-text" dir="auto"></div>
      <p id="mask-summary" class="mask-summary"></p>
      <div class="row">
        <button id="btn-confirm" class="primary" type="button">{bi("بھیجیں", "Send")}</button>
        <button id="btn-cancel" class="ghost" type="button">{bi("واپس جا کر ترمیم کریں", "Go back and edit")}</button>
      </div>
    </section>

    <section id="result" class="sheet" role="region" tabindex="-1" data-i18n-label="resultLabel" hidden></section>

    <section class="tips" aria-labelledby="tips-title">
      <h2 id="tips-title">{tips_title}</h2>
      <ul class="checks">
{tips_items}
      </ul>
    </section>
  </main>'''


def tip(ur, en, caveat=False):
    c = ' class="caveat"' if caveat else ""
    return f'        <li{c}><div data-l="ur">{ur}</div><div data-l="en">{en}</div></li>'


ask_body = tool_body(
    spot="spot-ask.svg",
    h1=bi("سوال پوچھیں", "Ask a question"),
    sub=bi("اپنا سوال اپنے الفاظ میں لکھیں۔ جواب کے ساتھ ماخذ بھی ملے گا۔", "Write your question in your own words. The answer comes with its sources."),
    label=bi("اپنا سوال لکھیں", "Write your question"),
    hint=bi("یا ان میں سے کوئی آزمائیں:", "Or try one of these:"),
    extra_compose="",
    tips_title=bi("بہتر جواب کے لیے", "For a better answer"),
    tips_items="\n".join([
        tip("بتائیں کہ کیا ہوا اور کس ادارے کا معاملہ ہے۔", "Say what happened and which office it involves."),
        tip("ایک وقت میں ایک سوال پوچھیں۔", "Ask one question at a time."),
        tip("شناختی کارڈ، فون یا اکاؤنٹ نمبر نہ لکھیں۔", "Don't type your CNIC, phone or account number.", True),
    ]),
    placeholder=True,
)

UPLOAD = f'''
      <div class="upload">
        <strong>{bi("تصویر سے نوٹس پڑھنا", "Read a notice from a photo")}</strong>
        <span>{bi("جلد دستیاب ہوگا۔ فی الحال نوٹس کا متن پیسٹ کریں۔", "Coming soon. For now, paste the notice text.")}</span>
      </div>'''

notice_body = tool_body(
    spot="spot-notice.svg",
    h1=bi("نوٹس سمجھیں", "Understand a notice"),
    sub=bi("نوٹس کا متن پیسٹ کریں۔ حقدار اسے آسان زبان میں سمجھائے گا اور جعلی ہونے کی علامتیں دیکھے گا۔", "Paste the text of a notice. Haqdar explains it in plain language and checks it for warning signs."),
    label=bi("نوٹس کا متن یہاں پیسٹ کریں", "Paste the notice text here"),
    hint=bi("یا نمونہ آزمائیں:", "Or try a sample:"),
    extra_compose=UPLOAD,
    tips_title=bi("ہم کیا دیکھتے ہیں", "What we look for"),
    tips_items="\n".join([
        tip("لنک سرکاری ویب سائٹ کا ہے یا نہیں", "Whether links go to an official government website"),
        tip("بھیجنے والے کا پتہ سرکاری ہے یا نہیں", "Whether the sender's address is official"),
        tip("موبائل والٹ یا گفٹ کارڈ سے ادائیگی کا مطالبہ", "Requests to pay through a mobile wallet or gift card"),
        tip("فوری یا دھمکی آمیز زبان", "Urgent or threatening language"),
        tip("یہ صرف انتباہی علامتیں ہیں، تصدیق نہیں۔", "These are warning signs only, not proof.", True),
    ]),
    placeholder=False,
)

# ---------------------------------------------------------------- About
about_body = f'''
  <main id="main" class="prose">
    {img2("logo-stacked.svg", "حقدار: آپ کا حق، آسان زبان میں", "Haqdar: your rights, in plain language", "about-logo", 360, 382)}
    <h1>{bi("حقدار کے بارے میں", "About Haqdar")}</h1>
    <p class="lead" data-l="ur">حقدار پاکستان میں لوگوں کو سرکاری نوٹس اور طریقۂ کار آسان اردو اور انگریزی میں سمجھنے میں مدد دیتا ہے، اور ہر قدم کے ساتھ اس کا ماخذ دکھاتا ہے۔</p>
    <p class="lead" data-l="en">Haqdar helps people in Pakistan understand official notices and procedures in plain Urdu and English, with a source for every step.</p>
    <p data-l="ur">«حقدار» کا مطلب ہے وہ شخص جس کا کسی چیز پر حق ہو۔ اپنے حقوق جاننے کی پہلی شرط یہ ہے کہ آپ کو سمجھ آئے کہ آپ سے کیا کہا جا رہا ہے۔</p>
    <p data-l="en">The name means someone who has a right to something. Knowing your rights starts with understanding what you are being asked to do.</p>

    <nav class="jump" aria-label="On this page">
      <a href="#problem">{bi("مسئلہ", "The problem")}</a>
      <a href="#how">{bi("کیسے کام کرتا ہے", "How it works")}</a>
      <a href="#privacy">{bi("پرائیویسی", "Privacy")}</a>
      <a href="#limits">{bi("حدود", "Limits")}</a>
      <a href="#open-source">{bi("اوپن سورس", "Open source")}</a>
      <a href="#team">{bi("ٹیم", "Team")}</a>
    </nav>

    <section id="problem">
      <h2>{bi("مسئلہ", "The problem")}</h2>
      <p data-l="ur">ٹیکس کے نوٹس، بجلی کے بل، شناختی کارڈ کے طریقۂ کار اور کرایہ نامے عموماً مشکل انگریزی یا قانونی زبان میں لکھے ہوتے ہیں۔ بہت سے لوگ سمجھ نہیں پاتے کہ نوٹس میں کیا مانگا گیا ہے، آخری تاریخ کیا ہے اور آگے کیا کرنا ہے۔ اس لیے وہ ایجنٹوں پر انحصار کرتے ہیں، تاریخ نکل جاتی ہے، یا ایسی رقم ادا کر دیتے ہیں جو ان کے ذمے نہیں تھی۔ دھوکے باز اسی الجھن کا فائدہ اٹھانے کے لیے سرکاری نوٹس کی نقل بناتے ہیں۔</p>
      <p data-l="en">Tax notices, utility bills, CNIC procedures and rent agreements are usually written in dense English or legal language. Many people can't tell what a notice asks for, when it is due, or what to do next, so they rely on agents, miss deadlines, or pay what they don't owe. Scammers copy the look of official notices to take advantage of the same confusion.</p>
    </section>

    <section id="how">
      <h2>{bi("یہ کیسے کام کرتا ہے", "How it works")}</h2>
      <ol class="steps-list">
        <li><div class="step-text" data-l="ur"><strong>لکھیں یا پیسٹ کریں</strong> سوال لکھیں یا نوٹس کا متن پیسٹ کریں۔</div>
            <div class="step-text" data-l="en"><strong>Write or paste</strong> Ask a question or paste the text of a notice.</div></li>
        <li><div class="step-text" data-l="ur"><strong>بھیجنے سے پہلے جانچیں</strong> حقدار شناختی کارڈ، فون اور اکاؤنٹ نمبر جیسی ذاتی معلومات چھپا دیتا ہے۔ بھیجنے سے پہلے آپ خود دیکھ لیتے ہیں کہ کیا جائے گا۔</div>
            <div class="step-text" data-l="en"><strong>Review what will be sent</strong> Haqdar hides personal details such as CNIC, phone and account numbers. You see exactly what will be sent before you confirm.</div></li>
        <li><div class="step-text" data-l="ur"><strong>جواب پڑھیں</strong> آپ کو آسان زبان میں اقدامات ملتے ہیں اور ہر قدم کے ساتھ اس کا ماخذ۔ نوٹس کی صورت میں جعلی ہونے کی علامتوں کی جانچ بھی ملتی ہے۔</div>
            <div class="step-text" data-l="en"><strong>Read the answer</strong> You get steps in plain language, each linked to its source. For a notice, you also get a check for signs that it may be fake.</div></li>
      </ol>
    </section>

    <section id="privacy">
      <h2>{bi("آپ کی پرائیویسی", "Your privacy")}</h2>
      <ul class="checks">
        <li><div data-l="ur">آپ کے دستاویزات محفوظ نہیں کیے جاتے، اور آپ جو لکھتے ہیں وہ لاگ نہیں ہوتا۔</div>
            <div data-l="en">Your documents are not stored, and what you type is not logged.</div></li>
        <li><div data-l="ur">ذاتی معلومات بھیجنے سے پہلے آپ کے براؤزر میں چھپائی جاتی ہیں، اور سرور پر دوبارہ۔</div>
            <div data-l="en">Personal details are masked in your browser before sending, and again on the server.</div></li>
        <li><div data-l="ur">یہ سائٹ آپ کے براؤزر میں صرف آپ کی زبان کا انتخاب یاد رکھتی ہے۔</div>
            <div data-l="en">This site remembers only your language choice, in your own browser.</div></li>
        <li class="caveat"><div data-l="ur">چھپانے کا عمل ہر چیز نہیں پکڑتا۔ یہ شناختی کارڈ، فون، ای میل، IBAN اور لیبل والے حوالہ نمبر پکڑتا ہے، مگر نام اور پتے رہ سکتے ہیں۔ باقی ذاتی معلومات بھیجنے سے پہلے خود ہٹا دیں۔</div>
            <div data-l="en">Masking is best-effort. It catches CNIC, phone, email, IBAN and labelled reference numbers, but names and addresses can slip through. Remove anything else personal yourself before sending.</div></li>
      </ul>
    </section>

    <section id="limits">
      <h2>{bi("حدود", "What it can't do")}</h2>
      <ul class="checks">
        <li class="caveat"><div data-l="ur">یہ معلومات ہیں، قانونی مشورہ نہیں۔</div>
            <div data-l="en">It gives information, not legal advice.</div></li>
        <li class="caveat"><div data-l="ur">یہ صرف انہی موضوعات کا جواب دیتا ہے جو سرکاری ماخذ سے جانچ کر لکھے گئے ہیں۔ ہم بجلی کے بل پر اعتراض، ایف بی آر کے نوٹس، شناختی کارڈ کی خدمات اور کرایہ نامے سے شروع کر رہے ہیں۔ باقی سوالوں پر حقدار صاف بتاتا ہے کہ تصدیق نہیں ہو سکی۔</div>
            <div data-l="en">It only answers topics that have been written up and checked against official sources. We are starting with electricity bill disputes, FBR notices, CNIC services and rent agreements. For anything else, Haqdar says plainly that it couldn't verify an answer.</div></li>
        <li class="caveat"><div data-l="ur">جعلی نوٹس کی جانچ صرف انتباہی علامتیں دیکھتی ہے۔ «ممکنہ طور پر اصلی» کا مطلب تصدیق نہیں، ادائیگی سے پہلے متعلقہ دفتر سے رابطہ کریں۔</div>
            <div data-l="en">The fake-notice check only looks for warning signs. "Possibly genuine" is not a confirmation: contact the office before you pay.</div></li>
        <li class="caveat"><div data-l="ur">قوانین اور ویب سائٹس بدلتی رہتی ہیں۔ ماخذ کا لنک کھول کر خود تصدیق کریں۔</div>
            <div data-l="en">Rules and websites change. Open the source link to check for yourself.</div></li>
      </ul>
    </section>

    <section id="open-source">
      <h2>{bi("اوپن سورس", "Open source")}</h2>
      <p data-l="ur">حقدار MIT لائسنس کے تحت اوپن سورس ہے۔ ہر طریقۂ کار ایک سادہ فائل میں لکھا جاتا ہے، اس لیے رضاکار پل ریکوئسٹ کے ذریعے نیا طریقۂ کار شامل یا غلطی درست کر سکتے ہیں۔ ہر ایک میں سرکاری ماخذ کا حوالہ ضروری ہے۔</p>
      <p data-l="en">Haqdar is open source under the MIT license. Each procedure is a simple file, so volunteers can add one or fix a mistake with a pull request. Every procedure must cite an official source.</p>
      <p class="muted" data-l="ur">لوگو اور تصویروں میں اردو الفاظ Noto Nastaliq Urdu فونٹ (SIL Open Font License) سے بنائے گئے ہیں۔</p>
      <p class="muted" data-l="en">The Urdu lettering in the logo and illustrations is drawn from the Noto Nastaliq Urdu font (SIL Open Font License).</p>
      <div class="link-row">
        <a class="linkbtn solid" href="https://github.com/malaikamalik23/Haqdar" target="_blank" rel="noopener noreferrer">{bi("GitHub پر دیکھیں", "View on GitHub")}</a>
        <a class="linkbtn" href="https://github.com/malaikamalik23/Haqdar/issues" target="_blank" rel="noopener noreferrer">{bi("مسئلہ رپورٹ کریں", "Report a problem")}</a>
      </div>
    </section>

    <section id="team">
      <h2>{bi("ٹیم", "Team")}</h2>
      <ul class="team">
        <li><strong>Malaika Adnan</strong>
            <span data-l="ur">بیک اینڈ، پرائیویسی اور سیکیورٹی، اور ویب ایپ۔</span>
            <span data-l="en">Backend, privacy and security, and the web app.</span></li>
        <li><strong>Malaika Khan</strong>
            <span data-l="ur">اے آئی اور ڈیٹا سائنس: جوابات کی تلاش، دستاویز پڑھنا، جانچ، اور طریقۂ کار کے پیک۔</span>
            <span data-l="en">AI and data science: finding answers, reading documents, evaluation, and procedure packs.</span></li>
      </ul>
      <p class="muted" data-l="ur">یہ پروجیکٹ Hacktoberfest Hackathon NUST × NSTP کے لیے بنایا گیا ہے۔ کس نے کیا بنایا اس کا مکمل ریکارڈ GitHub کی کمٹ ہسٹری میں موجود ہے۔</p>
      <p class="muted" data-l="en">Built for the Hacktoberfest Hackathon NUST × NSTP. The full record of who built what is in the GitHub commit history.</p>
    </section>
  </main>'''

PAGES = {
    "index.html": page("home", "حقدار: سرکاری کاغذات آسان اردو میں", "Haqdar: official papers in plain language", home_body, csp=CSP_STATIC),
    "ask.html": page("ask", "سوال پوچھیں | حقدار", "Ask a question | Haqdar", ask_body, csp=CSP_TOOL, mode="ask", end_scripts=("app.js",)),
    "notice.html": page("notice", "نوٹس سمجھیں | حقدار", "Understand a notice | Haqdar", notice_body, csp=CSP_TOOL, mode="notice", end_scripts=("app.js",)),
    "about.html": page("about", "حقدار کے بارے میں", "About Haqdar", about_body, csp=CSP_STATIC),
}

for name, html in PAGES.items():
    (WEB / name).write_text(html, encoding="utf-8", newline="\n")
    print("wrote", name, len(html))