
import { hasGithub } from "./github.js";

export function hasOpenRouter() {
  return !!process.env.OPENROUTER_API_KEY;
}

function extractUniquePairs(questions) {
  const seen = new Set(), pairs = [];
  for (const q of questions) {
    const subject = String(q.subject || "General").trim();
    const topic   = String(q.topic   || "General").trim();
    const key = `${subject}|||${topic}`;
    if (!seen.has(key)) { seen.add(key); pairs.push({ subject, topic }); }
  }
  return pairs;
}

function allPairsMatch(newPairs, githubStructure) {
  if (!githubStructure) return false;
  return newPairs.every(({ subject, topic }) => {
    const topics = githubStructure[subject];
    return Array.isArray(topics) && topics.includes(topic);
  });
}

async function aiNormalizePairs(newPairs, githubStructure) {
  if (!hasOpenRouter() || !newPairs.length) return null;
  const systemPrompt =
    "You are a taxonomy normalizer for an educational question bank.\n" +
    "Given new subject/topic pairs and the existing bank structure, map each pair to the best matching existing name.\n" +
    "Rules:\n" +
    "- Fix abbreviations: \"Phy\"→\"Physics\", \"Bio\"→\"Biology\"\n" +
    "- Fix case/spelling: \"optics basics\"→\"Optics\", \"Cell Bio\"→\"Cell Biology\"\n" +
    "- If no close match exists keep the original name exactly\n" +
    "- Never invent names — only use names from the existing bank OR the original\n" +
    "- Return a JSON OBJECT where each key is \"OriginalSubject|||OriginalTopic\" and each value is {\"subject\":\"NormalizedSubject\",\"topic\":\"NormalizedTopic\"}\n" +
    "- Return ONLY valid JSON, no explanation, no markdown fences";
  const userMsg =
    `Existing question bank:\n${JSON.stringify(githubStructure, null, 2)}\n\n` +
    `New pairs to normalize:\n${JSON.stringify(newPairs, null, 2)}\n\n` +
    `Return a JSON OBJECT (not an array). Key format: "Subject|||Topic". Every input pair must appear as a key.`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 25_000);
  try {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
        "Content-Type": "application/json",
        "HTTP-Referer": process.env.WORKER_ORIGIN || "https://quiz-generator.workers.dev",
        "X-Title": "Quiz Generator",
      },
      body: JSON.stringify({
        model: "openai/gpt-oss-120b:free",
        temperature: 0,
        max_tokens: 4096,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user",   content: userMsg },
        ],
      }),
    });
    if (!res.ok) {
      console.error("OpenRouter error", res.status, await res.text().catch(() => ""));
      return null;
    }
    const data = await res.json();
    const raw  = data?.choices?.[0]?.message?.content;
    if (!raw) return null;
    const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();
    const parsed  = JSON.parse(cleaned);
    if (typeof parsed !== "object" || Array.isArray(parsed)) return null;
    return parsed;
  } catch (e) {
    if (e.name === "AbortError") {
      console.error("aiNormalizePairs: timed out after 25s — skipping AI normalization");
    } else {
      console.error("aiNormalizePairs error:", e.message);
    }
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function applyNormalization(questions, aiResult) {
  if (!aiResult) return questions;
  return questions.map((q) => {
    const key    = `${q.subject}|||${q.topic}`;
    const mapped = aiResult[key];
    if (!mapped) return q;
    return { ...q, subject: mapped.subject, topic: mapped.topic };
  });
}

export async function normalizeQuestions(questions, githubStructure) {
  if (!githubStructure) return questions;
  const newPairs = extractUniquePairs(questions);
  if (allPairsMatch(newPairs, githubStructure)) return questions;
  if (!hasOpenRouter()) return questions;
  const aiResult = await aiNormalizePairs(newPairs, githubStructure);
  return applyNormalization(questions, aiResult);
}
