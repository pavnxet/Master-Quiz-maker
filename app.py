import os
import json
import tempfile
from flask import Flask, request, render_template_string, send_file, jsonify
from quiz_generator import load_questions, generate_html
from pathlib import Path

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

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
  .btn:hover{background:var(--pg);transform:translateY(-1px)}
  .btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
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
    <code>[
  {
    "qEnglish": "Question text",
    "qHindi": "प्रश्न",
    "optionsEnglish": ["A","B","C","D"],
    "optionsHindi": ["अ","ब","स","द"],
    "correct": 1,
    "explanationEnglish": "...",
    "subject": "Physics",
    "topic": "Optics"
  }
]</code>
  </div>
</div>
<footer>Works offline · No data stored · Self-contained HTML output</footer>

<script>
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const submitBtn = document.getElementById('submit-btn');
const fileName = document.getElementById('file-name');
const errorBox = document.getElementById('error-box');
const spinner = document.getElementById('spinner');

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) { fileName.textContent = fileInput.files[0].name; submitBtn.disabled = false; }
});
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault(); dropZone.classList.remove('over');
  const file = e.dataTransfer.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; fileName.textContent = file.name; submitBtn.disabled = false; }
});

document.getElementById('upload-form').addEventListener('submit', async e => {
  e.preventDefault();
  errorBox.style.display = 'none';
  spinner.style.display = 'block';
  submitBtn.disabled = true;
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  try {
    const resp = await fetch('/generate', { method: 'POST', body: fd });
    if (!resp.ok) {
      const j = await resp.json();
      throw new Error(j.error || 'Generation failed');
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const base = fileInput.files[0].name.replace(/\\.\\w+$/, '');
    a.download = base + '_quiz.html';
    a.click();
    URL.revokeObjectURL(url);
  } catch(err) {
    errorBox.textContent = err.message;
    errorBox.style.display = 'block';
  } finally {
    spinner.style.display = 'none';
    submitBtn.disabled = false;
  }
});
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(UPLOAD_PAGE)

@app.route("/generate", methods=["POST"])
def generate():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    content = f.read().decode("utf-8")
    try:
        questions = json.loads(content)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    if not isinstance(questions, list) or len(questions) == 0:
        return jsonify({"error": "JSON must be a non-empty array of question objects"}), 400

    title = Path(f.filename).stem.replace("_", " ").title()
    html_content = generate_html(questions, title)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    out_name = Path(f.filename).stem + "_quiz.html"
    return send_file(
        tmp_path,
        as_attachment=True,
        download_name=out_name,
        mimetype="text/html"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
