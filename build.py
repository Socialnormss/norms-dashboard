#!/usr/bin/env python3
"""
Norms Mission Control — v5 (folder-driven · 2 หน้า + bottom menu · 2026-05-27)

2 หน้าแยกกัน สลับด้วย bottom menu:
  🏠 HOME — ภาพรวม/glance: ATS progress (ใหญ่) + สรุป 3 โซน (จำนวน + อัปเดตล่าสุด)
  📖 READ — อ่านไฟล์: 3 โซน list → แตะ → อ่านเต็มจอ (โหลดเฉพาะไฟล์นั้น)

โซน (folder = section):
  DASHBOARD/active/01-current/   🔨 งานกำลังทำ
  DASHBOARD/active/02-unfinished/ ⏳ งานค้าง
  DASHBOARD/active/03-chapters/  📖 บทจาก atoms ★
  DASHBOARD/archive/             🗄️ เก่า
โยน .md/symlink ลง folder = โผล่เอง · watcher rebuild ทุก 15 นาที
ต้องมี .nojekyll (ไม่งั้น GitHub Pages แปลง data/*.md → 404)
"""

import json, datetime, subprocess, re, shutil
from pathlib import Path

HOME      = Path.home()
NC        = HOME / "Documents/Norms-Corp"
TRANS_ACC = NC / "Knowledge/transcripts_accurate"
DASH      = NC / "DASHBOARD"
ACTIVE    = DASH / "active"
ARCHIVE   = DASH / "archive"
ROOT      = Path(__file__).parent
DATA      = ROOT / "data"
OUT       = ROOT / "index.html"

TODAY = datetime.date.today()
NOW   = datetime.datetime.now()

SECTION_META = {
    "current":    {"icon": "🔨", "label": "งานกำลังทำ — ติดตาม/ตรวจ"},
    "unfinished": {"icon": "⏳", "label": "งานค้าง — ยังไม่เสร็จ"},
    "chapters":   {"icon": "📖", "label": "บทหนังสือ (จาก atoms) — อ่าน/แก้คำ"},
    "teaching-prep": {"icon": "🧑‍🏫", "label": "เตรียมสอน — เฉพาะกิจ ระหว่างรอเนื้อหาหลัก"},
}

def rel_time(ts):
    d = NOW.timestamp() - ts
    if d < 60:    return f"{int(d)}s ago"
    if d < 3600:  return f"{int(d/60)}m ago"
    if d < 86400: return f"{int(d/3600)}h ago"
    return f"{int(d/86400)}d ago"

def count_txt(p):
    return len(list(p.glob("*.txt"))) if p.exists() else 0

def title_of(content, fallback):
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback

def slugify(s):
    return re.sub(r"[^A-Za-z0-9_-]+", "-", s).strip("-")

def pretty(name):
    return re.sub(r"^\d+[-_]", "", name).replace("-", " ").replace("_", " ").strip().title()

# ─── content (เขียน data/<slug>.md · คืน metadata เบา) ──────────────
def collect_files(folder, section_id):
    files, latest = [], 0
    if not folder.exists():
        return files, None
    for f in sorted(folder.glob("*.md")):
        try:
            real = f.resolve()
            content = real.read_text(encoding="utf-8")
            st = real.stat()
        except OSError:
            continue
        slug = f"{section_id}--{slugify(f.stem)}"
        (DATA / f"{slug}.md").write_text(content, encoding="utf-8")
        title = title_of(content, f.stem)
        m = re.match(r"Chapter-0*(\d+)", f.stem)
        m_ep = re.match(r"EP-0*(\d+)", f.stem)
        if m:
            card = f"บท {int(m.group(1))} · {title}"
        elif m_ep:
            card = f"EP {int(m_ep.group(1))} · " + re.sub(r"^.*?EP\s*\d+\s*·\s*", "", title)
        else:
            card = title
        latest = max(latest, st.st_mtime)
        files.append({"slug": slug, "title": card,
                      "lines": content.count("\n") + 1, "mtime_ago": rel_time(st.st_mtime)})
    return files, (rel_time(latest) if latest else None)

def collect_sections():
    out = []
    if not ACTIVE.exists():
        return out
    for sub in sorted(p for p in ACTIVE.iterdir() if p.is_dir()):
        key = re.sub(r"^\d+[-_]", "", sub.name)
        meta = SECTION_META.get(key, {"icon": "📁", "label": pretty(sub.name)})
        files, latest = collect_files(sub, sub.name)
        if files:
            out.append({"id": sub.name, "icon": meta["icon"], "label": meta["label"],
                        "files": files, "latest": latest})
    return out

