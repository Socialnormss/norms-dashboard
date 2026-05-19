#!/usr/bin/env python3
"""
Norms Corp Dashboard Builder
อ่านข้อมูลจริงจากระบบ → build index.html → push to GitHub Pages
"""

import json, os, datetime, subprocess
from pathlib import Path

KV        = Path.home() / "Documents/Norms-Corp/Knowledge"
TRANS     = KV / "transcripts"
OUT       = Path(__file__).parent / "index.html"

DRIVE     = Path("/Volumes/SocialNorms")
GEN1_SRC  = DRIVE / "SocialNorms PV Course/NPC GEN1"
GEN2_SRC  = DRIVE / "SocialNorms PV Course/NPC GEN2"
NMSPC_SRC = DRIVE / "SocialNorms PV Course/NMSPC 2026/NMSPC"
FB_SRC    = DRIVE / "SocialNorms PV Course/FacebookLive"

def count_mp4(path):
    if not path.exists(): return 0
    return len([f for ext in ("*.mp4", "*.mov", "*.m4v")
                for f in path.glob(ext)
                if not f.name.startswith("._")])

def count_txt(path):
    if not path.exists(): return 0
    return len(list(path.glob("*.txt")))

def count_txt_multi(*paths):
    return sum(count_txt(p) for p in paths)

DRAFTS = KV / "content_drafts"  # paused per no-API memory

def load_drafts():
    if not DRAFTS.exists(): return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DRAFTS.glob("*.json"))]

def get_pipeline():
    nmspc_done = count_txt_multi(TRANS/"nmspc2026", TRANS/"nmspc2026_misc", TRANS/"nmspc2026_plan")
    accurate_dir = KV / "transcripts_accurate" / "npc_gen1"
    accurate_done = count_txt(accurate_dir)
    return {
        "npc_gen1":   {"done": count_txt(TRANS/"npc_gen1"),      "total": 168,                       "label": "NPC Gen1 (turbo)"},
        "accurate":   {"done": accurate_done,                    "total": 25,                        "label": "Accurate Batch (Phase 1)"},
        "npc_gen2":   {"done": count_txt(TRANS/"npc_gen2"),      "total": 145,                       "label": "NPC Gen2"},
        "nmspc2026":  {"done": nmspc_done,                       "total": max(nmspc_done, 62),        "label": "NMSPC 2026"},
        "facebook":   {"done": count_txt(TRANS/"facebook_live"), "total": count_mp4(FB_SRC) or 224,  "label": "Facebook Live"},
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
            session_name = ""
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
                                # extract name from first real human message
                                if not session_name and d.get("type") == "user":
                                    msg = d.get("message", {})
                                    content = msg.get("content", "")
                                    if isinstance(content, list):
                                        for block in content:
                                            if isinstance(block, dict) and block.get("type") == "text":
                                                content = block.get("text", "")
                                                break
                                    if isinstance(content, str):
                                        text = content.strip()
                                        # skip caveat/system injected messages
                                        if text and not text.startswith("<") and "caveat" not in text.lower():
                                            raw = text.splitlines()[0].strip()
                                            session_name = raw[:52] + ("…" if len(raw) > 52 else "")
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
                "name": session_name,
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
    {"id":"norms-book","icon":"🥇","title":"Norms Book + Website","subtitle":"NPC course flagship · ฿50K","status":"phase1","progress":55,
     "details":["✅ 17/17 Q sign-off (A1-A10 · B1-B7)","✅ Phase 1 KM v1 · 12 EP","✅ 6-block curriculum locked","✅ Phase 2 v1 draft · 53 NPC + 4 T1 + 4 T3","✅ Phase 3 mechanical pass · 12 ch edited","✅ 6 new chapters drafted (842 lines)","⏳ รอ หลิว sign-off C1-C10"],"next":"หลิว review C1-C10 → unlock Phase 3 production"},
    {"id":"npc-website","icon":"🌐","title":"NPC Website (Hero Visual)","subtitle":"Apple-premium landing","status":"phase1","progress":35,
     "details":["✅ Content A1-A10 locked","✅ Visual direction notes (Section 6)","✅ Hero copy: \"เทรดด้วย WYCKOFF ไม่ใช่ด้วยความหวัง\"","✅ 6-block curriculum · Tally form · phase refund","⏳ รอ Pro Hero cinematic visual"],"next":"Pro session → Hero visual implementation"},
    {"id":"dog-feeder","icon":"🐕","title":"Dog Feeder v3","subtitle":"Soft Cozy redesign","status":"phase1","progress":60,
     "details":["✅ v2.1 live · skip-meal + nutrition","✅ Round 2 (Soft Cozy) mockup ผ่าน","✅ Font prompt + Magnific 4 sheets dictated","⏳ รอ CSS+HTML จาก Claude Design"],"next":"Max integrate after Pro assets done"},
    {"id":"hero-bell","icon":"🦸","title":"Hero (Bell's Project)","subtitle":"Claude Project · BD Manager AI","status":"phase1","progress":85,
     "details":["✅ Project deployed @ liewsk129","✅ 7 knowledge files + system prompt","✅ Test 9/10 passed","✅ Memory updated","⏳ V2 vision: brief→deliverable automation"],"next":"V2 design session 2026-05-20"},
    {"id":"transcription","icon":"🎙️","title":"Transcription","subtitle":"Accurate batch · 25 EP","status":"running","progress":0,
     "details":[],"next":"Background batch · ETA 2 วัน · accurate model"},
    {"id":"migration","icon":"🚀","title":"Migration → Claude Max","subtitle":"socialnorms.t@gmail.com","status":"done","progress":100,
     "details":["✅ APIFY migrated","✅ Firebase Owner transfer","✅ Backup complete","✅ Two-instance setup (Max + Pro)"],"next":"—"},
    {"id":"norms-corp","icon":"🏢","title":"Norms Corp Infra","subtitle":"9 departments · ownership table","status":"phase1","progress":50,
     "details":["✅ Structure + CLAUDE.md + INDEX.md","✅ SYNC system (HANDOFF · MAX-LOG · PRO-LOG)","✅ Memory system v2","⏳ Phase 2: orchestrator + task queue"],"next":"Phase 2 orchestrator · backlog"},
    {"id":"digital-twin","icon":"🤖","title":"Digital Twin","subtitle":"AI ที่สอนแบบหลิว","status":"blocked","progress":5,
     "details":["🔴 ต้องการ 50 golden Logic Notes","🔴 ThinkAloud Pass 2 ยังไม่รัน","✅ Config + Prompt พร้อม"],"next":"รอ transcript จบ → ThinkAloud → review → golden"},
    {"id":"aa","icon":"⚡","title":"AA System","subtitle":"Another AI · workflow","status":"research","progress":35,
     "details":["✅ APIFY ready","✅ NotebookLM MCP login","⏳ NPC transcripts notebook รอ upload"],"next":"NotebookLM bulk upload (manual per [[notebooklm-upload]])"},
]

