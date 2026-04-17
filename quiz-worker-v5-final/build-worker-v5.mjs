#!/usr/bin/env node
/**
 * Transforms worker_v4.0 → worker_v5.0
 *
 * Security patches applied:
 *  S1. applySecurityHeaders() — X-Content-Type-Options, X-Frame-Options,
 *      Referrer-Policy, Permissions-Policy, CSP — applied to EVERY response
 *      via the main fetch entry point wrapper
 *  S2. Telegram webhook secret verification — checks
 *      X-Telegram-Bot-Api-Secret-Token on every /telegram request
 *  S3. setupWebhook now registers secret_token so Telegram signs all calls
 *  S4. isAdminAuthorized() guard on /setup and /initdb — requires ADMIN_SECRET
 *  S5. File-size guard on POST /generate — rejects > 10 MB requests early
 *  S6. Question-count cap — max 500 questions per upload (web + Telegram)
 *  S7. Title length cap — truncate to 200 chars to prevent oversized DB writes
 *
 * New optional env vars (all backward-compatible — safe to deploy without them):
 *   TELEGRAM_WEBHOOK_SECRET  — shared secret registered with Telegram's webhook
 *   ADMIN_SECRET             — required to call /setup and /initdb
 */
import { readFileSync, writeFileSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(__dirname, "../attached_assets/worker_v4.0.js");
const OUT = path.resolve(__dirname, "../attached_assets/worker_v5.0.js");

let src = readFileSync(SRC, "utf8").replace(/\r\n/g, "\n");

// ─────────────────────────────────────────────────────────────
// S0 — Version bump in header
// ─────────────────────────────────────────────────────────────
src = src.replace(
  " * Cloudflare Workers — Quiz Generator + Telegram Bot + Turso DB + GitHub Store + AI Normalizer",
  " * Cloudflare Workers — Quiz Generator + Telegram Bot + Turso DB + GitHub Store + AI Normalizer [v5]"
);
src = src.replace(
  " * v4.0 ADDITIONS:",
  " * v5.0 SECURITY HARDENING:\n" +
  " * S1. Security headers on every response (CSP, X-Frame-Options, nosniff, etc.)\n" +
  " * S2. Telegram webhook signature verification (X-Telegram-Bot-Api-Secret-Token)\n" +
  " * S3. setupWebhook registers secret_token with Telegram (TELEGRAM_WEBHOOK_SECRET)\n" +
  " * S4. /setup + /initdb gated behind ADMIN_SECRET query param or header\n" +
  " * S5. POST /generate: 10 MB file-size guard (Content-Length check)\n" +
  " * S6. 500-question cap per upload (web + Telegram)\n" +
  " * S7. Title length capped at 200 chars\n" +
  " *     New optional env vars: TELEGRAM_WEBHOOK_SECRET, ADMIN_SECRET\n" +
  " *\n" +
  " * v4.0 ADDITIONS:"
);
console.log("✅ S0: Version bumped to v5.0");

// ─────────────────────────────────────────────────────────────
// S1 — Add security helpers + wrap entry point
// ─────────────────────────────────────────────────────────────

// Add applySecurityHeaders + isAdminAuthorized right before the entry point
const ENTRY_ANCHOR = "export default {";
const SECURITY_HELPERS = `// ════════════════════════════════════════════════════════════
//  SECURITY HELPERS
// ════════════════════════════════════════════════════════════
function applySecurityHeaders(response) {
  const h = new Headers(response.headers);
  h.set("X-Content-Type-Options", "nosniff");
  h.set("X-Frame-Options", "DENY");
  h.set("Referrer-Policy", "strict-origin-when-cross-origin");
  h.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  h.set("X-XSS-Protection", "1; mode=block");
  if (!h.has("Content-Security-Policy")) {
    h.set(
      "Content-Security-Policy",
      "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; " +
      "img-src * data: blob:; connect-src *; frame-ancestors 'none'",
    );
  }
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers: h });
}

function isAdminAuthorized(request, env) {
  const adminSecret = env.ADMIN_SECRET;
  if (!adminSecret) return true; // not set → open (backward compatible)
  const url = new URL(request.url);
  const qs  = url.searchParams.get("secret");
  const hdr = request.headers.get("X-Admin-Secret");
  return qs === adminSecret || hdr === adminSecret;
}

`;

if (!src.includes(ENTRY_ANCHOR)) throw new Error("Cannot find export default entry point");
src = src.replace(ENTRY_ANCHOR, SECURITY_HELPERS + ENTRY_ANCHOR);
console.log("✅ S1a: applySecurityHeaders + isAdminAuthorized helpers added");

// Wrap the entire fetch handler so ALL responses get security headers
const OLD_FETCH_CLOSE = `    return new Response("Not found", { status: 404 });
  },
};`;
const NEW_FETCH_CLOSE = `    return new Response("Not found", { status: 404 });
  },
};`;

// Instead, wrap the inner handler call — replace the fetch signature so
// every returned response passes through applySecurityHeaders
const OLD_FETCH_SIG = `export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;`;

const NEW_FETCH_SIG = `export default {
  async fetch(request, env, ctx) {
    const response = await this._handle(request, env, ctx);
    return applySecurityHeaders(response);
  },

  async _handle(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;`;

if (!src.includes(OLD_FETCH_SIG)) throw new Error("Cannot find fetch handler signature");
src = src.replace(OLD_FETCH_SIG, NEW_FETCH_SIG);
console.log("✅ S1b: fetch handler wrapped — all responses get security headers");

// ─────────────────────────────────────────────────────────────
// S2 — Telegram webhook secret verification
// ─────────────────────────────────────────────────────────────
const OLD_TG_OPEN = `async function handleTelegram(request, env, ctx) {
  const token = env.TELEGRAM_TOKEN;
  let update;
  try {
    update = await request.json();
  } catch {
    return okResp();
  }`;

const NEW_TG_OPEN = `async function handleTelegram(request, env, ctx) {
  const token = env.TELEGRAM_TOKEN;

  // S2: Verify Telegram webhook secret token (TELEGRAM_WEBHOOK_SECRET env var)
  const webhookSecret = env.TELEGRAM_WEBHOOK_SECRET;
  if (webhookSecret) {
    const incoming = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
    if (incoming !== webhookSecret) {
      console.warn("handleTelegram: invalid or missing webhook secret — request rejected");
      return new Response("Forbidden", { status: 403 });
    }
  }

  let update;
  try {
    update = await request.json();
  } catch {
    return okResp();
  }`;

if (!src.includes(OLD_TG_OPEN)) throw new Error("Cannot find handleTelegram opening");
src = src.replace(OLD_TG_OPEN, NEW_TG_OPEN);
console.log("✅ S2: Telegram webhook secret verification added");

// ─────────────────────────────────────────────────────────────
// S3 — setupWebhook registers secret_token + admin guard
// ─────────────────────────────────────────────────────────────
const OLD_SETUP = `async function setupWebhook(request, env) {
  const token = env.TELEGRAM_TOKEN;
  const base = new URL(request.url).origin;
  const webhook = \`\${base}/telegram\`;
  const result = await tgApi(token, "setWebhook", {
    url: webhook,
    allowed_updates: ["message", "channel_post"],
  });
  return jsonResponse(
    {
      ok: result.ok,
      webhook,
      telegram: result.description,
      note: result.ok
        ? "✅ Bot ready! Send a .json file to your bot in Telegram."
        : "❌ Failed. Check TELEGRAM_TOKEN.",
    },
    result.ok ? 200 : 500,
  );
}`;

const NEW_SETUP = `async function setupWebhook(request, env) {
  // S4: Admin guard — set ADMIN_SECRET env var to lock this endpoint
  if (!isAdminAuthorized(request, env))
    return jsonResponse({ error: "Forbidden — ADMIN_SECRET required." }, 403);

  const token = env.TELEGRAM_TOKEN;
  const base = new URL(request.url).origin;
  const webhook = \`\${base}/telegram\`;

  // S3: Register webhook secret so Telegram signs every callback
  const webhookParams = { url: webhook, allowed_updates: ["message", "channel_post"] };
  if (env.TELEGRAM_WEBHOOK_SECRET) {
    webhookParams.secret_token = env.TELEGRAM_WEBHOOK_SECRET;
  }

  const result = await tgApi(token, "setWebhook", webhookParams);
  return jsonResponse(
    {
      ok: result.ok,
      webhook,
      telegram: result.description,
      secretRegistered: !!env.TELEGRAM_WEBHOOK_SECRET,
      note: result.ok
        ? "✅ Bot ready! Send a .json file to your bot in Telegram."
        : "❌ Failed. Check TELEGRAM_TOKEN.",
    },
    result.ok ? 200 : 500,
  );
}`;

if (!src.includes(OLD_SETUP)) throw new Error("Cannot find setupWebhook function");
src = src.replace(OLD_SETUP, NEW_SETUP);
console.log("✅ S3+S4a: setupWebhook registers secret_token + admin guard");

// ─────────────────────────────────────────────────────────────
// S4b — /initdb admin guard (in entry point)
// ─────────────────────────────────────────────────────────────
const OLD_INITDB = `    if (method === "GET" && path === "/initdb") {
      if (!hasDb(env))
        return jsonResponse(
          { error: "TURSO_DB_URL and TURSO_AUTH_TOKEN not set." },
          400,
        );
      await initDb(env);
      return jsonResponse({
        ok: true,
        message: "Tables created (or already exist).",
      });
    }`;

const NEW_INITDB = `    if (method === "GET" && path === "/initdb") {
      // S4: Admin guard
      if (!isAdminAuthorized(request, env))
        return jsonResponse({ error: "Forbidden — ADMIN_SECRET required." }, 403);
      if (!hasDb(env))
        return jsonResponse(
          { error: "TURSO_DB_URL and TURSO_AUTH_TOKEN not set." },
          400,
        );
      await initDb(env);
      return jsonResponse({
        ok: true,
        message: "Tables created (or already exist).",
      });
    }`;

if (!src.includes(OLD_INITDB)) throw new Error("Cannot find /initdb handler");
src = src.replace(OLD_INITDB, NEW_INITDB);
console.log("✅ S4b: /initdb admin guard added");

// ─────────────────────────────────────────────────────────────
// S5 + S6 + S7 — File-size, question count, title length in handleGenerate
// ─────────────────────────────────────────────────────────────
const OLD_HANDLE_GEN_OPEN = `async function handleGenerate(request, env, ctx) {
  let formData;
  try {
    formData = await request.formData();
  } catch {
    return jsonResponse({ error: "Could not parse form data." }, 400);
  }
  const file = formData.get("file");
  if (!file) return jsonResponse({ error: "No file uploaded." }, 400);

  const content = await file.text();
  const filename = formData.get("outname") || file.name || "quiz.json";
  const title =
    formData.get("title") ||
    filename
      .replace(/\\.\\w+$/, "")
      .replace(/_/g, " ")
      .replace(/\\b\\w/g, (c) => c.toUpperCase());

  let questions;
  try {
    questions = JSON.parse(content);
  } catch (e) {
    return jsonResponse({ error: \`Invalid JSON: \${e.message}\` }, 400);
  }
  if (!Array.isArray(questions) || !questions.length)
    return jsonResponse({ error: "JSON must be a non-empty array." }, 400);`;

const NEW_HANDLE_GEN_OPEN = `async function handleGenerate(request, env, ctx) {
  // S5: Reject oversized requests before reading body
  const contentLength = parseInt(request.headers.get("Content-Length") || "0", 10);
  if (contentLength > 10 * 1024 * 1024)
    return jsonResponse({ error: "Request too large. Maximum 10 MB per upload." }, 413);

  let formData;
  try {
    formData = await request.formData();
  } catch {
    return jsonResponse({ error: "Could not parse form data." }, 400);
  }
  const file = formData.get("file");
  if (!file) return jsonResponse({ error: "No file uploaded." }, 400);

  const content = await file.text();

  // S5: Also guard on actual content size after reading
  if (content.length > 10 * 1024 * 1024)
    return jsonResponse({ error: "File too large. Maximum 10 MB." }, 413);

  const rawFilename = formData.get("outname") || file.name || "quiz.json";
  const filename = rawFilename.slice(0, 200); // S7: cap filename length
  const rawTitle =
    formData.get("title") ||
    filename
      .replace(/\\.\\w+$/, "")
      .replace(/_/g, " ")
      .replace(/\\b\\w/g, (c) => c.toUpperCase());
  const title = rawTitle.slice(0, 200); // S7: cap title to 200 chars

  let questions;
  try {
    questions = JSON.parse(content);
  } catch (e) {
    return jsonResponse({ error: \`Invalid JSON: \${e.message}\` }, 400);
  }
  if (!Array.isArray(questions) || !questions.length)
    return jsonResponse({ error: "JSON must be a non-empty array." }, 400);

  // S6: Question count cap
  if (questions.length > 500)
    return jsonResponse({ error: "Too many questions. Maximum 500 per upload." }, 400);`;

if (!src.includes(OLD_HANDLE_GEN_OPEN)) throw new Error("Cannot find handleGenerate opening");
src = src.replace(OLD_HANDLE_GEN_OPEN, NEW_HANDLE_GEN_OPEN);
console.log("✅ S5+S6+S7: handleGenerate — file-size guard, question cap, title cap");

// ─────────────────────────────────────────────────────────────
// S6 — Question count cap in Telegram handler too
// ─────────────────────────────────────────────────────────────
const OLD_TG_Q_CHECK = `    if (!Array.isArray(questions) || !questions.length) {
      await setStatus("❌ JSON must be a non-empty array of question objects.");
      return okResp();
    }

    // Stage 2 — fetch GitHub taxonomy`;

const NEW_TG_Q_CHECK = `    if (!Array.isArray(questions) || !questions.length) {
      await setStatus("❌ JSON must be a non-empty array of question objects.");
      return okResp();
    }

    // S6: Question count cap
    if (questions.length > 500) {
      await setStatus(\`❌ Too many questions (\${questions.length}). Maximum 500 per upload.\`);
      return okResp();
    }

    // Stage 2 — fetch GitHub taxonomy`;

if (!src.includes(OLD_TG_Q_CHECK)) throw new Error("Cannot find Telegram question array check");
src = src.replace(OLD_TG_Q_CHECK, NEW_TG_Q_CHECK);
console.log("✅ S6b: Telegram handler — question count cap added");

// ─────────────────────────────────────────────────────────────
// Write output
// ─────────────────────────────────────────────────────────────
writeFileSync(OUT, src, "utf8");
console.log(`\n✅ Done! Written to: ${OUT}`);
console.log(`   Lines: ${src.split("\n").length}`);
console.log(`\nNew optional env vars to add in Cloudflare:`);
console.log(`  TELEGRAM_WEBHOOK_SECRET  — webhook signature (run /setup after setting)`);
console.log(`  ADMIN_SECRET             — protects /setup and /initdb endpoints`);
