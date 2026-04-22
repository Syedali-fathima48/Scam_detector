# -*- coding: utf-8 -*-
"""
============================================================
  🔐 Cybersecurity Safety Assistant — Single-file Flask App
  🤖 Powered by Google Gemini AI (google-genai SDK)
============================================================

SETUP (run these once):
    pip install flask google-genai

SET YOUR API KEY:
    Windows CMD:   set GOOGLE_API_KEY=AIza...your_key
    Mac / Linux:   export GOOGLE_API_KEY=AIza...your_key
    OR just paste your key on line 30 below.

RUN:
    python app.py
    Then open → http://localhost:5000
"""

from flask import Flask, request, jsonify
from google import genai
from google.genai import types
import sys, os, time

app = Flask(__name__)

# ─── 🔑 PASTE YOUR KEY HERE (or use env var) ──────────────
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")  # 👈 e.g. "AIzaSy..."
# ──────────────────────────────────────────────────────────

# Models tried in order when one is overloaded (503 / 429)
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]
RETRY_DELAYS = [1, 2, 4]   # seconds between retries on the SAME model

SUPPORTED_LANGUAGES = {
    # Indian Languages
    "english":    "English",
    "tamil":      "Tamil",
    "hindi":      "Hindi",
    "telugu":     "Telugu",
    "kannada":    "Kannada",
    "malayalam":  "Malayalam",
    "bengali":    "Bengali",
    "marathi":    "Marathi",
    "gujarati":   "Gujarati",
    "punjabi":    "Punjabi",
    "odia":       "Odia",
    "urdu":       "Urdu",
    # International Languages
    "french":     "French",
    "spanish":    "Spanish",
    "arabic":     "Arabic",
    "chinese":    "Chinese",
    "japanese":   "Japanese",
    "korean":     "Korean",
    "german":     "German",
    "portuguese": "Portuguese",
    "russian":    "Russian",
    "turkish":    "Turkish",
    "custom":     "custom",  # handled separately
}

