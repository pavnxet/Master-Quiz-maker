# AI Topic Normalizer — Implementation Plan

## Overview

When a user uploads a JSON/TXT quiz file, the worker will:
1. Parse the questions and extract all unique subject/topic pairs
2. Fetch the existing GitHub question bank taxonomy **in parallel**
3. Send both sets to the AI in a **single batch call** for normalization
4. Apply the AI's mapping to every question in the file
5. Save the normalized questions to GitHub and return the quiz HTML

Model: `openai/gpt-oss-120b:free` via OpenRouter (`https://openrouter.ai/api/v1/chat/completions`)

---

## New Environment Variable Required

```
OPENROUTER_API_KEY   — your OpenRouter API key
```

No other changes to existing env vars.

---

## Step-by-Step Logic

### Step 1 — File Downloaded & Parsed (existing flow, unchanged)

User sends `.json` or `.txt` file via Telegram (or web POST `/generate`).  
Worker downloads and parses it into a `questions[]` array. If parse fails → error message, stop.

---

### Step 2 — Extract New Pairs + Fetch GitHub Taxonomy (PARALLEL)

Both run at the **same time** with `Promise.all`:

```
[newPairs, githubStructure] = await Promise.all([
  extractPairs(questions),   // sync, immediate
  ghListTopics(env)          // async GitHub API call
])
```

**`extractPairs(questions)`** → collects unique `{ subject, topic }` objects from the array.  
Example output:
```json
[
  { "subject": "Phy", "topic": "optics basics" },
  { "subject": "Physics", "topic": "Optic" },
  { "subject": "Bio", "topic": "Cell Bio" }
]
```

**`ghListTopics(env)`** → returns existing taxonomy from GitHub:
```json
{
  "Physics": ["Optics", "Mechanics", "Thermodynamics"],
  "Biology": ["Cell Biology", "Genetics"]
}
```

If GitHub returns `null` (not configured or empty), skip AI and save as-is.

**Zero-latency bypass — local pre-check before any AI call:**

After both results are in hand, run a local JavaScript check to see if every extracted pair already exists verbatim in `githubStructure`. If so, skip the OpenRouter `fetch()` entirely — no network round-trip, no rate limit cost, 0 ms added latency.

```javascript
function allPairsMatch(newPairs, githubStructure) {
  if (!githubStructure) return false;
  return newPairs.every(({ subject, topic }) => {
    const topics = githubStructure[subject];
    return Array.isArray(topics) && topics.includes(topic);
  });
}

// After Promise.all resolves:
if (!githubStructure || allPairsMatch(newPairs, githubStructure)) {
  // Perfect match or no bank — skip AI, use questions as-is
  normalizedQuestions = questions;
} else {
  // Only call AI when there is real normalization work to do
  normalizedQuestions = await aiNormalizeAndApply(env, questions, newPairs, githubStructure);
}
```

---

### Step 3 — Single AI Batch Call

Build **one** prompt with all new pairs and the full existing taxonomy, then call OpenRouter once.

**System prompt (fixed):**
```
You are a taxonomy normalizer for an educational question bank.
Your job: given a list of new subject/topic pairs from a quiz file and the
existing question bank structure, map each new pair to the best matching
existing subject and topic.

Rules:
- Fix obvious abbreviations: "Phy" → "Physics", "Bio" → "Biology"
- Fix case/spelling: "optics basics" → "Optics", "Cell Bio" → "Cell Biology"
- If a new subject/topic has NO close match, keep it exactly as-is (it is new)
- Never invent names — only use names from the existing bank OR the original name
- Return ONLY valid JSON, no explanation, no markdown fences
```

