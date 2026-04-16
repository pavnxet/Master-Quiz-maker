# Quiz Generator — Cloudflare Worker

A self-contained Cloudflare Worker that turns JSON question banks into interactive, bilingual (English + Hindi) HTML quizzes. It integrates a web upload interface, a Telegram bot, a Turso database for analytics, and a GitHub repository as a persistent question store.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Endpoints](#endpoints)
5. [Environment Variables](#environment-variables)
6. [One-Time Setup](#one-time-setup)
7. [Question JSON Format](#question-json-format)
8. [Telegram Bot Commands](#telegram-bot-commands)
9. [Generated Quiz Features](#generated-quiz-features)
10. [GitHub Question Bank](#github-question-bank)
11. [Turso Database Schema](#turso-database-schema)
12. [Known Fixes & Improvements](#known-fixes--improvements)
13. [Deployment](#deployment)

---

## Overview

This single Worker file (`worker.js`) does everything:

- Serves a **drag-and-drop web UI** where users upload one or more JSON files and download a self-contained HTML quiz.
- Runs a **Telegram bot webhook** that accepts `.json` files and returns the quiz as a document, and supports commands to browse and download from the question bank.
- Writes every generated quiz's metadata to a **Turso (libSQL) database** for platform analytics.
- Saves every new question (deduplicated) to a **GitHub repository** as a structured question bank, organised by subject and topic.

The output is a **single, fully offline-capable HTML file** — no server required after download.

---

## Architecture

```
Browser / Telegram
       │
       ▼
Cloudflare Worker (worker.js)
       │
       ├── GET  /              Upload UI (UPLOAD_PAGE HTML)
       ├── POST /generate      Parse JSON → generateHtml() → return .html file
       ├── GET  /dbstats       Turso aggregate stats → JSON
       ├── GET  /api/browse    GitHub tree listing → JSON
       ├── GET  /api/download  GitHub questions → generateHtml() → .html file
       ├── POST /telegram      Telegram webhook handler
       ├── GET  /setup         Register Telegram webhook (run once)
       └── GET  /initdb        Create Turso tables (run once)
              │
              ├── Turso DB (libSQL HTTP)   — analytics & user stats
              └── GitHub API               — question bank (questions/<Subject>/<Topic>.json)
```

---

## Features

### Web Interface (`GET /`)
- Drag-and-drop or click-to-browse file picker.
- Accepts multiple `.json` files that are **merged** into a single quiz before generation.
- Shows question counts per file as soon as a file is selected.
- Displays live **platform stats** pulled from Turso (if configured).
- Shows the **Question Bank** card with all stored subjects/topics from GitHub (hidden automatically when GitHub is not configured).
- Dark mode, persisted via `localStorage`.

### Quiz Generator (`POST /generate`)
- Parses a JSON array of question objects.
- Injects questions as a `<script type="application/json">` data island — completely safe against `</script>` appearing inside question text.
- Returns a self-contained, download-ready HTML file.
- Fires-and-forgets two background tasks via `ctx.waitUntil`:
  - Writing generation metadata to Turso.
  - Saving new questions to GitHub.

### Telegram Bot (`POST /telegram`)
- Accepts `.json` or `.txt` files via direct message.
- Returns the generated quiz as a document (HTML file).
- Handles channel posts as well as personal messages safely.
- Supports commands: `/start`, `/help`, `/mystats`, `/globalstats`, `/topics`, `/download`.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Upload UI |
| `POST` | `/generate` | Generate quiz HTML from uploaded JSON |
| `GET` | `/dbstats` | Aggregate stats from Turso (503 if unconfigured) |
| `GET` | `/api/browse` | List all subjects/topics from GitHub (503 if unconfigured) |
| `GET` | `/api/download?subject=X&topic=Y` | Download quiz for a specific topic from GitHub |
| `POST` | `/telegram` | Telegram webhook receiver |
| `GET` | `/setup` | Register the Telegram webhook (run once) |
| `GET` | `/initdb` | Create Turso tables (run once) |
| `OPTIONS` | `*` | CORS preflight |

---

## Environment Variables

Set these in **Cloudflare Dashboard → Workers → Your Worker → Settings → Variables**.

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_TOKEN` | For Telegram bot | Bot token from [@BotFather](https://t.me/BotFather), e.g. `123456:ABC-DEF…` |
| `TURSO_DB_URL` | For analytics | Your Turso DB URL, e.g. `https://mydb-myorg.turso.io` or `libsql://…` |
| `TURSO_AUTH_TOKEN` | For analytics | Turso database auth token |
| `GITHUB_TOKEN` | For question bank | GitHub personal access token with `repo` scope (also accepted as `GITHUB_PERSONAL_ACCESS_TOKEN`) |
| `GITHUB_REPO` | For question bank | Repository in `owner/repo` format, e.g. `yourname/quiz-questions` |
| `GITHUB_BRANCH` | Optional | Branch to read/write questions (defaults to `main`) |

All integrations are **optional and independent**. The Worker degrades gracefully: if Turso is not configured, stats endpoints return 503 and the UI hides those sections. If GitHub is not configured, the question bank card is hidden.

---

## One-Time Setup

### 1. Create Turso tables

Visit `GET /initdb` once after deploying (or whenever you create a fresh database). This creates the two tables used for analytics. It is idempotent — safe to call multiple times.

### 2. Register the Telegram webhook

Visit `GET /setup` once after deploying. This tells Telegram where to deliver updates. The response confirms the registered webhook URL and whether the token is valid.

---

## Question JSON Format

Questions must be provided as a **JSON array**. Each element is an object with the fields below.

### Minimum required fields

```json
[
  {
    "qEnglish": "What is the speed of light?",
    "optionsEnglish": ["3×10⁸ m/s", "3×10⁶ m/s", "3×10⁴ m/s", "3×10² m/s"],
    "correct": 0
  }
]
```

### Full bilingual example

```json
[
  {
    "qEnglish": "Which planet is closest to the Sun?",
    "qHindi": "सूर्य के सबसे निकट कौन सा ग्रह है?",
    "optionsEnglish": ["Mercury", "Venus", "Earth", "Mars"],
    "optionsHindi": ["बुध", "शुक्र", "पृथ्वी", "मंगल"],
    "correct": 0,
    "explanationEnglish": "Mercury is the closest planet to the Sun.",
    "explanationHindi": "बुध सूर्य के सबसे निकट ग्रह है।",
    "subject": "Science",
    "topic": "Solar System",
    "imageUrl": "https://example.com/mercury.jpg"
  }
]
```

### Field reference

| Field | Type | Description |
|-------|------|-------------|
| `qEnglish` | string | Question text in English |
| `qHindi` | string | Question text in Hindi (optional) |
| `optionsEnglish` | string[] | Answer options in English (up to 4) |
| `optionsHindi` | string[] | Answer options in Hindi (optional, must match order) |
| `correct` | number | Zero-based index of the correct option |
| `explanationEnglish` | string | Explanation shown after answering (optional) |
| `explanationHindi` | string | Hindi explanation (optional) |
| `subject` | string | Subject name — used for filtering and GitHub folder structure |
| `topic` | string | Topic name — used for filtering and GitHub file name |
| `imageUrl` | string | URL of an image shown above the question (optional) |

### Match-type questions

For "match the following" questions, add these extra fields instead of or alongside options:

```json
{
  "qEnglish": "Match Column I with Column II",
  "matchItemsEnglish": [
    ["A. Transparent", "i. Clear water"],
    ["B. Opaque",      "ii. Wood"],
    ["C. Translucent", "iii. Frosted glass"]
  ],
  "matchItemsHindi": [
    ["A. पारदर्शी", "i. साफ पानी"],
    ["B. अपारदर्शी", "ii. लकड़ी"],
    ["C. पारभासी", "iii. सैंडब्लास्टेड काँच"]
  ],
  "optionsEnglish": ["A-i, B-ii, C-iii", "A-ii, B-i, C-iii", "A-iii, B-ii, C-i", "A-i, B-iii, C-ii"],
  "correct": 0,
  "subject": "Science",
  "topic": "Light"
}
```

`matchItemsEnglish` can be:
- An array of `[col1, col2]` pairs (two-column table).
- An array of strings or a comma/newline-separated string (single-column list).
- An object with `col1`, `col2` arrays and optional `col1Label`/`col2Label` keys.

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` or `/help` | Welcome message with full instructions and JSON format |
| `/topics` | List all subjects and topics in the question bank |
| `/download Subject \| Topic` | Receive a ready-to-use quiz HTML for that topic |
| `/mystats` | Your personal quiz generation history (requires Turso) |
| `/globalstats` | Platform-wide totals — quizzes, questions, users (requires Turso) |
| *(send a `.json` or `.txt` file)* | Instantly receive the generated quiz as an HTML file |

---

## Generated Quiz Features

The HTML file produced by the Worker is entirely self-contained. Once downloaded it works with no internet connection.

### Quiz setup
- Filter questions by **subject** and **topic**.
- Set the number of questions.
- Choose timer mode: **60 seconds per question**, **custom timer**, or **no timer**.
- Choose question order: **random** or **sequential**.
- **Scramble options** — shuffles A/B/C/D order on each attempt to discourage memorisation.
- Configure a **custom marking scheme** (marks for correct, marks deducted for wrong).

### During the quiz
- Progress bar showing current position.
- Live countdown timer with colour-coded urgency (normal → warning → danger pulse).
- **Flag questions** (⭐) for review later.
- **Skip** questions (recorded as skipped, not wrong).
- **Finish early** at any point.
- Click any dot in the **question navigator** to jump directly to that question.
- Answers are revealed immediately on selection with colour-coded feedback and an explanation.
- Keyboard shortcuts:
  - `1`–`4` — select option
  - `←` / `→` — previous/next question
  - `S` — skip
  - `F` — finish early
  - `*` — toggle flag

### Results page
- Accuracy ring showing score percentage.
- Total marks scored vs maximum.
- Breakdown bars for correct, wrong, and skipped.
- Per-subject accuracy table.
- Copy results as plain text (for sharing).
- Print the review page.

### Review page
- Filter by: all, wrong, correct, skipped, flagged.
- Filter by subject.
- Each card shows the question (English + Hindi), all options (correct highlighted, user's wrong answer marked), and the full explanation.

### Stats page
- Cumulative stats across all sessions stored in `localStorage` (up to 50 sessions kept).
- Best score, average accuracy, total questions attempted.
- Per-subject accuracy across all sessions.
- Session history list.

### UI & accessibility
- Dark mode (auto-detected from system preference, toggleable, persisted).
- Fully responsive for mobile (down to 320 px).
- Print-friendly layout (`@media print` hides navigation and quiz controls).
- Editable quiz title in the navbar.

---

## GitHub Question Bank

When questions are submitted (via web or Telegram), the Worker automatically saves them to a GitHub repository with deduplication.

### File structure

```
questions/
  Physics/
    Optics.json
    Mechanics.json
  Biology/
    Cell Biology.json
    Genetics.json
```

### Deduplication logic

A question is considered a duplicate if both its English text and Hindi text match an existing entry (case-insensitive, whitespace-normalised). If only one language is present, that field alone is used as the key.

### Browse and download via the web UI

The Question Bank card on the upload page lists all stored subjects and topics. Clicking **Download** on any topic generates and downloads a quiz HTML for that topic instantly — no file upload needed.

---

## Turso Database Schema

Two tables are created by `GET /initdb`:

### `quiz_generations`

Tracks every quiz that was generated.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `source` | TEXT | `"web"` or `"telegram"` |
| `title` | TEXT | Quiz title |
| `questions_count` | INTEGER | Number of questions in the quiz |
| `telegram_chat_id` | TEXT | Telegram chat ID (NULL for web) |
| `telegram_username` | TEXT | Telegram username (NULL for web) |
| `created_at` | TEXT | UTC timestamp |

### `telegram_users`

One row per Telegram user, upserted on each generation.

| Column | Type | Description |
|--------|------|-------------|
| `chat_id` | TEXT PK | Telegram chat ID |
| `username` | TEXT | Telegram username |
| `first_name` | TEXT | Telegram first name |
| `total_quizzes` | INTEGER | Cumulative quizzes generated |
| `first_seen` | TEXT | UTC timestamp of first quiz |
| `last_seen` | TEXT | UTC timestamp of most recent quiz |

---

## Known Fixes & Improvements

The following issues were addressed compared to the original version:

1. **Safe data island** — Questions are embedded as `<script type="application/json">` so `</script>` inside question text can never break the page.
2. **Correct JS string escaping** — The quiz title is embedded in JavaScript using `JSON.stringify`, preventing `&amp;` from appearing as literal text inside scripts.
3. **Full Turso error logging** — The full HTTP response body is logged on Turso pipeline errors, not just the status code.
4. **Single pipeline call** — `trackGeneration()` combines the `quiz_generations` insert and `telegram_users` upsert into one Turso pipeline request.
5. **Network-safe Telegram calls** — `tgApi()` is wrapped in try/catch so network errors don't crash the Worker.
6. **Caption length limit** — `tgSendDocument()` truncates captions to 1024 characters (Telegram's limit).
7. **RFC 5987 filename encoding** — `Content-Disposition` filenames use `encodeURIComponent` for correct handling of non-ASCII characters.
8. **503 for unconfigured DB** — `GET /dbstats` returns HTTP 503 (not 200) when Turso is unconfigured or has no data, so client code can distinguish "no stats" from "empty stats".
9. **Channel-post safety** — Messages from channels have no `from` field; the handler guards against this with `message.from || {}`.
10. **GitHub token alias** — Both `GITHUB_TOKEN` and `GITHUB_PERSONAL_ACCESS_TOKEN` are accepted, with a shared `ghToken()` helper.
11. **Question bank card hidden cleanly** — `GET /api/browse` returns 503 when GitHub is not configured, and the upload page checks this status to hide the card.
12. **CSP-safe event handlers** — All navigation button handlers are registered via `addEventListener`, never as inline `onclick` attributes.
13. **Single DOMContentLoaded entry point** — The quiz HTML uses one `DOMContentLoaded` listener so all functions are guaranteed to be defined before any button can trigger them.

---

## Deployment

1. Create a new Worker in the [Cloudflare Dashboard](https://dash.cloudflare.com) or use Wrangler CLI.
2. Paste or upload `worker.js` as the Worker script.
3. Add the required [environment variables](#environment-variables) in the Worker settings.
4. Deploy the Worker.
5. Visit `<your-worker-url>/initdb` to create the database tables.
6. Visit `<your-worker-url>/setup` to register the Telegram webhook.
7. Open `<your-worker-url>/` to use the web interface.
