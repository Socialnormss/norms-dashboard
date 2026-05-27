#!/usr/bin/env python3
"""
Norms Mission Control — Dashboard v3 (folder-driven · 2026-05-27)

หลักการใหม่:
- เนื้อหาบน dashboard = scan จาก DASHBOARD/active/ อัตโนมัติ (ไม่ hardcode list)
- โยน .md (หรือ symlink) ลง active/<section>/ = โผล่บน dashboard เอง
- ย้ายไป archive/ = ออกจากหน้าหลัก (ยังอ่านได้ในโซน archive)
- ATS pipeline = section live เดียวที่อ่าน real-time จาก disk/log
- watcher (watch.py) rebuild ทุก 15 นาที → เนื้อหา fresh เอง ไม่ต้องสั่ง build

โครงสร้าง:
  DASHBOARD/active/01-ats/          → section "ATS"
  DASHBOARD/active/02-norm-book-web/ → section "Norm Book + Web"
  DASHBOARD/active/03-reports/      → section "Reports"
  DASHBOARD/archive/                → โซนเก่า (collapsed)
"""

import json, datetime, subprocess, re
from pathlib import Path

# ─── PATHS ──────────────────────────────────────────────────────────
HOME      = Path.home()
NC        = HOME / "Documents/Norms-Corp"
TRANS_ACC = NC / "Knowledge/transcripts_accurate"
DASH      = NC / "DASHBOARD"
ACTIVE    = DASH / "active"
ARCHIVE   = DASH / "archive"
OUT       = Path(__file__).parent / "index.html"

TODAY = datetime.date.today()
NOW   = datetime.datetime.now()

# section folder (หลัง strip NN-) → label/icon · ไม่มีใน map = prettify อัตโนมัติ
SECTION_META = {
    "ats":           {"icon": "🟢", "label": "ATS Pipeline + งานต่อจาก ATS"},
    "norm-book-web": {"icon": "📚", "label": "Norm Book + Website"},
    "reports":       {"icon": "📄", "label": "Reports / สถานะงาน"},
}

# ─── HELPERS ────────────────────────────────────────────────────────
def rel_time(ts):
    d = NOW.timestamp() - ts
    if d < 60:    return f"{int(d)}s ago"
    if d < 3600:  return f"{int(d/60)}m ago"
    if d < 86400: return f"{int(d/3600)}h ago"
    return f"{int(d/86400)}d ago"

def count_txt(path):
    return len(list(path.glob("*.txt"))) if path.exists() else 0

def title_of(content, fallback):
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback

def pretty(name):
    return re.sub(r"^\d+[-_]", "", name).replace("-", " ").replace("_", " ").strip().title()

# ─── COLLECT: content folders (auto-discover) ───────────────────────
def collect_files(folder):
    """อ่าน .md ทุกไฟล์ใน folder (resolve symlink) → list of cards"""
    files = []
    if not folder.exists():
        return files
    for f in sorted(folder.glob("*.md")):
        try:
            real = f.resolve()
            content = real.read_text(encoding="utf-8")
            st = real.stat()
            files.append({
                "name": f.name,
                "title": title_of(content, f.stem),
                "content": content,
                "lines": content.count("\n") + 1,
                "mtime_ago": rel_time(st.st_mtime),
            })
        except Exception:
            continue
    return files

def collect_sections():
    """แต่ละ subfolder ใน active/ = 1 section"""
    sections = []
    if not ACTIVE.exists():
        return sections
    for sub in sorted(p for p in ACTIVE.iterdir() if p.is_dir()):
        key = re.sub(r"^\d+[-_]", "", sub.name)
        meta = SECTION_META.get(key, {"icon": "📁", "label": pretty(sub.name)})
        files = collect_files(sub)
        if not files:
            continue
        sections.append({
            "id": sub.name,
            "icon": meta["icon"],
            "label": meta["label"],
            "files": files,
        })
    return sections