**User message (dynamic, built per request):**
```
Existing question bank:
{
  "Physics": ["Optics", "Mechanics", "Thermodynamics"],
  "Biology": ["Cell Biology", "Genetics"]
}

New pairs to normalize:
[
  { "subject": "Phy", "topic": "optics basics" },
  { "subject": "Physics", "topic": "Optic" },
  { "subject": "Bio", "topic": "Cell Bio" },
  { "subject": "Chemistry", "topic": "Periodic Table" }
]

Return a JSON OBJECT (not an array) where each key is "OriginalSubject|||OriginalTopic"
and each value is { "subject": "NormalizedSubject", "topic": "NormalizedTopic" }.
Every input pair must appear as a key. Use the pipe-separated key format exactly.
```

**Expected AI response:**
```json
{
  "Phy|||optics basics":         { "subject": "Physics",   "topic": "Optics" },
  "Physics|||Optic":             { "subject": "Physics",   "topic": "Optics" },
  "Bio|||Cell Bio":              { "subject": "Biology",   "topic": "Cell Biology" },
  "Chemistry|||Periodic Table":  { "subject": "Chemistry", "topic": "Periodic Table" }
}
```

Using a dictionary keyed by `"Subject|||Topic"` instead of an array completely eliminates array alignment bugs — even if the AI reorders or drops an item, the worker looks up each question by its own key, so no question is ever mis-mapped.

**OpenRouter call:**
```javascript
POST https://openrouter.ai/api/v1/chat/completions
Authorization: Bearer OPENROUTER_API_KEY
{
  "model": "openai/gpt-oss-120b:free",
  "response_format": { "type": "json_object" },  // forces valid JSON output
  "max_tokens": 512,
  "temperature": 0,   // deterministic — no creativity needed here
  "messages": [
    { "role": "system", "content": "<system prompt above>" },
    { "role": "user",   "content": "<dynamic message above>" }
  ]
}
```

**Fallback:** If AI call fails (network error, invalid JSON, wrong array length) → log warning, skip normalization, proceed with original subject/topic values unchanged. Never block the quiz delivery.

---

### Step 4 — Apply Dictionary Mapping to Questions

The AI response is already a dictionary keyed by `"Subject|||Topic"`, so no re-indexing is needed. Each question is looked up directly by its own key — no alignment risk, no off-by-one errors possible.

```javascript
// aiResult is the parsed dictionary from the AI response, e.g.:
// { "Phy|||optics basics": { subject: "Physics", topic: "Optics" }, ... }

const normalized = questions.map(q => {
  const key = `${q.subject}|||${q.topic}`;
  const mapped = aiResult[key]; // direct dictionary lookup — never mis-maps
  if (!mapped) return q;        // key missing → keep original (safe fallback)
  return { ...q, subject: mapped.subject, topic: mapped.topic };
});
```

Result: every question has a clean, canonical subject/topic. Missing keys (if AI dropped one) safely fall back to the original value — no corruption, no wrong mappings.

---

### Step 5 — Save & Return (existing flow, with normalized questions)

The normalized questions flow into the **existing** functions unchanged:

- `saveQuestionsToGithub(env, normalized, source)` — saves under correct canonical paths
- `generateHtml(normalized, title)` — builds the interactive quiz HTML
- `tgSendDocument(...)` — sends the HTML back to user

Both the DB analytics tracking (`trackGeneration`) and GitHub save run in `ctx.waitUntil()` so they **never delay** the response to the user.

---

## Where AI Is Called (entry points)

The AI normalization is injected in **two places** in the existing code:

### A. Telegram file handler (`handleTelegram`)

Current flow:
```
parse questions → generateHtml → tgSendDocument → [waitUntil] saveToGithub
```

New flow:
```
parse questions
  ↓ (parallel)
[extract pairs + ghListTopics]
  ↓
[AI normalize — single call]
  ↓
apply mapping to questions
  ↓
generateHtml → tgSendDocument → [waitUntil] saveToGithub
```

### B. Web `/generate` endpoint (POST)

Same injection point: after parsing the uploaded file, before generating HTML.

---

## Loading / Progress Feedback

Because the AI call adds real processing time (~1–4 seconds), users are kept informed at every stage.

### Telegram — Sequential Status Messages

Telegram has no progress bars, so we send short text messages as each stage completes.  
Each message **edits the previous one in-place** using `editMessageText` (avoids chat spam).

