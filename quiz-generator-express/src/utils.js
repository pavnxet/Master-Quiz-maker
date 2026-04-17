
export function escHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function toBase64(str) {
  return Buffer.from(str, "utf8").toString("base64");
}

export function fromBase64(b64) {
  return Buffer.from(b64.replace(/\n/g, ""), "base64").toString("utf8");
}

export function safeName(s) {
  return (
    String(s || "General")
      .replace(/[/\\:*?"<>|#%]/g, "")
      .trim() || "General"
  );
}

export function dedupKey(q) {
  const en = String(q.qEnglish || "").toLowerCase().replace(/\s+/g, " ").trim();
  const hi = String(q.qHindi   || "").toLowerCase().replace(/\s+/g, " ").trim();
  if (en && hi) return `${en}|||${hi}`;
  if (en)       return `en:${en}`;
  if (hi)       return `hi:${hi}`;
  return `opts:${JSON.stringify(q.optionsEnglish || q.optionsHindi || [])}`;
}

export function validateQuestions(questions) {
  return questions.filter(
    (q) =>
      q !== null &&
      typeof q === "object" &&
      !Array.isArray(q) &&
      (q.qEnglish || q.qHindi || q.question || q.text || q.q),
  );
}