TODOS = {
    "urgent":[
        {"text":"หลิว review Phase 2 doc → ตอบ sign-off C1-C10","due":"ASAP","tag":"book"},
        {"text":"Pro Hero visual implementation (cinematic)","due":"สัปดาห์นี้","tag":"website"},
        {"text":"Dog Feeder v3: CSS+HTML จาก Claude Design → integrate","due":"สัปดาห์นี้","tag":"dog-feeder"},
    ],
    "soon":[
        {"text":"Phase 3 production: rename + reshape + 5 new chapters","due":"หลัง C1-C10 sign-off","tag":"book"},
        {"text":"File rename B1_C11 → NES_Synthesis · B1_C13 → Liquidity_Complex","due":"หลัง sign-off","tag":"book"},
        {"text":"Eightcap June onwards · รอ brief","due":"มิ.ย.","tag":"eightcap"},
        {"text":"AnotherAi: NPC transcripts → NotebookLM (manual bulk)","due":"สัปดาห์นี้","tag":"aa"},
    ],
    "backlog":[
        {"text":"Wyckoff Norms: 3D / cinematic visual","due":"ongoing","tag":"brand"},
        {"text":"AI Vocab (125 fields)","due":"หลัง Norms Book","tag":"book"},
        {"text":"Tickmill / FocusTrade sponsor","due":"TBD","tag":"sponsor"},
        {"text":"NPC Gen2 + NMSPC + Facebook Live books","due":"หลัง transcript จบ","tag":"book"},
        {"text":"Digital Twin: ThinkAloud Pass 2 → Logic Notes","due":"หลัง transcript","tag":"knowledge"},
        {"text":"Norms Corp Phase 2 orchestrator","due":"เดือนหน้า","tag":"norms-corp"},
    ],
}

TOPICS = [
    {"icon":"🥇","title":"NPC Course Launch","detail":"2026-07-19 deadline · Block 1-6 curriculum · ฿50,000 · 90 วัน cohort"},
    {"icon":"📚","title":"Phase 3 Production","detail":"หลัง sign-off C1-C10 → rename pass + 5 new chapters + Tier 1 packaging"},
    {"icon":"🎨","title":"NPC Website Visual","detail":"Pro session · Hero cinematic · Apple-premium · mascot integration"},
    {"icon":"🏗️","title":"Tier 1 Sub-courses","detail":"Prop Firm Challenge (ready) · Price Zone XAUUSD · Liquidity Mastery · Wyckoff F/G (parked)"},
    {"icon":"📖","title":"Tier 3 PDF Library","detail":"4 reference PDFs · ATH · Portfolio · NNE · Wyckoff Complex (post-Phase 3)"},
    {"icon":"🦸","title":"Hero V2 Vision","detail":"เบล brief → Hero deliverable พร้อมใช้ · Max CLI background · pipeline TBD"},
    {"icon":"🤖","title":"Digital Twin Training","detail":"50 golden notes · ThinkAloud Pass 2 หลัง transcript จบ"},
    {"icon":"🎓","title":"NPC Gen2 + NMSPC + FBLive","detail":"หลัง batch accurate · re-purpose สำหรับ Tier 1 + Tier 3"},
]