```
Stage 1 — immediately on file receipt:
  "⏳ Reading file… [▓░░░░] 20%"

Stage 2 — after parse + pairs extracted:
  "🔍 Checking question bank… [▓▓░░░] 40%"

Stage 3 — after ghListTopics returns:
  "🤖 AI normalizing topics… [▓▓▓░░] 60%"

Stage 4 — after AI responds + mapping applied:
  "⚙️ Building quiz… [▓▓▓▓░] 80%"

Stage 5 — quiz ready, sending file:
  "✅ Done! Sending your quiz… [▓▓▓▓▓] 100%"
```

Implementation: send first message → save `message_id` → edit in-place at each stage.

```javascript
// Send initial status and store message_id
const statusMsg = await tgSend(token, chatId, "⏳ Reading file… [▓░░░░] 20%");
const statusMsgId = statusMsg?.result?.message_id;

// Helper to update the same message
async function setStatus(text) {
  if (!statusMsgId) return;
  await tgApi(token, "editMessageText", {
    chat_id: chatId,
    message_id: statusMsgId,
    text,
    parse_mode: "HTML"
  });
}

// Called at each stage:
await setStatus("🔍 Checking question bank… [▓▓░░░] 40%");
await setStatus("🤖 AI normalizing topics… [▓▓▓░░] 60%");
await setStatus("⚙️ Building quiz… [▓▓▓▓░] 80%");
await setStatus("✅ Done! Sending your quiz… [▓▓▓▓▓] 100%");
```

If AI is skipped (GitHub not configured or `#nosave`), stages 3 and 4 are collapsed and the bar jumps straight to 80% → 100%.

---

### Web UI — Animated Progress Bar

The web `/generate` endpoint is called via `fetch()` in the browser.  
While waiting, the upload page shows an animated progress bar.

**Behaviour:**

- Bar starts at 0% the moment the user clicks "Generate"
- Animates automatically through fake checkpoints to create a sense of progress
- Snaps to 100% when the server responds
- If the server errors, the bar turns red and resets

**HTML/CSS/JS additions to the upload page UI (injected into `handleUpload` HTML):**

```html
<!-- Progress bar element (hidden by default) -->
<div id="progress-wrap" style="display:none; margin:16px 0;">
  <div style="display:flex; justify-content:space-between; font-size:.8rem; color:var(--muted); margin-bottom:6px;">
    <span id="progress-label">Processing…</span>
    <span id="progress-pct">0%</span>
  </div>
  <div style="background:var(--border); border-radius:99px; height:10px; overflow:hidden;">
    <div id="progress-bar"
         style="height:100%; width:0%; border-radius:99px;
                background:linear-gradient(90deg,var(--primary),var(--primary-light));
                transition:width .4s ease, background .3s;">
    </div>
  </div>
  <div id="progress-stage" style="font-size:.75rem; color:var(--muted); margin-top:5px; text-align:center;"></div>
</div>
```

**JavaScript — fake progress with real stages:**

