"use strict";

// Change this to your deployed backend URL (and update connect-src in ask.html and notice.html).
const API = "http://localhost:8000";
const MAX_CHARS = 4000;
const MODE = document.body.dataset.mode === "notice" ? "notice" : "ask";

// Static page text lives in the HTML (data-l spans). These are the dynamic strings.
const I18N = {
  ur: {
    progressLabel: "مراحل",
    placeholderAsk: "مثلاً: بجلی کا بل زیادہ آیا ہے، کیا کروں؟",
    counter: "{n} / {max}",
    maskedSome: "{n} ذاتی معلومات چھپائی گئیں۔",
    maskedNone: "کوئی ذاتی معلومات نہیں ملیں۔ بھیجنے سے پہلے خود بھی دیکھ لیں۔",
    statusEnter: "پہلے متن لکھیں۔",
    statusLong: "متن بہت لمبا ہے۔ {max} حروف تک رکھیں۔",
    statusWait: "جواب تیار ہو رہا ہے…",
    statusError: "سرور سے رابطہ نہیں ہو سکا۔ انٹرنیٹ دیکھیں اور دوبارہ «بھیجیں» دبائیں۔",
    resultLabel: "جواب",
    asked: "آپ کا سوال:",
    verdictGenuine: "ممکنہ طور پر اصلی",
    verdictSuspicious: "مشکوک: احتیاط کریں",
    verdictUnclear: "واضح نہیں",
    verdictNote: "یہ تصدیق نہیں ہے۔ ادائیگی سے پہلے متعلقہ دفتر سے رابطہ کریں۔",
    noticeDetails: "نوٹس کی تفصیل",
    fieldSender: "بھیجنے والا",
    fieldDate: "تاریخ",
    fieldDeadline: "آخری تاریخ",
    fieldAmount: "رقم",
    fieldDemand: "مطالبہ",
    stepsHeading: "اگلے اقدامات",
    docsHeading: "درکار کاغذات",
    topicsHeading: "ہم ان موضوعات میں مدد کر سکتے ہیں",
    sourcesHeading: "ماخذ",
    confidence: "اعتماد",
    legalNote: "یہ معلومات ہیں، قانونی مشورہ نہیں۔ اہم معاملات میں متعلقہ دفتر سے رابطہ کریں۔",
    abstainTitle: "اس کی تصدیق نہیں ہو سکی",
    defaultAbstain: "اس سوال کا جواب تصدیق شدہ ماخذ سے نہیں دیا جا سکتا۔ براہ کرم متعلقہ دفتر سے رابطہ کریں۔",
    urduOnlyNote: "",
    btnCopy: "جواب کاپی کریں",
    copied: "کاپی ہو گیا",
    btnNew: "نیا سوال پوچھیں",
  },
  en: {
    progressLabel: "Progress",
    placeholderAsk: "e.g. My electricity bill is too high. What should I do?",
    counter: "{n} / {max}",
    maskedSome: "{n} personal detail(s) hidden.",
    maskedNone: "No personal details found. Please double-check before sending.",
    statusEnter: "Write something first.",
    statusLong: "The text is too long. Keep it under {max} characters.",
    statusWait: "Preparing your answer…",
    statusError: "Could not reach the server. Check your connection and press Send again.",
    resultLabel: "Answer",
    asked: "You asked:",
    verdictGenuine: "Possibly genuine",
    verdictSuspicious: "Suspicious: be careful",
    verdictUnclear: "Unclear",
    verdictNote: "This is not a confirmation. Contact the relevant office before paying.",
    noticeDetails: "Notice details",
    fieldSender: "Sender",
    fieldDate: "Date",
    fieldDeadline: "Deadline",
    fieldAmount: "Amount",
    fieldDemand: "Demand",
    stepsHeading: "What to do next",
    docsHeading: "Documents you will need",
    topicsHeading: "Topics we can help with",
    sourcesHeading: "Sources",
    confidence: "Confidence",
    legalNote: "This is information, not legal advice. For important matters, contact the relevant office.",
    abstainTitle: "We couldn't verify this",
    defaultAbstain: "This question cannot be answered from a verified source. Please contact the relevant office.",
    urduOnlyNote: "This answer is currently available in Urdu only.",
    btnCopy: "Copy answer",
    copied: "Copied",
    btnNew: "Ask something else",
  },
};

