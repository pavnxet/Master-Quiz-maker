import os, json, tempfile
from flask import Flask, request, render_template_string, send_file, jsonify
from quiz_generator import load_questions, generate_html, merge_questions
from pathlib import Path

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024   # 100 MB (many files)

UPLOAD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quiz Generator</title>
<style>
:root{--p:#4f46e5;--pd:#3730a3;--s2:#7c3aed;--bg:#f8fafc;--sf:#fff;--b:#e2e8f0;--t:#1e293b;--m:#64748b;--ok:#16a34a;--del:#dc2626}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px}
.card{background:var(--sf);border:1px solid var(--b);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:36px;max-width:580px;width:100%}
h1{color:var(--p);font-size:1.65rem;margin-bottom:4px}
.sub{color:var(--m);font-size:.88rem;margin-bottom:24px}
/* file zones */
.zones{display:flex;flex-direction:column;gap:0}
.zone-wrap{position:relative;margin-bottom:8px}
.zone-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:5px}
.zone-label{font-size:.78rem;font-weight:700;color:var(--m);display:flex;align-items:center;gap:6px}
.badge-num{width:20px;height:20px;border-radius:50%;background:var(--p);color:#fff;font-size:.7rem;display:inline-flex;align-items:center;justify-content:center;font-weight:800}
.remove-btn{background:none;border:none;color:var(--del);cursor:pointer;font-size:1.1rem;padding:0 4px;line-height:1;opacity:.7;transition:.15s}
.remove-btn:hover{opacity:1}
.drop-zone{border:2px dashed var(--b);border-radius:11px;padding:18px 16px;text-align:center;cursor:pointer;transition:.2s;background:var(--bg);min-height:74px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.drop-zone:hover,.drop-zone.over{border-color:var(--p);background:#ede9fe18}
.drop-zone.has-file{border-color:var(--ok);background:#f0fdf4}
.drop-zone input{display:none}
.drop-zone .icon{font-size:1.4rem;margin-bottom:3px}
.drop-zone p{color:var(--m);font-size:.83rem}
.drop-zone p strong{color:var(--p);cursor:pointer}
.file-name{margin-top:4px;font-size:.78rem;font-weight:600;color:var(--ok);word-break:break-all}
/* merge connector */
.merge-connector{display:flex;align-items:center;gap:10px;padding:4px 0;margin-bottom:8px}
.merge-line{flex:1;height:1px;background:var(--b)}
.merge-pill{background:linear-gradient(135deg,var(--p),var(--s2));color:#fff;border-radius:99px;padding:3px 12px;font-size:.73rem;font-weight:800;white-space:nowrap}
/* add file btn */
.add-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;border:2px dashed var(--b);border-radius:10px;background:none;color:var(--p);font-size:.85rem;font-weight:700;cursor:pointer;transition:.2s;margin-top:4px}
.add-btn:hover{border-color:var(--p);background:#ede9fe20}
/* summary badge */
.summary{text-align:center;font-size:.8rem;color:var(--m);margin:10px 0 0}
.summary b{color:var(--t)}
/* main btn */
.btn{display:block;width:100%;background:var(--p);color:#fff;border:none;border-radius:10px;padding:13px;font-size:.95rem;font-weight:700;cursor:pointer;margin-top:18px;transition:.15s}
.btn:hover{background:var(--pd);transform:translateY(-1px)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.error{background:#fee2e2;border:1px solid #fca5a5;color:#dc2626;border-radius:8px;padding:11px 14px;font-size:.87rem;margin-top:12px;display:none}
.spinner{display:none;text-align:center;margin-top:12px;color:var(--m);font-size:.87rem}
.info-box{margin-top:22px;background:var(--bg);border-radius:10px;padding:15px;font-size:.78rem;color:var(--m)}
.info-box strong{color:var(--t)}
.info-box code{display:block;margin-top:7px;white-space:pre;font-size:.71rem;overflow-x:auto;line-height:1.55;background:#f1f5f9;padding:8px;border-radius:6px}
footer{margin-top:20px;font-size:.75rem;color:var(--m);text-align:center}
</style>
</head>
<body>
<div class="card">
  <h1>🎓 Quiz Generator</h1>
  <p class="sub">Upload one or more JSON quiz files → get a fully interactive bilingual HTML quiz. Duplicate questions are removed automatically when merging.</p>

  <form id="upload-form" enctype="multipart/form-data">
    <div class="zones" id="zones-container"></div>

    <button type="button" class="add-btn" id="add-btn" onclick="addZone()">
      ➕ Add Another File
    </button>

    <p class="summary" id="summary" style="display:none"></p>

    <div class="error" id="err"></div>
    <div class="spinner" id="spin">⚙️ Generating quiz…</div>
    <button type="submit" class="btn" id="sbtn" disabled>Generate Quiz HTML</button>
  </form>

  <div class="info-box">
    <strong>Expected JSON format (each file):</strong>
    <code>[
  {
    "qEnglish": "Question text in English",
    "qHindi": "प्रश्न हिंदी में",
    "optionsEnglish": ["A","B","C","D"],
    "optionsHindi":   ["अ","ब","स","द"],
    "correct": 1,
    "explanationEnglish": "Because…",
    "explanationHindi": "क्योंकि…",
    "subject": "Physics",
    "topic": "Optics"
  }
]</code>
    <p style="margin-top:8px">When multiple files are uploaded, duplicate questions (matched by English text) are removed automatically.</p>
  </div>
</div>
<footer>Works offline after download · No data stored · Self-contained HTML</footer>

<script>
let zoneCount = 0;
const COLORS = ['#4f46e5','#7c3aed','#0891b2','#059669','#d97706','#dc2626','#9333ea','#0284c7','#16a34a','#ca8a04'];

function addZone() {
  zoneCount++;
  const idx = zoneCount;
  const color = COLORS[(idx - 1) % COLORS.length];
  const container = document.getElementById('zones-container');

  // Insert merge connector between zones
  if (idx > 1) {
    const conn = document.createElement('div');
    conn.className = 'merge-connector';
    conn.id = 'conn' + idx;
    conn.innerHTML = '<div class="merge-line"></div><div class="merge-pill">+ MERGE</div><div class="merge-line"></div>';
    container.appendChild(conn);
  }

  const wrap = document.createElement('div');
  wrap.className = 'zone-wrap';
  wrap.id = 'wrap' + idx;
  wrap.innerHTML = `
    <div class="zone-header">
      <div class="zone-label">
        <span class="badge-num" style="background:${color}">${idx}</span>
        <span>File ${idx}</span>
      </div>
      ${idx > 1 ? `<button type="button" class="remove-btn" onclick="removeZone(${idx})" title="Remove">✕</button>` : ''}
    </div>
    <div class="drop-zone" id="dz${idx}">
      <div class="icon">📄</div>
      <p>Drop here or <strong onclick="document.getElementById('fi${idx}').click()">browse</strong></p>
      <input type="file" id="fi${idx}" name="file${idx}" accept=".json,.txt"/>
      <div class="file-name" id="fn${idx}"></div>
    </div>`;
  container.appendChild(wrap);

  setupZone(idx);
  checkReady();
}

function removeZone(idx) {
  const wrap = document.getElementById('wrap' + idx);
  const conn = document.getElementById('conn' + idx);
  if (wrap) wrap.remove();
  if (conn) conn.remove();
  checkReady();
}

function setupZone(idx) {
  const dz = document.getElementById('dz' + idx);
  const fi = document.getElementById('fi' + idx);
  const fn = document.getElementById('fn' + idx);
  fi.addEventListener('change', () => {
    if (fi.files[0]) { fn.textContent = '✓ ' + fi.files[0].name; dz.classList.add('has-file'); checkReady(); }
  });
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('over'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('over');
    const f = e.dataTransfer.files[0];
    if (f) {
      const dt = new DataTransfer(); dt.items.add(f); fi.files = dt.files;
      fn.textContent = '✓ ' + f.name; dz.classList.add('has-file'); checkReady();
    }
  });
}

function getLoadedFiles() {
  const files = [];
  for (let i = 1; i <= zoneCount; i++) {
    const fi = document.getElementById('fi' + i);
    if (fi && fi.files[0]) files.push({ idx: i, file: fi.files[0] });
  }
  return files;
}

function checkReady() {
  const loaded = getLoadedFiles();
  const sbtn = document.getElementById('sbtn');
  const summary = document.getElementById('summary');
  sbtn.disabled = loaded.length === 0;
  if (loaded.length > 1) {
    summary.style.display = '';
    summary.innerHTML = `Merging <b>${loaded.length} files</b> → duplicates will be removed`;
    sbtn.textContent = `Merge & Generate Quiz HTML`;
  } else if (loaded.length === 1) {
    summary.style.display = 'none';
    sbtn.textContent = 'Generate Quiz HTML';
  } else {
    summary.style.display = 'none';
    sbtn.textContent = 'Generate Quiz HTML';
  }
}

document.getElementById('upload-form').addEventListener('submit', async e => {
  e.preventDefault();
  const loaded = getLoadedFiles();
  if (!loaded.length) return;

  const err  = document.getElementById('err');
  const spin = document.getElementById('spin');
  const sbtn = document.getElementById('sbtn');
  err.style.display = 'none'; spin.style.display = 'block'; sbtn.disabled = true;

  const fd = new FormData();
  loaded.forEach((f, i) => fd.append('file' + (i + 1), f.file));

  try {
    const r = await fetch('/generate', { method: 'POST', body: fd });
    if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.error || 'Generation failed'); }
    const blob = await r.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a'); a.href = url;
    const base = loaded[0].file.name.replace(/\\.[^.]+$/, '');
    a.download = (loaded.length > 1 ? base + '_merged' : base) + '_quiz.html';
    a.click(); URL.revokeObjectURL(url);
  } catch(ex) {
    err.textContent = ex.message; err.style.display = 'block';
  } finally {
    spin.style.display = 'none'; sbtn.disabled = getLoadedFiles().length === 0;
  }
});

// Start with one zone
addZone();
</script>
</body>
</html>"""


def parse_upload(file_obj):
    content   = file_obj.read().decode("utf-8")
    questions = json.loads(content)
    if not isinstance(questions, list) or not questions:
        raise ValueError("JSON must be a non-empty array.")
    return questions


@app.route("/")
def index():
    return render_template_string(UPLOAD_PAGE)


@app.route("/generate", methods=["POST"])
def generate():
    # Collect all uploaded files: file1, file2, ..., fileN
    # Also support legacy single 'file' key
    all_lists = []
    all_names = []

    # Legacy support
    legacy = request.files.get("file")
    if legacy and legacy.filename:
        try:
            all_lists.append(parse_upload(legacy))
            all_names.append(Path(legacy.filename).stem)
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({"error": f"File error: {e}"}), 400

    # Numbered files: file1, file2, ..., up to 50
    for i in range(1, 51):
        f = request.files.get(f"file{i}")
        if not f or not f.filename:
            continue
        try:
            all_lists.append(parse_upload(f))
            all_names.append(Path(f.filename).stem)
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({"error": f"File {i} error: {e}"}), 400

    if not all_lists:
        return jsonify({"error": "No file uploaded"}), 400

    if len(all_lists) == 1:
        questions = all_lists[0]
        title     = all_names[0].replace("_", " ").title()
        out_name  = all_names[0] + "_quiz.html"
    else:
        questions = merge_questions(*all_lists)
        title     = " + ".join(n.replace("_", " ").title() for n in all_names)
        out_name  = all_names[0] + "_merged_quiz.html"

    html_content = generate_html(questions, title)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    return send_file(tmp_path, as_attachment=True, download_name=out_name, mimetype="text/html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
