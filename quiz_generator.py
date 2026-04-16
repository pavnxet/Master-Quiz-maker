#!/usr/bin/env python3
"""
Quiz HTML Generator — Bilingual Edition
----------------------------------------
Converts a JSON quiz file (array of question objects) into a fully
self-contained, bilingual (Hindi + English) HTML quiz page.

Usage:
    python3 quiz_generator.py <input_file.txt|json> [output_file.html]

Expected JSON format:
    [
      {
        "qHindi": "...",
        "qEnglish": "...",
        "optionsHindi": ["a", "b", "c", "d"],
        "optionsEnglish": ["a", "b", "c", "d"],
        "correct": 1,
        "explanationHindi": "...",
        "explanationEnglish": "...",
        "subject": "...",
        "topic": "..."
      }, ...
    ]
"""

import json
import sys
import os
import html as html_mod
from pathlib import Path


def load_questions(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array of question objects.")
    return data


def generate_html(questions: list, title: str) -> str:
    q_json = json.dumps(questions, ensure_ascii=False)
    title_safe = html_mod.escape(title)

    return f"""<!DOCTYPE html>
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
    --hindi-bg: #fdf4ff;
    --hindi-border: #e9d5ff;
    --hindi-text: #7c3aed;
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

  /* NAV */
  nav {{
    background: var(--primary);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    height: 56px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 12px rgba(79,70,229,0.3);
    gap: 8px;
  }}
  .logo {{ font-weight: 800; font-size: 1rem; white-space: nowrap; }}
  .nav-tabs {{ display: flex; gap: 2px; flex-shrink: 0; }}
  .nav-tab {{
    background: transparent; border: none; color: rgba(255,255,255,0.75);
    cursor: pointer; padding: 6px 12px; border-radius: 8px;
    font-size: 0.82rem; font-weight: 500; transition: all 0.15s; white-space: nowrap;
  }}
  .nav-tab:hover {{ background: rgba(255,255,255,0.15); color: #fff; }}
  .nav-tab.active {{ background: rgba(255,255,255,0.22); color: #fff; font-weight: 700; }}

  /* BILINGUAL BADGE */
  .bilingual-badge {{
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    color: #fff;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    white-space: nowrap;
    flex-shrink: 0;
  }}

  /* PAGES */
  .page {{ display: none; padding: 20px; max-width: 860px; margin: 0 auto; }}
  .page.active {{ display: block; }}

  /* CARDS */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    padding: 22px;
    margin-bottom: 18px;
  }}

  /* HOME */
  .home-hero {{ text-align: center; padding: 32px 16px 24px; }}
  .home-hero h1 {{ font-size: 1.8rem; color: var(--primary); margin-bottom: 6px; }}
  .home-hero p {{ color: var(--text-muted); font-size: 0.92rem; }}
  .bilingual-pill {{
    display: inline-block;
    background: linear-gradient(90deg, #4f46e5 50%, #7c3aed 50%);
    color: #fff;
    border-radius: 99px;
    padding: 3px 14px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-top: 8px;
    letter-spacing: 0.05em;
  }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 14px;
    margin: 20px 0;
  }}
  .stat-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px; text-align: center;
    box-shadow: var(--shadow-sm);
  }}
  .stat-card .value {{ font-size: 1.9rem; font-weight: 800; color: var(--primary); }}
  .stat-card .label {{ font-size: 0.78rem; color: var(--text-muted); margin-top: 3px; }}

  /* FILTERS */
  .filter-row {{
    display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 18px;
  }}
  .filter-row label {{ font-size: 0.88rem; font-weight: 600; color: var(--text-muted); }}
  select, input[type=number] {{
    border: 1px solid var(--border); border-radius: 8px; padding: 7px 11px;
    font-size: 0.88rem; background: var(--surface); color: var(--text); outline: none;
  }}
  select:focus, input:focus {{ border-color: var(--primary); }}

  /* BUTTONS */
  .btn {{
    display: inline-flex; align-items: center; gap: 6px; border: none;
    border-radius: 8px; padding: 9px 18px; font-size: 0.88rem;
    font-weight: 600; cursor: pointer; transition: all 0.15s;
  }}
  .btn-primary {{ background: var(--primary); color: #fff; }}
  .btn-primary:hover {{ background: var(--primary-dark); transform: translateY(-1px); }}
  .btn-outline {{ background: transparent; border: 2px solid var(--primary); color: var(--primary); }}
  .btn-outline:hover {{ background: var(--primary); color: #fff; }}
  .btn-sm {{ padding: 5px 12px; font-size: 0.8rem; }}
  .btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none !important; }}

  /* QUIZ */
  #quiz-progress-bar-wrap {{
    background: var(--border); border-radius: 99px; height: 6px;
    margin-bottom: 18px; overflow: hidden;
  }}
  #quiz-progress-bar {{
    background: linear-gradient(90deg, var(--primary), #7c3aed);
    height: 100%; border-radius: 99px; transition: width 0.3s; width: 0%;
  }}
  .quiz-meta {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 14px; font-size: 0.83rem; color: var(--text-muted);
  }}
  #quiz-timer {{
    background: var(--primary); color: #fff; border-radius: 20px;
    padding: 3px 13px; font-weight: 700; font-size: 0.92rem;
  }}
  #quiz-timer.warning {{ background: var(--warning); }}
  #quiz-timer.danger {{ background: var(--danger); }}

  /* BILINGUAL QUESTION */
  .question-tag {{
    display: inline-block; font-size: 0.73rem; background: #ede9fe;
    color: var(--primary); padding: 2px 10px; border-radius: 99px;
    margin-bottom: 10px; font-weight: 600;
  }}
  .question-block {{ margin-bottom: 18px; }}
  .q-english {{
    font-size: 1.05rem; font-weight: 700; line-height: 1.55;
    color: var(--text); margin-bottom: 7px;
  }}
  .q-hindi {{
    font-size: 0.97rem; font-weight: 500; line-height: 1.6;
    color: var(--hindi-text); background: var(--hindi-bg);
    border-left: 3px solid var(--hindi-border);
    padding: 7px 12px; border-radius: 0 8px 8px 0;
  }}

  /* BILINGUAL OPTIONS */
  .options-list {{ list-style: none; display: flex; flex-direction: column; gap: 9px; }}
  .option-item {{
    border: 2px solid var(--border); border-radius: 10px;
    padding: 11px 14px; cursor: pointer; transition: all 0.15s;
    display: flex; align-items: flex-start; gap: 11px;
  }}
  .option-item:hover:not(.disabled) {{ border-color: var(--primary-light); background: #ede9fe18; }}
  .option-item.selected {{ border-color: var(--primary); background: #ede9fe33; }}
  .option-item.correct {{ border-color: var(--success); background: #dcfce7; }}
  .option-item.wrong {{ border-color: var(--danger); background: #fee2e2; }}
  .option-item.disabled {{ cursor: default; }}
  .option-letter {{
    width: 30px; height: 30px; border-radius: 50%; background: var(--bg);
    border: 2px solid var(--border); display: flex; align-items: center;
    justify-content: center; font-weight: 700; font-size: 0.82rem;
    flex-shrink: 0; margin-top: 2px;
  }}
  .option-item.correct .option-letter {{ background: var(--success); border-color: var(--success); color: #fff; }}
  .option-item.wrong .option-letter {{ background: var(--danger); border-color: var(--danger); color: #fff; }}
  .option-item.selected .option-letter {{ background: var(--primary); border-color: var(--primary); color: #fff; }}
  .option-texts {{ display: flex; flex-direction: column; gap: 2px; }}
  .opt-english {{ font-size: 0.93rem; font-weight: 600; color: var(--text); }}
  .opt-hindi {{ font-size: 0.83rem; color: var(--hindi-text); font-weight: 400; }}

  /* EXPLANATION BOX — BILINGUAL */
  .explanation-box {{
    margin-top: 16px; border-radius: 10px; overflow: hidden;
    display: none; border: 1px solid var(--border);
  }}
  .explanation-box.show {{ display: block; }}
  .exp-english {{
    padding: 12px 16px; background: #f0fdf4;
    border-left: 4px solid var(--success);
    font-size: 0.88rem; line-height: 1.6; color: var(--text);
  }}
  .exp-english::before {{
    content: '💡 '; font-size: 0.9rem;
  }}
  .exp-hindi {{
    padding: 12px 16px; background: var(--hindi-bg);
    border-left: 4px solid var(--hindi-border);
    font-size: 0.88rem; line-height: 1.6; color: var(--hindi-text);
    border-top: 1px solid var(--border);
  }}
  .exp-hindi::before {{
    content: '💡 '; font-size: 0.9rem;
  }}

  /* NAV DOTS */
  .quiz-nav {{
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 20px; gap: 8px;
  }}
  .question-nav-grid {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 14px; }}
  .q-dot {{
    width: 32px; height: 32px; border-radius: 7px; border: 2px solid var(--border);
    background: var(--surface); cursor: pointer; font-size: 0.78rem; font-weight: 600;
    color: var(--text-muted); display: flex; align-items: center;
    justify-content: center; transition: all 0.12s;
  }}
  .q-dot:hover {{ border-color: var(--primary); color: var(--primary); }}
  .q-dot.current {{ border-color: var(--primary); background: var(--primary); color: #fff; }}
  .q-dot.answered {{ border-color: var(--success); background: #dcfce7; color: var(--success); }}
  .q-dot.wrong-answered {{ border-color: var(--danger); background: #fee2e2; color: var(--danger); }}
  .q-dot.skipped {{ border-color: var(--warning); background: #fef9c3; color: var(--warning); }}

  /* RESULTS */
  .result-hero {{ text-align: center; padding: 28px 0; }}
  .result-score-ring {{
    width: 130px; height: 130px; border-radius: 50%; border: 10px solid var(--border);
    display: inline-flex; align-items: center; justify-content: center;
    flex-direction: column; margin-bottom: 14px;
  }}
  .score-pct {{ font-size: 2rem; font-weight: 900; color: var(--primary); }}
  .score-label {{ font-size: 0.72rem; color: var(--text-muted); font-weight: 600; }}
  .result-bars {{ margin-top: 14px; }}
  .result-bar-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 9px; font-size: 0.86rem; }}
  .result-bar-label {{ width: 80px; color: var(--text-muted); }}
  .result-bar-track {{ flex: 1; background: var(--border); border-radius: 99px; height: 7px; overflow: hidden; }}
  .result-bar-fill {{ height: 100%; border-radius: 99px; }}
  .result-bar-count {{ width: 36px; text-align: right; font-weight: 700; }}

  /* REVIEW — BILINGUAL */
  .review-q {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px; margin-bottom: 14px;
  }}
  .review-q .q-number {{ font-size: 0.78rem; color: var(--text-muted); margin-bottom: 6px; }}
  .review-q .q-english {{ font-weight: 700; margin-bottom: 5px; line-height: 1.5; font-size: 1rem; }}
  .review-q .q-hindi {{ font-size: 0.9rem; color: var(--hindi-text); margin-bottom: 12px; }}
  .review-option {{
    padding: 8px 13px; border-radius: 8px; border: 2px solid var(--border);
    margin-bottom: 6px; display: flex; align-items: flex-start; gap: 9px; font-size: 0.88rem;
  }}
  .review-option.correct-opt {{ border-color: var(--success); background: #dcfce7; }}
  .review-option.user-wrong {{ border-color: var(--danger); background: #fee2e2; }}
  .review-option .opt-english {{ font-weight: 600; }}
  .review-option .opt-hindi {{ font-size: 0.8rem; color: var(--hindi-text); }}
  .review-exp-en {{
    padding: 9px 13px; background: #f0fdf4; border-left: 4px solid var(--success);
    font-size: 0.85rem; line-height: 1.55;
  }}
  .review-exp-hi {{
    padding: 9px 13px; background: var(--hindi-bg); border-left: 4px solid var(--hindi-border);
    font-size: 0.85rem; line-height: 1.55; color: var(--hindi-text);
    border-top: 1px solid var(--border);
  }}
  .review-exp-wrap {{
    margin-top: 10px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
  }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 0.72rem; font-weight: 700;
  }}
  .badge-correct {{ background: #dcfce7; color: var(--success); }}
  .badge-wrong {{ background: #fee2e2; color: var(--danger); }}
  .badge-skipped {{ background: #fef9c3; color: var(--warning); }}

  /* STATS */
  .history-item {{
    display: flex; align-items: center; gap: 10px; padding: 10px 14px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 9px; margin-bottom: 8px; font-size: 0.88rem;
  }}
  .h-score {{ font-weight: 800; font-size: 1.05rem; color: var(--primary); }}
  .h-detail {{ color: var(--text-muted); font-size: 0.8rem; flex: 1; }}
  .h-date {{ color: var(--text-muted); font-size: 0.78rem; }}
  .sub-row {{
    display: grid; grid-template-columns: 1fr 70px 70px;
    gap: 8px; padding: 7px 0; border-bottom: 1px solid var(--border);
    font-size: 0.86rem; align-items: center;
  }}
  .sub-row:last-child {{ border-bottom: none; }}
  .sub-name {{ font-weight: 600; }}
  .sub-pct {{ text-align: center; font-weight: 700; color: var(--primary); }}
  .sub-total {{ text-align: center; color: var(--text-muted); }}

  /* MISC */
  .section-title {{
    font-size: 1.05rem; font-weight: 700; margin-bottom: 14px;
    color: var(--text); display: flex; align-items: center; gap: 7px;
  }}
  .divider {{ border: none; border-top: 1px solid var(--border); margin: 18px 0; }}
  .empty-state {{ text-align: center; padding: 36px 16px; color: var(--text-muted); }}
  .empty-state .icon {{ font-size: 2.8rem; margin-bottom: 10px; }}
  .lang-divider {{
    display: flex; align-items: center; gap: 8px; margin: 6px 0;
    font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em;
  }}
  .lang-divider::before, .lang-divider::after {{
    content: ''; flex: 1; height: 1px; background: var(--border);
  }}
  @media (max-width: 600px) {{
    nav {{ padding: 0 10px; gap: 6px; }}
    .logo {{ font-size: 0.85rem; }}
    .nav-tab {{ padding: 5px 8px; font-size: 0.75rem; }}
    .page {{ padding: 12px; }}
    .q-english {{ font-size: 0.97rem; }}
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
  <div class="bilingual-badge">EN + हिं</div>
</nav>

<!-- HOME -->
<div id="home" class="page active">
  <div class="home-hero">
    <h1>{title_safe}</h1>
    <p>Bilingual quiz — English &amp; Hindi together</p>
    <div class="bilingual-pill">ENGLISH + हिंदी</div>
  </div>
  <div class="stats-grid" id="home-stats"></div>
  <div class="card">
    <div class="section-title">&#128200; Last Performance</div>
    <div id="home-overview"></div>
  </div>
  <div class="card">
    <div class="section-title">&#128337; Recent Sessions</div>
    <div id="home-recent"></div>
  </div>
</div>

<!-- QUIZ SETUP -->
<div id="quiz-setup" class="page">
  <div class="card">
    <div class="section-title">&#9881;&#65039; Quiz Settings</div>
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
      <input type="number" id="q-count" min="5" max="200" value="20" style="width:75px"/>
      <span style="font-size:0.83rem;color:var(--text-muted)" id="q-available"></span>
    </div>
    <div class="filter-row">
      <label>Timer</label>
      <select id="quiz-mode">
        <option value="timed">60s per question</option>
        <option value="custom">Custom timer</option>
        <option value="free">No timer</option>
      </select>
      <input type="number" id="custom-time" min="10" max="300" value="60" style="width:75px;display:none"/>
    </div>
    <div class="filter-row">
      <label>Order</label>
      <select id="quiz-order">
        <option value="random">Random</option>
        <option value="sequential">Sequential</option>
      </select>
    </div>
    <hr class="divider"/>
    <button class="btn btn-primary" onclick="startQuiz()">&#9654; Start Quiz</button>
    <span id="setup-msg" style="margin-left:10px;font-size:0.83rem;color:var(--danger)"></span>
  </div>
</div>

<!-- QUIZ PAGE -->
<div id="quiz-page" class="page">
  <div id="quiz-progress-bar-wrap"><div id="quiz-progress-bar"></div></div>
  <div class="quiz-meta">
    <span id="quiz-meta-left"></span>
    <span id="quiz-timer">60</span>
    <button class="btn btn-sm btn-outline" onclick="endQuizEarly()">Finish Early</button>
  </div>
  <div class="card" id="quiz-card">
    <div class="question-tag" id="q-tag"></div>
    <div class="question-block">
      <div class="q-english" id="q-english"></div>
      <div class="lang-divider">हिंदी</div>
      <div class="q-hindi" id="q-hindi"></div>
    </div>
    <ul class="options-list" id="options-list"></ul>
    <div class="explanation-box" id="explanation-box">
      <div class="exp-english" id="exp-english"></div>
      <div class="exp-hindi" id="exp-hindi"></div>
    </div>
    <div class="quiz-nav">
      <button class="btn btn-outline btn-sm" id="prev-btn" onclick="goQuestion(-1)">&#8592; Prev</button>
      <button class="btn btn-sm" id="skip-btn" onclick="skipQuestion()" style="background:#fef9c3;color:#92400e;border:2px solid #fbbf24;">Skip</button>
      <button class="btn btn-primary btn-sm" id="next-btn" onclick="goQuestion(1)">Next &#8594;</button>
    </div>
  </div>
  <div class="card">
    <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:7px;">Question Navigator</div>
    <div class="question-nav-grid" id="q-nav-grid"></div>
  </div>
</div>

<!-- RESULTS -->
<div id="results-page" class="page">
  <div class="card result-hero">
    <div class="result-score-ring" id="score-ring">
      <span class="score-pct" id="result-pct">0%</span>
      <span class="score-label">Score</span>
    </div>
    <h2 id="result-heading">Quiz Complete!</h2>
    <p id="result-summary" style="color:var(--text-muted);margin-top:5px;font-size:0.9rem;"></p>
  </div>
  <div class="card">
    <div class="section-title">&#128202; Breakdown</div>
    <div class="result-bars" id="result-bars"></div>
  </div>
  <div class="card">
    <div class="section-title">&#128218; Subject Performance</div>
    <div id="result-subject-breakdown"></div>
  </div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;">
    <button class="btn btn-primary" onclick="showPage('review-page')">&#128270; Review Answers</button>
    <button class="btn btn-outline" onclick="showPage('quiz-setup')">&#128257; New Quiz</button>
    <button class="btn btn-outline" onclick="showPage('home')">&#127968; Home</button>
  </div>
</div>

<!-- REVIEW PAGE -->
<div id="review-page" class="page">
  <div class="card">
    <div class="section-title">&#128270; Review Questions (EN + हिं)</div>
    <div class="filter-row">
      <label>Subject</label>
      <select id="review-subject" onchange="renderReview()"><option value="">All</option></select>
      <label>Filter</label>
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

<!-- STATS PAGE -->
<div id="stats-page" class="page">
  <div class="stats-grid" id="stats-grid"></div>
  <div class="card">
    <div class="section-title">&#128202; Subject-wise Accuracy</div>
    <div id="stats-subject"></div>
  </div>
  <div class="card">
    <div class="section-title">&#128337; Session History</div>
    <div id="stats-history"></div>
    <button class="btn btn-sm btn-outline" style="margin-top:10px;border-color:var(--danger);color:var(--danger)" onclick="clearHistory()">&#128465; Clear History</button>
  </div>
</div>

<script>
const ALL_QUESTIONS = {q_json};

// ---- STATE ----
let currentSession = null;
let history = [];

// ---- PERSISTENCE ----
function saveHistory() {{ localStorage.setItem('quiz_history_v2', JSON.stringify(history)); }}
function loadHistory() {{ try {{ history = JSON.parse(localStorage.getItem('quiz_history_v2') || '[]'); }} catch(e) {{ history = []; }} }}
function clearHistory() {{ if (!confirm('Clear all history?')) return; history = []; saveHistory(); renderStatsPage(); renderHomePage(); }}

// ---- PAGE NAV ----
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
}}

// ---- SUBJECTS / TOPICS ----
function getSubjects() {{ return [...new Set(ALL_QUESTIONS.map(q => q.subject).filter(Boolean))].sort(); }}
function getTopics(sub) {{
  return [...new Set(ALL_QUESTIONS.filter(q => !sub || q.subject === sub).map(q => q.topic).filter(Boolean))].sort();
}}
function populateFilters() {{
  const subSel = document.getElementById('filter-subject');
  const revSub = document.getElementById('review-subject');
  getSubjects().forEach(s => {{
    [subSel, revSub].forEach(el => {{ const o = document.createElement('option'); o.value = s; o.textContent = s; el.appendChild(o); }});
  }});
  subSel.addEventListener('change', () => {{
    const topSel = document.getElementById('filter-topic');
    topSel.innerHTML = '<option value="">All Topics</option>';
    getTopics(subSel.value).forEach(t => {{ const o = document.createElement('option'); o.value = t; o.textContent = t; topSel.appendChild(o); }});
    updateAvailable();
  }});
  document.getElementById('q-count').addEventListener('input', updateAvailable);
  updateAvailable();
}}
function updateAvailable() {{
  const sub = document.getElementById('filter-subject').value;
  const top = document.getElementById('filter-topic').value;
  const pool = ALL_QUESTIONS.filter(q => (!sub || q.subject === sub) && (!top || q.topic === top));
  document.getElementById('q-available').textContent = `(${{pool.length}} available)`;
  document.getElementById('q-count').max = pool.length;
}}
document.getElementById('quiz-mode').addEventListener('change', function() {{
  document.getElementById('custom-time').style.display = this.value === 'custom' ? '' : 'none';
}});

// ---- START QUIZ ----
function startQuiz() {{
  const sub = document.getElementById('filter-subject').value;
  const top = document.getElementById('filter-topic').value;
  const count = parseInt(document.getElementById('q-count').value) || 20;
  const mode = document.getElementById('quiz-mode').value;
  const order = document.getElementById('quiz-order').value;
  const customTime = parseInt(document.getElementById('custom-time').value) || 60;
  let pool = ALL_QUESTIONS.filter(q => (!sub || q.subject === sub) && (!top || q.topic === top));
  if (!pool.length) {{ document.getElementById('setup-msg').textContent = 'No questions match.'; return; }}
  if (count > pool.length) {{ document.getElementById('setup-msg').textContent = `Only ${{pool.length}} available.`; return; }}
  let questions = [...pool];
  if (order === 'random') questions = questions.sort(() => Math.random() - 0.5);
  questions = questions.slice(0, count);
  const secPerQ = mode === 'timed' ? 60 : mode === 'custom' ? customTime : null;
  currentSession = {{
    questions, answers: new Array(questions.length).fill(null),
    currentIdx: 0, startTime: Date.now(), secPerQ, timeLeft: secPerQ,
    timerInterval: null, subject: sub || 'All', topic: top || 'All',
    revealed: new Array(questions.length).fill(false),
  }};
  buildQuizNav();
  showPage('quiz-page');
  renderQuestion();
  if (secPerQ !== null) startTimer();
}}

// ---- QUIZ ENGINE ----
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
    else if (s.answers[i] !== null) {{
      d.classList.add(s.answers[i] === s.questions[i].correct ? 'answered' : 'wrong-answered');
    }}
  }});
}}
function renderQuestion() {{
  const s = currentSession;
  const q = s.questions[s.currentIdx];
  const total = s.questions.length;
  const answered = s.answers.filter(a => a !== null).length;

  document.getElementById('quiz-progress-bar').style.width = ((s.currentIdx + 1) / total * 100) + '%';
  document.getElementById('quiz-meta-left').textContent = `Q ${{s.currentIdx+1}} / ${{total}}  ·  Answered: ${{answered}}`;

  // Subject/topic tag
  const tag = [q.subject, q.topic].filter(Boolean).join(' › ');
  document.getElementById('q-tag').textContent = tag;

  // Bilingual question — ALWAYS both
  document.getElementById('q-english').textContent = q.qEnglish || '';
  document.getElementById('q-hindi').textContent = q.qHindi || '';

  // Hide Hindi section if no Hindi data
  const hindiDivider = document.querySelector('.lang-divider');
  const hindiQ = document.getElementById('q-hindi');
  const hasHindi = !!(q.qHindi);
  hindiDivider.style.display = hasHindi ? '' : 'none';
  hindiQ.style.display = hasHindi ? '' : 'none';

  // Options — bilingual
  const optsEn = q.optionsEnglish || [];
  const optsHi = q.optionsHindi || [];
  const ul = document.getElementById('options-list');
  ul.innerHTML = '';
  const chosen = s.answers[s.currentIdx];
  const revealed = s.revealed[s.currentIdx];

  optsEn.forEach((opt, i) => {{
    const li = document.createElement('li');
    li.className = 'option-item';
    if (revealed) li.classList.add('disabled');
    if (revealed) {{
      if (i === q.correct) li.classList.add('correct');
      else if (i === chosen && chosen !== q.correct) li.classList.add('wrong');
    }} else if (i === chosen) {{
      li.classList.add('selected');
    }}
    const hindiOpt = optsHi[i] || '';
    li.innerHTML = `
      <span class="option-letter">${{String.fromCharCode(65+i)}}</span>
      <span class="option-texts">
        <span class="opt-english">${{opt}}</span>
        ${{hindiOpt ? `<span class="opt-hindi">${{hindiOpt}}</span>` : ''}}
      </span>`;
    if (!revealed) li.onclick = () => selectOption(i);
    ul.appendChild(li);
  }});

  // Explanation — bilingual
  const expBox = document.getElementById('explanation-box');
  if (revealed) {{
    document.getElementById('exp-english').textContent = q.explanationEnglish || '';
    document.getElementById('exp-hindi').textContent = q.explanationHindi || '';
    document.getElementById('exp-hindi').style.display = q.explanationHindi ? '' : 'none';
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

  if (s.secPerQ !== null) {{ s.timeLeft = s.secPerQ; updateTimerDisplay(); }}
  updateNavDots();
}}
function selectOption(i) {{
  const s = currentSession;
  if (s.revealed[s.currentIdx]) return;
  s.answers[s.currentIdx] = i;
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
function endQuizEarly() {{ if (confirm('End quiz now?')) finishQuiz(); }}

// ---- TIMER ----
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
  el.id = 'quiz-timer';
  el.className = t > s.secPerQ * 0.5 ? '' : t > 10 ? 'warning' : 'danger';
}}

// ---- FINISH ----
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
    date: new Date().toISOString(), total: s.questions.length,
    correct, wrong, skipped, pct, elapsed,
    subject: s.subject, topic: s.topic, subjectStats,
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
  renderResults();
}}
function renderResults() {{
  if (!currentSession?._lastResult) return;
  const r = currentSession._lastResult;
  document.getElementById('result-pct').textContent = r.pct + '%';
  document.getElementById('result-heading').textContent =
    r.pct >= 80 ? '🎉 Excellent!' : r.pct >= 60 ? '👍 Good Job!' : '💪 Keep Practicing!';
  document.getElementById('result-summary').textContent =
    `${{r.correct}} correct · ${{r.wrong}} wrong · ${{r.skipped}} skipped · ${{fmtTime(r.elapsed)}}`;
  const color = r.pct >= 80 ? '#16a34a' : r.pct >= 60 ? '#4f46e5' : '#dc2626';
  const ring = document.getElementById('score-ring');
  ring.style.borderColor = color;
  document.getElementById('result-pct').style.color = color;
  document.getElementById('result-bars').innerHTML =
    barRow('Correct', r.correct, r.total, '#16a34a') +
    barRow('Wrong', r.wrong, r.total, '#dc2626') +
    barRow('Skipped', r.skipped, r.total, '#d97706');
  const sb = document.getElementById('result-subject-breakdown');
  sb.innerHTML = '<div class="sub-row" style="font-weight:700;font-size:0.78rem;color:var(--text-muted)"><span>Subject</span><span style="text-align:center">Acc.</span><span style="text-align:center">Qs</span></div>';
  Object.entries(r.subjectStats).forEach(([sub,st]) => {{
    const p = Math.round(st.correct/st.total*100);
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

// ---- REVIEW ----
function renderReview() {{
  const filterSub = document.getElementById('review-subject').value;
  const filterType = document.getElementById('review-filter').value;
  let items = [];
  if (currentSession?._lastResult) {{
    const r = currentSession._lastResult;
    r.questions.forEach((q, i) => {{
      const a = r.answers[i];
      const status = (a === -1 || a === null) ? 'skipped' : a === q.correct ? 'correct' : 'wrong';
      items.push({{q, a, status, idx: i}});
    }});
  }} else {{
    ALL_QUESTIONS.forEach((q, i) => items.push({{q, a: null, status: 'unanswered', idx: i}}));
  }}
  if (filterSub) items = items.filter(it => it.q.subject === filterSub);
  if (filterType === 'wrong') items = items.filter(it => it.status === 'wrong');
  else if (filterType === 'correct') items = items.filter(it => it.status === 'correct');
  else if (filterType === 'skipped') items = items.filter(it => it.status === 'skipped');

  const list = document.getElementById('review-list');
  if (!items.length) {{ list.innerHTML = '<div class="empty-state"><div class="icon">&#128269;</div><p>No questions.</p></div>'; return; }}
  list.innerHTML = items.map((it, n) => reviewCard(it, n+1)).join('');
}}
function reviewCard({{q, a, status}}, n) {{
  const optsEn = q.optionsEnglish || [];
  const optsHi = q.optionsHindi || [];
  const optRows = optsEn.map((opt, i) => {{
    let cls = '';
    if (i === q.correct) cls = 'correct-opt';
    else if (a !== null && a !== -1 && i === a && a !== q.correct) cls = 'user-wrong';
    const icon = i === q.correct ? '✓' : (a !== null && a !== -1 && i === a) ? '✗' : '○';
    const hiOpt = optsHi[i] || '';
    return `<div class="review-option ${{cls}}">
      <span style="font-weight:700;width:20px;flex-shrink:0">${{icon}} ${{String.fromCharCode(65+i)}}</span>
      <span class="option-texts">
        <span class="opt-english">${{opt}}</span>
        ${{hiOpt ? `<span class="opt-hindi">${{hiOpt}}</span>` : ''}}
      </span>
    </div>`;
  }}).join('');
  const badgeCls = status === 'correct' ? 'badge-correct' : status === 'wrong' ? 'badge-wrong' : 'badge-skipped';
  const badgeText = status === 'correct' ? 'Correct' : status === 'wrong' ? 'Wrong' : 'Skipped';
  const subTop = [q.subject, q.topic].filter(Boolean).join(' › ');
  const expEn = q.explanationEnglish || '';
  const expHi = q.explanationHindi || '';
  return `<div class="review-q">
    <div class="q-number">Q${{n}} — ${{subTop}} <span class="badge ${{badgeCls}}">${{badgeText}}</span></div>
    <div class="q-english">${{q.qEnglish || ''}}</div>
    ${{q.qHindi ? `<div class="q-hindi">${{q.qHindi}}</div>` : ''}}
    ${{optRows}}
    <div class="review-exp-wrap">
      ${{expEn ? `<div class="review-exp-en">💡 ${{expEn}}</div>` : ''}}
      ${{expHi ? `<div class="review-exp-hi">💡 ${{expHi}}</div>` : ''}}
    </div>
  </div>`;
}}

// ---- STATS ----
function renderStatsPage() {{
  if (!history.length) {{
    document.getElementById('stats-grid').innerHTML = '';
    document.getElementById('stats-subject').innerHTML = '<div class="empty-state"><div class="icon">&#128202;</div><p>Take a quiz first!</p></div>';
    document.getElementById('stats-history').innerHTML = '';
    return;
  }}
  const totalQ = history.reduce((s,r) => s+r.total, 0);
  const avgPct = Math.round(history.reduce((s,r) => s+r.pct, 0) / history.length);
  const best = Math.max(...history.map(r => r.pct));
  document.getElementById('stats-grid').innerHTML = `
    <div class="stat-card"><div class="value">${{history.length}}</div><div class="label">Sessions</div></div>
    <div class="stat-card"><div class="value">${{totalQ}}</div><div class="label">Attempted</div></div>
    <div class="stat-card"><div class="value">${{avgPct}}%</div><div class="label">Average</div></div>
    <div class="stat-card"><div class="value">${{best}}%</div><div class="label">Best</div></div>`;
  const subAcc = {{}};
  history.forEach(r => Object.entries(r.subjectStats||{{}}).forEach(([sub,st]) => {{
    if (!subAcc[sub]) subAcc[sub] = {{correct:0,total:0}};
    subAcc[sub].correct += st.correct; subAcc[sub].total += st.total;
  }}));
  const subEl = document.getElementById('stats-subject');
  subEl.innerHTML = '<div class="sub-row" style="font-weight:700;font-size:0.78rem;color:var(--text-muted)"><span>Subject</span><span style="text-align:center">Acc.</span><span style="text-align:center">Qs</span></div>';
  Object.entries(subAcc).sort((a,b)=>b[1].total-a[1].total).forEach(([sub,st]) => {{
    const p = Math.round(st.correct/st.total*100);
    subEl.innerHTML += `<div class="sub-row"><span class="sub-name">${{sub}}</span><span class="sub-pct">${{p}}%</span><span class="sub-total">${{st.total}}</span></div>`;
  }});
  document.getElementById('stats-history').innerHTML = history.slice(0,20).map(r => {{
    const d = new Date(r.date);
    const ds = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});
    const color = r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';
    return `<div class="history-item">
      <span class="h-score" style="color:${{color}}">${{r.pct}}%</span>
      <span class="h-detail">${{r.correct}}/${{r.total}} · ${{r.subject}}</span>
      <span class="h-date">${{ds}}</span>
    </div>`;
  }}).join('');
}}

// ---- HOME ----
function renderHomePage() {{
  loadHistory();
  const stats = document.getElementById('home-stats');
  const best = history.length ? Math.max(...history.map(r=>r.pct)) : null;
  const avg = history.length ? Math.round(history.reduce((s,r)=>s+r.pct,0)/history.length) : null;
  stats.innerHTML = `
    <div class="stat-card"><div class="value">${{ALL_QUESTIONS.length}}</div><div class="label">Total Questions</div></div>
    <div class="stat-card"><div class="value">${{getSubjects().length}}</div><div class="label">Subjects</div></div>
    <div class="stat-card"><div class="value">${{history.length}}</div><div class="label">Sessions</div></div>
    ${{best!==null ? `<div class="stat-card"><div class="value">${{best}}%</div><div class="label">Best Score</div></div>` : ''}}
    ${{avg!==null ? `<div class="stat-card"><div class="value">${{avg}}%</div><div class="label">Avg Score</div></div>` : ''}}`;
  const ov = document.getElementById('home-overview');
  if (!history.length) {{
    ov.innerHTML = '<div class="empty-state"><div class="icon">&#127919;</div><p>No sessions yet. Click <strong>Quiz</strong> to start!</p></div>';
  }} else {{
    const last = history[0];
    const color = last.pct>=80?'#16a34a':last.pct>=60?'#4f46e5':'#dc2626';
    ov.innerHTML = `<p style="font-size:0.88rem;color:var(--text-muted);margin-bottom:10px">Last: <strong style="color:${{color}}">${{last.pct}}%</strong> — ${{last.correct}}/${{last.total}} correct</p>
      ${{barRow('Correct',last.correct,last.total,'#16a34a')}}${{barRow('Wrong',last.wrong,last.total,'#dc2626')}}${{barRow('Skipped',last.skipped,last.total,'#d97706')}}`;
  }}
  const rec = document.getElementById('home-recent');
  rec.innerHTML = history.length ? history.slice(0,5).map(r => {{
    const d = new Date(r.date).toLocaleDateString();
    const color = r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';
    return `<div class="history-item"><span class="h-score" style="color:${{color}}">${{r.pct}}%</span><span class="h-detail">${{r.correct}}/${{r.total}} · ${{r.subject}}</span><span class="h-date">${{d}}</span></div>`;
  }}).join('') : '<div style="color:var(--text-muted);font-size:0.88rem">No sessions yet.</div>';
}}

function fmtTime(s) {{ if(!s) return '—'; const m=Math.floor(s/60); return m>0?`${{m}}m ${{s%60}}s`:`${{s}}s`; }}

// INIT
loadHistory();
populateFilters();
renderHomePage();
</script>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 quiz_generator.py <input_file.txt|json> [output_file.html]")
        print()
        print("Example:")
        print("  python3 quiz_generator.py questions.txt")
        print("  python3 quiz_generator.py questions.json my_quiz.html")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    output_path = sys.argv[2] if len(sys.argv) >= 3 else str(Path(input_path).parent / (Path(input_path).stem + "_quiz.html"))

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
    subjects = sorted(set(q.get("subject","") for q in questions if q.get("subject")))
    print(f"Subjects: {', '.join(subjects) or 'N/A'}")

    title = Path(input_path).stem.replace("_", " ").title()
    print(f"Generating bilingual HTML quiz: {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(generate_html(questions, title))

    size_kb = os.path.getsize(output_path) // 1024
    print(f"\nDone! Quiz saved to: {output_path} ({size_kb} KB)")
    print(f"\nBilingual features:")
    print(f"  - Every question shows English + Hindi simultaneously")
    print(f"  - Every option shows both languages")
    print(f"  - Explanations shown in both English and Hindi")
    print(f"  - Subject/topic filtering, timed quiz, results, review, stats")
    print(f"\nOpen {output_path} in any browser to start!")


if __name__ == "__main__":
    main()
