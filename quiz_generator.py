#!/usr/bin/env python3
"""
Quiz HTML Generator — Bilingual + Advanced Features
-----------------------------------------------------
Usage:
    python3 quiz_generator.py <input_file.txt|json> [output_file.html]
"""
import json, sys, os, html as html_mod
from pathlib import Path


def load_questions(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array of question objects.")
    return data


def generate_html(questions, title):
    q_json   = json.dumps(questions, ensure_ascii=False)
    title_s  = html_mod.escape(title)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title id="page-title">{title_s}</title>
<style>
/* ── LIGHT THEME TOKENS ─────────────────────────────── */
:root{{
  --primary:#4f46e5;--primary-light:#818cf8;--primary-dark:#3730a3;
  --success:#16a34a;--danger:#dc2626;--warning:#d97706;
  --bg:#f8fafc;--surface:#fff;--border:#e2e8f0;
  --text:#1e293b;--muted:#64748b;
  --hindi-bg:#fdf4ff;--hindi-border:#e9d5ff;--hindi-text:#7c3aed;
  --r:12px;--sh:0 4px 24px rgba(0,0,0,.08);--sh-sm:0 1px 6px rgba(0,0,0,.06);
}}
/* ── DARK THEME ─────────────────────────────────────── */
body.dark{{
  --bg:#0f172a;--surface:#1e293b;--border:#334155;
  --text:#f1f5f9;--muted:#94a3b8;
  --hindi-bg:#1e1b33;--hindi-border:#4c1d95;--hindi-text:#a78bfa;
  --sh:0 4px 24px rgba(0,0,0,.4);--sh-sm:0 1px 6px rgba(0,0,0,.3);
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .2s,color .2s}}

/* ── NAV ────────────────────────────────────────────── */
nav{{
  background:var(--primary);color:#fff;display:flex;align-items:center;
  justify-content:space-between;padding:0 16px;height:54px;position:sticky;
  top:0;z-index:100;box-shadow:0 2px 12px rgba(79,70,229,.35);gap:8px;
}}
.logo{{
  font-weight:800;font-size:.95rem;display:flex;align-items:center;gap:6px;
  flex-shrink:0;
}}
.quiz-title-edit{{
  outline:none;border-bottom:1px dashed rgba(255,255,255,.4);
  min-width:60px;max-width:200px;white-space:nowrap;overflow:hidden;
  cursor:text;transition:border .15s;
}}
.quiz-title-edit:focus{{border-bottom:1px solid #fff;background:rgba(255,255,255,.1);border-radius:4px;padding:1px 4px}}
.quiz-title-edit:empty:before{{content:attr(data-ph);opacity:.5}}
.nav-tabs{{display:flex;gap:2px;flex-shrink:0}}
.nav-tab{{
  background:transparent;border:none;color:rgba(255,255,255,.75);cursor:pointer;
  padding:5px 10px;border-radius:7px;font-size:.8rem;font-weight:500;transition:.15s;white-space:nowrap;
}}
.nav-tab:hover{{background:rgba(255,255,255,.15);color:#fff}}
.nav-tab.active{{background:rgba(255,255,255,.22);color:#fff;font-weight:700}}
.nav-right{{display:flex;align-items:center;gap:6px;flex-shrink:0}}
.icon-btn{{
  background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);
  color:#fff;width:32px;height:32px;border-radius:50%;cursor:pointer;
  display:flex;align-items:center;justify-content:center;font-size:1rem;transition:.15s;
}}
.icon-btn:hover{{background:rgba(255,255,255,.28)}}
.bilingual-badge{{
  background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);
  color:#fff;padding:3px 9px;border-radius:99px;font-size:.72rem;font-weight:700;white-space:nowrap;
}}

/* ── PAGES ──────────────────────────────────────────── */
.page{{display:none;padding:18px;max-width:860px;margin:0 auto}}
.page.active{{display:block}}

/* ── CARDS ──────────────────────────────────────────── */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--sh-sm);padding:20px;margin-bottom:16px}}

/* ── HOME ──────────────────────────────────────────── */
.home-hero{{text-align:center;padding:28px 12px 20px}}
.home-hero h1{{font-size:1.7rem;color:var(--primary);margin-bottom:5px}}
.home-hero p{{color:var(--muted);font-size:.9rem}}
.bilingual-pill{{display:inline-block;background:linear-gradient(90deg,#4f46e5 50%,#7c3aed 50%);color:#fff;border-radius:99px;padding:2px 14px;font-size:.75rem;font-weight:700;margin-top:7px}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:18px 0}}
.stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;text-align:center;box-shadow:var(--sh-sm)}}
.stat-card .value{{font-size:1.8rem;font-weight:800;color:var(--primary)}}
.stat-card .label{{font-size:.76rem;color:var(--muted);margin-top:3px}}

/* ── FORM CONTROLS ──────────────────────────────────── */
.filter-row{{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-bottom:16px}}
.filter-row label{{font-size:.86rem;font-weight:600;color:var(--muted)}}
select,input[type=number]{{
  border:1px solid var(--border);border-radius:7px;padding:6px 10px;
  font-size:.86rem;background:var(--surface);color:var(--text);outline:none;transition:.15s;
}}
select:focus,input:focus{{border-color:var(--primary)}}
body.dark select,body.dark input[type=number]{{background:var(--surface);color:var(--text)}}

/* ── BUTTONS ────────────────────────────────────────── */
.btn{{display:inline-flex;align-items:center;gap:5px;border:none;border-radius:7px;padding:8px 16px;font-size:.86rem;font-weight:600;cursor:pointer;transition:.15s}}
.btn-primary{{background:var(--primary);color:#fff}}
.btn-primary:hover{{background:var(--primary-dark);transform:translateY(-1px)}}
.btn-outline{{background:transparent;border:2px solid var(--primary);color:var(--primary)}}
.btn-outline:hover{{background:var(--primary);color:#fff}}
.btn-sm{{padding:5px 11px;font-size:.79rem}}
.btn:disabled{{opacity:.5;cursor:not-allowed;transform:none!important}}

/* ── MARKING BADGE ──────────────────────────────────── */
.marking-info{{
  display:inline-flex;gap:10px;padding:5px 12px;border-radius:99px;
  background:var(--bg);border:1px solid var(--border);font-size:.78rem;
  color:var(--muted);margin-bottom:14px;
}}
.marking-info .pos{{color:var(--success);font-weight:700}}
.marking-info .neg{{color:var(--danger);font-weight:700}}

/* ── QUIZ ────────────────────────────────────────────── */
#quiz-progress-bar-wrap{{background:var(--border);border-radius:99px;height:6px;margin-bottom:16px;overflow:hidden}}
#quiz-progress-bar{{background:linear-gradient(90deg,var(--primary),#7c3aed);height:100%;border-radius:99px;transition:width .3s;width:0%}}
.quiz-meta{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;font-size:.81rem;color:var(--muted)}}
#quiz-timer{{background:var(--primary);color:#fff;border-radius:20px;padding:3px 12px;font-weight:700;font-size:.9rem}}
#quiz-timer.warning{{background:var(--warning)}}
#quiz-timer.danger{{background:var(--danger)}}

/* ── BILINGUAL QUESTION ─────────────────────────────── */
.question-tag{{display:inline-block;font-size:.71rem;background:#ede9fe;color:var(--primary);padding:2px 10px;border-radius:99px;margin-bottom:9px;font-weight:600}}
body.dark .question-tag{{background:#2e1065;color:#a78bfa}}
.question-block{{margin-bottom:16px}}
.q-english{{font-size:1.03rem;font-weight:700;line-height:1.55;color:var(--text);margin-bottom:7px}}
.q-hindi{{font-size:.95rem;font-weight:500;line-height:1.6;color:var(--hindi-text);background:var(--hindi-bg);border-left:3px solid var(--hindi-border);padding:7px 12px;border-radius:0 8px 8px 0}}
.lang-divider{{display:flex;align-items:center;gap:7px;margin:6px 0;font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.lang-divider::before,.lang-divider::after{{content:'';flex:1;height:1px;background:var(--border)}}

/* ── BILINGUAL OPTIONS ──────────────────────────────── */
.options-list{{list-style:none;display:flex;flex-direction:column;gap:8px}}
.option-item{{border:2px solid var(--border);border-radius:9px;padding:10px 13px;cursor:pointer;transition:.15s;display:flex;align-items:flex-start;gap:10px}}
.option-item:hover:not(.disabled){{border-color:var(--primary-light);background:#ede9fe18}}
.option-item.selected{{border-color:var(--primary);background:#ede9fe33}}
.option-item.correct{{border-color:var(--success);background:#dcfce7}}
.option-item.wrong{{border-color:var(--danger);background:#fee2e2}}
.option-item.disabled{{cursor:default}}
body.dark .option-item.correct{{background:#14532d33}}
body.dark .option-item.wrong{{background:#7f1d1d33}}
.option-letter{{width:29px;height:29px;border-radius:50%;background:var(--bg);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem;flex-shrink:0;margin-top:2px}}
.option-item.correct .option-letter{{background:var(--success);border-color:var(--success);color:#fff}}
.option-item.wrong .option-letter{{background:var(--danger);border-color:var(--danger);color:#fff}}
.option-item.selected .option-letter{{background:var(--primary);border-color:var(--primary);color:#fff}}
.option-texts{{display:flex;flex-direction:column;gap:2px}}
.opt-english{{font-size:.91rem;font-weight:600;color:var(--text)}}
.opt-hindi{{font-size:.81rem;color:var(--hindi-text)}}

/* ── EXPLANATION ────────────────────────────────────── */
.explanation-box{{margin-top:14px;border-radius:9px;overflow:hidden;display:none;border:1px solid var(--border)}}
.explanation-box.show{{display:block}}
.exp-english{{padding:11px 15px;background:#f0fdf4;border-left:4px solid var(--success);font-size:.86rem;line-height:1.6;color:#14532d}}
.exp-hindi{{padding:11px 15px;background:var(--hindi-bg);border-left:4px solid var(--hindi-border);font-size:.86rem;line-height:1.6;color:var(--hindi-text);border-top:1px solid var(--border)}}
body.dark .exp-english{{background:#052e16;color:#86efac}}

/* ── NAV DOTS ───────────────────────────────────────── */
.quiz-nav{{display:flex;justify-content:space-between;align-items:center;margin-top:18px;gap:8px}}
.question-nav-grid{{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px}}
.q-dot{{width:30px;height:30px;border-radius:6px;border:2px solid var(--border);background:var(--surface);cursor:pointer;font-size:.76rem;font-weight:600;color:var(--muted);display:flex;align-items:center;justify-content:center;transition:.12s}}
.q-dot:hover{{border-color:var(--primary);color:var(--primary)}}
.q-dot.current{{border-color:var(--primary);background:var(--primary);color:#fff}}
.q-dot.answered{{border-color:var(--success);background:#dcfce7;color:var(--success)}}
.q-dot.wrong-answered{{border-color:var(--danger);background:#fee2e2;color:var(--danger)}}
.q-dot.skipped{{border-color:var(--warning);background:#fef9c3;color:var(--warning)}}
body.dark .q-dot.answered{{background:#14532d44}}
body.dark .q-dot.wrong-answered{{background:#7f1d1d44}}

/* ── RESULTS ────────────────────────────────────────── */
.result-hero{{text-align:center;padding:24px 0}}
.result-score-ring{{width:128px;height:128px;border-radius:50%;border:10px solid var(--border);display:inline-flex;align-items:center;justify-content:center;flex-direction:column;margin-bottom:12px}}
.score-pct{{font-size:1.9rem;font-weight:900;color:var(--primary)}}
.score-label{{font-size:.7rem;color:var(--muted);font-weight:600}}
.marks-display{{margin-top:8px;font-size:1rem;font-weight:700;color:var(--text)}}
.marks-display span{{color:var(--primary)}}
.result-bars{{margin-top:12px}}
.result-bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:.84rem}}
.result-bar-label{{width:75px;color:var(--muted)}}
.result-bar-track{{flex:1;background:var(--border);border-radius:99px;height:7px;overflow:hidden}}
.result-bar-fill{{height:100%;border-radius:99px}}
.result-bar-count{{width:34px;text-align:right;font-weight:700}}

/* ── REVIEW ─────────────────────────────────────────── */
.review-q{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:12px}}
.review-q .q-number{{font-size:.76rem;color:var(--muted);margin-bottom:5px}}
.review-q .q-english{{font-weight:700;margin-bottom:4px;line-height:1.5;font-size:.98rem}}
.review-q .q-hindi{{font-size:.88rem;color:var(--hindi-text);margin-bottom:10px}}
.review-option{{padding:7px 12px;border-radius:7px;border:2px solid var(--border);margin-bottom:5px;display:flex;align-items:flex-start;gap:8px;font-size:.86rem}}
.review-option.correct-opt{{border-color:var(--success);background:#dcfce7}}
.review-option.user-wrong{{border-color:var(--danger);background:#fee2e2}}
body.dark .review-option.correct-opt{{background:#052e16}}
body.dark .review-option.user-wrong{{background:#450a0a}}
.review-exp-en{{padding:8px 12px;background:#f0fdf4;border-left:4px solid var(--success);font-size:.83rem;line-height:1.55}}
.review-exp-hi{{padding:8px 12px;background:var(--hindi-bg);border-left:4px solid var(--hindi-border);font-size:.83rem;line-height:1.55;color:var(--hindi-text);border-top:1px solid var(--border)}}
body.dark .review-exp-en{{background:#052e16;color:#86efac}}
.review-exp-wrap{{margin-top:9px;border:1px solid var(--border);border-radius:7px;overflow:hidden}}
.badge{{display:inline-block;padding:2px 7px;border-radius:99px;font-size:.7rem;font-weight:700}}
.badge-correct{{background:#dcfce7;color:var(--success)}}
.badge-wrong{{background:#fee2e2;color:var(--danger)}}
.badge-skipped{{background:#fef9c3;color:var(--warning)}}

/* ── STATS ──────────────────────────────────────────── */
.history-item{{display:flex;align-items:center;gap:9px;padding:9px 13px;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:7px;font-size:.86rem}}
.h-score{{font-weight:800;font-size:1rem;color:var(--primary)}}
.h-detail{{color:var(--muted);font-size:.78rem;flex:1}}
.h-date{{color:var(--muted);font-size:.75rem}}
.sub-row{{display:grid;grid-template-columns:1fr 65px 65px;gap:7px;padding:6px 0;border-bottom:1px solid var(--border);font-size:.84rem;align-items:center}}
.sub-row:last-child{{border-bottom:none}}
.sub-name{{font-weight:600}}
.sub-pct{{text-align:center;font-weight:700;color:var(--primary)}}
.sub-total{{text-align:center;color:var(--muted)}}

/* ── MISC ───────────────────────────────────────────── */
.section-title{{font-size:1rem;font-weight:700;margin-bottom:13px;color:var(--text);display:flex;align-items:center;gap:6px}}
.divider{{border:none;border-top:1px solid var(--border);margin:16px 0}}
.empty-state{{text-align:center;padding:32px 16px;color:var(--muted)}}
.empty-state .icon{{font-size:2.6rem;margin-bottom:9px}}
@media(max-width:600px){{
  nav{{padding:0 9px;gap:5px}}
  .logo{{font-size:.82rem}}
  .nav-tab{{padding:4px 7px;font-size:.73rem}}
  .page{{padding:10px}}
  .quiz-title-edit{{max-width:110px}}
}}
</style>
</head>
<body>

<!-- ╔══ NAV ═══════════════════════════════════════════╗ -->
<nav>
  <div class="logo">
    <span>🎓</span>
    <span class="quiz-title-edit" id="quiz-title" contenteditable="true"
          data-ph="Quiz Title" title="Click to rename">{title_s}</span>
  </div>
  <div class="nav-tabs">
    <button class="nav-tab active" onclick="showPage('home')">Home</button>
    <button class="nav-tab" onclick="showPage('quiz-setup')">Quiz</button>
    <button class="nav-tab" onclick="showPage('review-page')">Review</button>
    <button class="nav-tab" onclick="showPage('stats-page')">Stats</button>
  </div>
  <div class="nav-right">
    <div class="bilingual-badge">EN + हिं</div>
    <button class="icon-btn" onclick="toggleDark()" id="dark-btn" title="Toggle dark mode">🌙</button>
  </div>
</nav>

<!-- ╔══ HOME ═══════════════════════════════════════════╗ -->
<div id="home" class="page active">
  <div class="home-hero">
    <h1 id="hero-title">{title_s}</h1>
    <p>Bilingual quiz · English &amp; Hindi together</p>
    <div class="bilingual-pill">ENGLISH + हिंदी</div>
  </div>
  <div class="stats-grid" id="home-stats"></div>
  <div class="card">
    <div class="section-title">📈 Last Performance</div>
    <div id="home-overview"></div>
  </div>
  <div class="card">
    <div class="section-title">🕐 Recent Sessions</div>
    <div id="home-recent"></div>
  </div>
</div>

<!-- ╔══ QUIZ SETUP ══════════════════════════════════════╗ -->
<div id="quiz-setup" class="page">
  <div class="card">
    <div class="section-title">⚙️ Quiz Settings</div>
    <div class="filter-row">
      <label>Subject</label>
      <select id="filter-subject"><option value="">All Subjects</option></select>
    </div>
    <div class="filter-row">
      <label>Topic</label>
      <select id="filter-topic"><option value="">All Topics</option></select>
    </div>
    <div class="filter-row">
      <label>Questions</label>
      <input type="number" id="q-count" min="5" max="200" value="20" style="width:72px"/>
      <span style="font-size:.81rem;color:var(--muted)" id="q-available"></span>
    </div>
    <div class="filter-row">
      <label>Timer</label>
      <select id="quiz-mode">
        <option value="timed">60s per question</option>
        <option value="custom">Custom timer</option>
        <option value="free">No timer</option>
      </select>
      <input type="number" id="custom-time" min="10" max="600" value="60" style="width:72px;display:none"/>
      <span id="custom-time-unit" style="font-size:.8rem;color:var(--muted);display:none">sec</span>
    </div>
    <div class="filter-row">
      <label>Order</label>
      <select id="quiz-order">
        <option value="random">Random</option>
        <option value="sequential">Sequential</option>
      </select>
    </div>

    <hr class="divider"/>
    <div class="section-title" style="margin-bottom:10px">🏅 Marking Scheme</div>
    <div class="filter-row">
      <label>✅ Correct</label>
      <input type="number" id="mark-correct" min="0.25" max="10" step="0.25" value="1" style="width:72px"/>
      <label style="margin-left:8px">marks</label>
    </div>
    <div class="filter-row">
      <label>❌ Wrong</label>
      <input type="number" id="mark-neg" min="0" max="10" step="0.25" value="0" style="width:72px"/>
      <label style="margin-left:8px">marks deducted</label>
    </div>
    <div id="marking-preview" style="font-size:.82rem;color:var(--muted);margin-bottom:14px"></div>

    <hr class="divider"/>
    <button class="btn btn-primary" onclick="startQuiz()">▶ Start Quiz</button>
    <span id="setup-msg" style="margin-left:9px;font-size:.81rem;color:var(--danger)"></span>
  </div>
</div>

<!-- ╔══ QUIZ PAGE ════════════════════════════════════════╗ -->
<div id="quiz-page" class="page">
  <div id="quiz-progress-bar-wrap"><div id="quiz-progress-bar"></div></div>
  <div class="quiz-meta">
    <span id="quiz-meta-left"></span>
    <span id="quiz-timer">60</span>
    <button class="btn btn-sm btn-outline" onclick="endQuizEarly()">Finish Early</button>
  </div>
  <div class="card">
    <div id="quiz-marking-badge" class="marking-info"></div>
    <div class="question-tag" id="q-tag"></div>
    <div class="question-block">
      <div class="q-english" id="q-english"></div>
      <div class="lang-divider" id="hindi-divider">हिंदी</div>
      <div class="q-hindi" id="q-hindi"></div>
    </div>
    <ul class="options-list" id="options-list"></ul>
    <div class="explanation-box" id="explanation-box">
      <div class="exp-english" id="exp-english"></div>
      <div class="exp-hindi" id="exp-hindi"></div>
    </div>
    <div class="quiz-nav">
      <button class="btn btn-outline btn-sm" id="prev-btn" onclick="goQuestion(-1)">← Prev</button>
      <button class="btn btn-sm" id="skip-btn" onclick="skipQuestion()" style="background:#fef9c3;color:#92400e;border:2px solid #fbbf24;">Skip</button>
      <button class="btn btn-primary btn-sm" id="next-btn" onclick="goQuestion(1)">Next →</button>
    </div>
  </div>
  <div class="card">
    <div style="font-size:.78rem;color:var(--muted);margin-bottom:6px">Question Navigator</div>
    <div class="question-nav-grid" id="q-nav-grid"></div>
  </div>
</div>

<!-- ╔══ RESULTS ═════════════════════════════════════════╗ -->
<div id="results-page" class="page">
  <div class="card result-hero">
    <div class="result-score-ring" id="score-ring">
      <span class="score-pct" id="result-pct">0%</span>
      <span class="score-label">Accuracy</span>
    </div>
    <h2 id="result-heading"></h2>
    <div class="marks-display" id="marks-display"></div>
    <p id="result-summary" style="color:var(--muted);margin-top:5px;font-size:.88rem;"></p>
  </div>
  <div class="card">
    <div class="section-title">📊 Breakdown</div>
    <div class="result-bars" id="result-bars"></div>
  </div>
  <div class="card">
    <div class="section-title">📚 Subject Performance</div>
    <div id="result-subject-breakdown"></div>
  </div>
  <div style="display:flex;gap:9px;flex-wrap:wrap;margin-bottom:18px">
    <button class="btn btn-primary" onclick="showPage('review-page')">🔍 Review Answers</button>
    <button class="btn btn-outline" onclick="showPage('quiz-setup')">🔄 New Quiz</button>
    <button class="btn btn-outline" onclick="showPage('home')">🏠 Home</button>
  </div>
</div>

<!-- ╔══ REVIEW PAGE ═════════════════════════════════════╗ -->
<div id="review-page" class="page">
  <div class="card">
    <div class="section-title">🔍 Review (EN + हिं)</div>
    <div class="filter-row">
      <label>Subject</label>
      <select id="review-subject" onchange="renderReview()"><option value="">All</option></select>
      <label>Show</label>
      <select id="review-filter" onchange="renderReview()">
        <option value="all">All</option>
        <option value="wrong">Wrong</option>
        <option value="correct">Correct</option>
        <option value="skipped">Skipped</option>
      </select>
    </div>
  </div>
  <div id="review-list"></div>
</div>

<!-- ╔══ STATS PAGE ══════════════════════════════════════╗ -->
<div id="stats-page" class="page">
  <div class="stats-grid" id="stats-grid"></div>
  <div class="card">
    <div class="section-title">📊 Subject-wise Accuracy</div>
    <div id="stats-subject"></div>
  </div>
  <div class="card">
    <div class="section-title">🕐 Session History</div>
    <div id="stats-history"></div>
    <button class="btn btn-sm btn-outline" style="margin-top:9px;border-color:var(--danger);color:var(--danger)" onclick="clearHistory()">🗑 Clear History</button>
  </div>
</div>

<script>
// ═══════════════════════════════════════════════════
//  DATA
// ═══════════════════════════════════════════════════
const ALL_QUESTIONS = {q_json};

// ═══════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════
let currentSession = null;
let history = [];

// ═══════════════════════════════════════════════════
//  DARK MODE
// ═══════════════════════════════════════════════════
function applyDark(on) {{
  document.body.classList.toggle('dark', on);
  document.getElementById('dark-btn').textContent = on ? '☀️' : '🌙';
  localStorage.setItem('quiz_theme', on ? 'dark' : 'light');
}}
function toggleDark() {{ applyDark(!document.body.classList.contains('dark')); }}
function initDark() {{
  const saved = localStorage.getItem('quiz_theme');
  if (saved === 'dark') applyDark(true);
  else if (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches) applyDark(true);
}}

// ═══════════════════════════════════════════════════
//  EDITABLE TITLE
// ═══════════════════════════════════════════════════
const titleEl = document.getElementById('quiz-title');
const heroTitle = document.getElementById('hero-title');
titleEl.addEventListener('input', () => {{
  heroTitle.textContent = titleEl.textContent.trim() || '{title_s}';
  document.title = titleEl.textContent.trim() || '{title_s}';
}});
titleEl.addEventListener('blur', () => {{
  if (!titleEl.textContent.trim()) titleEl.textContent = '{title_s}';
  heroTitle.textContent = titleEl.textContent.trim();
  document.title = titleEl.textContent.trim();
}});
titleEl.addEventListener('keydown', e => {{ if (e.key === 'Enter') {{ e.preventDefault(); titleEl.blur(); }} }});

// ═══════════════════════════════════════════════════
//  PERSISTENCE
// ═══════════════════════════════════════════════════
function saveHistory() {{ localStorage.setItem('quiz_history_v3', JSON.stringify(history)); }}
function loadHistory() {{ try {{ history = JSON.parse(localStorage.getItem('quiz_history_v3') || '[]'); }} catch(e) {{ history = []; }} }}
function clearHistory() {{ if (!confirm('Clear all session history?')) return; history = []; saveHistory(); renderStatsPage(); renderHomePage(); }}

// ═══════════════════════════════════════════════════
//  PAGE NAV
// ═══════════════════════════════════════════════════
let currentPage = 'home';
function showPage(id) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  const map = {{'home':0,'quiz-setup':1,'quiz-page':1,'results-page':1,'review-page':2,'stats-page':3}};
  document.querySelectorAll('.nav-tab').forEach((t,i) => t.classList.toggle('active', i === map[id]));
  currentPage = id;
  if (id === 'home') renderHomePage();
  if (id === 'review-page') renderReview();
  if (id === 'stats-page') renderStatsPage();
  if (id === 'results-page') renderResults();
}}

// ═══════════════════════════════════════════════════
//  SUBJECTS / TOPICS / FILTERS
// ═══════════════════════════════════════════════════
function getSubjects() {{ return [...new Set(ALL_QUESTIONS.map(q => q.subject).filter(Boolean))].sort(); }}
function getTopics(sub) {{
  return [...new Set(ALL_QUESTIONS.filter(q => !sub || q.subject === sub).map(q => q.topic).filter(Boolean))].sort();
}}
function populateFilters() {{
  const subSel = document.getElementById('filter-subject');
  const revSub = document.getElementById('review-subject');
  getSubjects().forEach(s => {{
    [subSel, revSub].forEach(el => {{
      const o = document.createElement('option'); o.value = s; o.textContent = s; el.appendChild(o);
    }});
  }});
  subSel.addEventListener('change', () => {{
    const topSel = document.getElementById('filter-topic');
    topSel.innerHTML = '<option value="">All Topics</option>';
    getTopics(subSel.value).forEach(t => {{
      const o = document.createElement('option'); o.value = t; o.textContent = t; topSel.appendChild(o);
    }});
    updateAvailable();
  }});
  document.getElementById('q-count').addEventListener('input', updateAvailable);
  document.getElementById('mark-correct').addEventListener('input', updateMarkingPreview);
  document.getElementById('mark-neg').addEventListener('input', updateMarkingPreview);
  updateAvailable();
  updateMarkingPreview();
}}
function updateAvailable() {{
  const sub = document.getElementById('filter-subject').value;
  const top = document.getElementById('filter-topic').value;
  const pool = ALL_QUESTIONS.filter(q => (!sub || q.subject === sub) && (!top || q.topic === top));
  document.getElementById('q-available').textContent = `(${{pool.length}} available)`;
  document.getElementById('q-count').max = pool.length;
}}
function updateMarkingPreview() {{
  const mc = parseFloat(document.getElementById('mark-correct').value) || 1;
  const mn = parseFloat(document.getElementById('mark-neg').value) || 0;
  document.getElementById('marking-preview').textContent =
    `Correct = +${{mc}} mark(s)  ·  Wrong = -${{mn}} mark(s)  ·  Skip = 0`;
}}
document.getElementById('quiz-mode').addEventListener('change', function() {{
  const show = this.value === 'custom';
  document.getElementById('custom-time').style.display = show ? '' : 'none';
  document.getElementById('custom-time-unit').style.display = show ? '' : 'none';
}});

// ═══════════════════════════════════════════════════
//  START QUIZ
// ═══════════════════════════════════════════════════
function startQuiz() {{
  const sub  = document.getElementById('filter-subject').value;
  const top  = document.getElementById('filter-topic').value;
  const cnt  = parseInt(document.getElementById('q-count').value) || 20;
  const mode = document.getElementById('quiz-mode').value;
  const ord  = document.getElementById('quiz-order').value;
  const cust = parseInt(document.getElementById('custom-time').value) || 60;
  const mc   = parseFloat(document.getElementById('mark-correct').value) || 1;
  const mn   = parseFloat(document.getElementById('mark-neg').value) || 0;

  let pool = ALL_QUESTIONS.filter(q => (!sub || q.subject === sub) && (!top || q.topic === top));
  if (!pool.length) {{ document.getElementById('setup-msg').textContent = 'No questions match.'; return; }}
  if (cnt > pool.length) {{ document.getElementById('setup-msg').textContent = `Only ${{pool.length}} available.`; return; }}
  document.getElementById('setup-msg').textContent = '';

  let questions = [...pool];
  if (ord === 'random') questions = questions.sort(() => Math.random() - 0.5);
  questions = questions.slice(0, cnt);

  const secPerQ = mode === 'timed' ? 60 : mode === 'custom' ? cust : null;

  currentSession = {{
    questions,
    answers:  new Array(questions.length).fill(null),
    revealed: new Array(questions.length).fill(false),
    currentIdx: 0,
    startTime: Date.now(),
    secPerQ, timeLeft: secPerQ,
    timerInterval: null,
    subject: sub || 'All', topic: top || 'All',
    markCorrect: mc, markNeg: mn,
  }};

  buildQuizNav();
  showPage('quiz-page');
  renderQuestion();
  if (secPerQ !== null) startTimer();
}}

// ═══════════════════════════════════════════════════
//  QUIZ ENGINE
// ═══════════════════════════════════════════════════
function buildQuizNav() {{
  const grid = document.getElementById('q-nav-grid');
  grid.innerHTML = '';
  currentSession.questions.forEach((_, i) => {{
    const d = document.createElement('div');
    d.className = 'q-dot'; d.textContent = i + 1; d.onclick = () => jumpTo(i);
    grid.appendChild(d);
  }});
}}
function updateNavDots() {{
  const dots = document.querySelectorAll('.q-dot');
  const s = currentSession;
  dots.forEach((d, i) => {{
    d.className = 'q-dot';
    if (i === s.currentIdx) d.classList.add('current');
    else if (s.answers[i] === -1) d.classList.add('skipped');
    else if (s.answers[i] !== null)
      d.classList.add(s.answers[i] === s.questions[i].correct ? 'answered' : 'wrong-answered');
  }});
}}
function renderQuestion() {{
  const s = currentSession;
  const q = s.questions[s.currentIdx];
  const total = s.questions.length;
  const answered = s.answers.filter(a => a !== null).length;

  document.getElementById('quiz-progress-bar').style.width = ((s.currentIdx + 1) / total * 100) + '%';
  document.getElementById('quiz-meta-left').textContent = `Q ${{s.currentIdx+1}} / ${{total}}  ·  Done: ${{answered}}`;

  // Marking badge
  document.getElementById('quiz-marking-badge').innerHTML =
    `<span class="pos">+${{s.markCorrect}} correct</span>` +
    (s.markNeg > 0 ? `<span class="neg">-${{s.markNeg}} wrong</span>` : '<span>No negative</span>');

  // Subject/topic tag
  document.getElementById('q-tag').textContent = [q.subject, q.topic].filter(Boolean).join(' › ');

  // Bilingual question
  document.getElementById('q-english').textContent = q.qEnglish || '';
  document.getElementById('q-hindi').textContent   = q.qHindi   || '';
  const hasHindi = !!q.qHindi;
  document.getElementById('hindi-divider').style.display = hasHindi ? '' : 'none';
  document.getElementById('q-hindi').style.display       = hasHindi ? '' : 'none';

  // Options — bilingual
  const optsEn = q.optionsEnglish || [];
  const optsHi = q.optionsHindi   || [];
  const ul      = document.getElementById('options-list');
  ul.innerHTML  = '';
  const chosen   = s.answers[s.currentIdx];
  const revealed = s.revealed[s.currentIdx];

  optsEn.forEach((opt, i) => {{
    const li = document.createElement('li');
    li.className = 'option-item';
    if (revealed) li.classList.add('disabled');
    if (revealed) {{
      if (i === q.correct) li.classList.add('correct');
      else if (i === chosen && chosen !== q.correct) li.classList.add('wrong');
    }} else if (i === chosen) li.classList.add('selected');

    const hiOpt = optsHi[i] || '';
    li.innerHTML = `
      <span class="option-letter">${{String.fromCharCode(65+i)}}</span>
      <span class="option-texts">
        <span class="opt-english">${{opt}}</span>
        ${{hiOpt ? `<span class="opt-hindi">${{hiOpt}}</span>` : ''}}
      </span>`;
    if (!revealed) li.onclick = () => selectOption(i);
    ul.appendChild(li);
  }});

  // Explanation
  const expBox = document.getElementById('explanation-box');
  if (revealed) {{
    document.getElementById('exp-english').textContent = q.explanationEnglish || '';
    const expHi = document.getElementById('exp-hindi');
    expHi.textContent   = q.explanationHindi || '';
    expHi.style.display = q.explanationHindi ? '' : 'none';
    expBox.classList.add('show');
  }} else {{
    expBox.classList.remove('show');
  }}

  document.getElementById('prev-btn').disabled = s.currentIdx === 0;
  const isLast = s.currentIdx === total - 1;
  const nb = document.getElementById('next-btn');
  nb.textContent = isLast ? '✓ Finish' : 'Next →';
  nb.onclick = isLast ? finishQuiz : () => goQuestion(1);
  document.getElementById('skip-btn').style.display = revealed ? 'none' : '';

  if (s.secPerQ !== null) {{ s.timeLeft = s.secPerQ; updateTimerDisplay(); }}
  updateNavDots();
}}
function selectOption(i) {{
  const s = currentSession;
  if (s.revealed[s.currentIdx]) return;
  s.answers[s.currentIdx]  = i;
  s.revealed[s.currentIdx] = true;
  renderQuestion();
  if (s.currentIdx < s.questions.length - 1) setTimeout(() => goQuestion(1), 1400);
}}
function goQuestion(dir) {{
  const s = currentSession;
  const next = s.currentIdx + dir;
  if (next < 0 || next >= s.questions.length) return;
  s.currentIdx = next;
  if (s.secPerQ !== null) {{ clearInterval(s.timerInterval); s.timeLeft = s.secPerQ; startTimer(); }}
  renderQuestion();
}}
function jumpTo(i) {{
  const s = currentSession;
  s.currentIdx = i;
  if (s.secPerQ !== null) {{ clearInterval(s.timerInterval); s.timeLeft = s.secPerQ; startTimer(); }}
  renderQuestion();
}}
function skipQuestion() {{
  const s = currentSession;
  if (s.answers[s.currentIdx] === null) s.answers[s.currentIdx] = -1;
  goQuestion(1);
}}
function endQuizEarly() {{ if (confirm('End quiz now and see results?')) finishQuiz(); }}

// ═══════════════════════════════════════════════════
//  TIMER
// ═══════════════════════════════════════════════════
function startTimer() {{
  const s = currentSession;
  if (s.secPerQ === null) return;
  clearInterval(s.timerInterval);
  s.timerInterval = setInterval(() => {{
    s.timeLeft--;
    updateTimerDisplay();
    if (s.timeLeft <= 0) {{
      clearInterval(s.timerInterval);
      if (s.answers[s.currentIdx] === null) s.answers[s.currentIdx] = -1;
      s.revealed[s.currentIdx] = true;
      renderQuestion();
      if (s.currentIdx < s.questions.length - 1) {{ setTimeout(() => {{ goQuestion(1); startTimer(); }}, 1100); }}
      else {{ setTimeout(finishQuiz, 1100); }}
    }}
  }}, 1000);
}}
function updateTimerDisplay() {{
  const s = currentSession;
  const el = document.getElementById('quiz-timer');
  if (s.secPerQ === null) {{ el.style.display = 'none'; return; }}
  el.style.display = '';
  const t = s.timeLeft;
  el.textContent = `${{Math.floor(t/60)}}:${{String(t%60).padStart(2,'0')}}`;
  el.className = t > s.secPerQ * 0.5 ? '' : t > 10 ? 'warning' : 'danger';
}}

// ═══════════════════════════════════════════════════
//  FINISH + CUSTOM MARKING
// ═══════════════════════════════════════════════════
function finishQuiz() {{
  const s = currentSession;
  clearInterval(s.timerInterval);
  let correct = 0, wrong = 0, skipped = 0, totalScore = 0;
  const subjectStats = {{}};
  const maxScore = s.questions.length * s.markCorrect;

  s.questions.forEach((q, i) => {{
    const a = s.answers[i];
    const sub = q.subject || 'Other';
    if (!subjectStats[sub]) subjectStats[sub] = {{correct:0, total:0}};
    subjectStats[sub].total++;
    if (a === -1 || a === null) {{ skipped++; }}
    else if (a === q.correct) {{ correct++; subjectStats[sub].correct++; totalScore += s.markCorrect; }}
    else {{ wrong++; totalScore -= s.markNeg; }}
  }});
  totalScore = Math.round(Math.max(0, totalScore) * 100) / 100;
  const pct     = Math.round(correct / s.questions.length * 100);
  const elapsed = Math.round((Date.now() - s.startTime) / 1000);

  const result = {{
    date: new Date().toISOString(),
    total: s.questions.length, correct, wrong, skipped, pct,
    totalScore, maxScore, markCorrect: s.markCorrect, markNeg: s.markNeg,
    elapsed, subject: s.subject, topic: s.topic, subjectStats,
    answers: [...s.answers],
    questions: s.questions.map(q => ({{
      qEnglish: q.qEnglish, qHindi: q.qHindi,
      optionsEnglish: q.optionsEnglish, optionsHindi: q.optionsHindi,
      correct: q.correct, explanationEnglish: q.explanationEnglish,
      explanationHindi: q.explanationHindi, subject: q.subject, topic: q.topic
    }}))
  }};
  history.unshift(result);
  if (history.length > 50) history = history.slice(0, 50);
  saveHistory();
  currentSession._lastResult = result;
  showPage('results-page');
}}
function renderResults() {{
  if (!currentSession?._lastResult) return;
  const r = currentSession._lastResult;
  document.getElementById('result-pct').textContent = r.pct + '%';
  const color = r.pct >= 80 ? '#16a34a' : r.pct >= 60 ? '#4f46e5' : '#dc2626';
  document.getElementById('score-ring').style.borderColor = color;
  document.getElementById('result-pct').style.color = color;
  document.getElementById('result-heading').textContent =
    r.pct >= 80 ? '🎉 Excellent!' : r.pct >= 60 ? '👍 Good Job!' : '💪 Keep Practicing!';

  // Marks display
  const md = document.getElementById('marks-display');
  md.innerHTML = `Score: <span>${{r.totalScore}} / ${{r.maxScore}}</span> marks
    &nbsp;·&nbsp; +${{r.markCorrect}} per correct${{r.markNeg > 0 ? `, -${{r.markNeg}} per wrong` : ''}}`;

  document.getElementById('result-summary').textContent =
    `${{r.correct}} correct · ${{r.wrong}} wrong · ${{r.skipped}} skipped · ${{fmtTime(r.elapsed)}}`;

  document.getElementById('result-bars').innerHTML =
    barRow('Correct', r.correct, r.total, '#16a34a') +
    barRow('Wrong',   r.wrong,   r.total, '#dc2626') +
    barRow('Skipped', r.skipped, r.total, '#d97706');

  const sb = document.getElementById('result-subject-breakdown');
  sb.innerHTML = '<div class="sub-row" style="font-weight:700;font-size:.76rem;color:var(--muted)"><span>Subject</span><span style="text-align:center">Acc.</span><span style="text-align:center">Qs</span></div>';
  Object.entries(r.subjectStats).forEach(([sub, st]) => {{
    const p = Math.round(st.correct / st.total * 100);
    sb.innerHTML += `<div class="sub-row"><span class="sub-name">${{sub}}</span><span class="sub-pct">${{p}}%</span><span class="sub-total">${{st.total}}</span></div>`;
  }});
}}
function barRow(label, val, total, color) {{
  const pct = total ? Math.round(val/total*100) : 0;
  return `<div class="result-bar-row">
    <span class="result-bar-label">${{label}}</span>
    <div class="result-bar-track"><div class="result-bar-fill" style="width:${{pct}}%;background:${{color}}"></div></div>
    <span class="result-bar-count">${{val}}</span>
  </div>`;
}}

// ═══════════════════════════════════════════════════
//  REVIEW PAGE
// ═══════════════════════════════════════════════════
function renderReview() {{
  const filterSub  = document.getElementById('review-subject').value;
  const filterType = document.getElementById('review-filter').value;
  let items = [];
  if (currentSession?._lastResult) {{
    const r = currentSession._lastResult;
    r.questions.forEach((q, i) => {{
      const a = r.answers[i];
      const status = (a === -1 || a === null) ? 'skipped' : a === q.correct ? 'correct' : 'wrong';
      items.push({{q, a, status}});
    }});
  }} else {{
    ALL_QUESTIONS.forEach(q => items.push({{q, a: null, status: 'unanswered'}}));
  }}
  if (filterSub)  items = items.filter(it => it.q.subject === filterSub);
  if (filterType === 'wrong')   items = items.filter(it => it.status === 'wrong');
  else if (filterType === 'correct') items = items.filter(it => it.status === 'correct');
  else if (filterType === 'skipped') items = items.filter(it => it.status === 'skipped');

  const list = document.getElementById('review-list');
  list.innerHTML = items.length
    ? items.map((it, n) => reviewCard(it, n+1)).join('')
    : '<div class="empty-state"><div class="icon">🔍</div><p>No questions.</p></div>';
}}
function reviewCard({{q, a, status}}, n) {{
  const optsEn = q.optionsEnglish || [];
  const optsHi = q.optionsHindi   || [];
  const optRows = optsEn.map((opt, i) => {{
    let cls = '';
    if (i === q.correct) cls = 'correct-opt';
    else if (a !== null && a !== -1 && i === a && a !== q.correct) cls = 'user-wrong';
    const icon  = i === q.correct ? '✓' : (a !== null && a !== -1 && i === a) ? '✗' : '○';
    const hiOpt = optsHi[i] || '';
    return `<div class="review-option ${{cls}}">
      <span style="font-weight:700;flex-shrink:0;width:22px">${{icon}}${{String.fromCharCode(65+i)}}</span>
      <span class="option-texts">
        <span class="opt-english">${{opt}}</span>
        ${{hiOpt ? `<span class="opt-hindi">${{hiOpt}}</span>` : ''}}
      </span></div>`;
  }}).join('');
  const badgeCls  = status==='correct'?'badge-correct':status==='wrong'?'badge-wrong':'badge-skipped';
  const badgeTxt  = status==='correct'?'Correct':status==='wrong'?'Wrong':'Skipped';
  const subTop    = [q.subject, q.topic].filter(Boolean).join(' › ');
  const expEn     = q.explanationEnglish || '';
  const expHi     = q.explanationHindi   || '';
  return `<div class="review-q">
    <div class="q-number">Q${{n}} — ${{subTop}} <span class="badge ${{badgeCls}}">${{badgeTxt}}</span></div>
    <div class="q-english">${{q.qEnglish || ''}}</div>
    ${{q.qHindi ? `<div class="q-hindi">${{q.qHindi}}</div>` : ''}}
    ${{optRows}}
    <div class="review-exp-wrap">
      ${{expEn ? `<div class="review-exp-en">💡 ${{expEn}}</div>` : ''}}
      ${{expHi ? `<div class="review-exp-hi">💡 ${{expHi}}</div>` : ''}}
    </div>
  </div>`;
}}

// ═══════════════════════════════════════════════════
//  STATS PAGE
// ═══════════════════════════════════════════════════
function renderStatsPage() {{
  if (!history.length) {{
    document.getElementById('stats-grid').innerHTML = '';
    document.getElementById('stats-subject').innerHTML = '<div class="empty-state"><div class="icon">📊</div><p>Take a quiz first!</p></div>';
    document.getElementById('stats-history').innerHTML = '';
    return;
  }}
  const totalQ  = history.reduce((s,r) => s+r.total, 0);
  const avgPct  = Math.round(history.reduce((s,r) => s+r.pct, 0) / history.length);
  const best    = Math.max(...history.map(r => r.pct));
  const bestMk  = Math.max(...history.map(r => r.totalScore||0));
  document.getElementById('stats-grid').innerHTML = `
    <div class="stat-card"><div class="value">${{history.length}}</div><div class="label">Sessions</div></div>
    <div class="stat-card"><div class="value">${{totalQ}}</div><div class="label">Attempted</div></div>
    <div class="stat-card"><div class="value">${{avgPct}}%</div><div class="label">Avg Accuracy</div></div>
    <div class="stat-card"><div class="value">${{best}}%</div><div class="label">Best Score</div></div>
    <div class="stat-card"><div class="value">${{bestMk}}</div><div class="label">Best Marks</div></div>`;

  const subAcc = {{}};
  history.forEach(r => Object.entries(r.subjectStats||{{}}).forEach(([sub,st]) => {{
    if (!subAcc[sub]) subAcc[sub] = {{correct:0,total:0}};
    subAcc[sub].correct += st.correct; subAcc[sub].total += st.total;
  }}));
  const subEl = document.getElementById('stats-subject');
  subEl.innerHTML = '<div class="sub-row" style="font-weight:700;font-size:.76rem;color:var(--muted)"><span>Subject</span><span style="text-align:center">Acc.</span><span style="text-align:center">Qs</span></div>';
  Object.entries(subAcc).sort((a,b)=>b[1].total-a[1].total).forEach(([sub,st]) => {{
    const p = Math.round(st.correct/st.total*100);
    subEl.innerHTML += `<div class="sub-row"><span class="sub-name">${{sub}}</span><span class="sub-pct">${{p}}%</span><span class="sub-total">${{st.total}}</span></div>`;
  }});

  document.getElementById('stats-history').innerHTML = history.slice(0,20).map(r => {{
    const d = new Date(r.date);
    const ds = d.toLocaleDateString()+' '+d.toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});
    const color = r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';
    const mk = r.totalScore !== undefined ? ` · ${{r.totalScore}}/${{r.maxScore}} marks` : '';
    return `<div class="history-item">
      <span class="h-score" style="color:${{color}}">${{r.pct}}%</span>
      <span class="h-detail">${{r.correct}}/${{r.total}}${{mk}} · ${{r.subject}}</span>
      <span class="h-date">${{ds}}</span>
    </div>`;
  }}).join('');
}}

// ═══════════════════════════════════════════════════
//  HOME PAGE
// ═══════════════════════════════════════════════════
function renderHomePage() {{
  loadHistory();
  const best = history.length ? Math.max(...history.map(r=>r.pct)) : null;
  const avg  = history.length ? Math.round(history.reduce((s,r)=>s+r.pct,0)/history.length) : null;
  document.getElementById('home-stats').innerHTML = `
    <div class="stat-card"><div class="value">${{ALL_QUESTIONS.length}}</div><div class="label">Total Questions</div></div>
    <div class="stat-card"><div class="value">${{getSubjects().length}}</div><div class="label">Subjects</div></div>
    <div class="stat-card"><div class="value">${{history.length}}</div><div class="label">Sessions</div></div>
    ${{best!==null?`<div class="stat-card"><div class="value">${{best}}%</div><div class="label">Best Score</div></div>`:''}}
    ${{avg!==null?`<div class="stat-card"><div class="value">${{avg}}%</div><div class="label">Avg Score</div></div>`:''}}`;

  const ov = document.getElementById('home-overview');
  if (!history.length) {{
    ov.innerHTML = '<div class="empty-state"><div class="icon">🎯</div><p>No sessions yet. Click <strong>Quiz</strong> to start!</p></div>';
  }} else {{
    const last = history[0];
    const color = last.pct>=80?'#16a34a':last.pct>=60?'#4f46e5':'#dc2626';
    const mk = last.totalScore !== undefined ? ` · <strong>${{last.totalScore}}/${{last.maxScore}} marks</strong>` : '';
    ov.innerHTML = `<p style="font-size:.86rem;color:var(--muted);margin-bottom:10px">Last: <strong style="color:${{color}}">${{last.pct}}%</strong>${{mk}} — ${{last.correct}}/${{last.total}} correct</p>
      ${{barRow('Correct',last.correct,last.total,'#16a34a')}}
      ${{barRow('Wrong',last.wrong,last.total,'#dc2626')}}
      ${{barRow('Skipped',last.skipped,last.total,'#d97706')}}`;
  }}
  document.getElementById('home-recent').innerHTML = history.length
    ? history.slice(0,5).map(r => {{
        const color = r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';
        const mk = r.totalScore !== undefined ? ` · ${{r.totalScore}} marks` : '';
        return `<div class="history-item">
          <span class="h-score" style="color:${{color}}">${{r.pct}}%</span>
          <span class="h-detail">${{r.correct}}/${{r.total}}${{mk}} · ${{r.subject}}</span>
          <span class="h-date">${{new Date(r.date).toLocaleDateString()}}</span>
        </div>`;
      }}).join('')
    : '<div style="color:var(--muted);font-size:.86rem">No sessions yet.</div>';
}}

function fmtTime(s) {{ if(!s) return '—'; const m=Math.floor(s/60); return m>0?`${{m}}m ${{s%60}}s`:`${{s}}s`; }}

// ═══════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════
initDark();
loadHistory();
populateFilters();
renderHomePage();
</script>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 quiz_generator.py <input_file> [output.html]")
        sys.exit(1)
    inp = sys.argv[1]
    if not os.path.exists(inp):
        print(f"Error: {inp} not found"); sys.exit(1)
    out = sys.argv[2] if len(sys.argv) >= 3 else str(Path(inp).parent / (Path(inp).stem + "_quiz.html"))
    print(f"Loading: {inp}")
    questions = load_questions(inp)
    print(f"Loaded {len(questions)} questions.")
    title = Path(inp).stem.replace("_", " ").title()
    with open(out, "w", encoding="utf-8") as f:
        f.write(generate_html(questions, title))
    print(f"Saved: {out} ({os.path.getsize(out)//1024} KB)")
    print("Features: Bilingual EN+हिं · Dark/Light mode · Custom marking · Editable title")


if __name__ == "__main__":
    main()
