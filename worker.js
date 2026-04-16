/**
 * Cloudflare Workers — Quiz Generator + Merge + Telegram Bot
 * ──────────────────────────────────────────────────────────
 * Web:           GET  /          → upload UI (unlimited file merge)
 *                POST /generate  → returns HTML quiz
 * Telegram bot:  POST /telegram  → webhook receiver
 *                /merge          → start multi-file collect flow
 *                /done           → finalise merge and generate quiz
 *                /cancel         → abort current merge
 * Setup:         GET  /setup     → registers Telegram webhook (run once)
 *
 * Environment variables (Cloudflare dashboard → Worker → Settings → Variables):
 *   TELEGRAM_TOKEN   — bot token from @BotFather
 *
 * KV namespace (for Telegram merge state — create once, bind as QUIZ_STORE):
 *   npx wrangler kv:namespace create QUIZ_STORE
 *   Then add the printed ID to wrangler.toml (see bottom of that file)
 */

// ════════════════════════════════════════════════════════════
//  MERGE HELPER  (accepts any number of lists)
// ════════════════════════════════════════════════════════════
function mergeQuestions(...lists) {
  const seen = new Set();
  const merged = [];
  for (const list of lists) {
    for (const q of list) {
      const key = (q.qEnglish || q.qHindi || JSON.stringify(q)).trim().toLowerCase();
      if (!seen.has(key)) { seen.add(key); merged.push(q); }
    }
  }
  return merged;
}