// The sample notice uses fake numbers only. It also shows the masking and the verdict.
const EXAMPLES = {
  ur: {
    ask: [
      "میرا میٹر تیز چل رہا ہے، کیا کروں؟",
      "ایف بی آر کا نوٹس ملا ہے، کیا کروں؟",
      "شناختی کارڈ کی تجدید کیسے کروں؟",
      "مالک مکان کرایہ نہیں لے رہا، کیا کروں؟",
    ],
    sample: {
      label: "نمونہ نوٹس آزمائیں",
      text: "FBR Notice: an amount of Rs 5000 is outstanding. Consumer No: 12345678901234. Pay by 30 November 2026 using Easypaisa, or call 0300-1234567.",
    },
  },
  en: {
    ask: [
      "My electricity meter is running fast, what should I do?",
      "I got a notice from FBR, how do I reply to it?",
      "How do I renew my CNIC online?",
      "Does my rent agreement in Islamabad need to be in writing?",
    ],
    sample: {
      label: "Try a sample notice",
      text: "FBR Notice: an amount of Rs 5000 is outstanding. Consumer No: 12345678901234. Pay by 30 November 2026 using Easypaisa, or call 0300-1234567.",
    },
  },
};

// Topic tiles on the home page link here, e.g. ask.html?topic=fbr
const TOPICS = { electricity: 0, fbr: 1, cnic: 2, rent: 3 };

