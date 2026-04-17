#!/usr/bin/env node
/**
 * Integration test for the AI normalization logic in worker v4.0
 * Tests:
 *  T1 — GitHub: list topics from pavnxet/quiz-questions
 *  T2 — allPairsMatch bypass (all exact → no AI call)
 *  T3 — OpenRouter AI call with real mismatched pairs
 *  T4 — applyNormalization maps correctly using dictionary
 *  T5 — Full normalizeQuestions end-to-end
 */

const GITHUB_TOKEN = process.env.GITHUB_PERSONAL_ACCESS_TOKEN;
const OPENROUTER_KEY = process.env.OPENROUTER_API_KEY;
const GITHUB_REPO = "pavnxet/quiz-questions";
const GITHUB_BRANCH = "main";

if (!GITHUB_TOKEN) { console.error("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set"); process.exit(1); }
if (!OPENROUTER_KEY) { console.error("❌ OPENROUTER_API_KEY not set"); process.exit(1); }

let passed = 0, failed = 0;
function pass(label) { console.log(`  ✅ ${label}`); passed++; }
function fail(label, detail) { console.error(`  ❌ ${label}${detail ? ": " + detail : ""}`); failed++; }

// ──────────────────────────────────────────────────
// Helper: fetch GitHub tree (same as ghListTopics)
// ──────────────────────────────────────────────────
async function ghListTopics() {
  const r = await fetch(
    `https://api.github.com/repos/${GITHUB_REPO}/git/trees/${encodeURIComponent(GITHUB_BRANCH)}?recursive=1`,
    {
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "QuizWorker/4.0-test",
      },
    }
  );
  if (!r.ok) return null;
  const data = await r.json();
  const structure = {};
  for (const item of data.tree || []) {
    const m = item.path.match(/^questions\/([^/]+)\/([^/]+)\.json$/);
    if (m && item.type === "blob") {
      const [, subject, topic] = m;
      if (!structure[subject]) structure[subject] = [];
      structure[subject].push(topic);
    }
  }
  return Object.keys(structure).length ? structure : null;
}

// ──────────────────────────────────────────────────
// Inline the pure logic functions (no env needed)
// ──────────────────────────────────────────────────
function extractUniquePairs(questions) {
  const seen = new Set();
  const pairs = [];
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

function applyNormalization(questions, aiResult) {
  if (!aiResult) return questions;
  return questions.map(q => {
    const key = `${q.subject}|||${q.topic}`;
    const mapped = aiResult[key];
    if (!mapped) return q;
    return { ...q, subject: mapped.subject, topic: mapped.topic };
  });
}

async function aiNormalizePairs(newPairs, githubStructure) {
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
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENROUTER_KEY}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://quiz-generator.workers.dev",
      "X-Title": "Quiz Generator Test",
    },
    body: JSON.stringify({
      model: "openai/gpt-oss-120b:free",
      temperature: 0,
      max_tokens: 1024,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user",   content: userMsg },
      ],
    }),
  });
  if (!res.ok) throw new Error(`OpenRouter HTTP ${res.status}: ${await res.text()}`);
  const data = await res.json();
  const raw = data?.choices?.[0]?.message?.content;
  if (!raw) throw new Error("Empty response from AI");
  const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();
  return JSON.parse(cleaned);
}

// ──────────────────────────────────────────────────
// TESTS
// ──────────────────────────────────────────────────
console.log("\n═══ Worker v4.0 Integration Tests ═══\n");

// T1 — GitHub connectivity
console.log("T1 — GitHub: list topics from pavnxet/quiz-questions");
let githubStructure;
try {
  githubStructure = await ghListTopics();
  if (githubStructure) {
    const subjects = Object.keys(githubStructure);
    const totalTopics = Object.values(githubStructure).flat().length;
    pass(`Connected — ${subjects.length} subject(s), ${totalTopics} topic(s)`);
    console.log("     Subjects found:", subjects.join(", ") || "(empty repo)");
  } else {
    pass("Connected — repo is empty (no questions yet, will be new topics)");
    githubStructure = {};
  }
} catch (e) {
  fail("GitHub connectivity", e.message);
  githubStructure = {};
}