// ════════════════════════════════════════════════════════════
//  QUIZ HTML GENERATOR
// ════════════════════════════════════════════════════════════
function generateHtml(questions, title) {
  const titleSafe = escHtml(title);
  const qJson = JSON.stringify(questions);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title id="page-title">${titleSafe}</title>
<style>
:root{--primary:#4f46e5;--primary-light:#818cf8;--primary-dark:#3730a3;--success:#16a34a;--danger:#dc2626;--warning:#d97706;--bg:#f8fafc;--surface:#fff;--border:#e2e8f0;--text:#1e293b;--muted:#64748b;--hindi-bg:#fdf4ff;--hindi-border:#e9d5ff;--hindi-text:#7c3aed;--r:12px;--sh:0 4px 24px rgba(0,0,0,.08);--sh-sm:0 1px 6px rgba(0,0,0,.06)}
body.dark{--bg:#0f172a;--surface:#1e293b;--border:#334155;--text:#f1f5f9;--muted:#94a3b8;--hindi-bg:#1e1b33;--hindi-border:#4c1d95;--hindi-text:#a78bfa;--sh:0 4px 24px rgba(0,0,0,.4);--sh-sm:0 1px 6px rgba(0,0,0,.3)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .2s,color .2s}
nav{background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 16px;height:54px;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(79,70,229,.35);gap:8px}
.logo{font-weight:800;font-size:.95rem;display:flex;align-items:center;gap:6px;flex-shrink:0}
.quiz-title-edit{outline:none;border-bottom:1px dashed rgba(255,255,255,.4);min-width:60px;max-width:200px;white-space:nowrap;overflow:hidden;cursor:text;transition:border .15s}
.quiz-title-edit:focus{border-bottom:1px solid #fff;background:rgba(255,255,255,.1);border-radius:4px;padding:1px 4px}
.nav-tabs{display:flex;gap:2px;flex-shrink:0}
.nav-tab{background:transparent;border:none;color:rgba(255,255,255,.75);cursor:pointer;padding:5px 10px;border-radius:7px;font-size:.8rem;font-weight:500;transition:.15s;white-space:nowrap}
.nav-tab:hover{background:rgba(255,255,255,.15);color:#fff}
.nav-tab.active{background:rgba(255,255,255,.22);color:#fff;font-weight:700}
.nav-right{display:flex;align-items:center;gap:6px;flex-shrink:0}
.icon-btn{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);color:#fff;width:32px;height:32px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1rem;transition:.15s}
.icon-btn:hover{background:rgba(255,255,255,.28)}
.bilingual-badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);color:#fff;padding:3px 9px;border-radius:99px;font-size:.72rem;font-weight:700;white-space:nowrap}
.page{display:none;padding:18px;max-width:860px;margin:0 auto}
.page.active{display:block}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--sh-sm);padding:20px;margin-bottom:16px}
.home-hero{text-align:center;padding:28px 12px 20px}
.home-hero h1{font-size:1.7rem;color:var(--primary);margin-bottom:5px}
.home-hero p{color:var(--muted);font-size:.9rem}
.bilingual-pill{display:inline-block;background:linear-gradient(90deg,#4f46e5 50%,#7c3aed 50%);color:#fff;border-radius:99px;padding:2px 14px;font-size:.75rem;font-weight:700;margin-top:7px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:18px 0}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;text-align:center;box-shadow:var(--sh-sm)}
.stat-card .value{font-size:1.8rem;font-weight:800;color:var(--primary)}
.stat-card .label{font-size:.76rem;color:var(--muted);margin-top:3px}
.filter-row{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-bottom:16px}
.filter-row label{font-size:.86rem;font-weight:600;color:var(--muted)}
select,input[type=number]{border:1px solid var(--border);border-radius:7px;padding:6px 10px;font-size:.86rem;background:var(--surface);color:var(--text);outline:none;transition:.15s}
select:focus,input:focus{border-color:var(--primary)}
body.dark select,body.dark input[type=number]{background:var(--surface);color:var(--text)}
.btn{display:inline-flex;align-items:center;gap:5px;border:none;border-radius:7px;padding:8px 16px;font-size:.86rem;font-weight:600;cursor:pointer;transition:.15s}
.btn-primary{background:var(--primary);color:#fff}
.btn-primary:hover{background:var(--primary-dark);transform:translateY(-1px)}
.btn-outline{background:transparent;border:2px solid var(--primary);color:var(--primary)}
.btn-outline:hover{background:var(--primary);color:#fff}
.btn-sm{padding:5px 11px;font-size:.79rem}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none!important}
.marking-info{display:inline-flex;gap:10px;padding:5px 12px;border-radius:99px;background:var(--bg);border:1px solid var(--border);font-size:.78rem;color:var(--muted);margin-bottom:14px}
.marking-info .pos{color:var(--success);font-weight:700}
.marking-info .neg{color:var(--danger);font-weight:700}
#quiz-progress-bar-wrap{background:var(--border);border-radius:99px;height:6px;margin-bottom:16px;overflow:hidden}
#quiz-progress-bar{background:linear-gradient(90deg,var(--primary),#7c3aed);height:100%;border-radius:99px;transition:width .3s;width:0%}
.quiz-meta{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;font-size:.81rem;color:var(--muted)}
#quiz-timer{background:var(--primary);color:#fff;border-radius:20px;padding:3px 12px;font-weight:700;font-size:.9rem}
#quiz-timer.warning{background:var(--warning)}
#quiz-timer.danger{background:var(--danger)}
.question-tag{display:inline-block;font-size:.71rem;background:#ede9fe;color:var(--primary);padding:2px 10px;border-radius:99px;margin-bottom:9px;font-weight:600}
body.dark .question-tag{background:#2e1065;color:#a78bfa}
.question-block{margin-bottom:16px}
.q-english{font-size:1.03rem;font-weight:700;line-height:1.55;color:var(--text);margin-bottom:7px;white-space:pre-line}
.q-hindi{font-size:.95rem;font-weight:500;line-height:1.6;color:var(--hindi-text);background:var(--hindi-bg);border-left:3px solid var(--hindi-border);padding:7px 12px;border-radius:0 8px 8px 0;white-space:pre-line}
.lang-divider{display:flex;align-items:center;gap:7px;margin:6px 0;font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.lang-divider::before,.lang-divider::after{content:'';flex:1;height:1px;background:var(--border)}
.options-list{list-style:none;display:flex;flex-direction:column;gap:8px}
.option-item{border:2px solid var(--border);border-radius:9px;padding:10px 13px;cursor:pointer;transition:.15s;display:flex;align-items:flex-start;gap:10px}
.option-item:hover:not(.disabled){border-color:var(--primary-light);background:#ede9fe18}
.option-item.selected{border-color:var(--primary);background:#ede9fe33}
.option-item.correct{border-color:var(--success);background:#dcfce7}
.option-item.wrong{border-color:var(--danger);background:#fee2e2}
.option-item.disabled{cursor:default}
body.dark .option-item.correct{background:#14532d33}
body.dark .option-item.wrong{background:#7f1d1d33}
.option-letter{width:29px;height:29px;border-radius:50%;background:var(--bg);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem;flex-shrink:0;margin-top:2px}
.option-item.correct .option-letter{background:var(--success);border-color:var(--success);color:#fff}
.option-item.wrong .option-letter{background:var(--danger);border-color:var(--danger);color:#fff}
.option-item.selected .option-letter{background:var(--primary);border-color:var(--primary);color:#fff}
.option-texts{display:flex;flex-direction:column;gap:2px}
.opt-english{font-size:.91rem;font-weight:600;color:var(--text);white-space:pre-line}
.opt-hindi{font-size:.81rem;color:var(--hindi-text);white-space:pre-line}
.explanation-box{margin-top:14px;border-radius:9px;overflow:hidden;display:none;border:1px solid var(--border)}
.explanation-box.show{display:block}
.exp-english{padding:11px 15px;background:#f0fdf4;border-left:4px solid var(--success);font-size:.86rem;line-height:1.6;color:#14532d}
.exp-hindi{padding:11px 15px;background:var(--hindi-bg);border-left:4px solid var(--hindi-border);font-size:.86rem;line-height:1.6;color:var(--hindi-text);border-top:1px solid var(--border)}
body.dark .exp-english{background:#052e16;color:#86efac}
.quiz-nav{display:flex;justify-content:space-between;align-items:center;margin-top:18px;gap:8px}
.question-nav-grid{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px}
.q-dot{width:30px;height:30px;border-radius:6px;border:2px solid var(--border);background:var(--surface);cursor:pointer;font-size:.76rem;font-weight:600;color:var(--muted);display:flex;align-items:center;justify-content:center;transition:.12s}
.q-dot:hover{border-color:var(--primary);color:var(--primary)}
.q-dot.current{border-color:var(--primary);background:var(--primary);color:#fff}
.q-dot.answered{border-color:var(--success);background:#dcfce7;color:var(--success)}
.q-dot.wrong-answered{border-color:var(--danger);background:#fee2e2;color:var(--danger)}
.q-dot.skipped{border-color:var(--warning);background:#fef9c3;color:var(--warning)}
body.dark .q-dot.answered{background:#14532d44}
body.dark .q-dot.wrong-answered{background:#7f1d1d44}
.result-hero{text-align:center;padding:24px 0}
.result-score-ring{width:128px;height:128px;border-radius:50%;border:10px solid var(--border);display:inline-flex;align-items:center;justify-content:center;flex-direction:column;margin-bottom:12px}
.score-pct{font-size:1.9rem;font-weight:900;color:var(--primary)}
.score-label{font-size:.7rem;color:var(--muted);font-weight:600}
.marks-display{margin-top:8px;font-size:1rem;font-weight:700;color:var(--text)}
.marks-display span{color:var(--primary)}
.result-bars{margin-top:12px}
.result-bar-row{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:.84rem}
.result-bar-label{width:75px;color:var(--muted)}
.result-bar-track{flex:1;background:var(--border);border-radius:99px;height:7px;overflow:hidden}
.result-bar-fill{height:100%;border-radius:99px}
.result-bar-count{width:34px;text-align:right;font-weight:700}
.review-q{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:12px}
.review-q .q-number{font-size:.76rem;color:var(--muted);margin-bottom:5px}
.review-q .q-english{font-weight:700;margin-bottom:4px;line-height:1.5;font-size:.98rem;white-space:pre-line}
.review-q .q-hindi{font-size:.88rem;color:var(--hindi-text);margin-bottom:10px;white-space:pre-line}
.review-option{padding:7px 12px;border-radius:7px;border:2px solid var(--border);margin-bottom:5px;display:flex;align-items:flex-start;gap:8px;font-size:.86rem}
.review-option.correct-opt{border-color:var(--success);background:#dcfce7}
.review-option.user-wrong{border-color:var(--danger);background:#fee2e2}
body.dark .review-option.correct-opt{background:#052e16}
body.dark .review-option.user-wrong{background:#450a0a}
.review-exp-en{padding:8px 12px;background:#f0fdf4;border-left:4px solid var(--success);font-size:.83rem;line-height:1.55}
.review-exp-hi{padding:8px 12px;background:var(--hindi-bg);border-left:4px solid var(--hindi-border);font-size:.83rem;line-height:1.55;color:var(--hindi-text);border-top:1px solid var(--border)}
body.dark .review-exp-en{background:#052e16;color:#86efac}
.review-exp-wrap{margin-top:9px;border:1px solid var(--border);border-radius:7px;overflow:hidden}
.badge{display:inline-block;padding:2px 7px;border-radius:99px;font-size:.7rem;font-weight:700}
.badge-correct{background:#dcfce7;color:var(--success)}
.badge-wrong{background:#fee2e2;color:var(--danger)}
.badge-skipped{background:#fef9c3;color:var(--warning)}
.history-item{display:flex;align-items:center;gap:9px;padding:9px 13px;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:7px;font-size:.86rem}
.h-score{font-weight:800;font-size:1rem;color:var(--primary)}
.h-detail{color:var(--muted);font-size:.78rem;flex:1}
.h-date{color:var(--muted);font-size:.75rem}
.sub-row{display:grid;grid-template-columns:1fr 65px 65px;gap:7px;padding:6px 0;border-bottom:1px solid var(--border);font-size:.84rem;align-items:center}
.sub-row:last-child{border-bottom:none}
.sub-name{font-weight:600}
.sub-pct{text-align:center;font-weight:700;color:var(--primary)}
.sub-total{text-align:center;color:var(--muted)}
.section-title{font-size:1rem;font-weight:700;margin-bottom:13px;color:var(--text);display:flex;align-items:center;gap:6px}
.divider{border:none;border-top:1px solid var(--border);margin:16px 0}
.empty-state{text-align:center;padding:32px 16px;color:var(--muted)}
.empty-state .icon{font-size:2.6rem;margin-bottom:9px}
@media(max-width:600px){nav{padding:0 9px;gap:5px}.logo{font-size:.82rem}.nav-tab{padding:4px 7px;font-size:.73rem}.page{padding:10px}.quiz-title-edit{max-width:110px}}
</style>
</head>
<body>
<nav>
  <div class="logo"><span>🎓</span><span class="quiz-title-edit" id="quiz-title" contenteditable="true" title="Click to rename">${titleSafe}</span></div>
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
<div id="home" class="page active">
  <div class="home-hero"><h1 id="hero-title">${titleSafe}</h1><p>Bilingual quiz · English &amp; Hindi together</p><div class="bilingual-pill">ENGLISH + हिंदी</div></div>
  <div class="stats-grid" id="home-stats"></div>
  <div class="card"><div class="section-title">📈 Last Performance</div><div id="home-overview"></div></div>
  <div class="card"><div class="section-title">🕐 Recent Sessions</div><div id="home-recent"></div></div>
</div>
<div id="quiz-setup" class="page">
  <div class="card">
    <div class="section-title">⚙️ Quiz Settings</div>
    <div class="filter-row"><label>Subject</label><select id="filter-subject"><option value="">All Subjects</option></select></div>
    <div class="filter-row"><label>Topic</label><select id="filter-topic"><option value="">All Topics</option></select></div>
    <div class="filter-row"><label>Questions</label><input type="number" id="q-count" min="5" max="200" value="20" style="width:72px"/><span style="font-size:.81rem;color:var(--muted)" id="q-available"></span></div>
    <div class="filter-row"><label>Timer</label><select id="quiz-mode"><option value="timed">60s per question</option><option value="custom">Custom timer</option><option value="free">No timer</option></select><input type="number" id="custom-time" min="10" max="600" value="60" style="width:72px;display:none"/><span id="custom-time-unit" style="font-size:.8rem;color:var(--muted);display:none">sec</span></div>
    <div class="filter-row"><label>Order</label><select id="quiz-order"><option value="random">Random</option><option value="sequential">Sequential</option></select></div>
    <hr class="divider"/>
    <div class="section-title" style="margin-bottom:10px">🏅 Marking Scheme</div>
    <div class="filter-row"><label>✅ Correct</label><input type="number" id="mark-correct" min="0.25" max="10" step="0.25" value="1" style="width:72px"/><label style="margin-left:8px">marks</label></div>
    <div class="filter-row"><label>❌ Wrong</label><input type="number" id="mark-neg" min="0" max="10" step="0.25" value="0" style="width:72px"/><label style="margin-left:8px">marks deducted</label></div>
    <div id="marking-preview" style="font-size:.82rem;color:var(--muted);margin-bottom:14px"></div>
    <hr class="divider"/>
    <button class="btn btn-primary" onclick="startQuiz()">▶ Start Quiz</button>
    <span id="setup-msg" style="margin-left:9px;font-size:.81rem;color:var(--danger)"></span>
  </div>
</div>
<div id="quiz-page" class="page">
  <div id="quiz-progress-bar-wrap"><div id="quiz-progress-bar"></div></div>
  <div class="quiz-meta"><span id="quiz-meta-left"></span><span id="quiz-timer">60</span><button class="btn btn-sm btn-outline" onclick="endQuizEarly()">Finish Early</button></div>
  <div class="card">
    <div id="quiz-marking-badge" class="marking-info"></div>
    <div class="question-tag" id="q-tag"></div>
    <div class="question-block">
      <div class="q-english" id="q-english"></div>
      <div class="lang-divider" id="hindi-divider">हिंदी</div>
      <div class="q-hindi" id="q-hindi"></div>
    </div>
    <ul class="options-list" id="options-list"></ul>
    <div class="explanation-box" id="explanation-box"><div class="exp-english" id="exp-english"></div><div class="exp-hindi" id="exp-hindi"></div></div>
    <div class="quiz-nav">
      <button class="btn btn-outline btn-sm" id="prev-btn" onclick="goQuestion(-1)">← Prev</button>
      <button class="btn btn-sm" id="skip-btn" onclick="skipQuestion()" style="background:#fef9c3;color:#92400e;border:2px solid #fbbf24;">Skip</button>
      <button class="btn btn-primary btn-sm" id="next-btn" onclick="goQuestion(1)">Next →</button>
    </div>
  </div>
  <div class="card"><div style="font-size:.78rem;color:var(--muted);margin-bottom:6px">Question Navigator</div><div class="question-nav-grid" id="q-nav-grid"></div></div>
</div>
<div id="results-page" class="page">
  <div class="card result-hero">
    <div class="result-score-ring" id="score-ring"><span class="score-pct" id="result-pct">0%</span><span class="score-label">Accuracy</span></div>
    <h2 id="result-heading"></h2><div class="marks-display" id="marks-display"></div>
    <p id="result-summary" style="color:var(--muted);margin-top:5px;font-size:.88rem;"></p>
  </div>
  <div class="card"><div class="section-title">📊 Breakdown</div><div class="result-bars" id="result-bars"></div></div>
  <div class="card"><div class="section-title">📚 Subject Performance</div><div id="result-subject-breakdown"></div></div>
  <div style="display:flex;gap:9px;flex-wrap:wrap;margin-bottom:18px">
    <button class="btn btn-primary" onclick="showPage('review-page')">🔍 Review Answers</button>
    <button class="btn btn-outline" onclick="showPage('quiz-setup')">🔄 New Quiz</button>
    <button class="btn btn-outline" onclick="showPage('home')">🏠 Home</button>
  </div>
</div>
<div id="review-page" class="page">
  <div class="card"><div class="section-title">🔍 Review (EN + हिं)</div>
    <div class="filter-row"><label>Subject</label><select id="review-subject" onchange="renderReview()"><option value="">All</option></select><label>Show</label><select id="review-filter" onchange="renderReview()"><option value="all">All</option><option value="wrong">Wrong</option><option value="correct">Correct</option><option value="skipped">Skipped</option></select></div>
  </div>
  <div id="review-list"></div>
</div>
<div id="stats-page" class="page">
  <div class="stats-grid" id="stats-grid"></div>
  <div class="card"><div class="section-title">📊 Subject-wise Accuracy</div><div id="stats-subject"></div></div>
  <div class="card"><div class="section-title">🕐 Session History</div><div id="stats-history"></div><button class="btn btn-sm btn-outline" style="margin-top:9px;border-color:var(--danger);color:var(--danger)" onclick="clearHistory()">🗑 Clear History</button></div>
</div>
<script>
const ALL_QUESTIONS=${qJson};
let currentSession=null,history=[];
function applyDark(on){document.body.classList.toggle('dark',on);document.getElementById('dark-btn').textContent=on?'☀️':'🌙';localStorage.setItem('quiz_theme',on?'dark':'light');}
function toggleDark(){applyDark(!document.body.classList.contains('dark'));}
function initDark(){const s=localStorage.getItem('quiz_theme');if(s==='dark')applyDark(true);else if(!s&&window.matchMedia('(prefers-color-scheme:dark)').matches)applyDark(true);}
const titleEl=document.getElementById('quiz-title'),heroEl=document.getElementById('hero-title');
titleEl.addEventListener('input',()=>{heroEl.textContent=titleEl.textContent.trim()||'${titleSafe}';document.title=titleEl.textContent.trim()||'${titleSafe}';});
titleEl.addEventListener('blur',()=>{if(!titleEl.textContent.trim())titleEl.textContent='${titleSafe}';heroEl.textContent=titleEl.textContent.trim();document.title=titleEl.textContent.trim();});
titleEl.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();titleEl.blur();}});
function saveHistory(){localStorage.setItem('quiz_history_v3',JSON.stringify(history));}
function loadHistory(){try{history=JSON.parse(localStorage.getItem('quiz_history_v3')||'[]');}catch(e){history=[];}}
function clearHistory(){if(!confirm('Clear all history?'))return;history=[];saveHistory();renderStatsPage();renderHomePage();}
function showPage(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');const m={home:0,'quiz-setup':1,'quiz-page':1,'results-page':1,'review-page':2,'stats-page':3};document.querySelectorAll('.nav-tab').forEach((t,i)=>t.classList.toggle('active',i===m[id]));if(id==='home')renderHomePage();if(id==='review-page')renderReview();if(id==='stats-page')renderStatsPage();if(id==='results-page')renderResults();}
function getSubjects(){return[...new Set(ALL_QUESTIONS.map(q=>q.subject).filter(Boolean))].sort();}
function getTopics(sub){return[...new Set(ALL_QUESTIONS.filter(q=>!sub||q.subject===sub).map(q=>q.topic).filter(Boolean))].sort();}
function populateFilters(){const subSel=document.getElementById('filter-subject'),revSub=document.getElementById('review-subject');getSubjects().forEach(s=>{[subSel,revSub].forEach(el=>{const o=document.createElement('option');o.value=s;o.textContent=s;el.appendChild(o);});});subSel.addEventListener('change',()=>{const topSel=document.getElementById('filter-topic');topSel.innerHTML='<option value="">All Topics</option>';getTopics(subSel.value).forEach(t=>{const o=document.createElement('option');o.value=t;o.textContent=t;topSel.appendChild(o);});updateAvailable();});document.getElementById('q-count').addEventListener('input',updateAvailable);document.getElementById('mark-correct').addEventListener('input',updateMarkingPreview);document.getElementById('mark-neg').addEventListener('input',updateMarkingPreview);updateAvailable();updateMarkingPreview();}
function updateAvailable(){const sub=document.getElementById('filter-subject').value,top=document.getElementById('filter-topic').value;const pool=ALL_QUESTIONS.filter(q=>(!sub||q.subject===sub)&&(!top||q.topic===top));document.getElementById('q-available').textContent='('+pool.length+' available)';document.getElementById('q-count').max=pool.length;}
function updateMarkingPreview(){const mc=parseFloat(document.getElementById('mark-correct').value)||1,mn=parseFloat(document.getElementById('mark-neg').value)||0;document.getElementById('marking-preview').textContent='Correct = +'+mc+'  ·  Wrong = -'+mn+'  ·  Skip = 0';}
document.getElementById('quiz-mode').addEventListener('change',function(){const show=this.value==='custom';document.getElementById('custom-time').style.display=show?'':'none';document.getElementById('custom-time-unit').style.display=show?'':'none';});
function startQuiz(){const sub=document.getElementById('filter-subject').value,top=document.getElementById('filter-topic').value,cnt=parseInt(document.getElementById('q-count').value)||20,mode=document.getElementById('quiz-mode').value,ord=document.getElementById('quiz-order').value,cust=parseInt(document.getElementById('custom-time').value)||60,mc=parseFloat(document.getElementById('mark-correct').value)||1,mn=parseFloat(document.getElementById('mark-neg').value)||0;let pool=ALL_QUESTIONS.filter(q=>(!sub||q.subject===sub)&&(!top||q.topic===top));if(!pool.length){document.getElementById('setup-msg').textContent='No questions match.';return;}if(cnt>pool.length){document.getElementById('setup-msg').textContent='Only '+pool.length+' available.';return;}document.getElementById('setup-msg').textContent='';let qs=[...pool];if(ord==='random')qs=qs.sort(()=>Math.random()-.5);qs=qs.slice(0,cnt);const secPerQ=mode==='timed'?60:mode==='custom'?cust:null;currentSession={questions:qs,answers:new Array(qs.length).fill(null),revealed:new Array(qs.length).fill(false),currentIdx:0,startTime:Date.now(),secPerQ,timeLeft:secPerQ,timerInterval:null,subject:sub||'All',topic:top||'All',markCorrect:mc,markNeg:mn};buildQuizNav();showPage('quiz-page');renderQuestion();if(secPerQ!==null)startTimer();}
function buildQuizNav(){const grid=document.getElementById('q-nav-grid');grid.innerHTML='';currentSession.questions.forEach((_,i)=>{const d=document.createElement('div');d.className='q-dot';d.textContent=i+1;d.onclick=()=>jumpTo(i);grid.appendChild(d);});}
function updateNavDots(){document.querySelectorAll('.q-dot').forEach((d,i)=>{const s=currentSession;d.className='q-dot';if(i===s.currentIdx)d.classList.add('current');else if(s.answers[i]===-1)d.classList.add('skipped');else if(s.answers[i]!==null)d.classList.add(s.answers[i]===s.questions[i].correct?'answered':'wrong-answered');});}
function renderQuestion(){const s=currentSession,q=s.questions[s.currentIdx],total=s.questions.length;document.getElementById('quiz-progress-bar').style.width=((s.currentIdx+1)/total*100)+'%';document.getElementById('quiz-meta-left').textContent='Q '+(s.currentIdx+1)+' / '+total+'  ·  Done: '+s.answers.filter(a=>a!==null).length;document.getElementById('quiz-marking-badge').innerHTML='<span class="pos">+'+s.markCorrect+' correct</span>'+(s.markNeg>0?'<span class="neg">-'+s.markNeg+' wrong</span>':'<span>No negative</span>');document.getElementById('q-tag').textContent=[q.subject,q.topic].filter(Boolean).join(' › ');document.getElementById('q-english').innerHTML=q.qEnglish||'';document.getElementById('q-hindi').innerHTML=q.qHindi||'';const hasHindi=!!q.qHindi;document.getElementById('hindi-divider').style.display=hasHindi?'':'none';document.getElementById('q-hindi').style.display=hasHindi?'':'none';const optsEn=q.optionsEnglish||[],optsHi=q.optionsHindi||[];const ul=document.getElementById('options-list');ul.innerHTML='';const chosen=s.answers[s.currentIdx],revealed=s.revealed[s.currentIdx];optsEn.forEach((opt,i)=>{const li=document.createElement('li');li.className='option-item';if(revealed){li.classList.add('disabled');if(i===q.correct)li.classList.add('correct');else if(i===chosen&&chosen!==q.correct)li.classList.add('wrong');}else if(i===chosen)li.classList.add('selected');const hiOpt=optsHi[i]||'';li.innerHTML='<span class="option-letter">'+String.fromCharCode(65+i)+'</span><span class="option-texts"><span class="opt-english">'+opt+'</span>'+(hiOpt?'<span class="opt-hindi">'+hiOpt+'</span>':'')+'</span>';if(!revealed)li.onclick=()=>selectOption(i);ul.appendChild(li);});const expBox=document.getElementById('explanation-box');if(revealed){document.getElementById('exp-english').textContent=q.explanationEnglish||'';const expHi=document.getElementById('exp-hindi');expHi.textContent=q.explanationHindi||'';expHi.style.display=q.explanationHindi?'':'none';expBox.classList.add('show');}else expBox.classList.remove('show');document.getElementById('prev-btn').disabled=s.currentIdx===0;const isLast=s.currentIdx===total-1;const nb=document.getElementById('next-btn');nb.textContent=isLast?'✓ Finish':'Next →';nb.onclick=isLast?finishQuiz:()=>goQuestion(1);document.getElementById('skip-btn').style.display=revealed?'none':'';if(s.secPerQ!==null){s.timeLeft=s.secPerQ;updateTimerDisplay();}updateNavDots();}
function selectOption(i){const s=currentSession;if(s.revealed[s.currentIdx])return;s.answers[s.currentIdx]=i;s.revealed[s.currentIdx]=true;renderQuestion();if(s.currentIdx<s.questions.length-1)setTimeout(()=>goQuestion(1),1400);}
function goQuestion(dir){const s=currentSession,next=s.currentIdx+dir;if(next<0||next>=s.questions.length)return;s.currentIdx=next;if(s.secPerQ!==null){clearInterval(s.timerInterval);s.timeLeft=s.secPerQ;startTimer();}renderQuestion();}
function jumpTo(i){const s=currentSession;s.currentIdx=i;if(s.secPerQ!==null){clearInterval(s.timerInterval);s.timeLeft=s.secPerQ;startTimer();}renderQuestion();}
function skipQuestion(){const s=currentSession;if(s.answers[s.currentIdx]===null)s.answers[s.currentIdx]=-1;goQuestion(1);}
function endQuizEarly(){if(confirm('End quiz now?'))finishQuiz();}
function startTimer(){const s=currentSession;if(s.secPerQ===null)return;clearInterval(s.timerInterval);s.timerInterval=setInterval(()=>{s.timeLeft--;updateTimerDisplay();if(s.timeLeft<=0){clearInterval(s.timerInterval);if(s.answers[s.currentIdx]===null)s.answers[s.currentIdx]=-1;s.revealed[s.currentIdx]=true;renderQuestion();if(s.currentIdx<s.questions.length-1)setTimeout(()=>{goQuestion(1);startTimer();},1100);else setTimeout(finishQuiz,1100);}},1000);}
function updateTimerDisplay(){const s=currentSession,el=document.getElementById('quiz-timer');if(s.secPerQ===null){el.style.display='none';return;}el.style.display='';const t=s.timeLeft;el.textContent=Math.floor(t/60)+':'+String(t%60).padStart(2,'0');el.className=t>s.secPerQ*.5?'':t>10?'warning':'danger';}
function finishQuiz(){const s=currentSession;clearInterval(s.timerInterval);let correct=0,wrong=0,skipped=0,totalScore=0;const subjectStats={};const maxScore=s.questions.length*s.markCorrect;s.questions.forEach((q,i)=>{const a=s.answers[i],sub=q.subject||'Other';if(!subjectStats[sub])subjectStats[sub]={correct:0,total:0};subjectStats[sub].total++;if(a===-1||a===null)skipped++;else if(a===q.correct){correct++;subjectStats[sub].correct++;totalScore+=s.markCorrect;}else{wrong++;totalScore-=s.markNeg;}});totalScore=Math.round(Math.max(0,totalScore)*100)/100;const pct=Math.round(correct/s.questions.length*100),elapsed=Math.round((Date.now()-s.startTime)/1000);const result={date:new Date().toISOString(),total:s.questions.length,correct,wrong,skipped,pct,totalScore,maxScore,markCorrect:s.markCorrect,markNeg:s.markNeg,elapsed,subject:s.subject,topic:s.topic,subjectStats,answers:[...s.answers],questions:s.questions.map(q=>({qEnglish:q.qEnglish,qHindi:q.qHindi,optionsEnglish:q.optionsEnglish,optionsHindi:q.optionsHindi,correct:q.correct,explanationEnglish:q.explanationEnglish,explanationHindi:q.explanationHindi,subject:q.subject,topic:q.topic}))};history.unshift(result);if(history.length>50)history=history.slice(0,50);saveHistory();currentSession._lastResult=result;showPage('results-page');}
function renderResults(){if(!currentSession?._lastResult)return;const r=currentSession._lastResult;document.getElementById('result-pct').textContent=r.pct+'%';const color=r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';document.getElementById('score-ring').style.borderColor=color;document.getElementById('result-pct').style.color=color;document.getElementById('result-heading').textContent=r.pct>=80?'🎉 Excellent!':r.pct>=60?'👍 Good Job!':'💪 Keep Practicing!';document.getElementById('marks-display').innerHTML='Score: <span>'+r.totalScore+' / '+r.maxScore+'</span> marks &nbsp;·&nbsp; +'+r.markCorrect+' correct'+(r.markNeg>0?', -'+r.markNeg+' wrong':'');document.getElementById('result-summary').textContent=r.correct+' correct · '+r.wrong+' wrong · '+r.skipped+' skipped · '+fmtTime(r.elapsed);document.getElementById('result-bars').innerHTML=barRow('Correct',r.correct,r.total,'#16a34a')+barRow('Wrong',r.wrong,r.total,'#dc2626')+barRow('Skipped',r.skipped,r.total,'#d97706');const sb=document.getElementById('result-subject-breakdown');sb.innerHTML='<div class="sub-row" style="font-weight:700;font-size:.76rem;color:var(--muted)"><span>Subject</span><span style="text-align:center">Acc.</span><span style="text-align:center">Qs</span></div>';Object.entries(r.subjectStats).forEach(([sub,st])=>{const p=Math.round(st.correct/st.total*100);sb.innerHTML+='<div class="sub-row"><span class="sub-name">'+sub+'</span><span class="sub-pct">'+p+'%</span><span class="sub-total">'+st.total+'</span></div>';});}
function barRow(label,val,total,color){const pct=total?Math.round(val/total*100):0;return '<div class="result-bar-row"><span class="result-bar-label">'+label+'</span><div class="result-bar-track"><div class="result-bar-fill" style="width:'+pct+'%;background:'+color+'"></div></div><span class="result-bar-count">'+val+'</span></div>';}
function renderReview(){const filterSub=document.getElementById('review-subject').value,filterType=document.getElementById('review-filter').value;let items=[];if(currentSession?._lastResult){const r=currentSession._lastResult;r.questions.forEach((q,i)=>{const a=r.answers[i];const status=(a===-1||a===null)?'skipped':a===q.correct?'correct':'wrong';items.push({q,a,status});});}else{ALL_QUESTIONS.forEach(q=>items.push({q,a:null,status:'unanswered'}));}if(filterSub)items=items.filter(it=>it.q.subject===filterSub);if(filterType==='wrong')items=items.filter(it=>it.status==='wrong');else if(filterType==='correct')items=items.filter(it=>it.status==='correct');else if(filterType==='skipped')items=items.filter(it=>it.status==='skipped');const list=document.getElementById('review-list');list.innerHTML=items.length?items.map((it,n)=>reviewCard(it,n+1)).join(''):'<div class="empty-state"><div class="icon">🔍</div><p>No questions.</p></div>';}
function reviewCard({q,a,status},n){const optsEn=q.optionsEnglish||[],optsHi=q.optionsHindi||[];const optRows=optsEn.map((opt,i)=>{let cls='';if(i===q.correct)cls='correct-opt';else if(a!==null&&a!==-1&&i===a&&a!==q.correct)cls='user-wrong';const icon=i===q.correct?'✓':(a!==null&&a!==-1&&i===a)?'✗':'○';return '<div class="review-option '+cls+'"><span style="font-weight:700;flex-shrink:0;width:22px">'+icon+String.fromCharCode(65+i)+'</span><span class="option-texts"><span class="opt-english">'+opt+'</span>'+(optsHi[i]?'<span class="opt-hindi">'+optsHi[i]+'</span>':'')+'</span></div>';}).join('');const badgeCls=status==='correct'?'badge-correct':status==='wrong'?'badge-wrong':'badge-skipped';return '<div class="review-q"><div class="q-number">Q'+n+' — '+([q.subject,q.topic].filter(Boolean).join(' › '))+' <span class="badge '+badgeCls+'">'+status.charAt(0).toUpperCase()+status.slice(1)+'</span></div><div class="q-english">'+(q.qEnglish||'')+'</div>'+(q.qHindi?'<div class="q-hindi">'+q.qHindi+'</div>':'')+optRows+'<div class="review-exp-wrap">'+(q.explanationEnglish?'<div class="review-exp-en">💡 '+q.explanationEnglish+'</div>':'')+(q.explanationHindi?'<div class="review-exp-hi">💡 '+q.explanationHindi+'</div>':'')+'</div></div>';}
function renderStatsPage(){if(!history.length){document.getElementById('stats-grid').innerHTML='';document.getElementById('stats-subject').innerHTML='<div class="empty-state"><div class="icon">📊</div><p>Take a quiz first!</p></div>';document.getElementById('stats-history').innerHTML='';return;}const totalQ=history.reduce((s,r)=>s+r.total,0),avgPct=Math.round(history.reduce((s,r)=>s+r.pct,0)/history.length),best=Math.max(...history.map(r=>r.pct)),bestMk=Math.max(...history.map(r=>r.totalScore||0));document.getElementById('stats-grid').innerHTML='<div class="stat-card"><div class="value">'+history.length+'</div><div class="label">Sessions</div></div><div class="stat-card"><div class="value">'+totalQ+'</div><div class="label">Attempted</div></div><div class="stat-card"><div class="value">'+avgPct+'%</div><div class="label">Avg</div></div><div class="stat-card"><div class="value">'+best+'%</div><div class="label">Best</div></div><div class="stat-card"><div class="value">'+bestMk+'</div><div class="label">Best Marks</div></div>';const subAcc={};history.forEach(r=>Object.entries(r.subjectStats||{}).forEach(([sub,st])=>{if(!subAcc[sub])subAcc[sub]={correct:0,total:0};subAcc[sub].correct+=st.correct;subAcc[sub].total+=st.total;}));const subEl=document.getElementById('stats-subject');subEl.innerHTML='<div class="sub-row" style="font-weight:700;font-size:.76rem;color:var(--muted)"><span>Subject</span><span style="text-align:center">Acc.</span><span style="text-align:center">Qs</span></div>';Object.entries(subAcc).sort((a,b)=>b[1].total-a[1].total).forEach(([sub,st])=>{const p=Math.round(st.correct/st.total*100);subEl.innerHTML+='<div class="sub-row"><span class="sub-name">'+sub+'</span><span class="sub-pct">'+p+'%</span><span class="sub-total">'+st.total+'</span></div>';});document.getElementById('stats-history').innerHTML=history.slice(0,20).map(r=>{const d=new Date(r.date),ds=d.toLocaleDateString()+' '+d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});const color=r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';return '<div class="history-item"><span class="h-score" style="color:'+color+'">'+r.pct+'%</span><span class="h-detail">'+r.correct+'/'+r.total+(r.totalScore!==undefined?' · '+r.totalScore+'/'+r.maxScore+' marks':'')+' · '+r.subject+'</span><span class="h-date">'+ds+'</span></div>';}).join('');}
function renderHomePage(){loadHistory();const best=history.length?Math.max(...history.map(r=>r.pct)):null,avg=history.length?Math.round(history.reduce((s,r)=>s+r.pct,0)/history.length):null;document.getElementById('home-stats').innerHTML='<div class="stat-card"><div class="value">'+ALL_QUESTIONS.length+'</div><div class="label">Total Questions</div></div><div class="stat-card"><div class="value">'+getSubjects().length+'</div><div class="label">Subjects</div></div><div class="stat-card"><div class="value">'+history.length+'</div><div class="label">Sessions</div></div>'+(best!==null?'<div class="stat-card"><div class="value">'+best+'%</div><div class="label">Best</div></div>':'')+(avg!==null?'<div class="stat-card"><div class="value">'+avg+'%</div><div class="label">Avg</div></div>':'');const ov=document.getElementById('home-overview');if(!history.length){ov.innerHTML='<div class="empty-state"><div class="icon">🎯</div><p>No sessions yet. Click <strong>Quiz</strong> to start!</p></div>';}else{const last=history[0];const color=last.pct>=80?'#16a34a':last.pct>=60?'#4f46e5':'#dc2626';ov.innerHTML='<p style="font-size:.86rem;color:var(--muted);margin-bottom:10px">Last: <strong style="color:'+color+'">'+last.pct+'%</strong>'+(last.totalScore!==undefined?' · <strong>'+last.totalScore+'/'+last.maxScore+' marks</strong>':'')+' — '+last.correct+'/'+last.total+' correct</p>'+barRow('Correct',last.correct,last.total,'#16a34a')+barRow('Wrong',last.wrong,last.total,'#dc2626')+barRow('Skipped',last.skipped,last.total,'#d97706');}document.getElementById('home-recent').innerHTML=history.length?history.slice(0,5).map(r=>{const color=r.pct>=80?'#16a34a':r.pct>=60?'#4f46e5':'#dc2626';return '<div class="history-item"><span class="h-score" style="color:'+color+'">'+r.pct+'%</span><span class="h-detail">'+r.correct+'/'+r.total+(r.totalScore!==undefined?' · '+r.totalScore+' marks':'')+' · '+r.subject+'</span><span class="h-date">'+new Date(r.date).toLocaleDateString()+'</span></div>';}).join(''):'<div style="color:var(--muted);font-size:.86rem">No sessions yet.</div>';}
function fmtTime(s){if(!s)return'—';const m=Math.floor(s/60);return m>0?m+'m '+s%60+'s':s+'s';}
initDark();loadHistory();populateFilters();renderHomePage();
</script>
</body>
</html>`;
}

// ════════════════════════════════════════════════════════════
//  WEB UPLOAD PAGE  (unlimited file merge)
// ════════════════════════════════════════════════════════════
const UPLOAD_PAGE = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quiz Generator</title>
<style>
:root{--p:#4f46e5;--pd:#3730a3;--p2:#7c3aed;--bg:#f8fafc;--sf:#fff;--b:#e2e8f0;--t:#1e293b;--m:#64748b;--ok:#16a34a;--del:#dc2626}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
.card{background:var(--sf);border:1px solid var(--b);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:36px;max-width:580px;width:100%}
h1{color:var(--p);font-size:1.65rem;margin-bottom:4px}
.sub{color:var(--m);font-size:.88rem;margin-bottom:24px}
.zones{display:flex;flex-direction:column;gap:0}
.zone-wrap{margin-bottom:8px}
.zone-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:5px}
.zone-label{font-size:.78rem;font-weight:700;color:var(--m);display:flex;align-items:center;gap:6px}
.badge-num{width:20px;height:20px;border-radius:50%;background:var(--p);color:#fff;font-size:.7rem;display:inline-flex;align-items:center;justify-content:center;font-weight:800}
.remove-btn{background:none;border:none;color:var(--del);cursor:pointer;font-size:1.05rem;padding:0 4px;opacity:.65;transition:.15s}
.remove-btn:hover{opacity:1}
.drop-zone{border:2px dashed var(--b);border-radius:11px;padding:18px 16px;text-align:center;cursor:pointer;transition:.2s;background:var(--bg);min-height:74px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.drop-zone:hover,.drop-zone.over{border-color:var(--p);background:#ede9fe18}
.drop-zone.has-file{border-color:var(--ok);background:#f0fdf4}
.drop-zone input{display:none}
.drop-zone .icon{font-size:1.4rem;margin-bottom:3px}
.drop-zone p{color:var(--m);font-size:.83rem}
.drop-zone p strong{color:var(--p);cursor:pointer}
.file-name{margin-top:4px;font-size:.78rem;font-weight:600;color:var(--ok);word-break:break-all}
.merge-connector{display:flex;align-items:center;gap:10px;padding:4px 0;margin-bottom:8px}
.merge-line{flex:1;height:1px;background:var(--b)}
.merge-pill{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;border-radius:99px;padding:3px 12px;font-size:.73rem;font-weight:800}
.add-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;border:2px dashed var(--b);border-radius:10px;background:none;color:var(--p);font-size:.85rem;font-weight:700;cursor:pointer;transition:.2s;margin-top:4px}
.add-btn:hover{border-color:var(--p);background:#ede9fe20}
.summary{text-align:center;font-size:.8rem;color:var(--m);margin:10px 0 0}
.summary b{color:var(--t)}
.btn{display:block;width:100%;background:var(--p);color:#fff;border:none;border-radius:10px;padding:13px;font-size:.95rem;font-weight:700;cursor:pointer;margin-top:18px;transition:.15s}
.btn:hover{background:var(--pd);transform:translateY(-1px)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.error{background:#fee2e2;border:1px solid #fca5a5;color:#dc2626;border-radius:8px;padding:11px 14px;font-size:.87rem;margin-top:12px;display:none}
.spinner{display:none;text-align:center;margin-top:12px;color:var(--m);font-size:.87rem}
.info-box{margin-top:22px;background:var(--bg);border-radius:10px;padding:15px;font-size:.78rem;color:var(--m)}
.info-box code{display:block;margin-top:7px;white-space:pre;font-size:.71rem;overflow-x:auto;line-height:1.55;background:#f1f5f9;padding:8px;border-radius:6px}
footer{margin-top:20px;font-size:.75rem;color:var(--m);text-align:center}
</style>
</head>
<body>
<div class="card">
  <h1>🎓 Quiz Generator</h1>
  <p class="sub">Upload one or more JSON quiz files → get a fully interactive bilingual HTML quiz. Duplicates removed automatically when merging.</p>
  <form id="upload-form" enctype="multipart/form-data">
    <div class="zones" id="zones-container"></div>
    <button type="button" class="add-btn" onclick="addZone()">➕ Add Another File</button>
    <p class="summary" id="summary" style="display:none"></p>
    <div class="error" id="err"></div>
    <div class="spinner" id="spin">⚙️ Generating quiz…</div>
    <button type="submit" class="btn" id="sbtn" disabled>Generate Quiz HTML</button>
  </form>
  <div class="info-box">
    <strong>JSON format (each file):</strong>
    <code>[{"qEnglish":"…","qHindi":"…","optionsEnglish":["A","B","C","D"],
 "optionsHindi":["अ","ब","स","द"],"correct":1,
 "explanationEnglish":"…","subject":"…","topic":"…"}]</code>
    <p style="margin-top:8px;font-size:.76rem">Add multiple files to merge them — duplicate questions are removed automatically.</p>
  </div>
</div>
<footer>Self-contained output · No data stored · Works offline after download</footer>
<script>
const COLORS=['#4f46e5','#7c3aed','#0891b2','#059669','#d97706','#dc2626','#9333ea','#0284c7','#16a34a','#ca8a04'];
let zoneCount=0;
function addZone(){
  zoneCount++;const idx=zoneCount;const color=COLORS[(idx-1)%COLORS.length];
  const container=document.getElementById('zones-container');
  if(idx>1){const conn=document.createElement('div');conn.className='merge-connector';conn.id='conn'+idx;conn.innerHTML='<div class="merge-line"></div><div class="merge-pill">+ MERGE</div><div class="merge-line"></div>';container.appendChild(conn);}
  const wrap=document.createElement('div');wrap.className='zone-wrap';wrap.id='wrap'+idx;
  wrap.innerHTML='<div class="zone-header"><div class="zone-label"><span class="badge-num" style="background:'+color+'">'+idx+'</span><span>File '+idx+'</span></div>'+(idx>1?'<button type="button" class="remove-btn" onclick="removeZone('+idx+')" title="Remove">✕</button>':'')+'</div><div class="drop-zone" id="dz'+idx+'"><div class="icon">📄</div><p>Drop here or <strong onclick="document.getElementById(\'fi'+idx+'\').click()">browse</strong></p><input type="file" id="fi'+idx+'" name="file'+idx+'" accept=".json,.txt"/><div class="file-name" id="fn'+idx+'"></div></div>';
  container.appendChild(wrap);
  setupZone(idx);checkReady();
}
function removeZone(idx){const w=document.getElementById('wrap'+idx),c=document.getElementById('conn'+idx);if(w)w.remove();if(c)c.remove();checkReady();}
function setupZone(idx){
  const dz=document.getElementById('dz'+idx),fi=document.getElementById('fi'+idx),fn=document.getElementById('fn'+idx);
  fi.addEventListener('change',()=>{if(fi.files[0]){fn.textContent='✓ '+fi.files[0].name;dz.classList.add('has-file');checkReady();}});
  dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over');});
  dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
  dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('over');const f=e.dataTransfer.files[0];if(f){const dt=new DataTransfer();dt.items.add(f);fi.files=dt.files;fn.textContent='✓ '+f.name;dz.classList.add('has-file');checkReady();}});
}
function getLoadedFiles(){const files=[];for(let i=1;i<=zoneCount;i++){const fi=document.getElementById('fi'+i);if(fi&&fi.files[0])files.push({idx:i,file:fi.files[0]});}return files;}
function checkReady(){
  const loaded=getLoadedFiles();const sbtn=document.getElementById('sbtn');const summary=document.getElementById('summary');
  sbtn.disabled=loaded.length===0;
  if(loaded.length>1){summary.style.display='';summary.innerHTML='Merging <b>'+loaded.length+' files</b> → duplicates will be removed';sbtn.textContent='Merge & Generate Quiz HTML';}
  else{summary.style.display='none';sbtn.textContent='Generate Quiz HTML';}
}
document.getElementById('upload-form').addEventListener('submit',async e=>{
  e.preventDefault();const loaded=getLoadedFiles();if(!loaded.length)return;
  const err=document.getElementById('err'),spin=document.getElementById('spin'),sbtn=document.getElementById('sbtn');
  err.style.display='none';spin.style.display='block';sbtn.disabled=true;
  const fd=new FormData();loaded.forEach((f,i)=>fd.append('file'+(i+1),f.file));
  try{const r=await fetch('/generate',{method:'POST',body:fd});if(!r.ok){const j=await r.json().catch(()=>({}));throw new Error(j.error||'Generation failed');}
    const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;
    const base=loaded[0].file.name.replace(/\\.[^.]+$/,'');a.download=(loaded.length>1?base+'_merged':base)+'_quiz.html';a.click();URL.revokeObjectURL(url);
  }catch(ex){err.textContent=ex.message;err.style.display='block';}
  finally{spin.style.display='none';sbtn.disabled=getLoadedFiles().length===0;}
});
addZone();
</script>
</body>
</html>`;

// ════════════════════════════════════════════════════════════
//  UTILITIES
// ════════════════════════════════════════════════════════════
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function jsonResp(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}
function okResp() { return new Response('OK', { headers: { 'Content-Type': 'text/plain' } }); }

// ════════════════════════════════════════════════════════════
//  TELEGRAM HELPERS
// ════════════════════════════════════════════════════════════
async function tgApi(token, method, payload = {}) {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  return res.json();
}
async function tgMsg(token, chatId, text, parseMode = 'HTML') {
  return tgApi(token, 'sendMessage', { chat_id: chatId, text, parse_mode: parseMode });
}
async function tgGetFileUrl(token, fileId) {
  const res = await tgApi(token, 'getFile', { file_id: fileId });
  const path = res?.result?.file_path;
  return path ? `https://api.telegram.org/file/bot${token}/${path}` : null;
}
async function tgSendDoc(token, chatId, html, filename, caption = '') {
  const form = new FormData();
  form.append('chat_id', String(chatId));
  if (caption) { form.append('caption', caption); form.append('parse_mode', 'HTML'); }
  form.append('document', new Blob([html], { type: 'text/html' }), filename);
  const res = await fetch(`https://api.telegram.org/bot${token}/sendDocument`, { method: 'POST', body: form });
  return res.json();
}

// ════════════════════════════════════════════════════════════
//  TELEGRAM BOT — MERGE STATE via KV
//  KV keys (TTL = 30 min):
//    merge:state:{chatId}  →  "collecting"
//    merge:files:{chatId}  →  JSON array of {content, name}
// ════════════════════════════════════════════════════════════
const KV_TTL = 1800; // 30 minutes

async function kvGet(kv, key) {
  if (!kv) return null;
  try { return await kv.get(key); } catch { return null; }
}
async function kvPut(kv, key, val) {
  if (!kv) return;
  try { await kv.put(key, val, { expirationTtl: KV_TTL }); } catch {}
}
async function kvDel(kv, key) {
  if (!kv) return;
  try { await kv.delete(key); } catch {}
}
async function clearMergeState(kv, chatId) {
  await kvDel(kv, `merge:state:${chatId}`);
  await kvDel(kv, `merge:files:${chatId}`);
}
async function getMergeFiles(kv, chatId) {
  const raw = await kvGet(kv, `merge:files:${chatId}`);
  if (!raw) return [];
  try { return JSON.parse(raw); } catch { return []; }
}
async function appendMergeFile(kv, chatId, content, name) {
  const files = await getMergeFiles(kv, chatId);
  files.push({ content, name });
  await kvPut(kv, `merge:files:${chatId}`, JSON.stringify(files));
  return files;
}

const HELP_MSG = `👋 <b>Quiz Generator Bot</b>

<b>Single file:</b> Send any <code>.json</code> or <code>.txt</code> file → get an interactive bilingual HTML quiz instantly.

<b>Merge unlimited files:</b>
1️⃣ Type /merge
2️⃣ Send files one by one (any number)
3️⃣ Type /done → bot merges all &amp; sends combined quiz

Type /cancel to abort a merge at any time.

<b>JSON format:</b>
<pre>[{
  "qEnglish": "Question?",
  "qHindi": "प्रश्न?",
  "optionsEnglish": ["A","B","C","D"],
  "optionsHindi": ["अ","ब","स","द"],
  "correct": 1,
  "explanationEnglish": "Because…",
  "subject": "Physics", "topic": "Optics"
}]</pre>`;

async function handleTelegram(request, token, kv) {
  let update;
  try { update = await request.json(); } catch { return okResp(); }

  const message = update.message || update.channel_post || {};
  const chatId  = message?.chat?.id;
  if (!chatId) return okResp();

  const text       = message.text || '';
  const mergeState = await kvGet(kv, `merge:state:${chatId}`);
  const collecting = mergeState === 'collecting';

  const toTitle = n => n.replace(/\.\w+$/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // ── Commands ─────────────────────────────────────────────
  if (text.startsWith('/start') || text.startsWith('/help')) {
    await clearMergeState(kv, chatId);
    await tgMsg(token, chatId, HELP_MSG);
    return okResp();
  }
  if (text.startsWith('/cancel')) {
    await clearMergeState(kv, chatId);
    await tgMsg(token, chatId, '❌ Merge cancelled. Send a file anytime for a single quiz, or /merge to start again.');
    return okResp();
  }
  if (text.startsWith('/merge')) {
    if (!kv) {
      await tgMsg(token, chatId,
        '⚠️ Merge mode requires KV storage.\nSet up QUIZ_STORE KV namespace in Cloudflare Workers (see wrangler.toml).');
      return okResp();
    }
    await clearMergeState(kv, chatId);
    await kvPut(kv, `merge:state:${chatId}`, 'collecting');
    await kvPut(kv, `merge:files:${chatId}`, '[]');
    await tgMsg(token, chatId,
      '🔀 <b>Merge mode — collecting files</b>\n\nSend your <b>.json</b> or <b>.txt</b> quiz files one by one.\nType /done when finished (minimum 2 files).\nType /cancel to abort.', 'HTML');
    return okResp();
  }
  if (text.startsWith('/done')) {
    if (!collecting) {
      await tgMsg(token, chatId, '⚠️ No merge in progress. Use /merge first to start collecting files.');
      return okResp();
    }
    const files = await getMergeFiles(kv, chatId);
    await clearMergeState(kv, chatId);
    if (files.length < 2) {
      await tgMsg(token, chatId, `⚠️ You only sent ${files.length} file(s). Please use /merge and send at least 2 files.`);
      return okResp();
    }
    await tgMsg(token, chatId, `⚙️ Merging ${files.length} files and generating quiz…`);
    const allLists = [];
    for (let i = 0; i < files.length; i++) {
      try {
        const q = JSON.parse(files[i].content);
        if (!Array.isArray(q) || !q.length) throw new Error('empty array');
        allLists.push(q);
      } catch {
        await tgMsg(token, chatId, `❌ File ${i + 1} (${escHtml(files[i].name)}) has invalid data. Please start over with /merge.`, 'HTML');
        return okResp();
      }
    }
    const merged  = mergeQuestions(...allLists);
    const title   = files.map(f => toTitle(f.name)).join(' + ');
    const outName = files[0].name.replace(/\.\w+$/, '') + '_merged_quiz.html';
    const htmlOut = generateHtml(merged, title);
    const totals  = allLists.map(l => l.length).join(' + ');
    const caption = `✅ <b>Merged Quiz (${files.length} files)</b>\n📋 ${merged.length} unique questions (${totals})\n🌙 Dark mode · 🏅 Custom marking · 📊 Stats`;
    const result  = await tgSendDoc(token, chatId, htmlOut, outName, caption);
    if (!result?.ok)
      await tgMsg(token, chatId, `⚠️ Generated but could not send: ${result?.description || 'error'}`);
    return okResp();
  }

  // ── Document received ────────────────────────────────────
  const doc = message.document;
  if (doc) {
    const filename = doc.file_name || 'quiz.json';
    const ext      = filename.split('.').pop().toLowerCase();

    if (!['json', 'txt'].includes(ext)) {
      await tgMsg(token, chatId, '❌ Please send a <b>.json</b> or <b>.txt</b> file.', 'HTML');
      return okResp();
    }

    const fileUrl = await tgGetFileUrl(token, doc.file_id);
    if (!fileUrl) { await tgMsg(token, chatId, '❌ Could not access your file. Try again.'); return okResp(); }
    const content = await (await fetch(fileUrl)).text();

    let questions;
    try { questions = JSON.parse(content); } catch {
      await tgMsg(token, chatId, '❌ Invalid JSON format. Please check your file.'); return okResp();
    }
    if (!Array.isArray(questions) || !questions.length) {
      await tgMsg(token, chatId, '❌ JSON must be a non-empty array of question objects.'); return okResp();
    }

    // ── COLLECTING MODE: add to pile ────────────────────────
    if (collecting) {
      const files = await appendMergeFile(kv, chatId, content, filename);
      await tgMsg(token, chatId,
        `✅ <b>File ${files.length} received</b>: ${escHtml(filename)} (${questions.length} questions)\n\nTotal collected: <b>${files.length} file(s)</b>\n\nSend more files or type /done to generate the merged quiz.\nType /cancel to abort.`, 'HTML');
      return okResp();
    }

    // ── SINGLE FILE MODE ─────────────────────────────────────
    await tgMsg(token, chatId, '⚙️ Generating quiz…');
    const title   = toTitle(filename);
    const outName = filename.replace(/\.\w+$/, '') + '_quiz.html';
    const htmlOut = generateHtml(questions, title);
    const caption = `✅ <b>${escHtml(title)}</b>\n📋 ${questions.length} questions · Bilingual EN+हिं\n🌙 Dark mode · 🏅 Custom marking\n\n💡 Use /merge to combine multiple quiz files!`;

    const result = await tgSendDoc(token, chatId, htmlOut, outName, caption);
    if (!result?.ok)
      await tgMsg(token, chatId, `⚠️ Generated but could not send: ${result?.description || 'error'}`);
    return okResp();
  }

  // ── Unknown input ─────────────────────────────────────────
  const hint = collecting
    ? `📎 Collecting files for merge. Send more <b>.json/.txt</b> files or /done to generate (${(await getMergeFiles(kv, chatId)).length} file(s) so far). /cancel to abort.`
    : '📄 Send a <b>.json</b> or <b>.txt</b> file to generate a quiz.\nUse /merge to combine multiple files, or /help for details.';
  await tgMsg(token, chatId, hint, 'HTML');
  return okResp();
}

// ════════════════════════════════════════════════════════════
//  WEBHOOK SETUP  (GET /setup — run once after deploy)
// ════════════════════════════════════════════════════════════
async function setupWebhook(request, token) {
  const base    = new URL(request.url).origin;
  const webhook = `${base}/telegram`;
  const result  = await tgApi(token, 'setWebhook', { url: webhook, allowed_updates: ['message', 'channel_post'] });
  return jsonResp({
    ok: result.ok, webhook, telegram: result.description,
    next_step: result.ok
      ? '✅ Bot ready! Send a .json file or use /merge in Telegram.'
      : '❌ Failed. Check your TELEGRAM_TOKEN.',
  }, result.ok ? 200 : 500);
}

// ════════════════════════════════════════════════════════════
//  WEB /generate  — supports unlimited files
// ════════════════════════════════════════════════════════════
async function handleGenerate(request) {
  let formData;
  try { formData = await request.formData(); } catch {
    return jsonResp({ error: 'Could not parse form data.' }, 400);
  }

  const allLists = [];
  const allNames = [];

  // Legacy single 'file' key
  const legacy = formData.get('file');
  if (legacy && legacy.size > 0) {
    let q;
    try { q = JSON.parse(await legacy.text()); } catch (e) { return jsonResp({ error: `File JSON error: ${e.message}` }, 400); }
    if (!Array.isArray(q) || !q.length) return jsonResp({ error: 'File must be a non-empty array.' }, 400);
    allLists.push(q); allNames.push(legacy.name || 'quiz.json');
  }

  // Numbered files: file1, file2, ..., up to 50
  for (let i = 1; i <= 50; i++) {
    const f = formData.get(`file${i}`);
    if (!f || f.size === 0) continue;
    let q;
    try { q = JSON.parse(await f.text()); } catch (e) { return jsonResp({ error: `File ${i} JSON error: ${e.message}` }, 400); }
    if (!Array.isArray(q) || !q.length) return jsonResp({ error: `File ${i} must be a non-empty array.` }, 400);
    allLists.push(q); allNames.push(f.name || `quiz${i}.json`);
  }

  if (!allLists.length) return jsonResp({ error: 'No file uploaded.' }, 400);

  const toTitle = n => n.replace(/\.\w+$/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  let questions, title, outName;

  if (allLists.length === 1) {
    questions = allLists[0];
    title     = toTitle(allNames[0]);
    outName   = allNames[0].replace(/\.\w+$/, '') + '_quiz.html';
  } else {
    questions = mergeQuestions(...allLists);
    title     = allNames.map(toTitle).join(' + ');
    outName   = allNames[0].replace(/\.\w+$/, '') + '_merged_quiz.html';
  }

  const htmlOut = generateHtml(questions, title);
  return new Response(htmlOut, {
    headers: {
      'Content-Type': 'text/html; charset=UTF-8',
      'Content-Disposition': `attachment; filename="${outName}"`,
    },
  });
}

// ════════════════════════════════════════════════════════════
//  ENTRY POINT
// ════════════════════════════════════════════════════════════
export default {
  async fetch(request, env) {
    const url    = new URL(request.url);
    const path   = url.pathname;
    const method = request.method;
    const token  = env.TELEGRAM_TOKEN || '';
    const kv     = env.QUIZ_STORE || null;    // KV namespace binding (optional)

    if (method === 'POST' && path === '/telegram')
      return token ? handleTelegram(request, token, kv) : okResp();

    if (method === 'GET' && path === '/setup')
      return token ? setupWebhook(request, token)
                   : jsonResp({ error: 'TELEGRAM_TOKEN not set.' }, 400);

    if (method === 'POST' && path === '/generate')
      return handleGenerate(request);

    if (method === 'GET')
      return new Response(UPLOAD_PAGE, { headers: { 'Content-Type': 'text/html; charset=UTF-8' } });

    return new Response('Not found', { status: 404 });
  },
};