// Client-side masking mirrors the server-side redactor, so identifiers can be
// hidden before anything leaves the browser. The server redacts again anyway.
const PATTERNS = [
  ["IBAN", /\bPK\d{2}[A-Z]{4}\d{16}\b/g],
  ["EMAIL", /[\w.+-]+@[\w-]+\.[\w.-]+/g],
  ["CNIC", /\b\d{5}-?\d{7}-?\d\b/g],
  ["PHONE", /(?<!\d)(?:\+92|0092|0)[-\s]?3\d{2}[-\s]?\d{7}(?!\d)/g],
];
const LABELLED = /\b((?:reference|ref|consumer|customer|account|meter|challan|ntn)\s*(?:no\.?|number|#|id)?\s*[:\-]?\s*)((?=[A-Z0-9\-/]*\d)[A-Z0-9][A-Z0-9\-/]{5,})/gi;
const PLACEHOLDER_RE = /(\[(?:IBAN|EMAIL|CNIC|PHONE|REF)_\d+\])/;

const VERDICT = {
  genuine: ["verdictGenuine", "ok", "✓"],
  suspicious: ["verdictSuspicious", "bad", "!"],
  unclear: ["verdictUnclear", "warn", "?"],
};
const FIELD_KEYS = {
  sender: "fieldSender",
  date: "fieldDate",
  deadline: "fieldDeadline",
  amount: "fieldAmount",
  demand: "fieldDemand",
};

const $ = (id) => document.getElementById(id);
let lang = (window.HaqdarLang && window.HaqdarLang.get()) || "ur";
let pending = null; // { text (masked), count }
let lastResult = null; // { data, asked }
let status = null; // { kind, key, vars }
let busy = false;
let topicIndex = null;
let prefilled = null;

function t(key, vars) {
  let s = (I18N[lang] && I18N[lang][key]) ?? I18N.ur[key] ?? key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace("{" + k + "}", String(v));
  return s;
}

function maskText(text) {
  const seen = new Map();
  const counters = {};
  let count = 0;
  const placeholder = (label, val) => {
    if (seen.has(val)) return seen.get(val);
    counters[label] = (counters[label] || 0) + 1;
    const ph = `[${label}_${counters[label]}]`;
    seen.set(val, ph);
    count += 1;
    return ph;
  };
  let out = text;
  for (const [label, re] of PATTERNS) out = out.replace(re, (m) => placeholder(label, m));
  out = out.replace(LABELLED, (_, lead, val) => lead + placeholder("REF", val));
  return { text: out, count };
}

// Every piece of server data goes through textContent, never innerHTML.
function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (cls) node.className = cls;
  return node;
}

// dir="auto" lets Urdu server text display right-to-left inside an English page.
function autoDir(node) {
  node.dir = "auto";
  return node;
}

function safeUrl(u) {
  try {
    const p = new URL(u);
    return p.protocol === "https:" || p.protocol === "http:" ? p.href : null;
  } catch {
    return null;
  }
}

// Picks the English text when asked for English and available, otherwise Urdu.
function pick(obj, base) {
  if (!obj) return { text: "", fallback: false };
  if (lang === "en" && obj[base + "_en"]) return { text: obj[base + "_en"], fallback: false };
  const ur = obj[base + "_ur"];
  return { text: ur || "", fallback: lang === "en" && Boolean(ur) };
}

function scrollBehavior() {
  return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
}

/* ---------- status, steps, views ---------- */

function showStatus(kind, key, vars) {
  const box = $("status");
  box.replaceChildren();
  status = kind ? { kind, key, vars } : null;
  if (!kind) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  box.className = "status" + (kind === "error" ? " error" : "");
  box.setAttribute("role", kind === "error" ? "alert" : "status");
  if (kind === "loading") {
    const sp = el("span", null, "spinner");
    sp.setAttribute("aria-hidden", "true");
    box.append(sp);
  }
  box.append(el("span", t(key, vars)));
}

function setStep(n) {
  [1, 2, 3].forEach((i) => {
    const li = $("step-" + i);
    li.classList.toggle("is-current", i === n);
    li.classList.toggle("is-done", i < n);
    if (i === n) li.setAttribute("aria-current", "step");
    else li.removeAttribute("aria-current");
  });
}

function showView(name) {
  $("compose").hidden = name !== "compose";
  $("preview").hidden = name !== "preview";
  $("result").hidden = name !== "result";
  setStep(name === "compose" ? 1 : name === "preview" ? 2 : 3);
}

/* ---------- compose: chips, counter, topic prefill ---------- */

function fill(text) {
  const ta = $("q");
  ta.value = text;
  updateCounter();
  ta.focus();
}

function buildChips() {
  const ex = EXAMPLES[lang];
  const box = $("chips");
  box.replaceChildren();
  if (MODE === "ask") {
    for (const text of ex.ask) {
      const b = el("button", text, "chip");
      b.type = "button";
      b.addEventListener("click", () => {
        prefilled = null;
        fill(text);
      });
      box.append(b);
    }
  } else {
    const b = el("button", ex.sample.label, "chip sample");
    b.type = "button";
    b.addEventListener("click", () => fill(ex.sample.text));
    box.append(b);
  }
}

function updateCounter() {
  $("count").textContent = t("counter", { n: $("q").value.length, max: MAX_CHARS });
}

function readTopic() {
  if (MODE !== "ask") return;
  const key = new URLSearchParams(location.search).get("topic");
  if (key && Object.prototype.hasOwnProperty.call(TOPICS, key)) topicIndex = TOPICS[key];
}

// Fills the question from a topic tile. Follows a language switch only while the box is untouched.
function applyTopicText() {
  if (topicIndex === null) return;
  const ta = $("q");
  if (ta.value === "" || ta.value === prefilled) {
    prefilled = EXAMPLES[lang].ask[topicIndex];
    ta.value = prefilled;
    updateCounter();
  }
}

/* ---------- language ---------- */

function applyLang() {
  for (const n of document.querySelectorAll("[data-i18n-placeholder]")) {
    n.placeholder = t(n.dataset.i18nPlaceholder);
  }
  for (const n of document.querySelectorAll("[data-i18n-label]")) {
    n.setAttribute("aria-label", t(n.dataset.i18nLabel));
  }
  buildChips();
  applyTopicText();
  updateCounter();
  if (pending) renderPreview();
  if (status) showStatus(status.kind, status.key, status.vars);
  if (lastResult) renderResult(lastResult, false);
}

/* ---------- review and send ---------- */

function renderPreview() {
  const box = $("preview-text");
  box.replaceChildren();
  for (const part of pending.text.split(PLACEHOLDER_RE)) {
    if (!part) continue;
    if (PLACEHOLDER_RE.test(part)) box.append(el("mark", part));
    else box.append(document.createTextNode(part));
  }
  $("mask-summary").textContent = pending.count
    ? t("maskedSome", { n: pending.count })
    : t("maskedNone");
}

function review() {
  const text = $("q").value.trim();
  if (!text) return showStatus("error", "statusEnter");
  if (text.length > MAX_CHARS) return showStatus("error", "statusLong", { max: MAX_CHARS });
  showStatus(null);
  const masked = maskText(text);
  pending = { text: masked.text, count: masked.count };
  renderPreview();
  showView("preview");
  $("preview-title").focus();
}

function backToEdit() {
  pending = null;
  showStatus(null);
  showView("compose");
  $("q").focus();
}

async function send() {
  if (!pending || busy) return;
  busy = true;
  $("btn-confirm").disabled = true;
  $("btn-cancel").disabled = true;
  showStatus("loading", "statusWait");
  const { text } = pending;
  try {
    const path = MODE === "ask" ? "/ask" : "/analyze";
    // "en" makes the API return both Urdu and English, so switching language needs no new request.
    const body = MODE === "ask" ? { question: text, lang: "en" } : { text, lang: "en" };
    const res = await fetch(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("bad status");
    const data = await res.json();
    lastResult = { data, asked: text };
    $("q").value = "";
    prefilled = null;
    topicIndex = null;
    updateCounter();
    pending = null;
    showStatus(null);
    renderResult(lastResult, true);
  } catch {
    showStatus("error", "statusError");
  } finally {
    busy = false;
    $("btn-confirm").disabled = false;
    $("btn-cancel").disabled = false;
  }
}

function newQuestion() {
  lastResult = null;
  pending = null;
  $("result").replaceChildren();
  showStatus(null);
  showView("compose");
  $("q").focus();
}

/* ---------- result ---------- */

function renderVerdict(box, verdict, copy, animate) {
  if (!verdict) return;
  const [titleKey, cls, icon] = VERDICT[verdict.label] || VERDICT.unclear;
  const stamp = el("div", null, "stamp " + cls + (animate ? " pop" : ""));
  const ic = el("span", icon, "stamp-icon");
  ic.setAttribute("aria-hidden", "true");
  stamp.append(ic, el("span", t(titleKey)));
  box.append(stamp);
  copy.push(t(titleKey));
  if (Array.isArray(verdict.reasons) && verdict.reasons.length) {
    const ul = el("ul", null, "reasons");
    for (const r of verdict.reasons) ul.append(autoDir(el("li", r)));
    box.append(ul);
  }
  box.append(el("p", t("verdictNote"), "muted"));
}

function renderFields(box, fields, fieldsUr) {
  if (!fields) return;
  const rows = Object.keys(FIELD_KEYS).filter((k) => fields[k]);
  if (rows.length === 0) return;
  box.append(el("h2", t("noticeDetails")));
  const dl = el("dl", null, "fields");
  for (const k of rows) {
    dl.append(el("dt", t(FIELD_KEYS[k])));
    const urdu = lang === "ur" && fieldsUr ? fieldsUr[k + "_ur"] : "";
    dl.append(autoDir(el("dd", urdu || fields[k])));
  }
  box.append(dl);
}

function renderSteps(box, steps, sources, flags, copy) {
  if (!Array.isArray(steps) || steps.length === 0) return;
  box.append(el("h2", t("stepsHeading")));
  const ol = el("ol", null, "steps-list");
  steps.forEach((s, idx) => {
    const picked = pick(s, "text");
    if (picked.fallback) flags.fallback = true;
    const li = el("li");
    const text = autoDir(el("span", picked.text, "step-text"));
    const i = sources.findIndex((x) => x.id === s.source_id);
    if (i >= 0) {
      const a = el("a", `[${i + 1}]`, "cite");
      a.href = "#src-" + (i + 1);
      text.append(a);
    }
    li.append(text);
    ol.append(li);
    copy.push(`${idx + 1}. ${picked.text}`);
  });
  box.append(ol);
}

function renderDocuments(box, docs, copy) {
  if (!Array.isArray(docs) || docs.length === 0) return;
  box.append(el("h2", t("docsHeading")));
  copy.push(t("docsHeading") + ":");
  const ul = el("ul", null, "checks");
  for (const d of docs) {
    ul.append(autoDir(el("li", d)));
    copy.push("- " + d);
  }
  box.append(ul);
}

function renderTopics(box, procs) {
  if (!Array.isArray(procs) || procs.length === 0) return;
  box.append(el("h2", t("topicsHeading")));
  const ul = el("ul", null, "checks");
  for (const p of procs) {
    const title = lang === "en" ? p.title_en || p.title_ur : p.title_ur || p.title_en;
    ul.append(autoDir(el("li", title)));
  }
  box.append(ul);
}

function renderSources(box, sources, copy) {
  if (sources.length === 0) return;
  const details = el("details", null, "sources");
  details.open = true;
  details.append(el("summary", `${t("sourcesHeading")} (${sources.length})`));
  const ul = el("ul");
  sources.forEach((s, i) => {
    const li = el("li");
    li.id = "src-" + (i + 1);
    li.append(el("span", i + 1, "src-n"));
    const body = el("div", null, "src-body");
    const href = safeUrl(s.url);
    if (href) {
      const a = el("a", href);
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.dir = "ltr";
      body.append(a);
      copy.push(`[${i + 1}] ${href}`);
    } else {
      body.append(el("span", s.url || ""));
    }
    if (s.quote) body.append(autoDir(el("blockquote", s.quote)));
    li.append(body);
    ul.append(li);
  });
  details.append(ul);
  box.append(details);
}

function addActions(box, copy) {
  const row = el("div", null, "actions");
  if (navigator.clipboard && copy.length) {
    const b = el("button", t("btnCopy"), "ghost");
    b.type = "button";
    b.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(copy.join("\n"));
        b.textContent = t("copied");
        setTimeout(() => {
          b.textContent = t("btnCopy");
        }, 2000);
      } catch {
        /* clipboard can be blocked */
      }
    });
    row.append(b);
  }
  const again = el("button", t("btnNew"), "primary");
  again.type = "button";
  again.addEventListener("click", newQuestion);
  row.append(again);
  box.append(row);
}