PREPS = [
    {"icon":"📝","title":"Phase 2 Sign-off","detail":"`Vault/05-Projects/Norms-Book/Phase2-Architecture.md` Section 9 · ตอบ C1-C10"},
    {"icon":"💻","title":"Chapter Edits (VS Code)","detail":"`~/Documents/Norms-Corp/Knowledge/Norms-Book/npc_gen1/chapters/` · 6 NEW_*.md ตอน review"},
    {"icon":"🎤","title":"Accurate Batch Monitor","detail":"5/25 EP done · /tmp/accurate_batch.log · caffeinate · ETA ~2 วัน"},
    {"icon":"🎨","title":"Pro Hero Visual Session","detail":"Hero cinematic · Wyckoff mascot · Apple-premium · `Vault/05-Projects/NPC/Website-Content-Draft.md` Section 6"},
    {"icon":"🐕","title":"Dog Feeder v3 Assets","detail":"รอ Claude Design ส่ง CSS+HTML · Magnific 4 sheets dictated (Mascot · Time · Food · Danger)"},
    {"icon":"🦸","title":"Hero V2 Design","detail":"2026-05-20 session · sync mechanism + output format + trigger flow"},
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

    # NPC launch deadline countdown
    npc_deadline = datetime.date(2026, 7, 19)
    days_left = (npc_deadline - now.date()).days
    deadline_color = "var(--red)" if days_left <= 14 else "var(--amber)" if days_left <= 30 else "var(--green)"

    total_done  = sum(v["done"]  for v in pipeline.values())
    total_vids  = sum(v["total"] for v in pipeline.values())
    trans_pct   = round(total_done / total_vids * 100) if total_vids else 0
    done_count  = sum(1 for p in PROJECTS if p["status"] == "done")
    draft_count = len(drafts) if drafts else 58

    for p in PROJECTS:
        if p["id"] == "transcription":
            acc = pipeline['accurate']
            acc_pct = round(acc['done'] / acc['total'] * 100) if acc['total'] else 0
            p["progress"] = acc_pct
            p["details"] = [
                f"🔥 Accurate Batch: {acc['done']}/{acc['total']} EP ({acc_pct}%)",
                f"✅ NPC Gen1 turbo: {pipeline['npc_gen1']['done']}/{pipeline['npc_gen1']['total']}",
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
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Norms Corp">
<meta name="theme-color" content="#080808">
<meta name="build-time" content="{ts}">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>Norms Corp</title>
<link rel="manifest" href="manifest.json">
<style>
:root{{
  --bg:#080808;--base:#0F0F0F;--surface:#161616;--raised:#1C1C1C;--overlay:#252525;
  --amber:#D47A2A;--a4:#E0944A;--at:rgba(212,122,42,.13);
  --text:#F0EDE8;--t2:#A8A49E;--muted:#5A5652;
  --border:rgba(255,255,255,.07);
  --green:#10B981;--blue:#3B82F6;--yellow:#F59E0B;--red:#EF4444;--purple:#8B5CF6;
  --r:14px;--sb:env(safe-area-inset-bottom)
}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
html,body{{height:100%;overflow:hidden;background:var(--base);color:var(--text);
  font-family:-apple-system,Sarabun,sans-serif;font-size:16px}}
.app{{display:flex;flex-direction:column;height:100%;height:100dvh}}

/* topbar */
.topbar{{background:var(--bg);padding:14px 16px 12px;border-bottom:1px solid var(--border);flex-shrink:0}}
.topbar-row{{display:flex;align-items:center;gap:8px}}
.logo{{font-size:15px;font-weight:800;color:var(--amber);letter-spacing:.03em}}
.update-ts{{font-size:10px;color:var(--muted);margin-left:4px}}
.pulse{{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;margin-right:4px;vertical-align:middle}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.35;transform:scale(.7)}}}}
.hstats{{margin-left:auto;display:flex;gap:12px}}
.hs{{text-align:right}}
.hs-n{{font-size:18px;font-weight:800;display:block;line-height:1}}
.hs-l{{font-size:9px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.04em}}

/* layout */
.content{{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;
  padding-bottom:calc(var(--sb) + 88px)}}
.panel{{display:none;padding:14px 14px 0}}.panel.active{{display:block}}

/* floating pill nav */
.bnav{{position:fixed;bottom:calc(var(--sb) + 12px);left:50%;transform:translateX(-50%);
  background:rgba(26,26,26,.96);border:1px solid rgba(255,255,255,.12);
  border-radius:50px;padding:8px 10px;display:flex;gap:2px;
  backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
  box-shadow:0 8px 32px rgba(0,0,0,.7);z-index:100}}
.nb{{display:flex;flex-direction:column;align-items:center;gap:2px;padding:7px 12px;
  border:none;background:none;color:rgba(255,255,255,.38);font-size:9px;font-weight:700;
  cursor:pointer;border-radius:36px;letter-spacing:.03em;transition:all .2s;white-space:nowrap}}
.nb .ic{{font-size:20px;line-height:1;transition:transform .2s}}
.nb.on{{background:rgba(255,255,255,.1);color:#fff}}
.nb.on .ic{{transform:scale(1.1)}}

/* section label */
.sh{{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--amber);margin:18px 0 10px;opacity:.8}}
.sh:first-child{{margin-top:0}}

/* ── HERO STATS ── */
.hero{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px}}
.hcard{{border-radius:var(--r);padding:14px 10px 12px;text-align:center;position:relative;overflow:hidden;
  border:1px solid var(--border)}}