# ─── ATS live ───────────────────────────────────────────────────────
def collect_ats():
    sources = [
        {"key":"npc_gen1","label":"Gen1","path":TRANS_ACC/"npc_gen1","total":168,"icon":"📘"},
        {"key":"npc_gen2","label":"Gen2","path":TRANS_ACC/"npc_gen2","total":145,"icon":"📙"},
        {"key":"nmspc","label":"NMSPC","path":TRANS_ACC/"nmspc2026","total":62,"icon":"📕"},
        {"key":"fblive","label":"FB Live","path":TRANS_ACC/"facebook_live","total":234,"icon":"📺"},
    ]
    tgt = sum(s["total"] for s in sources); done = 0
    for s in sources:
        d = count_txt(s["path"]); s["done"]=d; s["pct"]=round(d/s["total"]*100) if s["total"] else 0
        done += d; del s["path"]
    avg_min = None
    log = Path("/tmp/accurate_queue.log")
    if log.exists():
        try:
            for line in reversed(log.read_text().splitlines()):
                mm = re.search(r"avg\s+([\d.]+)\s*min", line)
                if mm: avg_min = float(mm.group(1)); break
        except Exception: pass
    avg_h = round(avg_min/60,2) if avg_min else 1.5
    try:
        ps = subprocess.run(["pgrep","-f","transcribe.py.*--accurate"],capture_output=True,text=True,timeout=3).stdout
        workers = max(1,len([p for p in ps.split() if p.strip()]))
    except Exception: workers = 2
    rem = tgt - done
    hrem = round(rem*avg_h,1)
    days = max(1,round(hrem/(24*workers))) if hrem else 0
    eta = (TODAY+datetime.timedelta(days=days)).isoformat() if days else TODAY.isoformat()
    current = None
    if log.exists():
        try:
            for line in reversed(log.read_text().splitlines()):
                mm = re.search(r"▶️\s*(.+)$", line)
                if mm: current = mm.group(1).strip(); break
        except Exception: pass
    return {"sources":sources,"done":done,"target":tgt,"remaining":rem,
            "pct":round(done/tgt*100) if tgt else 0,"workers":workers,"days":days,"eta":eta,"current":current}

