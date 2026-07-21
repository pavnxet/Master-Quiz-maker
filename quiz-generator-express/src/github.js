import { toBase64, fromBase64, safeName, dedupKey } from "./utils.js";

export function hasGithub() {
  return !!((process.env.GITHUB_TOKEN || process.env.GITHUB_PERSONAL_ACCESS_TOKEN) && process.env.GITHUB_REPO);
}

function ghToken() {
  return process.env.GITHUB_TOKEN || process.env.GITHUB_PERSONAL_ACCESS_TOKEN;
}

export async function ghFetch(method, filePath, body) {
  const branch = process.env.GITHUB_BRANCH || "main";
  const base = `https://api.github.com/repos/${process.env.GITHUB_REPO}/contents/${filePath}`;
  const url  = method === "GET" ? `${base}?ref=${encodeURIComponent(branch)}` : base;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 10_000);
  const opts = {
    method,
    signal: ctrl.signal,
    headers: {
      Authorization: `Bearer ${ghToken()}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "QuizWorker/1.0",
    },
  };
  if (body) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify({ ...body, branch });
  }
  try {
    return await fetch(url, opts);
  } finally {
    clearTimeout(timer);
  }
}

export async function ghListTopics() {
  if (!hasGithub()) return null;
  try {
    const branch = process.env.GITHUB_BRANCH || "main";
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10_000);
    let r;
    try {
      r = await fetch(
        `https://api.github.com/repos/${process.env.GITHUB_REPO}/git/trees/${encodeURIComponent(branch)}?recursive=1`,
        {
          signal: ctrl.signal,
          headers: {
            Authorization: `Bearer ${ghToken()}`,
            Accept: "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "QuizWorker/1.0",
          },
        },
      );
    } finally {
      clearTimeout(timer);
    }
    if (!r.ok) return null;
    const data = await r.json();
    const structure = {};
    for (const item of data.tree || []) {
      const m = item.path.match(/^questions\/([^\/]+)\/([^\/]+)\.json$/);
      if (m && item.type === "blob") {
        const [, subject, topic] = m;
        if (!structure[subject]) structure[subject] = [];
        structure[subject].push(topic);
      }
    }
    return Object.keys(structure).length ? structure : null;
  } catch (e) {
    console.error("ghListTopics error:", e.message);
    return null;
  }
}

export async function ghGetQuestions(subject, topic) {
  if (!hasGithub()) return null;
  try {
    const r = await ghFetch("GET", `questions/${safeName(subject)}/${safeName(topic)}.json`);
    if (!r.ok) return null;
    const data = await r.json();
    return JSON.parse(fromBase64(data.content));
  } catch (e) {
    console.error("ghGetQuestions error:", e.message);
    return null;
  }
}

export async function saveQuestionsToGithub(questions, source) {
  if (!hasGithub()) return;
  try {
    const groups = {};
    for (const q of questions) {
      const subject = safeName(q.subject);
      const topic   = safeName(q.topic);
      if (!groups[subject]) groups[subject] = {};
      if (!groups[subject][topic]) groups[subject][topic] = [];
      groups[subject][topic].push(q);
    }

    let saved = 0, failed = 0;

    for (const [subject, topics] of Object.entries(groups)) {
      for (const [topic, newQs] of Object.entries(topics)) {
        const filePath = `questions/${subject}/${topic}.json`;
        try {
          let existing = [], sha = null;
          try {
            const r = await ghFetch("GET", filePath);
            if (r.ok) {
              const data = await r.json();
              sha = data.sha;
              existing = JSON.parse(fromBase64(data.content));
            }
          } catch (_) {}

          const seen   = new Set(existing.map(dedupKey));
          const toAdd  = newQs.filter((q) => !seen.has(dedupKey(q)));
          if (toAdd.length === 0) continue;

          const merged  = [...existing, ...toAdd];
          const content = toBase64(JSON.stringify(merged, null, 2));

          const body = {
            message: `Add ${toAdd.length} question(s) to ${subject}/${topic} [${source}]`,
            content,
          };
          if (sha) body.sha = sha;

          const wr = await ghFetch("PUT", filePath, body);
          if (wr.ok) {
            saved++;
          } else {
            failed++;
            console.error(`GitHub save failed ${wr.status} for ${filePath}`);
          }
        } catch (e) {
          failed++;
          console.error(`GitHub save error for ${filePath}:`, e.message);
        }
      }
    }

    if (saved > 0 || failed > 0) {
      console.log(`GitHub save [${source}]: ${saved} saved, ${failed} failed`);
    }
  } catch (e) {
    console.error("saveQuestionsToGithub error:", e.message);
  }
}