.hcard-inner{{position:relative;z-index:1}}
.hcard::before{{content:"";position:absolute;inset:0;opacity:1}}
.hcard.c-green{{background:linear-gradient(145deg,#0a2318,#111)}}
.hcard.c-green::before{{background:radial-gradient(circle at 50% 0%,rgba(16,185,129,.2),transparent 70%)}}
.hcard.c-amber{{background:linear-gradient(145deg,#1e1100,#111)}}
.hcard.c-amber::before{{background:radial-gradient(circle at 50% 0%,rgba(212,122,42,.25),transparent 70%)}}
.hcard.c-blue{{background:linear-gradient(145deg,#0a1428,#111)}}
.hcard.c-blue::before{{background:radial-gradient(circle at 50% 0%,rgba(59,130,246,.2),transparent 70%)}}
.h-num{{font-size:28px;font-weight:800;line-height:1;margin-bottom:5px}}
.hcard.c-green .h-num{{color:var(--green)}}
.hcard.c-amber .h-num{{color:var(--a4)}}
.hcard.c-blue .h-num{{color:#60A5FA}}
.h-lbl{{font-size:10px;color:var(--t2);font-weight:600;line-height:1.4}}

/* ── PROJECT GRID ── */
.proj-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.pcard{{border-radius:var(--r);padding:14px 12px 12px;cursor:pointer;position:relative;
  overflow:hidden;border:1px solid var(--border);background:var(--raised);
  transition:border-color .15s,transform .1s;active:scale(.98)}}
.pcard:active{{transform:scale(.97)}}
.pcard::before{{content:"";position:absolute;top:0;left:0;right:0;height:3px;border-radius:var(--r) var(--r) 0 0}}
.pcard.st-done::before{{background:var(--green)}}
.pcard.st-running::before{{background:var(--amber)}}
.pcard.st-phase1::before{{background:var(--blue)}}
.pcard.st-blocked::before{{background:var(--red)}}
.pcard.st-research::before{{background:var(--purple)}}
.pcard.st-done{{background:linear-gradient(160deg,#0e1e18,#1a1a1a)}}
.pcard.st-running{{background:linear-gradient(160deg,#1e1500,#1a1a1a)}}
.pcard.st-phase1{{background:linear-gradient(160deg,#0e1428,#1a1a1a)}}
.pcard.st-blocked{{background:linear-gradient(160deg,#1e0e0e,#1a1a1a)}}
.pcard.st-research{{background:linear-gradient(160deg,#150e28,#1a1a1a)}}
.pc-icon{{font-size:24px;line-height:1;margin-bottom:8px}}
.pc-title{{font-weight:700;font-size:13px;line-height:1.3;margin-bottom:2px}}
.pc-sub{{font-size:10px;color:var(--muted);line-height:1.3;margin-bottom:8px}}
.sbadge{{padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;display:inline-block;margin-bottom:8px}}
.s-done{{background:rgba(16,185,129,.15);color:#34D399}}
.s-running{{background:rgba(245,158,11,.15);color:#FCD34D}}
.s-phase1{{background:rgba(59,130,246,.15);color:#60A5FA}}
.s-blocked{{background:rgba(239,68,68,.15);color:#FCA5A5}}
.s-research{{background:rgba(139,92,246,.15);color:#C4B5FD}}
.pbar-w{{background:rgba(255,255,255,.07);border-radius:4px;height:3px;margin-bottom:6px;overflow:hidden}}
.pbar{{height:100%;border-radius:4px;transition:width .5s ease}}
.pc-next{{font-size:10px;color:var(--t2);line-height:1.4}}
.pc-next::before{{content:"→ ";color:var(--amber)}}

/* ── PIPELINE INFOGRAPHIC ── */
.pipe-card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);
  padding:16px;margin-bottom:10px;position:relative;overflow:hidden}}
.pipe-glow{{position:absolute;top:0;left:0;right:0;height:100%;opacity:.04;pointer-events:none}}
.pipe-label{{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}}
.pipe-nums{{display:flex;align-items:baseline;gap:6px;margin-bottom:12px}}
.pipe-done{{font-size:36px;font-weight:800;line-height:1}}
.pipe-sep{{font-size:16px;color:var(--muted)}}
.pipe-total{{font-size:16px;color:var(--muted);font-weight:600}}
.pipe-pct{{margin-left:auto;font-size:13px;font-weight:700;padding:4px 12px;
  border-radius:20px}}
.pipe-pct.p-done{{background:rgba(16,185,129,.15);color:#34D399}}
.pipe-pct.p-active{{background:rgba(212,122,42,.15);color:var(--a4)}}
.pipe-pct.p-zero{{background:var(--overlay);color:var(--muted)}}
.pipe-bar-w{{background:rgba(255,255,255,.06);border-radius:6px;height:8px;overflow:hidden}}
.pipe-bar{{height:100%;border-radius:6px;transition:width .7s ease}}

/* roadmap */
.roadmap{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.rm{{background:var(--raised);border:1px solid var(--border);border-radius:12px;
  padding:14px 12px;text-align:center}}
.rm-ic{{font-size:22px;margin-bottom:6px}}
.rm-title{{font-size:12px;font-weight:700;margin-bottom:3px}}
.rm-sub{{font-size:10px;color:var(--muted);line-height:1.5}}
.rm.done{{border-color:rgba(16,185,129,.25);background:linear-gradient(145deg,#0e1e18,#1a1a1a)}}
.rm.done .rm-title{{color:var(--green)}}
.rm.pending{{border-color:rgba(212,122,42,.2);background:linear-gradient(145deg,#1e1500,#1a1a1a)}}
.rm.pending .rm-title{{color:var(--a4)}}
.rm.locked .rm-title{{color:var(--muted)}}

/* ── TODOS ── */
.todo-item{{display:flex;align-items:flex-start;gap:10px;background:var(--raised);
  border:1px solid var(--border);border-radius:var(--r);padding:12px;margin-bottom:8px;
  border-left-width:3px}}
.todo-item.urgent{{border-left-color:var(--red)}}
.todo-item.soon{{border-left-color:var(--amber)}}
.todo-item.backlog{{border-left-color:var(--border)}}
.chk{{width:22px;height:22px;border-radius:6px;border:1px solid rgba(255,255,255,.15);
  background:var(--overlay);flex-shrink:0;display:flex;align-items:center;
  justify-content:center;font-size:13px;cursor:pointer;transition:all .15s}}
.chk.on{{background:var(--green);border-color:var(--green)}}
.todo-body{{flex:1;min-width:0}}
.todo-text{{font-size:13px;line-height:1.5}}
.todo-text.done{{text-decoration:line-through;color:var(--muted)}}
.todo-meta{{margin-top:4px;display:flex;gap:5px;align-items:center;flex-wrap:wrap}}
.due{{font-size:10px;color:var(--muted)}}
.tag{{padding:2px 7px;border-radius:4px;font-size:9px;font-weight:700;text-transform:uppercase}}
.tag-book{{background:rgba(59,130,246,.2);color:#60A5FA}}
.tag-content{{background:rgba(16,185,129,.2);color:#34D399}}
.tag-aa{{background:rgba(139,92,246,.2);color:#C4B5FD}}
.tag-eightcap{{background:rgba(245,158,11,.2);color:#FCD34D}}
.tag-knowledge{{background:rgba(212,122,42,.15);color:var(--amber)}}
.tag-norms-corp{{background:rgba(239,68,68,.15);color:#FCA5A5}}

/* ── TOPICS / PREP (2-col grid) ── */
.tgrid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px}}
.tcard{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);
  padding:12px;display:flex;flex-direction:column;gap:5px}}
.t-ic{{font-size:20px;line-height:1}}
.t-title{{font-weight:700;font-size:12px;line-height:1.3}}
.t-detail{{font-size:10px;color:var(--t2);line-height:1.5}}

/* ── CONTENT ── */
.fscroll{{display:flex;gap:7px;overflow-x:auto;padding-bottom:10px;scrollbar-width:none}}
.fscroll::-webkit-scrollbar{{display:none}}
.fbtn{{flex-shrink:0;padding:6px 14px;border-radius:20px;border:1px solid var(--border);
  background:transparent;color:var(--t2);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}}
.fbtn.on{{background:var(--amber);border-color:var(--amber);color:#000}}
#search{{width:100%;background:var(--raised);border:1px solid var(--border);border-radius:10px;
  color:var(--text);font-size:14px;padding:10px 14px;outline:none;-webkit-appearance:none;margin-bottom:12px}}
#search:focus{{border-color:var(--amber)}}
.card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);
  padding:12px;margin-bottom:8px;cursor:pointer;position:relative;transition:border-color .15s}}
.card:active{{background:var(--overlay)}}.card.posted{{opacity:.4}}
.series-badge{{padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700}}
.card-topic{{font-weight:700;font-size:14px;line-height:1.3;margin:5px 0 4px}}
.card-meta{{display:flex;gap:5px}}
.time-tag{{background:var(--overlay);padding:2px 7px;border-radius:4px;font-size:10px;color:var(--muted)}}
.cid{{font-size:10px;color:var(--muted)}}
.pdot{{position:absolute;top:10px;right:10px;width:8px;height:8px;border-radius:50%;background:var(--green)}}

/* ── BOTTOM SHEET (shared) ── */
.sheet-bg{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:300;align-items:flex-end}}
.sheet-bg.open{{display:flex}}
.sheet{{background:var(--surface);border-radius:20px 20px 0 0;width:100%;max-height:88vh;
  overflow-y:auto;-webkit-overflow-scrolling:touch;padding:0 0 calc(20px + var(--sb))}}
.handle{{width:36px;height:4px;background:var(--border);border-radius:2px;margin:12px auto 14px}}
.si{{padding:0 16px}}
.s-badge{{margin-bottom:6px}}
.s-title{{font-size:18px;font-weight:800;margin-bottom:4px;line-height:1.3}}
.s-meta{{font-size:11px;color:var(--muted);margin-bottom:14px}}
.sec-l{{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--amber);margin-bottom:7px;margin-top:14px}}
.sec-l:first-child{{margin-top:0}}
.cbox{{background:var(--raised);border:1px solid var(--border);border-radius:10px;padding:12px;
  font-size:13px;line-height:1.8;white-space:pre-wrap;word-break:break-word;margin-bottom:7px}}
.cpbtn{{width:100%;background:var(--overlay);border:1px solid var(--border);border-radius:10px;
  color:var(--t2);font-size:13px;padding:11px;cursor:pointer;margin-bottom:10px;font-weight:600}}
.cpbtn:active{{background:var(--border)}}.cpbtn.cp{{border-color:var(--green);color:var(--green)}}
.comp{{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:8px;
  padding:9px 11px;font-size:12px;color:#FCD34D;margin-bottom:12px}}
.post-action{{display:flex;gap:10px;padding:0 16px;margin-top:6px}}
.postbtn{{flex:1;background:var(--amber);border:none;color:#000;font-size:14px;font-weight:700;
  padding:14px;border-radius:12px;cursor:pointer}}
.postbtn.unpost{{background:var(--overlay);color:var(--t2);border:1px solid var(--border)}}

/* project sheet extras */
.proj-det{{list-style:none;font-size:13px;color:var(--t2);margin-bottom:4px}}
.proj-det li{{padding:3px 0;line-height:1.5}}
.proj-next-s{{font-size:13px;color:var(--amber);background:var(--at);border-radius:10px;
  padding:10px 12px;margin-top:8px}}
.proj-next-s::before{{content:"→ "}}
.big-prog{{margin:14px 0 8px}}
.big-prog-n{{font-size:40px;font-weight:800;line-height:1;margin-bottom:6px}}

/* ── CLAUDE TAB ── */
.warn-box{{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:8px;
  padding:9px 11px;font-size:12px;color:#FCA5A5;margin-bottom:8px;line-height:1.5}}
.cmd-box{{background:var(--overlay);border:1px solid var(--border);border-radius:8px;
  padding:9px 12px;font-family:monospace;font-size:12px;color:var(--amber);margin-top:6px;word-break:break-all}}
.tok-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px}}
.tok-cell{{background:var(--overlay);border-radius:8px;padding:8px;text-align:center}}
.tok-n{{font-size:15px;font-weight:700}}.tok-l{{font-size:9px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:.04em}}
.cl-card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);padding:14px;margin-bottom:10px}}

/* update banner */
.update-banner{{display:none;position:fixed;top:16px;left:50%;transform:translateX(-50%);
  background:#0f2b0f;border:1px solid var(--green);color:var(--green);font-size:12px;font-weight:600;
  padding:9px 20px;border-radius:20px;z-index:200;cursor:pointer;white-space:nowrap;box-shadow:0 4px 20px rgba(0,0,0,.5)}}
.update-banner.show{{display:block;animation:slideDown .3s ease}}
@keyframes slideDown{{from{{opacity:0;transform:translateX(-50%) translateY(-8px)}}to{{opacity:1;transform:translateX(-50%) translateY(0)}}}}
</style>
</head>
<body>
<div class="app">
  <div class="topbar">
    <div class="topbar-row">
      <div class="logo">⬡ Norms Corp</div>
      <span class="update-ts"><span class="pulse"></span>{ts_thai}</span>
      <div class="hstats">
        <div class="hs"><span class="hs-n" style="color:var(--yellow)">{alive_count}</span><span class="hs-l">Running</span></div>
        <div class="hs"><span class="hs-n" style="color:var(--amber)">{draft_count}</span><span class="hs-l">Drafts</span></div>
        <div class="hs"><span class="hs-n" id="h-posted" style="color:var(--green)">0</span><span class="hs-l">Posted</span></div>
      </div>
    </div>
  </div>

  <div class="content">

    <!-- OVERVIEW -->
    <div class="panel active" id="p-overview">
      <!-- NPC Launch Countdown Banner -->
      <div style="background:linear-gradient(135deg,rgba(212,122,42,.15),rgba(212,122,42,.05));border:1px solid rgba(212,122,42,.3);border-radius:14px;padding:14px 16px;margin-bottom:14px;display:flex;align-items:center;gap:14px">
        <div style="flex-shrink:0;text-align:center;min-width:62px">
          <div style="font-size:32px;font-weight:800;color:{deadline_color};line-height:1">{days_left}</div>
          <div style="font-size:9px;color:var(--t2);font-weight:600;text-transform:uppercase;letter-spacing:.05em">days left</div>
        </div>
        <div style="flex:1">
          <div style="font-size:11px;color:var(--amber);font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px">🥇 NPC Launch Deadline</div>
          <div style="font-size:14px;color:var(--text);font-weight:600;line-height:1.3">2026-07-19 · Norms Book + Website</div>
          <div style="font-size:11px;color:var(--t2);margin-top:2px">Phase 2 sign-off pending · Phase 3 ready</div>
        </div>
      </div>
      <div class="hero">
        <div class="hcard c-green">
          <div class="hcard-inner">
            <div class="h-num">{done_count}/{len(PROJECTS)}</div>
            <div class="h-lbl">Projects<br>Done</div>
          </div>
        </div>
        <div class="hcard c-amber">
          <div class="hcard-inner">
            <div class="h-num">{pipeline['accurate']['done']}/{pipeline['accurate']['total']}</div>
            <div class="h-lbl">Accurate<br>Batch</div>
          </div>
        </div>
        <div class="hcard c-blue">
          <div class="hcard-inner">
            <div class="h-num">{trans_pct}%</div>
            <div class="h-lbl">Trans.<br>Done</div>
          </div>
        </div>
      </div>
      <div class="sh">Projects</div>
      <div class="proj-grid" id="proj-list"></div>
      <div class="sh">Transcription</div>
      <div id="pipe-list"></div>
      <div class="sh">Knowledge Roadmap</div>
      <div class="roadmap">
        <div class="rm done">
          <div class="rm-ic">✅</div>
          <div class="rm-title">Pass 1</div>
          <div class="rm-sub">Transcription<br>Gen1 Done</div>
        </div>
        <div class="rm pending">
          <div class="rm-ic">⏳</div>
          <div class="rm-title">Pass 2</div>
          <div class="rm-sub">ThinkAloud Agent<br>0 Logic Notes</div>
        </div>
        <div class="rm locked">
          <div class="rm-ic">🔴</div>
          <div class="rm-title">Pass 3</div>
          <div class="rm-sub">Human Review<br>raw → golden</div>
        </div>
        <div class="rm locked">
          <div class="rm-ic">🔴</div>
          <div class="rm-title">Train</div>
          <div class="rm-sub">Digital Twin<br>ต้องการ 50 golden</div>
        </div>
      </div>
    </div>

    <!-- TODOS -->
    <div class="panel" id="p-todos">
      <div class="sh">🚨 ด่วน</div><div id="todo-urgent"></div>
      <div class="sh">📅 สัปดาห์นี้</div><div id="todo-soon"></div>
      <div class="sh">📋 Backlog</div><div id="todo-backlog"></div>
    </div>

    <!-- TOPICS -->
    <div class="panel" id="p-topics">
      <div class="sh">หัวข้อที่จะคุยต่อ</div>
      <div class="tgrid" id="topic-list"></div>
      <div class="sh">สิ่งที่ต้องเตรียม</div>
      <div class="tgrid" id="prep-list"></div>
    </div>

    <!-- CONTENT -->
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

    <!-- CLAUDE -->
    <div class="panel" id="p-claude">
      <div class="sh">Claude Sessions</div>
      <div id="claude-sessions"></div>
      <div class="sh">วิธีกลับมาคุยงาน</div>
      <div class="tcard" style="flex-direction:row;gap:12px;margin-bottom:8px">
        <span class="t-ic">⚡</span>
        <div><div class="t-title">ต่อ session ล่าสุด</div>
        <div class="cmd-box">claude --continue</div></div>
      </div>
      <div class="tcard" style="flex-direction:row;gap:12px;margin-bottom:8px">
        <span class="t-ic">🔍</span>
        <div><div class="t-title">เลือก session เจาะจง</div>
        <div class="cmd-box">claude --resume &lt;sessionId&gt;</div></div>
      </div>
      <div class="tcard" style="flex-direction:row;gap:12px">
        <span class="t-ic">🚨</span>
        <div><div class="t-title">เมื่อไหร่เริ่ม session ใหม่?</div>
        <div class="t-detail" style="font-size:11px;color:var(--t2);line-height:1.5;margin-top:4px">Context bar เกิน 75% (สีแดง) → /clear หรือเปิด terminal ใหม่</div></div>
      </div>
    </div>

  </div>

  <nav class="bnav">
    <button class="nb on" data-nav="overview"><span class="ic">🏠</span>Overview</button>
    <button class="nb" data-nav="todos"><span class="ic">✅</span>Todos</button>
    <button class="nb" data-nav="topics"><span class="ic">💬</span>Topics</button>
    <button class="nb" data-nav="content"><span class="ic">📣</span>Content</button>
    <button class="nb" data-nav="claude"><span class="ic">⚡</span>Claude</button>
  </nav>
</div>

<!-- Content detail sheet -->
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

<!-- Project detail sheet -->
<div class="sheet-bg" id="proj-bg">
  <div class="sheet">
    <div class="handle"></div>
    <div class="si" id="proj-si"></div>
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
const STCLS    = {{done:"st-done",running:"st-running",phase1:"st-phase1",blocked:"st-blocked",research:"st-research"}};
const PBARCOL  = {{done:"var(--green)",running:"var(--amber)",phase1:"var(--blue)",blocked:"var(--red)",research:"var(--purple)"}};

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

/* projects grid */
function rProjects(){{
  document.getElementById("proj-list").innerHTML=PROJECTS.map((p,i)=>{{
    const bc=PBARCOL[p.status]||"var(--purple)";
    return `<div class="pcard ${{STCLS[p.status]||"st-research"}}" onclick="openProj(${{i}})">
      <div class="pc-icon">${{p.icon}}</div>
      <div class="pc-title">${{p.title}}</div>
      <div class="pc-sub">${{p.subtitle}}</div>
      <span class="sbadge ${{SCLASS[p.status]||"s-research"}}">${{SLABELS[p.status]||p.status}}</span>
      <div class="pbar-w"><div class="pbar" style="width:${{p.progress}}%;background:${{bc}}"></div></div>
      <div class="pc-next">${{p.next}}</div>
    </div>`;
  }}).join("");
}}

function openProj(i){{
  const p=PROJECTS[i];
  const bc=PBARCOL[p.status]||"var(--purple)";
  const pct=p.progress;
  document.getElementById("proj-si").innerHTML=`
    <span class="sbadge ${{SCLASS[p.status]||"s-research"}}" style="margin-bottom:8px">${{SLABELS[p.status]||p.status}}</span>
    <div style="font-size:22px;font-weight:800;margin-bottom:4px;line-height:1.2">${{p.icon}} ${{p.title}}</div>
    <div style="font-size:13px;color:var(--muted);margin-bottom:16px">${{p.subtitle}}</div>
    <div class="big-prog">
      <div class="big-prog-n" style="color:${{bc}}">${{pct}}%</div>
      <div class="pbar-w" style="height:8px"><div class="pbar" style="width:${{pct}}%;background:${{bc}}"></div></div>
    </div>
    <div class="sec-l">รายละเอียด</div>
    <ul class="proj-det">${{p.details.map(d=>`<li>${{d}}</li>`).join("")}}</ul>
    <div class="proj-next-s">${{p.next}}</div>
    <div style="height:8px"></div>
  `;
  document.getElementById("proj-bg").classList.add("open");
  document.body.style.overflow="hidden";
}}
document.getElementById("proj-bg").addEventListener("click",e=>{{
  if(e.target===document.getElementById("proj-bg")){{
    document.getElementById("proj-bg").classList.remove("open");
    document.body.style.overflow="";
  }}
}});

/* pipeline */
function rPipeline(){{
  document.getElementById("pipe-list").innerHTML=Object.values(PIPELINE).map(v=>{{
    const pct=Math.round(v.done/v.total*100)||0;
    const done=pct===100;const active=pct>0&&!done;
    const bc=done?"var(--green)":active?"var(--amber)":"rgba(255,255,255,.06)";
    const nc=done?"var(--green)":"#E0944A";
    const pc=done?"p-done":active?"p-active":"p-zero";
    return `<div class="pipe-card">
      <div class="pipe-label">${{v.label}}</div>
      <div class="pipe-nums">
        <span class="pipe-done" style="color:${{nc}}">${{v.done}}</span>
        <span class="pipe-sep">/</span>
        <span class="pipe-total">${{v.total}}</span>
        <span class="pipe-pct ${{pc}}">${{pct}}%</span>
      </div>
      <div class="pipe-bar-w"><div class="pipe-bar" style="width:${{pct}}%;background:${{bc}}"></div></div>
    </div>`;
  }}).join("");
}}

/* todos */
function rTodos(){{
  const done=gt();
  ["urgent","soon","backlog"].forEach(s=>{{
    document.getElementById("todo-"+s).innerHTML=TODOS[s].map((t,i)=>{{
      const id=s+"-"+i,ck=!!done[id];
      return `<div class="todo-item ${{s}}">
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
    <div class="tcard">
      <div class="t-ic">${{t.icon}}</div>
      <div class="t-title">${{t.title}}</div>
      <div class="t-detail">${{t.detail}}</div>
    </div>`).join("");
  document.getElementById("prep-list").innerHTML=PREPS.map(p=>`
    <div class="tcard">
      <div class="t-ic">${{p.icon}}</div>
      <div class="t-title">${{p.title}}</div>
      <div class="t-detail">${{p.detail}}</div>
    </div>`).join("");
}}

/* content */
let cF="all",cQ="",cD_draft=null;
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
        <span class="cid" style="float:right;margin-top:2px">${{d.chapter_id.substring(0,6)}}</span>
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

/* claude */
function rClaude(){{
  const el=document.getElementById("claude-sessions");
  if(!CLAUDE_SESSIONS.length){{el.innerHTML='<div style="text-align:center;padding:40px;color:var(--muted)">ไม่มี session</div>';return}}
  const ik=n=>n>=1000?(n/1000).toFixed(1)+'k':String(n);
  el.innerHTML=CLAUDE_SESSIONS.map(s=>{{
    const pct=s.tokens.context_pct;
    const bc=pct>75?'var(--red)':pct>50?'var(--yellow)':'var(--green)';
    const warn=s.warn?`<div class="warn-box">⚠️ Context ${{pct}}% — ควรเริ่ม session ใหม่<br><small>พิมพ์ /clear หรือเปิด terminal ใหม่</small></div>`:'';
    return `<div class="cl-card">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:20px">⚡</span>
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;font-size:13px;line-height:1.3;margin-bottom:2px">${{s.name||s.cwd}}</div>
          <div style="font-size:10px;color:var(--muted)">PID ${{s.pid}} · ${{s.runtime_min}} min · #${{s.session_id}}</div>
        </div>
        <span class="sbadge ${{s.alive?"s-done":"s-blocked"}}">${{s.alive?"LIVE":"OFF"}}</span>
      </div>
      ${{warn}}
      <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-bottom:4px">
        <span>Context ${{pct}}%</span><span>${{ik(s.tokens.latest_cache_read)}} / 200k tokens</span>
      </div>
      <div class="pbar-w" style="height:6px"><div class="pbar" style="width:${{pct}}%;background:${{bc}}"></div></div>
      <div class="tok-grid">
        <div class="tok-cell"><div class="tok-n" style="color:var(--blue)">${{ik(s.tokens.total_input)}}</div><div class="tok-l">Input</div></div>
        <div class="tok-cell"><div class="tok-n" style="color:var(--amber)">${{ik(s.tokens.total_output)}}</div><div class="tok-l">Output</div></div>
        <div class="tok-cell"><div class="tok-n" style="color:var(--t2)">${{s.tokens.msg_count}}</div><div class="tok-l">Msgs</div></div>
      </div>
    </div>`;
  }}).join('');
}}

/* auto-update check — ปล่อยไว้ตามเดิม */
function checkUpdate(){{
  fetch(location.href+"?_="+Date.now(),{{cache:"no-store"}})
    .then(r=>r.text()).then(html=>{{
      const m=html.match(/content="(\\d{{4}}-\\d{{2}}-\\d{{2}}T[^"]+)"/);
      if(m&&m[1]!==BUILD_TIME)document.getElementById("upd-banner").classList.add("show");
    }}).catch(()=>{{}});
}}
setInterval(checkUpdate, 60000);

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
