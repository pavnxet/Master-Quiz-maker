import "dotenv/config";
import express          from "express";
import multer           from "multer";
import { UPLOAD_PAGE }  from "./src/upload-page.js";
import { generateHtml } from "./src/quiz-html.js";
import { escHtml, safeName, validateQuestions } from "./src/utils.js";
import { initDb, trackGeneration, getDbStats }  from "./src/db.js";
import {
  hasGithub, ghListTopics, ghGetQuestions, saveQuestionsToGithub,
} from "./src/github.js";
import { hasOpenRouter, normalizeQuestions } from "./src/ai.js";
import {
  tgApi, tgSend, tgSendDocument, tgGetFileUrl, editStatus,
} from "./src/telegram.js";

// ─── Helpers ────────────────────────────────────────────────────────────────
function isAdminAuthorized(req) {
  const adminSecret = process.env.ADMIN_SECRET;
  if (!adminSecret) return true;
  return req.query.secret === adminSecret ||
         req.headers["x-admin-secret"] === adminSecret;
}

function fireAndForget(promise) {
  promise.catch((e) => console.error("background task error:", e.message));
}

// ─── Express setup ───────────────────────────────────────────────────────────
const app  = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: "10mb" }));

// Security headers on every response
app.use((req, res, next) => {
  res.set("X-Content-Type-Options",  "nosniff");
  res.set("X-Frame-Options",         "DENY");
  res.set("X-XSS-Protection",        "1; mode=block");
  res.set("Referrer-Policy",         "strict-origin-when-cross-origin");
  res.set("Permissions-Policy",      "camera=(), microphone=(), geolocation=()");
  res.set(
    "Content-Security-Policy",
    "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; " +
    "img-src * data: blob:; connect-src *; frame-ancestors 'none'",
  );
  next();
});

// CORS preflight
app.options("*", (req, res) => {
  res.set("Access-Control-Allow-Origin",  "*");
  res.set("Access-Control-Allow-Methods", "GET,POST");
  res.set("Access-Control-Allow-Headers", "Content-Type");
  res.sendStatus(204);
});

// Multer — in-memory, 10 MB limit
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
});

// ─────────────────────────────────────────────────────────────────────────────
//  GET /  — Upload page
// ─────────────────────────────────────────────────────────────────────────────
app.get("/", (req, res) => {
  res.set("Content-Type", "text/html; charset=UTF-8");
  res.send(UPLOAD_PAGE);
});

// ─────────────────────────────────────────────────────────────────────────────
//  GET /dbstats
// ─────────────────────────────────────────────────────────────────────────────
app.get("/dbstats", async (req, res) => {
  const stats = await getDbStats();
  if (!stats) return res.status(503).json({ error: "Database not configured or empty." });
  res.json(stats);
});

// ─────────────────────────────────────────────────────────────────────────────
//  GET /api/browse
// ─────────────────────────────────────────────────────────────────────────────
app.get("/api/browse", async (req, res) => {
  if (!hasGithub()) return res.status(503).json({ error: "GitHub not configured." });
  const structure = await ghListTopics();
  if (!structure)  return res.status(503).json({ error: "Question bank is empty or unreachable." });
  res.json(structure);
});

// ─────────────────────────────────────────────────────────────────────────────
//  GET /api/download?subject=X&topic=Y
// ─────────────────────────────────────────────────────────────────────────────
app.get("/api/download", async (req, res) => {
  const { subject, topic } = req.query;
  if (!subject || !topic) return res.status(400).json({ error: "subject and topic query params required." });
  if (!hasGithub())        return res.status(503).json({ error: "GitHub not configured." });
  const questions = await ghGetQuestions(subject, topic);
  if (!questions?.length)  return res.status(404).json({ error: "No questions found for that subject/topic." });
  res.json(questions);
});

// ─────────────────────────────────────────────────────────────────────────────
//  GET /initdb  — Create Turso tables (admin-guarded)
// ─────────────────────────────────────────────────────────────────────────────
app.get("/initdb", async (req, res) => {
  if (!isAdminAuthorized(req))
    return res.status(403).json({ error: "Forbidden — ADMIN_SECRET required." });
  if (!process.env.TURSO_DB_URL || !process.env.TURSO_AUTH_TOKEN)
    return res.status(400).json({ error: "TURSO_DB_URL and TURSO_AUTH_TOKEN not set." });
  await initDb();
  res.json({ ok: true, message: "Tables created (or already exist)." });
});

