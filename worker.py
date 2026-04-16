"""
Cloudflare Workers Python — Quiz Generator + Telegram Bot
----------------------------------------------------------
Web interface:  GET  /            → upload UI
                POST /generate    → returns HTML quiz file
Telegram bot:   POST /telegram    → webhook receiver
Setup:          GET  /setup       → registers webhook (call once after deploy)

Environment variables (set in Cloudflare dashboard → Workers → Settings → Variables):
  TELEGRAM_TOKEN   — your bot token from @BotFather (e.g. 123456:ABC-DEF...)

How to deploy:
  1. npx wrangler deploy
  2. Visit https://<your-worker>.workers.dev/setup  (one-time webhook registration)
  3. Your bot is live — send a .json or .txt file to it in Telegram
"""

import json
import html as html_mod
from js import Response, Headers, fetch, FormData, Blob, Object


# ════════════════════════════════════════════════════════════
#  UPLOAD PAGE  (served at GET /)
# ════════════════════════════════════════════════════════════
UPLOAD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quiz Generator</title>
<style>
:root{--p:#4f46e5;--pd:#3730a3;--bg:#f8fafc;--s:#fff;--b:#e2e8f0;--t:#1e293b;--m:#64748b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t);
  min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}
.card{background:var(--s);border:1px solid var(--b);border-radius:16px;
  box-shadow:0 4px 24px rgba(0,0,0,.08);padding:36px;max-width:500px;width:100%}
