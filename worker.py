"""
Cloudflare Workers Python entry point.
Serves the quiz generator as a serverless function.
"""
import json
import html as html_mod
from pathlib import Path
from js import Response, Headers, Object


UPLOAD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quiz Generator</title>
<style>
  :root{--p:#4f46e5;--pg:#3730a3;--bg:#f8fafc;--s:#fff;--b:#e2e8f0;--t:#1e293b;--m:#64748b}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
  .card{background:var(--s);border:1px solid var(--b);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:40px;max-width:520px;width:100%}
  h1{color:var(--p);font-size:1.7rem;margin-bottom:6px}
  p.sub{color:var(--m);font-size:.9rem;margin-bottom:28px}
  .drop-zone{border:2px dashed var(--b);border-radius:12px;padding:40px 20px;text-align:center;cursor:pointer;transition:.2s;background:var(--bg)}
  .drop-zone:hover,.drop-zone.over{border-color:var(--p);background:#ede9fe22}
  .drop-zone input{display:none}
  .drop-zone .icon{font-size:2.5rem;margin-bottom:10px}
  .drop-zone p{color:var(--m);font-size:.9rem}
  .drop-zone p strong{color:var(--p);cursor:pointer}
  #file-name{margin-top:10px;font-size:.85rem;color:var(--p);font-weight:600;min-height:20px}
  .btn{display:block;width:100%;background:var(--p);color:#fff;border:none;border-radius:10px;padding:13px;font-size:1rem;font-weight:700;cursor:pointer;margin-top:20px;transition:.15s}
  .btn:hover{background:var(--pg)}
  .btn:disabled{opacity:.5;cursor:not-allowed}
  .error{background:#fee2e2;border:1px solid #fca5a5;color:#dc2626;border-radius:8px;padding:12px 14px;font-size:.9rem;margin-top:14px;display:none}
  .spinner{display:none;text-align:center;margin-top:14px;color:var(--m);font-size:.9rem}
  .format-box{margin-top:24px;background:var(--bg);border-radius:10px;padding:16px;font-size:.8rem;color:var(--m)}
  .format-box code{display:block;margin-top:8px;white-space:pre;font-size:.75rem;overflow-x:auto;line-height:1.5}
  footer{margin-top:24px;font-size:.78rem;color:var(--m)}
</style>
</head>
<body>
<div class="card">
  <h1>&#127979; Quiz Generator</h1>
  <p class="sub">Upload a JSON quiz file and get a fully interactive HTML quiz page.</p>
  <form id="upload-form" enctype="multipart/form-data">
    <div class="drop-zone" id="drop-zone">
      <div class="icon">&#128196;</div>
      <p>Drop your file here or <strong onclick="document.getElementById('file-input').click()">browse</strong></p>
      <input type="file" id="file-input" name="file" accept=".json,.txt"/>
      <div id="file-name"></div>
    </div>
    <div class="error" id="error-box"></div>
    <div class="spinner" id="spinner">&#9881;&#65039; Generating quiz...</div>
    <button type="submit" class="btn" id="submit-btn" disabled>Generate Quiz HTML</button>
  </form>
  <div class="format-box">
    <strong>Expected JSON format:</strong>
    <code>[{"qEnglish":"Question","optionsEnglish":["A","B","C","D"],"correct":1,"subject":"Physics"}]</code>
  </div>
</div>
<footer>Works offline &middot; No data stored &middot; Self-contained HTML output</footer>
<script>
const dz=document.getElementById('drop-zone'),fi=document.getElementById('file-input'),sb=document.getElementById('submit-btn'),fn=document.getElementById('file-name'),eb=document.getElementById('error-box'),sp=document.getElementById('spinner');
fi.addEventListener('change',()=>{if(fi.files[0]){fn.textContent=fi.files[0].name;sb.disabled=false;}});
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over');});
dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('over');const f=e.dataTransfer.files[0];if(f){fi.files=e.dataTransfer.files;fn.textContent=f.name;sb.disabled=false;}});
document.getElementById('upload-form').addEventListener('submit',async e=>{
  e.preventDefault();eb.style.display='none';sp.style.display='block';sb.disabled=true;
  const fd=new FormData();fd.append('file',fi.files[0]);
  try{
    const r=await fetch('/generate',{method:'POST',body:fd});
    if(!r.ok){const j=await r.json();throw new Error(j.error||'Failed');}
    const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');
    a.href=url;a.download=fi.files[0].name.replace(/\\.\\w+$/,'')+'_quiz.html';a.click();URL.revokeObjectURL(url);
  }catch(err){eb.textContent=err.message;eb.style.display='block';}
  finally{sp.style.display='none';sb.disabled=false;}
});
</script>
</body>
</html>"""


def generate_html(questions, title):
    q_json = json.dumps(questions, ensure_ascii=False)
    title_safe = html_mod.escape(title)
    # Embed the full quiz HTML (same template as quiz_generator.py)
    # Import and delegate to avoid duplication
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from quiz_generator import generate_html as _gen
    return _gen(questions, title)


async def on_fetch(request, env):
    url = request.url
    method = request.method

    # Route: GET /
    if method == "GET" and (url.endswith("/") or url.endswith("/generate") is False):
        headers = Headers.new({"Content-Type": "text/html;charset=UTF-8"}.items())
        return Response.new(UPLOAD_PAGE, headers=headers, status=200)

    # Route: POST /generate
    if method == "POST" and "/generate" in url:
        try:
            form_data = await request.formData()
            file_obj = form_data.get("file")
            if not file_obj:
                headers = Headers.new({"Content-Type": "application/json"}.items())
                return Response.new(json.dumps({"error": "No file uploaded"}), headers=headers, status=400)

            content = await file_obj.text()
            filename = file_obj.name or "quiz"

            try:
                questions = json.loads(content)
            except json.JSONDecodeError as e:
                headers = Headers.new({"Content-Type": "application/json"}.items())
                return Response.new(json.dumps({"error": f"Invalid JSON: {e}"}), headers=headers, status=400)

            if not isinstance(questions, list) or len(questions) == 0:
                headers = Headers.new({"Content-Type": "application/json"}.items())
                return Response.new(json.dumps({"error": "JSON must be a non-empty array"}), headers=headers, status=400)

            import html as html_mod
            title = filename.rsplit(".", 1)[0].replace("_", " ").title()

            # Import and use generate_html from quiz_generator
            import sys, os
            sys.path.insert(0, "/")
            from quiz_generator import generate_html
            html_out = generate_html(questions, title)

            out_name = filename.rsplit(".", 1)[0] + "_quiz.html"
            headers = Headers.new({
                "Content-Type": "text/html;charset=UTF-8",
                "Content-Disposition": f'attachment; filename="{out_name}"',
            }.items())
            return Response.new(html_out, headers=headers, status=200)

        except Exception as e:
            headers = Headers.new({"Content-Type": "application/json"}.items())
            return Response.new(json.dumps({"error": str(e)}), headers=headers, status=500)

    # 404
    headers = Headers.new({"Content-Type": "text/plain"}.items())
    return Response.new("Not found", headers=headers, status=404)
