
function hasDb() {
  return !!(process.env.TURSO_DB_URL && process.env.TURSO_AUTH_TOKEN);
}

async function dbExec(statements) {
  if (!hasDb()) return null;
  const requests = statements.map((s) => ({
    type: "execute",
    stmt: {
      sql: s.sql,
      args: (s.args || []).map((v) =>
        v === null || v === undefined
          ? { type: "null" }
          : typeof v === "number"
            ? { type: "integer", value: String(Math.trunc(v)) }
            : { type: "text", value: String(v) },
      ),
    },
  }));
  requests.push({ type: "close" });
  const dbHttpUrl = process.env.TURSO_DB_URL.replace(/^libsql:\/\//, "https://");
  try {
    const r = await fetch(`${dbHttpUrl}/v2/pipeline`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.TURSO_AUTH_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ requests }),
    });
    if (!r.ok) {
      const errBody = await r.text().catch(() => "(unreadable)");
      console.error("Turso HTTP error", r.status, errBody);
      return null;
    }
    return r.json();
  } catch (e) {
    console.error("Turso fetch error:", e.message);
    return null;
  }
}

async function dbQuery(sql, args = []) {
  const res = await dbExec([{ sql, args }]);
  return res?.results?.[0]?.response?.result ?? null;
}

export async function initDb() {
  return dbExec([
    {
      sql: `CREATE TABLE IF NOT EXISTS quiz_generations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        title TEXT,
        questions_count INTEGER,
        telegram_chat_id TEXT,
        telegram_username TEXT,
        created_at TEXT DEFAULT (datetime('now'))
      )`,
    },
    {
      sql: `CREATE TABLE IF NOT EXISTS telegram_users (
        chat_id TEXT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        total_quizzes INTEGER DEFAULT 0,
        first_seen TEXT DEFAULT (datetime('now')),
        last_seen TEXT DEFAULT (datetime('now'))
      )`,
    },
  ]);
}

export async function trackGeneration({ source, title, questionsCount, chatId, username, firstName }) {
  if (!hasDb()) return;
  try {
    const stmts = [
      {
        sql: "INSERT INTO quiz_generations (source, title, questions_count, telegram_chat_id, telegram_username) VALUES (?, ?, ?, ?, ?)",
        args: [source, title || "", questionsCount, chatId ?? null, username ?? null],
      },
    ];
    if (chatId) {
      stmts.push({
        sql: `INSERT INTO telegram_users (chat_id, username, first_name, total_quizzes, last_seen)
              VALUES (?, ?, ?, 1, datetime('now'))
              ON CONFLICT(chat_id) DO UPDATE SET
                total_quizzes = total_quizzes + 1,
                last_seen     = datetime('now'),
                username      = COALESCE(excluded.username, username),
                first_name    = COALESCE(excluded.first_name, first_name)`,
        args: [String(chatId), username ?? null, firstName ?? null],
      });
    }
    await dbExec(stmts);
  } catch (e) {
    console.error("trackGeneration error:", e.message);
  }
}

export async function getDbStats() {
  if (!hasDb()) return null;
  try {
    const [gen, users] = await Promise.all([
      dbQuery(
        `SELECT COUNT(*) AS total, COALESCE(SUM(questions_count),0) AS total_questions,
                COUNT(CASE WHEN source='telegram' THEN 1 END) AS tg_count,
                COUNT(CASE WHEN source='web' THEN 1 END) AS web_count
         FROM quiz_generations`
      ),
      dbQuery("SELECT COUNT(*) AS total FROM telegram_users"),
    ]);
    if (!gen) return null;
    const row = (r) => Object.fromEntries((r?.columns || []).map((c, i) => [c, r.rows?.[0]?.[i] ?? 0]));
    const g = row(gen);
    const u = row(users);
    return {
      total: Number(g.total || 0),
      totalQuestions: Number(g.total_questions || 0),
      tgCount: Number(g.tg_count || 0),
      webCount: Number(g.web_count || 0),
      telegramUsers: Number(u.total || 0),
    };
  } catch (e) {
    console.error("getDbStats error:", e.message);
    return null;
  }
}