# ─── BUILD ──────────────────────────────────────────────────────────
def build():
    if DATA.exists(): shutil.rmtree(DATA)
    DATA.mkdir(parents=True)
    payload = {
        "built": NOW.strftime("%d %b %y · %H:%M"),
        "ats": collect_ats(),
        "sections": collect_sections(),
        "archive_files": collect_files(ARCHIVE, "archive")[0],
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(TEMPLATE.replace("__DATA__", data), encoding="utf-8")
    n = sum(len(s["files"]) for s in payload["sections"])
    print(f"[✓] v5 · {len(payload['sections'])} zones · {n} files · "
          f"ATS {payload['ats']['pct']}% · index {OUT.stat().st_size//1024}KB")

# ─── HTML ───────────────────────────────────────────────────────────
TEMPLATE = r"""<!DOCTYPE html>
<html lang="th"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0D0D0D">
<link rel="manifest" href="manifest.json"><link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>Norms Mission Control</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root{--bg:#0D0D0D;--card:#161616;--line:#2a2a2a;--orange:#f27e53;--txt:#ededed;--dim:#9a9a9a;--nav:64px;}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{background:var(--bg);color:var(--txt);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     max-width:760px;margin:0 auto;padding-bottom:calc(var(--nav) + env(safe-area-inset-bottom) + 10px);}
header{padding:18px 16px 12px;position:sticky;top:0;background:rgba(13,13,13,.93);
       backdrop-filter:blur(10px);z-index:10;border-bottom:1px solid var(--line);}
.hrow{display:flex;align-items:center;justify-content:space-between;gap:10px;}
h1{font-size:18px;font-weight:700;}h1 .dot{color:var(--orange);}
.refresh{background:var(--card);border:1px solid var(--line);color:var(--orange);font-size:18px;
         width:40px;height:40px;border-radius:11px;cursor:pointer;flex:none;}
.refresh:active{background:#2a2018;}
.built{font-size:12px;color:var(--dim);margin-top:4px;}
#q{width:100%;margin-top:12px;padding:11px 14px;border-radius:12px;border:1px solid var(--line);
   background:var(--card);color:var(--txt);font-size:15px;}#q::placeholder{color:#666;}
main{padding:14px 14px 0;}
.view{display:none;}.view.active{display:block;}

/* ATS — big (home) */
.ats-big{background:linear-gradient(180deg,#1a1410,#161616);border:1px solid #3a2b20;border-radius:16px;padding:16px;}
.ats-big .top{display:flex;justify-content:space-between;align-items:baseline;}
.ats-big .pct{font-size:34px;font-weight:800;color:var(--orange);line-height:1;}
.ats-big .meta{font-size:12px;color:var(--dim);text-align:right;}
.bar{height:9px;background:#000;border-radius:6px;overflow:hidden;margin:12px 0 4px;}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,var(--orange),#ffb088);}
.ats-big .cur{font-size:13px;margin-top:8px;}.ats-big .cur b{color:var(--orange);}
.src{display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;margin-top:10px;font-size:13px;}
.src .lbl{color:var(--dim);}.src .n{font-variant-numeric:tabular-nums;}.src .bar{height:6px;margin:0;}

/* zone summary (home) */
.zone{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);
      border-radius:14px;padding:16px;margin-bottom:10px;cursor:pointer;}
.zone:active{border-color:var(--orange);}
.zone .ic{font-size:26px;}
.zone .body{flex:1;}.zone .ttl{font-weight:600;font-size:15px;}
.zone .sub{font-size:12px;color:var(--dim);margin-top:2px;}
.zone .cnt{font-size:22px;font-weight:800;color:var(--orange);}
.zone::after{content:"›";color:var(--orange);font-size:22px;}

/* read list */
.sec-h{font-size:13px;font-weight:700;color:var(--dim);text-transform:uppercase;letter-spacing:1px;margin:22px 4px 10px;}
.card{display:flex;justify-content:space-between;align-items:center;gap:10px;background:var(--card);
      border:1px solid var(--line);border-radius:13px;padding:15px 16px;margin-bottom:9px;cursor:pointer;}
.card:active{border-color:var(--orange);}
.card .t{font-weight:600;font-size:15px;flex:1;}.card .m{font-size:11px;color:var(--dim);white-space:nowrap;}
.card::after{content:"›";color:var(--orange);font-size:22px;}
.hide{display:none!important;}
.foot{text-align:center;color:#555;font-size:11px;margin-top:24px;}

/* bottom nav */
nav{position:fixed;bottom:0;left:0;right:0;max-width:760px;margin:0 auto;height:calc(var(--nav) + env(safe-area-inset-bottom));
    padding-bottom:env(safe-area-inset-bottom);display:flex;background:rgba(13,13,13,.96);
    backdrop-filter:blur(12px);border-top:1px solid var(--line);z-index:40;}
nav button{flex:1;background:none;border:none;color:var(--dim);font-size:11px;display:flex;
           flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;}
nav button .ni{font-size:21px;}
nav button.active{color:var(--orange);}

/* reader overlay */
#reader{position:fixed;inset:0;background:var(--bg);z-index:60;display:none;flex-direction:column;max-width:760px;margin:0 auto;}
#reader.on{display:flex;}
.rbar{display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line);
      position:sticky;top:0;background:rgba(13,13,13,.96);backdrop-filter:blur(10px);}
.rbar .back{color:var(--orange);font-size:16px;font-weight:600;background:none;border:none;cursor:pointer;}
.rbar .rt{font-size:14px;font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.rbody{overflow-y:auto;padding:18px 18px 80px;-webkit-overflow-scrolling:touch;}
.md{font-size:16px;line-height:1.75;color:#e6e6e6;overflow-wrap:anywhere;}
.md h1,.md h2,.md h3{color:var(--txt);margin:18px 0 8px;line-height:1.3;}
.md h1{font-size:22px;}.md h2{font-size:19px;}.md h3{font-size:16px;color:var(--orange);}
.md p{margin:10px 0;}.md ul,.md ol{margin:10px 0 10px 22px;}.md li{margin:4px 0;}
.md code{background:#000;padding:1px 6px;border-radius:5px;font-size:14px;color:#ffb088;}
.md pre{background:#000;padding:12px;border-radius:10px;overflow-x:auto;}.md pre code{padding:0;}
.md a{color:var(--orange);}.md blockquote{border-left:3px solid var(--orange);padding-left:12px;color:var(--dim);margin:10px 0;}
.md hr{border:none;border-top:1px solid var(--line);margin:18px 0;}
.md table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;display:block;overflow-x:auto;}
.md th,.md td{border:1px solid var(--line);padding:7px 10px;}.md th{background:#000;color:var(--orange);}
.loading{color:var(--dim);padding:20px 0;}
</style></head><body>
<header>
  <div class="hrow">
    <h1>Norms <span class="dot">●</span> <span id="htitle">Mission Control</span></h1>
    <button class="refresh" onclick="location.reload()" aria-label="refresh">🔄</button>
  </div>
  <div class="built" id="built"></div>
  <input id="q" type="search" placeholder="🔍 ค้นหาชื่อบท/ไฟล์…" autocomplete="off" style="display:none">
</header>

<main>
  <div class="view active" id="home"></div>
  <div class="view" id="read"></div>
</main>

<nav>
  <button id="nav-home" class="active" onclick="show('home')"><span class="ni">🏠</span>Home</button>
  <button id="nav-read" onclick="show('read')"><span class="ni">📖</span>Read</button>
</nav>

<div id="reader">
  <div class="rbar"><button class="back" onclick="closeReader()">‹ กลับ</button><span class="rt" id="rt"></span></div>
  <div class="rbody"><div class="md" id="rbody"></div></div>
</div>

<script>
const D = __DATA__;
const $ = (s,el=document)=>el.querySelector(s);
marked.setOptions({gfm:true,breaks:true});

/* ---------- HOME ---------- */
function atsBig(a){
  const src=a.sources.map(s=>`<div class="src"><span class="lbl">${s.icon} ${s.label}</span>
    <span class="bar"><i style="width:${s.pct}%"></i></span><span class="n">${s.done}/${s.total}·${s.pct}%</span></div>`).join("");
  return `<div class="ats-big"><div class="top">
      <div><div class="pct">${a.pct}%</div><div class="meta" style="text-align:left">${a.done}/${a.target} EP · เหลือ ${a.remaining}</div></div>
      <div class="meta">${a.workers} workers · ${a.days}d<br>ETA ${a.eta}</div></div>
    <div class="bar"><i style="width:${a.pct}%"></i></div>
    ${a.current?`<div class="cur">▶️ กำลังถอด: <b>${a.current}</b></div>`:""}${src}</div>`;
}
function homeView(){
  let h=`<div class="sec-h">🟢 ATS Pipeline</div>`+atsBig(D.ats);
  h+=`<div class="sec-h">📂 โซนงาน (แตะเพื่ออ่าน)</div>`;
  D.sections.forEach(s=>{
    h+=`<div class="zone" onclick="gotoRead('${s.id}')">
      <span class="ic">${s.icon}</span>
      <div class="body"><div class="ttl">${s.label}</div>
        <div class="sub">${s.files.length} ไฟล์${s.latest?` · ล่าสุด ${s.latest}`:""}</div></div>
      <span class="cnt">${s.files.length}</span></div>`;
  });
  $("#home").innerHTML=h;
}

/* ---------- READ ---------- */
function cardHTML(f){
  return `<div class="card" data-t="${f.title.toLowerCase()}" onclick="openReader('${f.slug}','${f.title.replace(/'/g,"\\'")}')">
    <span class="t">${f.title}</span><span class="m">${f.lines} บรรทัด · ${f.mtime_ago}</span></div>`;
}
function readView(){
  let h="";
  D.sections.forEach(s=>{ h+=`<div class="sec-h" id="sec-${s.id}">${s.icon} ${s.label}</div>`+s.files.map(cardHTML).join(""); });
  if(D.archive_files.length){ h+=`<div class="sec-h">🗄️ Archive</div>`+D.archive_files.map(cardHTML).join(""); }
  const n=D.sections.reduce((a,s)=>a+s.files.length,0);
  h+=`<div class="foot">${n} ไฟล์ · ${D.archive_files.length} archive · folder-driven</div>`;
  $("#read").innerHTML=h;
}

/* ---------- nav ---------- */
function show(v){
  document.querySelectorAll(".view").forEach(x=>x.classList.toggle("active",x.id===v));
  $("#nav-home").classList.toggle("active",v==="home");
  $("#nav-read").classList.toggle("active",v==="read");
  $("#q").style.display = v==="read" ? "block" : "none";
  $("#htitle").textContent = v==="read" ? "READ" : "Mission Control";
  window.scrollTo(0,0);
}
function gotoRead(secId){
  show("read");
  const el=$("#sec-"+secId); if(el) el.scrollIntoView({behavior:"smooth"});
}

/* ---------- reader ---------- */
async function openReader(slug,title){
  $("#rt").textContent=title;
  $("#rbody").innerHTML='<div class="loading">กำลังโหลด…</div>';
  $("#reader").classList.add("on"); $(".rbody").scrollTop=0;
  history.pushState({reader:1},"");
  try{ const r=await fetch("data/"+slug+".md",{cache:"no-store"}); $("#rbody").innerHTML=marked.parse(await r.text()); }
  catch(e){ $("#rbody").innerHTML='<div class="loading">โหลดไม่ได้ — เปิดผ่าน URL เว็บ (ไม่ใช่ไฟล์)</div>'; }
}
function closeReader(){ $("#reader").classList.remove("on"); }
window.addEventListener("popstate",()=>{ if($("#reader").classList.contains("on")) closeReader(); });

$("#q").addEventListener("input",e=>{
  const q=e.target.value.toLowerCase().trim();
  document.querySelectorAll("#read .card").forEach(c=>c.classList.toggle("hide",q&&!c.dataset.t.includes(q)));
  document.querySelectorAll("#read .sec-h").forEach(h=>h.classList.toggle("hide",!!q));
});

$("#built").textContent="อัปเดต "+D.built+" · แตะ 🔄 เพื่อดึงข้อมูลล่าสุด";
homeView(); readView();
</script>
</body></html>"""

if __name__ == "__main__":
    build()
