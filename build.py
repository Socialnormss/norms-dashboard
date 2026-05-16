#!/usr/bin/env python3
"""
Norms Corp Dashboard Builder
อ่านข้อมูลจริงจากระบบ → build index.html → push to GitHub Pages
"""

import json, os, datetime, subprocess
from pathlib import Path

ROOT      = Path.home() / "Documents/Norms-Corp/Social-Norms"
DRAFTS    = ROOT / "02-Content/content_pipeline/drafts"
TRANS     = ROOT / "03-Knowledge/transcripts"
OUT       = Path(__file__).parent / "index.html"

DRIVE     = Path("/Volumes/socialnorms")
GEN1_SRC  = DRIVE / "SocialNorms PV Course/NPC GEN1"
GEN2_SRC  = DRIVE / "SocialNorms PV Course/NPC GEN2"
NMSPC_SRC = DRIVE / "SocialNorms PV Course/NMSPC 2026/NMSPC"
FB_SRC    = DRIVE / "Facebook Live"

def count_mp4(path):
    if not path.exists(): return 0
    return len(list(path.glob("*.mp4")) + list(path.glob("*.mov")))

def count_txt(path):
    if not path.exists(): return 0
    return len(list(path.glob("*.txt")))

def load_drafts():
    if not DRAFTS.exists(): return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DRAFTS.glob("*.json"))]

def get_pipeline():
    return {
        "npc_gen1":  {"done": count_txt(TRANS/"npc_gen1"),  "total": 168,            "label": "NPC Gen1"},
        "npc_gen2":  {"done": count_txt(TRANS/"npc_gen2"),  "total": count_mp4(GEN2_SRC) or 144, "label": "NPC Gen2"},
        "nmspc2026": {"done": count_txt(TRANS/"nmspc2026"), "total": count_mp4(NMSPC_SRC) or 30,  "label": "NMSPC 2026"},
        "facebook":  {"done": count_txt(TRANS/"facebook_live"), "total": count_mp4(FB_SRC) or 116, "label": "Facebook Live"},
    }