# ─── HTML (served inline so there are zero CORS / path issues) ───
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>CyberShield — Safety Analyzer</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet"/>
<style>
  :root{--bg:#0a0c10;--surface:#111318;--border:#1e2230;--accent:#00e5ff;--safe:#00e676;--warn:#ffea00;--danger:#ff3d00;--illegal:#ea00ff;--text:#e8eaf6;--muted:#5c6480;--mono:'Space Mono',monospace;--sans:'DM Sans',sans-serif}
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:48px 20px 80px;position:relative;overflow-x:hidden}
  body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,229,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}
  body::after{content:'';position:fixed;top:-200px;left:50%;transform:translateX(-50%);width:600px;height:600px;background:radial-gradient(circle,rgba(0,229,255,.06) 0%,transparent 70%);pointer-events:none;z-index:0}
  .wrapper{position:relative;z-index:1;width:100%;max-width:760px}
  header{text-align:center;margin-bottom:48px;animation:fadeDown .6s ease both}
  .logo-row{display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px}
  .shield-icon{width:48px;height:48px;filter:drop-shadow(0 0 12px var(--accent))}
  h1{font-family:var(--mono);font-size:clamp(1.6rem,4vw,2.4rem);letter-spacing:-1px;color:var(--accent);text-shadow:0 0 24px rgba(0,229,255,.4)}
  .tagline{font-size:.9rem;color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:32px;margin-bottom:28px;box-shadow:0 0 40px rgba(0,0,0,.5);animation:fadeUp .6s ease both}

  /* ── Language Selector ── */
  .lang-section{margin-bottom:24px}
  .lang-section-label{font-family:var(--mono);font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
  .lang-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:4px}
  .lang-btn{font-family:var(--mono);font-size:.73rem;padding:5px 13px;border:1px solid var(--border);border-radius:999px;background:transparent;color:var(--muted);cursor:pointer;transition:all .2s;letter-spacing:.04em;white-space:nowrap}
  .lang-btn:hover{border-color:var(--accent);color:var(--accent)}
  .lang-btn.active{background:var(--accent);border-color:var(--accent);color:var(--bg);box-shadow:0 0 14px rgba(0,229,255,.3);font-weight:700}
  .lang-btn.custom-btn{border-style:dashed}
  .lang-btn.custom-btn.active{background:transparent;color:var(--accent);font-weight:700}

  /* custom input row */
  .custom-row{display:flex;align-items:center;gap:10px;margin-top:10px;max-width:360px;transition:all .3s}
  .custom-row input{flex:1;background:rgba(0,0,0,.3);border:1px solid var(--accent);border-radius:8px;color:var(--text);font-family:var(--mono);font-size:.82rem;padding:8px 12px;outline:none}
  .custom-row input::placeholder{color:var(--muted)}
  .custom-row input:focus{box-shadow:0 0 0 3px rgba(0,229,255,.1)}
  .custom-row .set-btn{font-family:var(--mono);font-size:.72rem;padding:8px 14px;background:var(--accent);border:none;border-radius:8px;color:var(--bg);cursor:pointer;font-weight:700;white-space:nowrap;letter-spacing:.06em}
  .custom-row .set-btn:hover{box-shadow:0 0 12px rgba(0,229,255,.4)}
  .custom-tag{font-family:var(--mono);font-size:.72rem;padding:5px 12px;background:rgba(0,229,255,.08);border:1px solid var(--accent);border-radius:999px;color:var(--accent);display:inline-flex;align-items:center;gap:8px}
  .custom-tag .remove{cursor:pointer;opacity:.6;font-size:.9rem;line-height:1}
  .custom-tag .remove:hover{opacity:1}

  label{display:block;font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
  textarea{width:100%;min-height:140px;background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:10px;color:var(--text);font-family:var(--mono);font-size:.88rem;line-height:1.6;padding:16px;resize:vertical;outline:none;transition:border-color .2s,box-shadow .2s}
  textarea::placeholder{color:var(--muted)}
  textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,229,255,.1)}
  .btn-analyze{margin-top:20px;width:100%;padding:16px;font-family:var(--mono);font-size:.9rem;letter-spacing:.1em;text-transform:uppercase;background:var(--accent);color:var(--bg);border:none;border-radius:10px;cursor:pointer;font-weight:700;transition:transform .15s,box-shadow .2s;box-shadow:0 0 24px rgba(0,229,255,.25)}
  .btn-analyze:hover{transform:translateY(-2px);box-shadow:0 0 36px rgba(0,229,255,.45)}
  .btn-analyze:active{transform:translateY(0)}
  .btn-analyze:disabled{opacity:.5;cursor:not-allowed;transform:none}
  .spinner{display:none;width:20px;height:20px;border:2px solid rgba(0,229,255,.3);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;margin:0 auto}
  .btn-analyze.loading .btn-label{display:none}
  .btn-analyze.loading .spinner{display:block}
  #result-panel{display:none;animation:fadeUp .5s ease both}
  .result-header{display:flex;align-items:center;gap:12px;margin-bottom:20px}
  .badge{font-family:var(--mono);font-size:.75rem;font-weight:700;letter-spacing:.1em;padding:5px 14px;border-radius:999px;text-transform:uppercase}
  .badge-SAFE{background:rgba(0,230,118,.15);color:var(--safe);border:1px solid var(--safe)}
  .badge-SCAM{background:rgba(255,61,0,.15);color:var(--danger);border:1px solid var(--danger)}
  .badge-UNOFFICIAL{background:rgba(255,234,0,.15);color:var(--warn);border:1px solid var(--warn)}
  .badge-ILLEGAL,.badge-DANGEROUS{background:rgba(234,0,255,.15);color:var(--illegal);border:1px solid var(--illegal)}
  .badge-UNKNOWN{background:rgba(92,100,128,.15);color:var(--muted);border:1px solid var(--muted)}
  .result-body{background:rgba(0,0,0,.25);border:1px solid var(--border);border-radius:10px;padding:24px;font-family:var(--mono);font-size:.83rem;line-height:1.85;white-space:pre-wrap;word-break:break-word;color:var(--text)}
  .line-safe{color:var(--safe)}.line-scam,.line-danger{color:var(--danger)}.line-warn{color:var(--warn)}.line-illegal{color:var(--illegal)}.line-key{color:var(--accent)}.line-advice{color:#b0bec5}
  .error-msg{background:rgba(255,61,0,.1);border:1px solid var(--danger);border-radius:10px;padding:16px 20px;color:var(--danger);font-family:var(--mono);font-size:.85rem;display:none;margin-bottom:16px}
  footer{margin-top:48px;font-size:.75rem;color:var(--muted);text-align:center;font-family:var(--mono)}
  @keyframes fadeDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:none}}
  @keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
  @keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="wrapper">
  <header>
    <div class="logo-row">
      <svg class="shield-icon" viewBox="0 0 48 48" fill="none">
        <path d="M24 4L8 10V22C8 31.94 15.06 41.22 24 44C32.94 41.22 40 31.94 40 22V10L24 4Z" fill="rgba(0,229,255,.08)" stroke="#00e5ff" stroke-width="1.5"/>
        <path d="M17 24l5 5 9-9" stroke="#00e5ff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <h1>CyberShield</h1>
    </div>
    <p class="tagline">AI-Powered Scam &amp; Threat Detector</p>
  </header>

  <div class="card">
    <!-- ── Language Picker ── -->
    <div class="lang-section">
      <div class="lang-section-label">Response Language</div>
      <div class="lang-row">
        <button class="lang-btn active" data-lang="english">English</button>
        <button class="lang-btn" data-lang="tamil">Tamil</button>
        <button class="lang-btn" data-lang="hindi">Hindi</button>
        <button class="lang-btn" data-lang="malayalam">Malayalam</button>
        <button class="lang-btn" data-lang="telugu">Telugu</button>
        <button class="lang-btn custom-btn" id="custom-toggle-btn" data-lang="custom" onclick="toggleCustomInput()">Others ▾</button>
        <span id="custom-active-tag" style="display:none"></span>
      </div>
      <div class="custom-row" id="custom-row" style="display:none">
        <input type="text" id="custom-lang-input" placeholder="e.g. Kannada, French, Arabic…" maxlength="40"/>
        <button class="set-btn" onclick="setCustomLanguage()">Set</button>
      </div>
    </div>

    <label for="input-text">Paste message / link / UPI ID / email</label>
    <textarea id="input-text" placeholder="e.g. https://sbi-reward.xyz/claim  or  UPI: 9876543210@ybl  or paste a suspicious WhatsApp message…"></textarea>
    <button class="btn-analyze" id="analyze-btn" onclick="runAnalysis()">
      <span class="btn-label">🔍 &nbsp;Analyze Now</span>
      <span class="spinner"></span>
    </button>
  </div>

  <div class="error-msg" id="error-msg"></div>

  <div class="card" id="result-panel">
    <div class="result-header">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L4 5v7c0 5 3.53 9.61 8 11 4.47-1.39 8-6 8-11V5L12 2Z" stroke="#00e5ff" stroke-width="1.8" fill="none"/>
      </svg>
      <span style="font-family:var(--mono);font-size:.8rem;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;">Analysis Result</span>
      <span class="badge" id="classification-badge"></span>
    </div>
    <div class="result-body" id="result-body"></div>
  </div>

  <footer>Powered by Google Gemini 2.5 Flash · Stay safe online 🔐</footer>
