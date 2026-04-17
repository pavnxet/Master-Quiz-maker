# Quiz Generator — Express/Node.js (v5)

**Local machine · Vercel · Any Node.js host**

A full-featured bilingual quiz generator ported from the Cloudflare Worker v5. Runs as a standard Express.js application — deploy to Vercel in one command, or run locally with `npm start`. Zero proprietary platform APIs. All secrets live in a `.env` file.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Environment Variables](#environment-variables)
5. [Local Machine Setup](#local-machine-setup)
6. [Vercel Deployment](#vercel-deployment)
7. [One-Time Setup Steps](#one-time-setup-steps)
8. [Web UI Guide](#web-ui-guide)
9. [Telegram Bot Guide](#telegram-bot-guide)
10. [API Endpoints Reference](#api-endpoints-reference)
11. [Question JSON Format](#question-json-format)
12. [AI Topic Normalization](#ai-topic-normalization)
13. [GitHub Question Bank](#github-question-bank)
14. [Turso Database](#turso-database)
15. [Security Features](#security-features)
16. [Differences from Cloudflare Worker](#differences-from-cloudflare-worker)
17. [Troubleshooting](#troubleshooting)

---

## What It Does

| Feature | Description |
|---|---|
| **Web Upload UI** | Drag-and-drop JSON quiz files, merge multiple files, download a self-contained HTML quiz |
| **Telegram Bot** | Send a `.json` file → get a fully interactive HTML quiz file back |
| **AI Normalization** | OpenRouter AI corrects abbreviated/misspelled topic names automatically |
| **GitHub Question Bank** | All questions saved to a GitHub repo, organized by subject/topic, deduplicated |
| **Analytics** | Turso DB tracks all generations, users, and question counts |
| **Self-contained Quiz HTML** | Output file runs fully offline in any browser |

---

## Project Structure

```
quiz-generator-express/
├── server.js              ← Main Express app + all route handlers
├── src/
│   ├── quiz-html.js       ← Self-contained quiz HTML generator (auto-extracted)
│   ├── upload-page.js     ← Web upload page HTML (auto-extracted)
│   ├── utils.js           ← escHtml, toBase64, validateQuestions, etc.
│   ├── db.js              ← Turso libSQL HTTP API (analytics)
│   ├── github.js          ← GitHub Contents API (question bank)
│   ├── ai.js              ← OpenRouter AI topic normalization
│   └── telegram.js        ← Telegram Bot API helpers
├── package.json
├── vercel.json            ← Vercel deployment config
├── .env.example           ← Copy to .env and fill in
└── .gitignore
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Node.js 18+** | Uses built-in `fetch`, `AbortController`, `TextEncoder` |
| **npm or pnpm** | For installing the 3 dependencies |
| **Telegram Bot Token** | From [@BotFather](https://t.me/BotFather) — `/newbot` |
| **GitHub Personal Access Token** | Fine-grained token, `Contents: Read & Write` on your repo |
| **GitHub repository** | Empty repo, e.g. `yourname/quiz-questions` |
| **Turso account + DB** | [turso.tech](https://turso.tech) free tier — for analytics (optional) |
| **OpenRouter API key** | [openrouter.ai](https://openrouter.ai) — free models available (optional) |

---

## Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# ── Telegram ───────────────────────────────────────────────
TELEGRAM_TOKEN=123456:ABC-DEF...
TELEGRAM_WEBHOOK_SECRET=any_random_string_32_chars   # optional but recommended

# ── GitHub ─────────────────────────────────────────────────
GITHUB_TOKEN=github_pat_xxxxx          # OR: GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
GITHUB_REPO=yourname/quiz-questions
GITHUB_BRANCH=main                     # default: main

# ── Turso (analytics) ──────────────────────────────────────
TURSO_DB_URL=https://mydb-myorg.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOi...

# ── OpenRouter (AI normalization) ──────────────────────────
OPENROUTER_API_KEY=sk-or-v1-xxx

# ── Security ───────────────────────────────────────────────
ADMIN_SECRET=your_secret_for_setup_initdb    # optional but recommended

# ── Server ─────────────────────────────────────────────────
PORT=3000
WORKER_ORIGIN=https://your-domain.vercel.app  # used in OpenRouter HTTP-Referer
```

### Which variables are required?

| Variable | Required | Without it... |
|---|---|---|
| `TELEGRAM_TOKEN` | For bot | Telegram bot is disabled |
| `GITHUB_TOKEN` / `GITHUB_PERSONAL_ACCESS_TOKEN` | For question bank | Bank disabled, no AI normalization |
| `GITHUB_REPO` | For question bank | Same as above |
| `OPENROUTER_API_KEY` | For AI | Topic names not normalized |
| `TURSO_DB_URL` + `TURSO_AUTH_TOKEN` | For analytics | `/dbstats` returns 503 |
| `TELEGRAM_WEBHOOK_SECRET` | Security | Webhook unauthenticated |
| `ADMIN_SECRET` | Security | `/setup` + `/initdb` are public |
| `PORT` | Server | Defaults to 3000 |

---

## Local Machine Setup

### 1. Install dependencies

```bash
cd quiz-generator-express
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual values
```

### 3. Start the server

```bash
# Production
npm start

# Development (auto-restarts on file changes, Node 18+)
npm run dev
```

The server starts at `http://localhost:3000` and prints a status summary:

```
✅ Quiz Generator running at http://localhost:3000
   GitHub bank : yourname/quiz-questions
   Turso DB    : ✅ configured
   OpenRouter  : ✅ configured
   Telegram    : ✅ configured
```

### 4. Expose locally for Telegram webhook (development only)

Telegram needs a public HTTPS URL to send webhook events. Use [ngrok](https://ngrok.com) or [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/):

**Using ngrok:**
```bash
# In a separate terminal
ngrok http 3000
```
Note the HTTPS URL it gives you (e.g. `https://abc123.ngrok-free.app`).

**Using Cloudflare Tunnel:**
```bash
cloudflared tunnel --url http://localhost:3000
```

Then register the webhook using that URL:
```
GET https://abc123.ngrok-free.app/setup
```

---

## Vercel Deployment

### Option A — Vercel CLI (recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# From the quiz-generator-express directory:
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Link to existing project? No (create new)
# - Project name: quiz-generator
# - Directory: ./  (current)
```

After the first deploy, add environment variables:

```bash
vercel env add TELEGRAM_TOKEN
vercel env add TELEGRAM_WEBHOOK_SECRET
vercel env add GITHUB_TOKEN
vercel env add GITHUB_REPO
vercel env add OPENROUTER_API_KEY
vercel env add TURSO_DB_URL
vercel env add TURSO_AUTH_TOKEN
vercel env add ADMIN_SECRET
vercel env add WORKER_ORIGIN   # set to your vercel URL: https://your-project.vercel.app
```

Then redeploy to pick up the env vars:
```bash
vercel --prod
```

### Option B — Vercel Dashboard

1. Push this folder to a GitHub repository
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import your repo
3. Select the `quiz-generator-express` folder as the **root directory**
4. Under **Environment Variables**, add all variables from the table above
5. Click **Deploy**

### After deploying to Vercel

Your app is live at `https://your-project.vercel.app`. Run one-time setup:

```
GET https://your-project.vercel.app/setup?secret=YOUR_ADMIN_SECRET
GET https://your-project.vercel.app/initdb?secret=YOUR_ADMIN_SECRET
```

> **Important — Vercel function timeout:**
> Vercel Hobby plan has a **10-second** function timeout. The AI normalization call
> averages 15–25 seconds. Upgrade to Vercel Pro (60s timeout, already configured in
> `vercel.json`) or use a VPS/Railway/Render for reliable AI normalization.

### Other hosting options with no timeout issues

| Platform | Command | Notes |
|---|---|---|
| **Railway** | `railway up` | Persistent server, no timeout |
| **Render** | Push to GitHub, connect repo | Free tier sleeps after 15 min |
| **Fly.io** | `fly launch && fly deploy` | Generous free tier |
| **DigitalOcean App Platform** | Connect GitHub repo | $5/mo Starter |
| **VPS (any)** | `npm start` with PM2 | Full control |

**Running with PM2 on a VPS:**
```bash
npm install -g pm2
pm2 start server.js --name quiz-generator
pm2 save
pm2 startup
```

---

## One-Time Setup Steps

Run these once, in order, after your first deployment.

### Step 1 — Initialize the database

```
GET /initdb
```

If `ADMIN_SECRET` is set:
```
GET /initdb?secret=YOUR_ADMIN_SECRET
# or with header:
curl -H "X-Admin-Secret: YOUR_ADMIN_SECRET" https://your-domain.com/initdb
```

Expected response:
```json
{ "ok": true, "message": "Tables created (or already exist)." }
```

Safe to call multiple times — uses `CREATE TABLE IF NOT EXISTS`.

### Step 2 — Register the Telegram webhook

```
GET /setup
```

If `ADMIN_SECRET` is set:
```
GET /setup?secret=YOUR_ADMIN_SECRET
```

Expected response:
```json
{
  "ok": true,
  "webhook": "https://your-domain.com/telegram",
  "secretRegistered": true,
  "adminProtected": true,
  "warnings": [],
  "note": "✅ Bot ready! Send a .json file to your bot in Telegram."
}
```

If `warnings` is not empty, it means some security options are not configured.

> **Note:** Run `/setup` again whenever your domain changes (e.g. new ngrok URL during development).

---

## Web UI Guide

Open `http://localhost:3000` (or your deployed URL) in a browser.

### Page layout

```
┌──────────────────────────────────────────────────────────┐
│  📚 Quiz Generator                     [Question Bank]   │
│  Upload one or more JSON quiz files — merge & generate   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │    📂 Drop files here or click to browse         │   │
│  │    Supports .json and .txt (JSON content)        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  physics_optics.json — 45 questions            [✕]      │
│  biology_cells.json  — 32 questions            [✕]      │
│  Total: 77 questions across 2 files                      │
│                                                          │
│  ☑ Save to Question Bank                                 │
│    ⚡ Uncheck to skip GitHub sync & AI normalization     │
│                                                          │
│  [⬇️  Generate & Download Quiz HTML]                     │
│                                                          │
│  ▓▓▓▓▓▓▓░░░░░  62%                                      │
│  AI normalizing topics…  🤖 Talking to gpt-oss-120b     │
│                                                          │
│  📊 Platform Stats                                       │
│  ┌──────────┬──────────┬───────────┬──────────┐         │
│  │ 143      │ 4,821    │  112      │  31      │         │
│  │ Quizzes  │Questions │ Telegram  │Bot Users │         │
│  └──────────┴──────────┴───────────┴──────────┘         │
└──────────────────────────────────────────────────────────┘
```

### How to use

1. **Drag and drop** one or more `.json` quiz files onto the upload zone, or click to open a file picker
2. Each file shows its question count — remove any with the ✕ button
3. **Save to Question Bank** (checkbox, default: on):
   - **Checked** — questions are saved to GitHub after AI normalization; the 5-stage progress bar is shown
   - **Unchecked** — skips GitHub and AI; progress bar shows only 3 stages; much faster
4. Click **Generate & Download Quiz HTML**
5. The progress bar updates through stages:

   | Stage | % | What's happening |
   |---|---|---|
   | Reading file | 15% | Parsing your JSON |
   | Checking bank | 35% | Fetching GitHub taxonomy (bank mode only) |
   | AI normalizing | 62% | OpenRouter normalizes topic names (bank mode only) |
   | Building quiz | 82% | Generating the HTML |
   | Almost there | 95% | Packaging |
   | Done | 100% | File downloads automatically |

6. Your browser downloads a self-contained `.html` quiz file

### The generated quiz file

The downloaded HTML file:

- **Works fully offline** — open it from your desktop, no internet needed
- **Bilingual** — English and Hindi side by side
- **Features:** dark mode, scramble mode, flag questions for review, score tracking, keyboard shortcuts
- **Results screen** — shows score, percentage, review of wrong answers

---

## Telegram Bot Guide

### First time

1. Find your bot on Telegram (the username you chose with BotFather)
2. Send `/start`

### Commands

| Command | What it does |
|---|---|
| `/start` | Welcome message and quick guide |
| `/help` | Full help with all commands |
| `/topics` | List all subjects and topics in the question bank |
| `/download Physics \| Optics` | Download a quiz for a specific topic |
| `/mystats` | Your personal quiz generation count |
| `/globalstats` | Platform-wide totals |

### Uploading a file

1. Tap the **paperclip (📎)** icon
2. Select **File** (not Photo/Gallery)
3. Pick your `.json` quiz file
4. Optionally type `nosave` or `#nosave` in the caption to skip saving
5. Send

The bot sends progress updates in-place (editing a single message):

```
⏳ Reading file… [▓░░░░] 20%
🔍 Checking question bank… [▓▓░░░] 40%
🤖 AI normalizing topics… [▓▓▓░░] 60%
⚙️ Building quiz… [▓▓▓▓░] 80%
✅ Done! Quiz delivered. [▓▓▓▓▓] 100%
```

Then it sends the `.html` quiz file directly in the chat.

### Download from the bank

```
/download Physics | Optics
/download Biology | Cell Biology
/download गणित | बीजगणित
```

Use `/topics` first to see exact available names.

### Limits

| Limit | Value |
|---|---|
| Max file size | 20 MB (Telegram Bot API hard limit) |
| Max questions per upload | 500 |
| Supported formats | `.json`, `.txt` (JSON content) |

---

## API Endpoints Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | — | Upload page HTML |
| `POST` | `/generate` | — | Generate quiz HTML from upload |
| `POST` | `/telegram` | Webhook secret | Telegram webhook receiver |
| `GET` | `/setup` | ADMIN_SECRET | Register Telegram webhook |
| `GET` | `/initdb` | ADMIN_SECRET | Create database tables |
| `GET` | `/dbstats` | — | JSON usage statistics |
| `GET` | `/api/browse` | — | JSON list of topics in the bank |
| `GET` | `/api/download?subject=X&topic=Y` | — | JSON questions for a topic |

### POST /generate

**Request:** `multipart/form-data`

| Field | Required | Description |
|---|---|---|
| `file` | Yes | The `.json` quiz file (max 10 MB) |
| `title` | No | Quiz title (defaults to filename without extension) |
| `outname` | No | Output HTML filename |
| `saveToGithub` | No | `"true"` or `"false"` (default: `"true"`) |

**Response (success):** `text/html` — the complete self-contained quiz HTML file

**Response (error):**
```json
{ "error": "No file uploaded." }
{ "error": "Invalid JSON: Unexpected token ..." }
{ "error": "JSON must be a non-empty array." }
{ "error": "No valid question objects found." }
{ "error": "Too many questions. Maximum 500 per upload." }
{ "error": "File too large. Maximum 10 MB per upload." }
```

**Status codes:** `200` success · `400` bad request · `413` file too large · `503` dependency unavailable

---

## Question JSON Format

Each uploaded file must be a JSON array of question objects:

```json
[
  {
    "subject": "Physics",
    "topic": "Optics",
    "qEnglish": "What is the speed of light in vacuum?",
    "qHindi": "निर्वात में प्रकाश की गति क्या है?",
    "optionsEnglish": [
      "3 × 10⁸ m/s",
      "3 × 10⁶ m/s",
      "3 × 10¹⁰ m/s",
      "3 × 10⁴ m/s"
    ],
    "optionsHindi": [
      "3 × 10⁸ m/s",
      "3 × 10⁶ m/s",
      "3 × 10¹⁰ m/s",
      "3 × 10⁴ m/s"
    ],
    "correctIndex": 0,
    "explanation": "The speed of light in vacuum is approximately 3 × 10⁸ metres per second."
  }
]
```

| Field | Required | Description |
|---|---|---|
| `qEnglish` | One of these | Question text in English |
| `qHindi` | One of these | Question text in Hindi |
| `optionsEnglish` | Yes | 2–6 answer choices in English |
| `optionsHindi` | Yes | 2–6 answer choices in Hindi |
| `correctIndex` | Yes | Zero-based index of the correct answer |
| `subject` | No | Subject (used for bank organization) |
| `topic` | No | Topic (used for bank organization) |
| `explanation` | No | Shown after the user answers |

At least one of `qEnglish` or `qHindi` is required per question. Items missing both are silently dropped.

---

## AI Topic Normalization

When saving to the question bank is enabled, the server:

1. **Extracts** all unique `subject/topic` pairs from the upload
2. **Fetches** the current GitHub structure (existing subjects and topics)
3. **Checks** whether all pairs already match exactly — if yes, **AI is skipped** (instant)
4. **Calls OpenRouter** (`openai/gpt-oss-120b:free`, temperature 0, max 4096 tokens)
5. **Maps** each question to its normalized names via dictionary lookup
6. **Saves** normalized questions to GitHub

### AI has a hard 25-second timeout

If OpenRouter doesn't respond within 25 seconds, normalization is skipped and the original names are used. Questions are still saved and the quiz is still generated.

### Example normalizations

| Uploaded | Normalized to |
|---|---|
| `Phy / optics basics` | `Physics / Optics` |
| `Bio / Cell Bio` | `Biology / Cell Biology` |
| `chem / periodic tbl` | `Chemistry / Periodic Table` |
| `Physics / Optics` | `Physics / Optics` ← bypass, no AI call |

---

## GitHub Question Bank

Questions are stored in your repo as:

```
questions/
├── Physics/
│   ├── Optics.json          ← array of question objects
│   └── Mechanics.json
├── Biology/
│   └── Cell Biology.json
└── गणित/
    └── बीजगणित.json
```

- New uploads **merge** into existing files (deduplicated by question text)
- New subject/topic combinations create new files automatically
- Commit messages record the source (`web` or `telegram`) and number of new questions added

---

## Turso Database

Two tables track all activity:

### `quiz_generations`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-increment PK |
| `source` | TEXT | `web` or `telegram` |
| `title` | TEXT | Quiz title |
| `questions_count` | INTEGER | Question count |
| `telegram_chat_id` | TEXT | Telegram user ID (nullable) |
| `telegram_username` | TEXT | Telegram username (nullable) |
| `created_at` | TEXT | UTC datetime |

### `telegram_users`

| Column | Type | Description |
|---|---|---|
| `chat_id` | TEXT | Primary key |
| `username` | TEXT | Telegram username |
| `first_name` | TEXT | First name |
| `total_quizzes` | INTEGER | Cumulative quiz count |
| `first_seen` | TEXT | First interaction |
| `last_seen` | TEXT | Last interaction |

---

## Security Features

All security features from worker v5 are carried over:

| Feature | How it works |
|---|---|
| **Security headers** | Express middleware adds CSP, X-Frame-Options, nosniff, XSS-Protection to every response |
| **Webhook verification** | `/telegram` checks `X-Telegram-Bot-Api-Secret-Token` header against `TELEGRAM_WEBHOOK_SECRET` |
| **Admin guard** | `/setup` and `/initdb` require `?secret=ADMIN_SECRET` or `X-Admin-Secret` header |
| **File size limit** | Multer rejects uploads > 10 MB before they're read |
| **Question count cap** | Maximum 500 questions per upload (web + Telegram) |
| **Input validation** | Invalid question objects are dropped before processing |
| **AI timeout** | OpenRouter calls abort after 25 seconds |
| **GitHub timeout** | All GitHub API calls abort after 10 seconds |

---

## Differences from Cloudflare Worker

| Aspect | Cloudflare Worker | Express/Node.js |
|---|---|---|
| **Deployment** | CF Dashboard or Wrangler | `vercel`, `npm start`, PM2 |
| **Environment variables** | CF Worker Settings | `.env` file / host dashboard |
| **`ctx.waitUntil`** | Native CF API | `fireAndForget()` (unblocked promise) |
| **`btoa` / `atob`** | Built-in globals | Node.js built-ins (18+) |
| **Form data** | `request.formData()` | `multer` middleware |
| **Secret bindings** | CF encrypted bindings | `.env` + `dotenv` |
| **Cold starts** | ~0ms (V8 isolate) | Node.js process startup |
| **Execution timeout** | 30s wall-clock | No limit locally; 60s on Vercel Pro |
| **AI timeout risk** | High (30s limit) | Low (no limit locally) |

---

## Troubleshooting

### Server won't start

```
Error: Cannot find module 'express'
```
→ Run `npm install` in the `quiz-generator-express` directory.

```
TypeError: fetch is not a function
```
→ Upgrade Node.js to version 18 or higher. Check with `node --version`.

### Telegram bot not responding

1. Check `TELEGRAM_TOKEN` is correct in `.env`
2. Confirm the webhook is registered: visit `/setup?secret=YOUR_ADMIN_SECRET`
3. For local development: make sure ngrok/tunnel is running and the webhook URL is current
4. Check server logs for incoming POST requests to `/telegram`

### AI normalization not working

1. Verify `OPENROUTER_API_KEY` is set
2. Verify `GITHUB_TOKEN` and `GITHUB_REPO` are configured (AI only runs when the bank is accessible)
3. Check [openrouter.ai/models](https://openrouter.ai/models) — confirm `openai/gpt-oss-120b:free` is available
4. The AI has a 25-second timeout — if the model is slow, normalization is silently skipped

### Questions not saving to GitHub

1. Check `GITHUB_TOKEN` has `Contents: Read and Write` permission
2. Check `GITHUB_REPO` format is `owner/repo`, not a full URL
3. Check `GITHUB_BRANCH` matches an existing branch in the repo
4. Look for `GitHub save error` lines in server logs

### `/initdb` or `/setup` return 403

→ `ADMIN_SECRET` is set. Call with the secret:
```
/setup?secret=YOUR_ADMIN_SECRET
```
Or add the header:
```
curl -H "X-Admin-Secret: YOUR_ADMIN_SECRET" http://localhost:3000/setup
```

### Progress bar stalls at 62% (AI stage)

The `gpt-oss-120b:free` model averages 15–25 seconds. The progress bar is time-based animation and will appear stuck until the server responds. This is expected. The request times out after 25 seconds and proceeds without AI normalization.

### Vercel deployment returns 504 on /generate

→ The AI call exceeds Vercel's function timeout. Solutions:
- Upgrade to **Vercel Pro** (60s timeout, already set in `vercel.json`)
- Deploy to **Railway**, **Fly.io**, or a VPS where there's no timeout
- Upload files with `nosave` in caption / uncheck "Save to Bank" to bypass AI