# ─── COLLECT: ATS live progress ─────────────────────────────────────
def collect_ats():
    sources = [
        {"key":"npc_gen1", "label":"NPC Gen1",       "path": TRANS_ACC/"npc_gen1",      "total":168, "icon":"📘"},
        {"key":"npc_gen2", "label":"NPC Gen2",       "path": TRANS_ACC/"npc_gen2",      "total":145, "icon":"📙"},
        {"key":"nmspc",    "label":"NMSPC 2026",     "path": TRANS_ACC/"nmspc2026",     "total":62,  "icon":"📕"},
        {"key":"fblive",   "label":"Facebook Live",  "path": TRANS_ACC/"facebook_live", "total":234, "icon":"📺"},
    ]
    total_target = sum(s["total"] for s in sources)
    total_done = 0
    for s in sources:
        done = count_txt(s["path"])
        s["done"] = done
        s["pct"] = round(done / s["total"] * 100) if s["total"] else 0
        total_done += done
        del s["path"]
    total_remaining = total_target - total_done

    # real avg min/EP จาก queue log
    avg_min = None
    log = Path("/tmp/accurate_queue.log")
    if log.exists():
        try:
            for line in reversed(log.read_text().splitlines()):
                m = re.search(r"avg\s+([\d.]+)\s*min", line)
                if m:
                    avg_min = float(m.group(1)); break
        except Exception:
            pass
    avg_h = round(avg_min / 60, 2) if avg_min else 1.5

    # live workers
    try:
        ps = subprocess.run(["pgrep","-f","transcribe.py.*--accurate"],
                            capture_output=True, text=True, timeout=3).stdout
        workers = max(1, len([p for p in ps.split() if p.strip()]))
    except Exception:
        workers = 2

    hours_remaining = round(total_remaining * avg_h, 1)
    days = max(1, round(hours_remaining / (24 * workers))) if hours_remaining else 0
    eta = (TODAY + datetime.timedelta(days=days)).isoformat() if days else TODAY.isoformat()

    # current EP จาก log
    current = None
    if log.exists():
        try:
            for line in reversed(log.read_text().splitlines()):
                m = re.search(r"▶️\s*(.+)$", line)
                if m:
                    current = m.group(1).strip(); break
        except Exception:
            pass

    return {
        "sources": sources,
        "total_done": total_done,
        "total_target": total_target,
        "total_remaining": total_remaining,
        "overall_pct": round(total_done / total_target * 100) if total_target else 0,
        "workers": workers,
        "days": days,
        "eta": eta,
        "current": current,
    }

# ─── BUILD ──────────────────────────────────────────────────────────
def build():
    payload = {
        "built": NOW.strftime("%d %b %y · %H:%M"),
        "ats": collect_ats(),
        "sections": collect_sections(),
        "archive": collect_files(ARCHIVE),
    }
    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    OUT.write_text(html, encoding="utf-8")
    n = sum(len(s["files"]) for s in payload["sections"])
    print(f"[✓] built · {len(payload['sections'])} sections · {n} active files · "
          f"ATS {payload['ats']['overall_pct']}% · archive {len(payload['archive'])}")