</div>

<script>
  let selectedLang  = "english";
  let customLangVal = "";

  document.querySelectorAll(".lang-btn:not(.custom-btn)").forEach(btn => {
    btn.addEventListener("click", () => selectLang(btn.dataset.lang, btn));
  });

  function selectLang(key, clickedBtn) {
    document.querySelectorAll(".lang-btn:not(.custom-btn)").forEach(b => b.classList.remove("active"));
    document.getElementById("custom-toggle-btn").classList.remove("active");
    document.getElementById("custom-active-tag").style.display = "none";
    document.getElementById("custom-row").style.display = "none";
    customLangVal = "";
    if (clickedBtn) clickedBtn.classList.add("active");
    selectedLang = key;
  }

  function toggleCustomInput() {
    const row = document.getElementById("custom-row");
    const isOpen = row.style.display !== "none";
    if (isOpen) {
      row.style.display = "none";
      if (!customLangVal) selectLang("english",
        document.querySelector('.lang-btn[data-lang="english"]'));
    } else {
      row.style.display = "flex";
      document.getElementById("custom-lang-input").focus();
    }
  }

  function setCustomLanguage() {
    const input = document.getElementById("custom-lang-input");
    const val   = input.value.trim();
    if (!val) { input.focus(); return; }
    customLangVal = val;
    selectedLang  = "custom";
    document.querySelectorAll(".lang-btn:not(.custom-btn)").forEach(b => b.classList.remove("active"));
    document.getElementById("custom-toggle-btn").classList.add("active");
    const tag = document.getElementById("custom-active-tag");
    tag.style.display = "inline-flex";
    tag.innerHTML = `<span class="custom-tag">${escHtml(val)} <span class="remove" title="Remove" onclick="removeCustomLang()">✕</span></span>`;
    document.getElementById("custom-row").style.display = "none";
    input.value = "";
  }

  function removeCustomLang() {
    customLangVal = "";
    document.getElementById("custom-active-tag").style.display = "none";
    document.getElementById("custom-toggle-btn").classList.remove("active");
    const engBtn = document.querySelector('.lang-btn[data-lang="english"]');
    engBtn.classList.add("active");
    selectedLang = "english";
  }

  document.getElementById("custom-lang-input").addEventListener("keydown", e => {
    if (e.key === "Enter") setCustomLanguage();
    if (e.key === "Escape") toggleCustomInput();
  });

  async function runAnalysis() {
    const text  = document.getElementById("input-text").value.trim();
    const btn   = document.getElementById("analyze-btn");
    const errEl = document.getElementById("error-msg");
    const panel = document.getElementById("result-panel");

    errEl.style.display = "none";
    panel.style.display = "none";

    if (!text) { showError("⚠️  Please enter something to analyze."); return; }

    const langToSend  = selectedLang === "custom" ? "custom" : selectedLang;
    const customValue = selectedLang === "custom" ? customLangVal : "";

    btn.classList.add("loading");
    btn.disabled = true;

    try {
      const res  = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: langToSend, custom_language: customValue }),
      });
      const data = await res.json();
      if (data.error) showError("❌  " + data.error);
      else renderResult(data.result);
    } catch (err) {
      showError("❌  Request failed: " + err.message);
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  }

  document.getElementById("input-text").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runAnalysis();
  });

  function renderResult(raw) {
    const classMatch     = raw.match(/Classification:\s*(.+)/i);
    const classification = classMatch ? classMatch[1].trim().toUpperCase() : "UNKNOWN";
    const badge = document.getElementById("classification-badge");
    badge.textContent = classification;
    badge.className   = "badge badge-" + getBadgeClass(classification);

    const html = raw.split("\n").map(line => {
      const up = line.toUpperCase();
      let cls = "";
      if (/^Classification:/i.test(line)) {
        cls = up.includes("SAFE") && !up.includes("UNSAFE") ? "line-safe"
            : up.includes("SCAM")       ? "line-scam"
            : up.includes("UNOFFICIAL") ? "line-warn"
            : (up.includes("ILLEGAL") || up.includes("DANGEROUS")) ? "line-illegal"
            : "line-key";
      } else if (/^Risk Level:/i.test(line)) {
        cls = up.includes("LOW") ? "line-safe" : up.includes("MEDIUM") ? "line-warn" : "line-scam";
      } else if (/^(Explanation|Official|Why It Is)/i.test(line)) {
        cls = "line-key";
      } else if (/^Safety Advice:/i.test(line)) {
        cls = "line-key";
      } else if (/^\s+\d+\./i.test(line)) {
        cls = "line-advice";
      }
      return cls ? `<span class="${cls}">${escHtml(line)}</span>` : escHtml(line);
    });

    document.getElementById("result-body").innerHTML = html.join("\n");
    const panel = document.getElementById("result-panel");
    panel.style.display = "block";
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function getBadgeClass(c) {
    if (c.includes("SAFE") && !c.includes("UNSAFE")) return "SAFE";
    if (c.includes("SCAM"))       return "SCAM";
    if (c.includes("UNOFFICIAL")) return "UNOFFICIAL";
    if (c.includes("ILLEGAL") || c.includes("DANGEROUS")) return "ILLEGAL";
    return "UNKNOWN";
  }

  function showError(msg) {
    const el = document.getElementById("error-msg");
    el.textContent = msg;
    el.style.display = "block";
  }

  function escHtml(s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
# 🌐 ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return HTML


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body."}), 400

    user_text       = data.get("text", "").strip()
    language_key    = data.get("language", "english").strip().lower()
    custom_language = data.get("custom_language", "").strip()

    if language_key == "custom":
        language = custom_language if custom_language else "English"
    else:
        language = SUPPORTED_LANGUAGES.get(language_key, language_key.capitalize() or "English")

    if not user_text:
        return jsonify({"error": "Please provide some text to analyze."})

    api_key = GOOGLE_API_KEY.strip()
    if not api_key:
        return jsonify({
            "error": "Google API key not set. Get a free key at https://aistudio.google.com/app/apikey "
                     "then paste it in app.py on line 30."
        })

    client = genai.Client(api_key=api_key)
    prompt = f"""You are a professional Cybersecurity Safety Assistant AI.
YOU MUST REPLY ENTIRELY IN {language.upper()}. Every single word of your response must be in {language}. Do NOT use English if {language} is not English.

Analyze the following input and respond STRICTLY in this exact format — no extra text before or after:

Classification: <SAFE | SCAM | UNOFFICIAL | ILLEGAL / DANGEROUS>
Risk Level: <Low | Medium | High | Critical>
Explanation: <Simple 2-sentence explanation for normal users in {language}>
Official/Safe Alternative: <Name + exact URL of the real official website, or N/A>
Why It Is Suspicious: <1-2 sentences explaining the specific red flags>
Safety Advice:
  1. <First action>
  2. <Second action>
  3. <Third action>

RULES:
- Understand input in any language (Hindi, Tamil, English, etc.)
- Always respond ONLY in {language} — this is mandatory
- For SCAM entries, always provide the real official website URL
- Be strict about safety; do NOT encourage clicking suspicious links
- Warn clearly if SCAM or ILLEGAL / DANGEROUS
- No extra commentary outside the format above

Input to analyze: {user_text}"""

    last_error = None

    for model in GEMINI_MODELS:
        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                print(f"[INFO] Trying model={model} attempt={attempt+1}", file=sys.stderr)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=2048,   # ✅ fixed — was 1024, now 2048
                    ),
                )
                result = response.text
                return jsonify({"result": result.strip() if result else "No response received."})

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_overloaded = any(k in err_str for k in ("503", "unavailable", "429", "quota", "rate"))

                print(f"[WARN] model={model} attempt={attempt+1} error={e}", file=sys.stderr)

                if is_overloaded:
                    if attempt < len(RETRY_DELAYS) - 1:
                        time.sleep(delay)
                        continue
                    else:
                        break
                else:
                    return jsonify({"error": f"Gemini error: {type(e).__name__} — {e}"})

    print(f"[ERROR] All models failed. Last error: {last_error}", file=sys.stderr)
    return jsonify({"error": "Gemini is currently overloaded across all models. Please wait a moment and try again."})


@app.route("/models")
def list_models():
    """Lists all Gemini models available to your API key that support generateContent."""
    api_key = GOOGLE_API_KEY.strip()
    if not api_key:
        return jsonify({"error": "API key not set."})
    try:
        client = genai.Client(api_key=api_key)
        available = [
            m.name for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
        ]
        return jsonify({"models": available, "preferred": GEMINI_MODELS})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    print("=" * 55)
    print("  🔐 CyberShield — Cybersecurity Safety Assistant")
    print("  🌐 Open in browser → http://localhost:5000")
    print("  🔍 Check models   → http://localhost:5000/models")
    print("=" * 55)
    app.run(debug=True, port=5000)