def get_claude_stats():
    sessions_dir = Path.home() / ".claude/sessions"
    projects_dir = Path.home() / ".claude/projects"
    now_ms = datetime.datetime.now().timestamp() * 1000
    sessions = []
    if not sessions_dir.exists():
        return sessions
    for sf in sorted(sessions_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            data = json.loads(sf.read_text())
            pid = data.get("pid")
            session_id = data.get("sessionId", "")
            cwd = data.get("cwd", "")
            started_ms = data.get("startedAt", 0)
            status = data.get("status", "unknown")
            r = subprocess.run(["ps", "-p", str(pid), "-o", "pid="], capture_output=True, text=True)
            is_alive = bool(r.stdout.strip())
            runtime_min = int((now_ms - started_ms) / 60000) if started_ms else 0
            tokens = {"total_input": 0, "total_output": 0, "total_cache_read": 0,
                      "latest_cache_read": 0, "msg_count": 0, "context_pct": 0}
            for proj_subdir in projects_dir.iterdir():
                if not proj_subdir.is_dir():
                    continue
                jsonl_path = proj_subdir / f"{session_id}.jsonl"
                if jsonl_path.exists():
                    try:
                        lines = jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                        latest_cache = 0
                        for line in lines:
                            try:
                                d = json.loads(line)
                                if d.get("type") == "assistant" and isinstance(d.get("message"), dict):
                                    u = d["message"].get("usage", {})
                                    tokens["total_input"] += u.get("input_tokens", 0)
                                    tokens["total_output"] += u.get("output_tokens", 0)
                                    cr = u.get("cache_read_input_tokens", 0)
                                    tokens["total_cache_read"] += cr
                                    if cr > latest_cache:
                                        latest_cache = cr
                                    tokens["msg_count"] += 1
                            except Exception:
                                pass
                        tokens["latest_cache_read"] = latest_cache
                        tokens["context_pct"] = min(100, round(latest_cache / 200000 * 100))
                    except Exception:
                        pass
                    break
            sessions.append({
                "pid": pid,
                "session_id": session_id[:8],
                "cwd": cwd.replace(str(Path.home()), "~"),
                "runtime_min": runtime_min,
                "status": status,
                "alive": is_alive,
                "tokens": tokens,
                "warn": tokens["context_pct"] > 75,
            })
        except Exception:
            pass
    return sessions

PROJECTS = [
    {"id":"npc-book","icon":"📚","title":"NPC Book","subtitle":"3 เล่ม · 58 บท","status":"done","progress":100,
     "details":["Stage 1-4 ✅ ครบทุก stage","58 บทเขียนเสร็จแล้ว","3 HTML books พร้อม"],"next":"ส่งทีมตรวจ พุธ 20 พ.ค."},
    {"id":"content","icon":"📣","title":"Content Pipeline","subtitle":"58 drafts พร้อมโพสต์","status":"done","progress":100,
     "details":["📘 อ่านตลาดได้ 22 บท","📙 หลิวคิดอะไรอยู่ 18 บท","📗 จิตใจนักเทรด 18 บท"],"next":"เติม API credit → รัน content_pipeline.py คุณภาพสูงขึ้น"},
    {"id":"transcription","icon":"🎙️","title":"Transcription","subtitle":"แปล video → text (AA edition)","status":"running","progress":0,
     "details":[],"next":"รันทิ้งข้ามคืน · orchestrator auto-restart"},
    {"id":"norms-corp","icon":"🏢","title":"Norms Corp","subtitle":"9 departments · AI agents","status":"phase1","progress":40,
     "details":["✅ Structure + CLAUDE.md + INDEX.md + WORKFLOW.md","✅ Agent Briefs ครบ 9 แผนก","✅ AI Empire dissolved → merged","⏳ Phase 2: API orchestration"],"next":"Phase 2: orchestrator.py + task queue"},
    {"id":"digital-twin","icon":"🤖","title":"Digital Twin","subtitle":"AI ที่สอนแบบหลิว","status":"blocked","progress":5,
     "details":["🔴 ต้องการ 50 golden Logic Notes","🔴 ThinkAloud Pass 2 ยังไม่รัน","✅ DigitalTwin_Config.md พร้อม","✅ ThinkAloud_Prompt.md พร้อม"],"next":"รอ transcript ครบ → ThinkAloud → human review → golden"},
    {"id":"aa","icon":"⚡","title":"AA System","subtitle":"Another AI · Workflow framework","status":"research","progress":30,
     "details":["✅ Case studies: Ali Abdaal + ลงทุน Diary","✅ Synthesis + Priority Matrix","⏳ Whisper Flow ยังไม่ติดตั้ง","⏳ NotebookLM MCP ยังไม่ set up"],"next":"ติดตั้ง Whisper Flow (impact สูงสุด)"},
]

TODOS = {
    "urgent":[
        {"text":"ส่ง NPC Book ให้ทีมตรวจ","due":"พุธ 20 พ.ค.","tag":"book"},
        {"text":"Print HTML books → PDF (เปิด output/*.html → Print → Save as PDF)","due":"ก่อนพุธ","tag":"book"},
    ],
    "soon":[
        {"text":"เติม Anthropic API credit (58 บท < $0.10)","due":"สัปดาห์นี้","tag":"content"},
        {"text":"ติดตั้ง Whisper Flow — พูดแทนพิมพ์ ลด friction 5-10x","due":"สัปดาห์นี้","tag":"aa"},
        {"text":"Eightcap 3 posts (Gold → Oil/Silver pivot) รอ visuals","due":"สัปดาห์นี้","tag":"eightcap"},
    ],
    "backlog":[
        {"text":"รัน ThinkAloud Pass 2 → Logic Notes","due":"หลัง transcript จบ","tag":"knowledge"},
        {"text":"Human review Logic Notes (เฉพาะ [UNCLEAR] flags)","due":"หลัง Pass 2","tag":"knowledge"},
        {"text":"NPC Gen2 + NMSPC + Facebook Live books","due":"หลัง transcript","tag":"book"},
        {"text":"ลอง NotebookLM MCP (ประหยัด token ระยะยาว)","due":"เดือนนี้","tag":"aa"},
        {"text":"Phase 2: orchestrator.py + task queue","due":"เดือนหน้า","tag":"norms-corp"},
        {"text":"Phase 3: Web Dashboard CEO → departments","due":"หลัง Phase 2","tag":"norms-corp"},
    ],
}

TOPICS = [
    {"icon":"📚","title":"NPC Gen2 Book","detail":"หลัง transcript → book_pipeline → 4 เล่มใหม่"},
    {"icon":"📺","title":"Facebook Live Book","detail":"~116 คลิป → insights การสอนสด → เล่มที่ 4"},
    {"icon":"🎓","title":"ปรับ Class Structure","detail":"ใช้หนังสือทั้งหมดออกแบบหลักสูตร NMSPC + NPC รุ่นใหม่"},
    {"icon":"🤖","title":"Digital Twin Training","detail":"50 golden notes → เริ่ม train ได้เลย"},
    {"icon":"💰","title":"Eightcap Content System","detail":"workflow drafts → compliance → post"},
    {"icon":"⚡","title":"AA Implementation","detail":"Whisper Flow + NotebookLM MCP + Custom MCP server"},
    {"icon":"🏢","title":"Phase 2 Automation","detail":"Claude API orchestrator · CEO → departments task routing"},
    {"icon":"🌐","title":"Social Norms Website V2","detail":"mentorship · advanced · about · free pages"},
]

PREPS = [
    {"icon":"💳","title":"Anthropic API Credit","detail":"console.anthropic.com · 58 บท < $0.10 · รัน content_pipeline.py"},
    {"icon":"🎙️","title":"Whisper Flow","detail":"whisperflow.app · กด Fn+Space แล้วพูด · ลด friction 5-10x"},
    {"icon":"📒","title":"NotebookLM MCP","detail":"NPC 168 ไฟล์ใน NotebookLM · Claude query ตรงไป · ค้นหา 'notebooklm mcp' GitHub"},
    {"icon":"📄","title":"NPC Book PDF","detail":"03-Knowledge/book_pipeline/output/*.html → Print → Save as PDF"},
    {"icon":"🔌","title":"External Drive","detail":"เสียบ /Volumes/socialnorms ก่อนรัน transcription · orchestrator รอ auto"},
    {"icon":"🎨","title":"Eightcap Visuals","detail":"3 posts รอ visuals · Gold→Oil/Silver · ดู EIGHTCAP_STYLE_GUIDE.md"},
]

SC = {
    "อ่านตลาดได้":    {"bg":"rgba(59,130,246,.2)",  "color":"#60A5FA"},
    "หลิวคิดอะไรอยู่": {"bg":"rgba(245,158,11,.2)", "color":"#FCD34D"},
    "จิตใจนักเทรด":   {"bg":"rgba(16,185,129,.2)",  "color":"#34D399"},
}

def build():
    now      = datetime.datetime.now()
    ts       = now.strftime("%Y-%m-%dT%H:%M:%S")
    ts_thai  = now.strftime("อัพเดท %d/%m/%y %H:%M")
    drafts   = load_drafts()
    pipeline = get_pipeline()
    claude_sessions = get_claude_stats()
    alive_count = sum(1 for s in claude_sessions if s["alive"])

    # คำนวณ transcription progress
    total_done  = sum(v["done"]  for v in pipeline.values())
    total_vids  = sum(v["total"] for v in pipeline.values())
    trans_pct   = round(total_done / total_vids * 100) if total_vids else 0

    # อัพเดท project transcription progress
    for p in PROJECTS:
        if p["id"] == "transcription":
            p["progress"] = trans_pct
            p["details"] = [
                f"✅ NPC Gen1: {pipeline['npc_gen1']['done']}/{pipeline['npc_gen1']['total']}",
                f"{'🔄' if pipeline['npc_gen2']['done'] < pipeline['npc_gen2']['total'] else '✅'} NPC Gen2: {pipeline['npc_gen2']['done']}/{pipeline['npc_gen2']['total']}",
                f"{'⏳' if pipeline['nmspc2026']['done'] == 0 else '🔄'} NMSPC 2026: {pipeline['nmspc2026']['done']}/{pipeline['nmspc2026']['total']}",
                f"{'⏳' if pipeline['facebook']['done'] == 0 else '🔄'} Facebook Live: {pipeline['facebook']['done']}/{pipeline['facebook']['total']}",
            ]

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Norms Corp">
<meta name="theme-color" content="#0C0C0C">
<meta name="build-time" content="{ts}">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>Norms Corp</title>
<link rel="manifest" href="manifest.json">
<style>
:root{{--bg:#0C0C0C;--base:#131313;--surface:#1A1A1A;--raised:#222;--overlay:#2C2C2C;
--amber:#D47A2A;--a4:#E0944A;--at:rgba(212,122,42,.12);
--text:#F0EDE8;--t2:#A8A49E;--muted:#706C66;
--border:rgba(255,255,255,.08);--green:#10B981;--blue:#3B82F6;--yellow:#F59E0B;--red:#EF4444;
--r:12px;--st:env(safe-area-inset-top);--sb:env(safe-area-inset-bottom)}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
html,body{{height:100%;overflow:hidden;background:var(--base);color:var(--text);
font-family:-apple-system,Sarabun,sans-serif;font-size:16px}}
.app{{display:flex;flex-direction:column;height:100%;height:100dvh}}

/* topbar */
.topbar{{background:var(--bg);padding:calc(var(--st)+10px) 16px 10px;border-bottom:1px solid var(--border);flex-shrink:0}}
.topbar-row{{display:flex;align-items:center;gap:8px}}
.logo{{font-size:16px;font-weight:800;color:var(--amber)}}
.update-ts{{font-size:10px;color:var(--muted);margin-left:6px}}
.pulse{{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;margin-right:4px}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(.8)}}}}
.hstats{{margin-left:auto;display:flex;gap:14px}}
.hs{{text-align:right}}.hs-n{{font-size:18px;font-weight:700;display:block;line-height:1}}.hs-l{{font-size:10px;color:var(--muted)}}