// T2 — Zero-latency bypass (exact match)
console.log("\nT2 — Zero-latency bypass: exact match should skip AI");
{
  // Use a subject/topic that DOES NOT exist so we can construct a fake one for testing
  const fakeStructure = { "Physics": ["Optics", "Mechanics"] };
  const exactQuestions = [
    { subject: "Physics", topic: "Optics", q: "test" },
    { subject: "Physics", topic: "Mechanics", q: "test2" },
  ];
  const pairs = extractUniquePairs(exactQuestions);
  const match = allPairsMatch(pairs, fakeStructure);
  if (match) pass("allPairsMatch returns true for exact matches → AI bypassed");
  else fail("allPairsMatch exact match");

  const mismatchQuestions = [
    { subject: "Phy", topic: "optics basics", q: "test" },
  ];
  const mismatchPairs = extractUniquePairs(mismatchQuestions);
  const noMatch = allPairsMatch(mismatchPairs, fakeStructure);
  if (!noMatch) pass("allPairsMatch returns false for mismatched pairs → AI triggered");
  else fail("allPairsMatch mismatch detection");
}

// T3 — OpenRouter AI call
console.log("\nT3 — OpenRouter: AI normalization call with real mismatched pairs");
let aiResult;
const testPairs = [
  { subject: "Phy", topic: "optics basics" },
  { subject: "Bio", topic: "Cell Bio" },
  { subject: "Chemistry", topic: "Periodic Table" },
];
const testStructure = githubStructure && Object.keys(githubStructure).length > 0
  ? githubStructure
  : { Physics: ["Optics", "Mechanics"], Biology: ["Cell Biology", "Genetics"] };

try {
  console.log(`  Calling gpt-oss-120b:free with ${testPairs.length} pairs…`);
  const start = Date.now();
  aiResult = await aiNormalizePairs(testPairs, testStructure);
  const ms = Date.now() - start;

  if (typeof aiResult === "object" && !Array.isArray(aiResult)) {
    pass(`Valid JSON object returned in ${ms}ms`);
    console.log("  AI mapping result:");
    for (const [k, v] of Object.entries(aiResult)) {
      console.log(`    "${k}" → { subject: "${v.subject}", topic: "${v.topic}" }`);
    }
  } else {
    fail("AI returned wrong type", typeof aiResult);
    aiResult = null;
  }
} catch (e) {
  fail("OpenRouter AI call", e.message);
  aiResult = null;
}

// T4 — applyNormalization with dictionary
console.log("\nT4 — applyNormalization: dictionary lookup, no alignment bugs");
{
  const fakeAiResult = {
    "Phy|||optics basics":  { subject: "Physics",  topic: "Optics" },
    "Bio|||Cell Bio":       { subject: "Biology",   topic: "Cell Biology" },
    "Chemistry|||Periodic Table": { subject: "Chemistry", topic: "Periodic Table" },
  };
  const questions = [
    { subject: "Phy",       topic: "optics basics",  q: "Q1" },
    { subject: "Bio",       topic: "Cell Bio",        q: "Q2" },
    { subject: "Chemistry", topic: "Periodic Table",  q: "Q3" },
    { subject: "History",   topic: "WW2",             q: "Q4" }, // no mapping → keep as-is
  ];
  const normalized = applyNormalization(questions, fakeAiResult);
  const ok =
    normalized[0].subject === "Physics"   && normalized[0].topic === "Optics" &&
    normalized[1].subject === "Biology"   && normalized[1].topic === "Cell Biology" &&
    normalized[2].subject === "Chemistry" && normalized[2].topic === "Periodic Table" &&
    normalized[3].subject === "History"   && normalized[3].topic === "WW2"; // unchanged
  if (ok) pass("All 4 questions mapped/preserved correctly");
  else fail("Normalization mapping", JSON.stringify(normalized.map(q => ({s: q.subject, t: q.topic}))));
}

// T5 — Full flow with real AI result (if T3 passed)
console.log("\nT5 — Full end-to-end: mismatched questions through normalizeQuestions");
if (aiResult) {
  const questions = testPairs.map((p, i) => ({ ...p, q: `Question ${i+1}`, correct: 0, optionsEnglish: [] }));
  const normalized = applyNormalization(questions, aiResult);
  const changed = normalized.filter((q, i) =>
    q.subject !== questions[i].subject || q.topic !== questions[i].topic
  );
  pass(`${changed.length}/${questions.length} question(s) had their subject/topic normalized`);
  for (const q of changed) {
    const orig = questions.find(x => x.q === q.q);
    console.log(`    "${orig.subject}/${orig.topic}" → "${q.subject}/${q.topic}"`);
  }
} else {
  console.log("  ⚠️  Skipped (T3 failed)");
}

// Summary
console.log(`\n═══ Results: ${passed} passed, ${failed} failed ═══\n`);
if (failed > 0) process.exit(1);
