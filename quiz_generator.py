#!/usr/bin/env python3
"""
Quiz HTML Generator
-------------------
Converts a JSON quiz file (array of question objects) into a fully
self-contained, advanced HTML quiz page.

Usage:
    python quiz_generator.py <input_file.txt|json> [output_file.html]

If no output file is given, it is saved alongside the input file with .html extension.

Expected JSON format (array of objects):
    [
      {
        "qHindi": "...",
        "qEnglish": "...",
        "optionsHindi": ["a", "b", "c", "d"],
        "optionsEnglish": ["a", "b", "c", "d"],
        "correct": 1,            # 0-based index
        "explanationHindi": "...",
        "explanationEnglish": "...",
        "subject": "...",
        "topic": "..."
      },
      ...
    ]
"""

import json
import sys
import os
import html as html_mod
from pathlib import Path
from datetime import datetime


def load_questions(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array of question objects.")
    return data


def generate_html(questions: list, title: str) -> str:
    q_json = json.dumps(questions, ensure_ascii=False)
    title_safe = html_mod.escape(title)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title_safe}</title>
<style>
  :root {{
    --primary: #4f46e5;
    --primary-light: #818cf8;
    --primary-dark: #3730a3;
    --success: #16a34a;
    --danger: #dc2626;
    --warning: #d97706;
    --bg: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --text: #1e293b;
    --text-muted: #64748b;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0,0,0,0.08);
    --shadow-sm: 0 1px 6px rgba(0,0,0,0.06);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ---- NAV ---- */
  nav {{
    background: var(--primary);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    height: 58px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 12px rgba(79,70,229,0.25);
  }}
  nav .logo {{
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: 0.01em;
  }}
  nav .nav-tabs {{
    display: flex;
    gap: 4px;
  }}
  nav .nav-tab {{
    background: transparent;
    border: none;
    color: rgba(255,255,255,0.75);
    cursor: pointer;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.87rem;
    font-weight: 500;
    transition: all 0.15s;
  }}
  nav .nav-tab:hover {{ background: rgba(255,255,255,0.15); color: #fff; }}
  nav .nav-tab.active {{ background: rgba(255,255,255,0.2); color: #fff; font-weight: 700; }}
  nav .lang-toggle {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    color: #fff;
    padding: 5px 12px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: 600;
    transition: background 0.15s;
  }}
  nav .lang-toggle:hover {{ background: rgba(255,255,255,0.25); }}

  /* ---- PAGES ---- */
  .page {{ display: none; padding: 24px; max-width: 900px; margin: 0 auto; }}
  .page.active {{ display: block; }}

  /* ---- CARDS ---- */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    padding: 24px;
    margin-bottom: 20px;
  }}

  /* ---- HOME ---- */
  .home-hero {{
    text-align: center;
    padding: 40px 20px 32px;
  }}
  .home-hero h1 {{ font-size: 2rem; color: var(--primary); margin-bottom: 10px; }}
  .home-hero p {{ color: var(--text-muted); font-size: 1rem; }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin: 24px 0;
  }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    text-align: center;
    box-shadow: var(--shadow-sm);
  }}
  .stat-card .value {{
    font-size: 2rem;
    font-weight: 800;
    color: var(--primary);
  }}
  .stat-card .label {{
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 4px;
  }}
  .filter-row {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 20px;
  }}
  .filter-row label {{ font-size: 0.9rem; font-weight: 600; color: var(--text-muted); }}
  select, input[type=number] {{
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.9rem;
    background: var(--surface);
    color: var(--text);
    outline: none;
  }}
  select:focus, input:focus {{ border-color: var(--primary); }}
  .btn {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .btn-primary {{ background: var(--primary); color: #fff; }}
  .btn-primary:hover {{ background: var(--primary-dark); transform: translateY(-1px); }}
  .btn-success {{ background: var(--success); color: #fff; }}
  .btn-success:hover {{ background: #15803d; }}
  .btn-outline {{
    background: transparent;
    border: 2px solid var(--primary);
    color: var(--primary);
  }}
  .btn-outline:hover {{ background: var(--primary); color: #fff; }}
  .btn-sm {{ padding: 6px 14px; font-size: 0.82rem; }}
  .btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none !important; }}

  /* ---- QUIZ ---- */
  #quiz-progress-bar-wrap {{
    background: var(--border);
    border-radius: 99px;
    height: 6px;
    margin-bottom: 20px;
    overflow: hidden;
  }}
  #quiz-progress-bar {{ background: var(--primary); height: 100%; border-radius: 99px; transition: width 0.3s; width: 0%; }}
  .quiz-meta {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    font-size: 0.85rem;
    color: var(--text-muted);
  }}
  #quiz-timer {{
    background: var(--primary);
    color: #fff;
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 0.95rem;
  }}
  #quiz-timer.warning {{ background: var(--warning); }}
  #quiz-timer.danger {{ background: var(--danger); }}
  .question-text {{
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.6;
    margin-bottom: 22px;
  }}
  .question-tag {{
    display: inline-block;
    font-size: 0.75rem;
    background: #ede9fe;
    color: var(--primary);
    padding: 2px 10px;
    border-radius: 99px;
    margin-bottom: 12px;
    font-weight: 600;
  }}
  .options-list {{ list-style: none; display: flex; flex-direction: column; gap: 10px; }}
  .option-item {{
    border: 2px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .option-item:hover:not(.disabled) {{
    border-color: var(--primary-light);
    background: #ede9fe22;
  }}
  .option-item.selected {{ border-color: var(--primary); background: #ede9fe44; }}
  .option-item.correct {{ border-color: var(--success); background: #dcfce7; }}
  .option-item.wrong {{ border-color: var(--danger); background: #fee2e2; }}
  .option-item.disabled {{ cursor: default; }}
  .option-letter {{
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--bg);
    border: 2px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    flex-shrink: 0;
  }}
  .option-item.correct .option-letter {{ background: var(--success); border-color: var(--success); color: #fff; }}
  .option-item.wrong .option-letter {{ background: var(--danger); border-color: var(--danger); color: #fff; }}
  .option-item.selected .option-letter {{ background: var(--primary); border-color: var(--primary); color: #fff; }}
  .explanation-box {{
    margin-top: 18px;
    padding: 14px 16px;
    background: #f1f5f9;
    border-left: 4px solid var(--primary);
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
    line-height: 1.6;
    display: none;
  }}
  .explanation-box.show {{ display: block; }}
  .quiz-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 22px;
    gap: 10px;
  }}
  .question-nav-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 16px;
  }}
  .q-dot {{
    width: 34px;
    height: 34px;
    border-radius: 8px;
    border: 2px solid var(--border);
    background: var(--surface);
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.12s;
  }}
  .q-dot:hover {{ border-color: var(--primary); color: var(--primary); }}
  .q-dot.current {{ border-color: var(--primary); background: var(--primary); color: #fff; }}
  .q-dot.answered {{ border-color: var(--success); background: #dcfce7; color: var(--success); }}
  .q-dot.wrong-answered {{ border-color: var(--danger); background: #fee2e2; color: var(--danger); }}
  .q-dot.skipped {{ border-color: var(--warning); background: #fef9c3; color: var(--warning); }}

  /* ---- RESULTS ---- */
  .result-hero {{ text-align: center; padding: 30px 0; }}
  .result-score-ring {{
    width: 140px;
    height: 140px;
    border-radius: 50%;
    border: 10px solid var(--border);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    margin-bottom: 16px;
    position: relative;
  }}
  .result-score-ring .score-pct {{
    font-size: 2.2rem;
    font-weight: 900;
    color: var(--primary);
  }}
  .result-score-ring .score-label {{
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
  }}
  .result-bars {{ margin-top: 16px; }}
  .result-bar-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 0.88rem;
  }}
  .result-bar-label {{ width: 90px; color: var(--text-muted); }}
  .result-bar-track {{
    flex: 1;
    background: var(--border);
    border-radius: 99px;
    height: 8px;
    overflow: hidden;
  }}
  .result-bar-fill {{ height: 100%; border-radius: 99px; }}
  .result-bar-count {{ width: 40px; text-align: right; font-weight: 700; }}

  /* ---- REVIEW ---- */
  .review-q {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 16px;
  }}
  .review-q .q-number {{
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 6px;
  }}
  .review-q .q-text {{
    font-weight: 600;
    margin-bottom: 14px;
    line-height: 1.55;
  }}
  .review-option {{
    padding: 9px 14px;
    border-radius: 8px;
    border: 2px solid var(--border);
    margin-bottom: 7px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9rem;
  }}
  .review-option.correct-opt {{ border-color: var(--success); background: #dcfce7; }}
  .review-option.user-wrong {{ border-color: var(--danger); background: #fee2e2; }}
  .review-explanation {{
    margin-top: 10px;
    padding: 10px 14px;
    background: #f1f5f9;
    border-left: 4px solid var(--primary);
    border-radius: 0 8px 8px 0;
    font-size: 0.88rem;
    line-height: 1.55;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 700;
  }}
  .badge-correct {{ background: #dcfce7; color: var(--success); }}
  .badge-wrong {{ background: #fee2e2; color: var(--danger); }}
  .badge-skipped {{ background: #fef9c3; color: var(--warning); }}

  /* ---- STATS ---- */
  .history-list {{ margin-top: 12px; }}
  .history-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 10px;
    font-size: 0.9rem;
  }}
  .history-item .h-date {{ color: var(--text-muted); font-size: 0.8rem; flex: 1; }}
  .history-item .h-score {{ font-weight: 800; font-size: 1.1rem; color: var(--primary); }}
  .history-item .h-detail {{ color: var(--text-muted); font-size: 0.82rem; }}
  .subject-breakdown {{ margin-top: 8px; }}
  .sub-row {{
    display: grid;
    grid-template-columns: 1fr 80px 80px;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.88rem;
    align-items: center;
  }}
  .sub-row:last-child {{ border-bottom: none; }}
  .sub-row .sub-name {{ font-weight: 600; }}
  .sub-row .sub-pct {{ text-align: center; font-weight: 700; color: var(--primary); }}
  .sub-row .sub-total {{ text-align: center; color: var(--text-muted); }}

  /* MISC */
  .section-title {{
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 16px;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .divider {{ border: none; border-top: 1px solid var(--border); margin: 20px 0; }}
  .empty-state {{
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
  }}
  .empty-state .icon {{ font-size: 3rem; margin-bottom: 12px; }}
  @media (max-width: 600px) {{
    nav {{ padding: 0 12px; }}
    nav .logo {{ font-size: 0.9rem; }}
    nav .nav-tab {{ padding: 5px 10px; font-size: 0.78rem; }}
    .page {{ padding: 14px; }}
  }}
</style>
</head>
<body>

<nav>
  <div class="logo">&#127979; Quiz Master</div>
  <div class="nav-tabs">
    <button class="nav-tab active" onclick="showPage('home')">Home</button>
    <button class="nav-tab" onclick="showPage('quiz-setup')">Quiz</button>
    <button class="nav-tab" onclick="showPage('review-page')">Review</button>
    <button class="nav-tab" onclick="showPage('stats-page')">Stats</button>
  </div>
  <button class="lang-toggle" onclick="toggleLang()" id="lang-btn">EN / हिं</button>
</nav>

<!-- ============ HOME PAGE ============ -->
<div id="home" class="page active">
  <div class="home-hero">
    <h1 id="home-title">{title_safe}</h1>
    <p id="home-subtitle">Master your subjects with smart practice</p>
  </div>
  <div class="stats-grid" id="home-stats"></div>
  <div class="card">
    <div class="section-title">&#128200; Performance Overview</div>
    <div id="home-overview"></div>
  </div>
  <div class="card">
    <div class="section-title">&#128218; Recent Sessions</div>
    <div id="home-recent"></div>
  </div>
</div>

<!-- ============ QUIZ SETUP PAGE ============ -->
<div id="quiz-setup" class="page">
  <div class="card">
    <div class="section-title">&#9881;&#65039; Quiz Settings</div>
    <div class="filter-row">
      <label>Subject</label>
      <select id="filter-subject">
        <option value="">All Subjects</option>
      </select>
    </div>
    <div class="filter-row">
      <label>Topic</label>
      <select id="filter-topic">
        <option value="">All Topics</option>
      </select>
    </div>
    <div class="filter-row">
      <label>Questions</label>
      <input type="number" id="q-count" min="5" max="200" value="20" style="width:80px"/>
      <span style="font-size:0.85rem;color:var(--text-muted)" id="q-available"></span>
    </div>
    <div class="filter-row">
      <label>Mode</label>
      <select id="quiz-mode">
        <option value="timed">Timed (60s/question)</option>
        <option value="custom">Custom Timer</option>
        <option value="free">No Timer</option>
      </select>
      <input type="number" id="custom-time" min="10" max="300" value="60" style="width:80px;display:none"/>
      <span style="font-size:0.82rem;color:var(--text-muted)" id="custom-time-label" style="display:none"></span>
    </div>
    <div class="filter-row">
      <label>Order</label>
      <select id="quiz-order">
        <option value="random">Random</option>
        <option value="sequential">Sequential</option>
      </select>
    </div>
    <hr class="divider"/>
    <button class="btn btn-primary" onclick="startQuiz()" id="start-btn">&#9654; Start Quiz</button>
    <span id="setup-msg" style="margin-left:12px;font-size:0.85rem;color:var(--danger)"></span>
  </div>
</div>

<!-- ============ QUIZ PAGE ============ -->
<div id="quiz-page" class="page">
  <div id="quiz-progress-bar-wrap"><div id="quiz-progress-bar"></div></div>
  <div class="quiz-meta">
    <span id="quiz-meta-left"></span>
    <span id="quiz-timer">60</span>
    <button class="btn btn-sm btn-outline" onclick="endQuizEarly()">Finish Early</button>
  </div>
  <div class="card" id="quiz-card">
    <div class="question-tag" id="q-tag"></div>
    <div class="question-text" id="q-text"></div>
    <ul class="options-list" id="options-list"></ul>
    <div class="explanation-box" id="explanation-box"></div>
    <div class="quiz-nav">
      <button class="btn btn-outline btn-sm" id="prev-btn" onclick="goQuestion(-1)">&#8592; Prev</button>
      <button class="btn btn-sm" id="skip-btn" onclick="skipQuestion()" style="background:#fef9c3;color:#92400e;border:2px solid #fbbf24;">Skip</button>
      <button class="btn btn-primary btn-sm" id="next-btn" onclick="goQuestion(1)">Next &#8594;</button>
    </div>
  </div>
  <div class="card">
    <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:8px;">Question Navigator</div>
    <div class="question-nav-grid" id="q-nav-grid"></div>
  </div>
</div>

<!-- ============ RESULTS PAGE ============ -->
<div id="results-page" class="page">
  <div class="card result-hero">
    <div class="result-score-ring" id="score-ring">
      <span class="score-pct" id="result-pct">0%</span>
      <span class="score-label">Score</span>
    </div>
    <h2 id="result-heading">Quiz Complete!</h2>
    <p id="result-summary" style="color:var(--text-muted);margin-top:6px;"></p>
  </div>
  <div class="card">
    <div class="section-title">&#128202; Breakdown</div>
    <div class="result-bars" id="result-bars"></div>
  </div>
  <div class="card">
    <div class="section-title">&#128218; Subject Performance</div>
    <div id="result-subject-breakdown"></div>
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;">
    <button class="btn btn-primary" onclick="showPage('review-page')">&#128270; Review Answers</button>
    <button class="btn btn-outline" onclick="showPage('quiz-setup')">&#128257; New Quiz</button>
    <button class="btn btn-outline" onclick="showPage('home')">&#127968; Home</button>
  </div>
</div>

<!-- ============ REVIEW PAGE ============ -->
<div id="review-page" class="page">
  <div class="card">
    <div class="section-title">&#128270; Review Questions</div>
    <div class="filter-row">
      <label>Subject</label>
      <select id="review-subject" onchange="renderReview()">
        <option value="">All Subjects</option>
      </select>
      <label>Filter</label>
      <select id="review-filter" onchange="renderReview()">
        <option value="all">All</option>
        <option value="wrong">Wrong Only</option>
        <option value="correct">Correct Only</option>
        <option value="skipped">Skipped Only</option>
      </select>
    </div>
  </div>
  <div id="review-list"></div>
</div>

<!-- ============ STATS PAGE ============ -->
<div id="stats-page" class="page">
  <div class="stats-grid" id="stats-grid"></div>
  <div class="card">
    <div class="section-title">&#128202; Subject-wise Accuracy</div>
    <div class="subject-breakdown" id="stats-subject"></div>
  </div>
  <div class="card">
    <div class="section-title">&#128337; Session History</div>
    <div class="history-list" id="stats-history"></div>
    <button class="btn btn-sm btn-outline" style="margin-top:10px;border-color:var(--danger);color:var(--danger)" onclick="clearHistory()">&#128465; Clear History</button>
  </div>
</div>

<script>
// ============================================================
//  DATA
// ============================================================
const ALL_QUESTIONS = {q_json};

// ============================================================
//  STATE
// ============================================================
let lang = 'en';  // 'en' or 'hi'
let currentSession = null; // {{questions, answers, skipped, timer, mode}}
let history = [];           // array of session result objects

// ============================================================
//  PERSISTENCE
// ============================================================
function saveHistory() {{
  localStorage.setItem('quiz_history', JSON.stringify(history));
}}
function loadHistory() {{
  try {{
    history = JSON.parse(localStorage.getItem('quiz_history') || '[]');
  }} catch(e) {{ history = []; }}
}}
function clearHistory() {{
  if (!confirm('Clear all history?')) return;
  history = [];
  saveHistory();
  renderStatsPage();
  renderHomePage();
}}

// ============================================================
//  LANGUAGE
// ============================================================
function toggleLang() {{
  lang = lang === 'en' ? 'hi' : 'en';
  document.getElementById('lang-btn').textContent = lang === 'en' ? 'EN / हिं' : 'हिं / EN';
  refreshCurrentPage();
}}
function t(en, hi) {{ return lang === 'en' ? en : (hi || en); }}
function qText(q) {{ return lang === 'en' ? q.qEnglish : (q.qHindi || q.qEnglish); }}
function optList(q) {{ return lang === 'en' ? q.optionsEnglish : (q.optionsHindi || q.optionsEnglish); }}
function expText(q) {{ return lang === 'en' ? (q.explanationEnglish || '') : (q.explanationHindi || q.explanationEnglish || ''); }}
function subjectLabel(q) {{ return lang === 'en' ? (q.subject_en || q.subject || '') : (q.subject || ''); }}
function topicLabel(q) {{ return lang === 'en' ? (q.topic_en || q.topic || '') : (q.topic || ''); }}

// ============================================================
//  PAGE NAVIGATION
// ============================================================
let currentPage = 'home';
function showPage(id) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  const map = {{'home':0,'quiz-setup':1,'quiz-page':1,'results-page':1,'review-page':2,'stats-page':3}};
  const tabs = document.querySelectorAll('.nav-tab');
  if (map[id] !== undefined) tabs[map[id]].classList.add('active');
  currentPage = id;
  if (id === 'home') renderHomePage();
  if (id === 'review-page') renderReview();
  if (id === 'stats-page') renderStatsPage();
}}
function refreshCurrentPage() {{
  if (currentPage === 'home') renderHomePage();
  else if (currentPage === 'quiz-page') renderQuestion();
  else if (currentPage === 'review-page') renderReview();
  else if (currentPage === 'stats-page') renderStatsPage();
  else if (currentPage === 'results-page') renderResults();
}}

// ============================================================
//  SUBJECTS / TOPICS
// ============================================================
function getSubjects() {{
  return [...new Set(ALL_QUESTIONS.map(q => q.subject).filter(Boolean))].sort();
}}
function getTopics(subject) {{
  return [...new Set(
    ALL_QUESTIONS
      .filter(q => !subject || q.subject === subject)
      .map(q => q.topic).filter(Boolean)
  )].sort();
}}
function populateFilters() {{
  const subSel = document.getElementById('filter-subject');
  const subRev = document.getElementById('review-subject');
  getSubjects().forEach(s => {{
    [subSel, subRev].forEach(el => {{
      const o = document.createElement('option');
      o.value = s; o.textContent = s;
      el.appendChild(o);
    }});
  }});
  subSel.addEventListener('change', () => {{
    const topSel = document.getElementById('filter-topic');
    topSel.innerHTML = '<option value="">All Topics</option>';
    getTopics(subSel.value).forEach(t => {{
      const o = document.createElement('option');
      o.value = t; o.textContent = t;
      topSel.appendChild(o);
    }});
    updateAvailable();
  }});
  document.getElementById('q-count').addEventListener('input', updateAvailable);
  updateAvailable();
}}
function updateAvailable() {{
  const sub = document.getElementById('filter-subject').value;
  const top = document.getElementById('filter-topic').value;
  const pool = ALL_QUESTIONS.filter(q =>
    (!sub || q.subject === sub) && (!top || q.topic === top)
  );
  document.getElementById('q-available').textContent = `(${{pool.length}} available)`;
  document.getElementById('q-count').max = pool.length;
}}

// ============================================================
//  QUIZ SETUP
// ============================================================
document.getElementById('quiz-mode').addEventListener('change', function() {{
  const ct = document.getElementById('custom-time');
  ct.style.display = this.value === 'custom' ? '' : 'none';
}});

function startQuiz() {{
  const sub = document.getElementById('filter-subject').value;
  const top = document.getElementById('filter-topic').value;
  const count = parseInt(document.getElementById('q-count').value) || 20;
  const mode = document.getElementById('quiz-mode').value;
  const order = document.getElementById('quiz-order').value;
  const customTime = parseInt(document.getElementById('custom-time').value) || 60;

  let pool = ALL_QUESTIONS.filter(q =>
    (!sub || q.subject === sub) && (!top || q.topic === top)
  );
  if (pool.length === 0) {{ showMsg('No questions match.'); return; }}
  if (count > pool.length) {{ showMsg(`Only ${{pool.length}} questions available.`); return; }}

  let questions = [...pool];
  if (order === 'random') questions = questions.sort(() => Math.random() - 0.5);
  questions = questions.slice(0, count);

  const secPerQ = mode === 'timed' ? 60 : mode === 'custom' ? customTime : null;

  currentSession = {{
    questions,
    answers: new Array(questions.length).fill(null),  // null=unanswered, -1=skipped, 0-3=choice
    currentIdx: 0,
    startTime: Date.now(),
    secPerQ,
    timeLeft: secPerQ,
    timerInterval: null,
    subject: sub || 'All',
    topic: top || 'All',
    revealed: new Array(questions.length).fill(false),
  }};

  buildQuizNav();
  showPage('quiz-page');
  renderQuestion();
  if (secPerQ !== null) startTimer();
}}
function showMsg(m) {{ document.getElementById('setup-msg').textContent = m; }}

// ============================================================
//  QUIZ ENGINE
// ============================================================
function buildQuizNav() {{
  const grid = document.getElementById('q-nav-grid');
  grid.innerHTML = '';
  currentSession.questions.forEach((_, i) => {{
    const d = document.createElement('div');
    d.className = 'q-dot';
    d.textContent = i + 1;
    d.onclick = () => jumpTo(i);
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
    else if (s.answers[i] !== null) {{
      if (s.answers[i] === s.questions[i].correct) d.classList.add('answered');
      else d.classList.add('wrong-answered');
    }}
  }});
}}
function renderQuestion() {{
  const s = currentSession;
  const q = s.questions[s.currentIdx];
  const total = s.questions.length;
  const answered = s.answers.filter(a => a !== null).length;

  document.getElementById('quiz-progress-bar').style.width = ((s.currentIdx + 1) / total * 100) + '%';
  document.getElementById('quiz-meta-left').textContent =
    `Q ${{s.currentIdx + 1}} / ${{total}}  •  Answered: ${{answered}}`;

  document.getElementById('q-tag').textContent =
    `${{subjectLabel(q) || ''}}${{topicLabel(q) ? ' › ' + topicLabel(q) : ''}}`;
  document.getElementById('q-text').textContent = qText(q);

  const opts = optList(q);
  const ul = document.getElementById('options-list');
  ul.innerHTML = '';
  const chosen = s.answers[s.currentIdx];
  const revealed = s.revealed[s.currentIdx];

  opts.forEach((opt, i) => {{
    const li = document.createElement('li');
    li.className = 'option-item';
    if (revealed) li.classList.add('disabled');

    if (revealed) {{
      if (i === q.correct) li.classList.add('correct');
      else if (i === chosen && chosen !== q.correct) li.classList.add('wrong');
    }} else if (i === chosen) {{
      li.classList.add('selected');
    }}

    li.innerHTML = `<span class="option-letter">${{String.fromCharCode(65+i)}}</span><span>${{opt}}</span>`;
    if (!revealed) li.onclick = () => selectOption(i);
    ul.appendChild(li);
  }});

  const expBox = document.getElementById('explanation-box');
  if (revealed && expText(q)) {{
    expBox.textContent = expText(q);
    expBox.classList.add('show');
  }} else {{
    expBox.classList.remove('show');
  }}

  document.getElementById('prev-btn').disabled = s.currentIdx === 0;
  const isLast = s.currentIdx === total - 1;
  const nb = document.getElementById('next-btn');
  nb.textContent = isLast ? 'Finish ✓' : 'Next →';
  nb.onclick = isLast ? finishQuiz : () => goQuestion(1);

  document.getElementById('skip-btn').style.display = revealed ? 'none' : '';

  // reset timer display
  if (s.secPerQ !== null) {{
    s.timeLeft = s.secPerQ;
    updateTimerDisplay();
  }}

  updateNavDots();
}}
function selectOption(i) {{
  const s = currentSession;
  if (s.revealed[s.currentIdx]) return;
  s.answers[s.currentIdx] = i;
  s.revealed[s.currentIdx] = true;
  renderQuestion();
  // auto-advance after short delay if not last
  if (s.currentIdx < s.questions.length - 1) {{
    setTimeout(() => goQuestion(1), 1200);
  }}
}}
function goQuestion(dir) {{
  const s = currentSession;
  const next = s.currentIdx + dir;
  if (next < 0 || next >= s.questions.length) return;
  s.currentIdx = next;
  if (s.secPerQ !== null) {{
    clearInterval(s.timerInterval);
    s.timeLeft = s.secPerQ;
    startTimer();
  }}
  renderQuestion();
}}
function jumpTo(i) {{
  const s = currentSession;
  s.currentIdx = i;
  if (s.secPerQ !== null) {{
    clearInterval(s.timerInterval);
    s.timeLeft = s.secPerQ;
    startTimer();
  }}
  renderQuestion();
}}
function skipQuestion() {{
  const s = currentSession;
  if (s.answers[s.currentIdx] === null) s.answers[s.currentIdx] = -1;
  goQuestion(1);
}}
function endQuizEarly() {{
  if (!confirm('End quiz now and see results?')) return;
  finishQuiz();
}}

// ============================================================
//  TIMER
// ============================================================
function startTimer() {{
  const s = currentSession;
  if (s.secPerQ === null) return;
  clearInterval(s.timerInterval);
  s.timerInterval = setInterval(() => {{
    s.timeLeft--;
    updateTimerDisplay();
    if (s.timeLeft <= 0) {{
      clearInterval(s.timerInterval);
      // time up — mark as skipped if not answered, reveal, auto-advance
      if (s.answers[s.currentIdx] === null) s.answers[s.currentIdx] = -1;
      s.revealed[s.currentIdx] = true;
      renderQuestion();
      if (s.currentIdx < s.questions.length - 1) {{
        setTimeout(() => {{
          goQuestion(1);
          startTimer();
        }}, 1000);
      }} else {{
        setTimeout(finishQuiz, 1000);
      }}
    }}
  }}, 1000);
}}
function updateTimerDisplay() {{
  const s = currentSession;
  if (s.secPerQ === null) {{ document.getElementById('quiz-timer').style.display='none'; return; }}
  const el = document.getElementById('quiz-timer');
  el.style.display = '';
  const t = s.timeLeft;
  el.textContent = `${{Math.floor(t/60)}}:${{String(t%60).padStart(2,'0')}}`;
  el.className = t > s.secPerQ * 0.5 ? 'quiz-timer' : t > 10 ? 'warning' : 'danger';
  el.id = 'quiz-timer';
}}

// ============================================================
//  FINISH
// ============================================================
function finishQuiz() {{
  const s = currentSession;
  clearInterval(s.timerInterval);

  let correct = 0, wrong = 0, skipped = 0;
  const subjectStats = {{}};
  s.questions.forEach((q, i) => {{
    const a = s.answers[i];
    const sub = q.subject || 'Other';
    if (!subjectStats[sub]) subjectStats[sub] = {{correct:0,total:0}};
    subjectStats[sub].total++;
    if (a === -1 || a === null) skipped++;
    else if (a === q.correct) {{ correct++; subjectStats[sub].correct++; }}
    else wrong++;
  }});

  const pct = Math.round(correct / s.questions.length * 100);
  const elapsed = Math.round((Date.now() - s.startTime) / 1000);

  const result = {{
    date: new Date().toISOString(),
    total: s.questions.length,
    correct, wrong, skipped, pct, elapsed,
    subject: s.subject,
    topic: s.topic,
    subjectStats,
    answers: [...s.answers],
    questions: s.questions.map(q => ({{
      qEnglish: q.qEnglish, qHindi: q.qHindi,
      optionsEnglish: q.optionsEnglish, optionsHindi: q.optionsHindi,
      correct: q.correct,
      explanationEnglish: q.explanationEnglish, explanationHindi: q.explanationHindi,
      subject: q.subject, topic: q.topic
    }}))
  }};

  history.unshift(result);
  if (history.length > 50) history = history.slice(0, 50);
  saveHistory();

  currentSession._lastResult = result;

  showPage('results-page');
  renderResults();
}}
function renderResults() {{
  if (!currentSession || !currentSession._lastResult) {{
    document.getElementById('results-page').innerHTML = '<div class="empty-state"><div class="icon">&#128203;</div><p>No quiz taken yet.</p></div>';
    return;
  }}
  const r = currentSession._lastResult;
  document.getElementById('result-pct').textContent = r.pct + '%';
  document.getElementById('result-heading').textContent =
    r.pct >= 80 ? '&#127881; Excellent!' : r.pct >= 60 ? '&#128077; Good Job!' : '&#128170; Keep Practicing!';
  document.getElementById('result-summary').textContent =
    `${{r.correct}} correct, ${{r.wrong}} wrong, ${{r.skipped}} skipped — ${{formatTime(r.elapsed)}}`;

  const ring = document.getElementById('score-ring');
  const color = r.pct >= 80 ? '#16a34a' : r.pct >= 60 ? '#4f46e5' : '#dc2626';
  ring.style.borderColor = color;
  document.getElementById('result-pct').style.color = color;

  // bars
  const bars = document.getElementById('result-bars');
  bars.innerHTML = `
    ${{barRow('Correct', r.correct, r.total, '#16a34a')}}
    ${{barRow('Wrong', r.wrong, r.total, '#dc2626')}}
    ${{barRow('Skipped', r.skipped, r.total, '#d97706')}}
  `;

  // subject breakdown
  const sb = document.getElementById('result-subject-breakdown');
  sb.innerHTML = '<div class="sub-row" style="font-weight:700;color:var(--text-muted);font-size:0.8rem"><span>Subject</span><span style="text-align:center">Accuracy</span><span style="text-align:center">Questions</span></div>';
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

// ============================================================
//  REVIEW PAGE
// ============================================================
function renderReview() {{
  const filterSub = document.getElementById('review-subject').value;
  const filterType = document.getElementById('review-filter').value;

  // Use last session if available, else use all questions
  let items = [];
  if (currentSession && currentSession._lastResult) {{
    const r = currentSession._lastResult;
    r.questions.forEach((q, i) => {{
      const a = r.answers[i];
      let status = a === -1 || a === null ? 'skipped' : a === q.correct ? 'correct' : 'wrong';
      items.push({{q, a, status, idx: i}});
    }});
  }} else {{
    ALL_QUESTIONS.forEach((q, i) => {{
      items.push({{q, a: null, status: 'unanswered', idx: i}});
    }});
  }}

  if (filterSub) items = items.filter(it => it.q.subject === filterSub);
  if (filterType === 'wrong') items = items.filter(it => it.status === 'wrong');
  else if (filterType === 'correct') items = items.filter(it => it.status === 'correct');
  else if (filterType === 'skipped') items = items.filter(it => it.status === 'skipped');

  const list = document.getElementById('review-list');
  if (items.length === 0) {{
    list.innerHTML = '<div class="empty-state"><div class="icon">&#128269;</div><p>No questions to show.</p></div>';
    return;
  }}
  list.innerHTML = items.map((it, n) => reviewCard(it, n + 1)).join('');
}}
function reviewCard(it, n) {{
  const {{q, a, status}} = it;
  const opts = optList(q);
  const optRows = opts.map((opt, i) => {{
    let cls = '';
    if (i === q.correct) cls = 'correct-opt';
    else if (a !== null && a !== -1 && i === a && a !== q.correct) cls = 'user-wrong';
    const icon = i === q.correct ? '&#10003;' : (a !== null && a !== -1 && i === a) ? '&#10007;' : '&#9675;';
    return `<div class="review-option ${{cls}}">${{icon}} ${{String.fromCharCode(65+i)}}. ${{opt}}</div>`;
  }}).join('');

  const badgeCls = status === 'correct' ? 'badge-correct' : status === 'wrong' ? 'badge-wrong' : 'badge-skipped';
  const badgeText = status === 'correct' ? 'Correct' : status === 'wrong' ? 'Wrong' : 'Skipped';
  const subTop = [subjectLabel(q), topicLabel(q)].filter(Boolean).join(' › ');

  return `<div class="review-q">
    <div class="q-number">Q${{n}} — ${{subTop}} <span class="badge ${{badgeCls}}">${{badgeText}}</span></div>
    <div class="q-text">${{qText(q)}}</div>
    ${{optRows}}
    <div class="review-explanation">&#128161; ${{expText(q) || 'No explanation available.'}}</div>
  </div>`;
}}

// ============================================================
//  STATS PAGE
// ============================================================
function renderStatsPage() {{
  if (history.length === 0) {{
    document.getElementById('stats-grid').innerHTML = '';
    document.getElementById('stats-subject').innerHTML = '<div class="empty-state"><div class="icon">&#128202;</div><p>No sessions yet. Take a quiz first!</p></div>';
    document.getElementById('stats-history').innerHTML = '';
    return;
  }}
  const totalQ = history.reduce((s, r) => s + r.total, 0);
  const totalC = history.reduce((s, r) => s + r.correct, 0);
  const avgPct = Math.round(history.reduce((s, r) => s + r.pct, 0) / history.length);
  const best = Math.max(...history.map(r => r.pct));

  document.getElementById('stats-grid').innerHTML = `
    <div class="stat-card"><div class="value">${{history.length}}</div><div class="label">Sessions</div></div>
    <div class="stat-card"><div class="value">${{totalQ}}</div><div class="label">Questions Attempted</div></div>
    <div class="stat-card"><div class="value">${{avgPct}}%</div><div class="label">Average Score</div></div>
    <div class="stat-card"><div class="value">${{best}}%</div><div class="label">Best Score</div></div>
  `;

  // subject accuracy across all sessions
  const subAcc = {{}};
  history.forEach(r => {{
    Object.entries(r.subjectStats || {{}}).forEach(([sub, st]) => {{
      if (!subAcc[sub]) subAcc[sub] = {{correct:0,total:0}};
      subAcc[sub].correct += st.correct;
      subAcc[sub].total += st.total;
    }});
  }});
  const subEl = document.getElementById('stats-subject');
  subEl.innerHTML = '<div class="sub-row" style="font-weight:700;color:var(--text-muted);font-size:0.8rem"><span>Subject</span><span style="text-align:center">Accuracy</span><span style="text-align:center">Attempted</span></div>';
  Object.entries(subAcc).sort((a,b) => b[1].total - a[1].total).forEach(([sub, st]) => {{
    const p = Math.round(st.correct / st.total * 100);
    subEl.innerHTML += `<div class="sub-row"><span class="sub-name">${{sub}}</span><span class="sub-pct">${{p}}%</span><span class="sub-total">${{st.total}}</span></div>`;
  }});

  // history list
  const histEl = document.getElementById('stats-history');
  histEl.innerHTML = history.slice(0, 20).map(r => {{
    const d = new Date(r.date);
    const dateStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {{hour:'2-digit',minute:'2-digit'}});
    return `<div class="history-item">
      <span class="h-score">${{r.pct}}%</span>
      <span class="h-detail">${{r.correct}}/${{r.total}} • ${{r.subject}}${{r.topic !== 'All' ? ' › '+r.topic : ''}}</span>
      <span class="h-date">${{dateStr}}</span>
    </div>`;
  }}).join('');
}}

// ============================================================
//  HOME PAGE
// ============================================================
function renderHomePage() {{
  loadHistory();
  const stats = document.getElementById('home-stats');
  if (history.length === 0) {{
    stats.innerHTML = `<div class="stat-card"><div class="value">${{ALL_QUESTIONS.length}}</div><div class="label">Total Questions</div></div>
      <div class="stat-card"><div class="value">${{getSubjects().length}}</div><div class="label">Subjects</div></div>
      <div class="stat-card"><div class="value">0</div><div class="label">Quizzes Taken</div></div>
      <div class="stat-card"><div class="value">—</div><div class="label">Best Score</div></div>`;
  }} else {{
    const best = Math.max(...history.map(r => r.pct));
    const avg = Math.round(history.reduce((s, r) => s + r.pct, 0) / history.length);
    stats.innerHTML = `<div class="stat-card"><div class="value">${{ALL_QUESTIONS.length}}</div><div class="label">Total Questions</div></div>
      <div class="stat-card"><div class="value">${{getSubjects().length}}</div><div class="label">Subjects</div></div>
      <div class="stat-card"><div class="value">${{history.length}}</div><div class="label">Quizzes Taken</div></div>
      <div class="stat-card"><div class="value">${{best}}%</div><div class="label">Best Score</div></div>
      <div class="stat-card"><div class="value">${{avg}}%</div><div class="label">Avg Score</div></div>`;
  }}

  // overview
  const ov = document.getElementById('home-overview');
  if (history.length === 0) {{
    ov.innerHTML = '<div class="empty-state"><div class="icon">&#127919;</div><p>No quizzes taken yet. Click <strong>Quiz</strong> to get started!</p></div>';
  }} else {{
    const last = history[0];
    const color = last.pct >= 80 ? '#16a34a' : last.pct >= 60 ? '#4f46e5' : '#dc2626';
    ov.innerHTML = `<p style="font-size:0.9rem;color:var(--text-muted);margin-bottom:10px">Last session: <strong style="color:${{color}}">${{last.pct}}%</strong> — ${{last.correct}}/${{last.total}} correct</p>
      ${{barRow('Correct', last.correct, last.total, '#16a34a')}}
      ${{barRow('Wrong', last.wrong, last.total, '#dc2626')}}
      ${{barRow('Skipped', last.skipped, last.total, '#d97706')}}`;
  }}

  // recent
  const rec = document.getElementById('home-recent');
  if (history.length === 0) {{
    rec.innerHTML = '<div style="color:var(--text-muted);font-size:0.9rem">No sessions yet.</div>';
  }} else {{
    rec.innerHTML = history.slice(0, 5).map(r => {{
      const d = new Date(r.date);
      const dateStr = d.toLocaleDateString();
      const color = r.pct >= 80 ? '#16a34a' : r.pct >= 60 ? '#4f46e5' : '#dc2626';
      return `<div class="history-item">
        <span class="h-score" style="color:${{color}}">${{r.pct}}%</span>
        <span class="h-detail">${{r.correct}}/${{r.total}} • ${{r.subject}}</span>
        <span class="h-date">${{dateStr}}</span>
      </div>`;
    }}).join('');
  }}
}}

// ============================================================
//  UTILS
// ============================================================
function formatTime(sec) {{
  if (!sec) return '—';
  const m = Math.floor(sec / 60), s = sec % 60;
  return m > 0 ? `${{m}}m ${{s}}s` : `${{s}}s`;
}}

// ============================================================
//  INIT
// ============================================================
loadHistory();
populateFilters();
renderHomePage();
</script>
</body>
</html>"""
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python quiz_generator.py <input_file.txt|json> [output_file.html]")
        print()
        print("Example:")
        print("  python quiz_generator.py questions.txt")
        print("  python quiz_generator.py questions.json my_quiz.html")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base = Path(input_path).stem
        output_path = str(Path(input_path).parent / (base + "_quiz.html"))

    print(f"Loading questions from: {input_path}")
    try:
        questions = load_questions(input_path)
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON — {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Loaded {len(questions)} questions.")

    subjects = list(set(q.get("subject", "") for q in questions if q.get("subject")))
    print(f"Subjects: {', '.join(sorted(subjects)) or 'N/A'}")

    title = Path(input_path).stem.replace("_", " ").title()
    print(f"Generating HTML quiz: {output_path}")

    html_content = generate_html(questions, title)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"\nDone! Quiz saved to: {output_path} ({size_kb} KB)")
    print(f"\nFeatures included:")
    print(f"  - Quiz mode with timer (60s/question by default, customizable)")
    print(f"  - Subject/topic filtering and random/sequential order")
    print(f"  - Question navigator dots during quiz")
    print(f"  - Auto-reveal answers with explanations")
    print(f"  - Detailed results with subject-wise breakdown")
    print(f"  - Review mode (filter by correct/wrong/skipped)")
    print(f"  - Full statistics with session history (saved in browser)")
    print(f"  - Hindi/English language toggle")
    print(f"\nOpen {output_path} in any browser to start!")


if __name__ == "__main__":
    main()