/* content */
.content{{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}}
.panel{{display:none;padding:16px 16px calc(16px + var(--sb))}}.panel.active{{display:block}}

/* bottom nav */
.bnav{{background:var(--bg);border-top:1px solid var(--border);display:flex;padding:8px 4px calc(var(--sb)+4px);flex-shrink:0}}
.nb{{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 2px;
border:none;background:none;color:var(--muted);font-size:10px;font-weight:600;cursor:pointer;border-radius:10px}}
.nb .ic{{font-size:22px;line-height:1}}.nb.on{{color:var(--amber)}}

/* section heading */
.sh{{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--amber);margin:20px 0 10px}}
.sh:first-child{{margin-top:0}}

/* project cards */
.proj{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);padding:14px;margin-bottom:10px}}
.proj-h{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.p-icon{{font-size:24px;flex-shrink:0}}
.p-title{{font-weight:700;font-size:15px}}.p-sub{{font-size:12px;color:var(--muted)}}
.sbadge{{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;margin-left:auto;flex-shrink:0;white-space:nowrap}}
.s-done{{background:rgba(16,185,129,.15);color:#34D399}}
.s-running{{background:rgba(245,158,11,.15);color:#FCD34D}}
.s-phase1{{background:rgba(59,130,246,.15);color:#60A5FA}}
.s-blocked{{background:rgba(239,68,68,.15);color:#FCA5A5}}
.s-research{{background:rgba(139,92,246,.15);color:#C4B5FD}}
.pbar-w{{background:var(--overlay);border-radius:4px;height:4px;margin:0 0 10px;overflow:hidden}}
.pbar{{height:100%;border-radius:4px;background:var(--amber)}}
.proj-det{{list-style:none;font-size:13px;color:var(--t2);margin-bottom:8px}}.proj-det li{{padding:1px 0}}
.proj-next{{font-size:12px;color:var(--amber);background:var(--at);border-radius:8px;padding:8px 10px}}
.proj-next::before{{content:"→ "}}

/* pipeline */
.pipe-row{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);padding:14px;margin-bottom:10px}}
.pipe-h{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}}
.pipe-label{{font-weight:600;font-size:14px}}.pipe-pct{{font-size:12px;color:var(--muted)}}
.pipe-n{{font-size:22px;font-weight:800;color:var(--amber);margin-bottom:8px}}

/* todos */
.todo-item{{display:flex;align-items:flex-start;gap:12px;background:var(--raised);border:1px solid var(--border);border-radius:var(--r);padding:12px;margin-bottom:8px}}
.chk{{width:24px;height:24px;border-radius:6px;border:1px solid var(--border);background:var(--overlay);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:14px;cursor:pointer}}
.chk.on{{background:var(--green);border-color:var(--green)}}
.todo-body{{flex:1;min-width:0}}.todo-text{{font-size:14px;line-height:1.4}}.todo-text.done{{text-decoration:line-through;color:var(--muted)}}
.todo-meta{{margin-top:5px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}}
.due{{font-size:11px;color:var(--muted)}}
.tag{{padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;text-transform:uppercase}}
.tag-book{{background:rgba(59,130,246,.2);color:#60A5FA}}.tag-content{{background:rgba(16,185,129,.2);color:#34D399}}
.tag-aa{{background:rgba(139,92,246,.2);color:#C4B5FD}}.tag-eightcap{{background:rgba(245,158,11,.2);color:#FCD34D}}
.tag-knowledge{{background:rgba(212,122,42,.15);color:var(--amber)}}.tag-norms-corp{{background:rgba(239,68,68,.15);color:#FCA5A5}}

/* topics / prep */
.tcard{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);padding:14px;margin-bottom:8px;display:flex;gap:12px}}
.t-ic{{font-size:24px;flex-shrink:0}}.t-title{{font-weight:700;font-size:14px;margin-bottom:3px}}.t-detail{{font-size:13px;color:var(--t2);line-height:1.4}}

/* content cards */
.fscroll{{display:flex;gap:8px;overflow-x:auto;padding-bottom:12px;scrollbar-width:none}}.fscroll::-webkit-scrollbar{{display:none}}
.fbtn{{flex-shrink:0;padding:7px 16px;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--t2);font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap}}
.fbtn.on{{background:var(--amber);border-color:var(--amber);color:#000}}
#search{{width:100%;background:var(--raised);border:1px solid var(--border);border-radius:10px;color:var(--text);font-size:15px;padding:10px 14px;outline:none;-webkit-appearance:none;margin-bottom:14px}}
#search:focus{{border-color:var(--amber)}}
.card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);padding:14px;margin-bottom:10px;cursor:pointer;position:relative}}
.card:active{{background:var(--overlay)}}.card.posted{{opacity:.45}}
.series-badge{{padding:3px 9px;border-radius:4px;font-size:11px;font-weight:700}}
.card-topic{{font-weight:700;font-size:15px;line-height:1.3;margin:6px 0 4px}}
.card-meta{{display:flex;gap:6px}}.time-tag{{background:var(--overlay);padding:2px 8px;border-radius:4px;font-size:11px;color:var(--muted)}}
.cid{{font-size:11px;color:var(--muted)}}.pdot{{position:absolute;top:12px;right:12px;width:9px;height:9px;border-radius:50%;background:var(--green)}}

/* sheet */
.sheet-bg{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:300;align-items:flex-end}}
.sheet-bg.open{{display:flex}}
.sheet{{background:var(--surface);border-radius:20px 20px 0 0;width:100%;max-height:90vh;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:0 0 calc(20px + var(--sb))}}
.handle{{width:40px;height:4px;background:var(--border);border-radius:2px;margin:12px auto 16px}}
.si{{padding:0 18px}}
.s-badge{{margin-bottom:8px}}.s-title{{font-size:18px;font-weight:800;margin-bottom:4px;line-height:1.3}}.s-meta{{font-size:12px;color:var(--muted);margin-bottom:16px}}
.sec-l{{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--amber);margin-bottom:8px}}
.cbox{{background:var(--raised);border:1px solid var(--border);border-radius:10px;padding:14px;font-size:14px;line-height:1.8;white-space:pre-wrap;word-break:break-word;margin-bottom:8px}}
.cpbtn{{width:100%;background:var(--overlay);border:1px solid var(--border);border-radius:10px;color:var(--t2);font-size:14px;padding:12px;cursor:pointer;margin-bottom:14px;font-weight:600}}
.cpbtn:active{{background:var(--border)}}.cpbtn.cp{{border-color:var(--green);color:var(--green)}}
.comp{{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:8px;padding:10px 12px;font-size:13px;color:#FCD34D;margin-bottom:14px}}
.post-action{{display:flex;gap:10px;padding:0 18px;margin-top:4px}}
.postbtn{{flex:1;background:var(--amber);border:none;color:#000;font-size:15px;font-weight:700;padding:14px;border-radius:12px;cursor:pointer}}
.postbtn.unpost{{background:var(--overlay);color:var(--t2)}}

/* update banner */
.update-banner{{display:none;position:fixed;top:calc(var(--st)+65px);left:50%;transform:translateX(-50%);
background:#1a3a1a;border:1px solid var(--green);color:var(--green);font-size:13px;font-weight:600;
padding:10px 20px;border-radius:20px;z-index:200;cursor:pointer;white-space:nowrap}}
.update-banner.show{{display:block}}

/* claude monitor */
.warn-box{{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:8px;padding:10px 12px;font-size:13px;color:#FCA5A5;margin-bottom:10px;line-height:1.5}}
.cmd-box{{background:var(--overlay);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-family:monospace;font-size:13px;color:var(--amber);margin-top:4px}}
</style>
</head>
<body>
<div class="app">
  <div class="topbar">
    <div class="topbar-row">
      <div class="logo">Norms Corp</div>
      <span class="update-ts"><span class="pulse"></span>{ts_thai}</span>
      <div class="hstats">
        <div class="hs"><span class="hs-n" style="color:var(--yellow)">{alive_count}</span><span class="hs-l">รันอยู่</span></div>
        <div class="hs"><span class="hs-n" style="color:var(--amber)">58</span><span class="hs-l">drafts</span></div>
        <div class="hs"><span class="hs-n" id="h-posted" style="color:var(--green)">0</span><span class="hs-l">posted</span></div>
      </div>
    </div>
  </div>

  <div class="content">
    <div class="panel active" id="p-overview"><div id="proj-list"></div></div>

    <div class="panel" id="p-pipeline">
      <div class="sh">Transcription (live)</div>
      <div id="pipe-list"></div>
      <div class="sh">Knowledge Roadmap</div>
      <div style="background:var(--raised);border:1px solid var(--border);border-radius:var(--r);overflow:hidden;margin-bottom:10px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border)">
          <div style="background:var(--raised);padding:12px"><div style="color:var(--green);font-weight:700;font-size:13px">✅ Pass 1</div><div style="font-size:12px;color:var(--t2)">Transcription</div><div style="font-size:11px;color:var(--muted)">Gen1 Done · Gen2 WIP</div></div>
          <div style="background:var(--raised);padding:12px"><div style="color:var(--amber);font-weight:700;font-size:13px">⏳ Pass 2</div><div style="font-size:12px;color:var(--t2)">ThinkAloud Agent</div><div style="font-size:11px;color:var(--muted)">0 Logic Notes yet</div></div>
          <div style="background:var(--raised);padding:12px"><div style="color:var(--muted);font-weight:700;font-size:13px">🔴 Pass 3</div><div style="font-size:12px;color:var(--t2)">Human Review</div><div style="font-size:11px;color:var(--muted)">raw → golden</div></div>
          <div style="background:var(--raised);padding:12px"><div style="color:var(--muted);font-weight:700;font-size:13px">🔴 Train</div><div style="font-size:12px;color:var(--t2)">Digital Twin</div><div style="font-size:11px;color:var(--muted)">ต้องการ 50 golden</div></div>
        </div>
      </div>
    </div>

    <div class="panel" id="p-todos">
      <div class="sh">🚨 ด่วน</div><div id="todo-urgent"></div>
      <div class="sh">📅 สัปดาห์นี้</div><div id="todo-soon"></div>
      <div class="sh">📋 Backlog</div><div id="todo-backlog"></div>
    </div>

    <div class="panel" id="p-topics">
      <div class="sh">หัวข้อที่จะคุยต่อ</div><div id="topic-list"></div>
      <div class="sh">สิ่งที่ต้องเตรียม</div><div id="prep-list"></div>
    </div>

    <div class="panel" id="p-content">
      <div class="fscroll" id="filters">
        <button class="fbtn on" data-f="all">ทั้งหมด</button>
        <button class="fbtn" data-f="B1">📘 อ่านตลาดได้</button>
        <button class="fbtn" data-f="B2">📙 หลิวคิดอะไรอยู่</button>
        <button class="fbtn" data-f="B3">📗 จิตใจนักเทรด</button>
        <button class="fbtn" data-f="evergreen">🌿 Evergreen</button>
        <button class="fbtn" data-f="reactive">⚡ Reactive</button>
        <button class="fbtn" data-f="pending">⏳ ยังไม่โพสต์</button>
      </div>
      <input type="search" id="search" placeholder="ค้นหาหัวข้อ...">
      <div id="card-list"></div>
    </div>

    <div class="panel" id="p-claude">
      <div class="sh">Claude Sessions</div>
      <div id="claude-sessions"></div>
      <div class="sh">วิธีกลับมาคุยงานที่เพิ่งปิด</div>
      <div class="tcard"><span class="t-ic">⚡</span><div>
        <div class="t-title">ต่อ session ล่าสุดของ dir นั้น</div>
        <div class="cmd-box">claude --continue</div>
        <div class="t-detail" style="margin-top:6px">เปิด terminal ใน dir เดิม แล้วพิมพ์คำสั่งนี้ — Claude จะโหลด conversation ล่าสุดต่อได้เลย</div>
      </div></div>
      <div class="tcard"><span class="t-ic">🔍</span><div>
        <div class="t-title">เลือก session เจาะจง (จาก Session ID)</div>
        <div class="cmd-box">claude --resume &lt;sessionId&gt;</div>
        <div class="t-detail" style="margin-top:6px">Session ID 8 ตัวแรกอยู่ในการ์ดด้านบน — ใช้คำสั่งนี้เพื่อเปิด session เจาะจงได้</div>
      </div></div>
      <div class="tcard"><span class="t-ic">🚨</span><div>
        <div class="t-title">เมื่อไหร่ควรเริ่ม session ใหม่?</div>
        <div class="t-detail">เมื่อ Context bar เกิน 75% (สีแดง) — context เต็มทำให้ Claude ลืมต้นบทสนทนา ประสิทธิภาพลด ค่าใช้จ่ายสูงขึ้น<br><br>แนะนำ: สรุปงานที่ทำค้างไว้ แล้ว /clear หรือเปิด terminal ใหม่</div>
      </div></div>
    </div>
  </div>

  <nav class="bnav">
    <button class="nb on" data-nav="overview"><span class="ic">🏠</span>Overview</button>
    <button class="nb" data-nav="pipeline"><span class="ic">🔄</span>Pipeline</button>
    <button class="nb" data-nav="todos"><span class="ic">✅</span>Todos</button>
    <button class="nb" data-nav="topics"><span class="ic">💬</span>Topics</button>
    <button class="nb" data-nav="content"><span class="ic">📣</span>Content</button>
    <button class="nb" data-nav="claude"><span class="ic">⚡</span>Claude</button>
  </nav>
</div>

<div class="sheet-bg" id="sheet-bg">
  <div class="sheet">
    <div class="handle"></div>
    <div class="si">
      <div class="s-badge" id="s-badge"></div>
      <div class="s-title" id="s-title"></div>
      <div class="s-meta" id="s-meta"></div>
      <div id="s-comp"></div>
      <div class="sec-l">Facebook Post</div>
      <div class="cbox" id="s-fb"></div>
      <button class="cpbtn" onclick="cp('s-fb',this)">📋 Copy FB Post</button>
      <div class="sec-l">TikTok Hook</div>
      <div class="cbox" id="s-tiktok"></div>
      <button class="cpbtn" onclick="cp('s-tiktok',this)">📋 Copy TikTok Hook</button>
      <div class="sec-l">Caption</div>
      <div class="cbox" id="s-caption"></div>
      <button class="cpbtn" onclick="cp('s-caption',this)">📋 Copy Caption</button>
    </div>
    <div class="post-action">
      <button class="postbtn" id="post-btn" onclick="togglePosted()">✓ Mark as Posted</button>
    </div>
  </div>
</div>

<div class="update-banner" id="upd-banner" onclick="location.reload()">🔄 มีอัพเดทใหม่ — กดเพื่อโหลด</div>

<script>
const BUILD_TIME = "{ts}";
const DRAFTS   = {json.dumps(drafts,   ensure_ascii=False)};
const PROJECTS = {json.dumps(PROJECTS, ensure_ascii=False)};
const TODOS    = {json.dumps(TODOS,    ensure_ascii=False)};
const TOPICS   = {json.dumps(TOPICS,   ensure_ascii=False)};
const PREPS    = {json.dumps(PREPS,    ensure_ascii=False)};
const PIPELINE = {json.dumps(pipeline, ensure_ascii=False)};
const SC       = {json.dumps(SC,       ensure_ascii=False)};
const CLAUDE_SESSIONS = {json.dumps(claude_sessions, ensure_ascii=False)};
const SLABELS  = {{done:"✅ Done",running:"🔄 Running",phase1:"Phase 1",blocked:"🔴 Blocked",research:"Research"}};
const SCLASS   = {{done:"s-done",running:"s-running",phase1:"s-phase1",blocked:"s-blocked",research:"s-research"}};

/* storage */
const gp=()=>{{try{{return JSON.parse(localStorage.getItem("sn_p")||"{{}}")}}catch{{return{{}}}}}};
const sp=(id,v)=>{{const p=gp();v?p[id]=true:delete p[id];localStorage.setItem("sn_p",JSON.stringify(p))}};
const gt=()=>{{try{{return JSON.parse(localStorage.getItem("sn_t")||"{{}}")}}catch{{return{{}}}}}};
const st=(id,v)=>{{const t=gt();v?t[id]=true:delete t[id];localStorage.setItem("sn_t",JSON.stringify(t))}};

/* nav */
document.querySelectorAll(".nb").forEach(b=>b.addEventListener("click",()=>{{
  document.querySelectorAll(".nb,.panel").forEach(x=>x.classList.remove("on","active"));
  b.classList.add("on");
  document.getElementById("p-"+b.dataset.nav).classList.add("active");
  document.querySelector(".content").scrollTo(0,0);
}}));

/* projects */
function rProjects(){{
  document.getElementById("proj-list").innerHTML="<div class='sh'>Projects</div>"+
  PROJECTS.map(p=>`<div class="proj">
    <div class="proj-h"><span class="p-icon">${{p.icon}}</span>
      <div><div class="p-title">${{p.title}}</div><div class="p-sub">${{p.subtitle}}</div></div>
      <span class="sbadge ${{SCLASS[p.status]||"s-research"}}">${{SLABELS[p.status]||p.status}}</span>
    </div>
    <div class="pbar-w"><div class="pbar" style="width:${{p.progress}}%${{p.status==="done"?";background:var(--green)":""}}"></div></div>
    <ul class="proj-det">${{p.details.map(d=>`<li>${{d}}</li>`).join("")}}</ul>
    <div class="proj-next">${{p.next}}</div>
  </div>`).join("");
}}

/* pipeline */
function rPipeline(){{
  document.getElementById("pipe-list").innerHTML=Object.values(PIPELINE).map(v=>{{
    const pct=Math.round(v.done/v.total*100)||0;
    const bc=pct===100?"var(--green)":pct>0?"var(--amber)":"transparent";
    return `<div class="pipe-row">
      <div class="pipe-h"><span class="pipe-label">${{v.label}}</span><span class="pipe-pct">${{pct}}%</span></div>
      <div class="pipe-n">${{v.done}}<span style="font-size:14px;color:var(--muted)"> / ${{v.total}}</span></div>
      <div class="pbar-w" style="height:6px"><div class="pbar" style="width:${{pct}}%;background:${{bc}}"></div></div>
    </div>`;
  }}).join("");
}}

/* todos */
function rTodos(){{
  const done=gt();
  ["urgent","soon","backlog"].forEach(s=>{{
    document.getElementById("todo-"+s).innerHTML=TODOS[s].map((t,i)=>{{
      const id=s+"-"+i,ck=!!done[id];
      return `<div class="todo-item">
        <div class="chk${{ck?" on":""}}" onclick="tTodo('${{id}}',this)">${{ck?"✓":""}}</div>
        <div class="todo-body">
          <div class="todo-text${{ck?" done":""}}">${{t.text}}</div>
          <div class="todo-meta"><span class="due">📅 ${{t.due}}</span><span class="tag tag-${{t.tag}}">${{t.tag}}</span></div>
        </div>
      </div>`;
    }}).join("");
  }});
}}
function tTodo(id,el){{
  const v=!gt()[id];st(id,v);
  el.className="chk"+(v?" on":"");el.textContent=v?"✓":"";
  el.nextElementSibling.querySelector(".todo-text").className="todo-text"+(v?" done":"");
}}

/* topics */
function rTopics(){{
  document.getElementById("topic-list").innerHTML=TOPICS.map(t=>`
    <div class="tcard"><span class="t-ic">${{t.icon}}</span>
    <div><div class="t-title">${{t.title}}</div><div class="t-detail">${{t.detail}}</div></div></div>`).join("");
  document.getElementById("prep-list").innerHTML=PREPS.map(p=>`
    <div class="tcard"><span class="t-ic">${{p.icon}}</span>
    <div><div class="t-title">${{p.title}}</div><div class="t-detail">${{p.detail}}</div></div></div>`).join("");
}}

/* content */
let cF="all",cQ="",cD=null;
function rContent(){{
  const posted=gp(),q=cQ.toLowerCase();
  const items=DRAFTS.filter(d=>{{
    const bk=d.chapter_id.substring(0,2);
    if(cF==="B1"&&bk!=="B1")return false;
    if(cF==="B2"&&bk!=="B2")return false;
    if(cF==="B3"&&bk!=="B3")return false;
    if(cF==="evergreen"&&!d.best_time.startsWith("evergreen"))return false;
    if(cF==="reactive"&&!d.best_time.startsWith("reactive"))return false;
    if(cF==="pending"&&posted[d.chapter_id])return false;
    if(q&&!d.topic.toLowerCase().includes(q)&&!d.fb_post.toLowerCase().includes(q))return false;
    return true;
  }});
  document.getElementById("card-list").innerHTML=items.length
    ?items.map(d=>{{
      const ip=!!posted[d.chapter_id],sc=SC[d.series]||{{bg:"rgba(255,255,255,.1)",color:"#aaa"}};
      const tl=d.best_time.startsWith("reactive:")?"⚡ "+d.best_time.replace("reactive:",""):"🌿 evergreen";
      return `<div class="card${{ip?" posted":""}}" onclick="openSheet('${{d.chapter_id}}')">
        ${{ip?'<div class="pdot"></div>':""}}
        <span class="series-badge" style="background:${{sc.bg}};color:${{sc.color}}">${{d.series}}</span>
        <span class="cid" style="float:right;margin-top:3px">${{d.chapter_id.substring(0,6)}}</span>
        <div class="card-topic">${{d.topic}}</div>
        <div class="card-meta"><span class="time-tag">${{tl}}</span></div>
      </div>`;
    }}).join("")
    :'<div style="text-align:center;padding:40px;color:var(--muted)">ไม่พบ content</div>';
  document.getElementById("h-posted").textContent=Object.keys(gp()).length;
}}
document.querySelectorAll(".fbtn").forEach(b=>b.addEventListener("click",()=>{{
  document.querySelectorAll(".fbtn").forEach(x=>x.classList.remove("on"));
  b.classList.add("on");cF=b.dataset.f;rContent();
}}));
document.getElementById("search").addEventListener("input",e=>{{cQ=e.target.value;rContent()}});

let cD_draft=null;
function openSheet(id){{
  const d=DRAFTS.find(x=>x.chapter_id===id);if(!d)return;
  cD_draft=d;const sc=SC[d.series]||{{bg:"rgba(255,255,255,.1)",color:"#aaa"}};const ip=!!gp()[id];
  document.getElementById("s-badge").innerHTML=`<span class="series-badge" style="background:${{sc.bg}};color:${{sc.color}};padding:3px 10px;border-radius:5px;font-size:11px;font-weight:700">${{d.series}}</span>`;
  document.getElementById("s-title").textContent=d.topic;
  document.getElementById("s-meta").textContent=d.chapter_id+" · "+d.best_time;
  document.getElementById("s-fb").textContent=d.fb_post;
  document.getElementById("s-tiktok").textContent=d.tiktok_hook;
  document.getElementById("s-caption").textContent=d.caption;
  document.getElementById("s-comp").innerHTML=d.compliance_note?`<div class="comp">⚠️ ${{d.compliance_note}}</div>`:"";
  const btn=document.getElementById("post-btn");
  btn.textContent=ip?"✗ Unmark":"✓ Mark as Posted";btn.className="postbtn"+(ip?" unpost":"");
  document.getElementById("sheet-bg").classList.add("open");document.body.style.overflow="hidden";
}}
function closeSheet(){{document.getElementById("sheet-bg").classList.remove("open");document.body.style.overflow="";cD_draft=null}}
function togglePosted(){{
  if(!cD_draft)return;const id=cD_draft.chapter_id,v=!gp()[id];sp(id,v);
  const btn=document.getElementById("post-btn");btn.textContent=v?"✗ Unmark":"✓ Mark as Posted";btn.className="postbtn"+(v?" unpost":"");
  rContent();
}}
function cp(eid,btn){{
  navigator.clipboard.writeText(document.getElementById(eid).textContent).then(()=>{{
    const o=btn.textContent;btn.textContent="✅ Copied!";btn.classList.add("cp");
    setTimeout(()=>{{btn.textContent=o;btn.classList.remove("cp")}},1500);
  }});
}}
document.getElementById("sheet-bg").addEventListener("click",e=>{{if(e.target===document.getElementById("sheet-bg"))closeSheet()}});

/* claude monitor */
function rClaude(){{
  const el=document.getElementById("claude-sessions");
  if(!CLAUDE_SESSIONS.length){{el.innerHTML='<div style="text-align:center;padding:40px;color:var(--muted)">ไม่มี session</div>';return}}
  const ik=n=>n>=1000?(n/1000).toFixed(1)+'k':String(n);
  el.innerHTML=CLAUDE_SESSIONS.map(s=>{{
    const pct=s.tokens.context_pct;
    const bc=pct>75?'var(--red)':pct>50?'var(--yellow)':'var(--green)';
    const stC=s.alive?'s-done':'s-blocked';
    const warn=s.warn?`<div class="warn-box">⚠️ Context ${{pct}}% — ควรเริ่ม session ใหม่<br><small>พิมพ์ /clear หรือเปิด terminal ใหม่แล้วพิมพ์ claude</small></div>`:'';
    return `<div class="proj">
      <div class="proj-h"><span class="p-icon">⚡</span>
        <div><div class="p-title">${{s.cwd}}</div><div class="p-sub">PID ${{s.pid}} · ${{s.runtime_min}} นาที · #${{s.session_id}}</div></div>
        <span class="sbadge ${{stC}}">${{s.alive?'LIVE':'STOPPED'}}</span>
      </div>
      ${{warn}}
      <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:4px">
        <span>Context ${{pct}}%</span><span>${{ik(s.tokens.latest_cache_read)}} / 200k tokens</span>
      </div>
      <div class="pbar-w"><div class="pbar" style="width:${{pct}}%;background:${{bc}}"></div></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px">
        <div style="background:var(--overlay);border-radius:8px;padding:8px;text-align:center">
          <div style="font-size:15px;font-weight:700;color:var(--blue)">${{ik(s.tokens.total_input)}}</div>
          <div style="font-size:10px;color:var(--muted)">Input</div>
        </div>
        <div style="background:var(--overlay);border-radius:8px;padding:8px;text-align:center">
          <div style="font-size:15px;font-weight:700;color:var(--amber)">${{ik(s.tokens.total_output)}}</div>
          <div style="font-size:10px;color:var(--muted)">Output</div>
        </div>
        <div style="background:var(--overlay);border-radius:8px;padding:8px;text-align:center">
          <div style="font-size:15px;font-weight:700;color:var(--t2)">${{s.tokens.msg_count}}</div>
          <div style="font-size:10px;color:var(--muted)">Messages</div>
        </div>
      </div>
    </div>`;
  }}).join('');
}}

/* auto-update check */
function checkUpdate(){{
  fetch(location.href+"?_="+Date.now(),{{cache:"no-store"}})
    .then(r=>r.text()).then(html=>{{
      const m=html.match(/content="(\\d{{4}}-\\d{{2}}-\\d{{2}}T[^"]+)"/);
      if(m&&m[1]!==BUILD_TIME)document.getElementById("upd-banner").classList.add("show");
    }}).catch(()=>{{}});
}}
setInterval(checkUpdate, 60000); // ตรวจทุก 60 วินาที

/* init */
rProjects();rPipeline();rTodos();rTopics();rContent();rClaude();
</script>
</body>
</html>"""
    return html

if __name__ == "__main__":
    print("Building...")
    html = build()
    OUT.write_text(html, encoding="utf-8")
    print(f"✓ index.html ({len(html):,} bytes)")
