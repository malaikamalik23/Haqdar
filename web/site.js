"use strict";

// Shared by every page: remembers the language, builds the footer, registers the service worker.
(function () {
  var KEY = "haqdar-lang";
  var REPO = "https://github.com/malaikamalik23/Haqdar";
  var root = document.documentElement;
  var current = "ur";

  function load() {
    try {
      var v = localStorage.getItem(KEY);
      if (v === "ur" || v === "en") return v;
    } catch (e) {
      /* storage can be unavailable */
    }
    return "ur";
  }

  function save(l) {
    try {
      localStorage.setItem(KEY, l);
    } catch (e) {
      /* ignore */
    }
  }

  // Runs in <head>, so the right language and direction are set before first paint.
  function apply(l) {
    current = l;
    root.lang = l;
    root.dir = l === "ur" ? "rtl" : "ltr";
    var ur = document.getElementById("lang-ur");
    var en = document.getElementById("lang-en");
    if (ur) ur.setAttribute("aria-pressed", String(l === "ur"));
    if (en) en.setAttribute("aria-pressed", String(l === "en"));
    var b = document.body;
    if (b && b.dataset.titleUr && b.dataset.titleEn) {
      document.title = l === "ur" ? b.dataset.titleUr : b.dataset.titleEn;
    }
  }

  function setLang(l) {
    if (l === current) return;
    save(l);
    apply(l);
    document.dispatchEvent(new CustomEvent("haqdar:lang", { detail: l }));
  }

  // Both language variants are in the page; style.css shows only the matching one.
  function bi(ur, en) {
    var frag = document.createDocumentFragment();
    [["ur", ur], ["en", en]].forEach(function (p) {
      var s = document.createElement("span");
      s.setAttribute("data-l", p[0]);
      s.textContent = p[1];
      frag.appendChild(s);
    });
    return frag;
  }

  function el(tag, cls) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    return n;
  }

  function link(href, ur, en, external) {
    var a = el("a");
    a.href = href;
    if (external) {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    }
    a.appendChild(bi(ur, en));
    return a;
  }

  function column(titleUr, titleEn, links) {
    var col = el("div", "footer-col");
    var h = el("h2", "footer-title");
    h.appendChild(bi(titleUr, titleEn));
    col.appendChild(h);
    var ul = el("ul");
    links.forEach(function (a) {
      var li = el("li");
      li.appendChild(a);
      ul.appendChild(li);
    });
    col.appendChild(ul);
    return col;
  }

  function buildFooter() {
    var host = document.getElementById("site-footer");
    if (!host) return;

    var brand = el("div", "footer-col");
    var logo = el("img", "footer-logo");
    logo.src = "logo-light.svg";
    logo.alt = "حقدار Haqdar";
    logo.width = 134;
    logo.height = 51;
    var blurb = el("p");
    blurb.appendChild(bi("آپ کا حق، آسان زبان میں۔", "Your rights, in plain language."));
    var disc = el("p", "footer-small");
    disc.appendChild(bi("یہ معلومات ہیں، قانونی مشورہ نہیں۔", "Information, not legal advice."));
    brand.append(logo, blurb, disc);

    var project = el("div", "footer-col");
    var ph = el("h2", "footer-title");
    ph.appendChild(bi("یہ پروجیکٹ", "The project"));
    var pp = el("p");
    pp.textContent = "Hacktoberfest Hackathon NUST × NSTP";
    var pl = el("p");
    pl.appendChild(link("about.html#team", "ٹیم سے ملیں", "Meet the team"));
    project.append(ph, pp, pl);

    var inner = el("div", "footer-inner");
    inner.append(
      brand,
      column("صفحات", "Pages", [
        link("index.html", "مرکزی صفحہ", "Home"),
        link("ask.html", "سوال پوچھیں", "Ask a question"),
        link("notice.html", "نوٹس سمجھیں", "Understand a notice"),
        link("about.html", "ہمارے بارے میں", "About"),
      ]),
      column("اوپن سورس", "Open source", [
        link(REPO, "سورس کوڈ (GitHub)", "Source code on GitHub", true),
        link(REPO + "/blob/main/LICENSE", "MIT لائسنس", "MIT License", true),
        link(REPO + "/issues", "مسئلہ رپورٹ کریں", "Report a problem", true),
        link("about.html#privacy", "پرائیویسی", "Privacy"),
      ]),
      project
    );

    var year = new Date().getFullYear();
    var bottom = el("div", "footer-bottom");
    var p1 = el("p");
    p1.appendChild(bi("حقدار اوپن سورس (MIT) ہے۔ یہ معلومات فراہم کرتا ہے، قانونی مشورہ نہیں۔", "Haqdar is open source (MIT). It provides information, not legal advice."));
    var p2 = el("p");
    p2.appendChild(bi("© " + year + " ٹیم حقدار", "© " + year + " Haqdar team"));
    bottom.append(p1, p2);

    host.replaceChildren(inner, bottom);
  }

  function init() {
    apply(load());
    var ur = document.getElementById("lang-ur");
    var en = document.getElementById("lang-en");
    if (ur) ur.addEventListener("click", function () { setLang("ur"); });
    if (en) en.addEventListener("click", function () { setLang("en"); });
    buildFooter();
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").catch(function () {});
    }
  }

  apply(load());
  window.HaqdarLang = { get: function () { return current; } };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();