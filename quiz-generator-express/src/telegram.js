
export async function tgApi(method, payload = {}) {
  const token = process.env.TELEGRAM_TOKEN;
  try {
    const r = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return r.json();
  } catch (e) {
    console.error(`tgApi ${method} error:`, e.message);
    return { ok: false, description: e.message };
  }
}

export function tgSend(chatId, text, extra = {}) {
  return tgApi("sendMessage", { chat_id: chatId, text, parse_mode: "HTML", ...extra });
}

export async function tgSendDocument(chatId, content, filename, caption) {
  const token = process.env.TELEGRAM_TOKEN;
  try {
    const form = new FormData();
    form.append("chat_id",    String(chatId));
    form.append("parse_mode", "HTML");
    form.append("caption",    (caption || "").slice(0, 1024));
    const blob = new Blob([content], { type: "text/html" });
    form.append("document", blob, filename);
    const r = await fetch(`https://api.telegram.org/bot${token}/sendDocument`, {
      method: "POST",
      body: form,
    });
    return r.json();
  } catch (e) {
    console.error("tgSendDocument error:", e.message);
    return { ok: false, description: e.message };
  }
}

export async function tgGetFileUrl(fileId) {
  const token = process.env.TELEGRAM_TOKEN;
  const res   = await tgApi("getFile", { file_id: fileId });
  if (!res?.result?.file_path) return null;
  return `https://api.telegram.org/file/bot${token}/${res.result.file_path}`;
}

export async function editStatus(chatId, messageId, text) {
  if (!messageId) return;
  return tgApi("editMessageText", { chat_id: chatId, message_id: messageId, text, parse_mode: "HTML" });
}
