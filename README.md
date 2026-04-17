# Quiz Generator — Express / Node.js

**Node.js · Express · Vercel · Local Machine · Telegram Bot · GitHub Question Bank · AI Topic Normalization · Turso DB**

> This is the **Express / Node.js port** of `worker_v5.0.js`. Every feature works identically. Instead of running on Cloudflare's edge infrastructure, it runs as a standard Node.js HTTP server — locally, on any VPS, or deployed to Vercel.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Environment Variables](#environment-variables)
5. [Local Development Setup](#local-development-setup)
   - [Install Node.js](#install-nodejs)
   - [Clone and Install](#clone-and-install)
   - [Configure .env](#configure-env)
   - [Run the Server](#run-the-server)
   - [Set Up Telegram Webhook with ngrok](#set-up-telegram-webhook-with-ngrok)
6. [Vercel Deployment](#vercel-deployment)
   - [Step 1 — Install Vercel CLI](#step-1--install-vercel-cli)
   - [Step 2 — Deploy](#step-2--deploy)
   - [Step 3 — Set Environment Variables](#step-3--set-environment-variables)
   - [Step 4 — One-Time Setup](#step-4--one-time-setup)
   - [vercel.json Explained](#verceljson-explained)
   - [Vercel Timeout Limitation](#vercel-timeout-limitation)
7. [VPS / Any Server Deployment](#vps--any-server-deployment)
8. [One-Time Setup Calls](#one-time-setup-calls)
9. [Security Configuration](#security-configuration)
   - [TELEGRAM_WEBHOOK_SECRET](#telegram_webhook_secret)
   - [ADMIN_SECRET](#admin_secret)
10. [Web UI — Complete Guide](#web-ui--complete-guide)
    - [Upload Page](#upload-page)
    - [Uploading Files](#uploading-files)
    - [Progress Bar Stages](#progress-bar-stages)
    - [The Downloaded Quiz File](#the-downloaded-quiz-file)
11. [Telegram Bot — Complete Guide](#telegram-bot--complete-guide)
    - [Setting Up the Webhook](#setting-up-the-webhook)
    - [Commands Reference](#commands-reference)
    - [Uploading a Quiz File](#uploading-a-quiz-file)
    - [Progress Messages](#progress-messages)
    - [Opt-Out of Saving](#opt-out-of-saving)
    - [Downloading from the Bank](#downloading-from-the-bank)
12. [API Reference](#api-reference)
13. [Question JSON Format](#question-json-format)
14. [AI Topic Normalization](#ai-topic-normalization)
15. [GitHub Question Bank](#github-question-bank)
16. [Turso Database](#turso-database)
17. [Differences from the Cloudflare Worker](#differences-from-the-cloudflare-worker)
18. [Troubleshooting](#troubleshooting)

---

## Overview

This Express application provides the exact same API surface, UI, and behavior as the Cloudflare Worker v5.0 — just on Node.js. Deploy it anywhere Node.js can run.

| Feature | Status |
|---|---|
| Web UI (upload page, progress bar, quiz download) | ✅ |
| Telegram bot (file upload, commands, progress) | ✅ |
| AI topic normalization (OpenRouter) | ✅ |
| GitHub question bank (save, deduplicate, browse, download) | ✅ |
| Turso DB analytics | ✅ |
| HTTP security headers | ✅ |
| Telegram webhook signature verification | ✅ |
| Admin-guarded `/setup` and `/initdb` | ✅ |
| File upload size limit (10 MB) | ✅ |
| 500-question cap | ✅ |

---

## Project Structure

```
quiz-generator-express/
│
├── server.js               Main Express app — all HTTP routes
│
├── src/
│   ├── utils.js            escHtml, validateQuestions, base64 helpers
│   ├── db.js               Turso libSQL (initDb, trackGeneration, getStats, getUserStats)
│   ├── github.js           GitHub REST API (saveQuestions, listTopics, downloadTopic)
│   ├── ai.js               OpenRouter AI normalization (25s timeout)
│   ├── telegram.js         tgSend, tgSendDocument, tgDownloadFile
│   ├── quiz-html.js        generateHtml — self-contained quiz HTML builder
│   └── upload-page.js      UPLOAD_PAGE — web UI HTML template
│
├── .env.example            Template for all environment variables
├── .gitignore              Excludes node_modules, .env, downloaded quiz files
├── package.json            express, multer, dotenv dependencies
├── vercel.json             Vercel routing + function timeout config
└── README.md               This file
```

### Module responsibilities

| File | Responsibility |
|---|---|
| `server.js` | Express app, route definitions, multer config, request validation, fire-and-forget Telegram background tasks |
| `src/utils.js` | Pure utilities: HTML escaping, question validation, base64 encoding/decoding |
| `src/db.js` | All Turso (libSQL) database calls over HTTP API |
| `src/github.js` | GitHub REST API: list topics, save questions, download topic questions |
| `src/ai.js` | OpenRouter AI call with 25-second timeout and dictionary-keyed response |
| `src/telegram.js` | Telegram Bot API: send messages, send files, download uploaded files |
| `src/quiz-html.js` | HTML/CSS/JS template that generates a self-contained offline quiz |
| `src/upload-page.js` | Upload page web UI (drag-drop zone, progress bar, file list, stats cards) |

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Node.js** | 18 or later | Required for built-in `fetch`, `AbortController`, `FormData`, `Blob` |
| **npm** or **pnpm** | Any modern version | For installing dependencies |

**External services** (all optional at startup — disable features you don't need):

| Service | Feature | How to get credentials |
|---|---|---|
| Telegram | Bot | [@BotFather](https://t.me/BotFather) → `/newbot` |
| GitHub | Question bank | GitHub → Settings → Developer settings → Fine-grained PAT → `Contents: Read & Write` |
| Turso | Analytics | [turso.tech](https://turso.tech) → Create DB → Show credentials |
| OpenRouter | AI normalization | [openrouter.ai](https://openrouter.ai) → Keys |
| ngrok | Local Telegram webhook tunnel | [ngrok.com](https://ngrok.com) — free tier works |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

```bash
cp .env.example .env
```

### All variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `PORT` | No | HTTP port (default: 3000) | `3000` |
| `TELEGRAM_TOKEN` | For bot | Bot token from BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_WEBHOOK_SECRET` | Recommended | Random string verifying webhook authenticity | `a8f3c2e71b94d056...` |
| `OPENROUTER_API_KEY` | For AI | OpenRouter API key | `sk-or-v1-xxx...` |
| `GITHUB_TOKEN` | For bank | GitHub PAT (also accepts `GITHUB_PERSONAL_ACCESS_TOKEN`) | `github_pat_xxx...` |
| `GITHUB_REPO` | For bank | `owner/name` format | `yourname/quiz-questions` |
| `GITHUB_BRANCH` | No | Branch name (default: `main`) | `main` |
| `TURSO_DB_URL` | For analytics | Turso HTTPS URL | `https://mydb-org.turso.io` |
| `TURSO_AUTH_TOKEN` | For analytics | Turso auth token | `eyJhbGci...` |
| `ADMIN_SECRET` | Recommended | Guards `/setup` and `/initdb` | `my-admin-password` |
| `WORKER_ORIGIN` | No | Your server URL sent as `HTTP-Referer` to OpenRouter | `https://my-quiz-app.vercel.app` |

### Startup log

When the server starts, it prints which services are configured:

```
✅ Quiz Generator running at http://localhost:3000
   GitHub bank : ✅ yourname/quiz-questions
   Turso DB    : ✅ configured
   OpenRouter  : ✅ configured
   Telegram    : ✅ configured
```

Missing variables show `⚠️  not configured`. The server still starts and all other features work.

---

## Local Development Setup

### Install Node.js

**Windows / macOS:**
Download the LTS installer from [nodejs.org](https://nodejs.org). Run it.

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

Verify:
```bash
node --version   # must print v18.x or higher
npm --version
```

### Clone and Install

```bash
# Navigate to the project folder
cd quiz-generator-express

# Install dependencies
npm install
```

This installs:
- `express` — HTTP server framework
- `multer` — multipart form file upload handler (v2.x — no known vulnerabilities)
- `dotenv` — loads `.env` into `process.env`

### Configure .env

```bash
cp .env.example .env
```

Open `.env` in any text editor. Fill in at minimum `OPENROUTER_API_KEY` if you want AI features. Everything else can stay empty — the server starts fine.

**Full `.env` example:**
```ini
PORT=3000

# Telegram Bot
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_WEBHOOK_SECRET=a8f3c2e71b94d056f8a2c7e3d1b94a57

# AI
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# GitHub Question Bank
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=yourname/quiz-questions
GITHUB_BRANCH=main

# Turso Analytics
TURSO_DB_URL=https://mydb-myorg.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3...

# Admin protection for /setup and /initdb
ADMIN_SECRET=my-secret-admin-password

# Your public URL — used as HTTP-Referer for OpenRouter
WORKER_ORIGIN=http://localhost:3000
```

### Run the Server

```bash
npm start
```

Open `http://localhost:3000` to see the upload page.

For auto-restart during development:
```bash
npm install -g nodemon
nodemon server.js
```

### Set Up Telegram Webhook with ngrok

Telegram needs a **public HTTPS URL** to deliver bot events. On a local machine, use ngrok to create a secure tunnel.

**Step 1 — Install ngrok:**

```bash
# macOS
brew install ngrok

# Windows
choco install ngrok

# Linux
snap install ngrok
```

Or download directly from [ngrok.com/download](https://ngrok.com/download).

**Step 2 — Authenticate** (free account required):

```bash
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

Get your token at [dashboard.ngrok.com](https://dashboard.ngrok.com).

**Step 3 — Start the tunnel:**

```bash
ngrok http 3000
```

ngrok shows your public URL:
```
Forwarding   https://a1b2c3d4.ngrok-free.app -> http://localhost:3000
```

**Step 4 — Register the Telegram webhook:**

```bash
curl "https://a1b2c3d4.ngrok-free.app/setup"
# or with ADMIN_SECRET:
curl "https://a1b2c3d4.ngrok-free.app/setup?secret=YOUR_ADMIN_SECRET"
```

Expected response:
```json
{
  "ok": true,
  "webhook": "https://a1b2c3d4.ngrok-free.app/telegram",
  "secretRegistered": true,
  "adminProtected": true,
  "warnings": []
}
```

**Step 5 — Test:** Send any message to your Telegram bot. You'll see the request arrive in the ngrok console.

> **Every time ngrok restarts, the URL changes.** You must call `/setup` again with the new URL. Use ngrok's paid "reserved domain" feature for a persistent URL.

---

## Vercel Deployment

Vercel is the recommended cloud host — automatic HTTPS, no server management, free tier available.

### Step 1 — Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2 — Deploy

From inside the `quiz-generator-express/` folder:

```bash
vercel
```

Follow the prompts:
- **Set up and deploy** → Yes
- **Which scope?** → Your Vercel account
- **Link to existing project?** → No (first time)
- **Project name** → e.g. `quiz-generator`
- **Directory** → `.` (current folder)
- **Override settings?** → No

After completion:
```
✅  Production: https://quiz-generator-yourname.vercel.app
```

### Step 3 — Set Environment Variables

**Method A — Vercel Dashboard (recommended):**

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Open your project → **Settings** → **Environment Variables**
3. Add each variable (Name, Value, check all environments: Production / Preview / Development)
4. Click the 🔒 lock icon on sensitive values to encrypt them
5. Click **Save**
6. Redeploy to apply: `vercel --prod`

**Method B — Vercel CLI:**

```bash
vercel env add TELEGRAM_TOKEN
vercel env add TELEGRAM_WEBHOOK_SECRET
vercel env add OPENROUTER_API_KEY
vercel env add GITHUB_TOKEN
vercel env add GITHUB_REPO
vercel env add GITHUB_BRANCH
vercel env add TURSO_DB_URL
vercel env add TURSO_AUTH_TOKEN
vercel env add ADMIN_SECRET
vercel env add WORKER_ORIGIN

# Apply
vercel --prod
```

Each `vercel env add` command prompts for the value — it's not shown in your terminal.

### Step 4 — One-Time Setup

After the deployment with environment variables is live:

```bash
# Initialize Turso tables (if using Turso)
curl "https://your-app.vercel.app/initdb?secret=YOUR_ADMIN_SECRET"

# Register Telegram webhook
curl "https://your-app.vercel.app/setup?secret=YOUR_ADMIN_SECRET"
```

Set `WORKER_ORIGIN` to your actual Vercel URL:
```
WORKER_ORIGIN=https://quiz-generator-yourname.vercel.app
```

### vercel.json Explained

```json
{
  "version": 2,
  "builds": [{ "src": "server.js", "use": "@vercel/node" }],
  "routes": [{ "src": "/(.*)", "dest": "/server.js" }],
  "functions": {
    "server.js": {
      "maxDuration": 60
    }
  }
}
```

| Setting | What it does |
|---|---|
| `"use": "@vercel/node"` | Runs `server.js` as a serverless Node.js function |
| `"routes": [...]` | Routes all paths (`/`, `/generate`, `/telegram`, etc.) to `server.js` |
| `"maxDuration": 60` | Extends function timeout from the default 10s to 60s |

### Vercel Timeout Limitation

| Plan | Max timeout with `maxDuration: 60` |
|---|---|
| Hobby (free) | 60 seconds |
| Pro | Up to 300 seconds |

The AI normalization step (OpenRouter `gpt-oss-120b:free`) averages 15–25 seconds. On Hobby, this usually fits within 60s — but the free model can occasionally take longer.

**When you hit a Vercel timeout:**
- Your questions are valid — re-upload with "Save to Bank" **unchecked** for instant generation (no AI, no GitHub)
- Pre-normalize your JSON: match `subject`/`topic` exactly to names already in your bank — the AI bypass detects this and skips the slow call entirely

---

## VPS / Any Server Deployment

For DigitalOcean, AWS EC2, Render, Railway, etc.:

```bash
# Copy project to server (or clone your repo)
cd quiz-generator-express
npm install --production

# Set environment variables (or use a .env file)
export TELEGRAM_TOKEN="..."
export OPENROUTER_API_KEY="..."
# ... etc.

# Start with pm2 for production (auto-restart on crash + reboot)
npm install -g pm2
pm2 start server.js --name quiz-generator
pm2 save
pm2 startup   # follow the printed instruction to enable auto-start on reboot

# Register webhook (use your actual public domain)
curl "https://yourdomain.com/setup?secret=YOUR_ADMIN_SECRET"
```

**Sample Nginx reverse proxy** (port 80/443 → your app on 3000):

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        # Extend timeout for AI calls (25s) + GitHub calls (10s)
        proxy_read_timeout 90s;
    }
}
```

Free TLS via Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## One-Time Setup Calls

Run these once after your first deployment.

### Initialize the database

Creates Turso tables (`quiz_generations`, `telegram_users`). Uses `CREATE TABLE IF NOT EXISTS` — safe to re-run.

```
GET /initdb
```

With `ADMIN_SECRET`:
```bash
# Query string
curl "https://your-app/initdb?secret=YOUR_ADMIN_SECRET"

# Or header (more secure)
curl -H "X-Admin-Secret: YOUR_ADMIN_SECRET" https://your-app/initdb
```

Expected response:
```json
{ "ok": true, "message": "Tables created (or already exist)." }
```

### Register the Telegram webhook

Tells Telegram to POST all bot events to your server's `/telegram` endpoint.

```bash
curl "https://your-app/setup?secret=YOUR_ADMIN_SECRET"
```

Expected response (all security features active):
```json
{
  "ok": true,
  "webhook": "https://your-app/telegram",
  "secretRegistered": true,
  "adminProtected": true,
  "warnings": []
}
```

**Re-run `/setup` whenever:**
- Your public URL changes (new ngrok session, redeployment to new domain)
- You add or rotate `TELEGRAM_WEBHOOK_SECRET`
- The bot stops receiving messages

---

## Security Configuration

### TELEGRAM_WEBHOOK_SECRET

Prevents spoofed webhook calls — ensures only Telegram can trigger `/telegram`.

**Generate a secret:**
```bash
# macOS / Linux
openssl rand -hex 32

# Any 32+ character random string works
```

**Add to `.env` or Vercel env vars:**
```ini
TELEGRAM_WEBHOOK_SECRET=a8f3c2e71b94d056f8a2c7e3d1b94a57f2c8e3d7a1b9c4f2e8a3c7d1b5f94e2
```

**Re-register the webhook:**
```bash
curl "https://your-app/setup?secret=YOUR_ADMIN_SECRET"
```

Once registered, Telegram sends `X-Telegram-Bot-Api-Secret-Token: <your_secret>` with every request. Your server rejects any request missing it with HTTP 403.

### ADMIN_SECRET

Protects `/setup` and `/initdb` from unauthorized public calls.

**Add to `.env` or Vercel env vars:**
```ini
ADMIN_SECRET=my-secret-admin-password
```

**Calling protected endpoints:**
```bash
# Query string
GET /setup?secret=my-secret-admin-password
GET /initdb?secret=my-secret-admin-password

# Header (not logged in web server access logs — more secure)
curl -H "X-Admin-Secret: my-secret-admin-password" https://your-app/setup
```

---

## Web UI — Complete Guide

### Upload Page

Open your server URL in any browser.

```
┌───────────────────────────────────────────────────────────────────────┐
│  📚 Quiz Generator                                [Question Bank ▾]   │
│───────────────────────────────────────────────────────────────────────│
│                                                                       │
│  Upload one or more JSON quiz files. Merge and generate a            │
│  self-contained bilingual HTML quiz.                                 │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                                                                 │  │
│  │              📂  Drop files here                               │  │
│  │           or click to browse                                   │  │
│  │         Supports .json and .txt files                         │  │
│  │                                                                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  physics_optics.json          45 questions              [✕ Remove]   │
│  biology_cells.json           32 questions              [✕ Remove]   │
│  Total: 77 questions across 2 files                                   │
│                                                                       │
│  ☑ Save to Question Bank                                             │
│                                                                       │
│  [⬇️  Generate & Download Quiz HTML]                                  │
│                                                                       │
│  ████████████░░░░  62%  AI normalizing topics…                       │
│                                                                       │
├───────────────────────────────────────────────────────────────────────┤
│  📊 Platform Stats                    📚 Question Bank               │
│  143 quizzes · 4,821 questions        3 subjects · 36 topics         │
└───────────────────────────────────────────────────────────────────────┘
```

### Uploading Files

**Drag and drop:** Drag one or more `.json` files onto the dashed zone.

**Click to browse:** Click anywhere in the zone — a file picker opens. Select one or multiple files.

- Each file shows its name and question count
- Duplicate filenames are ignored
- Remove a file with ✕
- Multiple files are merged into one quiz

### Progress Bar Stages

**Saving enabled** (5 stages, ~20–30s total including AI):

| Stage | % | What's happening |
|---|---|---|
| Reading file | 15% | JSON parsed in browser |
| Checking bank | 35% | GitHub repo structure fetched |
| AI normalizing | 62% | OpenRouter AI normalizing topic names (15–25s actual) |
| Building quiz | 82% | Self-contained HTML generated |
| Almost there | 95% | Packaging for download |
| Done | 100% | Download triggers automatically |

> The bar animation pauses at 62% while waiting for the AI response — this is expected. The file downloads the moment the server replies.

**Saving disabled** (3 stages, ~2s):

| Stage | % | What's happening |
|---|---|---|
| Reading file | 15% | JSON parsed |
| Building quiz | 57% | HTML generated immediately |
| Almost there | 95% | Packaging |
| Done | 100% | Download |

The AI stage label is hidden entirely when saving is off.

### The Downloaded Quiz File

The browser downloads a `.html` file — fully self-contained and offline-capable. Double-click to open in any browser.

```
┌──────────────────────────────────────────────────────────────┐
│ 📚 [editable title]       Home  Quiz  Review  Stats          │
│                                           🌙  🔀  ⭐          │
├──────────────────────────────────────────────────────────────┤
│               Question  3 / 45                              │
│                                                              │
│  What is the refractive index of glass?                     │
│  काँच का अपवर्तनांक क्या है?                               │
│                                                              │
│  ◉  1.5          ○  1.0                                     │
│  ○  2.0          ○  2.5                                     │
│                                                              │
│  ✅  Correct! Glass has n ≈ 1.5                             │
│                                                              │
│  [← Prev]    Flagged: 2    Remaining: 31    [Next →]        │
├──────────────────────────────────────────────────────────────┤
│  Score  ████████████░░░░░  14/22  64%                       │
└──────────────────────────────────────────────────────────────┘
```

| Feature | Control |
|---|---|
| Dark mode | 🌙 button |
| Scramble option order | 🔀 button |
| Flag question for review | ⭐ button |
| Navigate questions | `←` / `→` keys or Prev/Next buttons |
| Select answer | `1` `2` `3` `4` keys |
| Edit quiz title | Click the title in the nav bar |
| Review flagged questions | Click the **Review** tab |
| Score breakdown | Click the **Stats** tab |

---

## Telegram Bot — Complete Guide

### Setting Up the Webhook

Telegram needs a **public HTTPS URL** to send bot events to your server.

| Where you're running | How to get a public URL |
|---|---|
| Vercel | Your deployment URL is already public |
| VPS with domain | Your domain URL |
| Local machine | Use ngrok (see [ngrok setup](#set-up-telegram-webhook-with-ngrok)) |

After you have a public URL, call `/setup` once.

### Commands Reference

| Command | Description |
|---|---|
| `/start` | Welcome message and quick guide |
| `/help` | Full command reference |
| `/topics` | Lists every subject and topic in the question bank |
| `/download Subject \| Topic` | Generates and sends a quiz for that topic |
| `/mystats` | Your personal quiz generation count (Turso required) |
| `/globalstats` | Platform-wide totals (Turso required) |

### Uploading a Quiz File

1. Tap 📎 → **File** (not Photo — Photo compresses the file)
2. Navigate to your `.json` or `.txt` quiz file
3. Optional: add a caption (type `nosave` to skip saving)
4. Tap **Send**

The bot sends back progress updates, then delivers the complete quiz `.html` file.

**Limits:**
- Max file size: 20 MB (Telegram Bot API hard limit)
- Max questions per upload: 500
- Supported formats: `.json`, `.txt` (text file containing valid JSON)

### Progress Messages

The bot sends one message and edits it in-place through stages:

```
⏳ Reading file… [▓░░░░] 20%
🔍 Checking question bank… [▓▓░░░] 40%
🤖 AI normalizing topics… [▓▓▓░░] 60%
⚙️ Building quiz… [▓▓▓▓░] 80%
✅ Done! Quiz delivered. [▓▓▓▓▓] 100%
```

Stages 2 and 3 are skipped when `nosave` is in the caption or the question bank isn't configured.

If delivery fails:
```
❌ Quiz built but delivery failed: [Telegram error description]
```

> **How the Express version handles Telegram:** Unlike the Cloudflare Worker which uses `ctx.waitUntil()`, Express responds to Telegram with HTTP 200 immediately, then processes the file and sends updates as a background `Promise`. The Telegram message edits (progress updates) work exactly the same way — only the internal mechanism differs.

### Opt-Out of Saving

Add `nosave` or `#nosave` anywhere in the file caption:

```
draft questions — do not save  #nosave
```

The quiz is still generated and sent. GitHub and AI are skipped entirely.

### Downloading from the Bank

```
/download Physics | Optics
/download Biology | Cell Biology
/download गणित | बीजगणित
/download Chemistry | Periodic Table
```

Use `/topics` first to see exact subject and topic names.

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | None | Upload page HTML |
| `POST` | `/generate` | None | Generate quiz HTML from uploaded file |
| `POST` | `/telegram` | Webhook secret | Telegram webhook event receiver |
| `GET` | `/setup` | ADMIN_SECRET | Register Telegram webhook |
| `GET` | `/initdb` | ADMIN_SECRET | Create Turso DB tables |
| `GET` | `/dbstats` | None | JSON analytics counters |
| `GET` | `/api/browse` | None | JSON map of all subjects and topics |
| `GET` | `/api/download?subject=X&topic=Y` | None | JSON array of questions for a topic |

### POST /generate — Full Details

**Request:** `multipart/form-data`

| Field | Required | Description |
|---|---|---|
| `file` | Yes | `.json` quiz file — max 10 MB |
| `title` | No | Quiz title shown in the HTML |
| `outname` | No | Output HTML filename for the download |
| `saveToGithub` | No | `"true"` (default) or `"false"` |

**Responses:**

| Status | Body | Meaning |
|---|---|---|
| `200` | `text/html` | Quiz file download |
| `400` | `{ "error": "No file uploaded." }` | `file` field missing |
| `400` | `{ "error": "Invalid JSON: ..." }` | File content is not valid JSON |
| `400` | `{ "error": "JSON must be a non-empty array." }` | Wrong JSON shape |
| `400` | `{ "error": "No valid question objects found." }` | All items failed validation |
| `400` | `{ "error": "Too many questions. Maximum 500 per upload." }` | Over the cap |
| `413` | `{ "error": "Request too large. Maximum 10 MB per upload." }` | File too large |

### Calling admin-protected endpoints

```bash
# Query string
GET /setup?secret=YOUR_ADMIN_SECRET
GET /initdb?secret=YOUR_ADMIN_SECRET

# Header — recommended (not logged in Nginx / Vercel access logs)
curl -H "X-Admin-Secret: YOUR_ADMIN_SECRET" https://your-app/setup
curl -H "X-Admin-Secret: YOUR_ADMIN_SECRET" https://your-app/initdb
```

---

## Question JSON Format

```json
[
  {
    "subject": "Physics",
    "topic": "Optics",
    "qEnglish": "What is the refractive index of glass?",
    "qHindi": "काँच का अपवर्तनांक क्या है?",
    "optionsEnglish": ["1.0", "1.5", "2.0", "2.5"],
    "optionsHindi":   ["1.0", "1.5", "2.0", "2.5"],
    "correctIndex": 1,
    "explanation": "Glass has n ≈ 1.5, slowing light to about 2/3 of its vacuum speed."
  },
  {
    "subject": "Biology",
    "topic": "Cell Biology",
    "qEnglish": "What is the powerhouse of the cell?",
    "qHindi": "कोशिका का पावरहाउस क्या है?",
    "optionsEnglish": ["Nucleus", "Mitochondria", "Ribosome", "Golgi Apparatus"],
    "optionsHindi":   ["नाभिक", "माइटोकॉन्ड्रिया", "राइबोसोम", "गॉल्जी उपकरण"],
    "correctIndex": 1
  }
]
```

### Field Reference

| Field | Required | Description |
|---|---|---|
| `qEnglish` | At least one of `qEnglish` / `qHindi` | Question text in English |
| `qHindi` | At least one of `qEnglish` / `qHindi` | Question text in Hindi (Devanagari) |
| `optionsEnglish` | Yes | 2–6 answer choices in English |
| `optionsHindi` | Yes | 2–6 answer choices in Hindi |
| `correctIndex` | Yes | Zero-based index of the correct answer |
| `subject` | No | Subject name — defaults to `"General"` |
| `topic` | No | Topic name — defaults to `"General"` |
| `explanation` | No | Shown to the user after they submit an answer |

### Validation

- Root must be a non-empty JSON array
- Each item must be a non-null object with at least one recognizable question text field
- Items failing validation are silently dropped — the rest of the upload continues
- Maximum 500 valid items after filtering

---

## AI Topic Normalization

OpenRouter (`gpt-oss-120b:free`) corrects abbreviated or misspelled subject/topic names before saving to the bank.

| Uploaded | Normalized |
|---|---|
| `Phy / optics basics` | `Physics / Optics` |
| `Bio / Cell Bio` | `Biology / Cell Biology` |
| `chem / periodic tbl` | `Chemistry / Periodic Table` |
| `physics / OPTICS` | `Physics / Optics` |
| `Physics / Optics` | `Physics / Optics` (bypass — no AI call) |

**Zero-latency bypass:** If all subject/topic pairs already match the bank exactly, the AI call is skipped entirely.

**25-second timeout:** If OpenRouter doesn't respond in time, original names are kept and the quiz is still generated and saved.

---

## GitHub Question Bank

Questions are saved to your GitHub repo as JSON files organized by subject and topic:

```
your-repo/
└── questions/
    ├── Physics/
    │   ├── Optics.json
    │   └── Mechanics.json
    ├── Biology/
    │   └── Cell Biology.json
    └── गणित/
        └── बीजगणित.json
```

Each file is a JSON array of question objects matching the format above.

**Deduplication:** Questions already in the bank (matched by `qEnglish + qHindi` text) are never re-added. If nothing new is found, no GitHub commit is made.

**GitHub API timeout:** All GitHub calls use a 10-second `AbortController`. Slow responses abort gracefully.

**Commit messages:**
```
Add 12 question(s) to Physics/Optics [web]
Add 5 question(s) to Biology/Cell Biology [telegram]
```

---

## Turso Database

Initialize once with `GET /initdb`. Creates two tables:

```sql
CREATE TABLE quiz_generations (
  id               INTEGER  PRIMARY KEY AUTOINCREMENT,
  source           TEXT,      -- 'web' or 'telegram'
  title            TEXT,
  questions_count  INTEGER,
  telegram_chat_id TEXT,
  telegram_username TEXT,
  created_at       TEXT  DEFAULT (datetime('now'))
);

CREATE TABLE telegram_users (
  chat_id       TEXT  PRIMARY KEY,
  username      TEXT,
  first_name    TEXT,
  total_quizzes INTEGER  DEFAULT 0,
  first_seen    TEXT  DEFAULT (datetime('now')),
  last_seen     TEXT  DEFAULT (datetime('now'))
);
```

`GET /dbstats` returns:
```json
{
  "total": 143,
  "totalQuestions": 4821,
  "tgCount": 112,
  "webCount": 31,
  "telegramUsers": 28
}
```

---

## Differences from the Cloudflare Worker

| Aspect | Cloudflare Worker (v5.0) | This Express app |
|---|---|---|
| **Runtime** | V8 isolate (Web API surface) | Node.js 18+ |
| **Background tasks** | `ctx.waitUntil()` | Fire-and-forget `Promise` |
| **File upload parsing** | `request.formData()` (Web API) | `multer` middleware |
| **Config** | `env.VAR_NAME` (Workers bindings) | `process.env.VAR_NAME` (dotenv) |
| **Deployment** | Cloudflare Workers (global CDN edge) | Vercel, VPS, or local |
| **Execution timeout** | 30s wall-clock on paid plan | 60s on Vercel Hobby |
| **Cold start** | Zero — instant everywhere | ~200ms on Vercel serverless |
| **Local dev** | `wrangler dev` | `node server.js` |
| **AI timeout behavior** | Same 25s abort + fallback | Same 25s abort + fallback |
| **GitHub timeout** | Same 10s abort | Same 10s abort |
| **Security headers** | Applied by `applySecurityHeaders()` | Applied by Express middleware |
| **Webhook auth** | X-Telegram-Bot-Api-Secret-Token | Same — identical implementation |

---

## Troubleshooting

### Server won't start — "Cannot use import statement"

Node.js is below version 18, or the package type is not set to `module`.

```bash
node --version   # must be v18+
```

Check `package.json` contains `"type": "module"`.

### The bot doesn't respond in Telegram

1. Make sure the server is publicly reachable (not just `localhost`)
2. Call `/setup` with your current public URL
3. ngrok users: restart ngrok and call `/setup` again — the URL changes every restart
4. Verify `TELEGRAM_TOKEN` is correct

### `/telegram` returns 403

A client called the endpoint without a valid webhook secret header. If you're seeing this from Telegram itself (not a test), `TELEGRAM_WEBHOOK_SECRET` changed after the last `/setup` call — run `/setup` again.

### `/setup` or `/initdb` return 403

`ADMIN_SECRET` is configured. Call with:
```
/setup?secret=YOUR_ADMIN_SECRET
```

### POST /generate returns 413

The uploaded file exceeds 10 MB. Split the question set into smaller files.

### POST /generate returns "Too many questions"

The file has over 500 valid questions. Split into multiple uploads.

### AI normalization times out on Vercel

The free tier of `gpt-oss-120b:free` on OpenRouter can take 20–30 seconds on busy periods. Options:
1. Uncheck "Save to Bank" — quiz generates in under 2 seconds
2. Pre-normalize your JSON to use exact bank topic names — AI bypass skips the slow call
3. Use a faster paid model in `src/ai.js`

### Questions not saving to GitHub

1. `GITHUB_TOKEN` must have `Contents: Read and Write` permission on the specific repo
2. `GITHUB_REPO` must be `owner/repo` — not a full URL (`github.com/...`)
3. `GITHUB_BRANCH` must exist in the repository
4. Check server logs for `GitHub save error` lines

### Quiz HTML file is blank or truncated

The Vercel function may have timed out before the HTML was fully written. Check Vercel's function logs in the dashboard. Re-upload without saving for an instant result.

### `/dbstats` returns 503

Turso is not configured. Set `TURSO_DB_URL` and `TURSO_AUTH_TOKEN`, then run `/initdb`.

### Progress bar sticks at 62%

The AI model is being called and taking its time (15–25s is normal). The bar animation pauses visually — this is expected. The download triggers the moment the server responds. If nothing happens after 30 seconds on Vercel, the function likely timed out — try again with saving disabled.