# ─── HTML TEMPLATE ──────────────────────────────────────────────────
TEMPLATE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0D0D0D">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>Norms Mission Control</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root{ --bg:#0D0D0D; --card:#161616; --card2:#1e1e1e; --line:#2a2a2a;
         --orange:#f27e53; --txt:#ededed; --dim:#9a9a9a; --green:#3ecf8e; }
  *{box-sizing:border-box; margin:0; padding:0; -webkit-tap-highlight-color:transparent;}
  body{background:var(--bg); color:var(--txt); font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
       padding:env(safe-area-inset-top) 0 40px; max-width:760px; margin:0 auto;}
  header{padding:18px 16px 12px; position:sticky; top:0; background:rgba(13,13,13,.92);
         backdrop-filter:blur(10px); z-index:10; border-bottom:1px solid var(--line);}
  h1{font-size:18px; font-weight:700; letter-spacing:.3px;}
  h1 .dot{color:var(--orange);}
  .built{font-size:12px; color:var(--dim); margin-top:2px;}
  #q{width:100%; margin-top:12px; padding:11px 14px; border-radius:12px; border:1px solid var(--line);
     background:var(--card); color:var(--txt); font-size:15px;}
  #q::placeholder{color:#666;}
  main{padding:14px 14px 0;}

  /* ATS hero */
  .ats{background:linear-gradient(180deg,#1a1410,#161616); border:1px solid #3a2b20;
       border-radius:16px; padding:16px; margin-bottom:18px;}
  .ats .top{display:flex; justify-content:space-between; align-items:baseline;}
  .ats .pct{font-size:34px; font-weight:800; color:var(--orange); line-height:1;}
  .ats .meta{font-size:12px; color:var(--dim); text-align:right;}
  .bar{height:9px; background:#000; border-radius:6px; overflow:hidden; margin:12px 0 4px;}
  .bar > i{display:block; height:100%; background:linear-gradient(90deg,var(--orange),#ffb088);}
  .ats .cur{font-size:13px; color:var(--txt); margin-top:8px;}
  .ats .cur b{color:var(--orange);}
  .src{display:grid; grid-template-columns:auto 1fr auto; gap:8px; align-items:center;
       margin-top:10px; font-size:13px;}
  .src .lbl{color:var(--dim);} .src .n{color:var(--txt); font-variant-numeric:tabular-nums;}
  .src .bar{height:6px; margin:0;}

  /* sections + cards */
  .sec-h{font-size:13px; font-weight:700; color:var(--dim); text-transform:uppercase;
         letter-spacing:1px; margin:22px 4px 10px;}
  details.card{background:var(--card); border:1px solid var(--line); border-radius:14px;
               margin-bottom:10px; overflow:hidden;}
  details.card[open]{border-color:#3a2b20;}
  summary{padding:14px 16px; cursor:pointer; list-style:none; display:flex;
          justify-content:space-between; align-items:center; gap:10px;}
  summary::-webkit-details-marker{display:none;}
  summary .t{font-weight:600; font-size:15px; flex:1;}
  summary .m{font-size:11px; color:var(--dim); white-space:nowrap;}
  summary::after{content:"›"; color:var(--orange); font-size:20px; transition:transform .2s;}
  details[open] summary::after{transform:rotate(90deg);}
  .body{padding:0 16px 18px; border-top:1px solid var(--line); margin-top:2px;}
  .body.md{font-size:14.5px; color:#dcdcdc; overflow-wrap:anywhere;}
  .md h1,.md h2,.md h3{color:var(--txt); margin:16px 0 6px; line-height:1.3;}
  .md h1{font-size:19px;} .md h2{font-size:17px;} .md h3{font-size:15px; color:var(--orange);}
  .md p{margin:8px 0;} .md ul,.md ol{margin:8px 0 8px 20px;} .md li{margin:3px 0;}
  .md code{background:#000; padding:1px 6px; border-radius:5px; font-size:13px; color:#ffb088;}
  .md pre{background:#000; padding:12px; border-radius:10px; overflow-x:auto; margin:10px 0;}
  .md pre code{padding:0;}
  .md a{color:var(--orange);}
  .md blockquote{border-left:3px solid var(--orange); padding-left:12px; color:var(--dim); margin:10px 0;}
  .md hr{border:none; border-top:1px solid var(--line); margin:16px 0;}
  .md table{border-collapse:collapse; width:100%; margin:10px 0; font-size:13px; display:block; overflow-x:auto;}
  .md th,.md td{border:1px solid var(--line); padding:6px 9px; text-align:left;}
  .md th{background:#000; color:var(--orange);}
  .arch summary .t{color:var(--dim);}
  .empty{color:var(--dim); font-size:13px; padding:8px 4px;}
  .hide{display:none !important;}
  footer{text-align:center; color:#555; font-size:11px; margin-top:30px;}
</style>
</head>
<body>
<header>
  <h1>Norms <span class="dot">●</span> Mission Control</h1>
  <div class="built" id="built"></div>
  <input id="q" type="search" placeholder="🔍 ค้นหา…" autocomplete="off">
</header>
<main id="app"></main>
<footer id="foot"></footer>

<script>
const D = __DATA__;
const $ = (s,el=document)=>el.querySelector(s);
marked.setOptions({gfm:true, breaks:true});

function mdParse(t){ try{return marked.parse(t);}catch(e){return "<pre>"+t.replace(/</g,"&lt;")+"</pre>";} }

function atsHero(a){
  const src = a.sources.map(s=>`
    <div class="src">
      <span class="lbl">${s.icon} ${s.label}</span>
      <span class="bar"><i style="width:${s.pct}%"></i></span>
      <span class="n">${s.done}/${s.total} · ${s.pct}%</span>
    </div>`).join("");
  return `<div class="ats">
    <div class="top">
      <div><div class="pct">${a.overall_pct}%</div>
        <div class="meta" style="text-align:left">${a.total_done}/${a.total_target} EP · เหลือ ${a.total_remaining}</div></div>
      <div class="meta">${a.workers} workers · ${a.days}d<br>ETA ${a.eta}</div>
    </div>
    <div class="bar"><i style="width:${a.overall_pct}%"></i></div>
    ${a.current?`<div class="cur">▶️ กำลังถอด: <b>${a.current}</b></div>`:""}
    ${src}
  </div>`;
}

function card(f, arch){
  return `<details class="card${arch?' arch':''}">
    <summary><span class="t">${f.title}</span><span class="m">${f.lines} บรรทัด · ${f.mtime_ago}</span></summary>
    <div class="body md" data-raw="${encodeURIComponent(f.content)}"></div>
  </details>`;
}

function render(){
  let h = atsHero(D.ats);
  D.sections.forEach(s=>{
    h += `<div class="sec-h">${s.icon} ${s.label}</div>`;
    h += s.files.map(f=>card(f,false)).join("");
  });
  if(D.archive.length){
    h += `<div class="sec-h">🗄️ Archive (เก่า)</div>`;
    h += D.archive.map(f=>card(f,true)).join("");
  }
  $("#app").innerHTML = h;
  $("#built").textContent = "อัปเดต " + D.built + " · pull เพื่อ refresh";
  const n = D.sections.reduce((a,s)=>a+s.files.length,0);
  $("#foot").textContent = `${n} active · ${D.archive.length} archive · folder-driven`;

  // lazy-render markdown on first open
  document.querySelectorAll("details.card").forEach(d=>{
    d.addEventListener("toggle",()=>{
      const b = $(".body", d);
      if(d.open && !b.dataset.done){
        b.innerHTML = mdParse(decodeURIComponent(b.dataset.raw));
        b.dataset.done = "1";
      }
    });
  });
}

// search filter (title + content)
$("#q").addEventListener("input", e=>{
  const q = e.target.value.toLowerCase().trim();
  document.querySelectorAll("details.card").forEach(d=>{
    const t = $(".t",d).textContent.toLowerCase();
    const raw = decodeURIComponent($(".body",d).dataset.raw).toLowerCase();
    const hit = !q || t.includes(q) || raw.includes(q);
    d.classList.toggle("hide", !hit);
    if(q && hit && !$(".body",d).dataset.done){
      const b=$(".body",d); b.innerHTML=mdParse(decodeURIComponent(b.dataset.raw)); b.dataset.done="1"; d.open=true;
    }
  });
  document.querySelectorAll(".sec-h").forEach(h=>h.classList.toggle("hide", !!q));
});

render();
</script>
</body>
</html>"""

if __name__ == "__main__":
    build()