function renderResult({ data, asked }, fresh) {
  const box = $("result");
  box.replaceChildren();
  const copy = [];
  const flags = { fallback: false };
  const sources = Array.isArray(data.sources) ? data.sources : [];

  const askedLine = el("p", null, "asked");
  askedLine.append(el("strong", t("asked") + " "));
  askedLine.append(autoDir(el("span", asked.length > 160 ? asked.slice(0, 160) + "…" : asked)));
  box.append(askedLine);

  if (MODE === "notice") {
    renderVerdict(box, data.verdict, copy, fresh);
    renderFields(box, data.fields, data.fields_ur);
  }

  const lead = pick(data, MODE === "ask" ? "answer" : "explanation");
  if (lead.fallback) flags.fallback = true;
  if (data.abstained) {
    const a = autoDir(el("div", null, "abstain"));
    a.append(el("strong", t("abstainTitle")));
    a.append(el("span", lead.text || t("defaultAbstain")));
    box.append(a);
    renderTopics(box, data.available_procedures);
  } else {
    if (lead.text) {
      box.append(autoDir(el("p", lead.text, "lead")));
      copy.push(lead.text);
    }
    renderSteps(box, data.steps, sources, flags, copy);
    renderDocuments(box, data.documents_needed, copy);
    renderSources(box, sources, copy);
    if (typeof data.confidence === "number") {
      box.append(el("p", `${t("confidence")}: ${Math.round(data.confidence * 100)}%`, "muted"));
    }
  }
  if (flags.fallback && t("urduOnlyNote")) askedLine.after(el("p", t("urduOnlyNote"), "muted"));
  box.append(el("p", t("legalNote"), "muted"));
  addActions(box, copy);

  showView("result");
  if (fresh) {
    box.scrollIntoView({ behavior: scrollBehavior(), block: "start" });
    box.focus({ preventScroll: true });
  }
}

/* ---------- events ---------- */

document.addEventListener("haqdar:lang", (e) => {
  lang = e.detail === "en" ? "en" : "ur";
  applyLang();
});
$("q").addEventListener("input", updateCounter);
$("q").addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") review();
});
$("btn-review").addEventListener("click", review);
$("btn-confirm").addEventListener("click", send);
$("btn-cancel").addEventListener("click", backToEdit);

readTopic();
applyLang();
showView("compose");