```javascript
const STAGES = [
  { pct: 15, label: "Reading file…",              stage: "⏳ Parsing questions" },
  { pct: 35, label: "Checking question bank…",    stage: "🔍 Fetching GitHub taxonomy" },
  { pct: 60, label: "AI normalizing topics…",     stage: "🤖 Talking to gpt-oss-120b" },
  { pct: 80, label: "Building quiz…",             stage: "⚙️ Applying topic mapping" },
  { pct: 95, label: "Almost there…",              stage: "📦 Generating HTML" },
];

function runProgressBar() {
  const wrap  = document.getElementById('progress-wrap');
  const bar   = document.getElementById('progress-bar');
  const lbl   = document.getElementById('progress-label');
  const pct   = document.getElementById('progress-pct');
  const stage = document.getElementById('progress-stage');

  wrap.style.display = 'block';
  let i = 0;

  // Advance through stages every ~1.2 s
  const iv = setInterval(() => {
    if (i >= STAGES.length) { clearInterval(iv); return; }
    const s = STAGES[i++];
    bar.style.width   = s.pct + '%';
    lbl.textContent   = s.label;
    pct.textContent   = s.pct + '%';
    stage.textContent = s.stage;
  }, 1200);

  return {
    complete() {
      clearInterval(iv);
      bar.style.width       = '100%';
      lbl.textContent       = 'Done!';
      pct.textContent       = '100%';
      stage.textContent     = '✅ Quiz ready — downloading';
      setTimeout(() => { wrap.style.display = 'none'; }, 2000);
    },
    error() {
      clearInterval(iv);
      bar.style.background  = 'var(--danger)';
      bar.style.width       = '100%';
      lbl.textContent       = 'Failed';
      stage.textContent     = '❌ Something went wrong';
      setTimeout(() => { wrap.style.display = 'none'; bar.style.background = ''; bar.style.width = '0%'; }, 3000);
    }
  };
}

// Usage in the generate button handler:
const progress = runProgressBar();
try {
  const r = await fetch('/generate', { method: 'POST', body: fd });
  if (!r.ok) { progress.error(); /* show error */ return; }
  progress.complete();
  // ... trigger download
} catch(e) {
  progress.error();
}
```

---

## New Functions to Add

```
aiNormalizePairs(env, newPairs, githubStructure)
  → calls OpenRouter (model: openai/gpt-oss-120b:free), returns normalized pairs array
  → on any failure: returns newPairs unchanged

extractUniquePairs(questions)
  → returns deduplicated [{subject, topic}] array

applyNormalization(questions, newPairs, normalizedPairs)
  → returns new questions array with canonical subject/topic

setStatus(token, chatId, msgId, text)        [Telegram only]
  → editMessageText in-place for progress updates

runProgressBar()                              [Web UI only]
  → returns { complete(), error() } controller
```

---

## Timing Estimate (per request)

| Step | Time |
|---|---|
| Parse questions (sync) | ~0 ms |
| `Promise.all` [extractPairs + ghListTopics] | ~200–400 ms (GitHub API) |
| AI call — `gpt-oss-120b:free` (single batch) | ~1000–4000 ms |
| Apply mapping + generateHtml | ~10 ms |
| **Total added latency** | **~1200–4500 ms** |

The user sees live progress the entire time — no blank waiting screen.  
GitHub save + DB tracking are background tasks (zero extra wait after response).

---

## Edge Cases

| Case | Behavior |
|---|---|
| GitHub not configured | Skip AI entirely, save as-is, progress bar jumps to 100% |
| GitHub bank is empty | Skip AI (no taxonomy to compare), progress bar jumps to 100% |
| AI call fails / times out | Log warning, use original names, progress continues normally |
| AI returns invalid JSON | Fall back to original names |
| AI omits some keys from the dictionary | Missing keys fall back to original name per question — no corruption |
| `#nosave` in caption | Skip AI + GitHub entirely, quiz still generated, fast path |
| All new pairs already match existing names exactly | **Local JS check catches this first — AI call skipped entirely (0 ms added latency)** |

---

## New Env Var Summary

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Auth for OpenRouter API |
| (all existing vars unchanged) | — |

---

## What Does NOT Change

- Quiz HTML generation logic
- Turso DB tracking
- Telegram commands (`/topics`, `/download`, `/mystats`, `/globalstats`)
- GitHub deduplication logic
- `#nosave` opt-out behaviour

---

## Green Light Checklist

- [ ] Logic flow approved
- [ ] Model confirmed: `openai/gpt-oss-120b:free`
- [ ] `OPENROUTER_API_KEY` will be added to Cloudflare Worker env vars
- [ ] Confirm: AI normalization applies to both Telegram AND web `/generate` endpoint
- [ ] Confirm: Telegram progress via edited messages is acceptable
- [ ] Confirm: Web UI animated progress bar is acceptable
- [ ] Confirm: fallback (original names) on AI failure is acceptable