// ─────────────────────────────────────────────────────────────────────────────
//  GET /setup  — Register Telegram webhook (admin-guarded)
// ─────────────────────────────────────────────────────────────────────────────
app.get("/setup", async (req, res) => {
  if (!isAdminAuthorized(req))
    return res.status(403).json({ error: "Forbidden — ADMIN_SECRET required." });
  if (!process.env.TELEGRAM_TOKEN)
    return res.status(400).json({ error: "TELEGRAM_TOKEN not set." });

  const base    = `${req.protocol}://${req.get("host")}`;
  const webhook = `${base}/telegram`;
  const params  = { url: webhook, allowed_updates: ["message", "channel_post"] };
  if (process.env.TELEGRAM_WEBHOOK_SECRET) {
    params.secret_token = process.env.TELEGRAM_WEBHOOK_SECRET;
  }
  const result = await tgApi("setWebhook", params);
  res.status(result.ok ? 200 : 500).json({
    ok: result.ok,
    webhook,
    telegram: result.description,
    secretRegistered: !!process.env.TELEGRAM_WEBHOOK_SECRET,
    adminProtected: !!process.env.ADMIN_SECRET,
    warnings: [
      ...(!process.env.TELEGRAM_WEBHOOK_SECRET ? ["TELEGRAM_WEBHOOK_SECRET not set — webhook is unauthenticated"] : []),
      ...(!process.env.ADMIN_SECRET ? ["ADMIN_SECRET not set — /setup and /initdb are publicly accessible"] : []),
    ],
    note: result.ok
      ? "✅ Bot ready! Send a .json file to your bot in Telegram."
      : "❌ Failed. Check TELEGRAM_TOKEN.",
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  POST /generate  — Web upload handler
// ─────────────────────────────────────────────────────────────────────────────
app.post("/generate", upload.single("file"), async (req, res) => {
  if (!req.file)
    return res.status(400).json({ error: "No file uploaded." });

  // Content-size guard (multer already enforces fileSize, but double-check)
  if (req.file.size > 10 * 1024 * 1024)
    return res.status(413).json({ error: "File too large. Maximum 10 MB per upload." });

  let questions;
  try {
    questions = JSON.parse(req.file.buffer.toString("utf8"));
  } catch (e) {
    return res.status(400).json({ error: `Invalid JSON: ${e.message}` });
  }
  if (!Array.isArray(questions) || !questions.length)
    return res.status(400).json({ error: "JSON must be a non-empty array." });

  questions = validateQuestions(questions);
  if (!questions.length)
    return res.status(400).json({ error: "No valid question objects found." });

  if (questions.length > 500)
    return res.status(400).json({ error: "Too many questions. Maximum 500 per upload." });

  const rawFilename = req.body.outname || req.file.originalname || "quiz.json";
  const filename    = rawFilename.slice(0, 200);
  const rawTitle    = req.body.title ||
    filename.replace(/\.\w+$/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const title = rawTitle.slice(0, 200);

  const shouldSave = (req.body.saveToGithub ?? "true") !== "false";

  let normalizedQuestions = questions;
  if (shouldSave && hasGithub()) {
    const structure = await ghListTopics();
    normalizedQuestions = await normalizeQuestions(questions, structure);
  }

  const htmlOut = generateHtml(normalizedQuestions, title);
  const outName = filename.replace(/\.\w+$/, "") + "_quiz.html";

  res.set("Content-Type", "text/html; charset=UTF-8");
  res.set("Content-Disposition",
    `attachment; filename="${outName}"; filename*=UTF-8''${encodeURIComponent(outName)}`);
  res.send(htmlOut);

  // Fire-and-forget: save to GitHub + track analytics
  fireAndForget(Promise.all([
    trackGeneration({ source: "web", title, questionsCount: normalizedQuestions.length }),
    ...(shouldSave ? [saveQuestionsToGithub(normalizedQuestions, "web")] : []),
  ]));
});

// ─────────────────────────────────────────────────────────────────────────────
//  POST /telegram  — Telegram webhook
// ─────────────────────────────────────────────────────────────────────────────
app.post("/telegram", async (req, res) => {
  if (!process.env.TELEGRAM_TOKEN) return res.sendStatus(200);

  // Webhook secret verification
  const webhookSecret = process.env.TELEGRAM_WEBHOOK_SECRET;
  if (webhookSecret) {
    const incoming = req.headers["x-telegram-bot-api-secret-token"] || "";
    if (incoming !== webhookSecret) {
      console.warn("handleTelegram: invalid webhook secret — rejected");
      return res.sendStatus(403);
    }
  }

  // Always respond 200 immediately — Telegram requires it within 60s
  res.sendStatus(200);

  // Process the update asynchronously after responding
  fireAndForget(handleTelegramUpdate(req.body));
});

// ─────────────────────────────────────────────────────────────────────────────
//  Telegram update handler (runs after HTTP 200 is already sent)
// ─────────────────────────────────────────────────────────────────────────────
async function handleTelegramUpdate(update) {
  if (!update) return;
  const token   = process.env.TELEGRAM_TOKEN;
  const message = update.message || update.channel_post || {};
  const chatId  = message?.chat?.id;
  if (!chatId) return;

  const from      = message.from || {};
  const username  = from.username  || null;
  const firstName = from.first_name || null;
  const text      = message.text || "";

  // ── Commands ───────────────────────────────────────────────────────────────
  if (text === "/start" || text.startsWith("/start ")) {
    await tgSend(chatId,
      "👋 <b>Welcome to Quiz Generator Bot!</b>\n\n" +
      "📎 <b>Send me a <code>.json</code> quiz file</b> and I'll turn it into an interactive bilingual quiz.\n\n" +
      "📋 <b>Commands:</b>\n" +
      "/help — Full guide\n" +
      "/topics — Browse question bank\n" +
      "/download Subject | Topic — Get a topic quiz\n" +
      "/mystats — Your quiz history\n" +
      "/globalstats — Platform totals\n\n" +
      "💡 <i>Add <code>nosave</code> to your file caption to skip saving to the bank.</i>"
    );
    return;
  }

  if (text === "/help" || text.startsWith("/help ")) {
    await tgSend(chatId,
      "📖 <b>Quiz Generator — Help</b>\n\n" +
      "<b>Upload a quiz file:</b>\n" +
      "Tap 📎 → File → select your <code>.json</code> file → Send\n" +
      "Add <code>nosave</code> or <code>#nosave</code> to caption to skip bank save\n\n" +
      "<b>Commands:</b>\n" +
      "/topics — List all subjects &amp; topics in the question bank\n" +
      "/download Subject | Topic — Download a quiz for a topic\n" +
      "/mystats — Your personal quiz stats\n" +
      "/globalstats — Total platform stats\n\n" +
      "<b>Supported file formats:</b> <code>.json</code>, <code>.txt</code> (JSON content)\n" +
      "<b>Max file size:</b> 20 MB\n" +
      "<b>Max questions per upload:</b> 500"
    );
    return;
  }

  if (text === "/mystats" || text.startsWith("/mystats ")) {
    const { getDbStats: _s, ...dbMod } = await import("./src/db.js");
    const stats = await _s();
    if (!stats) {
      await tgSend(chatId, "📊 Analytics not configured on this server.");
      return;
    }
    await tgSend(chatId,
      `📊 <b>Your Stats</b>\n\nTotal platform quizzes: <b>${stats.total}</b>\n` +
      `Questions processed: <b>${stats.totalQuestions}</b>`
    );
    return;
  }

  if (text === "/globalstats" || text.startsWith("/globalstats ")) {
    const stats = await getDbStats();
    if (!stats) {
      await tgSend(chatId, "📊 Analytics not configured on this server.");
      return;
    }
    await tgSend(chatId,
      `📊 <b>Global Stats</b>\n\n` +
      `📝 Total quizzes generated: <b>${stats.total}</b>\n` +
      `📋 Questions handled: <b>${stats.totalQuestions}</b>\n` +
      `🌐 Via Web:      ${stats.webCount}\n` +
      `📱 Via Telegram: ${stats.tgCount}\n` +
      `👥 Bot users:    ${stats.telegramUsers}`
    );
    return;
  }

  if (text.startsWith("/topics")) {
    if (!hasGithub()) {
      await tgSend(chatId, "⚠️ Question bank not configured on this server.");
      return;
    }
    await tgSend(chatId, "🔍 Fetching question bank…");
    const structure = await ghListTopics();
    if (!structure) {
      await tgSend(chatId,
        "📭 Question bank is empty. Send a <code>.json</code> file to start building it!"
      );
      return;
    }
    const subjects = Object.keys(structure).sort();
    let msg = `📚 <b>Question Bank</b> — ${subjects.length} subject${subjects.length !== 1 ? "s" : ""}\n`;
    for (const subject of subjects) {
      const topics = structure[subject].sort();
      msg += `\n📖 <b>${escHtml(subject)}</b> (${topics.length} topic${topics.length !== 1 ? "s" : ""})\n`;
      msg += topics.map((t) => `  • ${escHtml(t)}`).join("\n") + "\n";
    }
    msg += `\n💡 <i>Use /download &lt;Subject&gt; | &lt;Topic&gt; to get a quiz</i>`;
    await tgSend(chatId, msg);
    return;
  }

  if (text.startsWith("/download")) {
    if (!hasGithub()) {
      await tgSend(chatId, "⚠️ Question bank not configured on this server.");
      return;
    }
    const arg = text.replace(/^\/download\s*/i, "").trim();
    if (!arg) {
      await tgSend(chatId,
        "📥 Usage: <code>/download Subject | Topic</code>\n\n" +
        "Example:\n<code>/download Physics | Optics</code>\n\nUse /topics to see available subjects and topics."
      );
      return;
    }
    let subject, topic;
    if (arg.includes("|")) {
      [subject, topic] = arg.split("|").map((s) => s.trim());
    } else {
      await tgSend(chatId, "❌ Please use the format: <code>/download Subject | Topic</code>");
      return;
    }
    if (!subject || !topic) {
      await tgSend(chatId,
        "❌ Both subject and topic are required.\nExample: <code>/download Biology | Cell Biology</code>"
      );
      return;
    }
    await tgSend(chatId, `⚙️ Fetching <b>${escHtml(subject)} › ${escHtml(topic)}</b>…`);
    const questions = await ghGetQuestions(subject, topic);
    if (!questions?.length) {
      await tgSend(chatId,
        `❌ No questions found for <b>${escHtml(subject)} › ${escHtml(topic)}</b>.\n\nUse /topics to see available subjects and topics.`
      );
      return;
    }
    const title    = `${subject} — ${topic}`;
    const htmlOut  = generateHtml(questions, title);
    const outName  = `${safeName(subject)}_${safeName(topic)}_quiz.html`;
    const caption  = `✅ <b>${escHtml(title)}</b>\n📋 ${questions.length} question${questions.length !== 1 ? "s" : ""} · EN + हिं\n⭐ Flag · 🔀 Scramble · 🌙 Dark mode`;
    const result   = await tgSendDocument(chatId, htmlOut, outName, caption);
    if (!result?.ok) {
      await tgSend(chatId, `⚠️ Could not send file: ${escHtml(result?.description || "unknown error")}`);
    }
    return;
  }

  // ── File / document handler ────────────────────────────────────────────────
  const doc = message.document;
  if (doc) {
    const filename = doc.file_name || "quiz.json";
    const ext      = filename.split(".").pop().toLowerCase();
    if (!["json", "txt"].includes(ext)) {
      await tgSend(chatId, "❌ Please send a <b>.json</b> or <b>.txt</b> file.");
      return;
    }

    // File size guard (Telegram Bot API max is 20 MB)
    if (doc.file_size && doc.file_size > 20 * 1024 * 1024) {
      await tgSend(chatId,
        `❌ File too large (${(doc.file_size / 1024 / 1024).toFixed(1)} MB). Maximum is 20 MB.`
      );
      return;
    }

    const caption        = message.caption || "";
    const shouldSaveToRepo = !/nosave/i.test(caption);

    const statusMsg   = await tgSend(chatId, "⏳ Reading file… [▓░░░░] 20%");
    const statusMsgId = statusMsg?.result?.message_id;
    const setStatus   = (text) => editStatus(chatId, statusMsgId, text);

    const fileUrl = await tgGetFileUrl(doc.file_id);
    if (!fileUrl) {
      await setStatus("❌ Could not access your file. Please try again.");
      return;
    }

    let content;
    try {
      const fileResp = await fetch(fileUrl);
      if (!fileResp.ok) throw new Error(`HTTP ${fileResp.status}`);
      content = await fileResp.text();
    } catch (e) {
      await setStatus(`❌ Failed to download the file: ${escHtml(e.message)}`);
      return;
    }

    let questions;
    try {
      questions = JSON.parse(content);
    } catch (e) {
      await setStatus(`❌ Invalid JSON: ${escHtml(e.message)}`);
      return;
    }

    if (!Array.isArray(questions) || !questions.length) {
      await setStatus("❌ JSON must be a non-empty array of question objects.");
      return;
    }

    questions = validateQuestions(questions);
    if (!questions.length) {
      await setStatus("❌ No valid question objects found. Each item must have a text field.");
      return;
    }

    if (questions.length > 500) {
      await setStatus(`❌ Too many questions (${questions.length}). Maximum 500 per upload.`);
      return;
    }

    await setStatus("🔍 Checking question bank… [▓▓░░░] 40%");
    let githubStructure = null;
    if (shouldSaveToRepo && hasGithub()) {
      githubStructure = await ghListTopics();
    }

    if (shouldSaveToRepo && githubStructure) {
      await setStatus("🤖 AI normalizing topics… [▓▓▓░░] 60%");
      questions = await normalizeQuestions(questions, githubStructure);
    }

    await setStatus("⚙️ Building quiz… [▓▓▓▓░] 80%");
    const title   = filename
      .replace(/\.\w+$/, "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    const htmlOut = generateHtml(questions, title);
    const outName = filename.replace(/\.\w+$/, "") + "_quiz.html";
    const saveNote = shouldSaveToRepo ? "\n💾 Saved to Question Bank" : "\n⚡ Temporary (not saved)";
    const docCaption = `✅ <b>${escHtml(title)}</b>\n📋 ${questions.length} questions · EN + हिं\n⭐ Flag · ⌨️ Shortcuts · 🔀 Scramble · 🌙 Dark mode${saveNote}`;

    const result = await tgSendDocument(chatId, htmlOut, outName, docCaption);
    if (result?.ok) {
      await setStatus("✅ Done! Quiz delivered. [▓▓▓▓▓] 100%");
    } else {
      await setStatus(`❌ Quiz built but delivery failed: ${escHtml(result?.description || "unknown error")}`);
    }

    // Fire and forget: analytics + GitHub save
    fireAndForget(Promise.all([
      trackGeneration({ source: "telegram", title, questionsCount: questions.length, chatId, username, firstName }),
      ...(shouldSaveToRepo ? [saveQuestionsToGithub(questions, "telegram")] : []),
    ]));
    return;
  }

  // Default
  await tgSend(chatId,
    "📄 Send a <b>.json</b> quiz file, or type /help for instructions."
  );
}

// ─── Start server ─────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✅ Quiz Generator running at http://localhost:${PORT}`);
  console.log(`   GitHub bank : ${process.env.GITHUB_REPO    || "⚠️  not configured"}`);
  console.log(`   Turso DB    : ${process.env.TURSO_DB_URL   ? "✅ configured" : "⚠️  not configured"}`);
  console.log(`   OpenRouter  : ${process.env.OPENROUTER_API_KEY ? "✅ configured" : "⚠️  not configured"}`);
  console.log(`   Telegram    : ${process.env.TELEGRAM_TOKEN  ? "✅ configured" : "⚠️  not configured"}`);
});

export default app;
