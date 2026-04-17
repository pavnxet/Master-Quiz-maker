// Auto-extracted from worker_v5.0.js — do not edit manually
const UPLOAD_PAGE = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quiz Generator</title>
<style>
:root{--p:#4f46e5;--pd:#3730a3;--bg:#f8fafc;--s:#fff;--b:#e2e8f0;--t:#1e293b;--m:#64748b;--err:#dc2626}
body.dark{--bg:#0f172a;--s:#1e293b;--b:#334155;--t:#f1f5f9;--m:#94a3b8}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--t);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;transition:background .2s,color .2s}
.card{background:var(--s);border:1px solid var(--b);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:36px;max-width:540px;width:100%;position:relative}
h1{color:var(--p);font-size:1.6rem;margin-bottom:5px}
.sub{color:var(--m);font-size:.88rem;margin-bottom:22px}
.dark-toggle{position:absolute;top:18px;right:18px;background:none;border:1px solid var(--b);border-radius:50%;width:32px;height:32px;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;color:var(--t);transition:.15s}
.dark-toggle:hover{background:var(--b)}
.tg-banner{background:#e7f3ff;border:1px solid #93c5fd;border-radius:10px;padding:11px 14px;font-size:.82rem;color:#1e40af;margin-bottom:18px;line-height:1.5}
body.dark .tg-banner{background:#1e3a5f;border-color:#3b82f6;color:#93c5fd}
.drop-zone{border:2px dashed var(--b);border-radius:11px;padding:32px 18px;text-align:center;cursor:pointer;transition:.2s;background:var(--bg);user-select:none}
.drop-zone:hover,.drop-zone.over{border-color:var(--p);background:#ede9fe18}
.drop-zone .icon{font-size:2.2rem;margin-bottom:8px;pointer-events:none}
.drop-zone p{color:var(--m);font-size:.88rem;pointer-events:none}
.browse-lbl{color:var(--p);font-weight:700;text-decoration:underline;cursor:pointer;pointer-events:auto}
#fi{display:none}
#file-list{margin-top:10px;text-align:left;pointer-events:auto}
.ftag{display:inline-flex;align-items:center;gap:5px;background:#ede9fe;border-radius:99px;padding:3px 10px;margin:3px;font-size:.78rem;color:var(--p)}
body.dark .ftag{background:#312e81;color:#a5b4fc}
.ftag .qcount{font-size:.72rem;opacity:.75}
.ftag button{background:none;border:none;cursor:pointer;color:var(--p);font-size:.9rem;line-height:1;padding:0;pointer-events:auto}
.merge-note{margin-top:8px;font-size:.78rem;color:var(--m);text-align:center;display:none}
.dbstats{margin-top:14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px}
.dbstat{background:var(--bg);border:1px solid var(--b);border-radius:9px;padding:10px;text-align:center}
.dbstat .v{font-size:1.3rem;font-weight:800;color:var(--p)}
.dbstat .l{font-size:.7rem;color:var(--m);margin-top:2px}
.btn{display:block;width:100%;background:var(--p);color:#fff;border:none;border-radius:9px;padding:12px;font-size:.95rem;font-weight:700;cursor:pointer;margin-top:18px;transition:.15s}
.btn:hover{background:var(--pd)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.error{background:#fee2e2;border:1px solid #fca5a5;color:var(--err);border-radius:7px;padding:10px 13px;font-size:.87rem;margin-top:12px;display:none}
.spinner{display:none;text-align:center;margin-top:12px;color:var(--m);font-size:.88rem}
.prog-wrap{display:none;margin-top:14px}
.prog-header{display:flex;justify-content:space-between;font-size:.78rem;color:var(--m);margin-bottom:5px}
.prog-track{background:var(--b);border-radius:99px;height:9px;overflow:hidden}
.prog-bar{height:100%;width:0%;border-radius:99px;background:linear-gradient(90deg,var(--p),#818cf8);transition:width .45s ease,background .3s}
.prog-stage{font-size:.73rem;color:var(--m);margin-top:5px;text-align:center;min-height:1em}
.fmt{margin-top:20px;background:var(--bg);border-radius:9px;padding:14px;font-size:.78rem;color:var(--m)}
.fmt code{display:block;margin-top:6px;white-space:pre;font-size:.71rem;overflow-x:auto;line-height:1.5;color:var(--m)}
footer{margin-top:20px;font-size:.75rem;color:var(--m);text-align:center}
.qbank-card{margin-top:20px;background:var(--s);border:1px solid var(--b);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:28px;max-width:540px;width:100%}
.qbank-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.qbank-hdr strong{font-size:.97rem;color:var(--t)}
.qbank-hdr span{font-size:.75rem;color:var(--m)}
.qbank-subject{background:var(--bg);border:1px solid var(--b);border-radius:9px;margin-bottom:8px;overflow:hidden}
.qbank-subj-hd{display:flex;align-items:center;justify-content:space-between;padding:10px 13px;cursor:pointer;user-select:none;font-weight:600;font-size:.86rem;color:var(--t)}
.qbank-subj-hd:hover{background:var(--b)}
.qbank-subj-hd .arrow{transition:.2s;display:inline-block;font-style:normal}
.qbank-subj-bd{padding:4px 13px 10px;display:none}
.qbank-subj-bd.open{display:block}
.qbank-topic-row{display:flex;align-items:center;justify-content:space-between;padding:5px 0;font-size:.81rem;color:var(--t);border-bottom:1px solid var(--b)}
.qbank-topic-row:last-child{border-bottom:none}
.qbank-dl-btn{background:var(--p);color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:.7rem;font-weight:600;cursor:pointer;white-space:nowrap;flex-shrink:0}
.qbank-dl-btn:hover{background:var(--pd)}
.qbank-empty{font-size:.83rem;color:var(--m);text-align:center;padding:10px 0}
.save-toggle{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:.84rem;color:var(--t);cursor:pointer;user-select:none}
.save-toggle input[type=checkbox]{accent-color:var(--p);width:15px;height:15px;cursor:pointer;flex-shrink:0}
.save-toggle .nosave-hint{margin-left:auto;font-size:.72rem;color:var(--m);font-style:italic;display:none}
</style>
</head>
<body>
<div class="card">
  <button class="dark-toggle" id="dk" title="Toggle dark mode">🌙</button>
  <h1>🎓 Quiz Generator</h1>
  <p class="sub">Upload one or more JSON quiz files — merge &amp; generate an interactive bilingual HTML quiz.</p>
  <div class="tg-banner">
    📱 <strong>Telegram Bot:</strong> Send your <code>.json</code> file to get the quiz instantly. Use <code>/topics</code> to browse the question bank, <code>/download Subject | Topic</code> to get a quiz, or <code>/mystats</code> for your history.
  </div>

  <input type="file" id="fi" accept=".json,.txt" multiple/>

  <div class="drop-zone" id="dz">
    <div class="icon">📂</div>
    <p>Drop files here or <label for="fi" class="browse-lbl">click to browse</label></p>
    <div id="file-list"></div>
  </div>

  <div class="merge-note" id="mn">✨ Multiple files will be merged into one quiz</div>

  <label class="save-toggle">
    <input type="checkbox" id="save-to-bank" checked/>
    <span>💾 Save to Question Bank <span style="font-weight:400;color:var(--m)">(public GitHub repo)</span></span>
    <span class="nosave-hint" id="nosave-hint">⚡ Temp mode — no GitHub sync</span>
  </label>

  <div id="dbstats-wrap"></div>
  <div class="error" id="err"></div>
  <div class="spinner" id="sp">⚙️ Reading &amp; generating quiz…</div>
  <div class="prog-wrap" id="prog-wrap">
    <div class="prog-header">
      <span id="prog-label">Processing…</span>
      <span id="prog-pct">0%</span>
    </div>
    <div class="prog-track"><div class="prog-bar" id="prog-bar"></div></div>
    <div class="prog-stage" id="prog-stage"></div>
  </div>
  <button class="btn" id="sb" disabled>⬇️ Generate &amp; Download Quiz HTML</button>

  <div class="fmt">
    <strong>JSON format:</strong>
    <code>[{
  "qEnglish":"Question?", "qHindi":"प्रश्न?",
  "optionsEnglish":["A","B","C","D"],
  "optionsHindi":["अ","ब","स","द"],
  "correct":1,
  "explanationEnglish":"…", "explanationHindi":"…",
  "subject":"Physics", "topic":"Optics",
  "imageUrl":"https://…"  // optional image
}]

Match-type extra fields:
  "matchItemsEnglish":[["A. Transparent","i. Clear water"],…],
  "matchItemsHindi":[["A. पारदर्शी","i. साफ पानी"],…]</code>
  </div>
</div>
<footer>Self-contained output · No data stored client-side · Works fully offline after download</footer>

<div class="qbank-card" id="qbank-card">
  <div class="qbank-hdr">
    <strong>📚 Question Bank</strong>
    <span id="qbank-status">Loading…</span>
  </div>
  <div id="qbank-tree"><div class="qbank-empty" style="color:var(--m)">Fetching…</div></div>
</div>

<script>
function escQ(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}

async function loadQBank(){
  const tree=document.getElementById('qbank-tree');
  const status=document.getElementById('qbank-status');
  try{
    const r=await fetch('/api/browse');
    if(!r.ok){
      if(r.status===503){document.getElementById('qbank-card').style.display='none';return;}
      throw new Error('HTTP '+r.status);
    }
    const data=await r.json();
    const structure=data.structure||{};
    const subjects=Object.keys(structure).sort();
    if(!subjects.length){
      tree.innerHTML='<div class="qbank-empty">No questions stored yet — upload a .json file to start building the bank!</div>';
      status.textContent='Empty';return;
    }
    status.textContent=subjects.length+' subject'+(subjects.length!==1?'s':'')+' · '+data.totalTopics+' topic'+(data.totalTopics!==1?'s':'');
    tree.innerHTML=subjects.map(subj=>{
      const topics=(structure[subj]||[]).sort();
      const tid='qbs-'+subj.replace(/\\W/g,'_');
      return '<div class="qbank-subject">'+
        '<div class="qbank-subj-hd" data-tid="'+tid+'">'+
          '<span>📖 '+escQ(subj)+'</span>'+
          '<span><span class="arrow" id="arr-'+tid+'">▶</span> '+topics.length+' topic'+(topics.length!==1?'s':'')+'</span>'+
        '</div>'+
        '<div class="qbank-subj-bd" id="'+tid+'">'+
          topics.map(t=>'<div class="qbank-topic-row">'+
            '<span>'+escQ(t)+'</span>'+
            '<button class="qbank-dl-btn" data-subject="'+escQ(subj)+'" data-topic="'+escQ(t)+'">⬇ Download</button>'+
          '</div>').join('')+
        '</div>'+
      '</div>';
    }).join('');

    // Wire subject toggles
    tree.querySelectorAll('.qbank-subj-hd').forEach(hd=>{
      hd.addEventListener('click',()=>{
        const id=hd.dataset.tid;
        const bd=document.getElementById(id);
        const arr=document.getElementById('arr-'+id);
        const open=bd.classList.toggle('open');
        if(arr)arr.textContent=open?'▼':'▶';
      });
    });
    // Wire download buttons
    tree.querySelectorAll('.qbank-dl-btn').forEach(btn=>{
      btn.addEventListener('click',()=>dlTopic(btn.dataset.subject,btn.dataset.topic,btn));
    });
  }catch(e){
    tree.innerHTML='<div class="qbank-empty">Could not load question bank.</div>';
    status.textContent='Error';
  }
}

async function dlTopic(subject,topic,btn){
  const orig=btn.textContent;btn.textContent='⏳';btn.disabled=true;
  try{
    const r=await fetch('/api/download?subject='+encodeURIComponent(subject)+'&topic='+encodeURIComponent(topic));
    if(!r.ok){const j=await r.json().catch(()=>({}));alert(j.error||'Download failed');return;}
    const blob=await r.blob();
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    const cd=r.headers.get('Content-Disposition')||'';
    const m=cd.match(/filename="([^"]+)"/);
    a.download=m?m[1]:subject+'_'+topic+'_quiz.html';
    a.click();URL.revokeObjectURL(url);
  }finally{btn.textContent=orig;btn.disabled=false;}
}

loadQBank();

// Dark mode
function applyDark(on){document.body.classList.toggle('dark',on);document.getElementById('dk').textContent=on?'☀️':'🌙';localStorage.setItem('qg_theme',on?'dark':'light');}
function toggleDark(){applyDark(!document.body.classList.contains('dark'));}
document.getElementById('dk').addEventListener('click',toggleDark);
(function initDark(){const s=localStorage.getItem('qg_theme');if(s==='dark')applyDark(true);else if(s==='light')applyDark(false);else if(window.matchMedia('(prefers-color-scheme:dark)').matches)applyDark(true);})();

// File handling
const dz=document.getElementById('dz'),fi=document.getElementById('fi'),
      sb=document.getElementById('sb'),fl=document.getElementById('file-list'),
      er=document.getElementById('err'),sp=document.getElementById('sp'),
      mn=document.getElementById('mn');
let selectedFiles=[],fileCounts={};

dz.addEventListener('click',e=>{
  if(e.target.tagName==='LABEL'||e.target.tagName==='BUTTON'||e.target.closest('.ftag'))return;
  fi.click();
});

function renderList(){
  fl.innerHTML=selectedFiles.map((f,i)=>
    '<span class="ftag">📄 '+f.name+
    (fileCounts[f.name]?' <span class="qcount">('+fileCounts[f.name]+'q)</span>':'')+
    ' <button data-idx="'+i+'">✕</button></span>'
  ).join('');
  // Wire remove buttons
  fl.querySelectorAll('button[data-idx]').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const i=parseInt(btn.dataset.idx);
      const f=selectedFiles.splice(i,1)[0];
      delete fileCounts[f.name];
      renderList();
    });
  });
  sb.disabled=!selectedFiles.length;
  mn.style.display=selectedFiles.length>1?'block':'none';
}

async function addFiles(files){
  for(const f of Array.from(files)){
    if(selectedFiles.find(x=>x.name===f.name))continue;
    selectedFiles.push(f);
    try{const d=JSON.parse(await f.text());if(Array.isArray(d))fileCounts[f.name]=d.length;}catch(e){}
  }
  renderList();
}
fi.addEventListener('change',async()=>{await addFiles(fi.files);fi.value='';});
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over');});
dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
dz.addEventListener('drop',async e=>{e.preventDefault();dz.classList.remove('over');await addFiles(e.dataTransfer.files);});

async function readJson(file){
  return new Promise((res,rej)=>{
    const r=new FileReader();
    r.onload=e=>{try{const d=JSON.parse(e.target.result);if(!Array.isArray(d))throw new Error('Not a JSON array');res(d);}catch(ex){rej(new Error(file.name+': '+ex.message));}};
    r.onerror=()=>rej(new Error('Could not read '+file.name));
    r.readAsText(file,'utf-8');
  });
}

// Show/hide temp-mode hint when checkbox is toggled
const saveChk=document.getElementById('save-to-bank');
const nosaveHint=document.getElementById('nosave-hint');
saveChk.addEventListener('change',()=>{
  nosaveHint.style.display=saveChk.checked?'none':'inline';
  // [H1] textContent does not decode HTML entities — use plain & not &amp;
  sp.textContent=saveChk.checked?'⚙️ Reading & generating quiz…':'⚡ Generating temporary quiz (no GitHub sync)…';
});

// Progress bar controller
// [M3] Pass saveToBank so AI stage is hidden when save is disabled
function startProgress(saveToBank){
  const wrap=document.getElementById('prog-wrap'),bar=document.getElementById('prog-bar'),
    lbl=document.getElementById('prog-label'),pct=document.getElementById('prog-pct'),
    stg=document.getElementById('prog-stage');
  // AI + bank stages only shown when save is on
  const ALL_STAGES=[
    {p:15,l:'Reading file…',s:'⏳ Parsing questions'},
    {p:35,l:'Checking question bank…',s:'🔍 Fetching GitHub taxonomy',bankOnly:true},
    {p:62,l:'AI normalizing topics…',s:'🤖 Talking to gpt-oss-120b',bankOnly:true},
    {p:82,l:'Building quiz…',s:'⚙️ Applying topic mapping'},
    {p:95,l:'Almost there…',s:'📦 Generating HTML'},
  ];
  const STAGES=ALL_STAGES.filter(s=>!s.bankOnly||saveToBank);
  // Re-distribute percentages evenly when stages are skipped
  const n=STAGES.length;
  STAGES.forEach((s,i)=>{s.p=Math.round(15+(80/(n-1))*i)||(15+80);});
  STAGES[STAGES.length-1].p=95;
  wrap.style.display='block';bar.style.background='';
  let i=0;
  const iv=setInterval(()=>{
    if(i>=STAGES.length){clearInterval(iv);return;}
    const s=STAGES[i++];
    bar.style.width=s.p+'%';lbl.textContent=s.l;pct.textContent=s.p+'%';stg.textContent=s.s;
  },1200);
  return{
    done(){
      clearInterval(iv);bar.style.width='100%';lbl.textContent='Done!';pct.textContent='100%';
      stg.textContent='✅ Quiz ready — downloading';
      setTimeout(()=>{wrap.style.display='none';bar.style.width='0%';},2200);
    },
    fail(){
      clearInterval(iv);bar.style.background='#dc2626';bar.style.width='100%';
      lbl.textContent='Failed';stg.textContent='❌ Something went wrong';
      setTimeout(()=>{wrap.style.display='none';bar.style.background='';bar.style.width='0%';},3000);
    }
  };
}

async function generate(){
  if(!selectedFiles.length)return;
  er.style.display='none';sb.disabled=true;
  const saveToBank=saveChk.checked;
  const prog=startProgress(saveToBank); // [M3] pass flag so AI stage shows/hides
  try{
    let merged=[];
    for(const f of selectedFiles){const d=await readJson(f);merged=merged.concat(d);}
    if(!merged.length)throw new Error('No questions found in the selected files.');
    const firstName=selectedFiles[0].name.replace(/\.[^.]+$/,'');
    const outName=(selectedFiles.length===1?firstName:'merged')+'_quiz.html';
    const title=selectedFiles.length===1
      ?firstName.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())
      :'Merged Quiz ('+merged.length+' questions)';
    const blob=new Blob([JSON.stringify(merged)],{type:'application/json'});
    const fd=new FormData();
    fd.append('file',blob,selectedFiles.length===1?selectedFiles[0].name:'merged.json');
    fd.append('title',title);fd.append('outname',outName);
    fd.append('saveToGithub',saveToBank?'true':'false');
    const r=await fetch('/generate',{method:'POST',body:fd});
    if(!r.ok){const j=await r.json().catch(()=>({error:'Generation failed'}));throw new Error(j.error||'Generation failed');}
    const dlBlob=await r.blob();
    const url=URL.createObjectURL(dlBlob);
    const a=document.createElement('a');a.href=url;a.download=outName;a.click();URL.revokeObjectURL(url);
    prog.done();
  }catch(e){prog.fail();er.textContent=e.message;er.style.display='block';}
  finally{sb.disabled=!selectedFiles.length;}
}

sb.addEventListener('click',generate);

(async function loadDbStats(){
  try{
    const r=await fetch('/dbstats');if(!r.ok)return;
    const d=await r.json();if(!d||d.error)return;
    document.getElementById('dbstats-wrap').innerHTML=
      '<div style="font-size:.72rem;color:var(--m);margin-top:14px;margin-bottom:6px;font-weight:600">📊 Platform Stats</div>'+
      '<div class="dbstats">'+
      '<div class="dbstat"><div class="v">'+d.total+'</div><div class="l">Quizzes Generated</div></div>'+
      '<div class="dbstat"><div class="v">'+d.totalQuestions+'</div><div class="l">Questions Processed</div></div>'+
      '<div class="dbstat"><div class="v">'+d.tgCount+'</div><div class="l">Via Telegram</div></div>'+
      '<div class="dbstat"><div class="v">'+d.telegramUsers+'</div><div class="l">Bot Users</div></div>'+
      '</div>';
  }catch(e){}
})();
</script>
</body>
</html>`;

export { UPLOAD_PAGE };