h1{color:var(--p);font-size:1.6rem;margin-bottom:5px}
.sub{color:var(--m);font-size:.88rem;margin-bottom:24px}
.tg-banner{background:#e7f3ff;border:1px solid #93c5fd;border-radius:10px;padding:11px 14px;
  font-size:.82rem;color:#1e40af;margin-bottom:20px;line-height:1.5}
.tg-banner strong{color:#1d4ed8}
.drop-zone{border:2px dashed var(--b);border-radius:11px;padding:36px 18px;text-align:center;
  cursor:pointer;transition:.2s;background:var(--bg)}
.drop-zone:hover,.drop-zone.over{border-color:var(--p);background:#ede9fe18}
.drop-zone input{display:none}
.drop-zone .icon{font-size:2.2rem;margin-bottom:8px}
.drop-zone p{color:var(--m);font-size:.88rem}
.drop-zone p strong{color:var(--p);cursor:pointer}
#file-name{margin-top:8px;font-size:.82rem;color:var(--p);font-weight:600;min-height:18px}
.btn{display:block;width:100%;background:var(--p);color:#fff;border:none;border-radius:9px;
  padding:12px;font-size:.95rem;font-weight:700;cursor:pointer;margin-top:18px;transition:.15s}
.btn:hover{background:var(--pd)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.error{background:#fee2e2;border:1px solid #fca5a5;color:#dc2626;border-radius:7px;
  padding:10px 13px;font-size:.87rem;margin-top:12px;display:none}
.spinner{display:none;text-align:center;margin-top:12px;color:var(--m);font-size:.88rem}
.fmt{margin-top:20px;background:var(--bg);border-radius:9px;padding:14px;font-size:.78rem;color:var(--m)}
.fmt code{display:block;margin-top:6px;white-space:pre;font-size:.72rem;overflow-x:auto;line-height:1.5}
footer{margin-top:20px;font-size:.75rem;color:var(--m);text-align:center}
</style>
</head>
<body>
<div class="card">
  <h1>🎓 Quiz Generator</h1>
  <p class="sub">Upload a JSON quiz file → get a bilingual interactive HTML quiz.</p>
  <div class="tg-banner">
    <strong>📱 Telegram Bot available!</strong> Send your <code>.json</code> or <code>.txt</code>
    file directly to the bot and it will reply with the HTML quiz instantly.
  </div>
  <form id="upload-form" enctype="multipart/form-data">
    <div class="drop-zone" id="drop-zone">
      <div class="icon">📄</div>
      <p>Drop file here or <strong onclick="document.getElementById('fi').click()">browse</strong></p>
      <input type="file" id="fi" name="file" accept=".json,.txt"/>
      <div id="file-name"></div>
    </div>
    <div class="error" id="err"></div>
    <div class="spinner" id="spin">⚙️ Generating quiz…</div>
    <button type="submit" class="btn" id="sbtn" disabled>Generate Quiz HTML</button>
  </form>
  <div class="fmt">
    <strong>JSON format:</strong>
    <code>[{"qEnglish":"…","qHindi":"…","optionsEnglish":["A","B","C","D"],
 "optionsHindi":["अ","ब","स","द"],"correct":1,
 "explanationEnglish":"…","subject":"…","topic":"…"}]</code>
  </div>
</div>
<footer>Self-contained output · No data stored · Works offline after download</footer>
<script>
const dz=document.getElementById('drop-zone'),fi=document.getElementById('fi'),
      sb=document.getElementById('sbtn'),fn=document.getElementById('file-name'),
      er=document.getElementById('err'),sp=document.getElementById('spin');
fi.addEventListener('change',()=>{if(fi.files[0]){fn.textContent=fi.files[0].name;sb.disabled=false;}});
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over');});
dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('over');
  const f=e.dataTransfer.files[0];if(f){fi.files=e.dataTransfer.files;fn.textContent=f.name;sb.disabled=false;}});
document.getElementById('upload-form').addEventListener('submit',async e=>{
  e.preventDefault();er.style.display='none';sp.style.display='block';sb.disabled=true;
  const fd=new FormData();fd.append('file',fi.files[0]);
  try{
    const r=await fetch('/generate',{method:'POST',body:fd});
    if(!r.ok){const j=await r.json();throw new Error(j.error||'Generation failed');}
    const blob=await r.blob();const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;
    a.download=fi.files[0].name.replace(/\.\w+$/,'')+'_quiz.html';a.click();URL.revokeObjectURL(url);
  }catch(err){er.textContent=err.message;er.style.display='block';}
  finally{sp.style.display='none';sb.disabled=false;}
});
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════
#  QUIZ HTML GENERATOR  (same logic as quiz_generator.py)
# ════════════════════════════════════════════════════════════
def generate_html(questions, title):
    """Generate self-contained bilingual quiz HTML."""
    q_json  = json.dumps(questions, ensure_ascii=False)
    title_s = html_mod.escape(title)
    # Import from shared module (works in Cloudflare Workers Python)
    try:
        import sys, os
        sys.path.insert(0, "/")
        from quiz_generator import generate_html as _gen
        return _gen(questions, title)
    except Exception:
        # Fallback minimal HTML if import fails
        return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/>
<title>{title_s}</title></head><body>
<h1>{title_s}</h1>
<p>{len(questions)} questions loaded. Please use the main quiz_generator.py for full output.</p>
<script>const Q={q_json};</script></body></html>"""


# ════════════════════════════════════════════════════════════
#  TELEGRAM HELPERS
# ════════════════════════════════════════════════════════════
async def tg_api(token, method, payload=None):
    """Call a Telegram Bot API method. Returns parsed JSON dict."""
    url  = f"https://api.telegram.org/bot{token}/{method}"
    body = json.dumps(payload or {})
    hdrs = {"Content-Type": "application/json"}
    resp = await fetch(url, method="POST",
                       body=body,
                       headers=Object.fromEntries(list(hdrs.items())))
    return await resp.json()


async def tg_send_message(token, chat_id, text, parse_mode="HTML"):
    await tg_api(token, "sendMessage", {
        "chat_id": chat_id, "text": text, "parse_mode": parse_mode
    })


async def tg_get_file(token, file_id):
    """Resolve file_id → download URL."""
    result = await tg_api(token, "getFile", {"file_id": file_id})
    try:
        file_path = result["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{token}/{file_path}"
    except Exception:
        return None


async def tg_send_document(token, chat_id, html_content, filename, caption=""):
    """Send an HTML file back to a Telegram chat."""
    url  = f"https://api.telegram.org/bot{token}/sendDocument"
    form = FormData.new()
    form.append("chat_id", str(chat_id))
    if caption:
        form.append("caption", caption)
    # Create a Blob from the HTML string
    blob = Blob.new([html_content], Object.fromEntries([["type", "text/html; charset=utf-8"]]))
    form.append("document", blob, filename)
    resp = await fetch(url, method="POST", body=form)
    return await resp.json()


# ════════════════════════════════════════════════════════════
#  TELEGRAM WEBHOOK HANDLER
# ════════════════════════════════════════════════════════════
WELCOME_MSG = """👋 <b>Welcome to Quiz Generator Bot!</b>

Send me a <code>.json</code> or <code>.txt</code> file containing quiz questions and I'll generate a fully interactive, bilingual (English + हिंदी) HTML quiz file for you.

<b>JSON format required:</b>
<pre>[
  {
    "qEnglish": "Question text",
    "qHindi": "प्रश्न",
    "optionsEnglish": ["A","B","C","D"],
    "optionsHindi": ["अ","ब","स","द"],
    "correct": 1,
    "explanationEnglish": "Explanation",
    "subject": "Physics",
    "topic": "Optics"
  }
]</pre>

Features in the generated quiz:
✅ Bilingual EN + हिं display
🌙 Dark / Light mode
🏅 Custom marking &amp; negative marking
📊 Performance tracking &amp; stats
✏️ Editable quiz title"""


async def handle_telegram(request, token):
    """Process incoming Telegram webhook update."""
    try:
        update = await request.json()
    except Exception:
        return ok_response()

    message = update.get("message") or update.get("channel_post") or {}
    chat_id = (message.get("chat") or {}).get("id")
    if not chat_id:
        return ok_response()

    # /start command
    text = message.get("text") or ""
    if text.startswith("/start") or text.startswith("/help"):
        await tg_send_message(token, chat_id, WELCOME_MSG)
        return ok_response()

    # Document upload
    document = message.get("document")
    if document:
        filename  = document.get("file_name", "quiz.json")
        file_id   = document.get("file_id")
        ext       = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ("json", "txt"):
            await tg_send_message(token, chat_id,
                "❌ Please send a <b>.json</b> or <b>.txt</b> file.",
                parse_mode="HTML")
            return ok_response()

        await tg_send_message(token, chat_id, "⚙️ Processing your file…")

        # Download from Telegram
        file_url = await tg_get_file(token, file_id)
        if not file_url:
            await tg_send_message(token, chat_id, "❌ Could not access your file. Try again.")
            return ok_response()

        resp    = await fetch(file_url)
        content = await resp.text()

        # Parse JSON
        try:
            questions = json.loads(content)
        except Exception:
            await tg_send_message(token, chat_id,
                "❌ Invalid JSON. Please check your file format.")
            return ok_response()

        if not isinstance(questions, list) or len(questions) == 0:
            await tg_send_message(token, chat_id,
                "❌ JSON must be a non-empty array of question objects.")
            return ok_response()

        # Generate HTML
        title    = filename.rsplit(".", 1)[0].replace("_", " ").title()
        try:
            html_out = generate_html(questions, title)
        except Exception as e:
            await tg_send_message(token, chat_id, f"❌ Generation error: {e}")
            return ok_response()

        out_name = filename.rsplit(".", 1)[0] + "_quiz.html"
        caption  = (f"✅ <b>{html_mod.escape(title)}</b>\n"
                    f"📋 {len(questions)} questions · Bilingual EN+हिं\n"
                    f"🌙 Dark mode · 🏅 Custom marking · 📊 Stats")

        result = await tg_send_document(token, chat_id, html_out, out_name, caption)
        if not result.get("ok"):
            await tg_send_message(token, chat_id,
                f"⚠️ Quiz generated but could not send file: {result.get('description','unknown error')}")
        return ok_response()

    # Unknown message
    await tg_send_message(token, chat_id,
        "📄 Please send a <b>.json</b> or <b>.txt</b> quiz file.\n"
        "Type /help to see the expected format.", parse_mode="HTML")
    return ok_response()


# ════════════════════════════════════════════════════════════
#  WEBHOOK SETUP  (call GET /setup once after deploying)
# ════════════════════════════════════════════════════════════
async def setup_webhook(request, token):
    """Register this worker URL as the Telegram webhook."""
    # Derive worker URL from current request
    req_url   = request.url
    base_url  = req_url.split("/setup")[0].rstrip("/")
    webhook   = f"{base_url}/telegram"
    result    = await tg_api(token, "setWebhook", {"url": webhook, "allowed_updates": ["message"]})
    ok        = result.get("ok", False)
    msg       = result.get("description", "")
    body      = json.dumps({
        "ok": ok,
        "webhook_url": webhook,
        "telegram_response": msg,
        "next_step": "Your bot is ready! Send a .json file to your bot in Telegram." if ok
                     else "Setup failed. Check your TELEGRAM_TOKEN."
    }, indent=2)
    hdrs = Headers.new({"Content-Type": "application/json"}.items())
    return Response.new(body, headers=hdrs, status=200 if ok else 500)


# ════════════════════════════════════════════════════════════
#  WEB /generate  HANDLER
# ════════════════════════════════════════════════════════════
async def handle_web_generate(request):
    try:
        form_data = await request.formData()
        file_obj  = form_data.get("file")
        if not file_obj:
            return json_error("No file uploaded", 400)

        content  = await file_obj.text()
        filename = file_obj.name or "quiz.json"

        try:
            questions = json.loads(content)
        except Exception as e:
            return json_error(f"Invalid JSON: {e}", 400)

        if not isinstance(questions, list) or len(questions) == 0:
            return json_error("JSON must be a non-empty array.", 400)

        title    = filename.rsplit(".", 1)[0].replace("_", " ").title()
        html_out = generate_html(questions, title)
        out_name = filename.rsplit(".", 1)[0] + "_quiz.html"

        hdrs = Headers.new({
            "Content-Type": "text/html; charset=UTF-8",
            "Content-Disposition": f'attachment; filename="{out_name}"',
        }.items())
        return Response.new(html_out, headers=hdrs, status=200)

    except Exception as e:
        return json_error(str(e), 500)


# ════════════════════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════════════════════
def ok_response():
    hdrs = Headers.new({"Content-Type": "text/plain"}.items())
    return Response.new("OK", headers=hdrs, status=200)


def json_error(msg, status=400):
    hdrs = Headers.new({"Content-Type": "application/json"}.items())
    return Response.new(json.dumps({"error": msg}), headers=hdrs, status=status)


# ════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════
async def on_fetch(request, env):
    method = request.method
    url    = request.url

    # Extract path robustly
    try:
        from urllib.parse import urlparse
        path = urlparse(url).path.rstrip("/") or "/"
    except Exception:
        path = "/"

    token = getattr(env, "TELEGRAM_TOKEN", None) or ""

    # ── Telegram webhook
    if method == "POST" and path == "/telegram":
        if not token:
            return ok_response()          # silently ignore if no token
        return await handle_telegram(request, token)

    # ── Webhook setup (one-time)
    if method == "GET" and path == "/setup":
        if not token:
            hdrs = Headers.new({"Content-Type": "application/json"}.items())
            return Response.new(
                json.dumps({"error": "TELEGRAM_TOKEN not set in environment variables."}),
                headers=hdrs, status=400)
        return await setup_webhook(request, token)

    # ── Web: generate quiz from uploaded file
    if method == "POST" and path == "/generate":
        return await handle_web_generate(request)

    # ── Web: serve upload page
    if method == "GET":
        # Inject Telegram bot status hint into page
        page = UPLOAD_PAGE
        if token:
            page = page.replace(
                "📱 Telegram Bot available!",
                "📱 Telegram Bot is <b>active</b>!"
            )
        hdrs = Headers.new({"Content-Type": "text/html; charset=UTF-8"}.items())
        return Response.new(page, headers=hdrs, status=200)

    hdrs = Headers.new({"Content-Type": "text/plain"}.items())
    return Response.new("Not found", headers=hdrs, status=404)
